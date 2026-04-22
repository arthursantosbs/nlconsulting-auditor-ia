# Checklist de Publicacao

## Antes de publicar

- abrir [powerbi/generated_pbip/NLC.pbix](/C:/Users/arthur/Desktop/NLConsulting/powerbi/generated_pbip/NLC.pbix)
- confirmar se o relatorio abre com os dados da pasta final
- validar se `summary.json` bate com os cards do Power BI
- clicar em `Refresh`
- entrar na conta Microsoft/Power BI
- clicar em `Publicar`

## Itens do relatorio

- pagina 1 com KPIs e distribuicao por anomalia
- pagina 2 com investigacao e tabela detalhada
- pagina 3 com trilha de auditoria

## Itens da entrega

- link publico da aplicacao: [https://nlconsulting-document-auditor.onrender.com](https://nlconsulting-document-auditor.onrender.com)
- link do GitHub publico: [arthursantosbs/nlconsulting-auditor-ia](https://github.com/arthursantosbs/nlconsulting-auditor-ia)
- `results.csv` ou `results.xlsx`
- dashboard publicado no Power BI Service
- log de auditoria exportavel

## Conferencias finais

- `Total Arquivos` igual ao total do `summary.json`
- `Total Anomalias` igual ao total do `summary.json`
- `Alertas de Processamento` igual a `FILE_PROCESSING_ISSUE`
- `Total Arquivos = 1000`
- `Total Anomalias = 167`
- `Alertas de Processamento = 3`
- filtros funcionando por fornecedor e tipo de anomalia
- tabela de auditoria mostrando `file_processed` e `anomaly_detected`

## Roteiro de demo em 3 minutos

1. abrir pagina `Resumo Executivo`
2. mostrar KPI total e top anomalias
3. clicar em um tipo de anomalia e filtrar a tabela de casos
4. abrir a pagina de auditoria e provar rastreabilidade por `file_name`
5. encerrar mostrando exportacao e consistencia com o CSV
