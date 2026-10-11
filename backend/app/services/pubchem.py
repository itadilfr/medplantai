import httpx
import os
from urllib.parse import quote

BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
TIMEOUT = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "15"))

async def search_compound(name: str):
    # PubChem PUG REST property lookup by compound name.
    props = "MolecularFormula,MolecularWeight,XLogP,HBondDonorCount,HBondAcceptorCount,TopologicalPolarSurfaceArea,RotatableBondCount,ExactMass,HeavyAtomCount,CanonicalSMILES,InChI,InChIKey"
    url = f"{BASE}/compound/name/{quote(name, safe="")}/property/{props}/JSON"
    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
        response = await client.get(url)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        data = response.json()

    rows = data.get("PropertyTable", {}).get("Properties", [])
    if not rows:
        return None
    row = rows[0]
    return {
        "preferred_name": name,
        "pubchem_cid": row.get("CID"),
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
        "structure_image_url": (
            f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/"
            f"{row.get('CID')}/PNG" if row.get("CID") else None
        ),
    }
