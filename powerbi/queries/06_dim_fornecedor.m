let
    Base = Table.SelectColumns(results, {"fornecedor", "cnpj_fornecedor"}),
    Filtrado = Table.SelectRows(Base, each Text.Trim([fornecedor] & "") <> "" and [fornecedor] <> "nao extraido"),
    Ordenado = Table.Sort(Filtrado, {{"fornecedor", Order.Ascending}, {"cnpj_fornecedor", Order.Ascending}}),
    Distinto = Table.Distinct(Ordenado, {"fornecedor"})
in
    Distinto
