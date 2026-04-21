from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from random import random
from time import time

import httpx

from app.config import Settings
from app.models import EXPECTED_FIELDS


PROMPT_TEMPLATE = """Extraia campos de um documento financeiro e responda somente em JSON valido.
Use exatamente "nao extraido" em qualquer campo incerto.
Preserve datas, moedas e nomes como aparecem no documento.
Formato:
{
  "fields": {
    "tipo_documento": "...",
    "numero_documento": "...",
    "data_emissao": "...",
    "fornecedor": "...",
    "cnpj_fornecedor": "...",
    "descricao_servico": "...",
    "valor_bruto": "...",
    "data_pagamento": "...",
    "data_emissao_nf": "...",
    "aprovado_por": "...",
    "banco_destino": "...",
    "status": "...",
    "hash_verificacao": "..."
  },
  "warnings": [],
  "confidence": "Alta|Media|Baixa",
  "processable": true
}"""


@dataclass
class LLMExtractionResult:
    fields: dict[str, str]
    warnings: list[str]
    confidence: str
    processable: bool
    source: str
    provider: str


class LLMExtractionService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._semaphore = asyncio.Semaphore(settings.llm_concurrency)

    async def extract(
        self,
        *,
        filename: str,
        document_text: str,
        preliminary_fields: dict[str, str],
    ) -> LLMExtractionResult:
        if not self.settings.ai_enabled:
            return LLMExtractionResult(
                fields=preliminary_fields,
                warnings=[],
                confidence="Media",
                processable=True,
                source="rule_based_fallback",
                provider="offline-parser",
            )

        payload = {
            "model": self.settings.openai_model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": PROMPT_TEMPLATE},
                {
                    "role": "user",
                    "content": f"Documento bruto:\n{document_text[:4000]}",
                },
            ],
        }
        if _is_gemini_openai_compatible(self.settings):
            # Gemini 2.5 defaults to thinking; disabling it lowers latency and
            # reduces free-tier instability for high-volume extraction tasks.
            payload["reasoning_effort"] = "none"

        async with self._semaphore:
            response_json = await self._post_with_retry(payload)

        raw_content = response_json["choices"][0]["message"]["content"]
        parsed = json.loads(raw_content)
        fields = parsed.get("fields") or _extract_top_level_fields(parsed)
        return LLMExtractionResult(
            fields=_normalize_llm_fields(fields),
            warnings=[str(item) for item in parsed.get("warnings", [])],
            confidence=_normalize_confidence(parsed.get("confidence", "Media")),
            processable=bool(parsed.get("processable", True)),
            source="llm",
            provider=self.settings.ai_provider_label,
        )

    async def _post_with_retry(self, payload: dict) -> dict:
        headers = {
            "Authorization": f"Bearer {self.settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        last_error: Exception | None = None
        for attempt in range(1, self.settings.llm_max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.settings.llm_timeout_seconds) as client:
                    response = await client.post(
                        f"{self.settings.openai_base_url}/chat/completions",
                        headers=headers,
                        json=payload,
                    )
                if response.status_code >= 400:
                    response.raise_for_status()
                return response.json()
            except json.JSONDecodeError as exc:
                last_error = exc
                if attempt >= self.settings.llm_max_retries:
                    break
                await asyncio.sleep(_retry_delay_seconds(attempt))
            except httpx.HTTPStatusError as exc:
                last_error = exc
                if attempt >= self.settings.llm_max_retries or not _should_retry_status(exc.response.status_code):
                    break
                await asyncio.sleep(_retry_delay_seconds(attempt, exc.response))
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt >= self.settings.llm_max_retries:
                    break
                await asyncio.sleep(_retry_delay_seconds(attempt))
        raise RuntimeError(f"Falha ao consultar a API de IA: {last_error}") from last_error


def _normalize_llm_fields(raw_fields: dict) -> dict[str, str]:
    normalized: dict[str, str] = {}
    if not isinstance(raw_fields, dict):
        return normalized

    for raw_key, raw_value in raw_fields.items():
        key = _canonicalize_field_name(raw_key)
        if not key:
            continue
        value = str(raw_value).strip()
        if not value or value.lower() == "nao extraido":
            continue
        normalized[key] = value
    return normalized


def _extract_top_level_fields(payload: object) -> dict:
    if not isinstance(payload, dict):
        return {}
    if any(_canonicalize_field_name(key) for key in payload.keys()):
        return payload
    return {}


def _canonicalize_field_name(raw_key: object) -> str | None:
    key = re.sub(r"[^a-z0-9]+", "_", str(raw_key).strip().lower()).strip("_")
    if key in EXPECTED_FIELDS:
        return key
    return None


def _normalize_confidence(value: object) -> str:
    if isinstance(value, (int, float)):
        if value >= 0.85:
            return "Alta"
        if value >= 0.6:
            return "Media"
        return "Baixa"

    normalized = str(value).strip().lower()
    mapping = {
        "alta": "Alta",
        "high": "Alta",
        "media": "Media",
        "média": "Media",
        "medium": "Media",
        "baixa": "Baixa",
        "low": "Baixa",
    }
    return mapping.get(normalized, "Media")


def _is_gemini_openai_compatible(settings: Settings) -> bool:
    return (
        "generativelanguage.googleapis.com" in settings.openai_base_url.lower()
        or settings.openai_model.lower().startswith("gemini-")
    )


def _should_retry_status(status_code: int) -> bool:
    return status_code in {408, 409, 425, 429, 500, 502, 503, 504}


def _retry_delay_seconds(attempt: int, response: httpx.Response | None = None) -> float:
    if response is not None:
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            parsed = _parse_retry_after(retry_after)
            if parsed is not None:
                return parsed

    base_delay = min(2 ** attempt, 20)
    return base_delay + (0.25 * random())


def _parse_retry_after(value: str) -> float | None:
    try:
        return max(float(value), 0.0)
    except ValueError:
        try:
            retry_at = parsedate_to_datetime(value).timestamp()
        except (TypeError, ValueError, OverflowError):
            return None
        return max(retry_at - time(), 0.0)
