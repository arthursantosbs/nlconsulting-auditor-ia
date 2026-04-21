let
    Base = Table.SelectColumns(anomalies, {"tipo_anomalia", "codigo_anomalia", "gravidade"}),
    Filtrado = Table.SelectRows(Base, each Text.Trim([tipo_anomalia] & "") <> ""),
    Ordenado = Table.Sort(Filtrado, {{"tipo_anomalia", Order.Ascending}}),
    Distinto = Table.Distinct(Ordenado, {"tipo_anomalia"})
in
    Distinto
