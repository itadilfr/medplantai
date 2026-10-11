# MedPlant AI Frontend v1

Attractive botanical + technology themed React/Vite frontend for the MedPlant AI project.

## Run
1. Make sure the FastAPI backend is running on `http://localhost:8000`.
2. `npm install`
3. Copy `.env.example` to `.env` if the backend URL differs.
4. `npm run dev`

Production build: `npm run build`.

## Backend endpoints used
- GET `/api/plants/search?q=...`
- GET `/api/compounds/search?q=...`

The UI keeps users inside MedPlant AI. External-source fallback remains a backend responsibility.
