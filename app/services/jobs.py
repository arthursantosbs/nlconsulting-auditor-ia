from __future__ import annotations

import asyncio
import io
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.config import Settings
from app.models import DocumentResult, JobState
from app.services.anomalies import detect_anomalies
from app.services.exports import write_exports
from app.services.llm import LLMExtractionService
from app.services.parsing import (
    decode_text,
    fill_not_extracted,
    parse_key_value_pairs,
    validate_extracted_fields,
)


STRUCTURAL_WARNING_TOKENS = (
    "campo ausente",
    "truncado",
    "linha sem separador",
    "encoding",
)


def _has_structural_parse_issue(warnings: list[str]) -> bool:
    return any(
        token in warning.lower()
        for warning in warnings
        for token in STRUCTURAL_WARNING_TOKENS
    )


class JobManager:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.llm_service = LLMExtractionService(settings)
        self.jobs: dict[str, JobState] = {}
        self.job_dirs: dict[str, Path] = {}

    def create_job(self, uploads: list[tuple[str, bytes]]) -> JobState:
        job_id = uuid4().hex
        created_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
        state = JobState(
            job_id=job_id,
            created_at=created_at,
            status="queued",
            total_files=len(uploads),
            processed_files=0,
            progress_message="Fila criada. Preparando processamento.",
        )
        self.jobs[job_id] = state
        job_dir = self.settings.upload_root / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        self.job_dirs[job_id] = job_dir
        asyncio.create_task(self._process_job(job_id, uploads))
        return state

    def get_job(self, job_id: str) -> JobState | None:
        return self.jobs.get(job_id)

    def get_download_path(self, job_id: str, artifact: str) -> Path | None:
        job_dir = self.job_dirs.get(job_id)
        if not job_dir:
            return None
        candidate = job_dir / artifact
        if candidate.exists():
            return candidate
        return None

    async def _process_job(self, job_id: str, uploads: list[tuple[str, bytes]]) -> None:
        state = self.jobs[job_id]
        state.status = "processing"
        state.progress_message = "Lendo arquivos e iniciando extracao."

        try:
            tasks = [self._process_single_file(filename, content) for filename, content in uploads]
            for index, task in enumerate(asyncio.as_completed(tasks), start=1):
                result = await task
                state.documents.append(result)
                state.processed_files = index
                state.progress_message = f"Processados {index} de {state.total_files} arquivos."

            detect_anomalies(state.documents)
            exports = write_exports(self.job_dirs[job_id], state.documents)
            state.downloads = {
                name: f"/api/jobs/{job_id}/download/{path.name}" for name, path in exports.items()
            }
            state.status = "completed"
            state.completed_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
            state.progress_message = "Processamento concluido com sucesso."
        except Exception:
            state.status = "failed"
            state.error_message = "Falha interna no processamento do lote. Revise os arquivos e tente novamente."
            state.completed_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
            state.progress_message = "O processamento foi interrompido."

    async def _process_single_file(self, filename: str, content: bytes) -> DocumentResult:
        processed_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
        decoded = decode_text(content)
        parsed_fields, parse_warnings = parse_key_value_pairs(decoded.text)
        structural_warnings = decoded.warnings + parse_warnings

        if not _has_structural_parse_issue(structural_warnings):
            merged_fields = parsed_fields
            extraction_warnings = list(dict.fromkeys(structural_warnings))
            process_status = "processed"
            extraction_source = "parser_structured"
            provider = "structured-parser"
            confidence = "Alta"
        else:
            try:
                llm_result = await self.llm_service.extract(
                    filename=filename,
                    document_text=decoded.text,
                    preliminary_fields=parsed_fields,
                )
                merged_fields = {**parsed_fields, **llm_result.fields}
                extraction_warnings = list(
                    dict.fromkeys(structural_warnings + llm_result.warnings)
                )
                process_status = "processed" if llm_result.processable else "warning"
                extraction_source = llm_result.source
                provider = llm_result.provider
                confidence = llm_result.confidence
            except Exception:
                merged_fields = parsed_fields
                extraction_warnings = structural_warnings + [
                    "Falha ao consultar a API de IA; aplicado fallback seguro para continuar o lote."
                ]
                process_status = "warning" if not self.settings.ai_required else "failed"
                extraction_source = "parser_only"
                provider = "fallback-after-error"
                confidence = "Baixa"

        normalized_fields, missing_fields = fill_not_extracted(merged_fields)
        validation_warnings = validate_extracted_fields(normalized_fields)
        extraction_warnings = list(dict.fromkeys(extraction_warnings + validation_warnings))
        document = DocumentResult(
            file_name=filename,
            processed_at=processed_at,
            prompt_version=self.settings.prompt_version,
            extraction_source=extraction_source,
            provider=provider,
            encoding_used=decoded.encoding_used,
            process_status=process_status,
            extraction_confidence=confidence,
            fields=normalized_fields,
            missing_fields=missing_fields,
            warnings=extraction_warnings,
        )
        document.add_audit_entry(
            event_type="file_processed",
            rule="document-ingestion",
            outcome=process_status,
            confidence=confidence,
            details="Arquivo lido, decodificado e submetido ao pipeline de extracao.",
            evidence_fields=["encoding", "prompt_version"],
        )
        return document

    async def process_uploads(
        self,
        uploads: list[tuple[str, bytes]],
        *,
        detect_batch_anomalies: bool = True,
    ) -> list[DocumentResult]:
        documents: list[DocumentResult] = []
        tasks = [self._process_single_file(filename, content) for filename, content in uploads]
        for task in asyncio.as_completed(tasks):
            documents.append(await task)
        if detect_batch_anomalies:
            detect_anomalies(documents)
        return documents


def expand_uploads(
    files: list[tuple[str, bytes]],
    *,
    max_files: int,
) -> list[tuple[str, bytes]]:
    expanded: list[tuple[str, bytes]] = []
    for filename, content in files:
        lower_name = filename.lower()
        if lower_name.endswith(".zip"):
            try:
                with zipfile.ZipFile(io.BytesIO(content)) as archive:
                    for member in archive.infolist():
                        if member.is_dir():
                            continue
                        if not member.filename.lower().endswith(".txt"):
                            continue
                        expanded.append((Path(member.filename).name, archive.read(member)))
            except zipfile.BadZipFile as exc:
                raise ValueError(f"Arquivo ZIP invalido ou corrompido: {filename}") from exc
        elif lower_name.endswith(".txt"):
            expanded.append((filename, content))
        else:
            raise ValueError(f"Tipo de arquivo nao suportado: {filename}")

        if len(expanded) > max_files:
            raise ValueError(f"O lote excede o limite de {max_files} arquivos.")

    if not expanded:
        raise ValueError("Nenhum arquivo .txt valido foi encontrado para processamento.")
    return expanded
