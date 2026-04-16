# NLConsulting · Auditor de Documentos com IA

Aplicacao web para processar lotes de documentos financeiros (`.zip` ou varios `.txt`), extrair campos com IA, detectar anomalias, exportar resultados para CSV/Excel e gerar trilha de auditoria separada para consumo no Power BI.

## O que esta entrega cobre

- Upload de arquivo `.zip` ou multiplos `.txt`
- Extracao de campos com API de IA compatível com OpenAI
- Fallback deterministico para desenvolvimento quando a chave nao estiver configurada
- Tratamento de encoding invalido, campos vazios ou truncados e arquivos malformados
- Deteccao de anomalias pedidas no briefing
- Exportacao de `results.csv`, `anomalies.csv`, `audit_log.csv` e `results.xlsx`
- Interface web com progresso, resumo, filtros e downloads
- Guia para Power BI e deploy

## Stack

- Backend: FastAPI
- Frontend: HTML, CSS e JavaScript servidos pelo proprio backend
- IA: API compatível com OpenAI (`/v1/chat/completions`)
- Exportacao Excel: `openpyxl`
- Deploy sugerido: Render

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

Versao do prompt: `2026-04-16-v1`

Estratégia:

- O parser deterministico tenta ler os campos por `CHAVE: VALOR`
- Em seguida o LLM recebe nome do arquivo, texto bruto e campos preliminares
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

## Dados reais da tarefa

O pacote `arquivos_nf.zip` nao estava presente neste workspace durante a implementacao. A aplicacao ja esta pronta para receber esse lote real assim que ele for disponibilizado.

## Deploy no Render

1. Suba este projeto para um repositório GitHub publico.
2. No Render, crie um novo `Web Service` apontando para o repositório.
3. O arquivo [render.yaml](/C:/Users/arthur/Desktop/NLConsulting/render.yaml) ja define `buildCommand` e `startCommand`.
4. Configure `OPENAI_API_KEY` nas environment variables do Render.
5. Depois do deploy, a URL publica entregavel sera a URL gerada pelo Render.

## Power BI

O guia detalhado esta em [powerbi/README.md](/C:/Users/arthur/Desktop/NLConsulting/powerbi/README.md).

Arquivos sugeridos como fonte:

- `results.csv`
- `anomalies.csv`
- `audit_log.csv`

## Limitações honestas

- Sem `OPENAI_API_KEY`, o sistema usa um parser deterministico para facilitar desenvolvimento local. Para a submissao final da vaga, configure a API real.
- A publicacao online e a criacao do repositório GitHub dependem da sua conta e de credenciais externas. O projeto foi preparado para esse passo.
