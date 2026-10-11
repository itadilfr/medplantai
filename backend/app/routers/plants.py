from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from ..database import get_db, SessionLocal
from ..models import Plant, PlantAlias, Source, Compound, PlantCompound, GenomicRecord, Activity, CompoundActivity, Target, CompoundTarget
from ..schemas import PlantOut, PlantCreate
from ..services.plant_lookup import ncbi_taxonomy_lookup, ncbi_taxonomy_search
from ..services.ncbi import nucleotide_accessions
from ..services.pubchem_enrichment import taxonomy_assay_compound_ids, compound_properties
from ..services.pubchem import search_compound
from ..services.profile_seed import profile_for
from ..services.gbif import species_match, species_media
import datetime, os, asyncio

router = APIRouter(prefix='/plants', tags=['plants'])

BULK_STATUS={'running':False,'completed':0,'total':100,'failed':0,'message':'Ready'}

async def get_or_create_source(db, *, source_name, source_type, source_url=None, external_record_id=None, note=''):
    stmt=select(Source).where(Source.source_name==source_name, Source.external_record_id==external_record_id)
    source=(await db.execute(stmt)).scalar_one_or_none()
    if source: return source
    source=Source(source_name=source_name,source_type=source_type,source_url=source_url,external_record_id=external_record_id,retrieval_date=datetime.date.today().isoformat(),license_or_usage_note=note)
    db.add(source); await db.flush(); return source

def plant_dict(p):
    return {'plant_id':p.plant_id,'scientific_name':p.scientific_name,'common_name':p.common_name,'family':p.family,'description':p.description,'traditional_relevance':p.traditional_relevance,'plant_part_used':p.plant_part_used,'taxonomy_id':p.taxonomy_id,'ncbi_taxonomy_url':p.ncbi_taxonomy_url,'image_url':getattr(p,'image_url',None),'genomic_background':getattr(p,'genomic_background',None),'phytochemical_information':getattr(p,'phytochemical_information',None),'reported_biological_activities':getattr(p,'reported_biological_activities',None),'data_status':p.data_status,'verified':bool(p.verified)}

async def apply_baseline(db,p):
    d=profile_for(p.scientific_name,p.common_name)
    changed=False
    if not p.family and d['family']: p.family=d['family']; changed=True
    if not p.plant_part_used: p.plant_part_used=d['plant_part_used']; changed=True
    for field in ['genomic_background','phytochemical_information','reported_biological_activities']:
        if not getattr(p, field, None) and d.get(field):
            setattr(p, field, d[field]); changed=True
    if not p.description: p.description=d['description']; changed=True
    if not p.traditional_relevance: p.traditional_relevance=d['traditional_relevance']; changed=True
    if changed: p.updated_at=datetime.datetime.now(datetime.UTC).isoformat()
    return changed

async def sync_seed_compounds(db):
    # Fill the four poster compounds with current PubChem molecular properties when possible.
    for name in ['Azadirachtin','Curcumin','Ursolic Acid','Withaferin A']:
        c=(await db.execute(select(Compound).where(func.lower(Compound.preferred_name)==name.lower()))).scalar_one_or_none()
        if not c: continue
        try:
            data=await search_compound(name)
        except Exception: continue
        if data:
            for k,v in data.items():
                if k!='preferred_name' and v is not None: setattr(c,k,v)
            c.data_status='pubchem_synced'
            c.updated_at=datetime.datetime.now(datetime.UTC).isoformat()
    await db.commit()

