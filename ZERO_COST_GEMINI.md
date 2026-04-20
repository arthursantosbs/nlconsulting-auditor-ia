# Caminho Zero Custo com Gemini

## Status real desta conta

Nos testes feitos em `20/04/2026`, a sua chave/projeto retornou erro `429 RESOURCE_EXHAUSTED` com **quotaValue=20** requests por dia para `gemini-2.5-flash-lite` e tambem **quotaValue=20** para `gemini-2.5-flash`.

Isso significa que, **com esta conta Gemini**, o caminho zero custo nao e suficiente para processar o lote completo de `1000` arquivos.

## O que foi preparado

- ZIP pronto com **1000 arquivos** para caber no limite gratis diario do Gemini:
  [sample_data/arquivos_nf_gemini_free.zip](/C:/Users/arthur/Desktop/NLConsulting/sample_data/arquivos_nf_gemini_free.zip)
- Arquivo de exemplo para configuracao:
  [.env.gemini-free.example](/C:/Users/arthur/Desktop/NLConsulting/.env.gemini-free.example)

O arquivo extra removido foi `DOC_0633_v2.txt`, porque o lote original tem `1001` `.txt`.

## Passo a passo

1. Crie uma chave gratis no Google AI Studio:
   [Gemini quickstart](https://ai.google.dev/gemini-api/docs/quickstart)

2. Copie `.env.gemini-free.example` para `.env` e cole sua chave no campo `OPENAI_API_KEY`.

3. Rode a aplicacao:

```bash
uvicorn app.main:app --reload
```

4. Envie este ZIP na interface:

```text
sample_data/arquivos_nf_gemini_free.zip
```

## Configuracao usada

```env
OPENAI_MODEL=gemini-2.5-flash-lite
OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
AI_PROVIDER_LABEL=Gemini Free Tier
AI_REQUIRED=true
LLM_CONCURRENCY=1
LLM_MAX_RETRIES=5
```

## Observacoes importantes

- O Gemini tem compatibilidade com a API estilo OpenAI, por isso o projeto consegue usar apenas `api key + base URL + model`.
- No plano gratis, a pagina oficial informa que o conteudo pode ser usado para melhorar os produtos.
- Na sua conta atual, a quota observada em teste foi **20 requests por dia por modelo**, o que inviabiliza o lote completo.
- Para zero custo de verdade com chance real de fechar os `1000` arquivos, o melhor candidato agora e Groq. Se quiser, use o guia [ZERO_COST_GROQ.md](/C:/Users/arthur/Desktop/NLConsulting/ZERO_COST_GROQ.md).
- Se sua chave ainda nao estiver ativa, aguarde alguns minutos e tente novamente.

## Fontes oficiais

- [Gemini pricing](https://ai.google.dev/pricing)
- [Gemini rate limits](https://ai.google.dev/gemini-api/docs/quota)
- [OpenAI compatibility for Gemini](https://ai.google.dev/gemini-api/docs/openai)
