from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any


EXPECTED_FIELDS = [
    "tipo_documento",
    "numero_documento",
    "data_emissao",
    "fornecedor",
    "cnpj_fornecedor",
    "descricao_servico",
    "valor_bruto",
    "data_pagamento",
    "data_emissao_nf",
    "aprovado_por",
    "banco_destino",
    "status",
    "hash_verificacao",
]


@dataclass
class AnomalyRecord:
    code: str
    label: str
    severity: str
    confidence: str
    rule: str
    evidence_fields: list[str]
    evidence_values: dict[str, str]
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AuditLogEntry:
    file_name: str
    timestamp: str
    event_type: str
    rule: str
    outcome: str
    confidence: str
    prompt_version: str
    evidence_fields: str
    details: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DocumentResult:
    file_name: str
    processed_at: str
    prompt_version: str
    extraction_source: str
    provider: str
    encoding_used: str
    process_status: str
    extraction_confidence: str
    fields: dict[str, str]
    missing_fields: list[str]
    warnings: list[str]
    anomalies: list[AnomalyRecord] = field(default_factory=list)
    audit_log: list[AuditLogEntry] = field(default_factory=list)

    def add_audit_entry(
        self,
        *,
        event_type: str,
        rule: str,
        outcome: str,
        confidence: str,
        details: str,
        evidence_fields: list[str] | None = None,
    ) -> None:
        self.audit_log.append(
            AuditLogEntry(
                file_name=self.file_name,
                timestamp=datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
                event_type=event_type,
                rule=rule,
                outcome=outcome,
                confidence=confidence,
                prompt_version=self.prompt_version,
                evidence_fields=", ".join(evidence_fields or []),
                details=details,
            )
        )

    def add_anomaly(self, anomaly: AnomalyRecord) -> None:
        if any(existing.code == anomaly.code for existing in self.anomalies):
            return
        self.anomalies.append(anomaly)
        self.add_audit_entry(
            event_type="anomaly_detected",
            rule=anomaly.rule,
            outcome=anomaly.label,
            confidence=anomaly.confidence,
            details=anomaly.message,
            evidence_fields=anomaly.evidence_fields,
        )

    def summary_row(self) -> dict[str, Any]:
        row = {
            "file_name": self.file_name,
            "processed_at": self.processed_at,
            "prompt_version": self.prompt_version,
            "extraction_source": self.extraction_source,
            "provider": self.provider,
            "encoding_used": self.encoding_used,
            "process_status": self.process_status,
            "extraction_confidence": self.extraction_confidence,
            "missing_fields": ", ".join(self.missing_fields),
            "warnings": " | ".join(self.warnings),
            "anomaly_count": len(self.anomalies),
            "anomaly_types": ", ".join(anomaly.label for anomaly in self.anomalies),
            "is_suspect": "SIM" if self.anomalies else "NAO",
        }
        for field_name in EXPECTED_FIELDS:
            row[field_name] = self.fields.get(field_name, "nao extraido")
        return row

    def anomaly_rows(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for anomaly in self.anomalies:
            rows.append(
                {
                    "file_name": self.file_name,
                    "numero_documento": self.fields.get("numero_documento", "nao extraido"),
                    "fornecedor": self.fields.get("fornecedor", "nao extraido"),
                    "tipo_anomalia": anomaly.label,
                    "codigo_anomalia": anomaly.code,
                    "gravidade": anomaly.severity,
                    "confianca": anomaly.confidence,
                    "regra": anomaly.rule,
                    "campos_evidencia": ", ".join(anomaly.evidence_fields),
                    "valores_evidencia": " | ".join(
                        f"{key}={value}" for key, value in anomaly.evidence_values.items()
                    ),
                    "mensagem": anomaly.message,
                    "processed_at": self.processed_at,
                }
            )
        return rows

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_name": self.file_name,
            "processed_at": self.processed_at,
            "prompt_version": self.prompt_version,
            "extraction_source": self.extraction_source,
            "provider": self.provider,
            "encoding_used": self.encoding_used,
            "process_status": self.process_status,
            "extraction_confidence": self.extraction_confidence,
            "fields": self.fields,
            "missing_fields": self.missing_fields,
            "warnings": self.warnings,
            "anomalies": [item.to_dict() for item in self.anomalies],
        }


@dataclass
class JobState:
    job_id: str
    created_at: str
    status: str
    total_files: int
    processed_files: int
    progress_message: str
    documents: list[DocumentResult] = field(default_factory=list)
    downloads: dict[str, str] = field(default_factory=dict)
    error_message: str | None = None
    completed_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        anomalies = sum(len(document.anomalies) for document in self.documents)
        failed = sum(document.process_status != "processed" for document in self.documents)
        return {
            "job_id": self.job_id,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "status": self.status,
            "total_files": self.total_files,
            "processed_files": self.processed_files,
            "progress_message": self.progress_message,
            "error_message": self.error_message,
            "summary": {
                "documents": len(self.documents),
                "anomalies": anomalies,
                "failed_or_warning": failed,
                "encoding_issues": sum(
                    1
                    for document in self.documents
                    if any("encoding" in warning.lower() for warning in document.warnings)
                ),
            },
            "downloads": self.downloads,
            "documents": [document.to_dict() for document in self.documents],
        }
