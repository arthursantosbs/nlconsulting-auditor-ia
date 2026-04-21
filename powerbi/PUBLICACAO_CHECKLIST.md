# Checklist de Publicacao

## Antes de publicar

- confirmar que o lote oficial terminou
- validar se `summary.json` bate com os cards do Power BI
- trocar `pCaminhoExportacao` para a pasta final do lote oficial
- clicar em `Refresh`
- revisar se todas as tabelas ficaram com `1000` documentos no total

## Itens do relatorio

- pagina 1 com KPIs e distribuicao por anomalia
- pagina 2 com investigacao e tabela detalhada
- pagina 3 com trilha de auditoria

## Itens da entrega

- link publico da aplicacao
- link do GitHub publico
- `results.csv` ou `results.xlsx`
- dashboard publicado no Power BI Service
- log de auditoria exportavel

## Conferencias finais

- `Total Arquivos` igual ao total do `summary.json`
- `Total Anomalias` igual ao total do `summary.json`
- `Alertas de Processamento` igual a `FILE_PROCESSING_ISSUE`
- filtros funcionando por fornecedor e tipo de anomalia
- tabela de auditoria mostrando `file_processed` e `anomaly_detected`

## Roteiro de demo em 3 minutos

1. abrir pagina `Resumo Executivo`
2. mostrar KPI total e top anomalias
3. clicar em um tipo de anomalia e filtrar a tabela de casos
4. abrir a pagina de auditoria e provar rastreabilidade por `file_name`
5. encerrar mostrando exportacao e consistencia com o CSV
