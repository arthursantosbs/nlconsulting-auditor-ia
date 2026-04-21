let
    Datas = List.RemoveNulls(
        List.Combine(
            {
                Table.Column(results, "data_emissao_data"),
                Table.Column(results, "data_pagamento_data"),
                Table.Column(results, "data_emissao_nf_data")
            }
        )
    ),
    Hoje = Date.From(DateTime.LocalNow()),
    DataInicial = if List.IsEmpty(Datas) then #date(Date.Year(Hoje), 1, 1) else List.Min(Datas),
    DataFinal = if List.IsEmpty(Datas) then Hoje else List.Max(Datas),
    QuantidadeDias = Duration.Days(DataFinal - DataInicial) + 1,
    Lista = List.Dates(DataInicial, QuantidadeDias, #duration(1, 0, 0, 0)),
    Tabela = Table.FromList(Lista, Splitter.SplitByNothing(), {"Data"}),
    ComAno = Table.AddColumn(Tabela, "Ano", each Date.Year([Data]), Int64.Type),
    ComMesNumero = Table.AddColumn(ComAno, "MesNumero", each Date.Month([Data]), Int64.Type),
    ComMes = Table.AddColumn(ComMesNumero, "Mes", each Date.ToText([Data], "MMMM", "pt-BR"), type text),
    ComAnoMes = Table.AddColumn(ComMes, "AnoMes", each Date.ToText([Data], "yyyy-MM"), type text),
    ComTrimestre = Table.AddColumn(ComAnoMes, "Trimestre", each "T" & Text.From(Date.QuarterOfYear([Data])), type text)
in
    ComTrimestre
