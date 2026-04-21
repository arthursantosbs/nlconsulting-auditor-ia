# Layout do Dashboard

## Pagina 1 · Resumo Executivo

Objetivo: dar a leitura de 15 segundos da operacao.

Cards no topo:

- `Total Arquivos`
- `Total Anomalias`
- `Arquivos Suspeitos`
- `Taxa de Suspeita`
- `Alertas de Processamento`
- `Taxa LLM`

Visuais principais:

- barras horizontais: `Anomalias por Tipo`
- barras horizontais: `Top 10 Fornecedores com Mais Ocorrencias`
- rosca: `Anomalias por Gravidade`
- linha ou area: `Valor Bruto por Data de Emissao NF`
- tabela curta: `Top Arquivos para Revisao`

Slicers recomendados:

- `fornecedor`
- `tipo_anomalia`
- `gravidade`
- `process_status`
- `provider`

## Pagina 2 · Investigacao de Casos

Objetivo: permitir drill-down rapido na demo.

Bloco esquerdo:

- slicers verticais
- `tipo_documento`
- `status`
- `extraction_source`
- `aprovado_por`

Centro:

- matriz: linhas `fornecedor`, colunas `tipo_anomalia`, valor `Total Anomalias`
- barras: `Valor Bruto Suspeito por Fornecedor`

Base:

- tabela detalhada com:
  - `file_name`
  - `numero_documento`
  - `fornecedor`
  - `tipo_anomalia`
  - `gravidade`
  - `mensagem`
  - `status`
  - `valor_bruto`
  - `data_pagamento`

Drillthrough recomendado:

- pagina filtrada por `file_name`
- mostrar dados do documento, warnings, anomalias e auditoria do arquivo

## Pagina 3 · Rastreabilidade e Auditoria

Objetivo: provar governanca e trilha de evidencias.

Cards:

- `Eventos de Auditoria`
- `Arquivos com Falha`
- `Providers Distintos`
- `Prompts Distintos`

Visuais:

- barras empilhadas: `Eventos por Tipo`
- barras horizontais: `Eventos por Rule`
- linha: `Eventos de Auditoria por Timestamp`
- tabela grande:
  - `file_name`
  - `timestamp`
  - `event_type`
  - `rule`
  - `outcome`
  - `confidence`
  - `details`

## Ajustes de usabilidade

- deixe a pagina 1 como landing page da demo
- habilite `tooltip` com `file_name`, `numero_documento` e `mensagem`
- congele os slicers mais importantes no topo
- use interacoes cruzadas entre grafico por tipo e tabela detalhada
- destaque `Arquivo nao processavel` e `Alta` com a cor de risco
