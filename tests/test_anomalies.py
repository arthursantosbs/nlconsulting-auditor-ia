from __future__ import annotations

import asyncio
import unittest
import zipfile
from io import BytesIO

from app.config import Settings
from app.models import DocumentResult
from app.services.anomalies import detect_anomalies
from app.services.jobs import JobManager, expand_uploads
from app.services.llm import (
    _extract_batch_items,
    _extract_top_level_fields,
    _is_gemini_openai_compatible,
    _normalize_confidence,
    _normalize_llm_fields,
    _should_retry_status,
)
from app.services.parsing import validate_extracted_fields


def make_document(file_name: str, supplier: str, number: str, cnpj: str, status: str = "PAGO") -> DocumentResult:
    return DocumentResult(
        file_name=file_name,
        processed_at="2026-04-16T00:00:00Z",
        prompt_version="test",
        extraction_source="test",
        provider="test",
        encoding_used="utf-8",
        process_status="processed",
        extraction_confidence="Alta",
        fields={
            "tipo_documento": "NOTA_FISCAL",
            "numero_documento": number,
            "data_emissao": "15/04/2024",
            "fornecedor": supplier,
            "cnpj_fornecedor": cnpj,
            "descricao_servico": "Servico",
            "valor_bruto": "R$ 10.000,00",
            "data_pagamento": "20/04/2024",
            "data_emissao_nf": "15/04/2024",
            "aprovado_por": "Maria Silva",
            "banco_destino": "Banco do Brasil",
            "status": status,
            "hash_verificacao": "ABC",
        },
        missing_fields=[],
        warnings=[],
    )


def make_document_text(
    *,
    supplier: str = "TechSoft",
    number: str = "NF-1",
    cnpj: str = "12.345.678/0001-90",
    status: str = "PAGO",
) -> str:
    return "\n".join(
        [
            "TIPO_DOCUMENTO: NOTA_FISCAL",
            f"NUMERO_DOCUMENTO: {number}",
            "DATA_EMISSAO: 15/04/2024",
            f"FORNECEDOR: {supplier}",
            f"CNPJ_FORNECEDOR: {cnpj}",
            "DESCRICAO_SERVICO: Servico",
            "VALOR_BRUTO: R$ 10.000,00",
            "DATA_PAGAMENTO: 20/04/2024",
            "DATA_EMISSAO_NF: 15/04/2024",
            "APROVADO_POR: Maria Silva",
            "BANCO_DESTINO: Banco do Brasil",
            f"STATUS: {status}",
            "HASH_VERIFICACAO: ABC123",
        ]
    )