async def enrich_plant_record(db,p):
    summary={'ncbi':False,'genbank':0,'pubchem_compounds':0,'gbif':False,'notes':[]}
    now=datetime.datetime.now(datetime.UTC).isoformat()
    await apply_baseline(db,p)
    # GBIF: family + representative image where available.
    if os.getenv('GBIF_ENABLED','true').lower()=='true':
        try:
            g=await species_match(p.scientific_name)
            if g and g.get('matchType') in ('EXACT','FUZZY'):
                if not p.family: p.family=g.get('family') or p.family
                key=g.get('usageKey')
                if key and not p.image_url: p.image_url=await species_media(int(key))
                summary['gbif']=True
                await get_or_create_source(db,source_name='GBIF Species API',source_type='taxonomy_media_api',source_url='https://www.gbif.org/developer/species',external_record_id=str(key) if key else p.scientific_name,note='Taxonomic/media metadata; verify source attribution and reuse terms.')
        except Exception as exc: summary['notes'].append(f'GBIF lookup unavailable: {exc}')
    if os.getenv('NCBI_ENABLED','true').lower()!='true':
        p.data_status='profile_seeded_local'; p.updated_at=now; await db.commit(); await db.refresh(p); return summary
    tax=None
    try: tax=await ncbi_taxonomy_lookup(p.scientific_name)
    except Exception as exc: summary['notes'].append(f'NCBI taxonomy lookup failed: {exc}')
    if tax:
        p.taxonomy_id=tax['taxonomy_id']; p.scientific_name=tax['scientific_name']; p.ncbi_taxonomy_url=f"https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id={tax['taxonomy_id']}"; summary['ncbi']=True
        if (not p.common_name) or p.common_name.lower()==p.scientific_name.lower(): p.common_name=tax.get('common_name') or p.common_name
        await get_or_create_source(db,source_name='NCBI Taxonomy',source_type='taxonomy_api',source_url='https://www.ncbi.nlm.nih.gov/taxonomy',external_record_id=str(tax['taxonomy_id']),note='Retrieved through NCBI E-utilities; verify current terms for redistribution.')
        try: accessions=await nucleotide_accessions(tax['taxonomy_id'],max_records=8)
        except Exception as exc: accessions=[]; summary['notes'].append(f'NCBI nucleotide lookup failed: {exc}')
        for rec in accessions:
            exists=(await db.execute(select(GenomicRecord).where(GenomicRecord.plant_id==p.plant_id,GenomicRecord.accession==rec['accession']))).scalar_one_or_none()
            if not exists:
                src=await get_or_create_source(db,source_name='NCBI Nucleotide / GenBank',source_type='genomic_database',source_url='https://www.ncbi.nlm.nih.gov/nuccore/',external_record_id=rec['accession'],note='Accession metadata retrieved from NCBI.')
                db.add(GenomicRecord(plant_id=p.plant_id,ncbi_taxonomy_id=tax['taxonomy_id'],accession=rec['accession'],record_type=rec.get('record_type') or 'nucleotide',sequence_status='NCBI record found',source_id=src.source_id,notes=rec.get('title'))); summary['genbank']+=1
        if os.getenv('PUBCHEM_ENABLED','true').lower()=='true':
            try:
                cids=await taxonomy_assay_compound_ids(tax['taxonomy_id'],max_aids=5,max_cids=25); props=await compound_properties(cids)
            except Exception as exc: props=[]; summary['notes'].append(f'PubChem enrichment failed: {exc}')
            source=await get_or_create_source(db,source_name='PubChem PUG REST',source_type='chemical_api',source_url='https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest',external_record_id=f"taxonomy:{tax['taxonomy_id']}",note='Bioactivity-linked compound candidates; not proof of phytochemical occurrence.')
            for data in props:
                cid=data.get('pubchem_cid')
                if not cid: continue
                existing=(await db.execute(select(Compound).where(Compound.pubchem_cid==cid))).scalar_one_or_none()
                if not existing:
                    existing=Compound(**data,data_status='imported_from_pubchem_taxonomy',created_at=now,updated_at=now); db.add(existing); await db.flush()
                link=(await db.execute(select(PlantCompound).where(PlantCompound.plant_id==p.plant_id,PlantCompound.compound_id==existing.compound_id))).scalar_one_or_none()
                if not link:
                    db.add(PlantCompound(plant_id=p.plant_id,compound_id=existing.compound_id,relationship_type='pubchem_bioactivity_candidate',evidence='Linked through organism-level PubChem bioassay records; not proof that this compound occurs in the plant.',source_id=source.source_id)); summary['pubchem_compounds']+=1
    p.data_status='enriched_external_sources' if (summary['ncbi'] or summary['genbank'] or summary['pubchem_compounds'] or summary['gbif']) else 'profile_seeded_external_unavailable'
    p.updated_at=now; await db.commit(); await db.refresh(p); return summary

