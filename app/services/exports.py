from __future__ import annotations

import csv
import json
from pathlib import Path

from openpyxl import Workbook

from app.models import DocumentResult


def _has_processing_alert(document: DocumentResult) -> bool:
    return document.process_status != "processed" or any(
        anomaly.code == "FILE_PROCESSING_ISSUE" for anomaly in document.anomalies
    )


def write_exports(job_dir: Path, documents: list[DocumentResult]) -> dict[str, Path]:
    summary_rows = [document.summary_row() for document in documents]
    anomaly_rows = [row for document in documents for row in document.anomaly_rows()]
    audit_rows = [entry.to_dict() for document in documents for entry in document.audit_log]

    results_csv = job_dir / "results.csv"
    anomalies_csv = job_dir / "anomalies.csv"
    audit_csv = job_dir / "audit_log.csv"
    workbook_path = job_dir / "results.xlsx"
    summary_json = job_dir / "summary.json"
    anomaly_report = job_dir / "anomaly_report.md"

    _write_csv(results_csv, summary_rows)
    _write_csv(anomalies_csv, anomaly_rows)
    _write_csv(audit_csv, audit_rows)
    _write_workbook(workbook_path, summary_rows, anomaly_rows, audit_rows)
    _write_summary_json(summary_json, documents)
    _write_anomaly_report(anomaly_report, documents)

    return {
        "results_csv": results_csv,
        "anomalies_csv": anomalies_csv,
        "audit_log_csv": audit_csv,
        "results_xlsx": workbook_path,
        "summary_json": summary_json,
        "anomaly_report_md": anomaly_report,
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


def _write_summary_json(path: Path, documents: list[DocumentResult]) -> None:
    summary = {
        "documents": len(documents),
        "processed": sum(document.process_status == "processed" for document in documents),
        "warnings_or_failures": sum(_has_processing_alert(document) for document in documents),
        "processing_alerts": sum(_has_processing_alert(document) for document in documents),
        "anomalies": sum(len(document.anomalies) for document in documents),
        "by_anomaly": {},
        "by_supplier": {},
    }

    for document in documents:
        supplier = document.fields.get("fornecedor", "nao extraido")
        summary["by_supplier"].setdefault(supplier, 0)
        summary["by_supplier"][supplier] += len(document.anomalies)
        for anomaly in document.anomalies:
            summary["by_anomaly"].setdefault(anomaly.label, 0)
            summary["by_anomaly"][anomaly.label] += 1

    with path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)


def _write_anomaly_report(path: Path, documents: list[DocumentResult]) -> None:
    total_docs = len(documents)
    total_anomalies = sum(len(document.anomalies) for document in documents)
    processing_alerts = sum(_has_processing_alert(document) for document in documents)
    anomaly_counts: dict[str, int] = {}
    supplier_counts: dict[str, int] = {}

    for document in documents:
        supplier = document.fields.get("fornecedor", "nao extraido")
        supplier_counts.setdefault(supplier, 0)
        supplier_counts[supplier] += len(document.anomalies)
        for anomaly in document.anomalies:
            anomaly_counts.setdefault(anomaly.label, 0)
            anomaly_counts[anomaly.label] += 1

    sorted_anomalies = sorted(anomaly_counts.items(), key=lambda item: (-item[1], item[0]))
    sorted_suppliers = sorted(supplier_counts.items(), key=lambda item: (-item[1], item[0]))
    top_documents = sorted(
        documents,
        key=lambda document: (-len(document.anomalies), document.file_name.lower()),
    )[:10]

    lines = [
        "# Relatorio de Anomalias",
        "",
        f"- Total de arquivos processados: **{total_docs}**",
        f"- Total de anomalias detectadas: **{total_anomalies}**",
        f"- Arquivos com alerta de processamento: **{processing_alerts}**",
        "",
        "## Anomalias por tipo",
        "",
    ]

    if sorted_anomalies:
        lines.extend([f"- {label}: **{count}**" for label, count in sorted_anomalies])
    else:
        lines.append("- Nenhuma anomalia detectada.")

    lines.extend(["", "## Fornecedores com mais ocorrencias", ""])
    lines.extend([f"- {supplier}: **{count}**" for supplier, count in sorted_suppliers[:10] if count > 0] or ["- Sem ocorrencias concentradas."])

    lines.extend(["", "## Top arquivos para revisao", ""])
    for document in top_documents:
        if not document.anomalies:
            continue
        lines.append(
            f"- `{document.file_name}` | fornecedor: **{document.fields.get('fornecedor', 'nao extraido')}** | anomalias: **{len(document.anomalies)}**"
        )
    if all(not document.anomalies for document in top_documents):
        lines.append("- Nenhum arquivo critico para revisao manual.")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
