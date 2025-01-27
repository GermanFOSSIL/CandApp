import streamlit as st
import pandas as pd
import random
import string
import os
from datetime import date, timedelta
import io

# IMPORTANTE: Usamos fpdf2 (ya instalada con pip install fpdf2)
from fpdf import FPDF
import qrcode

# Plotly para gráficos
import plotly.express as px
import plotly.io as pio
pio.kaleido.scope.default_format = "png"  # Para exportar a PNG con Plotly

# --------------------------------------------------------------------------------
# USUARIOS (demo)
# --------------------------------------------------------------------------------
users_data = {
    "admin": {"password": "admin", "role": "admin"},
    "operador": {"password": "123", "role": "operador"},
    "invitado": {"password": "guest", "role": "invitado"},
}

# --------------------------------------------------------------------------------
# ARCHIVOS DE EJEMPLO
# --------------------------------------------------------------------------------
LOGO_PATH = "logo1.png"
EXCEL_FILE_LOTO = "candados_data.xlsx"

# --------------------------------------------------------------------------------
# MAIN
# --------------------------------------------------------------------------------
def main():
    st.set_page_config(page_title="CandApp by Fossil", layout="wide")

    # Manejo de sesión
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.current_user = None
        st.session_state.role = None

    # Cargar LOTO
    if "candados_df" not in st.session_state:
        st.session_state["candados_df"] = load_loto_excel()

    # Cargar “itembook” para precomisionado
    if "itembook_df" not in st.session_state:
        st.session_state["itembook_df"] = generate_itembook()

    if not st.session_state.authenticated:
        apply_custom_styles()
        login()
    else:
        apply_custom_styles()
        # Muestra el logo en la parte superior (en todas las secciones)
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=250)
        top_menu()