class AnomalyDetectionTests(unittest.TestCase):
    def test_duplicate_nf_is_flagged(self) -> None:
        documents = [
            make_document("a.txt", "TechSoft", "NF-1", "12.345.678/0001-90"),
            make_document("b.txt", "TechSoft", "NF-1", "12.345.678/0001-90"),
        ]
        detect_anomalies(documents)
        self.assertTrue(any(anomaly.code == "DUPLICATE_NF" for anomaly in documents[0].anomalies))
        self.assertTrue(any(anomaly.code == "DUPLICATE_NF" for anomaly in documents[1].anomalies))

    def test_status_inconsistency_is_flagged(self) -> None:
        document = make_document("c.txt", "TechSoft", "NF-2", "12.345.678/0001-90", status="CANCELADO")
        detect_anomalies([document])
        self.assertTrue(any(anomaly.code == "STATUS_INCONSISTENCY" for anomaly in document.anomalies))

    def test_validation_flags_unexpected_status_value(self) -> None:
        warnings = validate_extracted_fields(
            {
                "tipo_documento": "RECIBO",
                "numero_documento": "REC-1",
                "data_emissao": "15/04/2024",
                "fornecedor": "TechSoft",
                "cnpj_fornecedor": "12.345.678/0001-90",
                "descricao_servico": "Servico",
                "valor_bruto": "R$ 10.000,00",
                "data_pagamento": "20/04/2024",
                "data_emissao_nf": "15/04/2024",
                "aprovado_por": "Maria Silva",
                "banco_destino": "Banco do Brasil",
                "status": "PAG",
                "hash_verificacao": "ABC123",
            }
        )
        self.assertTrue(any("status=PAG" in warning for warning in warnings))

    def test_llm_fields_are_normalized_case_insensitively(self) -> None:
        normalized = _normalize_llm_fields(
            {
                "TIPO_DOCUMENTO": "NOTA_FISCAL",
                "NUMERO_DOCUMENTO": "NF-1",
                "DATA_PAGAMENTO": "20/04/2024",
                "STATUS": "PAGO",
            }
        )
        self.assertEqual(normalized["tipo_documento"], "NOTA_FISCAL")
        self.assertEqual(normalized["numero_documento"], "NF-1")
        self.assertEqual(normalized["data_pagamento"], "20/04/2024")
        self.assertEqual(normalized["status"], "PAGO")

    def test_llm_numeric_confidence_maps_to_label(self) -> None:
        self.assertEqual(_normalize_confidence(0.95), "Alta")
        self.assertEqual(_normalize_confidence(0.7), "Media")
        self.assertEqual(_normalize_confidence(0.2), "Baixa")

    def test_top_level_field_payload_is_accepted(self) -> None:
        extracted = _extract_top_level_fields(
            {
                "TIPO_DOCUMENTO": "NOTA_FISCAL",
                "NUMERO_DOCUMENTO": "NF-1",
                "STATUS": "PAGO",
            }
        )
        self.assertIn("TIPO_DOCUMENTO", extracted)

    def test_batch_payload_items_are_extracted(self) -> None:
        extracted = _extract_batch_items(
            {
                "documents": [
                    {"file_name": "a.txt", "fields": {"STATUS": "PAGO"}},
                    {"file_name": "b.txt", "fields": {"STATUS": "CANCELADO"}},
                ]
            }
        )
        self.assertEqual(len(extracted), 2)
        self.assertEqual(extracted[0]["file_name"], "a.txt")

    def test_gemini_openai_compatibility_is_detected(self) -> None:
        settings = Settings(
            openai_api_key="test",
            openai_model="gemini-2.5-flash-lite",
            openai_base_url="https://generativelanguage.googleapis.com/v1beta/openai",
        )
        self.assertTrue(_is_gemini_openai_compatible(settings))

    def test_retry_status_classifier_handles_transient_errors(self) -> None:
        self.assertTrue(_should_retry_status(429))
        self.assertTrue(_should_retry_status(503))
        self.assertFalse(_should_retry_status(400))

    def test_expand_uploads_reads_zip_with_txt_files(self) -> None:
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("a.txt", "TIPO_DOCUMENTO: NOTA_FISCAL")
            archive.writestr("b.csv", "ignored")

        uploads = expand_uploads([("lote.zip", buffer.getvalue())], max_files=10)
        self.assertEqual(len(uploads), 1)
        self.assertEqual(uploads[0][0], "a.txt")

    def test_expand_uploads_rejects_bad_zip(self) -> None:
        with self.assertRaises(ValueError):
            expand_uploads([("quebrado.zip", b"not-a-zip")], max_files=10)

    def test_process_uploads_can_skip_batch_anomaly_detection(self) -> None:
        manager = JobManager(Settings(openai_api_key="", llm_concurrency=1))
        uploads = [
            ("a.txt", make_document_text(number="NF-1").encode("utf-8")),
            ("b.txt", make_document_text(number="NF-1").encode("utf-8")),
        ]

        documents = asyncio.run(manager.process_uploads(uploads, detect_batch_anomalies=False))

        self.assertTrue(all(not document.anomalies for document in documents))
        detect_anomalies(documents)
        self.assertTrue(
            all(any(anomaly.code == "DUPLICATE_NF" for anomaly in document.anomalies) for document in documents)
        )

    def test_structured_documents_skip_llm_and_still_process(self) -> None:
        manager = JobManager(Settings(openai_api_key="test", ai_required=True, llm_concurrency=1))
        uploads = [("ok.txt", make_document_text(number="NF-7").encode("utf-8"))]

        documents = asyncio.run(manager.process_uploads(uploads))

        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0].extraction_source, "parser_structured")
        self.assertEqual(documents[0].provider, "structured-parser")
        self.assertEqual(documents[0].process_status, "processed")


if __name__ == "__main__":
    unittest.main()
