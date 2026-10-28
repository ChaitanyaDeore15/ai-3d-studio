# AI 3D Studio - REST API Reference

All requests and responses use JSON (except binary file downloads and multipart image uploads).

## 1. System Endpoints

### `GET /api/health`
Checks backend and Blender health status.
**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2026-10-28T02:14:00.000Z",
  "database_connected": true,
  "blender_available": true,
  "blender_version": "5.2.0 LTS"
}
```

### `GET /api/capabilities`
Returns current engine capabilities, active AI provider, supported procedural categories, and spending metrics.

---

## 2. Generation Endpoints

### `POST /api/generations`
Submits a natural language or image generation request. Dispatches asynchronously and returns immediately.
**Payload**:
```json
{
  "prompt": "rustic oak dining table 1.8m wide",
  "generation_mode": "auto",
  "object_category": "table",
  "style": "rustic",
  "dimensions": {
    "width": 1.8,
    "depth": 0.9,
    "height": 0.75,
    "units": "meters"
  },
  "material_preferences": {
    "preset": "wood",
    "color_hex": "#8B5A2B"
  },
  "export_format": "glb"
}
```

### `GET /api/generations/{job_id}`
Returns progress (`0-100`), status (`queued`, `running`, `completed`, `failed`), and output asset information.

### `POST /api/generations/{job_id}/cancel`
Cancels a pending or running generation job safely.

---

## 3. Asset & File Serving

### `GET /api/assets/{asset_id}`
Retrieves calculated metadata, polygon count, vertex count, and validation results.

### `GET /api/assets/{asset_id}/file`
Directly serves the valid `.glb` binary model for 3D viewers.

### `POST /api/refine/{asset_id}`
Creates a refined variant of an existing asset with updated parameters while preserving version history.

---

## 4. Reference Image Uploads

### `POST /api/uploads`
Accepts `multipart/form-data` with `file`. Strictly enforces image magic bytes and returns a sanitized storage ID for image-to-3D.
