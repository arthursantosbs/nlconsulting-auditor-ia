# Power BI Pack

Este diretorio deixa o dashboard praticamente pronto para montar no Power BI Desktop.

Enquanto o lote oficial de `1000` arquivos termina, use esta pasta validada como fonte de desenvolvimento:

- [manual_runs/groq_llama_validation_100_v2/arquivos_nf_gemini_free_100](/C:/Users/arthur/Desktop/NLConsulting/manual_runs/groq_llama_validation_100_v2/arquivos_nf_gemini_free_100)

Quando o lote oficial finalizar, troque apenas o parametro `pCaminhoExportacao` para:

- [manual_runs/groq_final_llama_v2/arquivos_nf_gemini_free](/C:/Users/arthur/Desktop/NLConsulting/manual_runs/groq_final_llama_v2/arquivos_nf_gemini_free)

## O que existe aqui

- [theme.json](/C:/Users/arthur/Desktop/NLConsulting/powerbi/theme.json): tema visual alinhado com a web app
- [MEASURES.dax](/C:/Users/arthur/Desktop/NLConsulting/powerbi/MEASURES.dax): medidas prontas
- [DASHBOARD_LAYOUT.md](/C:/Users/arthur/Desktop/NLConsulting/powerbi/DASHBOARD_LAYOUT.md): desenho das paginas
- [PUBLICACAO_CHECKLIST.md](/C:/Users/arthur/Desktop/NLConsulting/powerbi/PUBLICACAO_CHECKLIST.md): fechamento da entrega
- [queries](/C:/Users/arthur/Desktop/NLConsulting/powerbi/queries): consultas Power Query

## Modelo recomendado

Use estas tabelas no Power BI:

- `results`: fato principal por documento
- `anomalies`: uma linha por anomalia
- `audit_log`: uma linha por evento de rastreabilidade
- `dim_fornecedor`: dimensao de fornecedor
- `dim_tipo_anomalia`: dimensao de tipo de anomalia
- `dim_calendario`: calendario derivado das datas do lote

## Relacionamentos

Crie estes relacionamentos:

- `results[file_name]` 1:* `anomalies[file_name]`
- `results[file_name]` 1:* `audit_log[file_name]`
- `dim_fornecedor[fornecedor]` 1:* `results[fornecedor]`
- `dim_fornecedor[fornecedor]` 1:* `anomalies[fornecedor]`
- `dim_tipo_anomalia[tipo_anomalia]` 1:* `anomalies[tipo_anomalia]`
- `dim_calendario[Data]` 1:* `results[data_emissao_nf_data]`

Direcao de filtro:

- mantenha `single` por padrao
- use `dim_* -> fatos`

## Ordem sugerida de montagem

1. Abra o Power BI Desktop.
2. Importe o [theme.json](/C:/Users/arthur/Desktop/NLConsulting/powerbi/theme.json).
3. Crie as queries na ordem dos arquivos em [queries](/C:/Users/arthur/Desktop/NLConsulting/powerbi/queries).
4. Aplique os relacionamentos acima.
5. Cole as medidas de [MEASURES.dax](/C:/Users/arthur/Desktop/NLConsulting/powerbi/MEASURES.dax).
6. Monte as paginas conforme [DASHBOARD_LAYOUT.md](/C:/Users/arthur/Desktop/NLConsulting/powerbi/DASHBOARD_LAYOUT.md).
7. Quando o lote oficial terminar, troque o parametro `pCaminhoExportacao` e clique em `Refresh`.
8. Publique no Power BI Service.

## Resultado esperado para a entrega

O relatorio final deve mostrar pelo menos:

- volume total processado
- total de anomalias
- taxa de arquivos suspeitos
- top fornecedores impactados
- distribuicao por tipo de anomalia
- tabela detalhada de casos
- trilha de auditoria filtravel

## Observacao importante

Nao consegui gerar um `.pbix` automaticamente daqui porque o Power BI Desktop nao esta disponivel neste ambiente. O que deixei pronto reduz o trabalho manual para importar, colar as medidas, montar os visuais e publicar.
