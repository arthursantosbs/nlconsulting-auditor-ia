# Caminho Zero Custo com Groq

## Por que este caminho e mais promissor

Nos testes de hoje, a conta Gemini atual ficou limitada a `20 requests/dia` por modelo, o que nao fecha o lote final.

O Groq publica um plano gratis com modelos que chegam a `1000 RPD` ou mais, mantendo compatibilidade com a API da OpenAI:

- `openai/gpt-oss-20b`: `1000 RPD`
- `qwen/qwen3-32b`: `1000 RPD`
- `llama-3.1-8b-instant`: `14.4K RPD`

## Configuracao pronta

Arquivo modelo:
[.env.groq-free.example](/C:/Users/arthur/Desktop/NLConsulting/.env.groq-free.example)

Conteudo:

```env
OPENAI_MODEL=openai/gpt-oss-20b
OPENAI_BASE_URL=https://api.groq.com/openai/v1
AI_PROVIDER_LABEL=Groq Free Plan
AI_REQUIRED=true
LLM_MAX_RETRIES=5
LLM_CONCURRENCY=1
```

## Passo a passo

1. Crie uma conta e uma API key no Groq.
2. Copie `.env.groq-free.example` para `.env`.
3. Cole sua chave no campo `OPENAI_API_KEY`.
4. Rode a aplicacao:

```bash
uvicorn app.main:app --reload
```

5. Use o lote:

```text
sample_data/arquivos_nf_gemini_free.zip
```

## Observacoes

- O projeto atual ja aceita providers OpenAI-compatibles, entao a troca e basicamente `base URL + model + key`.
- O nome do ZIP continua valendo; ele so tem `1000` arquivos e continua sendo o lote ideal para um provider free.
- Eu ainda nao testei Groq neste workspace porque a sua chave atual e do Gemini, nao do Groq.

## Fontes oficiais

- [Groq free plan](https://console.groq.com/settings/billing/plans)
- [Groq rate limits](https://console.groq.com/docs/rate-limits)
- [Groq OpenAI compatibility](https://console.groq.com/docs/openai)
