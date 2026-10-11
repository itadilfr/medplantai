from sqlalchemy import String, Integer, Float, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

class Plant(Base):
    __tablename__ = "plants"
    plant_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scientific_name: Mapped[str] = mapped_column(String, unique=True)
    common_name: Mapped[str] = mapped_column(String)
    family: Mapped[str] = mapped_column(String, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    traditional_relevance: Mapped[str] = mapped_column(Text, nullable=True)
    plant_part_used: Mapped[str] = mapped_column(Text, nullable=True)
    taxonomy_id: Mapped[int] = mapped_column(Integer, nullable=True)
    ncbi_taxonomy_url: Mapped[str] = mapped_column(Text, nullable=True)
    image_url: Mapped[str] = mapped_column(Text, nullable=True)
    genomic_background: Mapped[str] = mapped_column(Text, nullable=True)
    phytochemical_information: Mapped[str] = mapped_column(Text, nullable=True)
    reported_biological_activities: Mapped[str] = mapped_column(Text, nullable=True)
    data_status: Mapped[str] = mapped_column(String, default="seeded_needs_enrichment")
    verified: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[str] = mapped_column(String)
    updated_at: Mapped[str] = mapped_column(String)

class PlantAlias(Base):
    __tablename__ = "plant_aliases"
    alias_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plant_id: Mapped[int] = mapped_column(ForeignKey("plants.plant_id"))
    alias: Mapped[str] = mapped_column(String)
    alias_type: Mapped[str] = mapped_column(String, nullable=True)

class Compound(Base):
    __tablename__ = "compounds"
    compound_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    preferred_name: Mapped[str] = mapped_column(String, unique=True)
    pubchem_cid: Mapped[int] = mapped_column(Integer, nullable=True)
    molecular_formula: Mapped[str] = mapped_column(String, nullable=True)
    molecular_weight: Mapped[float] = mapped_column(Float, nullable=True)
    xlogp: Mapped[float] = mapped_column(Float, nullable=True)
    h_bond_donors: Mapped[int] = mapped_column(Integer, nullable=True)
    h_bond_acceptors: Mapped[int] = mapped_column(Integer, nullable=True)
    tpsa: Mapped[float] = mapped_column(Float, nullable=True)
    rotatable_bonds: Mapped[int] = mapped_column(Integer, nullable=True)
    exact_mass: Mapped[float] = mapped_column(Float, nullable=True)
    heavy_atom_count: Mapped[int] = mapped_column(Integer, nullable=True)
    canonical_smiles: Mapped[str] = mapped_column(Text, nullable=True)
    inchi: Mapped[str] = mapped_column(Text, nullable=True)
    inchikey: Mapped[str] = mapped_column(String, nullable=True)
    structure_image_url: Mapped[str] = mapped_column(Text, nullable=True)
    data_status: Mapped[str] = mapped_column(String, default="needs_enrichment")
    created_at: Mapped[str] = mapped_column(String)
    updated_at: Mapped[str] = mapped_column(String)

class PlantCompound(Base):
    __tablename__ = "plant_compounds"
    plant_id: Mapped[int] = mapped_column(ForeignKey("plants.plant_id"), primary_key=True)
    compound_id: Mapped[int] = mapped_column(ForeignKey("compounds.compound_id"), primary_key=True)
    relationship_type: Mapped[str] = mapped_column(String, default="reported_association")
    evidence: Mapped[str] = mapped_column(Text, nullable=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.source_id"), nullable=True)

class GenomicRecord(Base):
    __tablename__ = "genomic_records"
    genomic_record_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plant_id: Mapped[int] = mapped_column(ForeignKey("plants.plant_id"))
    ncbi_taxonomy_id: Mapped[int] = mapped_column(Integer, nullable=True)
    accession: Mapped[str] = mapped_column(String, nullable=True)
    record_type: Mapped[str] = mapped_column(String, nullable=True)
    barcode_region: Mapped[str] = mapped_column(String, nullable=True)
    sequence_status: Mapped[str] = mapped_column(String, nullable=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.source_id"), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)

class Source(Base):
    __tablename__ = "sources"
    source_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_name: Mapped[str] = mapped_column(String)
    source_type: Mapped[str] = mapped_column(String, nullable=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=True)
    external_record_id: Mapped[str] = mapped_column(String, nullable=True)
    retrieval_date: Mapped[str] = mapped_column(String, nullable=True)
    license_or_usage_note: Mapped[str] = mapped_column(Text, nullable=True)

class Activity(Base):
    __tablename__ = 'activities'
    activity_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)

class CompoundActivity(Base):
    __tablename__ = 'compound_activities'
    compound_id: Mapped[int] = mapped_column(ForeignKey('compounds.compound_id'), primary_key=True)
    activity_id: Mapped[int] = mapped_column(ForeignKey('activities.activity_id'), primary_key=True)
    evidence_level: Mapped[str] = mapped_column(String, nullable=True)
    evidence_text: Mapped[str] = mapped_column(Text, nullable=True)
    source_id: Mapped[int] = mapped_column(ForeignKey('sources.source_id'), nullable=True)

class Target(Base):
    __tablename__ = 'targets'
    target_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    target_name: Mapped[str] = mapped_column(String)
    gene_symbol: Mapped[str] = mapped_column(String, nullable=True)
    organism: Mapped[str] = mapped_column(String, nullable=True)
    ncbi_gene_id: Mapped[int] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)

class CompoundTarget(Base):
    __tablename__ = 'compound_targets'
    compound_id: Mapped[int] = mapped_column(ForeignKey('compounds.compound_id'), primary_key=True)
    target_id: Mapped[int] = mapped_column(ForeignKey('targets.target_id'), primary_key=True)
    evidence_level: Mapped[str] = mapped_column(String, nullable=True)
    source_id: Mapped[int] = mapped_column(ForeignKey('sources.source_id'), nullable=True)
