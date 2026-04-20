from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation

from app.models import EXPECTED_FIELDS


KEY_ALIASES = {
    "TIPO_DOCUMENTO": "tipo_documento",
    "NUMERO_DOCUMENTO": "numero_documento",
    "DATA_EMISSAO": "data_emissao",
    "FORNECEDOR": "fornecedor",
    "CNPJ_FORNECEDOR": "cnpj_fornecedor",
    "DESCRICAO_SERVICO": "descricao_servico",
    "VALOR_BRUTO": "valor_bruto",
    "DATA_PAGAMENTO": "data_pagamento",
    "DATA_EMISSAO_NF": "data_emissao_nf",
    "APROVADO_POR": "aprovado_por",
    "BANCO_DESTINO": "banco_destino",
    "STATUS": "status",
    "HASH_VERIFICACAO": "hash_verificacao",
}

VALID_DOCUMENT_TYPES = {
    "NOTA_FISCAL",
    "RECIBO",
    "FATURA",
    "CONTRATO_ADITIVO",
}
VALID_STATUS_VALUES = {"PAGO", "CANCELADO", "ESTORNADO", "PENDENTE"}


@dataclass
class DecodedDocument:
    text: str
    encoding_used: str
    warnings: list[str]


def decode_text(content: bytes) -> DecodedDocument:
    attempts = [
        ("utf-8-sig", "strict"),
        ("utf-8", "strict"),
        ("cp1252", "strict"),
        ("latin-1", "strict"),
    ]
    warnings: list[str] = []
    for encoding, errors in attempts:
        try:
            text = content.decode(encoding, errors=errors)
            if "\ufffd" in text:
                warnings.append("Conteudo com caracteres substituidos apos decodificacao.")
            if encoding != "utf-8-sig":
                warnings.append(f"Arquivo recuperado usando encoding {encoding}.")
            return DecodedDocument(text=text, encoding_used=encoding, warnings=warnings)
        except UnicodeDecodeError:
            continue

    recovered = content.decode("utf-8", errors="replace")
    warnings.append("Arquivo com encoding invalido; conteudo recuperado parcialmente com substituicao.")
    return DecodedDocument(text=recovered, encoding_used="utf-8(replace)", warnings=warnings)


def parse_key_value_pairs(text: str) -> tuple[dict[str, str], list[str]]:
    parsed: dict[str, str] = {}
    warnings: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if ":" not in line:
            warnings.append(f"Linha sem separador chave/valor: {line[:80]}")
            continue
        raw_key, raw_value = line.split(":", 1)
        key = KEY_ALIASES.get(raw_key.strip().upper())
        if not key:
            continue
        value = raw_value.strip()
        if not value:
            warnings.append(f"Campo aparentemente truncado ou vazio: {key}")
        parsed[key] = value or "nao extraido"

    missing = [field_name for field_name in EXPECTED_FIELDS if field_name not in parsed]
    for field_name in missing:
        parsed[field_name] = "nao extraido"
        warnings.append(f"Campo ausente: {field_name}")
    return parsed, warnings


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def normalize_cnpj(value: str) -> str:
    digits = re.sub(r"\D", "", value or "")
    if len(digits) != 14:
        return normalize_text(value)
    return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"


def parse_currency_to_decimal(value: str) -> Decimal | None:
    if not value or value == "nao extraido":
        return None
    cleaned = value.replace("R$", "").strip().replace(".", "").replace(",", ".")
    cleaned = re.sub(r"[^0-9.-]", "", cleaned)
    if not cleaned:
        return None
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def parse_date(value: str) -> datetime | None:
    if not value or value == "nao extraido":
        return None
    normalized = normalize_text(value)
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(normalized, fmt)
        except ValueError:
            continue
    return None


def fill_not_extracted(fields: dict[str, str]) -> tuple[dict[str, str], list[str]]:
    missing: list[str] = []
    normalized: dict[str, str] = {}
    for field_name in EXPECTED_FIELDS:
        value = normalize_text(fields.get(field_name, ""))
        if not value:
            normalized[field_name] = "nao extraido"
            missing.append(field_name)
        elif field_name == "cnpj_fornecedor":
            normalized[field_name] = normalize_cnpj(value)
        else:
            normalized[field_name] = value
    return normalized, missing


def validate_extracted_fields(fields: dict[str, str]) -> list[str]:
    warnings: list[str] = []

    document_type = fields.get("tipo_documento", "nao extraido")
    if document_type != "nao extraido" and document_type.upper() not in VALID_DOCUMENT_TYPES:
        warnings.append(
            f"Campo com valor fora do dominio esperado: tipo_documento={document_type}"
        )

    status = fields.get("status", "nao extraido")
    if status != "nao extraido" and status.upper() not in VALID_STATUS_VALUES:
        warnings.append(f"Campo com valor fora do dominio esperado: status={status}")

    for date_field in ("data_emissao", "data_pagamento", "data_emissao_nf"):
        value = fields.get(date_field, "nao extraido")
        if value != "nao extraido" and parse_date(value) is None:
            warnings.append(f"Campo com data invalida: {date_field}={value}")

    amount = fields.get("valor_bruto", "nao extraido")
    if amount != "nao extraido" and parse_currency_to_decimal(amount) is None:
        warnings.append(f"Campo com formato invalido: valor_bruto={amount}")

    cnpj = fields.get("cnpj_fornecedor", "nao extraido")
    if cnpj != "nao extraido" and not re.fullmatch(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}", cnpj):
        warnings.append(f"Campo com formato invalido: cnpj_fornecedor={cnpj}")

    verification_hash = fields.get("hash_verificacao", "nao extraido")
    if verification_hash != "nao extraido" and not re.fullmatch(r"[A-Za-z0-9-]+", verification_hash):
        warnings.append(
            f"Campo com formato invalido: hash_verificacao={verification_hash}"
        )

    return warnings
