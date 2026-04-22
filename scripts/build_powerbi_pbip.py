from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKBOOK_PATH = REPO_ROOT / "manual_runs" / "final_fasttrack_1000" / "arquivos_nf_gemini_free" / "results.xlsx"
OUTPUT_ROOT = REPO_ROOT / "powerbi" / "generated_pbip"


def q(name: str) -> str:
    return f"'{name}'" if any(ch in name for ch in " -%/#().") else name


def table_ref(table: str, column: str) -> str:
    return f"{q(table)}[{column}]"


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def guid() -> str:
    return str(uuid.uuid4())


def make_pbip() -> dict:
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
        "version": "1.0",
        "artifacts": [{"report": {"path": "NLC.Report"}}],
        "settings": {"enableAutoRecovery": True},
    }


def make_definition_pbir() -> dict:
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
        "version": "4.0",
        "datasetReference": {"byPath": {"path": "../NLC.SemanticModel"}},
    }


def make_definition_pbism() -> dict:
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
        "version": "4.2",
        "settings": {"qnaEnabled": True},
    }


def make_version_json() -> dict:
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
        "version": "2.0.0",
    }


def report_json() -> dict:
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.0.0/schema.json",
        "themeCollection": {},
        "settings": {
            "useStylableVisualContainerHeader": True,
            "useEnhancedTooltips": True,
        },
        "slowDataSourceSettings": {
            "isCrossHighlightingDisabled": False,
            "isSlicerSelectionsButtonEnabled": False,
            "isFilterSelectionsButtonEnabled": False,
            "isFieldWellButtonEnabled": False,
        },
    }


def pages_json() -> dict:
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
        "pageOrder": ["page_overview", "page_details", "page_audit"],
        "activePageName": "page_overview",
    }


def page_json(name: str, display_name: str) -> dict:
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.0.0/schema.json",
        "name": name,
        "displayName": display_name,
        "displayOption": "FitToPage",
        "height": 720,
        "width": 1280,
        "pageBinding": {"name": "Pod", "type": "Default", "parameters": []},
        "objects": {
            "outspace": [
                {
                    "properties": {
                        "color": {
                            "solid": {
                                "color": {"expr": {"Literal": {"Value": "'#B3B3B3'"}}}
                            }
                        }
                    }
                }
            ],
            "background": [
                {
                    "properties": {
                        "color": {
                            "solid": {
                                "color": {"expr": {"Literal": {"Value": "'#F5F7FA'"}}}
                            }
                        }
                    }
                }
            ],
        },
    }


