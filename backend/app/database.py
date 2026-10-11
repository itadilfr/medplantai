from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
import os

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB = BASE_DIR / 'medplant_ai.db'
DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite+aiosqlite:///{DEFAULT_DB}')
engine = create_async_engine(DATABASE_URL, future=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
class Base(DeclarativeBase): pass

async def init_db():
    async with engine.begin() as conn:
        await conn.execute(text('PRAGMA foreign_keys=ON'))
        await conn.execute(text('SELECT 1'))
        # v6 keeps the original DB and adds one optional image field.
        cols=(await conn.execute(text('PRAGMA table_info(plants)'))).all()
        names={r[1] for r in cols}
        if 'image_url' not in names:
            await conn.execute(text('ALTER TABLE plants ADD COLUMN image_url TEXT'))
        for col in ['genomic_background','phytochemical_information','reported_biological_activities']:
            if col not in names:
                await conn.execute(text(f'ALTER TABLE plants ADD COLUMN {col} TEXT'))
        ccols={r[1] for r in (await conn.execute(text('PRAGMA table_info(compounds)'))).all()}
        additions={'h_bond_donors':'INTEGER','h_bond_acceptors':'INTEGER','tpsa':'REAL','rotatable_bonds':'INTEGER','exact_mass':'REAL','heavy_atom_count':'INTEGER'}
        for col,typ in additions.items():
            if col not in ccols:
                await conn.execute(text(f'ALTER TABLE compounds ADD COLUMN {col} {typ}'))

async def get_db():
    async with SessionLocal() as session:
        yield session
