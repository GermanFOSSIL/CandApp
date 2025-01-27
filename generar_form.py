import pandas as pd

# Definimos cada fila como un diccionario
rows = [
    {"field_type": "text",   "label": "N° de Tag",                                                                "options": "",                         "default": ""},
    {"field_type": "text",   "label": "Descripción del Equipo",                                                   "options": "",                         "default": ""},
    {"field_type": "text",   "label": "N° de Sistema",                                                            "options": "",                         "default": ""},
    {"field_type": "text",   "label": "N° de Subsistema",                                                         "options": "",                         "default": ""},
    {"field_type": "text",   "label": "Ubicación",                                                                "options": "",                         "default": ""},
    {"field_type": "text",   "label": "Ficha Técnica",                                                            "options": "",                         "default": ""},
    {"field_type": "text",   "label": "Tipo de Referencia",                                                       "options": "",                         "default": ""},
    {"field_type": "text",   "label": "Voltaje",                                                                  "options": "",                         "default": ""},
    {"field_type": "text",   "label": "Tipo",                                                                     "options": "",                         "default": ""},
    {"field_type": "text",   "label": "Core",                                                                     "options": "",                         "default": ""},
    {"field_type": "text",   "label": "Tamaño",                                                                   "options": "",                         "default": ""},
    {"field_type": "text",   "label": "Desde",                                                                    "options": "",                         "default": ""},
    {"field_type": "text",   "label": "Hasta",                                                                    "options": "",                         "default": ""},
    {"field_type": "text",   "label": "Marca",                                                                    "options": "",                         "default": ""},
    {"field_type": "text",   "label": "Modelo",                                                                   "options": "",                         "default": ""},
    {"field_type": "text",   "label": "N° de Serie",                                                              "options": "",                         "default": ""},
    {"field_type": "text",   "label": "Fecha de Vencimiento",                                                     "options": "",                         "default": ""},
    {"field_type": "select", "label": "1) Placa de identificación / etiquetado / etiquetas de identificación correctos",           "options": "OK, N/A, PunchList",  "default": "OK"},
    {"field_type": "select", "label": "2) Verificar ordenamiento y precintado de partes de conexión interna",                 "options": "OK, N/A, PunchList",  "default": "OK"},
    {"field_type": "select", "label": "3) Cable protegido mecánicamente",                                         "options": "OK, N/A, PunchList",       "default": "OK"},
    {"field_type": "select", "label": "4) Terminación correcta",                                                  "options": "OK, N/A, PunchList",       "default": "OK"},
    {"field_type": "select", "label": "5) Verificar continuidad (Probar todos los conductores, incluso la pantalla)", "options": "OK, N/A, PunchList",   "default": "OK"},
    {"field_type": "select", "label": "6) Prensacables / tuercas de seguridad / lubricante aprobado colocados",   "options": "OK, N/A, PunchList",       "default": "OK"},
    {"field_type": "select", "label": "7) Resistencia de aislamiento (250 Voltios Megger Min., 100MΩ)",           "options": "OK, N/A, PunchList",       "default": "OK"},
    {"field_type": "select", "label": "8) Armadura – tierra MΩ",                                                 "options": "OK, N/A, PunchList",       "default": "OK"},
    {"field_type": "select", "label": "9) Blindaje total – tierra MΩ",                                            "options": "OK, N/A, PunchList",       "default": "OK"},
    {"field_type": "select", "label": "10) Todos los conductores – tierra MΩ",                                    "options": "OK, N/A, PunchList",       "default": "OK"},
    {"field_type": "select", "label": "11) Cada par a blindaje MΩ",                                              "options": "OK, N/A, PunchList",       "default": "OK"},
    {"field_type": "select", "label": "12) Conductores par MΩ",                                                  "options": "OK, N/A, PunchList",       "default": "OK"},
    {"field_type": "select", "label": "13) Blindaje a blindaje MΩ",                                              "options": "OK, N/A, PunchList",       "default": "OK"},
    {"field_type": "select", "label": "14) Radio de curvatura satisfactorio",                                     "options": "OK, N/A, PunchList",       "default": "OK"},
    {"field_type": "select", "label": "15) Puesta a tierra según especificaciones",                               "options": "OK, N/A, PunchList",       "default": "OK"},
    {"field_type": "select", "label": "16) Pantalla correcta",                                                   "options": "OK, N/A, PunchList",       "default": "OK"},
    {"field_type": "select", "label": "17) Confirmar hilos vacante y pantallas puestas a tierra según especificaciones", "options": "OK, N/A, PunchList",  "default": "OK"},
    {"field_type": "text",   "label": "Comentarios / Observaciones",                                              "options": "",                         "default": ""},
]

# Convertimos a DataFrame y exportamos
df = pd.DataFrame(rows)
df.to_excel("form_definition.xlsx", index=False)
print("Archivo 'form_definition.xlsx' creado exitosamente.")
