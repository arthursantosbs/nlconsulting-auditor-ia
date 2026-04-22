# NLConsulting - Auditor de Documentos com IA

Aplicacao web para auditoria de documentos financeiros com extracao assistida por IA, deteccao de anomalias, exportacao para Excel/CSV e dashboard final em Power BI.

## Links da entrega

- Aplicacao publicada: [nlconsulting-document-auditor.onrender.com](https://nlconsulting-document-auditor.onrender.com)
- Dashboard Power BI: [NLC.pbix](/C:/Users/arthur/Desktop/NLConsulting/powerbi/generated_pbip/NLC.pbix)
- Projeto Power BI: [NLC.pbip](/C:/Users/arthur/Desktop/NLConsulting/powerbi/generated_pbip/NLC.pbip)

## Funcionalidades

- Upload de `.zip` ou multiplos `.txt`
- Extracao de campos com API compativel com OpenAI
- Parser estruturado para documentos bem formatados
- Deteccao automatica de anomalias
- Tabela de resultados com flags de risco
- Exportacao de `results.csv`, `anomalies.csv`, `audit_log.csv` e `results.xlsx`
- Log de auditoria rastreavel por documento

## Anomalias cobertas

- `NF duplicada`
- `CNPJ divergente`
- `Fornecedor sem historico`
- `NF emitida apos pagamento`
- `Valor fora da faixa do fornecedor`
- `Aprovador nao reconhecido`
- `STATUS inconsistente`
- `Arquivo nao processavel`

## Stack

- FastAPI
- HTML, CSS e JavaScript
- API LLM compativel com OpenAI
- `openpyxl` para Excel
- Render para deploy
- Power BI para visualizacao final

## Estrutura do repositorio

- [app](/C:/Users/arthur/Desktop/NLConsulting/app): backend, frontend e regras de negocio
- [scripts/process_batch.py](/C:/Users/arthur/Desktop/NLConsulting/scripts/process_batch.py): processamento local em lote
- [scripts/build_powerbi_pbip.py](/C:/Users/arthur/Desktop/NLConsulting/scripts/build_powerbi_pbip.py): geracao do projeto Power BI
- [tests](/C:/Users/arthur/Desktop/NLConsulting/tests): testes automatizados
- [powerbi/generated_pbip](/C:/Users/arthur/Desktop/NLConsulting/powerbi/generated_pbip): dashboard final

## Como rodar localmente

```bash
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Configure o `.env` a partir de [.env.example](/C:/Users/arthur/Desktop/NLConsulting/.env.example).

## Como processar um lote pela linha de comando

```bash
python scripts/process_batch.py "C:\\caminho\\para\\arquivos_nf.zip"
```

Os artefatos sao salvos em `manual_runs/<nome-do-lote>/`.

## Variaveis de ambiente principais

- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `OPENAI_BASE_URL`
- `AI_REQUIRED`
- `MAX_UPLOAD_MB`
- `MAX_FILES_PER_JOB`
- `LLM_TIMEOUT_SECONDS`
- `LLM_MAX_RETRIES`
- `LLM_CONCURRENCY`

## Artefatos gerados por lote

- `results.csv`
- `anomalies.csv`
- `audit_log.csv`
- `results.xlsx`
- `summary.json`
- `anomaly_report.md`

## Power BI

O dashboard final ja esta salvo em:

- [powerbi/generated_pbip/NLC.pbix](/C:/Users/arthur/Desktop/NLConsulting/powerbi/generated_pbip/NLC.pbix)
- [powerbi/generated_pbip/NLC.pbip](/C:/Users/arthur/Desktop/NLConsulting/powerbi/generated_pbip/NLC.pbip)

## Deploy

O projeto inclui:

- [render.yaml](/C:/Users/arthur/Desktop/NLConsulting/render.yaml)
- [Dockerfile](/C:/Users/arthur/Desktop/NLConsulting/Dockerfile)

## Testes

```bash
python -m unittest discover -s tests -v
```
