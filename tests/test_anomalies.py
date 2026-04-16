from __future__ import annotations

import unittest
import zipfile
from io import BytesIO

from app.models import DocumentResult
from app.services.anomalies import detect_anomalies
from app.services.jobs import expand_uploads


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


if __name__ == "__main__":
    unittest.main()
