import os
import time
import json
import logging
import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from backend.app.db.session import SessionLocal
from backend.app.models.models import GenerationJob, Asset, UsageLedger, ExportJob
from backend.app.services.blender.blender_runner import BlenderRunner
from backend.app.services.storage.storage_service import get_storage_service
from backend.app.services.validation.model_validator import validate_3d_asset_file
from backend.app.services.providers import get_ai_provider

logger = logging.getLogger(__name__)

# Dedicated thread pool for non-blocking asynchronous generation tasks
executor = ThreadPoolExecutor(max_workers=4)

active_cancellations = set()

def cancel_running_job(job_id: str):
    active_cancellations.add(job_id)

def is_job_cancelled(job_id: str) -> bool:
    return job_id in active_cancellations

def enqueue_generation_job(job_id: str):
    executor.submit(_process_generation_job, job_id)

def enqueue_export_job(export_job_id: str):
    executor.submit(_process_export_job, export_job_id)

def _process_generation_job(job_id: str):
    db: Session = SessionLocal()
    try:
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found in database.")
            return

        if is_job_cancelled(job_id):
            job.status = "cancelled"
            job.safe_error_message = "Job was cancelled by the user."
            job.completed_at = datetime.datetime.utcnow()
            db.commit()
            return

        job.status = "running"
        job.progress = 10
        job.started_at = datetime.datetime.utcnow()
        db.commit()

        if job.generation_mode == "procedural" or job.provider == "blender":
            _execute_procedural_job(db, job)
        else:
            _execute_ai_provider_job(db, job)

    except Exception as e:
        logger.exception(f"Unhandled error processing job {job_id}: {e}")
        try:
            job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
            if job and job.status != "cancelled":
                job.status = "failed"
                job.error_code = "INTERNAL_WORKER_ERROR"
                job.safe_error_message = str(e)
                job.completed_at = datetime.datetime.utcnow()
                db.commit()
        except Exception:
            pass
    finally:
        active_cancellations.discard(job_id)
        db.close()

def _execute_procedural_job(db: Session, job: GenerationJob):
    runner = BlenderRunner()
    raw_params = json.loads(job.raw_parameters or "{}")
    category = raw_params.get("category", "table")
    builder_params = raw_params.get("builder_params", {})
    export_format = raw_params.get("export_format", "glb")

    job.progress = 30
    db.commit()

    if is_job_cancelled(job.id):
        job.status = "cancelled"
        job.completed_at = datetime.datetime.utcnow()
        db.commit()
        return

    # Run Blender headless worker
    result = runner.execute_procedural_generation(
        category=category,
        parameters=builder_params,
        export_format=export_format
    )

    job.progress = 75
    db.commit()

    model_bytes = result["model_bytes"]
    ext = result["file_extension"]
    report = result["report"]
    stats = report.get("statistics", {})

    # Save to owned storage
    storage = get_storage_service()
    storage_key, file_size, checksum = storage.store_file(
        source_path_or_bytes=model_bytes,
        extension=ext,
        prefix=f"projects/{job.project_id or 'default'}"
    )

    # Validate output model
    local_file_path = storage.retrieve_file_path(storage_key)
    validation = validate_3d_asset_file(local_file_path, format_hint=ext)

    # Create Asset record
    dimensions = stats.get("dimensions", {})
    polygon_count = stats.get("triangles", stats.get("faces", 0))
    vertex_count = stats.get("vertices", 0)

    asset = Asset(
        owner_id=job.owner_id,
        project_id=job.project_id,
        source_job_id=job.id,
        storage_key=storage_key,
        mime_type="model/gltf-binary" if ext == "glb" else "application/zip",
        file_size=file_size,
        file_checksum=checksum,
        file_format=ext,
        dimensions_json=json.dumps(dimensions),
        polygon_count=polygon_count,
        vertex_count=vertex_count,
        validation_status="valid" if validation.get("valid") else "failed",
        validation_report=json.dumps(validation)
    )
    db.add(asset)
    db.flush()

    # Record usage
    ledger = UsageLedger(
        owner_id=job.owner_id,
        job_id=job.id,
        operation_type="procedural_gen",
        usage_units=1.0,
        cost_usd=0.0
    )
    db.add(ledger)

    job.status = "completed"
    job.progress = 100
    job.completed_at = datetime.datetime.utcnow()
    db.commit()