def textbox_visual(name: str, text: str, x: float, y: float, w: float, h: float) -> dict:
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.2.0/schema.json",
        "name": name,
        "position": {"x": x, "y": y, "z": 0, "height": h, "width": w},
        "visual": {
            "visualType": "textbox",
            "objects": {
                "general": [
                    {
                        "properties": {
                            "paragraphs": [
                                {
                                    "textRuns": [
                                        {
                                            "value": text,
                                            "textStyle": {
                                                "fontFamily": "Segoe (Bold)",
                                                "fontSize": "18pt",
                                            },
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                ]
            },
            "visualContainerObjects": {
                "title": [
                    {"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}
                ],
                "background": [
                    {
                        "properties": {
                            "show": {"expr": {"Literal": {"Value": "false"}}},
                            "transparency": {"expr": {"Literal": {"Value": "0D"}}},
                        }
                    }
                ],
            },
        },
    }


def card_visual(name: str, title: str, measure_name: str, x: float, y: float, w: float, h: float) -> dict:
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.2.0/schema.json",
        "name": name,
        "position": {"x": x, "y": y, "z": 100, "height": h, "width": w},
        "visual": {
            "visualType": "card",
            "query": {
                "queryState": {
                    "Values": {
                        "projections": [
                            {
                                "field": {
                                    "Measure": {
                                        "Expression": {"SourceRef": {"Entity": "results"}},
                                        "Property": measure_name,
                                    }
                                },
                                "queryRef": f"results.{measure_name}",
                            }
                        ]
                    }
                }
            },
            "objects": {
                "categoryLabels": [
                    {"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}
                ],
                "labels": [
                    {
                        "properties": {
                            "color": {
                                "solid": {
                                    "color": {"expr": {"Literal": {"Value": "'#081018'"}}}
                                }
                            },
                            "fontFamily": {
                                "expr": {
                                    "Literal": {
                                        "Value": "'''Segoe UI Bold'', wf_segoe-ui_bold, helvetica, arial, sans-serif'"
                                    }
                                }
                            },
                            "fontSize": {"expr": {"Literal": {"Value": "'19'"}}},
                        }
                    }
                ],
            },
            "visualContainerObjects": {
                "title": [
                    {
                        "properties": {
                            "show": {"expr": {"Literal": {"Value": "true"}}},
                            "fontColor": {
                                "solid": {
                                    "color": {"expr": {"Literal": {"Value": "'#081018'"}}}
                                }
                            },
                            "alignment": {"expr": {"Literal": {"Value": "'left'"}}},
                            "fontSize": {"expr": {"Literal": {"Value": "'10'"}}},
                            "text": {"expr": {"Literal": {"Value": f"'{title}'"}}},
                            "fontFamily": {
                                "expr": {
                                    "Literal": {
                                        "Value": "'''Segoe UI Bold'', wf_segoe-ui_bold, helvetica, arial, sans-serif'"
                                    }
                                }
                            },
                            "background": {
                                "solid": {
                                    "color": {"expr": {"Literal": {"Value": "'#EFF7F9'"}}}
                                }
                            },
                        }
                    }
                ],
                "background": [
                    {
                        "properties": {
                            "show": {"expr": {"Literal": {"Value": "true"}}},
                            "transparency": {"expr": {"Literal": {"Value": "0D"}}},
                        }
                    }
                ],
                "stylePreset": [
                    {"properties": {"name": {"expr": {"Literal": {"Value": "'None'"}}}}}
                ],
                "border": [
                    {
                        "properties": {
                            "show": {"expr": {"Literal": {"Value": "true"}}},
                            "color": {
                                "solid": {
                                    "color": {"expr": {"Literal": {"Value": "'#D8E2E6'"}}}
                                }
                            },
                        }
                    }
                ],
                "visualHeader": [
                    {"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}
                ],
            },
        },
    }


def clustered_bar_visual(
    name: str,
    title: str,
    entity: str,
    column: str,
    measure_name: str,
    x: float,
    y: float,
    w: float,
    h: float,
) -> dict:
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.2.0/schema.json",
        "name": name,
        "position": {"x": x, "y": y, "z": 100, "height": h, "width": w},
        "visual": {
            "visualType": "clusteredBarChart",
            "query": {
                "queryState": {
                    "Category": {
                        "projections": [
                            {
                                "field": {
                                    "Column": {
                                        "Expression": {"SourceRef": {"Entity": entity}},
                                        "Property": column,
                                    }
                                },
                                "queryRef": f"{entity}.{column}",
                                "active": True,
                            }
                        ]
                    },
                    "Y": {
                        "projections": [
                            {
                                "field": {
                                    "Measure": {
                                        "Expression": {"SourceRef": {"Entity": "results"}},
                                        "Property": measure_name,
                                    }
                                },
                                "queryRef": f"results.{measure_name}",
                            }
                        ]
                    },
                },
                "sortDefinition": {
                    "sort": [
                        {
                            "field": {
                                "Measure": {
                                    "Expression": {"SourceRef": {"Entity": "results"}},
                                    "Property": measure_name,
                                }
                            },
                            "direction": "Descending",
                        }
                    ],
                    "isDefaultSort": True,
                },
            },
            "objects": {
                "valueAxis": [
                    {"properties": {"fontSize": {"expr": {"Literal": {"Value": "8M"}}}}}
                ],
                "categoryAxis": [
                    {
                        "properties": {
                            "fontSize": {"expr": {"Literal": {"Value": "8M"}}},
                            "concatenateLabels": {"expr": {"Literal": {"Value": "true"}}},
                        }
                    }
                ],
                "legend": [
                    {"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}
                ],
            },
            "visualContainerObjects": {
                "title": [
                    {
                        "properties": {
                            "show": {"expr": {"Literal": {"Value": "true"}}},
                            "text": {"expr": {"Literal": {"Value": f"'{title}'"}}},
                            "fontColor": {
                                "solid": {
                                    "color": {"expr": {"Literal": {"Value": "'#081018'"}}}
                                }
                            },
                            "background": {
                                "solid": {
                                    "color": {"expr": {"Literal": {"Value": "'#EFF7F9'"}}}
                                }
                            },
                            "fontSize": {"expr": {"Literal": {"Value": "'11'"}}},
                            "fontFamily": {
                                "expr": {
                                    "Literal": {
                                        "Value": "'''Segoe UI Bold'', wf_segoe-ui_bold, helvetica, arial, sans-serif'"
                                    }
                                }
                            },
                        }
                    }
                ],
                "background": [
                    {
                        "properties": {
                            "show": {"expr": {"Literal": {"Value": "true"}}},
                            "transparency": {"expr": {"Literal": {"Value": "0D"}}},
                        }
                    }
                ],
                "border": [
                    {
                        "properties": {
                            "show": {"expr": {"Literal": {"Value": "true"}}},
                            "color": {
                                "solid": {
                                    "color": {"expr": {"Literal": {"Value": "'#D8E2E6'"}}}
                                }
                            },
                        }
                    }
                ],
                "visualHeader": [
                    {"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}
                ],
            },
        },
    }


def table_visual(
    name: str,
    title: str,
    fields: list[tuple[str, str, str | None]],
    x: float,
    y: float,
    w: float,
    h: float,
) -> dict:
    projections = []
    for entity, column, display_name in fields:
        item: dict = {
            "field": {
                "Column": {
                    "Expression": {"SourceRef": {"Entity": entity}},
                    "Property": column,
                }
            },
            "queryRef": f"{entity}.{column}",
        }
        if display_name:
            item["displayName"] = display_name
        projections.append(item)

    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.2.0/schema.json",
        "name": name,
        "position": {"x": x, "y": y, "z": 100, "height": h, "width": w},
        "visual": {
            "visualType": "tableEx",
            "query": {"queryState": {"Values": {"projections": projections}}},
            "objects": {
                "grid": [
                    {
                        "properties": {
                            "outlineColor": {
                                "solid": {
                                    "color": {"expr": {"Literal": {"Value": "'#E5EDF0'"}}}
                                }
                            },
                            "outlineWeight": {"expr": {"Literal": {"Value": "1.5D"}}},
                            "gridVertical": {"expr": {"Literal": {"Value": "true"}}},
                            "gridHorizontal": {"expr": {"Literal": {"Value": "true"}}},
                            "rowPadding": {"expr": {"Literal": {"Value": "4D"}}},
                            "textSize": {"expr": {"Literal": {"Value": "8D"}}},
                        }
                    }
                ],
                "columnHeaders": [
                    {
                        "properties": {
                            "fontColor": {
                                "solid": {
                                    "color": {"expr": {"Literal": {"Value": "'#081018'"}}}
                                }
                            },
                            "fontFamily": {
                                "expr": {
                                    "Literal": {
                                        "Value": "'''Segoe UI Bold'', wf_segoe-ui_bold, helvetica, arial, sans-serif'"
                                    }
                                }
                            },
                            "fontSize": {"expr": {"Literal": {"Value": "9D"}}},
                            "backColor": {
                                "solid": {
                                    "color": {"expr": {"Literal": {"Value": "'#EFF7F9'"}}}
                                }
                            },
                        }
                    }
                ],
                "values": [
                    {
                        "properties": {
                            "fontSize": {"expr": {"Literal": {"Value": "8D"}}},
                            "wordWrap": {"expr": {"Literal": {"Value": "true"}}},
                        }
                    }
                ],
                "total": [{"properties": {"totals": {"expr": {"Literal": {"Value": "false"}}}}}],
            },
            "visualContainerObjects": {
                "title": [
                    {
                        "properties": {
                            "show": {"expr": {"Literal": {"Value": "true"}}},
                            "text": {"expr": {"Literal": {"Value": f"'{title}'"}}},
                            "fontColor": {
                                "solid": {
                                    "color": {"expr": {"Literal": {"Value": "'#081018'"}}}
                                }
                            },
                            "background": {
                                "solid": {
                                    "color": {"expr": {"Literal": {"Value": "'#EFF7F9'"}}}
                                }
                            },
                            "fontSize": {"expr": {"Literal": {"Value": "11D"}}},
                            "fontFamily": {
                                "expr": {
                                    "Literal": {
                                        "Value": "'''Segoe UI Bold'', wf_segoe-ui_bold, helvetica, arial, sans-serif'"
                                    }
                                }
                            },
                        }
                    }
                ],
                "background": [
                    {
                        "properties": {
                            "show": {"expr": {"Literal": {"Value": "true"}}},
                            "color": {
                                "solid": {
                                    "color": {"expr": {"Literal": {"Value": "'#FFFFFF'"}}}
                                }
                            },
                            "transparency": {"expr": {"Literal": {"Value": "0D"}}},
                        }
                    }
                ],
                "border": [
                    {
                        "properties": {
                            "show": {"expr": {"Literal": {"Value": "true"}}},
                            "color": {
                                "solid": {
                                    "color": {"expr": {"Literal": {"Value": "'#D8E2E6'"}}}
                                }
                            },
                        }
                    }
                ],
                "visualHeader": [
                    {"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}
                ],
            },
        },
    }


def workbook_m(sheet: str, type_lines: list[str], extra_steps: list[str]) -> str:
    workbook = str(WORKBOOK_PATH).replace("\\", "\\\\")
    lines = [
        "let",
        f'    Source = Excel.Workbook(File.Contents("{workbook}"), null, true),',
        f'    Raw = Source{{[Item="{sheet}",Kind="Sheet"]}}[Data],',
        '    #"Promoted Headers" = Table.PromoteHeaders(Raw, [PromoteAllScalars=true]),',
        "    fnDataBR = (txt as nullable text) as nullable date =>",
        "        let",
        "            normalized = if txt = null or Text.Trim(txt) = \"\" then null else Text.Trim(txt),",
        "            parsed = try if normalized = null then null else Date.FromText(normalized, [Culture=\"pt-BR\"]) otherwise null",
        "        in",
        "            parsed,",
        "    fnDateTimeIso = (txt as nullable text) as nullable datetime =>",
        "        let",
        "            normalized = if txt = null or Text.Trim(txt) = \"\" then null else Text.Trim(txt),",
        "            parsed = try if normalized = null then null else DateTime.From(DateTimeZone.FromText(normalized)) otherwise null",
        "        in",
        "            parsed,",
        "    fnMoedaBR = (txt as nullable text) as nullable number =>",
        "        let",
        "            normalized = if txt = null or Text.Trim(txt) = \"\" then null else Text.Trim(Text.Replace(txt, \"R$\", \"\")),",
        "            semMilhar = if normalized = null then null else Text.Replace(normalized, \".\", \"\"),",
        "            decimalPoint = if semMilhar = null then null else Text.Replace(semMilhar, \",\", \".\"),",
        "            parsed = try if decimalPoint = null then null else Number.FromText(decimalPoint, \"en-US\") otherwise null",
        "        in",
        "            parsed,",
        '    #"Changed Types" = Table.TransformColumnTypes(#"Promoted Headers", {',
    ]
    for idx, type_line in enumerate(type_lines):
        suffix = "," if idx < len(type_lines) - 1 else ""
        lines.append(f"        {type_line}{suffix}")
    lines.append('    }, "pt-BR"),')
    lines.extend(extra_steps[:-1])
    lines.append(f"    {extra_steps[-1]}")
    lines.append("in")
    lines.append(f"    {extra_steps[-1].split('=')[0].strip()}")
    return "\n".join(lines)


def results_tmdl() -> str:
    m_source = workbook_m(
        "documents",
        [
            '{"file_name", type text}',
            '{"processed_at", type text}',
            '{"prompt_version", type text}',
            '{"extraction_source", type text}',
            '{"provider", type text}',
            '{"encoding_used", type text}',
            '{"process_status", type text}',
            '{"extraction_confidence", type text}',
            '{"missing_fields", type text}',
            '{"warnings", type text}',
            '{"anomaly_count", Int64.Type}',
            '{"anomaly_types", type text}',
            '{"is_suspect", type text}',
            '{"tipo_documento", type text}',
            '{"numero_documento", type text}',
            '{"data_emissao", type text}',
            '{"fornecedor", type text}',
            '{"cnpj_fornecedor", type text}',
            '{"descricao_servico", type text}',
            '{"valor_bruto", type text}',
            '{"data_pagamento", type text}',
            '{"data_emissao_nf", type text}',
            '{"aprovado_por", type text}',
            '{"banco_destino", type text}',
            '{"status", type text}',
            '{"hash_verificacao", type text}',
        ],
        [
            '#"Added Valor Bruto Num" = Table.AddColumn(#"Changed Types", "valor_bruto_num", each fnMoedaBR([valor_bruto]), type number),',
            '#"Added Processed At Datetime" = Table.AddColumn(#"Added Valor Bruto Num", "processed_at_datetime", each fnDateTimeIso([processed_at]), type datetime),',
            '#"Added Data Emissao NF Data" = Table.AddColumn(#"Added Processed At Datetime", "data_emissao_nf_data", each fnDataBR([data_emissao_nf]), type date)',
        ],
    )

    return f"""
table results

\tcolumn file_name
\t\tdataType: string
\t\tisKey
\t\tsummarizeBy: none
\t\tsourceColumn: file_name

\tcolumn processed_at
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: processed_at

\tcolumn prompt_version
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: prompt_version

\tcolumn extraction_source
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: extraction_source

\tcolumn provider
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: provider

\tcolumn encoding_used
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: encoding_used

\tcolumn process_status
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: process_status

\tcolumn extraction_confidence
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: extraction_confidence

\tcolumn missing_fields
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: missing_fields

\tcolumn warnings
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: warnings

\tcolumn anomaly_count
\t\tdataType: int64
\t\tformatString: 0
\t\tsummarizeBy: sum
\t\tsourceColumn: anomaly_count

\tcolumn anomaly_types
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: anomaly_types

\tcolumn is_suspect
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: is_suspect

\tcolumn tipo_documento
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: tipo_documento

\tcolumn numero_documento
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: numero_documento

\tcolumn data_emissao
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: data_emissao

\tcolumn fornecedor
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: fornecedor

\tcolumn cnpj_fornecedor
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: cnpj_fornecedor

\tcolumn descricao_servico
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: descricao_servico

\tcolumn valor_bruto
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: valor_bruto

\tcolumn valor_bruto_num
\t\tdataType: decimal
\t\tformatString: "R$ #,##0.00"
\t\tsummarizeBy: sum
\t\tsourceColumn: valor_bruto_num

\tcolumn data_pagamento
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: data_pagamento

\tcolumn data_emissao_nf
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: data_emissao_nf

\tcolumn data_emissao_nf_data
\t\tdataType: dateTime
\t\tformatString: Short Date
\t\tsummarizeBy: none
\t\tsourceColumn: data_emissao_nf_data

\tcolumn aprovado_por
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: aprovado_por

\tcolumn banco_destino
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: banco_destino

\tcolumn status
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: status

\tcolumn hash_verificacao
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: hash_verificacao

\tcolumn processed_at_datetime
\t\tdataType: dateTime
\t\tformatString: General Date
\t\tsummarizeBy: none
\t\tsourceColumn: processed_at_datetime

\tmeasure 'Total Arquivos' = COUNTROWS(results)
\t\tformatString: 0

\tmeasure 'Total Anomalias' = COUNTROWS(anomalies)
\t\tformatString: 0

\tmeasure 'Arquivos Suspeitos' =
\t\t\tCALCULATE(
\t\t\t\tDISTINCTCOUNT(results[file_name]),
\t\t\t\tresults[is_suspect] = "SIM"
\t\t\t)
\t\tformatString: 0

\tmeasure 'Arquivos Processados' =
\t\t\tCALCULATE(
\t\t\t\tDISTINCTCOUNT(results[file_name]),
\t\t\t\tresults[process_status] = "processed"
\t\t\t)
\t\tformatString: 0

\tmeasure 'Arquivos com Falha' =
\t\t\tCALCULATE(
\t\t\t\tDISTINCTCOUNT(results[file_name]),
\t\t\t\tresults[process_status] <> "processed"
\t\t\t)
\t\tformatString: 0

\tmeasure 'Arquivos via LLM' =
\t\t\tCALCULATE(
\t\t\t\tDISTINCTCOUNT(results[file_name]),
\t\t\t\tresults[extraction_source] = "llm"
\t\t\t)
\t\tformatString: 0

\tmeasure 'Taxa de Suspeita' = DIVIDE([Arquivos Suspeitos], [Total Arquivos], 0)
\t\tformatString: 0.00%

\tmeasure 'Taxa de Falha' = DIVIDE([Arquivos com Falha], [Total Arquivos], 0)
\t\tformatString: 0.00%

\tmeasure 'Taxa LLM' = DIVIDE([Arquivos via LLM], [Total Arquivos], 0)
\t\tformatString: 0.00%

\tmeasure 'Alertas de Processamento' =
\t\t\tCALCULATE(
\t\t\t\tDISTINCTCOUNT(anomalies[file_name]),
\t\t\t\tanomalies[codigo_anomalia] = "FILE_PROCESSING_ISSUE"
\t\t\t)
\t\tformatString: 0

\tmeasure 'Fornecedores Impactados' = DISTINCTCOUNT(anomalies[fornecedor])
\t\tformatString: 0

\tmeasure 'Tipos de Anomalia' = DISTINCTCOUNT(anomalies[tipo_anomalia])
\t\tformatString: 0

\tmeasure 'Eventos de Auditoria' = COUNTROWS(audit_log)
\t\tformatString: 0

\tmeasure 'Providers Distintos' = DISTINCTCOUNT(results[provider])
\t\tformatString: 0

\tmeasure 'Prompts Distintos' = DISTINCTCOUNT(results[prompt_version])
\t\tformatString: 0

\tmeasure 'Valor Bruto Total' = SUM(results[valor_bruto_num])
\t\tformatString: "R$ #,##0.00"

\tmeasure 'Valor Bruto Medio' = AVERAGE(results[valor_bruto_num])
\t\tformatString: "R$ #,##0.00"

\tmeasure 'Valor Bruto Suspeito' =
\t\t\tCALCULATE(
\t\t\t\tSUM(results[valor_bruto_num]),
\t\t\t\tresults[is_suspect] = "SIM"
\t\t\t)
\t\tformatString: "R$ #,##0.00"

\tmeasure 'Percentual de Valor Suspeito' = DIVIDE([Valor Bruto Suspeito], [Valor Bruto Total], 0)
\t\tformatString: 0.00%

\tmeasure 'Anomalias Alta Gravidade' =
\t\t\tCALCULATE(
\t\t\t\tCOUNTROWS(anomalies),
\t\t\t\tanomalies[gravidade] = "Alta"
\t\t\t)
\t\tformatString: 0

\tmeasure 'Anomalias Media Gravidade' =
\t\t\tCALCULATE(
\t\t\t\tCOUNTROWS(anomalies),
\t\t\t\tanomalies[gravidade] = "Media"
\t\t\t)
\t\tformatString: 0

\tmeasure 'Documentos Pagos' =
\t\t\tCALCULATE(
\t\t\t\tDISTINCTCOUNT(results[file_name]),
\t\t\t\tresults[status] = "PAGO"
\t\t\t)
\t\tformatString: 0

\tmeasure 'Documentos Cancelados' =
\t\t\tCALCULATE(
\t\t\t\tDISTINCTCOUNT(results[file_name]),
\t\t\t\tresults[status] = "CANCELADO"
\t\t\t)
\t\tformatString: 0

\tmeasure 'Ultimo Processamento' = MAX(results[processed_at_datetime])
\t\tformatString: General Date

\tmeasure 'Erros de Encoding' =
\t\t\tCOUNTROWS(
\t\t\t\tFILTER(
\t\t\t\t\tresults,
\t\t\t\t\tCONTAINSSTRING(LOWER(results[warnings]), "encoding")
\t\t\t\t)
\t\t\t)
\t\tformatString: 0

\tpartition results = m
\t\tmode: import
\t\tsource = ```
{m_source}
\t\t\t```
"""


def anomalies_tmdl() -> str:
    m_source = workbook_m(
        "anomalies",
        [
            '{"file_name", type text}',
            '{"numero_documento", type text}',
            '{"fornecedor", type text}',
            '{"tipo_anomalia", type text}',
            '{"codigo_anomalia", type text}',
            '{"gravidade", type text}',
            '{"confianca", type text}',
            '{"regra", type text}',
            '{"campos_evidencia", type text}',
            '{"valores_evidencia", type text}',
            '{"mensagem", type text}',
            '{"processed_at", type text}',
        ],
        [
            '#"Added Processed At Datetime" = Table.AddColumn(#"Changed Types", "processed_at_datetime", each fnDateTimeIso([processed_at]), type datetime)'
        ],
    )

    return f"""
table anomalies

\tcolumn file_name
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: file_name

\tcolumn numero_documento
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: numero_documento

\tcolumn fornecedor
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: fornecedor

\tcolumn tipo_anomalia
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: tipo_anomalia

\tcolumn codigo_anomalia
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: codigo_anomalia

\tcolumn gravidade
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: gravidade

\tcolumn confianca
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: confianca

\tcolumn regra
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: regra

\tcolumn campos_evidencia
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: campos_evidencia

\tcolumn valores_evidencia
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: valores_evidencia

\tcolumn mensagem
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: mensagem

\tcolumn processed_at
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: processed_at

\tcolumn processed_at_datetime
\t\tdataType: dateTime
\t\tformatString: General Date
\t\tsummarizeBy: none
\t\tsourceColumn: processed_at_datetime

\tpartition anomalies = m
\t\tmode: import
\t\tsource = ```
{m_source}
\t\t\t```
"""


def audit_log_tmdl() -> str:
    m_source = workbook_m(
        "audit_log",
        [
            '{"file_name", type text}',
            '{"timestamp", type text}',
            '{"event_type", type text}',
            '{"rule", type text}',
            '{"outcome", type text}',
            '{"confidence", type text}',
            '{"prompt_version", type text}',
            '{"evidence_fields", type text}',
            '{"details", type text}',
        ],
        [
            '#"Added Timestamp Datetime" = Table.AddColumn(#"Changed Types", "timestamp_datetime", each fnDateTimeIso([timestamp]), type datetime)'
        ],
    )

    return f"""
table audit_log

\tcolumn file_name
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: file_name

\tcolumn timestamp
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: timestamp

\tcolumn event_type
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: event_type

\tcolumn rule
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: rule

\tcolumn outcome
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: outcome

\tcolumn confidence
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: confidence

\tcolumn prompt_version
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: prompt_version

\tcolumn evidence_fields
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: evidence_fields

\tcolumn details
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: details

\tcolumn timestamp_datetime
\t\tdataType: dateTime
\t\tformatString: General Date
\t\tsummarizeBy: none
\t\tsourceColumn: timestamp_datetime

\tpartition audit_log = m
\t\tmode: import
\t\tsource = ```
{m_source}
\t\t\t```
"""


def dim_fornecedor_tmdl() -> str:
    return """
table dim_fornecedor

\tcolumn fornecedor
\t\tdataType: string
\t\tisKey
\t\tsummarizeBy: none
\t\tsourceColumn: [fornecedor]

\tpartition dim_fornecedor = calculated
\t\tmode: import
\t\tsource =
\t\t\tFILTER(
\t\t\t\tDISTINCT(
\t\t\t\t\tUNION(
\t\t\t\t\t\tSELECTCOLUMNS(results, "fornecedor", results[fornecedor]),
\t\t\t\t\t\tSELECTCOLUMNS(anomalies, "fornecedor", anomalies[fornecedor])
\t\t\t\t\t)
\t\t\t\t),
\t\t\t\tNOT ISBLANK([fornecedor]) && [fornecedor] <> ""
\t\t\t)
"""


def dim_tipo_anomalia_tmdl() -> str:
    return """
table dim_tipo_anomalia

\tcolumn tipo_anomalia
\t\tdataType: string
\t\tisKey
\t\tsummarizeBy: none
\t\tsourceColumn: [tipo_anomalia]

\tpartition dim_tipo_anomalia = calculated
\t\tmode: import
\t\tsource =
\t\t\tFILTER(
\t\t\t\tVALUES(anomalies[tipo_anomalia]),
\t\t\t\tNOT ISBLANK([tipo_anomalia]) && [tipo_anomalia] <> ""
\t\t\t)
"""


def dim_calendario_tmdl() -> str:
    return """
table dim_calendario

\tcolumn Date
\t\tdataType: dateTime
\t\tisKey
\t\tformatString: Short Date
\t\tsummarizeBy: none
\t\tsourceColumn: [Date]

\tcolumn Year = YEAR([Date])
\t\tformatString: 0
\t\tsummarizeBy: none

\tcolumn MonthNo = MONTH([Date])
\t\tformatString: 0
\t\tsummarizeBy: none

\tcolumn Month = FORMAT([Date], "MMMM")
\t\tsummarizeBy: none
\t\tsortByColumn: MonthNo

\tcolumn Day = DAY([Date])
\t\tformatString: 0
\t\tsummarizeBy: none

\thierarchy 'Date Hierarchy'
\t\tlevel Year
\t\t\tcolumn: Year

\t\tlevel Month
\t\t\tcolumn: Month

\t\tlevel Day
\t\t\tcolumn: Day

\tpartition dim_calendario = calculated
\t\tmode: import
\t\tsource =
\t\t\tVAR startDate = MIN(results[data_emissao_nf_data])
\t\t\tVAR endDate = MAX(results[data_emissao_nf_data])
\t\t\tRETURN
\t\t\t\tCALENDAR(
\t\t\t\t\tDATE(YEAR(startDate), 1, 1),
\t\t\t\t\tDATE(YEAR(endDate), 12, 31)
\t\t\t\t)
"""


def model_tmdl() -> str:
    return """
model Model
\tculture: pt-BR
\tdefaultPowerBIDataSourceVersion: powerBI_V3
\tsourceQueryCulture: pt-BR
\tdataAccessOptions
\t\tlegacyRedirects
\t\treturnErrorValuesAsNull

ref table results
ref table anomalies
ref table audit_log
"""


def relationships_tmdl() -> str:
    relationships = [
        ("anomalies.file_name", "results.file_name"),
        ("audit_log.file_name", "results.file_name"),
    ]
    parts = []
    for from_col, to_col in relationships:
        parts.append(
            f"relationship {guid()}\n\tfromColumn: {from_col}\n\ttoColumn: {to_col}"
        )
    return "\n\n".join(parts)


def visual_path(report_root: Path, page_name: str, visual_name: str) -> Path:
    return report_root / "definition" / "pages" / page_name / "visuals" / visual_name / "visual.json"


def build_report(report_root: Path) -> None:
    write_json(report_root / "definition.pbir", make_definition_pbir())
    write_json(report_root / "definition" / "report.json", report_json())
    write_json(report_root / "definition" / "version.json", make_version_json())
    write_json(report_root / "definition" / "pages" / "pages.json", pages_json())

    write_json(report_root / "definition" / "pages" / "page_overview" / "page.json", page_json("page_overview", "Visao Geral"))
    write_json(report_root / "definition" / "pages" / "page_details" / "page.json", page_json("page_details", "Casos Detalhados"))
    write_json(report_root / "definition" / "pages" / "page_audit" / "page.json", page_json("page_audit", "Auditoria"))

    overview_visuals = [
        textbox_visual("title_overview", "NLC Document Auditor", 24, 14, 420, 36),
        card_visual("card_total_arquivos", "Total Arquivos", "Total Arquivos", 24, 64, 180, 100),
        card_visual("card_total_anomalias", "Total Anomalias", "Total Anomalias", 216, 64, 180, 100),
        card_visual("card_arquivos_suspeitos", "Arquivos Suspeitos", "Arquivos Suspeitos", 408, 64, 180, 100),
        card_visual("card_taxa_suspeita", "Taxa de Suspeita", "Taxa de Suspeita", 600, 64, 180, 100),
        card_visual("card_alertas", "Alertas de Processamento", "Alertas de Processamento", 792, 64, 180, 100),
        card_visual("card_taxa_llm", "Taxa LLM", "Taxa LLM", 984, 64, 180, 100),
        clustered_bar_visual("chart_tipo_anomalia", "Anomalias por Tipo", "anomalies", "tipo_anomalia", "Total Anomalias", 24, 188, 590, 500),
        clustered_bar_visual("chart_fornecedor", "Top Fornecedores com Anomalias", "anomalies", "fornecedor", "Total Anomalias", 638, 188, 618, 236),
        table_visual(
            "table_overview_cases",
            "Casos Criticos",
            [
                ("anomalies", "file_name", "arquivo"),
                ("anomalies", "numero_documento", "documento"),
                ("anomalies", "fornecedor", "fornecedor"),
                ("anomalies", "tipo_anomalia", "anomalia"),
                ("anomalies", "gravidade", "gravidade"),
                ("anomalies", "mensagem", "mensagem"),
            ],
            638,
            438,
            618,
            250,
        ),
    ]
    for visual in overview_visuals:
        write_json(visual_path(report_root, "page_overview", visual["name"]), visual)

    detail_visuals = [
        textbox_visual("title_details", "Casos Detalhados", 24, 14, 420, 36),
        table_visual(
            "table_detail_anomalies",
            "Detalhamento de Anomalias",
            [
                ("anomalies", "file_name", "arquivo"),
                ("anomalies", "numero_documento", "documento"),
                ("anomalies", "fornecedor", "fornecedor"),
                ("anomalies", "tipo_anomalia", "tipo"),
                ("anomalies", "codigo_anomalia", "codigo"),
                ("anomalies", "gravidade", "gravidade"),
                ("anomalies", "regra", "regra"),
                ("anomalies", "mensagem", "mensagem"),
            ],
            24,
            64,
            1232,
            624,
        ),
    ]
    for visual in detail_visuals:
        write_json(visual_path(report_root, "page_details", visual["name"]), visual)

    audit_visuals = [
        textbox_visual("title_audit", "Auditoria e Rastreabilidade", 24, 14, 520, 36),
        card_visual("card_eventos_auditoria", "Eventos de Auditoria", "Eventos de Auditoria", 24, 64, 220, 100),
        card_visual("card_providers", "Providers Distintos", "Providers Distintos", 256, 64, 220, 100),
        card_visual("card_prompts", "Prompts Distintos", "Prompts Distintos", 488, 64, 220, 100),
        clustered_bar_visual("chart_audit_event_type", "Eventos por Tipo", "audit_log", "event_type", "Eventos de Auditoria", 24, 188, 590, 500),
        table_visual(
            "table_audit_log",
            "Log de Auditoria",
            [
                ("audit_log", "file_name", "arquivo"),
                ("audit_log", "timestamp", "timestamp"),
                ("audit_log", "event_type", "evento"),
                ("audit_log", "rule", "regra"),
                ("audit_log", "outcome", "resultado"),
                ("audit_log", "details", "detalhes"),
            ],
            638,
            188,
            618,
            500,
        ),
    ]
    for visual in audit_visuals:
        write_json(visual_path(report_root, "page_audit", visual["name"]), visual)


def build_semantic_model(model_root: Path) -> None:
    write_json(model_root / "definition.pbism", make_definition_pbism())
    write_text(model_root / "definition" / "database.tmdl", "database\n\tcompatibilityLevel: 1601")
    write_text(model_root / "definition" / "model.tmdl", model_tmdl())
    write_text(model_root / "definition" / "relationships.tmdl", relationships_tmdl())
    write_text(model_root / "definition" / "tables" / "results.tmdl", results_tmdl())
    write_text(model_root / "definition" / "tables" / "anomalies.tmdl", anomalies_tmdl())
    write_text(model_root / "definition" / "tables" / "audit_log.tmdl", audit_log_tmdl())


def main() -> None:
    if not WORKBOOK_PATH.exists():
        raise SystemExit(f"Workbook not found: {WORKBOOK_PATH}")

    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    write_json(OUTPUT_ROOT / "NLC.pbip", make_pbip())
    build_report(OUTPUT_ROOT / "NLC.Report")
    build_semantic_model(OUTPUT_ROOT / "NLC.SemanticModel")

    print(OUTPUT_ROOT)


if __name__ == "__main__":
    main()
