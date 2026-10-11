from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from ..database import get_db
from ..models import Compound, Source
from ..services.pubchem import search_compound
import datetime, os

router = APIRouter(prefix="/compounds", tags=["compounds"])

@router.get("/search")
async def search_compounds(
    q: str = Query(min_length=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    term = f"%{q.lower()}%"
    stmt = select(Compound).where(func.lower(Compound.preferred_name).like(term)).limit(limit)
    rows = (await db.execute(stmt)).scalars().all()

    if rows:
        return {
            "query": q,
            "count": len(rows),
            "source": "local_database",
            "results": [compound_dict(c) for c in rows]
        }

    if os.getenv("PUBCHEM_ENABLED","true").lower() != "true":
        return {"query": q, "count": 0, "source": "local_database", "results": []}

    # External fallback: retrieve, store, then return through OUR API.
    try:
        data = await search_compound(q)
    except Exception as exc:
        return {
            "query": q,
            "count": 0,
            "source": "external_lookup_failed",
            "results": [],
            "error": str(exc)
        }

    if not data:
        return {"query": q, "count": 0, "source": "not_found", "results": []}

    existing = (await db.execute(
        select(Compound).where(Compound.pubchem_cid == data["pubchem_cid"])
    )).scalar_one_or_none()

    if existing:
        return {"query": q, "count": 1, "source": "local_database_after_external_match", "results": [compound_dict(existing)]}

    now = datetime.datetime.now(datetime.UTC).isoformat()
    c = Compound(**data, data_status="imported_from_pubchem", created_at=now, updated_at=now)
    db.add(c)
    await db.flush()

    source = Source(
        source_name="PubChem PUG REST",
        source_type="chemical_api",
        source_url="https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest",
        external_record_id=str(data["pubchem_cid"]),
        retrieval_date=datetime.date.today().isoformat(),
        license_or_usage_note="Imported via API; verify current usage terms before redistribution."
    )
    db.add(source)
    await db.commit()
    await db.refresh(c)

    return {"query": q, "count": 1, "source": "pubchem_then_saved", "results": [compound_dict(c)]}

@router.get("/{compound_id}")
async def get_compound(compound_id: int, db: AsyncSession = Depends(get_db)):
    c = await db.get(Compound, compound_id)
    if not c:
        raise HTTPException(404, "Compound not found")
    return compound_dict(c)

def compound_dict(c):
    return {
        "compound_id": c.compound_id,
        "preferred_name": c.preferred_name,
        "pubchem_cid": c.pubchem_cid,
        "molecular_formula": c.molecular_formula,
        "molecular_weight": c.molecular_weight,
        "xlogp": c.xlogp,
        "canonical_smiles": c.canonical_smiles,
        "inchi": c.inchi,
        "inchikey": c.inchikey,
        "structure_image_url": c.structure_image_url,
        "data_status": c.data_status,
    }
