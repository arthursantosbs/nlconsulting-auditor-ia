# Guia do Dashboard Power BI

Use os CSVs exportados pela aplicacao como fonte de dados do dashboard.

## Arquivos

- `results.csv`: uma linha por documento
- `anomalies.csv`: uma linha por anomalia
- `audit_log.csv`: uma linha por evento rastreavel
- `summary.json`: resumo agregado opcional para validar totais

## Visuais obrigatorios

1. Cards
   - total de arquivos: `COUNTROWS(results)`
   - total de anomalias: `COUNTROWS(anomalies)`
   - arquivos com erro de encoding: filtro em `results[warnings]` contendo `encoding`

2. Grafico de barras por tipo de anomalia
   - eixo: `anomalies[tipo_anomalia]`
   - valor: contagem de linhas

3. Tabela de anomalias detalhada
   - `file_name`
   - `tipo_anomalia`
   - `campos_evidencia`
   - `confianca`
   - `gravidade`

4. Grafico por fornecedor
   - eixo: `anomalies[fornecedor]`
   - valor: quantidade de anomalias
   - legenda opcional: `gravidade`

5. Tabela de log de auditoria
   - `file_name`
   - `timestamp`
   - `rule`
   - `outcome`
   - `details`

## Slicers recomendados

- `tipo_anomalia`
- `gravidade`
- `fornecedor`
- `process_status`

## Medidas DAX uteis

```DAX
Total Arquivos = COUNTROWS(results)
Total Anomalias = COUNTROWS(anomalies)
Arquivos Suspeitos = CALCULATE(COUNTROWS(results), results[is_suspect] = "SIM")
Erros Encoding = COUNTROWS(FILTER(results, CONTAINSSTRING(results[warnings], "encoding")))
```

## Publicacao

Publique no Power BI Service e inclua o link do relatorio junto com:

- URL da aplicacao
- link do repositório GitHub
- breve relatorio das anomalias encontradas

## Observacao pratica

Depois de processar o lote oficial, o arquivo `anomaly_report.md` pode servir como roteiro da apresentacao de 3 minutos e como checklist para conferir se os totais do Power BI batem com os exports.

O arquivo [theme.json](/C:/Users/arthur/Desktop/NLConsulting/powerbi/theme.json) pode ser importado no Power BI para deixar o visual mais consistente com a interface web.
