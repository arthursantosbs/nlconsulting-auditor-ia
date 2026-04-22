from __future__ import annotations

import argparse
import asyncio
import json
import math
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings
from app.models import DocumentResult
from app.services.anomalies import detect_anomalies
from app.services.exports import write_exports
from app.services.jobs import expand_uploads
from app.services.llm import LLMExtractionResult, LLMExtractionService
from app.services.parsing import (
    decode_text,
    fill_not_extracted,
    parse_key_value_pairs,
    validate_extracted_fields,
)


@dataclass
class PreparedUpload:
    file_name: str
    document_text: str
    encoding_used: str
    decoded_warnings: list[str]
    parsed_fields: dict[str, str]
    parse_warnings: list[str]


def _batched(items: list, batch_size: int) -> list[list]:
    return [items[index : index + batch_size] for index in range(0, len(items), batch_size)]


def _write_progress(
    path: Path,
    *,
    status: str,
    total_documents: int,
    processed_documents: int,
    current_group: int,
    total_groups: int,
    output_dir: Path,
) -> None:
    payload = {
        "status": status,
        "total_documents": total_documents,
        "processed_documents": processed_documents,
        "current_group": current_group,
        "total_groups": total_groups,
        "output_dir": str(output_dir),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _prepare_uploads(uploads: list[tuple[str, bytes]]) -> list[PreparedUpload]:
    prepared: list[PreparedUpload] = []
    for file_name, content in uploads:
        decoded = decode_text(content)
        parsed_fields, parse_warnings = parse_key_value_pairs(decoded.text)
        prepared.append(
            PreparedUpload(
                file_name=file_name,
                document_text=decoded.text,
                encoding_used=decoded.encoding_used,
                decoded_warnings=decoded.warnings,
                parsed_fields=parsed_fields,
                parse_warnings=parse_warnings,
            )
        )
    return prepared


def _build_document_result(
    upload: PreparedUpload,
    *,
    llm_result: LLMExtractionResult | None,
    prompt_version: str,
) -> DocumentResult:
    if llm_result is None:
        merged_fields = upload.parsed_fields
        extraction_warnings = upload.decoded_warnings + upload.parse_warnings + [
            "Falha ao consultar a API de IA em lote; aplicado fallback seguro para continuar o processamento."
        ]
        process_status = "warning" if not settings.ai_required else "failed"
        extraction_source = "parser_only"
        provider = "fallback-after-error"
        confidence = "Baixa"
    else:
        merged_fields = {**upload.parsed_fields, **llm_result.fields}
        extraction_warnings = list(
            dict.fromkeys(upload.decoded_warnings + upload.parse_warnings + llm_result.warnings)
        )
        process_status = "processed" if llm_result.processable else "warning"
        extraction_source = llm_result.source
        provider = llm_result.provider
        confidence = llm_result.confidence

    normalized_fields, missing_fields = fill_not_extracted(merged_fields)
    validation_warnings = validate_extracted_fields(normalized_fields)
    extraction_warnings = list(dict.fromkeys(extraction_warnings + validation_warnings))
    document = DocumentResult(
        file_name=upload.file_name,
        processed_at=datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        prompt_version=prompt_version,
        extraction_source=extraction_source,
        provider=provider,
        encoding_used=upload.encoding_used,
        process_status=process_status,
        extraction_confidence=confidence,
        fields=normalized_fields,
        missing_fields=missing_fields,
        warnings=extraction_warnings,
    )
    document.add_audit_entry(
        event_type="file_processed",
        rule="document-ingestion-batch-llm",
        outcome=process_status,
        confidence=confidence,
        details="Arquivo lido, decodificado e submetido ao pipeline de extracao em lote.",
        evidence_fields=["encoding", "prompt_version", "batch_mode"],
    )
    return document


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Processa um lote local agrupando varios documentos por request de IA."
    )
    parser.add_argument("input_path", help="Caminho para um arquivo .zip ou .txt")
    parser.add_argument(
        "--output-dir",
        default="manual_runs",
        help="Diretorio onde os artefatos exportados serao salvos",
    )
    parser.add_argument(
        "--request-batch-size",
        type=int,
        default=5,
        help="Quantidade de documentos enviados em cada request de IA",
    )
    args = parser.parse_args()

    if args.request_batch_size <= 0:
        raise SystemExit("--request-batch-size deve ser maior que zero.")

    input_path = Path(args.input_path).expanduser().resolve()
    if not input_path.exists():
        raise SystemExit(f"Arquivo de entrada nao encontrado: {input_path}")

    uploads = expand_uploads(
        [(input_path.name, input_path.read_bytes())],
        max_files=settings.max_files_per_job,
    )
    prepared_uploads = _prepare_uploads(uploads)

    output_root = Path(args.output_dir).expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    job_dir = output_root / input_path.stem
    job_dir.mkdir(parents=True, exist_ok=True)
    progress_path = job_dir / "progress.json"

    llm_service = LLMExtractionService(settings)
    prompt_version = f"{settings.prompt_version}-batch{args.request_batch_size}"
    groups = _batched(prepared_uploads, args.request_batch_size)
    total_groups = len(groups)
    documents: list[DocumentResult] = []
    processed_documents = 0

    try:
        print(
            (
                f"Processamento LLM em lote ativado. "
                f"Arquivos: {len(prepared_uploads)} | Batch size: {args.request_batch_size} | Grupos: {total_groups}"
            ),
            flush=True,
        )
        for index, group in enumerate(groups, start=1):
            _write_progress(
                progress_path,
                status="processing",
                total_documents=len(prepared_uploads),
                processed_documents=processed_documents,
                current_group=index,
                total_groups=total_groups,
                output_dir=job_dir,
            )
            llm_results: dict[str, LLMExtractionResult]
            try:
                llm_results = await llm_service.extract_batch(
                    documents=[(item.file_name, item.document_text) for item in group]
                )
            except Exception:
                llm_results = {}

            for item in group:
                documents.append(
                    _build_document_result(
                        item,
                        llm_result=llm_results.get(item.file_name),
                        prompt_version=prompt_version,
                    )
                )

            processed_documents = len(documents)
            print(
                (
                    f"Grupo {index}/{total_groups} concluido. "
                    f"Arquivos no grupo: {len(group)} | "
                    f"Acumulado: {processed_documents}/{len(prepared_uploads)}"
                ),
                flush=True,
            )
            _write_progress(
                progress_path,
                status="processing",
                total_documents=len(prepared_uploads),
                processed_documents=processed_documents,
                current_group=index,
                total_groups=total_groups,
                output_dir=job_dir,
            )

        documents.sort(key=lambda document: document.file_name.lower())
        detect_anomalies(documents)
        exports = write_exports(job_dir, documents)
        _write_progress(
            progress_path,
            status="completed",
            total_documents=len(prepared_uploads),
            processed_documents=len(documents),
            current_group=total_groups,
            total_groups=total_groups,
            output_dir=job_dir,
        )
    except Exception:
        _write_progress(
            progress_path,
            status="failed",
            total_documents=len(prepared_uploads),
            processed_documents=processed_documents,
            current_group=min(total_groups, math.floor(processed_documents / args.request_batch_size) + 1),
            total_groups=total_groups,
            output_dir=job_dir,
        )
        raise

    print(f"Lote processado: {input_path}")
    print(f"Arquivos analisados: {len(documents)}")
    print(f"Anomalias detectadas: {sum(len(document.anomalies) for document in documents)}")
    print(f"Progresso consolidado: {progress_path}")
    print("Artefatos gerados:")
    for name, path in exports.items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    asyncio.run(main())
