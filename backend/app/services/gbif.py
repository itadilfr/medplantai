import os, httpx
BASE='https://api.gbif.org/v1'
TIMEOUT=float(os.getenv('REQUEST_TIMEOUT_SECONDS','20'))

async def species_match(name:str):
    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
        r=await client.get(f'{BASE}/species/match',params={'name':name})
        r.raise_for_status(); return r.json()

async def species_media(key:int):
    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
        r=await client.get(f'{BASE}/species/{key}/media',params={'limit':5})
        if r.status_code!=200: return None
        data=r.json()
        for m in data.get('results',[]):
            ident=m.get('identifier') or m.get('references')
            if ident: return ident
    return None
