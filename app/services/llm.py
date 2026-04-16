from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass

import httpx

from app.config import Settings
from app.models import EXPECTED_FIELDS


PROMPT_TEMPLATE = """Voce e um auditor de documentos financeiros.
Extraia APENAS os campos abaixo do texto bruto informado.
Se um campo nao puder ser identificado com seguranca, devolva exatamente "nao extraido".
Responda em JSON valido com esta estrutura:
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
  "warnings": ["..."],
  "confidence": "Alta|Media|Baixa",
  "processable": true
}
Mantenha os valores em portugues e preserve datas/moedas como no documento."""


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
                warnings=[
                    "OPENAI_API_KEY ausente; usando extracao deterministica para desenvolvimento.",
                ],
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
                    "content": (
                        f"Arquivo: {filename}\n"
                        f"Campos preliminares: {json.dumps(preliminary_fields, ensure_ascii=True)}\n\n"
                        f"Documento bruto:\n{document_text[:12000]}"
                    ),
                },
            ],
        }

        async with self._semaphore:
            response_json = await self._post_with_retry(payload)

        raw_content = response_json["choices"][0]["message"]["content"]
        parsed = json.loads(raw_content)
        fields = parsed.get("fields") or {}
        normalized_fields = {
            field_name: str(fields.get(field_name, "nao extraido"))
            for field_name in EXPECTED_FIELDS
        }
        return LLMExtractionResult(
            fields=normalized_fields,
            warnings=[str(item) for item in parsed.get("warnings", [])],
            confidence=str(parsed.get("confidence", "Media")),
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
                response.raise_for_status()
                return response.json()
            except (httpx.HTTPError, json.JSONDecodeError) as exc:
                last_error = exc
                if attempt >= self.settings.llm_max_retries:
                    break
                await asyncio.sleep(min(attempt * 2, 6))
        raise RuntimeError(f"Falha ao consultar a API de IA: {last_error}") from last_error
