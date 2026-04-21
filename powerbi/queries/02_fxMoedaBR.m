(texto as nullable text) as nullable number =>
let
    Valor = Text.Trim(texto & ""),
    Limpo =
        if Valor = "" or Valor = "nao extraido" then
            null
        else
            Text.Replace(
                Text.Replace(
                    Text.Replace(Valor, "R$", ""),
                    ".",
                    ""
                ),
                ",",
                "."
            ),
    Resultado = if Limpo = null then null else try Number.FromText(Text.Trim(Limpo), "en-US") otherwise null
in
    Resultado
