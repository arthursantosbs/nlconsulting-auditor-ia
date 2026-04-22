# Power BI Pack

Este diretorio agora contem o pacote completo do dashboard final.

Fonte oficial do relatorio:

- [manual_runs/final_fasttrack_1000/arquivos_nf_gemini_free](/C:/Users/arthur/Desktop/NLConsulting/manual_runs/final_fasttrack_1000/arquivos_nf_gemini_free)

Arquivos gerados no Power BI:

- [powerbi/generated_pbip/NLC.pbip](/C:/Users/arthur/Desktop/NLConsulting/powerbi/generated_pbip/NLC.pbip)
- [powerbi/generated_pbip/NLC.pbix](/C:/Users/arthur/Desktop/NLConsulting/powerbi/generated_pbip/NLC.pbix)

Validacao do lote final no dashboard:

- `1000` arquivos
- `167` anomalias
- `3` alertas de processamento
- `149` casos de `STATUS inconsistente`
- `8` casos de `NF duplicada`
- `3` casos de `CNPJ divergente`

## O que existe aqui

- [theme.json](/C:/Users/arthur/Desktop/NLConsulting/powerbi/theme.json): tema visual alinhado com a web app
- [MEASURES.dax](/C:/Users/arthur/Desktop/NLConsulting/powerbi/MEASURES.dax): medidas prontas
- [DASHBOARD_LAYOUT.md](/C:/Users/arthur/Desktop/NLConsulting/powerbi/DASHBOARD_LAYOUT.md): desenho das paginas
- [PUBLICACAO_CHECKLIST.md](/C:/Users/arthur/Desktop/NLConsulting/powerbi/PUBLICACAO_CHECKLIST.md): fechamento da entrega
- [queries](/C:/Users/arthur/Desktop/NLConsulting/powerbi/queries): consultas Power Query
- [generated_pbip](/C:/Users/arthur/Desktop/NLConsulting/powerbi/generated_pbip): projeto PBIP e arquivo `.pbix` final

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

## Estado atual

O dashboard ja foi montado e salvo localmente no Power BI Desktop. O trabalho manual que sobra e:

1. abrir [powerbi/generated_pbip/NLC.pbix](/C:/Users/arthur/Desktop/NLConsulting/powerbi/generated_pbip/NLC.pbix) ou [powerbi/generated_pbip/NLC.pbip](/C:/Users/arthur/Desktop/NLConsulting/powerbi/generated_pbip/NLC.pbip)
2. clicar em `Publicar`
3. entrar com a conta Microsoft/Power BI
4. escolher o workspace
5. copiar o link do Power BI Service

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

O publish no Power BI Service ainda depende de login humano na conta Microsoft/Power BI. Todo o resto ja esta pronto e validado localmente.
