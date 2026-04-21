from __future__ import annotations

import argparse
import asyncio
import json
import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings
from app.services.anomalies import detect_anomalies
from app.services.exports import write_exports
from app.services.jobs import JobManager, expand_uploads


def _batched(items: list[tuple[str, bytes]], chunk_size: int) -> list[list[tuple[str, bytes]]]:
    return [items[index : index + chunk_size] for index in range(0, len(items), chunk_size)]


def _write_progress(
    path: Path,
    *,
    status: str,
    total_documents: int,
    processed_documents: int,
    current_chunk: int,
    total_chunks: int,
    output_dir: Path,
) -> None:
    payload = {
        "status": status,
        "total_documents": total_documents,
        "processed_documents": processed_documents,
        "current_chunk": current_chunk,
        "total_chunks": total_chunks,
        "output_dir": str(output_dir),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


async def _process_in_chunks(
    manager: JobManager,
    uploads: list[tuple[str, bytes]],
    *,
    chunk_size: int,
    pause_seconds: float,
    progress_path: Path,
    job_dir: Path,
) -> list:
    chunks = _batched(uploads, chunk_size)
    documents = []
    total_documents = len(uploads)
    total_chunks = len(chunks)

    for index, chunk in enumerate(chunks, start=1):
        _write_progress(
            progress_path,
            status="processing",
            total_documents=total_documents,
            processed_documents=len(documents),
            current_chunk=index,
            total_chunks=total_chunks,
            output_dir=job_dir,
        )
        chunk_documents = await manager.process_uploads(chunk, detect_batch_anomalies=False)
        documents.extend(chunk_documents)
        print(
            (
                f"Chunk {index}/{total_chunks} concluido. "
                f"Arquivos no chunk: {len(chunk_documents)} | "
                f"Acumulado: {len(documents)}/{total_documents}"
            ),
            flush=True,
        )
        _write_progress(
            progress_path,
            status="processing",
            total_documents=total_documents,
            processed_documents=len(documents),
            current_chunk=index,
            total_chunks=total_chunks,
            output_dir=job_dir,
        )
        if pause_seconds > 0 and index < total_chunks:
            await asyncio.sleep(pause_seconds)

    detect_anomalies(documents)
    return documents


async def main() -> None:
    parser = argparse.ArgumentParser(description="Processa um lote local de documentos financeiros.")
    parser.add_argument("input_path", help="Caminho para um arquivo .zip ou .txt")
    parser.add_argument(
        "--output-dir",
        default="manual_runs",
        help="Diretorio onde os artefatos exportados serao salvos",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=0,
        help="Quantidade de arquivos por lote interno. Use para dividir cargas grandes e consolidar no final.",
    )
    parser.add_argument(
        "--pause-seconds",
        type=float,
        default=0.0,
        help="Pausa opcional entre chunks para reduzir pressao sobre a API.",
    )
    args = parser.parse_args()
    if args.chunk_size < 0:
        raise SystemExit("--chunk-size nao pode ser negativo.")
    if args.pause_seconds < 0:
        raise SystemExit("--pause-seconds nao pode ser negativo.")

    input_path = Path(args.input_path).expanduser().resolve()
    if not input_path.exists():
        raise SystemExit(f"Arquivo de entrada nao encontrado: {input_path}")

    uploads = expand_uploads(
        [(input_path.name, input_path.read_bytes())],
        max_files=settings.max_files_per_job,
    )

    output_root = Path(args.output_dir).expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    job_dir = output_root / input_path.stem
    job_dir.mkdir(parents=True, exist_ok=True)
    progress_path = job_dir / "progress.json"

    manager = JobManager(settings)
    try:
        if args.chunk_size > 0 and len(uploads) > args.chunk_size:
            total_chunks = math.ceil(len(uploads) / args.chunk_size)
            print(
                (
                    f"Processamento em chunks ativado. "
                    f"Arquivos: {len(uploads)} | Chunk size: {args.chunk_size} | Chunks: {total_chunks}"
                ),
                flush=True,
            )
            documents = await _process_in_chunks(
                manager,
                uploads,
                chunk_size=args.chunk_size,
                pause_seconds=args.pause_seconds,
                progress_path=progress_path,
                job_dir=job_dir,
            )
        else:
            _write_progress(
                progress_path,
                status="processing",
                total_documents=len(uploads),
                processed_documents=0,
                current_chunk=1,
                total_chunks=1,
                output_dir=job_dir,
            )
            documents = await manager.process_uploads(uploads)
            print(f"Processamento concluido em lote unico com {len(documents)} arquivos.", flush=True)

        documents.sort(key=lambda document: document.file_name.lower())
        exports = write_exports(job_dir, documents)
        total_chunks = max(1, math.ceil(len(uploads) / args.chunk_size)) if args.chunk_size > 0 else 1
        _write_progress(
            progress_path,
            status="completed",
            total_documents=len(uploads),
            processed_documents=len(documents),
            current_chunk=total_chunks,
            total_chunks=total_chunks,
            output_dir=job_dir,
        )
    except Exception:
        total_chunks = max(1, math.ceil(len(uploads) / args.chunk_size)) if args.chunk_size > 0 else 1
        processed_documents = 0
        current_chunk = 1
        if progress_path.exists():
            try:
                current_progress = json.loads(progress_path.read_text(encoding="utf-8"))
                processed_documents = int(current_progress.get("processed_documents", 0))
                current_chunk = int(current_progress.get("current_chunk", 1))
            except (OSError, ValueError, json.JSONDecodeError, TypeError):
                pass
        _write_progress(
            progress_path,
            status="failed",
            total_documents=len(uploads),
            processed_documents=processed_documents,
            current_chunk=current_chunk,
            total_chunks=total_chunks,
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
