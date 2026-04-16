from __future__ import annotations

import csv
from pathlib import Path

from openpyxl import Workbook

from app.models import DocumentResult


def write_exports(job_dir: Path, documents: list[DocumentResult]) -> dict[str, Path]:
    summary_rows = [document.summary_row() for document in documents]
    anomaly_rows = [row for document in documents for row in document.anomaly_rows()]
    audit_rows = [entry.to_dict() for document in documents for entry in document.audit_log]

    results_csv = job_dir / "results.csv"
    anomalies_csv = job_dir / "anomalies.csv"
    audit_csv = job_dir / "audit_log.csv"
    workbook_path = job_dir / "results.xlsx"

    _write_csv(results_csv, summary_rows)
    _write_csv(anomalies_csv, anomaly_rows)
    _write_csv(audit_csv, audit_rows)
    _write_workbook(workbook_path, summary_rows, anomaly_rows, audit_rows)

    return {
        "results_csv": results_csv,
        "anomalies_csv": anomalies_csv,
        "audit_log_csv": audit_csv,
        "results_xlsx": workbook_path,
    }


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        rows = [{"status": "sem_dados"}]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_workbook(
    workbook_path: Path,
    summary_rows: list[dict],
    anomaly_rows: list[dict],
    audit_rows: list[dict],
) -> None:
    workbook = Workbook()
    sheets = [
        ("documents", summary_rows),
        ("anomalies", anomaly_rows),
        ("audit_log", audit_rows),
    ]

    for index, (title, rows) in enumerate(sheets):
        worksheet = workbook.active if index == 0 else workbook.create_sheet()
        worksheet.title = title
        dataset = rows or [{"status": "sem_dados"}]
        headers = list(dataset[0].keys())
        worksheet.append(headers)
        for row in dataset:
            worksheet.append([row.get(header, "") for header in headers])
        worksheet.freeze_panes = "A2"
    workbook.save(workbook_path)
