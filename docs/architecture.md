# AI 3D Studio - System Architecture & Technical Specifications

## 1. System Overview

**AI 3D Studio** is a production-grade, hybrid 3D asset creation platform designed to reconcile the precision requirements of architectural/parametric modeling with the creative freedom of generative AI.

The platform provides two genuine generation pathways:
1. **Procedural Generation**: Directly drives a headless Blender 5.x / 4.x instance via its native Python API (`bpy`). Generates clean, manifold, mathematically exact parametric assets (tables, chairs, cabinets, rooms, houses, columns, road segments, platforms) in seconds with zero external API fees.
2. **Generative AI (Text & Image-to-3D)**: Communicates with established external providers (Meshy, Tripo) for organic, freeform characters, sculpts, and complex meshes.

```
                           +---------------------------+
                           |   React + Three.js UI     |
                           |   (Vite, Tailwind, R3F)   |
                           +-------------+-------------+
                                         |
                                  REST / JSON / Multipart
                                         |
                                         v
                           +-------------+-------------+
                           |      FastAPI Backend      |
                           | (Auth, Validation, Router)|
                           +-------------+-------------+
                                         |
                    +--------------------+--------------------+
                    |                                         |
                    v                                         v
   +----------------+----------------+      +-----------------+---------------+
   |   Blender Headless Subprocess   |      |  External AI Providers Client   |
   |   (bpy scripts, glTF 2.0 export)|      |  (Meshy v2 / Tripo v2 API)      |
   +----------------+----------------+      +-----------------+---------------+
                    |                                         |
                    +--------------------+--------------------+
                                         |
                                         v
                           +-------------+-------------+
                           |  3D File Validation Engine |
                           |  (Binary glTF header &    |
                           |   mesh topology checks)   |
                           +-------------+-------------+
                                         |
                                         v
                           +-------------+-------------+
                           | Storage & Database Layer  |
                           | (Local / S3 + PostgreSQL) |
                           +---------------------------+
```

## 2. Hybrid Router & Intent Analysis

When a user submits a natural language prompt in `Auto` mode:
- The router checks for procedural category keywords (e.g., dining table, armchair, modern house, marble pillar, road segment).
- If recognized, the router extracts dimensions, material preferences, and styles, dispatching directly to Blender.
- If the object is complex, organic, or free-form (e.g., "cyberpunk dragon robot"), the router selects the configured AI provider.
- If AI credentials are not configured, the platform transparently explains the limitation and falls back to a clean procedural asset or prompts for keys.

## 3. Blender Headless Worker Subsystem

- Subprocesses are spawned with `--background --python entrypoint.py -- <spec.json> <out.glb> <report.json>`.
- The worker executes inside an isolated process group with a strict timeout (`BLENDER_TIMEOUT_SECONDS = 60s`).
- Bounding box metrics, vertex counts, and face counts are extracted directly from Blender `mathutils` and the mesh RNA.
- Exports are generated using Blender's native `export_scene.gltf` operator with PBR materials preserved.

## 4. 3D Model Validation & Security

Before any generated or exported file is served or stored:
- **Binary Header Verification**: GLB files must have magic header `0x46546C67` (`glTF`), version 2, and exact byte length matching the file size.
- **JSON Chunk Verification**: Chunk 0 is inspected to ensure `asset.version` is defined, `meshes` contains at least one primitive, and buffer sizes match.
- **Archive Verification**: For `.gltf` ZIP packages, all external `.bin` and image URIs referenced in the JSON are verified against archive members, preventing directory traversal attacks (`../`).
- **Upload Safety**: Reference images are strictly validated against magic bytes (`\xFF\xD8\xFF` for JPEG, `\x89PNG` for PNG, `RIFF` for WEBP). User filenames are never stored; cryptographically secure UUID keys are generated.