# --------------------------------------------------------------------------------
# LOGIN
# --------------------------------------------------------------------------------
def login():
    st.markdown(
        """
        <div style="text-align: center; margin-top: 50px;">
            <img src="logo.png" alt="Logo" style="width: 150px; margin-bottom: 20px;">
            <h1 style="color: #4dd0e1;">CandApp by FOSSIL</h1>
            <h3 style="color: #80cbc4; margin-bottom: 20px;">Iniciar sesión</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("login_form"):
        username = st.text_input("Usuario", placeholder="Ingresa tu usuario")
        password = st.text_input("Contraseña", type="password", placeholder="Ingresa tu contraseña")
        submitted = st.form_submit_button("Entrar")

        if submitted:
            if username in users_data:
                if password == users_data[username]["password"]:
                    # Login correcto
                    st.session_state.authenticated = True
                    st.session_state.current_user = username
                    st.session_state.role = users_data[username]["role"]
                    st.experimental_rerun()
                else:
                    st.error("Contraseña incorrecta.")
            else:
                st.error("Usuario no encontrado.")

# --------------------------------------------------------------------------------
# MENÚ PRINCIPAL (solapas arriba)
# --------------------------------------------------------------------------------
def top_menu():
    # 3 tabs principales: LOTO, Precomisionado, Salir
    tabs = st.tabs(["LOTO", "Precomisionado", "Salir"])

    with tabs[0]:
        # Mostramos la sección de LOTO
        show_loto_section()

    with tabs[1]:
        # Mostramos la sección de Precomisionado
        show_precomisionado_section()

    with tabs[2]:
        # Opción de Cerrar Sesión
        st.warning("¿Deseas cerrar sesión?")
        if st.button("Cerrar Sesión"):
            st.session_state.authenticated = False
            st.session_state.current_user = None
            st.session_state.role = None
            st.experimental_rerun()

# --------------------------------------------------------------------------------
# SECCIÓN LOTO (subsolapas)
# --------------------------------------------------------------------------------
def show_loto_section():
    st.markdown("<h2 style='text-align:center; color:#4dd0e1;'>Sección LOTO</h2>", unsafe_allow_html=True)

    # Agregamos una sub-pestaña para el formulario dinámico
    sub_tabs = st.tabs([
        "Dashboard",
        "Registrar Candado (Clásico)",
        "Registrar Candado (Dinámico)",
        "Editar/Borrar Candado",
        "Generar Reporte Excel",
        "Usuarios"
    ])

    with sub_tabs[0]:
        show_dashboard()

    # ----------------------
    # Registrador Clásico
    # ----------------------
    with sub_tabs[1]:
        if st.session_state.role in ["admin", "operador"]:
            # Llamamos a la función original (NO se elimina)
            input_data()
        else:
            st.error("No tienes permiso (operador o admin) para Registrar Candado.")

    # ----------------------
    # Registrador Dinámico
    # ----------------------
    with sub_tabs[2]:
        if st.session_state.role in ["admin", "operador"]:
            registrar_candado_dinamico()
        else:
            st.error("No tienes permiso (operador o admin) para Registrar Candado.")

    # ----------------------
    # Editar/Borrar
    # ----------------------
    with sub_tabs[3]:
        if st.session_state.role == "admin":
            edit_or_delete_candado()
        else:
            st.error("Solo un admin puede Editar o Borrar Candados.")

    # ----------------------
    # Generar Reporte
    # ----------------------
    with sub_tabs[4]:
        if st.session_state.role in ["admin", "operador"]:
            generate_excel()
        else:
            st.error("Solo operador/admin pueden generar reportes.")

    # ----------------------
    # Usuarios
    # ----------------------
    with sub_tabs[5]:
        if st.session_state.role == "admin":
            manage_users()
        else:
            st.error("Solo admin puede administrar usuarios.")

# --------------------------------------------------------------------------------
# DASHBOARD LOTO
# --------------------------------------------------------------------------------
def show_dashboard():
    st.markdown("<h1 style='text-align:center; color:#4dd0e1;'>Lockout-Tagout Dashboard</h1>", unsafe_allow_html=True)
    df = st.session_state["candados_df"]

    if not df.empty:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("### Total Locks")
            st.metric(label="", value=len(df))
        with col2:
            st.markdown("### Activos")
            activos = (df["Estado"] == "Activo").sum()
            st.metric(label="", value=int(activos))
        with col3:
            st.markdown("### Alertas")
            alertas = (df["Valor"] > 200).sum() if "Valor" in df.columns else 0
            st.metric(label="", value=int(alertas))

        # Ejemplo de gráfico
        st.markdown("<h2 style='color:#4dd0e1;'>Gráfico de Candados Activos</h2>", unsafe_allow_html=True)
        fig = plot_active_locks(df)
        st.plotly_chart(fig, use_container_width=True)

        # Actividad reciente
        st.markdown("<h2 style='color:#4dd0e1;'>Recent Activity</h2>", unsafe_allow_html=True)
        df_sorted = df.sort_values("Fecha", ascending=False)
        for _, row in df_sorted.iterrows():
            st.markdown(
                f"<div style='background:#1c2b3a; padding:10px; border-radius:5px; margin-bottom:10px;'>"
                f"<span style='color:#ffffff;'>"
                f"ID: {row['ID']} | Descripción: {row['Descripción']} | "
                f"Responsable: {row['Responsable']} | Estado: {row['Estado']} | "
                f"Fecha: {row['Fecha']}"
                f"</span></div>",
                unsafe_allow_html=True
            )
    else:
        st.warning("No hay candados registrados.")

def plot_active_locks(df):
    df_copy = df.copy()
    df_copy["Fecha"] = pd.to_datetime(df_copy["Fecha"], errors="coerce")

    df_activos = df_copy[df_copy["Estado"] == "Activo"]
    df_count = df_activos.groupby(df_activos["Fecha"].dt.date).size().reset_index(name="count")

    fig = px.line(
        df_count,
        x="Fecha",
        y="count",
        markers=True,
        title="Tendencia de Candados Activos",
    )
    fig.update_layout(
        plot_bgcolor="#1c2b3a",
        paper_bgcolor="#0e1a2b",
        font_color="#ffffff",
        title_font_color="#4dd0e1"
    )
    fig.update_traces(line_color="#4dd0e1", marker_color="#4dd0e1")
    return fig

# --------------------------------------------------------------------------------
# REGISTRO CLÁSICO (NO SE ELIMINA)
# --------------------------------------------------------------------------------
def input_data():
    """
    Función original para registrar candado de forma clásica.
    Se mantiene intacta.
    """
    st.markdown("<h1 style='text-align:center; color:#4dd0e1;'>Registrar Nuevo Candado (Clásico)</h1>", unsafe_allow_html=True)
    with st.form("register_lock"):
        id_candado = st.text_input("ID Candado")
        descripcion = st.text_input("Descripción")
        responsable = st.text_input("Responsable")
        fecha_reg = st.date_input("Fecha", value=date.today())
        estado_check = st.checkbox("Activo", value=True)

        tipo = st.selectbox("Tipo de registro", ["Candado Activo", "Candado Inactivo", "Caja LOTO"])
        ptw = st.text_input("Permiso de trabajo (PTW)")
        valor = st.number_input("Valor", min_value=0, max_value=99999, value=0)

        uploaded_file = st.file_uploader("Adjuntar PDF (opcional)", type=["pdf"])

        submitted = st.form_submit_button("Guardar Registro")

        if submitted:
            df = st.session_state["candados_df"]
            new_row = {
                "ID": id_candado,
                "Descripción": descripcion,
                "Responsable": responsable,
                "Fecha": str(fecha_reg),
                "Estado": "Activo" if estado_check else "Inactivo",
                "Tipo": tipo,
                "PTW": ptw,
                "Valor": valor,
            }
            if uploaded_file is not None:
                file_bytes = uploaded_file.read()
                new_row["PDF_Adjunto"] = file_bytes
            else:
                new_row["PDF_Adjunto"] = None

            from pandas import DataFrame, concat
            new_df = DataFrame([new_row])
            df = concat([df, new_df], ignore_index=True)

            st.session_state["candados_df"] = df
            save_loto_excel(df)
            st.success("Registro guardado exitosamente.")

# --------------------------------------------------------------------------------
# NUEVO: REGISTRAR CANDADO DINÁMICO (CON QR)
# --------------------------------------------------------------------------------
def registrar_candado_dinamico():
    """
    NUEVA función para registrar candados a partir de un Excel
    con field_type, label, default, options.
    Genera un PDF con código QR.
    """
    st.markdown("<h1 style='text-align:center; color:#4dd0e1;'>Registrar Nuevo Candado (Dinámico)</h1>", 
                unsafe_allow_html=True)

    # Subir Excel que define los campos
    form_excel = st.file_uploader("Subir Excel que define los campos (field_type, label, default, options)", 
                                  type=["xlsx", "xls"])
    if not form_excel:
        st.info("Por favor, sube un archivo Excel para generar el formulario dinámico.")
        return

    # Leemos la definición
    try:
        df_form_def = pd.read_excel(form_excel)
    except Exception as e:
        st.error(f"Error leyendo el Excel: {e}")
        return

    st.write("Completa el formulario a continuación. Los campos provienen del Excel subido.")
    form_values = {}

    with st.form("candado_dynamic_form"):
        for i, row in df_form_def.iterrows():
            field_type = str(row.get("field_type", "")).lower().strip()
            label = row.get("label", f"Campo_{i}")
            default = row.get("default", "")
            options = row.get("options", "")

            if field_type == "text":
                form_values[label] = st.text_input(label, value=str(default))

            elif field_type == "number":
                try:
                    val_num = float(default)
                except:
                    val_num = 0
                form_values[label] = st.number_input(label, value=val_num)

            elif field_type == "checkbox":
                default_bool = (str(default).lower() == "true")
                form_values[label] = st.checkbox(label, value=default_bool)

            elif field_type == "select":
                # 'options' -> "candado activo, candado inactivo, caja loto"
                opt_list = [o.strip() for o in str(options).split(",")]
                if default in opt_list:
                    idx = opt_list.index(default)
                else:
                    idx = 0
                form_values[label] = st.selectbox(label, opt_list, index=idx)

            elif field_type == "date":
                import datetime
                try:
                    val_date = pd.to_datetime(default).date()
                except:
                    val_date = datetime.date.today()
                form_values[label] = st.date_input(label, value=val_date)

            else:
                # Por defecto, text_input
                form_values[label] = st.text_input(label, value=str(default))

        submitted = st.form_submit_button("Guardar Registro")

    if submitted:
        # Guardar en DF
        df = st.session_state["candados_df"]

        # Aseguramos que haya un campo "ID"
        if "ID" not in form_values:
            import uuid
            form_values["ID"] = "CD-" + str(uuid.uuid4())[:8]

        new_df = pd.DataFrame([form_values])
        df = pd.concat([df, new_df], ignore_index=True)
        st.session_state["candados_df"] = df
        save_loto_excel(df)

        st.success("Registro guardado exitosamente con datos dinámicos.")

        # Generar PDF con QR
        candado_id = form_values["ID"]
        # Link ejemplo para el QR (cámbialo a tu dominio real)
        link_qr = f"http://miapp.com/loto?id={candado_id}"
        pdf_bytes = generar_pdf_dinamico_qr(form_values, link_qr)

        st.download_button(
            label="Descargar PDF con QR",
            data=pdf_bytes,
            file_name=f"candado_{candado_id}.pdf",
            mime="application/pdf"
        )

def generar_pdf_dinamico_qr(data_dict: dict, link: str) -> bytes:
    """
    Genera un PDF con la info del candado y un QR code incrustado,
    apuntando a 'link'.
    """
    # Generamos QR en memoria
    qr_img = qrcode.make(link)
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)

    pdf = FPDF()
    pdf.add_font("DejaVu", "", "DejaVuSansCondensed.ttf", uni=True)
    pdf.set_font("DejaVu", "", 14)
    pdf.add_page()

    pdf.cell(0, 10, txt="Registro de Candado (Dinámico)", ln=True, align="C")
    pdf.ln(5)

    # Imprimimos la data
    pdf.set_font("DejaVu", "", 12)
    for k, v in data_dict.items():
        pdf.multi_cell(0, 8, f"{k}: {v}")
    pdf.ln(5)

    # Guardamos QR como archivo temporal para insertarlo
    temp_qr = "temp_qr.png"
    with open(temp_qr, "wb") as f:
        f.write(qr_buffer.getvalue())

    pdf.image(temp_qr, x=10, y=None, w=40)
    pdf.ln(40)
    pdf.multi_cell(0, 8, f"Escanea el QR para ver detalles:\n{link}")

    # Convertimos a bytes
    pdf_bytes = pdf.output(dest="S")

    # Limpieza
    if os.path.exists(temp_qr):
        os.remove(temp_qr)

    return pdf_bytes

# --------------------------------------------------------------------------------
# EDITAR/BORRAR CANDADO
# --------------------------------------------------------------------------------
def edit_or_delete_candado():
    st.markdown("<h1 style='text-align:center; color:#4dd0e1;'>Editar o Borrar Candados</h1>", unsafe_allow_html=True)
    df = st.session_state["candados_df"]
    if df.empty:
        st.info("No hay candados para editar/borrar.")
        return

    st.subheader("Candados disponibles:")
    df_display = df[["ID", "Descripción", "Responsable", "Estado", "Fecha"]].reset_index(drop=True)
    select_idx = st.selectbox(
        "Elige un candado para editar/borrar:",
        options=df_display.index,
        format_func=lambda i: f"ID: {df_display.loc[i, 'ID']} | Desc: {df_display.loc[i, 'Descripción']}"
    )
    row_data = df.iloc[select_idx]

    col_left, col_right = st.columns([1,1])
    with col_left:
        if st.button("Editar"):
            st.session_state["edit_mode"] = select_idx
    with col_right:
        if st.button("Borrar"):
            df.drop(df.index[select_idx], inplace=True)
            st.session_state["candados_df"] = df
            save_loto_excel(df)
            st.success("Candado borrado.")
            st.experimental_rerun()

    if "edit_mode" in st.session_state and st.session_state["edit_mode"] == select_idx:
        with st.expander(f"Editando ID: {row_data['ID']}", expanded=True):
            edit_candado_form(select_idx)

def edit_candado_form(idx):
    df = st.session_state["candados_df"]
    candado = df.loc[idx]
    with st.form(f"edit_form_{idx}", clear_on_submit=True):
        new_desc = st.text_input("Descripción", value=candado["Descripción"])
        new_resp = st.text_input("Responsable", value=candado["Responsable"])
        new_fecha = st.date_input("Fecha", value=pd.to_datetime(candado["Fecha"]))
        new_estado = st.selectbox("Estado", ["Activo", "Inactivo"], index=0 if candado["Estado"] == "Activo" else 1)
        new_valor = st.number_input("Valor", min_value=0, max_value=999999, value=int(candado.get("Valor", 0)))

        submitted = st.form_submit_button("Guardar Cambios")
        if submitted:
            df.at[idx, "Descripción"] = new_desc
            df.at[idx, "Responsable"] = new_resp
            df.at[idx, "Fecha"] = str(new_fecha)
            df.at[idx, "Estado"] = new_estado
            df.at[idx, "Valor"] = new_valor

            st.session_state["candados_df"] = df
            save_loto_excel(df)
            st.success("Cambios guardados.")
            del st.session_state["edit_mode"]
            st.experimental_rerun()

# --------------------------------------------------------------------------------
# GENERAR REPORTE EXCEL (LOTO)
# --------------------------------------------------------------------------------
def generate_excel():
    st.markdown("<h1 style='text-align:center; color:#4dd0e1;'>Generar Reporte Excel</h1>", unsafe_allow_html=True)
    df = st.session_state["candados_df"]
    if not df.empty:
        if st.button("Generar y Descargar Excel"):
            excel_bytes = generate_excel_file(df)
            st.download_button(
                label="Descargar Reporte en Excel",
                data=excel_bytes,
                file_name="reporte_candados.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.warning("No hay datos para exportar.")

def generate_excel_file(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="ReporteCandados")
    output.seek(0)
    return output.getvalue()

# --------------------------------------------------------------------------------
# ADMINISTRAR USUARIOS (solo admin)
# --------------------------------------------------------------------------------
def manage_users():
    st.markdown("<h1 style='text-align:center; color:#4dd0e1;'>Administrar Usuarios</h1>", unsafe_allow_html=True)

    st.subheader("Usuarios actuales:")
    for user, info in users_data.items():
        st.write(f"- **{user}** (rol: {info['role']})")

    st.write("---")
    st.subheader("Crear nuevo usuario")
    with st.form("new_user_form"):
        new_username = st.text_input("Nombre de usuario")
        new_password = st.text_input("Contraseña", type="password")
        new_role = st.selectbox("Rol", ["admin", "operador", "invitado"])
        create_submitted = st.form_submit_button("Crear Usuario")
        if create_submitted:
            if new_username in users_data:
                st.error("Ese usuario ya existe.")
            else:
                users_data[new_username] = {"password": new_password, "role": new_role}
                st.success(f"Usuario '{new_username}' creado con rol '{new_role}'.")

# --------------------------------------------------------------------------------
# SECCIÓN PRECOMISIONADO (subsolapas)
# --------------------------------------------------------------------------------
def show_precomisionado_section():
    st.markdown("<h2 style='text-align:center; color:#4dd0e1;'>Precomisionado - Dossier Digital</h2>", unsafe_allow_html=True)

    sub_tabs = st.tabs(["Items", "Generar ITR (PDF)", "Formulario Excel Dinámico"])
    with sub_tabs[0]:
        show_item_list()       # Lista de Items
    with sub_tabs[1]:
        generate_itr_pdf()     # Form para generar PDF ITR
    with sub_tabs[2]:
        run_document_form()    # Nuevo: formulario generado desde Excel

# --------------------------------------------------------------------------------
# SUB-SECCIÓN: LISTA DE ITEMS
# --------------------------------------------------------------------------------
def show_item_list():
    st.write("**Items** (ejemplo) para Precomisionado:")
    df_items = st.session_state["itembook_df"]
    st.dataframe(df_items)

# --------------------------------------------------------------------------------
# SUB-SECCIÓN: GENERAR ITR (PDF) - USO fpdf2 con UNICODE
# --------------------------------------------------------------------------------
def generate_itr_pdf():
    st.write("Completa el formulario de ITR y genera un PDF similar al ejemplo.")

    df_items = st.session_state["itembook_df"]
    if df_items.empty:
        st.warning("No hay items en la base de datos.")
        return

    item_id = st.selectbox("Seleccionar ItemID", df_items["ItemID"].unique())
    row_item = df_items[df_items["ItemID"] == item_id].iloc[0]

    # Usamos un form para generar el PDF
    with st.form("itr_form"):
        equipo = st.text_input("Descripción del Equipo", value=row_item["Descripcion"])
        subsistema = st.text_input("Sub-sistema", "Tensión segura (ejemplo)")
        responsable = st.text_input("Responsable", "Ing. Precomisionado")
        comentarios = st.text_area("Comentarios", "Observaciones...")

        # Botón dentro del form
        submitted = st.form_submit_button("Generar PDF")

    # Si se presionó "Generar PDF"
    if submitted:
        pdf_bytes = generar_pdf_precom(row_item, equipo, subsistema, responsable, comentarios)
        st.session_state["pdf_bytes"] = pdf_bytes
        st.success("PDF generado con éxito. Descarga a continuación:")

    # Botón de descarga fuera del form
    if "pdf_bytes" in st.session_state and st.session_state["pdf_bytes"] is not None:
        st.download_button(
            label="Descargar ITR PDF",
            data=st.session_state["pdf_bytes"],
            file_name=f"ITR_{item_id}.pdf",
            mime="application/pdf"
        )

def generar_pdf_precom(item_row, equipo, subsistema, responsable, comentarios):
    pdf = FPDF()
    pdf.add_font("DejaVu", "", "DejaVuSansCondensed.ttf", uni=True)
    pdf.set_font("DejaVu", "", 14)

    pdf.add_page()
    pdf.cell(0, 10, txt="E11A - Centro de Control de Motores (BT/AT) (MCC)", ln=1, align="C")
    pdf.set_font("DejaVu", "", 12)
    pdf.cell(0, 10, txt="Completamiento de la Construcción", ln=1, align="C")

    pdf.ln(5)
    pdf.cell(0, 8, txt=f"N° de Tag: {item_row['ItemID']}", ln=1)
    pdf.cell(0, 8, txt=f"Descripción del Equipo: {equipo}", ln=1)
    pdf.cell(0, 8, txt=f"N° de Subsistema: {subsistema}", ln=1)
    pdf.cell(0, 8, txt=f"Proyecto: {item_row['Proyecto']}", ln=1)
    pdf.cell(0, 8, txt=f"Responsable: {responsable}", ln=1)

    pdf.ln(5)
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 8, txt="Items para verificar:", ln=1)
    pdf.set_font("DejaVu", "", 12)
    pdf.multi_cell(0, 8, "- Placa de identificación\n- Dispositivo de fijación\n- MCCB, contactores...")

    pdf.ln(5)
    pdf.cell(0, 8, txt="Comentarios / Observaciones:", ln=1)
    pdf.multi_cell(0, 8, comentarios)
    pdf.ln(10)

    pdf.cell(0, 8, txt="Firmado por: _______________________", ln=1)
    pdf.cell(0, 8, txt="Fecha: _____________________________", ln=1)

    pdf_bytes = pdf.output(dest="S")
    return pdf_bytes

# --------------------------------------------------------------------------------
# FORMULARIO EXCEL DINÁMICO (con PDF fpdf2 y Unicode) - DEMO en Precomisionado
# --------------------------------------------------------------------------------
def run_document_form():
    """
    Permite subir un Excel con la definición del formulario,
    generar dinámicamente los campos y exportar a PDF.
    """
    st.write("### Crear formulario a partir de un archivo Excel")

    uploaded_file = st.file_uploader("Subir archivo Excel", type=["xlsx", "xls"])
    if uploaded_file is None:
        st.info("Por favor, sube un archivo para continuar.")
        return

    # Intentamos leer el Excel
    try:
        df_def = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Error al leer el Excel: {e}")
        return

    st.write("Se generará un formulario basado en las filas del Excel.")
    st.write("Columnas esperadas: `field_type`, `label`, `options`, `default` (puede variar)")

    # Diccionario para almacenar respuestas
    form_values = {}

    # Creamos un FORM para recopilar los datos
    with st.form("dynamic_form"):
        for i, row in df_def.iterrows():
            field_type = str(row.get("field_type", "")).lower()
            label = row.get("label", f"Campo {i}")
            options = row.get("options", "")
            default = row.get("default", "")

            if field_type == "text":
                form_values[label] = st.text_input(label, value=str(default))

            elif field_type == "checkbox":
                # Convertimos default a boolean si es 'True'/'False'
                default_bool = (str(default).lower() == "true")
                form_values[label] = st.checkbox(label, value=default_bool)

            elif field_type == "select":
                # Por ejemplo: 'OK, Dañado, Revisar'
                opt_list = [o.strip() for o in str(options).split(",")]
                if default not in opt_list:
                    default_index = 0
                else:
                    default_index = opt_list.index(default)
                form_values[label] = st.selectbox(label, opt_list, index=default_index)

            else:
                # Si no reconoce el tipo, usa text_input por defecto
                form_values[label] = st.text_input(label, value=str(default))

        submitted = st.form_submit_button("Generar PDF")

    # Manejo posterior al submit
    if submitted:
        pdf_bytes = generar_pdf_dinamico(form_values)
        st.success("Se generó el PDF con la información. Descarga abajo:")

        # Botón de descarga (fuera de un form)
        st.download_button(
            label="Descargar PDF",
            data=pdf_bytes,
            file_name="formulario_generado.pdf",
            mime="application/pdf"
        )

def generar_pdf_dinamico(form_data: dict) -> bytes:
    """
    Crea un PDF con la info de form_data, usando fpdf2 con fuente Unicode.
    """
    pdf = FPDF()
    pdf.add_font("DejaVu", "", "DejaVuSansCondensed.ttf", uni=True)
    pdf.set_font("DejaVu", "", 14)

    pdf.add_page()
    pdf.cell(0, 10, txt="Formulario Dinámico - Resultado", ln=True, align="C")
    pdf.set_font("DejaVu", "", 12)
    pdf.ln(5)

    for label, value in form_data.items():
        pdf.multi_cell(0, 8, f"{label}: {value}")
        pdf.ln(2)

    pdf_bytes = pdf.output(dest="S")
    return pdf_bytes

# --------------------------------------------------------------------------------
# GENERACIÓN DE ITEMS DE EJEMPLO (Precomisionado)
# --------------------------------------------------------------------------------
def generate_itembook():
    proyectos = ["Proyecto A"] * 20 + ["Proyecto B"] * 20
    rows = []
    for i in range(40):
        item_id = f"ITM-{i+1:03d}"
        desc = "Item Ejemplo " + "".join(random.choices(string.ascii_uppercase, k=2))
        row = {
            "Proyecto": proyectos[i],
            "ItemID": item_id,
            "Descripcion": desc,
        }
        rows.append(row)
    return pd.DataFrame(rows)

# --------------------------------------------------------------------------------
# LECTURA/ESCRITURA DE CANDADOS (LOTO)
# --------------------------------------------------------------------------------
def load_loto_excel():
    if not os.path.exists(EXCEL_FILE_LOTO):
        df = prepopulate_loto(n=30)
        df.to_excel(EXCEL_FILE_LOTO, index=False)
    else:
        df = pd.read_excel(EXCEL_FILE_LOTO)
    return df

def save_loto_excel(df):
    df.to_excel(EXCEL_FILE_LOTO, index=False)

def prepopulate_loto(n=30):
    rows = []
    today = date.today()
    for _ in range(n):
        random_id = "".join(random.choices(string.digits, k=6))
        desc = "Candado Demo " + "".join(random.choices(string.ascii_uppercase, k=2))
        resp = random.choice(["Juan", "Maria", "Pedro", "Ana", "Gonzalo", "Carla"])
        days_back = random.randint(0, 60)
        fecha_rand = today - timedelta(days=days_back)
        estado = random.choice(["Activo", "Inactivo"])
        tipo = random.choice(["Candado Activo", "Candado Inactivo", "Caja LOTO"])
        ptw = f"PTW-{random.randint(100,999)}"
        valor = random.randint(0,300)
        row = {
            "ID": random_id,
            "Descripción": desc,
            "Responsable": resp,
            "Fecha": str(fecha_rand),
            "Estado": estado,
            "Tipo": tipo,
            "PTW": ptw,
            "Valor": valor,
            "PDF_Adjunto": None,
        }
        rows.append(row)
    return pd.DataFrame(rows)

# --------------------------------------------------------------------------------
# APLICAR ESTILOS (CSS) TEMA OSCURO
# --------------------------------------------------------------------------------
def apply_custom_styles():
    st.markdown(
        """
        <style>
            [data-testid="stAppViewContainer"] {
                background-color: #0e1a2b !important;
            }
            [data-testid="stHeader"] {
                background-color: #0e1a2b !important;
            }
            html, body, [class*="css"]  {
                color: #ffffff !important;
            }
            /* Ajuste de estilo para las tabs (solapas) */
            .stTabs [role="tablist"] button [data-baseweb="tab"] {
                color: #ffffff !important;
                background-color: #0e1a2b !important;
                border: 1px solid #4dd0e1 !important;
            }
            .stTabs [role="tablist"] button[aria-selected="true"] {
                background-color: #1c2b3a !important;
                color: #4dd0e1 !important;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

# --------------------------------------------------------------------------------
# EJECUTAR
# --------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
