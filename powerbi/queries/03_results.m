let
    Fonte = Csv.Document(
        File.Contents(pCaminhoExportacao & "\results.csv"),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    Cabecalhos = Table.PromoteHeaders(Fonte, [PromoteAllScalars = true]),
    ComoTexto = Table.TransformColumnTypes(
        Cabecalhos,
        List.Transform(Table.ColumnNames(Cabecalhos), each {_, type text}),
        "pt-BR"
    ),
    ComAnomalyCount = Table.TransformColumnTypes(ComoTexto, {{"anomaly_count", Int64.Type}}),
    ComValor = Table.AddColumn(ComAnomalyCount, "valor_bruto_num", each fxMoedaBR([valor_bruto]), type number),
    ComDataEmissao = Table.AddColumn(ComValor, "data_emissao_data", each fxDataBR([data_emissao]), type date),
    ComDataPagamento = Table.AddColumn(ComDataEmissao, "data_pagamento_data", each fxDataBR([data_pagamento]), type date),
    ComDataEmissaoNF = Table.AddColumn(ComDataPagamento, "data_emissao_nf_data", each fxDataBR([data_emissao_nf]), type date),
    ComProcessadoEm = Table.AddColumn(
        ComDataEmissaoNF,
        "processed_at_datetime",
        each try DateTimeZone.FromText([processed_at]) otherwise null,
        type datetimezone
    ),
    ComFlagSuspeito = Table.AddColumn(
        ComProcessadoEm,
        "is_suspect_num",
        each if [is_suspect] = "SIM" then 1 else 0,
        Int64.Type
    ),
    ComFlagAlerta = Table.AddColumn(
        ComFlagSuspeito,
        "has_processing_alert",
        each
            if [process_status] <> "processed"
                or Text.Contains(Text.Upper([anomaly_types] & ""), "ARQUIVO NAO PROCESSAVEL")
                or Text.Length(Text.Trim([warnings] & "")) > 0
            then 1
            else 0,
        Int64.Type
    )
in
    ComFlagAlerta
