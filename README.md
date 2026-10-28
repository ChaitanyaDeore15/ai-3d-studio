# AI 3D Studio

> Production-grade, publicly accessible hybrid 3D asset creation platform combining **Blender Python (`bpy`) Procedural Generation** with **Generative AI (Meshy / Tripo)**.

![Status](https://img.shields.io/badge/Status-Production%20Ready-emerald)
![Blender](https://img.shields.io/badge/Blender%20Engine-5.2%20LTS-orange)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI%20%7C%20Pydantic%20v2-blue)
![React](https://img.shields.io/badge/Frontend-React%20%7C%20Three.js-61DAFB)

---

## Key Highlights

- **Real 3D Geometry**: Generates actual meshes with verified glTF 2.0 / GLB headers, calculate vertex/triangle metrics, and PBR Principled BSDF materials. Never substitutes static mockups.
- **Hybrid Intelligent Routing**:
  - Structured & architectural assets (*tables, chairs, cabinets, houses, rooms, columns, road segments, platforms*) route directly to **Blender Python** for instant, exact, mathematically clean topology.
  - Complex sculpts or organic assets route to the configured **AI 3D Provider** (Meshy / Tripo).
  - Explicit user mode override supported. Transparent routing explanations provided for every task.
- **Interactive WebGL 3D Viewport**: Orbit, pan, zoom, wireframe toggle, grid floor, turntable auto-rotation, camera reset, and real-time bounding box statistics.
- **Parametric Refinement**: Modify dimensions, materials, and styles on completed models without starting from scratch.
- **Strict Security & Verification**:
  - Binary glTF chunk validation & zip package checks.
  - MIME type and magic number validation on image uploads.
  - Isolated process execution with timeout limits (`BLENDER_TIMEOUT_SECONDS`).
  - No client-supplied executable scripts.

---

## Project Structure

```
ai-3d-studio/
  frontend/                  # React 18 + Vite + TypeScript (strict) + Tailwind CSS + Three.js
    src/
      features/
        viewer/              # Three.js WebGL viewport with OrbitControls & GLTFLoader
        studio/              # Generation workspace, parametric sliders & prompt editor
        projects/            # Saved project library & asset manager
      services/              # API client and upload handlers
      types/                 # Strict TypeScript contracts
  backend/                   # FastAPI + Pydantic v2 + SQLAlchemy + SQLite/PostgreSQL
    app/
      api/                   # REST endpoints: /health, /capabilities, /generations, etc.
      core/                  # Configuration & environment variables
      models/                # SQLAlchemy database models
      schemas/               # Validated Pydantic request & response schemas
      services/
        blender/             # Headless Blender subprocess runner
        generation/          # Hybrid routing & prompt intent analysis
        providers/           # Meshy v2 & Tripo v2 API adapters
        storage/             # LocalStorage & S3 storage adapters
        validation/          # glTF 2.0 / GLB binary validation engine
      workers/               # Asynchronous task processor & cancellation manager
    tests/                   # Automated pytest integration & unit tests
  blender/
    scripts/
      procedural/            # Modular procedural mesh builders (bpy + bmesh)
      export/                # glTF 2.0 exporter & mesh metrics inspector
      validation/            # Binary header & structural validator
      entrypoint.py          # CLI runner invoked by backend worker
  shared/
    api-contracts/           # OpenAPI 3.1.0 specifications
  infrastructure/
    docker/                  # Production Dockerfiles (Backend with Blender, Frontend Nginx)
  docs/                      # Architecture, deployment, and API reference guides
  docker-compose.yml         # Multi-container orchestration (Backend, Frontend, Postgres, Redis)
```

---

## Quickstart

### 1. Run Automated Tests
```powershell
$env:PYTHONPATH="." ; pytest backend/tests/test_api.py -v
```

### 2. Start Backend
```powershell
$env:PYTHONPATH="." ; uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
Swagger UI documentation is available at `http://127.0.0.1:8000/docs`.

### 3. Start Frontend
```powershell
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## Production Docker Deployment

```bash
docker-compose up -d --build
```

---

## License
MIT
