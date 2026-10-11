import os
import httpx

TIMEOUT = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "20"))
BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

async def _get_json(endpoint: str, params: dict):
    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
        r = await client.get(f"{BASE}/{endpoint}", params=params)
        r.raise_for_status()
        return r.json()

async def taxonomy_lookup(query: str):
    data = await _get_json("esearch.fcgi", {"db":"taxonomy", "term":f'"{query}"[All Names]', "retmode":"json", "retmax":5})
    ids = data.get("esearchresult", {}).get("idlist", [])
    if not ids:
        return None
    tid = int(ids[0])
    summary = await _get_json("esummary.fcgi", {"db":"taxonomy", "id":tid, "retmode":"json"})
    s = summary.get("result", {}).get(str(tid), {})
    scientific = s.get("scientificname") or s.get("ScientificName")
    if not scientific:
        return None
    return {
        "taxonomy_id": tid,
        "scientific_name": scientific,
        "common_name": s.get("commonname") or s.get("CommonName") or query,
        "rank": s.get("rank") or s.get("Rank"),
        "lineage": s.get("lineage") or s.get("Lineage"),
    }

async def nucleotide_accessions(taxonomy_id: int, max_records: int = 5):
    term = f"txid{taxonomy_id}[Organism:exp] AND (biomol_genomic[PROP] OR biomol_mrna[PROP])"
    data = await _get_json("esearch.fcgi", {"db":"nuccore", "term":term, "retmode":"json", "retmax":max_records, "sort":"relevance"})
    ids = data.get("esearchresult", {}).get("idlist", [])
    if not ids:
        return []
    summary = await _get_json("esummary.fcgi", {"db":"nuccore", "id":','.join(ids), "retmode":"json", "version":"2.0"})
    result = summary.get("result", {})
    records = []
    for uid in ids:
        row = result.get(str(uid), {})
        acc = row.get("accessionversion") or row.get("caption") or row.get("accession")
        if acc:
            records.append({"accession": acc, "record_type": row.get("moltype") or "nucleotide", "title": row.get("title")})
    return records
