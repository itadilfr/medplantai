# MedPlant AI — V10

## Purpose
MedPlant AI is a medicinal-plant research platform with two core workflows:

1. **Plant Explorer** — search a plant name and open its complete local profile.
2. **Therapeutic Candidate Discovery** — enter a disease/virus and let the computational intelligence layer compare the query against every plant profile available in the local knowledge base, recognise activity patterns, evaluate phytochemical composition and target context, and rank the most promising research candidates.

## Researcher workflow
**Disease/virus query → profile-wide pattern recognition → reported biological activities → phytochemical composition → target/evidence context → ranked plants → most promising compounds**

If the condition is not yet recognised, the researcher can still provide optional biological, molecular, structural or sequence/marker clues. These are treated as additional pattern features. Any probable matches remain research hypotheses and require independent validation.

## What the ranking engine does
- Considers every plant profile currently available in the local database.
- Gives strong weight to **reported biological activities** and their alignment with the query.
- Identifies the strongest compound composition associated with each plant candidate.
- Uses molecular target context and data completeness as supporting signals.
- Returns reasons for why a plant and compound were surfaced.
- Can show potentially complementary plants as a **research hypothesis**, not a treatment recommendation.

### AI status
V10 contains an **AI-assisted pattern-recognition prototype**. The current engine is transparent and reproducible rather than pretending that a trained machine-learning model exists. Its architecture is intentionally replaceable: a future trained model can consume the same plant-profile features and return validated rankings once a sufficiently curated training dataset and evaluation metrics are available.

## Scientific boundary
The system identifies **potential research candidates**, not cures. A computational ranking does not establish efficacy, safety, dosage, diagnosis, or clinical suitability. Reported biological activities are evidence signals and must be validated against appropriate primary literature and experimental studies.

## Run on Windows
1. Install Python 3.14 and Node.js.
2. Extract this ZIP into a new folder.
3. Double-click `start_medplant_ai.bat`.
4. Keep the two black terminal windows open.
5. Open `http://localhost:5173/`.

## Main navigation
- **Plant Explorer**: search and inspect plants.
- **Candidate Discovery**: disease/virus → promising plants and compounds.
- **How it works**: overview of the computational pipeline.

## API
- `POST /api/discovery/match` — therapeutic candidate discovery.
- `GET /api/plants/search?q=...` — plant search.
- `GET /api/plants/{plant_id}` — full plant profile.

## Visual assets

V10 includes reference plant photography for the four poster plants. The bundled profile uses Wikimedia Commons files identified as CC0/public-domain on their file pages: Azadirachta indica2024.jpg, Turmeric plants images.jpg, Ocimum Tenuiflorum.jpg, and Ashwagandha.jpg.


## V10 Therapeutic Candidate Discovery update
The discovery page now includes an explicit Back to home control and a more visible AI-assisted research prediction layer. The backend returns a predicted research pattern, pattern-strength label, matched biological signals, weighted signal breakdown, leading composition signal, and a transparent research-priority statement. The engine remains a deterministic/semantic pattern-ranking prototype rather than a separately trained clinical ML model; results are research hypotheses requiring literature and experimental validation.
