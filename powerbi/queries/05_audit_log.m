let
    Fonte = Csv.Document(
        File.Contents(pCaminhoExportacao & "\audit_log.csv"),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    Cabecalhos = Table.PromoteHeaders(Fonte, [PromoteAllScalars = true]),
    ComoTexto = Table.TransformColumnTypes(
        Cabecalhos,
        List.Transform(Table.ColumnNames(Cabecalhos), each {_, type text}),
        "pt-BR"
    ),
    ComTimestamp = Table.AddColumn(
        ComoTexto,
        "timestamp_datetime",
        each try DateTimeZone.FromText([timestamp]) otherwise null,
        type datetimezone
    )
in
    ComTimestamp
