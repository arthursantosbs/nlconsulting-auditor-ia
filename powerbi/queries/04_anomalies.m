let
    Fonte = Csv.Document(
        File.Contents(pCaminhoExportacao & "\anomalies.csv"),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    Cabecalhos = Table.PromoteHeaders(Fonte, [PromoteAllScalars = true]),
    ComoTexto = Table.TransformColumnTypes(
        Cabecalhos,
        List.Transform(Table.ColumnNames(Cabecalhos), each {_, type text}),
        "pt-BR"
    ),
    ComProcessadoEm = Table.AddColumn(
        ComoTexto,
        "processed_at_datetime",
        each try DateTimeZone.FromText([processed_at]) otherwise null,
        type datetimezone
    )
in
    ComProcessadoEm
