from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.services.jobs import JobManager, expand_uploads


app = FastAPI(title=settings.app_name, version=settings.app_version)
job_manager = JobManager(settings)

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
async def healthcheck() -> dict:
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "ai_enabled": settings.ai_enabled,
        "provider": settings.ai_provider_label,
    }


@app.post("/api/jobs")
async def create_job(files: list[UploadFile] = File(...)) -> JSONResponse:
    if not files:
        raise HTTPException(status_code=400, detail="Envie ao menos um arquivo ZIP ou TXT.")

    loaded_files: list[tuple[str, bytes]] = []
    max_bytes = settings.max_upload_mb * 1024 * 1024

    for upload in files:
        content = await upload.read()
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"O arquivo {upload.filename} ultrapassa o limite de {settings.max_upload_mb} MB.",
            )
        loaded_files.append((upload.filename or "arquivo.txt", content))

    try:
        expanded = expand_uploads(loaded_files, max_files=settings.max_files_per_job)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    state = job_manager.create_job(expanded)
    return JSONResponse(state.to_dict())


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str) -> JSONResponse:
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job nao encontrado.")
    return JSONResponse(job.to_dict())


@app.get("/api/jobs/{job_id}/download/{artifact}")
async def download_artifact(job_id: str, artifact: str) -> FileResponse:
    if Path(artifact).name != artifact:
        raise HTTPException(status_code=400, detail="Nome de artefato invalido.")
    path = job_manager.get_download_path(job_id, artifact)
    if not path:
        raise HTTPException(status_code=404, detail="Arquivo de download nao encontrado.")
    return FileResponse(path, filename=path.name, media_type="application/octet-stream")
