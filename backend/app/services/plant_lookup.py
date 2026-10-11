from .ncbi import taxonomy_lookup

async def ncbi_taxonomy_search(scientific_name: str):
    data = await taxonomy_lookup(scientific_name)
    return data["taxonomy_id"] if data else None

async def ncbi_taxonomy_lookup(query: str):
    return await taxonomy_lookup(query)