async def profile_detail(db,plant_id):
    p=await db.get(Plant,plant_id)
    if not p: return None
    compounds=(await db.execute(select(Compound,PlantCompound).join(PlantCompound,PlantCompound.compound_id==Compound.compound_id).where(PlantCompound.plant_id==plant_id))).all()
    genomes=(await db.execute(select(GenomicRecord).where(GenomicRecord.plant_id==plant_id))).scalars().all()
    activities=(await db.execute(select(Activity,CompoundActivity,Compound).join(CompoundActivity,CompoundActivity.activity_id==Activity.activity_id).join(Compound,Compound.compound_id==CompoundActivity.compound_id).join(PlantCompound,PlantCompound.compound_id==Compound.compound_id).where(PlantCompound.plant_id==plant_id))).all()
    targets=(await db.execute(select(Target,CompoundTarget,Compound).join(CompoundTarget,CompoundTarget.target_id==Target.target_id).join(Compound,Compound.compound_id==CompoundTarget.compound_id).join(PlantCompound,PlantCompound.compound_id==Compound.compound_id).where(PlantCompound.plant_id==plant_id))).all()
    source_ids=[g.source_id for g in genomes if g.source_id] + [link.source_id for _,link in compounds if link.source_id] + [ct.source_id for _,ct,_ in targets if ct.source_id]
    sources=(await db.execute(select(Source).where(Source.source_id.in_(source_ids)))).scalars().all() if source_ids else []
    return {'plant':plant_dict(p),'completeness':{'identity':bool(p.scientific_name and p.common_name and p.family),'traditional':bool(p.traditional_relevance and p.plant_part_used),'genomic':bool(genomes or p.taxonomy_id or p.genomic_background),'chemical':bool(compounds),'phytochemical':bool(p.phytochemical_information),'activities':bool(p.reported_biological_activities or activities),'sources':bool(sources)},'compounds':[{'compound_id':c.compound_id,'preferred_name':c.preferred_name,'pubchem_cid':c.pubchem_cid,'molecular_formula':c.molecular_formula,'molecular_weight':c.molecular_weight,'xlogp':c.xlogp,'h_bond_donors':c.h_bond_donors,'h_bond_acceptors':c.h_bond_acceptors,'tpsa':c.tpsa,'rotatable_bonds':c.rotatable_bonds,'exact_mass':c.exact_mass,'heavy_atom_count':c.heavy_atom_count,'canonical_smiles':c.canonical_smiles,'structure_image_url':c.structure_image_url,'relationship_type':link.relationship_type,'evidence':link.evidence} for c,link in compounds],'genomic_records':[{'accession':g.accession,'record_type':g.record_type,'barcode_region':g.barcode_region,'sequence_status':g.sequence_status,'notes':g.notes} for g in genomes],'activities':[{'compound':c.preferred_name,'activity':a.name,'evidence_level':ca.evidence_level,'evidence_text':ca.evidence_text} for a,ca,c in activities],'targets':[{'compound':c.preferred_name,'target':t.target_name,'gene_symbol':t.gene_symbol,'organism':t.organism,'description':t.description,'evidence_level':ct.evidence_level,'source_id':ct.source_id} for t,ct,c in targets],'sources':[{'source_name':s.source_name,'source_type':s.source_type,'source_url':s.source_url,'external_record_id':s.external_record_id} for s in sources]}

@router.get('')
async def list_plants(q:str|None=Query(default=None),offset:int=Query(default=0,ge=0),limit:int=Query(default=100,ge=1,le=500),db:AsyncSession=Depends(get_db)):
    stmt=select(Plant).order_by(Plant.common_name,Plant.plant_id); count_stmt=select(func.count()).select_from(Plant)
    if q and q.strip():
        term=f"%{q.strip().lower()}%"; cond=or_(func.lower(Plant.common_name).like(term),func.lower(Plant.scientific_name).like(term)); stmt=stmt.where(cond); count_stmt=count_stmt.where(cond)
    total=(await db.execute(count_stmt)).scalar_one(); rows=(await db.execute(stmt.offset(offset).limit(limit))).scalars().all()
    return {'count':len(rows),'total':total,'offset':offset,'limit':limit,'source':'local_database','results':[plant_dict(p) for p in rows]}

@router.get('/enrichment-status')
async def enrichment_status(): return BULK_STATUS

async def enrich_one(plant_id):
    async with SessionLocal() as db:
        p=await db.get(Plant,plant_id)
        if p:
            try: await enrich_plant_record(db,p); return True
            except Exception: return False
    return False

async def enrich_all_background():
    if BULK_STATUS['running']: return
    BULK_STATUS.update(running=True,completed=0,failed=0,message='Enriching the 100-plant starter library…')
    async with SessionLocal() as db:
        await sync_seed_compounds(db)
        ids=[x.plant_id for x in (await db.execute(select(Plant).order_by(Plant.plant_id))).scalars().all()]
    sem=asyncio.Semaphore(2)
    async def worker(pid):
        async with sem: return await enrich_one(pid)
    for i in range(0,len(ids),2):
        res=await asyncio.gather(*(worker(pid) for pid in ids[i:i+2]))
        BULK_STATUS['completed']+=len(res); BULK_STATUS['failed']+=sum(1 for x in res if not x)
    BULK_STATUS['running']=False; BULK_STATUS['message']='100-plant enrichment pass complete. Records remain source-aware and locally cached.'

