from pydantic import BaseModel, Field
from typing import Optional

class PlantOut(BaseModel):
    plant_id: int
    scientific_name: str
    common_name: str
    family: Optional[str] = None
    description: Optional[str] = None
    traditional_relevance: Optional[str] = None
    plant_part_used: Optional[str] = None
    taxonomy_id: Optional[int] = None
    ncbi_taxonomy_url: Optional[str] = None
    image_url: Optional[str] = None
    genomic_background: Optional[str] = None
    phytochemical_information: Optional[str] = None
    reported_biological_activities: Optional[str] = None
    data_status: str
    verified: bool

class PlantCreate(BaseModel):
    scientific_name: str = Field(min_length=2)
    common_name: str = Field(min_length=1)
    family: Optional[str] = None
    description: Optional[str] = None
    traditional_relevance: Optional[str] = None
    plant_part_used: Optional[str] = None
    taxonomy_id: Optional[int] = None
    ncbi_taxonomy_url: Optional[str] = None
    verified: bool = False

class CompoundOut(BaseModel):
    compound_id: int
    preferred_name: str
    pubchem_cid: Optional[int] = None
    molecular_formula: Optional[str] = None
    molecular_weight: Optional[float] = None
    xlogp: Optional[float] = None
    h_bond_donors: Optional[int] = None
    h_bond_acceptors: Optional[int] = None
    tpsa: Optional[float] = None
    rotatable_bonds: Optional[int] = None
    exact_mass: Optional[float] = None
    heavy_atom_count: Optional[int] = None
    canonical_smiles: Optional[str] = None
    inchi: Optional[str] = None
    inchikey: Optional[str] = None
    structure_image_url: Optional[str] = None
    data_status: str

class SearchResponse(BaseModel):
    query: str
    source: str
    result: dict
