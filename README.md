# NLConsulting · Auditor de Documentos com IA

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/arthursantosbs/nlconsulting-auditor-ia)

Aplicacao web para processar lotes de documentos financeiros (`.zip` ou varios `.txt`), extrair campos com IA, detectar anomalias, exportar resultados para CSV/Excel e gerar trilha de auditoria separada para consumo no Power BI.

## O que esta entrega cobre

- Upload de arquivo `.zip` ou multiplos `.txt`
- Extracao de campos com API de IA compatível com OpenAI
- Fallback deterministico para desenvolvimento quando a chave nao estiver configurada
- Tratamento de encoding invalido, campos vazios ou truncados e arquivos malformados
- Deteccao de anomalias pedidas no briefing
- Exportacao de `results.csv`, `anomalies.csv`, `audit_log.csv` e `results.xlsx`
- Relatorio executivo em `anomaly_report.md` e resumo estruturado em `summary.json`
- Interface web com progresso, resumo, filtros e downloads
- Guia para Power BI e deploy

## Stack

- Backend: FastAPI
- Frontend: HTML, CSS e JavaScript servidos pelo proprio backend
- IA: API compatível com OpenAI (`/v1/chat/completions`)
- Exportacao Excel: `openpyxl`
- Deploy sugerido: Render
- Deploy alternativo: Docker em qualquer provedor compatível

## Como rodar localmente

1. Crie e ative um ambiente virtual.
2. Instale as dependencias:

```bash
python -m pip install -r requirements.txt
```

3. Configure o `.env` a partir de [.env.example](/C:/Users/arthur/Desktop/NLConsulting/.env.example).
4. Suba a aplicacao:

```bash
uvicorn app.main:app --reload
```

5. Abra `http://127.0.0.1:8000`.

## Como processar o lote real pela linha de comando

Quando voce receber o `arquivos_nf.zip`, pode gerar todos os artefatos sem abrir a interface:

```bash
python scripts/process_batch.py "C:\caminho\para\arquivos_nf.zip"
```

Os arquivos serao salvos em `manual_runs/<nome-do-lote>/`.

## Variaveis de ambiente

- `OPENAI_API_KEY`: chave da API de IA
- `OPENAI_MODEL`: modelo usado para extracao
- `OPENAI_BASE_URL`: endpoint base compatível com OpenAI
- `AI_REQUIRED`: se `true`, falhas da API fazem o arquivo marcar erro em vez de fallback
- `MAX_UPLOAD_MB`: limite por arquivo
- `MAX_FILES_PER_JOB`: limite de arquivos no lote
- `LLM_TIMEOUT_SECONDS`: timeout da API
- `LLM_MAX_RETRIES`: tentativas com backoff
- `LLM_CONCURRENCY`: paralelismo controlado para batch

## Prompt utilizado

Versao do prompt: `2026-04-21-v2`

Estratégia:

- O parser deterministico tenta ler os campos por `CHAVE: VALOR`
- Quando o documento ja vem estruturado e consistente, o sistema usa o parser diretamente com `extraction_source=parser_structured`
- Quando ha sinais de problema estrutural, o LLM entra como camada de recuperacao
- O modelo responde JSON puro com `fields`, `warnings`, `confidence` e `processable`
- Se um campo nao puder ser extraido com seguranca, a instrucao exige `nao extraido`

Isso ajuda a manter rastreabilidade e evita assumir valores vazios como corretos.

## Regras de anomalia implementadas

- `NF duplicada`
- `CNPJ divergente`
- `Fornecedor sem historico`
- `NF emitida apos pagamento`
- `Valor fora da faixa do fornecedor`
- `Aprovador nao reconhecido`
- `STATUS inconsistente`
- `Arquivo nao processavel`

## Rastreabilidade

Cada documento registra:

- nome do arquivo
- timestamp do processamento
- versao do prompt
- fonte da extracao
- provider usado
- warnings e campos ausentes

Cada anomalia registra:

- regra que disparou
- campos de evidencia
- valores de evidencia
- confianca
- gravidade

Tudo isso vai para `audit_log.csv` e para a aba `audit_log` do Excel.

## Artefatos gerados por lote

- `results.csv`: base principal por documento
- `anomalies.csv`: uma linha por anomalia
- `audit_log.csv`: trilha de auditoria
- `results.xlsx`: workbook com abas separadas
- `summary.json`: resumo agregado para integrações
- `anomaly_report.md`: relatorio textual para entrega e entrevista

## Validacao com API real

O projeto foi validado com provider OpenAI-compatible real durante o desenvolvimento:

- `Groq Free Plan` com `openai/gpt-oss-20b`
- smoke test com `25` arquivos: `25/25` documentos processados via LLM
- teste de estabilidade com `100` arquivos: `100/100` documentos processados via LLM
- lote final de `1000` arquivos fechado em modo hibrido rapido, priorizando parser estruturado e usando IA para recuperacao de casos problemáticos

Os artefatos desses testes ficam em `manual_runs/groq_checks/` no ambiente local e nao sao versionados.

## Dados da tarefa

O repositório inclui `sample_data/arquivos_nf_gemini_free.zip`, uma versao com `1000` arquivos `.txt` preparada para providers com limite gratis por request. O lote oficial original recebido para a vaga continua sendo o `arquivos_nf.zip`.

## Relatorio de anomalias para entrega

Assim que o lote oficial for processado, use o arquivo `anomaly_report.md` gerado automaticamente como base para o item obrigatorio "quais anomalias foram encontradas". Ele ja resume:

- volume total processado
- contagem por tipo de anomalia
- fornecedores mais concentrados
- top arquivos para revisao manual

## Deploy no Render

1. Suba este projeto para um repositório GitHub publico.
2. No Render, crie um novo `Web Service` apontando para o repositório.
3. O arquivo [render.yaml](/C:/Users/arthur/Desktop/NLConsulting/render.yaml) ja define `buildCommand` e `startCommand`.
4. Configure `OPENAI_API_KEY` nas environment variables do Render com a sua chave da Groq.
5. O arquivo [render.yaml](/C:/Users/arthur/Desktop/NLConsulting/render.yaml) ja aponta para `llama-3.1-8b-instant` em `https://api.groq.com/openai/v1`.
6. Depois do deploy, a URL publica entregavel sera a URL gerada pelo Render.

### Configuracao recomendada para o Render

- `OPENAI_API_KEY`: sua chave Groq
- `OPENAI_MODEL`: `llama-3.1-8b-instant`
- `OPENAI_BASE_URL`: `https://api.groq.com/openai/v1`
- `AI_PROVIDER_LABEL`: `Groq Free Plan`
- `AI_REQUIRED`: `false`
- `LLM_CONCURRENCY`: `1`

Como alternativa, o projeto tambem inclui [Dockerfile](/C:/Users/arthur/Desktop/NLConsulting/Dockerfile).

## Power BI

O guia detalhado esta em [powerbi/README.md](/C:/Users/arthur/Desktop/NLConsulting/powerbi/README.md).

Arquivos sugeridos como fonte:

- `results.csv`
- `anomalies.csv`
- `audit_log.csv`

## Limitações honestas

- Sem `OPENAI_API_KEY`, o sistema usa um parser deterministico para facilitar desenvolvimento local. Para a submissao final da vaga, configure a API real.
- Provedores gratuitos podem impor limites diarios agressivos. Durante a validacao, o Gemini Free Tier desta conta ficou restrito a `20` requests por modelo, por isso a recomendacao pratica deste repositório passou a ser Groq para o caminho zero custo.
- A publicacao online depende da sua conta e de credenciais externas. O projeto foi preparado para esse passo.
