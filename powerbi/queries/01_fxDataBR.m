(texto as nullable text) as nullable date =>
let
    Valor = Text.Trim(texto & ""),
    Partes = Text.Split(Valor, "/"),
    Resultado =
        if Valor = "" or Valor = "nao extraido" or List.Count(Partes) <> 3 then
            null
        else
            try #date(
                Number.FromText(Partes{2}),
                Number.FromText(Partes{1}),
                Number.FromText(Partes{0})
            ) otherwise null
in
    Resultado
