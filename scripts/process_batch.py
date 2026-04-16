from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings
from app.services.exports import write_exports
from app.services.jobs import JobManager, expand_uploads


async def main() -> None:
    parser = argparse.ArgumentParser(description="Processa um lote local de documentos financeiros.")
    parser.add_argument("input_path", help="Caminho para um arquivo .zip ou .txt")
    parser.add_argument(
        "--output-dir",
        default="manual_runs",
        help="Diretorio onde os artefatos exportados serao salvos",
    )
    args = parser.parse_args()

    input_path = Path(args.input_path).expanduser().resolve()
    if not input_path.exists():
        raise SystemExit(f"Arquivo de entrada nao encontrado: {input_path}")

    uploads = expand_uploads(
        [(input_path.name, input_path.read_bytes())],
        max_files=settings.max_files_per_job,
    )

    manager = JobManager(settings)
    documents = await manager.process_uploads(uploads)

    output_root = Path(args.output_dir).expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    job_dir = output_root / input_path.stem
    job_dir.mkdir(parents=True, exist_ok=True)
    exports = write_exports(job_dir, documents)

    print(f"Lote processado: {input_path}")
    print(f"Arquivos analisados: {len(documents)}")
    print(f"Anomalias detectadas: {sum(len(document.anomalies) for document in documents)}")
    print("Artefatos gerados:")
    for name, path in exports.items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    asyncio.run(main())
