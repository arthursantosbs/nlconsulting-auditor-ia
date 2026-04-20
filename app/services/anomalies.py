from __future__ import annotations

from collections import Counter, defaultdict
from decimal import Decimal

from app.models import AnomalyRecord, DocumentResult
from app.services.parsing import parse_currency_to_decimal, parse_date


def _quartiles(values: list[Decimal]) -> tuple[Decimal, Decimal]:
    ordered = sorted(values)
    mid = len(ordered) // 2
    lower = ordered[:mid]
    upper = ordered[mid + (0 if len(ordered) % 2 == 0 else 1) :]
    q1 = lower[len(lower) // 2] if lower else ordered[0]
    q3 = upper[len(upper) // 2] if upper else ordered[-1]
    return q1, q3


def detect_anomalies(documents: list[DocumentResult]) -> None:
    supplier_counts = Counter()
    approver_counts = Counter()
    supplier_cnpjs: dict[str, Counter[str]] = defaultdict(Counter)
    supplier_values: dict[str, list[Decimal]] = defaultdict(list)
    duplicates = Counter()

    for document in documents:
        supplier = document.fields.get("fornecedor", "nao extraido")
        approver = document.fields.get("aprovado_por", "nao extraido")
        cnpj = document.fields.get("cnpj_fornecedor", "nao extraido")
        number = document.fields.get("numero_documento", "nao extraido")

        if supplier != "nao extraido":
            supplier_counts[supplier] += 1
        if approver != "nao extraido":
            approver_counts[approver] += 1
        if supplier != "nao extraido" and cnpj != "nao extraido":
            supplier_cnpjs[supplier][cnpj] += 1
        if supplier != "nao extraido":
            value = parse_currency_to_decimal(document.fields.get("valor_bruto", ""))
            if value is not None:
                supplier_values[supplier].append(value)
        if supplier != "nao extraido" and number != "nao extraido":
            duplicates[(supplier, number)] += 1

    canonical_cnpj = {
        supplier: values.most_common(1)[0][0] for supplier, values in supplier_cnpjs.items() if values
    }

    for document in documents:
        _detect_file_process_issues(document)
        _detect_duplicate_nf(document, duplicates)
        _detect_cnpj_divergence(document, canonical_cnpj, supplier_counts)
        _detect_supplier_without_history(document, supplier_counts)
        _detect_issue_after_payment(document)
        _detect_value_outlier(document, supplier_values)
        _detect_approver(document, approver_counts)
        _detect_status_inconsistency(document)


def _detect_file_process_issues(document: DocumentResult) -> None:
    technical_issue = any(
        token in warning.lower()
        for warning in document.warnings
        for token in (
            "encoding",
            "campo ausente",
            "truncado",
            "invalido",
            "fora do dominio esperado",
            "linha sem separador",
        )
    )
    if document.process_status != "processed" or document.missing_fields or technical_issue:
        document.add_anomaly(
            AnomalyRecord(
                code="FILE_PROCESSING_ISSUE",
                label="Arquivo nao processavel",
                severity="Media",
                confidence="Alta",
                rule="encoding-invalid-or-fields-missing",
                evidence_fields=document.missing_fields[:5] or ["warnings"],
                evidence_values={
                    "missing_fields": ", ".join(document.missing_fields) or "nenhum",
                    "warnings": " | ".join(document.warnings) or "nenhum",
                },
                message="O arquivo apresentou problemas de encoding, campos ausentes ou extracao incompleta.",
            )
        )


def _detect_duplicate_nf(document: DocumentResult, duplicates: Counter[tuple[str, str]]) -> None:
    supplier = document.fields.get("fornecedor", "nao extraido")
    number = document.fields.get("numero_documento", "nao extraido")
    if supplier == "nao extraido" or number == "nao extraido":
        return
    if duplicates[(supplier, number)] > 1:
        document.add_anomaly(
            AnomalyRecord(
                code="DUPLICATE_NF",
                label="NF duplicada",
                severity="Alta",
                confidence="Alta",
                rule="same-document-number-same-supplier",
                evidence_fields=["fornecedor", "numero_documento"],
                evidence_values={"fornecedor": supplier, "numero_documento": number},
                message="Mesmo numero de NF apareceu mais de uma vez para o mesmo fornecedor.",
            )
        )


def _detect_cnpj_divergence(
    document: DocumentResult,
    canonical_cnpj: dict[str, str],
    supplier_counts: Counter[str],
) -> None:
    supplier = document.fields.get("fornecedor", "nao extraido")
    cnpj = document.fields.get("cnpj_fornecedor", "nao extraido")
    if supplier_counts[supplier] <= 1 or cnpj == "nao extraido":
        return
    expected = canonical_cnpj.get(supplier)
    if expected and expected != cnpj:
        document.add_anomaly(
            AnomalyRecord(
                code="CNPJ_DIVERGENCE",
                label="CNPJ divergente",
                severity="Alta",
                confidence="Alta",
                rule="supplier-cnpj-profile-mismatch",
                evidence_fields=["fornecedor", "cnpj_fornecedor"],
                evidence_values={"fornecedor": supplier, "cnpj_documento": cnpj, "cnpj_esperado": expected},
                message="O CNPJ deste documento difere do padrao historico do fornecedor.",
            )
        )


def _detect_supplier_without_history(document: DocumentResult, supplier_counts: Counter[str]) -> None:
    supplier = document.fields.get("fornecedor", "nao extraido")
    if supplier == "nao extraido":
        return
    if supplier_counts[supplier] == 1:
        document.add_anomaly(
            AnomalyRecord(
                code="SUPPLIER_WITHOUT_HISTORY",
                label="Fornecedor sem historico",
                severity="Alta",
                confidence="Media",
                rule="supplier-appears-once-in-batch",
                evidence_fields=["fornecedor"],
                evidence_values={"fornecedor": supplier},
                message="O fornecedor nao aparece em nenhum outro documento do lote.",
            )
        )


def _detect_issue_after_payment(document: DocumentResult) -> None:
    issue_date = parse_date(document.fields.get("data_emissao_nf", ""))
    payment_date = parse_date(document.fields.get("data_pagamento", ""))
    if issue_date and payment_date and issue_date > payment_date:
        document.add_anomaly(
            AnomalyRecord(
                code="ISSUED_AFTER_PAYMENT",
                label="NF emitida apos pagamento",
                severity="Alta",
                confidence="Alta",
                rule="invoice-date-greater-than-payment-date",
                evidence_fields=["data_emissao_nf", "data_pagamento"],
                evidence_values={
                    "data_emissao_nf": document.fields.get("data_emissao_nf", ""),
                    "data_pagamento": document.fields.get("data_pagamento", ""),
                },
                message="A data de emissao da NF e posterior a data de pagamento.",
            )
        )


def _detect_value_outlier(document: DocumentResult, supplier_values: dict[str, list[Decimal]]) -> None:
    supplier = document.fields.get("fornecedor", "nao extraido")
    value = parse_currency_to_decimal(document.fields.get("valor_bruto", ""))
    values = supplier_values.get(supplier, [])
    if supplier == "nao extraido" or value is None or len(values) < 4:
        return
    q1, q3 = _quartiles(values)
    iqr = q3 - q1
    lower = q1 - (iqr * Decimal("1.5"))
    upper = q3 + (iqr * Decimal("1.5"))
    if value < lower or value > upper:
        document.add_anomaly(
            AnomalyRecord(
                code="VALUE_OUTLIER",
                label="Valor fora da faixa do fornecedor",
                severity="Media",
                confidence="Media",
                rule="supplier-interquartile-range",
                evidence_fields=["fornecedor", "valor_bruto"],
                evidence_values={
                    "fornecedor": supplier,
                    "valor_bruto": document.fields.get("valor_bruto", ""),
                    "faixa_esperada": f"{lower:.2f} ate {upper:.2f}",
                },
                message="O valor bruto ficou fora da faixa historica esperada do fornecedor.",
            )
        )


def _detect_approver(document: DocumentResult, approver_counts: Counter[str]) -> None:
    approver = document.fields.get("aprovado_por", "nao extraido")
    if approver == "nao extraido":
        return
    if len(approver_counts) > 1 and approver_counts[approver] == 1:
        document.add_anomaly(
            AnomalyRecord(
                code="UNKNOWN_APPROVER",
                label="Aprovador nao reconhecido",
                severity="Media",
                confidence="Media",
                rule="approver-appears-once-in-batch",
                evidence_fields=["aprovado_por"],
                evidence_values={"aprovado_por": approver},
                message="O nome do aprovador nao faz parte do conjunto recorrente observado no lote.",
            )
        )


def _detect_status_inconsistency(document: DocumentResult) -> None:
    status = document.fields.get("status", "").upper()
    payment_date = document.fields.get("data_pagamento", "nao extraido")
    if status == "CANCELADO" and payment_date != "nao extraido":
        document.add_anomaly(
            AnomalyRecord(
                code="STATUS_INCONSISTENCY",
                label="STATUS inconsistente",
                severity="Media",
                confidence="Alta",
                rule="cancelled-with-payment-date",
                evidence_fields=["status", "data_pagamento"],
                evidence_values={"status": status, "data_pagamento": payment_date},
                message="Documento cancelado nao deveria manter data de pagamento preenchida.",
            )
        )
    if status == "PAGO" and payment_date == "nao extraido":
        document.add_anomaly(
            AnomalyRecord(
                code="STATUS_INCONSISTENCY",
                label="STATUS inconsistente",
                severity="Media",
                confidence="Alta",
                rule="paid-without-payment-date",
                evidence_fields=["status", "data_pagamento"],
                evidence_values={"status": status, "data_pagamento": payment_date},
                message="Documento marcado como pago sem data de pagamento extraida.",
            )
        )
