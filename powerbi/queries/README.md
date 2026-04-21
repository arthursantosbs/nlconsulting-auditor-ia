# Queries Power Query

Crie as queries nesta ordem:

1. `pCaminhoExportacao`
2. `fxDataBR`
3. `fxMoedaBR`
4. `results`
5. `anomalies`
6. `audit_log`
7. `dim_fornecedor`
8. `dim_tipo_anomalia`
9. `dim_calendario`

Como usar:

1. No Power BI Desktop, clique em `Transform data`.
2. Crie uma `Blank Query` para cada arquivo desta pasta.
3. De a cada query exatamente o mesmo nome do arquivo, sem numero e sem extensao.
4. Cole o conteudo correspondente no `Advanced Editor`.
5. Em `pCaminhoExportacao`, ajuste o caminho quando o lote oficial terminar.

Sugestao pratica:

- monte o dashboard primeiro com os `100` arquivos validados
- quando o lote oficial sair, troque so o caminho e clique em `Refresh`
