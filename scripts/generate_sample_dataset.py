from __future__ import annotations

import random
import zipfile
from pathlib import Path


OUTPUT_DIR = Path("sample_data")
SUPPLIERS = [
    ("TechSoft Ltda", "12.345.678/0001-90"),
    ("Alpha Data Services", "44.555.666/0001-20"),
    ("Vision Consulting", "88.777.666/0001-45"),
]
APPROVERS = ["Maria Silva", "Joao Souza", "Carla Lima"]
SERVICES = [
    "Licenca de Software ERP",
    "Consultoria fiscal recorrente",
    "Manutencao de infraestrutura em nuvem",
]


def build_document(index: int, supplier: tuple[str, str]) -> str:
    supplier_name, cnpj = supplier
    amount = random.choice([5200, 7800, 15000, 17500, 19000])
    return f"""TIPO_DOCUMENTO: NOTA_FISCAL
NUMERO_DOCUMENTO: NF-{78000 + index}
DATA_EMISSAO: 15/04/2024
FORNECEDOR: {supplier_name}
CNPJ_FORNECEDOR: {cnpj}
DESCRICAO_SERVICO: {random.choice(SERVICES)}
VALOR_BRUTO: R$ {amount:,.2f}
DATA_PAGAMENTO: 20/04/2024
DATA_EMISSAO_NF: 15/04/2024
APROVADO_POR: {random.choice(APPROVERS)}
BANCO_DESTINO: Banco do Brasil Ag.1234 C/C 56789-0
STATUS: PAGO
HASH_VERIFICACAO: NLC{420000000 + index}
""".replace(",", "X").replace(".", ",").replace("X", ".")


def main() -> None:
    random.seed(42)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = OUTPUT_DIR / "sample_arquivos_nf.zip"

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for index in range(1, 26):
            text = build_document(index, random.choice(SUPPLIERS))
            if index == 4:
                text = text.replace("NF-78004", "NF-78003")
            if index == 7:
                text = text.replace("12.345.678/0001-90", "99.999.999/0001-99")
            if index == 11:
                text = text.replace("15/04/2024", "25/04/2024", 1)
                text = text.replace("20/04/2024", "18/04/2024")
            if index == 15:
                text = text.replace("STATUS: PAGO", "STATUS: CANCELADO")
            if index == 20:
                text = text.replace("APROVADO_POR: Maria Silva", "APROVADO_POR: Nome Raro")
            archive.writestr(f"documento_{index:03d}.txt", text.encode("utf-8"))

    print(f"Amostra criada em: {zip_path.resolve()}")


if __name__ == "__main__":
    main()