def _execute_ai_provider_job(db: Session, job: GenerationJob):
    provider = get_ai_provider()
    if not provider.is_configured():
        job.status = "failed"
        job.error_code = "PROVIDER_UNCONFIGURED"
        job.safe_error_message = (
            f"The selected AI provider '{provider.get_provider_name()}' is not configured on this server. "
            f"Please set {provider.get_provider_name().upper()}_API_KEY or use procedural generation mode."
        )
        job.completed_at = datetime.datetime.utcnow()
        db.commit()
        return

    raw_params = json.loads(job.raw_parameters or "{}")

    # 1. Create task on provider
    if job.generation_mode == "ai_image":
        image_url = raw_params.get("image_url")
        task_id = provider.create_image_to_3d_task(image_url=image_url, prompt=job.prompt)
    else:
        task_id = provider.create_text_to_3d_task(prompt=job.prompt, style=raw_params.get("style"))

    job.provider_task_id = task_id
    job.progress = 20
    db.commit()

    # 2. Poll provider task until completion or timeout
    start_time = time.time()
    max_duration = 360 # 6 minutes max
    poll_interval = 4.0

    while time.time() - start_time < max_duration:
        if is_job_cancelled(job.id):
            job.status = "cancelled"
            job.completed_at = datetime.datetime.utcnow()
            db.commit()
            return

        time.sleep(poll_interval)
        status_info = provider.get_task_status(task_id)
        current_status = status_info.get("status")
        job.progress = max(20, min(95, status_info.get("progress", 20)))
        db.commit()

        if current_status == "completed":
            model_url = status_info.get("model_url")
            if not model_url:
                raise RuntimeError("Provider reported completion but gave no model URL.")

            # 3. Retrieve model bytes before URL expires
            model_bytes = provider.retrieve_completed_asset(model_url)

            # 4. Save to owned storage
            storage = get_storage_service()
            storage_key, file_size, checksum = storage.store_file(
                source_path_or_bytes=model_bytes,
                extension="glb",
                prefix=f"projects/{job.project_id or 'default'}"
            )

            # 5. Validate file
            local_path = storage.retrieve_file_path(storage_key)
            validation = validate_3d_asset_file(local_path, format_hint="glb")

            asset = Asset(
                owner_id=job.owner_id,
                project_id=job.project_id,
                source_job_id=job.id,
                storage_key=storage_key,
                mime_type="model/gltf-binary",
                file_size=file_size,
                file_checksum=checksum,
                file_format="glb",
                dimensions_json=json.dumps({"x": 1.0, "y": 1.0, "z": 1.0}),
                polygon_count=validation.get("primitive_count", 1) * 500,
                vertex_count=validation.get("mesh_count", 1) * 250,
                validation_status="valid" if validation.get("valid") else "failed",
                validation_report=json.dumps(validation)
            )
            db.add(asset)

            # Record usage
            usage_info = provider.get_usage_information()
            cost = usage_info.get("cost_per_preview_usd", 0.05)
            job.actual_cost_usd = cost

            ledger = UsageLedger(
                owner_id=job.owner_id,
                job_id=job.id,
                operation_type="ai_text_to_3d" if job.generation_mode == "ai_text" else "ai_image_to_3d",
                usage_units=1.0,
                cost_usd=cost
            )
            db.add(ledger)

            job.status = "completed"
            job.progress = 100
            job.completed_at = datetime.datetime.utcnow()
            db.commit()
            return

        elif current_status == "failed":
            job.status = "failed"
            job.error_code = "PROVIDER_TASK_FAILED"
            job.safe_error_message = status_info.get("error", "AI provider task failed.")
            job.completed_at = datetime.datetime.utcnow()
            db.commit()
            return

        poll_interval = min(10.0, poll_interval * 1.1)

    # Timed out
    job.status = "failed"
    job.error_code = "TIMEOUT"
    job.safe_error_message = f"AI Generation timed out after {max_duration} seconds."
    job.completed_at = datetime.datetime.utcnow()
    db.commit()

def _process_export_job(export_job_id: str):
    db: Session = SessionLocal()
    try:
        exp_job = db.query(ExportJob).filter(ExportJob.id == export_job_id).first()
        if not exp_job:
            return

        exp_job.status = "running"
        db.commit()

        asset = exp_job.asset
        storage = get_storage_service()
        src_path = storage.retrieve_file_path(asset.storage_key)

        req_fmt = exp_job.requested_format.lower()
        if req_fmt == "glb" and asset.file_format == "glb":
            # Already GLB, direct pass-through
            out_key, size, checksum = storage.store_file(src_path, "glb", prefix="exports")
            validation = validate_3d_asset_file(storage.retrieve_file_path(out_key), "glb")
        elif req_fmt in ("gltf_zip", "gltf") and asset.file_format == "glb":
            # Convert GLB to glTF ZIP package using Blender
            import tempfile
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_out = os.path.join(tmpdir, "package.zip")
                # Run blender import and re-export separate
                conv_script = (
                    "import bpy, sys\n"
                    f"bpy.ops.import_scene.gltf(filepath=r'{src_path}')\n"
                    "import os, zipfile\n"
                    f"tdir = r'{tmpdir}/extracted'\n"
                    "os.makedirs(tdir, exist_ok=True)\n"
                    f"gltf_p = os.path.join(tdir, 'model.gltf')\n"
                    "bpy.ops.export_scene.gltf(filepath=gltf_p, export_format='GLTF_SEPARATE', export_apply=True, export_materials='EXPORT', export_yup=True)\n"
                    f"with zipfile.ZipFile(r'{zip_out}', 'w', zipfile.ZIP_DEFLATED) as zf:\n"
                    "    for root, _, files in os.walk(tdir):\n"
                    "        for f in files:\n"
                    "            p = os.path.join(root, f)\n"
                    "            zf.write(p, arcname=os.path.relpath(p, tdir))\n"
                )
                runner = BlenderRunner()
                cmd = [runner.blender_path, "--background", "--python-expr", conv_script]
                import subprocess
                subprocess.run(cmd, check=True, timeout=60)

                out_key, size, checksum = storage.store_file(zip_out, "zip", prefix="exports")
                validation = validate_3d_asset_file(storage.retrieve_file_path(out_key), "gltf_zip")
        else:
            # Pass through current format
            out_key, size, checksum = storage.store_file(src_path, asset.file_format, prefix="exports")
            validation = validate_3d_asset_file(storage.retrieve_file_path(out_key), asset.file_format)

        exp_job.status = "completed"
        exp_job.output_storage_key = out_key
        exp_job.validation_report = json.dumps(validation)
        exp_job.completed_at = datetime.datetime.utcnow()
        db.commit()

    except Exception as e:
        logger.exception(f"Export job error: {e}")
        if exp_job:
            exp_job.status = "failed"
            exp_job.error_message = str(e)
            db.commit()
    finally:
        db.close()