@router.post('/enrich-all')
async def start_enrich_all():
    if BULK_STATUS['running']: return BULK_STATUS
    asyncio.create_task(enrich_all_background()); return {'started':True,**BULK_STATUS}

@router.get('/search')
async def search_plants(q:str=Query(min_length=1),limit:int=Query(default=20,ge=1,le=100),db:AsyncSession=Depends(get_db)):
    term=f"%{q.lower()}%"; stmt=select(Plant).outerjoin(PlantAlias,PlantAlias.plant_id==Plant.plant_id).where(or_(func.lower(Plant.common_name).like(term),func.lower(Plant.scientific_name).like(term),func.lower(PlantAlias.alias).like(term))).distinct().order_by(Plant.common_name,Plant.plant_id).limit(limit)
    rows=(await db.execute(stmt)).scalars().all()
    if rows: return {'query':q,'count':len(rows),'source':'local_database','results':[plant_dict(p) for p in rows]}
    if os.getenv('NCBI_ENABLED','true').lower()!='true': return {'query':q,'count':0,'source':'not_found','results':[]}
    try: data=await ncbi_taxonomy_lookup(q.strip())
    except Exception as exc: return {'query':q,'count':0,'source':'external_lookup_failed','results':[],'error':str(exc)}
    if not data: return {'query':q,'count':0,'source':'not_found','results':[]}
    existing=(await db.execute(select(Plant).where(Plant.taxonomy_id==data['taxonomy_id']))).scalar_one_or_none()
    if existing:
        await enrich_plant_record(db,existing); return {'query':q,'count':1,'source':'local_database_after_external_match','results':[plant_dict(existing)]}
    now=datetime.datetime.now(datetime.UTC).isoformat(); p=Plant(scientific_name=data['scientific_name'],common_name=data.get('common_name') or q.strip(),taxonomy_id=data['taxonomy_id'],ncbi_taxonomy_url=f"https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id={data['taxonomy_id']}",data_status='imported_from_ncbi_taxonomy',verified=0,created_at=now,updated_at=now)
    db.add(p); await db.flush(); db.add(PlantAlias(plant_id=p.plant_id,alias=q.strip(),alias_type='search_term')); db.add(PlantAlias(plant_id=p.plant_id,alias=p.common_name,alias_type='common_name')); await db.commit(); await db.refresh(p)
    await enrich_plant_record(db,p)
    return {'query':q,'count':1,'source':'external_researched_saved','results':[plant_dict(p)]}

@router.get('/{plant_id}/enrichment')
async def get_enrichment(plant_id:int,db:AsyncSession=Depends(get_db)):
    d=await profile_detail(db,plant_id)
    if not d: raise HTTPException(404,'Plant not found')
    return d

@router.get('/{plant_id}')
async def get_plant(plant_id:int,db:AsyncSession=Depends(get_db)):
    d=await profile_detail(db,plant_id)
    if not d: raise HTTPException(404,'Plant not found')
    return d

@router.post('',response_model=PlantOut,status_code=201)
async def create_plant(payload:PlantCreate,db:AsyncSession=Depends(get_db)):
    exists=(await db.execute(select(Plant).where(func.lower(Plant.scientific_name)==payload.scientific_name.lower()))).scalar_one_or_none()
    if exists: raise HTTPException(409,'Plant with this scientific name already exists')
    now=datetime.datetime.now(datetime.UTC).isoformat(); p=Plant(scientific_name=payload.scientific_name.strip(),common_name=payload.common_name.strip(),family=payload.family,description=payload.description,traditional_relevance=payload.traditional_relevance,plant_part_used=payload.plant_part_used,taxonomy_id=payload.taxonomy_id,genomic_background=None,phytochemical_information=None,reported_biological_activities=None,ncbi_taxonomy_url=None,data_status='created_needs_enrichment',verified=int(payload.verified),created_at=now,updated_at=now)
    db.add(p); await db.flush(); db.add(PlantAlias(plant_id=p.plant_id,alias=p.common_name,alias_type='common_name')); await db.commit(); await db.refresh(p)
    await enrich_plant_record(db,p)
    return PlantOut(**plant_dict(p))
