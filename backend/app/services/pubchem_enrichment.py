import os
import httpx
from urllib.parse import quote

BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
TIMEOUT = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "20"))

async def taxonomy_assay_compound_ids(taxonomy_id: int, max_aids: int = 5, max_cids: int = 20):
    """Return PubChem compound CIDs linked to bioassays for an organism taxonomy.

    These are bioactivity-linked candidates, NOT automatically confirmed phytochemicals.
    """
    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
        r = await client.get(f"{BASE}/taxonomy/taxid/{taxonomy_id}/aids/TXT")
        if r.status_code == 404:
            return []
        r.raise_for_status()
        aids = [x.strip() for x in r.text.splitlines() if x.strip()][:max_aids]
        cids = []
        for aid in aids:
            cr = await client.get(f"{BASE}/assay/aid/{aid}/cids/TXT")
            if cr.status_code != 200:
                continue
            for x in cr.text.splitlines():
                x=x.strip()
                if x.isdigit() and x not in cids:
                    cids.append(x)
                if len(cids) >= max_cids:
                    return cids
    return cids

async def compound_properties(cids):
    if not cids:
        return []
    props = "MolecularFormula,MolecularWeight,XLogP,HBondDonorCount,HBondAcceptorCount,TopologicalPolarSurfaceArea,RotatableBondCount,ExactMass,HeavyAtomCount,ConnectivitySMILES,InChI,InChIKey,IUPACName"
    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
        r = await client.get(f"{BASE}/compound/cid/{','.join(map(str,cids))}/property/{props}/JSON")
        if r.status_code == 404:
            return []
        r.raise_for_status()
        rows = r.json().get("PropertyTable", {}).get("Properties", [])
    out=[]
    for row in rows:
        cid=row.get("CID")
        out.append({
            "preferred_name": row.get("IUPACName") or f"PubChem CID {cid}",
            "pubchem_cid": cid,
            "molecular_formula": row.get("MolecularFormula"),
            "molecular_weight": float(row["MolecularWeight"]) if row.get("MolecularWeight") else None,
            "xlogp": float(row["XLogP"]) if row.get("XLogP") is not None else None,
        "h_bond_donors": int(row["HBondDonorCount"]) if row.get("HBondDonorCount") is not None else None,
        "h_bond_acceptors": int(row["HBondAcceptorCount"]) if row.get("HBondAcceptorCount") is not None else None,
        "tpsa": float(row["TopologicalPolarSurfaceArea"]) if row.get("TopologicalPolarSurfaceArea") is not None else None,
        "rotatable_bonds": int(row["RotatableBondCount"]) if row.get("RotatableBondCount") is not None else None,
        "exact_mass": float(row["ExactMass"]) if row.get("ExactMass") is not None else None,
        "heavy_atom_count": int(row["HeavyAtomCount"]) if row.get("HeavyAtomCount") is not None else None,
            "canonical_smiles": row.get("ConnectivitySMILES") or row.get("CanonicalSMILES"),
            "inchi": row.get("InChI"),
            "inchikey": row.get("InChIKey"),
            "structure_image_url": f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/PNG" if cid else None,
        })
    return out
