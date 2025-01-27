import streamlit as st
from datetime import datetime
import pandas as pd
import random
import string
import os
from datetime import date, timedelta
import io
import tempfile
from fpdf import FPDF
import qrcode
import plotly.express as px
import plotly.io as pio
pio.kaleido.scope.default_format = "png"

# =============================================================================
# CONFIGURACIÓN INICIAL (ORIGINAL)
# =============================================================================
LOGO_PATH = "logo1.png"  # ¡Archivo obligatorio en la misma carpeta!
EXCEL_FILE_LOTO = "candados_data.xlsx"
EXCEL_FILE_SIMOPS = "simops_data.xlsx"  # Nuevo archivo para almacenar datos de SIMOPS

# -----------------------------------------------------------------------------
# USUARIOS DEMO (ORIGINAL)
# -----------------------------------------------------------------------------
users_data = {
    "admin": {"password": "admin", "role": "admin"},
    "admin2": {"password": "admin2", "role": "admin2"},
    "operador": {"password": "123", "role": "operador"},
    "invitado": {"password": "guest", "role": "invitado"},
}

# =============================================================================
# TARJETA LOTO PROFESIONAL (NUEVO DISEÑO)
# =============================================================================
def generate_loto_card(row) -> bytes:
    """
    Genera la tarjeta LOTO en PDF con diseño profesional.
    """
    class LotoPDF(FPDF):
        def __init__(self):
            super().__init__()
            self.page_width = 85  # Ancho tarjeta (85 mm)
            self.page_height = 140  # Alto tarjeta (140 mm)
            self.set_auto_page_break(False)
            
        def header(self):
            # Fondo rojo con borde
            self.set_fill_color(178, 34, 34)
            self.rect(0, 0, self.page_width, self.page_height, 'F')
            self.set_draw_color(0, 0, 0)
            self.set_line_width(1.5)
            self.rect(3, 3, self.page_width - 6, self.page_height - 6, 'D')

            # Icono de advertencia
            self.image("warning_icon.png", 
                       x=(self.page_width - 18)/2, 
                       y=8, 
                       w=18)

            # Textos superiores
            self.set_text_color(255, 255, 255)
            self.set_font("Arial", 'B', 14)
            self.set_xy(0, 28)
            self.cell(self.page_width, 6, "PELIGRO", 0, 0, 'C')
            
            textos = [
                "ENERGÍA BLOQUEADA",
                "NO OPERAR/RETIRAR",
                "INCUMPLIMIENTO = SANCIÓN"
            ]
            
            y = 40
            for texto in textos:
                self.set_xy(0, y)
                self.cell(self.page_width, 5, texto, 0, 0, 'C')
                y += 7

            # Logo ampliado (60mm de ancho)
            logo_width = 60
            self.image(LOGO_PATH, 
                       x=(self.page_width - logo_width)/2, 
                       y=70,  
                       w=logo_width)

        def footer(self):
            # Fondo blanco para datos técnicos (ajustado)
            self.set_fill_color(255, 255, 255)
            self.rect(10, 110, self.page_width - 20, 25, 'F')  # Nueva posición
            self.set_draw_color(0, 0, 0)
            self.rect(10, 110, self.page_width - 20, 25, 'D')
            
            # Datos técnicos (corregido "Eecha" -> "Fecha")
            self.set_text_color(0, 0, 0)
            self.set_font("Arial", 'B', 10)
            data = [
                f"No: {row.get('NoCandado','')}",
                f"Área: {row.get('Area','')}",
                f"Responsable: {row.get('EjecPorNombre','')}",
                f"Fecha: {row.get('Fecha','')}"
            ]
            
            y = 115  # Posición alineada con el fondo
            for item in data:
                self.set_xy(12, y)
                self.cell(0, 5, item)
                y += 6

    pdf = LotoPDF()
    pdf.add_page(format=(pdf.page_width, pdf.page_height))
    return bytes(pdf.output(dest='S'))

# =============================================================================
# FUNCIONALIDAD ORIGINAL COMPLETA (SIN MODIFICAR) + NUEVA SECCIÓN SIMOPS
# =============================================================================
def main():
    """
    Punto de entrada principal de la aplicación Streamlit.
    """
    st.set_page_config(page_title="CandApp by Fossil", layout="wide")

    # Manejo de sesión
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.current_user = None
        st.session_state.role = None

    if "candados_df" not in st.session_state:
        st.session_state["candados_df"] = load_loto_excel()

    # Nuevo: SIMOPS
    if "simops_df" not in st.session_state:
        st.session_state["simops_df"] = load_simops_data()

    if "itembook_df" not in st.session_state:
        st.session_state["itembook_df"] = generate_itembook()

    # Login:
    if not st.session_state.authenticated:
        apply_custom_styles()
        login()
        st.stop()
    else:
        apply_custom_styles()
        st.image(LOGO_PATH, width=250)
        top_menu()

def login():
    """
    Pantalla de inicio de sesión.
    """
    st.markdown("""<div style="text-align: center; margin-top: 50px;">
        <img src="logo.png" alt="Logo" style="width: 150px; margin-bottom: 20px;">
        <h1 style="color: #4dd0e1;">CandApp by FOSSIL Energies</h1>
        <h3 style="color: #80cbc4; margin-bottom: 20px;">Iniciar sesión</h3></div>""", 
        unsafe_allow_html=True)

    with st.form("login_form"):
        username = st.text_input("Usuario", placeholder="Ingresa tu usuario")
        password = st.text_input("Contraseña", type="password", placeholder="Ingresa tu contraseña")
        submitted = st.form_submit_button("Entrar")

        if submitted:
            if username in users_data:
                if password == users_data[username]["password"]:
                    st.session_state.authenticated = True
                    st.session_state.current_user = username
                    st.session_state.role = users_data[username]["role"]
                    st.success("¡Bienvenido!")
                else:
                    st.error("Contraseña incorrecta.")
            else:
                st.error("Usuario no encontrado.")

def top_menu():
    """
    Muestra la barra de menús superior con pestañas.
    """
    tabs = st.tabs(["LOTO", "Precomisionado", "SIMOPS", "Salir"])

    with tabs[0]:
        show_loto_section()

    with tabs[1]:
        show_precomisionado_section()

    # NUEVO: SIMOPS
    with tabs[2]:
        show_simops_section()

    with tabs[3]:
        st.warning("¿Deseas cerrar sesión?")
        if st.button("Cerrar Sesión"):
            st.session_state.authenticated = False
            st.session_state.current_user = None
            st.session_state.role = None
            st.success("Sesión cerrada.")

# =============================================================================
# SECCIÓN LOTO
# =============================================================================
def show_loto_section():
    """
    Sección dedicada a LOTO.
    """
    st.markdown("<h2 style='text-align:center; color:#4dd0e1;'>Sección LOTO</h2>", unsafe_allow_html=True)
    sub_tabs = st.tabs(["Dashboard","Registrar Candado","Editar/Borrar Candado","Generar Reporte Excel/PDF","Usuarios"])
    
    with sub_tabs[0]:
        show_dashboard()
    with sub_tabs[1]: 
        if st.session_state.role in ["admin", "operador"]:
            input_data()
        else:
            st.error("No tienes permiso para Registrar Candado.")
    with sub_tabs[2]: 
        if st.session_state.role == "admin":
            edit_or_delete_candado()
        else:
            st.error("Solo un admin puede Editar/Borrar.")
    with sub_tabs[3]: 
        if st.session_state.role in ["admin", "operador"]:
            generate_reports()
        else:
            st.error("Solo operador/admin pueden generar reportes.")
    with sub_tabs[4]: 
        if st.session_state.role == "admin":
            manage_users()
        else:
            st.error("Solo admin puede administrar usuarios.")

def show_dashboard():
    """
    Muestra un pequeño dashboard con métrica y gráfico de tendencia.
    """
    st.markdown("<h1 style='text-align:center; color:#4dd0e1;'>Lockout-Tagout Dashboard</h1>", unsafe_allow_html=True)
    df = st.session_state["candados_df"]
    
    if not df.empty:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Total Locks", value=len(df))
        with col2:
            st.metric(label="Activos", value=(df["Estado"] == "Activo").sum())
        with col3:
            st.metric(label="Alertas", value=(df["Valor"] > 200).sum())
        
        st.plotly_chart(plot_active_locks(df), use_container_width=True)
        st.markdown("<h2 style='color:#4dd0e1;'>Actividad Reciente</h2>", unsafe_allow_html=True)
        df_sorted = df.sort_values("Fecha", ascending=False)
        for _, row in df_sorted.iterrows():
            st.markdown(f"""<div style='background:#1c2b3a; padding:10px; margin-bottom:10px;'>
                <span style='color:#ffffff;'>No. Candado: {row.get('NoCandado','')} | Área: {row.get('Area','')} | 
                Estado: {row.get('Estado','')} | Fecha: {row.get('Fecha','')}</span></div>""", 
                unsafe_allow_html=True)
    else:
        st.warning("No hay candados registrados.")

def plot_active_locks(df):
    """
    Genera un gráfico de línea con la cantidad de candados activos por fecha.
    """
    df_copy = df.copy()
    df_copy["Fecha"] = pd.to_datetime(df_copy["Fecha"], errors="coerce")
    df_activos = df_copy[df_copy["Estado"] == "Activo"]
    if not df_activos.empty:
        df_count = df_activos.groupby(df_activos["Fecha"].dt.date).size().reset_index(name="count")
    else:
        df_count = pd.DataFrame()

    fig = px.line(df_count, x="Fecha", y="count", markers=True, title="Tendencia de Candados Activos")
    fig.update_layout(plot_bgcolor="#1c2b3a", paper_bgcolor="#0e1a2b", font_color="#ffffff", title_font_color="#4dd0e1")
    fig.update_traces(line_color="#4dd0e1", marker_color="#4dd0e1")
    return fig

def input_data():
    """
    Formulario para el registro de nuevos candados LOTO.
    """
    st.markdown("<h1 style='text-align:center; color:#4dd0e1;'>Registrar Nuevo Candado</h1>", unsafe_allow_html=True)
    with st.form("register_lock"):
        no_candado = st.text_input("No. de Candado")
        area = st.text_input("Área")
        tablero_equipo = st.text_input("Tablero o Equipo")
        kks = st.text_input("KKS")
        tipo_bloqueo = st.text_input("Tipo de Bloqueo")
        lider_aut = st.text_input("Líder Autorizador")
        ejecutado_por_nombre = st.text_input("Bloqueo Ejecutado Por - Nombre")
        ejecutado_por_cargo = st.text_input("Bloqueo Ejecutado Por - Cargo")
        n_ptw = st.text_input("N° PTW")
        fecha_reg = st.date_input("Fecha de Bloqueo", value=date.today())
        descripcion = st.text_area("Descripción (opcional)", "")
        responsable = st.text_input("Responsable (opcional)")
        estado_check = st.checkbox("Activo", value=True)
        valor = st.number_input("Valor (opcional)", min_value=0, max_value=99999, value=0)
        uploaded_file = st.file_uploader("Adjuntar PDF (opcional)", type=["pdf"])
        submitted = st.form_submit_button("Guardar Registro")

        if submitted:
            pdf_data = bytes(uploaded_file.read()) if uploaded_file else None
            data_qr = f"NoCandado={no_candado}, Area={area}, Fecha={fecha_reg}"
            qr_bytes = generate_qr_code(data_qr)
            
            new_row = {
                "ID": no_candado,
                "NoCandado": no_candado,
                "Area": area,
                "TableroEquipo": tablero_equipo,
                "KKS": kks,
                "TipoBloqueo": tipo_bloqueo,
                "LiderAutorizador": lider_aut,
                "EjecPorNombre": ejecutado_por_nombre,
                "EjecPorCargo": ejecutado_por_cargo,
                "N_PTW": n_ptw,
                "Fecha": str(fecha_reg),
                "Descripción": descripcion,
                "Responsable": responsable,
                "Estado": "Activo" if estado_check else "Inactivo",
                "Valor": valor,
                "QR_Bytes": qr_bytes,
                "PDF_Adjunto": pdf_data
            }
            
            df = st.session_state["candados_df"]
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            st.session_state["candados_df"] = df
            save_loto_excel(df)
            st.success("Registro guardado exitosamente.")

def generate_qr_code(data: str) -> bytes:
    """
    Genera un código QR válido y retorna los datos como bytes.
    """
    qr = qrcode.QRCode(version=1, box_size=5, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")  # Asegúrate de guardarlo como PNG
    buf.seek(0)  # Asegúrate de que el puntero esté al inicio del buffer
    return buf.getvalue()

def edit_or_delete_candado():
    """
    Sección para editar o borrar candados existentes.
    """
    st.markdown("<h1 style='text-align:center; color:#4dd0e1;'>Editar o Borrar Candados</h1>", unsafe_allow_html=True)
    df = st.session_state["candados_df"]
    
    if df.empty:
        st.info("No hay candados para editar/borrar.")
        return

    df_display = df[["NoCandado", "Area", "Estado", "Fecha"]].reset_index(drop=True)
    if "edit_mode" not in st.session_state:
        st.session_state["edit_mode"] = None
    if "tarjeta_pdf" not in st.session_state:
        st.session_state["tarjeta_pdf"] = None
    if "tarjeta_idx" not in st.session_state:
        st.session_state["tarjeta_idx"] = None

    select_idx = st.selectbox(
        "Elige un candado:",
        df_display.index, 
        format_func=lambda i: f"No. {df_display.loc[i, 'NoCandado']} | Área: {df_display.loc[i, 'Area']}"
    )
    row_data = df.iloc[select_idx]

    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        if st.button("Editar", key=f"editar_btn_{select_idx}"):
            st.session_state["edit_mode"] = select_idx
    with col2:
        if st.button("Borrar", key=f"borrar_btn_{select_idx}"):
            df.drop(df.index[select_idx], inplace=True)
            st.session_state["candados_df"] = df
            save_loto_excel(df)
            st.success("Candado borrado.")
    with col3:
        if st.button("Generar Tarjeta", key=f"tarjeta_btn_{select_idx}"):
            pdf_card = generate_loto_card(row_data)
            st.session_state["tarjeta_pdf"] = pdf_card
            st.session_state["tarjeta_idx"] = select_idx
            st.success("Tarjeta generada.")

    if st.session_state["tarjeta_pdf"] and st.session_state["tarjeta_idx"] == select_idx:
        st.download_button(
            "Descargar Tarjeta PDF",
            st.session_state["tarjeta_pdf"], 
            file_name=f"tarjeta_{row_data.get('NoCandado','')}.pdf", 
            mime="application/pdf"
        )

    if st.session_state["edit_mode"] == select_idx:
        with st.expander(f"Editando No. Candado: {row_data.get('NoCandado','')}", expanded=True):
            edit_candado_form(select_idx)

def edit_candado_form(idx):
    """
    Formulario que se despliega al seleccionar un candado para edición.
    """
    df = st.session_state["candados_df"]
    candado = df.loc[idx]

    with st.form(f"edit_form_{idx}", clear_on_submit=True):
        no_candado = st.text_input("No. de Candado", value=candado.get("NoCandado", ""))
        area = st.text_input("Área", value=candado.get("Area",""))
        tablero_equipo = st.text_input("Tablero o Equipo", value=candado.get("TableroEquipo",""))
        kks = st.text_input("KKS", value=candado.get("KKS",""))
        tipo_bloqueo = st.text_input("Tipo de Bloqueo", value=candado.get("TipoBloqueo",""))
        lider_aut = st.text_input("Líder Autorizador", value=candado.get("LiderAutorizador",""))
        e_nom = st.text_input("Bloqueo Ejecutado Por - Nombre", value=candado.get("EjecPorNombre",""))
        e_cargo = st.text_input("Bloqueo Ejecutado Por - Cargo", value=candado.get("EjecPorCargo",""))
        n_ptw = st.text_input("N° PTW", value=candado.get("N_PTW",""))
        new_fecha = st.date_input("Fecha", value=pd.to_datetime(candado.get("Fecha", date.today())).date())
        new_desc = st.text_area("Descripción", value=candado.get("Descripción",""))
        new_resp = st.text_input("Responsable", value=candado.get("Responsable",""))
        new_estado = st.selectbox("Estado", ["Activo", "Inactivo"], 
                                  index=0 if candado.get("Estado", "Activo") == "Activo" else 1)
        new_valor = st.number_input("Valor", min_value=0, max_value=999999, value=int(candado.get("Valor", 0)))
        
        if st.form_submit_button("Guardar Cambios"):
            df.at[idx, "NoCandado"] = no_candado
            df.at[idx, "Area"] = area
            df.at[idx, "TableroEquipo"] = tablero_equipo
            df.at[idx, "KKS"] = kks
            df.at[idx, "TipoBloqueo"] = tipo_bloqueo
            df.at[idx, "LiderAutorizador"] = lider_aut
            df.at[idx, "EjecPorNombre"] = e_nom
            df.at[idx, "EjecPorCargo"] = e_cargo
            df.at[idx, "N_PTW"] = n_ptw
            df.at[idx, "Fecha"] = str(new_fecha)
            df.at[idx, "Descripción"] = new_desc
            df.at[idx, "Responsable"] = new_resp
            df.at[idx, "Estado"] = new_estado
            df.at[idx, "Valor"] = new_valor
            df.at[idx, "ID"] = no_candado
            df.at[idx, "QR_Bytes"] = generate_qr_code(
                f"NoCandado={no_candado}, Area={area}, Fecha={new_fecha}"
            )
            
            st.session_state["candados_df"] = df
            save_loto_excel(df)
            st.success("Cambios guardados.")
            st.session_state["edit_mode"] = None

def generate_reports():
    """
    Genera reportes en Excel o PDF a partir de los candados registrados.
    """
    st.markdown("<h1 style='text-align:center; color:#4dd0e1;'>Generar Reporte Excel / PDF</h1>", unsafe_allow_html=True)
    df = st.session_state["candados_df"]
    
    if df.empty:
        st.warning("No hay datos para exportar.")
        return

    formato = st.radio("Formato:", ["Excel", "PDF"], horizontal=True)
    if formato == "Excel":
        if st.button("Generar Excel"):
            excel_bytes = generate_excel_file(df)
            st.download_button(
                "Descargar Excel",
                excel_bytes,
                "reporte_candados.xlsx", 
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        selected = st.selectbox("Seleccionar:", ["Todos"] + df["NoCandado"].dropna().unique().tolist())
        if st.button("Generar PDF"):
            sub_df = df if selected == "Todos" else df[df["NoCandado"] == selected]
            pdf_bytes = generate_pdf_all(sub_df)
            st.download_button(
                "Descargar PDF",
                bytes(pdf_bytes),
                "candados.pdf",
                "application/pdf"
            )

def generate_excel_file(df: pd.DataFrame) -> bytes:
    """
    Genera un archivo Excel en memoria con la información de candados.
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        cols = [c for c in df.columns if c not in ["QR_Bytes", "PDF_Adjunto"]]
        df[cols].to_excel(writer, index=False, sheet_name="ReporteCandados")
    output.seek(0)
    return output.getvalue()

from fpdf import FPDF
from datetime import datetime
import tempfile

class LotoPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=10)
        self.set_fill_color(255, 255, 255)  # Fondo blanco para las celdas
        self.set_text_color(0, 0, 0)  # Texto en color negro

    def header(self):
        """Encabezado con el logo y el título centrado."""
        # Fondo azul claro para el encabezado
        self.set_fill_color(173, 216, 230)
        self.rect(0, 0, self.w, 20, 'F')
        self.image('logo1.png', x=(self.w - 30) / 2, y=5, w=30)
        self.set_y(15)
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'Reporte LOTO', align='C', ln=True)
        self.ln(10)

    def footer(self):
        """Pie de página con la fecha y hora de generación."""
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f"Generado por Sistema LOTO - {datetime.now().strftime('%d/%m/%Y %H:%M')}", align='C')

    def add_loto_info(self, data):
        """Agrega la información del candado al PDF en formato tabla."""
        self.set_font('Arial', '', 12)

        # Fondo de las celdas blanco
        self.set_fill_color(255, 255, 255)

        # Anchura y altura de las celdas
        col_width = 60
        row_height = 8

        # Generar tabla
        for key, value in data.items():
            self.cell(col_width, row_height, key, border=1, fill=True, align='L')
            self.cell(0, row_height, str(value), border=1, fill=True, align='L')
            self.ln(row_height)

        # Espacio para QR o mensaje alternativo
        qr_data = data.get('QR_Bytes', None)
        if isinstance(qr_data, (bytes, bytearray)):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                tmp.write(qr_data)
                self.image(tmp.name, x=(self.w - 40) / 2, y=self.get_y() + 10, w=40)
        else:
            self.ln(10)
            self.set_font('Arial', 'I', 10)
            self.cell(0, 10, 'QR no disponible', align='C')

# Función para generar el PDF

def generate_pdf_all(df: pd.DataFrame) -> bytes:
    """
    Genera un PDF con diseño profesional incluyendo un código QR.
    """
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=False, margin=0)

    for _, row in df.iterrows():
        pdf.add_page()

        # Encabezado con logo y título
        pdf.set_fill_color(44, 118, 137)  # Ajusta al color del fondo del logo
        pdf.rect(0, 0, 210, 50, 'F')  # Fondo ajustado al color del logo
        pdf.image(LOGO_PATH, x=55, y=10, w=100)  # Doble de tamaño centrado
        pdf.set_font("Helvetica", 'B', 18)
        pdf.set_text_color(255, 255, 255)  # Texto en blanco
        pdf.set_xy(0, 32)  # Ajuste de posición entre logo y tabla
        pdf.cell(0, 10, "Reporte LOTO", 0, 0, 'C')

        # Sección de contenido
        pdf.set_text_color(0, 0, 0)  # Volver al texto negro
        pdf.set_font("Helvetica", '', 12)
        pdf.set_y(60)  # Comienza la tabla después del encabezado
        
        # Datos principales en tabla
        pdf.set_fill_color(255, 255, 255)
        pdf.set_draw_color(0, 0, 0)
        col_width = 70
        line_height = 12  # Mayor separación entre celdas

        data = [
            ("No. Candado:", row.get('NoCandado', '')),
            ("Área:", row.get('Area', '')),
            ("Equipo:", row.get('TableroEquipo', '')),
            ("KKS:", row.get('KKS', '')),
            ("Tipo Bloqueo:", row.get('TipoBloqueo', '')),
            ("Líder Autorizador:", row.get('LiderAutorizador', '')),
            ("Ejecutado por:", f"{row.get('EjecPorNombre', '')} ({row.get('EjecPorCargo', '')})"),
            ("N° PTW:", row.get('N_PTW', '')),
            ("Fecha:", row.get('Fecha', '')),
            ("Estado:", row.get('Estado', '')),
            ("Valor:", str(row.get('Valor', 0))),
            ("Descripción:", row.get('Descripción', '')),
        ]

        for label, value in data:
            pdf.cell(col_width, line_height, label, 1, 0, 'L', 1)
            pdf.cell(0, line_height, str(value), 1, 1, 'L', 1)

        # QR Code debajo de las celdas
        pdf.ln(10)  # Espacio después de la tabla
        qr_data = row.get("QR_Bytes")
        if isinstance(qr_data, (bytes, bytearray)):  # Validación QR
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                tmp.write(qr_data)
                tmp.seek(0)  # Asegúrate de que el puntero esté al inicio
                qr_y = pdf.get_y()  # Obtener la posición actual en Y
                pdf.image(tmp.name, x=85, y=qr_y, w=40)  # Centrado en la página
        else:
            qr_y = pdf.get_y()
            pdf.set_xy(85, qr_y)
            pdf.set_font("Helvetica", 'I', 10)
            pdf.cell(40, 10, "QR no disponible", 0, 1, 'C')

        # Texto debajo del QR
        pdf.set_y(qr_y + 45)  # Ajustar posición después del QR
        pdf.set_font("Helvetica", 'I', 10)
        pdf.cell(0, 10, "QR listo para imprimir y pegar en candado", 0, 1, 'C')

        # Footer
        pdf.set_y(-20)
        pdf.set_font("Helvetica", 'I', 8)
        pdf.cell(0, 10, f"Generado por Sistema LOTO - {datetime.now().strftime('%d/%m/%Y %H:%M')}", 0, 0, 'C')

    return bytes(pdf.output(dest='S'))  # Devuelve directamente como bytes

def manage_users():
    """
    Sección para administrar usuarios (solo rol admin).
    """
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
        if st.form_submit_button("Crear Usuario"):
            if new_username in users_data:
                st.error("Ese usuario ya existe.")
            else:
                users_data[new_username] = {"password": new_password, "role": new_role}
                st.success(f"Usuario '{new_username}' creado con rol '{new_role}'.")

# =============================================================================
# SECCIÓN PRECOMISIONADO
# =============================================================================
def show_precomisionado_section():
    """
    Sección dedicada a Precomisionado.
    """
    st.markdown("<h2 style='text-align:center; color:#4dd0e1;'>Precomisionado - Dossier Digital</h2>", unsafe_allow_html=True)
    sub_tabs = st.tabs(["Items", "Generar ITR (PDF)", "Formulario Excel Dinámico"])
    
    with sub_tabs[0]:
        show_item_list()
    with sub_tabs[1]:
        generate_itr_pdf()
    with sub_tabs[2]:
        run_document_form()

def show_item_list():
    """
    Muestra la lista de items para precomisionado.
    """
    st.write("**Items** (ejemplo) para Precomisionado:")
    df_items = st.session_state["itembook_df"]
    st.dataframe(df_items)

def generate_itr_pdf():
    """
    Genera un PDF de ITR basado en un formulario sencillo.
    """
    st.write("Completa el formulario de ITR y genera un PDF similar al ejemplo.")
    df_items = st.session_state["itembook_df"]
    
    if df_items.empty:
        st.warning("No hay items en la base de datos.")
        return

    item_id = st.selectbox("Seleccionar ItemID", df_items["ItemID"].unique())
    row_item = df_items[df_items["ItemID"] == item_id].iloc[0]

    with st.form("itr_form"):
        equipo = st.text_input("Descripción del Equipo", value=row_item["Descripcion"])
        subsistema = st.text_input("Sub-sistema", "Tensión segura (ejemplo)")
        responsable = st.text_input("Responsable", "Ing. Precomisionado")
        comentarios = st.text_area("Comentarios", "Observaciones...")
        submitted = st.form_submit_button("Generar PDF")

    if submitted:
        pdf_bytes = generar_pdf_precom(row_item, equipo, subsistema, responsable, comentarios)
        st.session_state["pdf_bytes"] = pdf_bytes
        st.success("PDF generado con éxito. Descarga a continuación:")

    if "pdf_bytes" in st.session_state and st.session_state["pdf_bytes"] is not None:
        st.download_button(
            "Descargar ITR PDF",
            st.session_state["pdf_bytes"], 
            f"ITR_{item_id}.pdf", 
            "application/pdf"
        )

def generar_pdf_precom(item_row, equipo, subsistema, responsable, comentarios):
    """
    Genera un PDF simulando el ITR de precomisionado.
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "", 12)

    pdf.cell(0, 10, txt="E11A - Centro de Control de Motores (BT/AT) (MCC)", ln=1, align="C")
    pdf.cell(0, 10, txt="Completamiento de la Construcción", ln=1, align="C")
    pdf.ln(5)
    
    pdf.cell(0, 8, txt=f"N° de Tag: {item_row['ItemID']}", ln=1)
    pdf.cell(0, 8, txt=f"Descripción del Equipo: {equipo}", ln=1)
    pdf.cell(0, 8, txt=f"N° de Subsistema: {subsistema}", ln=1)
    pdf.cell(0, 8, txt=f"Proyecto: {item_row['Proyecto']}", ln=1)
    pdf.cell(0, 8, txt=f"Responsable: {responsable}", ln=1)
    
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, txt="Items para verificar:", ln=1)
    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 8, "- Placa de identificación\n- Dispositivo de fijación\n- MCCB, contactores...")
    
    pdf.ln(5)
    pdf.cell(0, 8, txt="Comentarios / Observaciones:", ln=1)
    pdf.multi_cell(0, 8, comentarios)
    pdf.ln(10)
    pdf.cell(0, 8, txt="Firmado por: _______________________", ln=1)
    pdf.cell(0, 8, txt="Fecha: _____________________________", ln=1)

    return pdf.output(dest="S")

def run_document_form():
    """
    Generación de un formulario dinámico a partir de un Excel.
    """
    st.write("### Crear formulario a partir de un archivo Excel")
    uploaded_file = st.file_uploader("Subir archivo Excel", type=["xlsx", "xls"])
    
    if uploaded_file is None:
        st.info("Por favor, sube un archivo para continuar.")
        return

    try:
        df_def = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Error al leer el Excel: {e}")
        return

    form_values = {}
    with st.form("dynamic_form"):
        for i, row in df_def.iterrows():
            field_type = str(row.get("field_type", "")).lower()
            label = row.get("label", f"Campo {i}")
            options = row.get("options", "")
            default = row.get("default", "")
            
            if field_type == "text":
                form_values[label] = st.text_input(label, value=str(default))
            elif field_type == "checkbox":
                form_values[label] = st.checkbox(label, value=(str(default).lower() == "true"))
            elif field_type == "select":
                opt_list = [o.strip() for o in str(options).split(",")]
                default_index = opt_list.index(default) if default in opt_list else 0
                form_values[label] = st.selectbox(label, opt_list, index=default_index)
            else:
                form_values[label] = st.text_input(label, value=str(default))
        
        if st.form_submit_button("Generar PDF"):
            pdf_bytes = generar_pdf_dinamico(form_values)
            st.success("Se generó el PDF con la información. Descarga abajo:")
            st.download_button(
                "Descargar PDF",
                pdf_bytes,
                "formulario_generado.pdf",
                "application/pdf"
            )

def generar_pdf_dinamico(form_data: dict) -> bytes:
    """
    Genera un PDF con la información de un formulario dinámico.
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "", 12)
    
    pdf.cell(0, 10, txt="Formulario Dinámico - Resultado", ln=True, align="C")
    pdf.ln(5)
    
    for label, value in form_data.items():
        pdf.multi_cell(0, 8, f"{label}: {value}")
        pdf.ln(2)
    
    return pdf.output(dest="S").encode('latin1')

# =============================================================================
# SECCIÓN SIMOPS (ACTUALIZADA CON PDF FIX Y MEJORAS)
# =============================================================================
from io import BytesIO
from fpdf import FPDF
import pandas as pd
import streamlit as st
from datetime import date, timedelta
import plotly.express as px

# Configuración de constantes (ajusta según tu necesidad)
LOGO_PATH = "logo.png"  # Asegúrate de tener el archivo en tu proyecto

def show_simops_section():
    """
    Sección dedicada a SIMOPS (Simultaneous Operations).
    Aquí se gestionan las operaciones simultáneas para la coordinación de permisos de trabajo.
    """
    st.markdown("<h2 style='text-align:center; color:#4dd0e1;'>SIMOPS - Operaciones Simultáneas</h2>", unsafe_allow_html=True)
    
    simops_tabs = st.tabs(["Visión General", "Registrar SIMOPS", "Editar/Borrar", "Reporte PDF"])
    
    with simops_tabs[0]:
        show_simops_overview()
    with simops_tabs[1]:
        if st.session_state.role in ["admin", "operador"]:
            register_simops()
        else:
            st.error("No tienes permiso para registrar SIMOPS.")
    with simops_tabs[2]:
        if st.session_state.role == "admin":
            edit_delete_simops()
        else:
            st.error("Solo un admin puede editar/borrar SIMOPS.")
    with simops_tabs[3]:
        generate_simops_report_pdf()

def show_simops_overview():
    """
    Muestra un resumen o dashboard para SIMOPS.
    """
    df = st.session_state["simops_df"]
    if df.empty:
        st.warning("No hay operaciones SIMOPS registradas.")
        return
    
    st.markdown("#### Tabla de Operaciones SIMOPS")
    st.dataframe(df)
    
    if "Estado" in df.columns:
        estado_count = df["Estado"].value_counts().reset_index()
        estado_count.columns = ["Estado", "Cantidad"]
        fig = px.bar(estado_count, x="Estado", y="Cantidad", title="SIMOPS por Estado")
        fig.update_layout(plot_bgcolor="#1c2b3a", paper_bgcolor="#0e1a2b", font_color="#ffffff")
        fig.update_traces(marker_color="#4dd0e1")
        st.plotly_chart(fig, use_container_width=True)

def register_simops():
    """
    Formulario para registrar nuevas operaciones simultáneas.
    """
    st.markdown("### Registrar Nueva Operación SIMOPS")
    with st.form("register_simops"):
        simops_id = st.text_input("ID SIMOPS")
        descripcion = st.text_area("Descripción de la Operación")
        area = st.text_input("Área")
        ptw_involucrados = st.text_input("Permisos de Trabajo (PTW) involucrados")
        fecha_inicio = st.date_input("Fecha de Inicio", value=date.today())
        fecha_fin = st.date_input("Fecha de Fin", value=date.today() + timedelta(days=1))
        encargado = st.text_input("Encargado/Responsable")
        estado = st.selectbox("Estado", ["Planificado", "En Ejecución", "Finalizado", "Suspendido"])
        riesgos = st.text_area("Riesgos / Observaciones")
        acciones = st.text_area("Acciones / Mitigaciones")
        submit_simops = st.form_submit_button("Guardar SIMOPS")

    if submit_simops:
        df = st.session_state["simops_df"]
        new_row = {
            "SIMOPS_ID": simops_id,
            "Descripción": descripcion,
            "Área": area,
            "PTWs_Involucrados": ptw_involucrados,
            "Fecha_Inicio": str(fecha_inicio),
            "Fecha_Fin": str(fecha_fin),
            "Encargado": encargado,
            "Estado": estado,
            "Riesgos": riesgos,
            "Acciones_Mitigación": acciones
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        st.session_state["simops_df"] = df
        save_simops_data(df)
        st.success("Operación SIMOPS registrada con éxito.")

def edit_delete_simops():
    """
    Permite editar o eliminar operaciones SIMOPS existentes.
    """
    st.markdown("### Editar / Borrar SIMOPS")
    df = st.session_state["simops_df"]
    if df.empty:
        st.info("No hay operaciones SIMOPS para editar/borrar.")
        return
    
    df_display = df[["SIMOPS_ID", "Descripción", "Estado", "Fecha_Inicio", "Fecha_Fin"]].reset_index(drop=True)
    if "edit_simops_mode" not in st.session_state:
        st.session_state["edit_simops_mode"] = None

    select_idx = st.selectbox(
        "Elige una operación SIMOPS:",
        df_display.index,
        format_func=lambda i: f"ID: {df_display.loc[i, 'SIMOPS_ID']} | {df_display.loc[i, 'Descripción']}"
    )
    row_data = df.iloc[select_idx]

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Editar"):
            st.session_state["edit_simops_mode"] = select_idx
    with col2:
        if st.button("Borrar"):
            df.drop(df.index[select_idx], inplace=True)
            st.session_state["simops_df"] = df
            save_simops_data(df)
            st.success("Operación SIMOPS eliminada.")

    if st.session_state["edit_simops_mode"] == select_idx:
        with st.expander(f"Editando SIMOPS ID: {row_data.get('SIMOPS_ID','')}", expanded=True):
            edit_simops_form(select_idx)

def edit_simops_form(idx):
    """
    Formulario para editar SIMOPS seleccionada.
    """
    df = st.session_state["simops_df"]
    simops = df.loc[idx]

    with st.form(f"edit_simops_form_{idx}", clear_on_submit=True):
        simops_id = st.text_input("ID SIMOPS", value=simops.get("SIMOPS_ID", ""))
        descripcion = st.text_area("Descripción de la Operación", value=simops.get("Descripción",""))
        area = st.text_input("Área", value=simops.get("Área",""))
        ptw_involucrados = st.text_input("Permisos de Trabajo (PTW) involucrados",
                                         value=simops.get("PTWs_Involucrados",""))
        f_inicio = pd.to_datetime(simops.get("Fecha_Inicio", date.today())).date()
        fecha_inicio = st.date_input("Fecha de Inicio", value=f_inicio)
        f_fin = pd.to_datetime(simops.get("Fecha_Fin", date.today())).date()
        fecha_fin = st.date_input("Fecha de Fin", value=f_fin)
        encargado = st.text_input("Encargado/Responsable", value=simops.get("Encargado",""))
        estado = st.selectbox("Estado", ["Planificado", "En Ejecución", "Finalizado", "Suspendido"],
                              index=["Planificado", "En Ejecución", "Finalizado", "Suspendido"].index(
                                  simops.get("Estado","Planificado")
                              ))
        riesgos = st.text_area("Riesgos / Observaciones", value=simops.get("Riesgos",""))
        acciones = st.text_area("Acciones / Mitigaciones", value=simops.get("Acciones_Mitigación",""))

        if st.form_submit_button("Guardar Cambios"):
            df.at[idx, "SIMOPS_ID"] = simops_id
            df.at[idx, "Descripción"] = descripcion
            df.at[idx, "Área"] = area
            df.at[idx, "PTWs_Involucrados"] = ptw_involucrados
            df.at[idx, "Fecha_Inicio"] = str(fecha_inicio)
            df.at[idx, "Fecha_Fin"] = str(fecha_fin)
            df.at[idx, "Encargado"] = encargado
            df.at[idx, "Estado"] = estado
            df.at[idx, "Riesgos"] = riesgos
            df.at[idx, "Acciones_Mitigación"] = acciones

            st.session_state["simops_df"] = df
            save_simops_data(df)
            st.success("Cambios guardados.")
            st.session_state["edit_simops_mode"] = None

def generate_simops_report_pdf():
    """
    Permite generar un reporte PDF de las operaciones SIMOPS.
    """
    st.markdown("### Generar Reporte PDF de SIMOPS")
    df = st.session_state["simops_df"]
    if df.empty:
        st.warning("No hay datos de SIMOPS para exportar.")
        return

    selected = st.selectbox("Seleccionar SIMOPS:", ["Todos"] + df["SIMOPS_ID"].dropna().unique().tolist())
    if st.button("Generar PDF SIMOPS"):
        sub_df = df if selected == "Todos" else df[df["SIMOPS_ID"] == selected]
        try:
            pdf_bytes = generate_pdf_simops(sub_df)
            if pdf_bytes:
                st.download_button("Descargar Reporte PDF", pdf_bytes, "SIMOPS.pdf", "application/pdf")
        except Exception as e:
            st.error(f"Error generando PDF: {str(e)}")

def generate_pdf_simops(df_simops: pd.DataFrame) -> bytes:
    """
    Genera un PDF con la información de SIMOPS (versión mejorada)
    """
    buffer = BytesIO()
    
    try:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        # Configurar fuentes
        pdf.add_font("Arial", style="", fname="arial.ttf", uni=True)
        pdf.set_font("Arial", size=12)
        
        # Logo profesional
        add_image_safe(pdf, LOGO_PATH, x=(pdf.w - 50)/2, y=10, w=50)
        pdf.ln(40)
        
        # Título principal
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Reporte SIMOPS", 0, 1, "C")
        pdf.ln(10)
        
        # Contenido profesional
        for _, row in df_simops.iterrows():
            data = {
                "SIMOPS ID": row.get('SIMOPS_ID', 'N/A'),
                "Descripción": row.get('Descripción', ''),
                "Área": row.get('Área', ''),
                "PTWs Involucrados": row.get('PTWs_Involucrados', ''),
                "Fecha Inicio": row.get('Fecha_Inicio', ''),
                "Fecha Fin": row.get('Fecha_Fin', ''),
                "Encargado": row.get('Encargado', ''),
                "Estado": row.get('Estado', ''),
                "Riesgos": row.get('Riesgos', ''),
                "Acciones/Mitigación": row.get('Acciones_Mitigación', '')
            }
            
            add_professional_table(pdf, data)
            pdf.ln(15)
        
        pdf.output(buffer)
        return buffer.getvalue()
    
    except Exception as e:
        st.error(f"Error crítico al generar PDF: {str(e)}")
        return b''
    finally:
        buffer.close()

def add_image_safe(pdf, image_path, x, y, w):
    """Manejo seguro de imágenes con fallback"""
    try:
        pdf.image(image_path, x=x, y=y, w=w)
    except RuntimeError:
        pdf.set_xy(x, y)
        pdf.set_font("Arial", "I", 8)
        pdf.cell(0, 10, txt=f"[Logo no disponible: {image_path}]")

def add_professional_table(pdf, data):
    """Crea tablas con estilo profesional"""
    pdf.set_fill_color(240, 240, 240)
    pdf.set_text_color(0, 0, 0)
    
    for key, value in data.items():
        pdf.set_font("Arial", "B", 10)
        pdf.cell(40, 8, txt=f"{key}:", border=0, fill=True)
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, 8, txt=str(value), border=0)
        pdf.ln(3)
    
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), pdf.w - 10, pdf.get_y())

def save_simops_data(df):
    """Función dummy para guardar datos - implementa según tu necesidad"""
    # Ejemplo: df.to_excel("simops_data.xlsx", index=False)
    pass
# =============================================================================
# UTILIDADES DE DATOS
# =============================================================================
def load_loto_excel():
    """
    Carga el archivo Excel de candados LOTO, o lo crea con datos de ejemplo si no existe.
    """
    if not os.path.exists(EXCEL_FILE_LOTO):
        df = prepopulate_loto(n=30)
        df.to_excel(EXCEL_FILE_LOTO, index=False)
    else:
        df = pd.read_excel(EXCEL_FILE_LOTO)
        needed_cols = [
            "NoCandado","Area","TableroEquipo","KKS","TipoBloqueo","LiderAutorizador",
            "EjecPorNombre","EjecPorCargo","N_PTW","QR_Bytes","PDF_Adjunto","Valor",
            "Estado","Descripción","Responsable","Fecha","ID"
        ]
        for col in needed_cols:
            if col not in df.columns:
                df[col] = ""
    return df

def save_loto_excel(df):
    """
    Guarda los datos de LOTO en un archivo Excel.
    """
    df.to_excel(EXCEL_FILE_LOTO, index=False)

def prepopulate_loto(n=30):
    """
    Genera datos de ejemplo para candados LOTO.
    """
    rows = []
    today = date.today()
    for i in range(n):
        candado_id = f"Rojo{i+1}"
        area = random.choice(["SHELTER LV", "Sala Compresores", "Tanques", "Area Baterías"])
        tablero = random.choice(["UPS", "UPS DISTRIBUTION BOARD", "Q74", "Q43"])
        kks_val = random.choice(["Q73", "Q74", "Q43", "Q99"])
        tipo = f"CANDADO {i+1}"
        lider = random.choice(["Monsu Ariel", "Avecilla Miguel", "Scimeca Gabriel"])
        ejecutor = random.choice(["Perez Martin", "Sanchez Pedro", "Lopez Carlos"])
        cargo = random.choice(["Supervisor", "Operador", "Técnico"])
        ptw_number = str(random.randint(1, 10))
        days_back = random.randint(0, 60)
        fecha_rand = today - timedelta(days=days_back)
        estado = random.choice(["Activo", "Inactivo"])
        qr_str = f"NoCandado={candado_id}, Area={area}, Fecha={fecha_rand}"
        qr_bytes = generate_qr_code(qr_str) if qr_str else None

        rows.append({
            "ID": candado_id,
            "NoCandado": candado_id,
            "Area": area,
            "TableroEquipo": tablero,
            "KKS": kks_val,
            "TipoBloqueo": tipo,
            "LiderAutorizador": lider,
            "EjecPorNombre": ejecutor,
            "EjecPorCargo": cargo,
            "N_PTW": ptw_number,
            "Fecha": str(fecha_rand),
            "Descripción": f"Descripción {i+1}",
            "Responsable": lider,
            "Estado": estado,
            "Valor": random.randint(0, 300),
            "QR_Bytes": qr_bytes if isinstance(qr_bytes, bytes) else b"",  # Validación QR
            "PDF_Adjunto": None
        })
    return pd.DataFrame(rows)

def generate_itembook():
    """
    Genera datos de ejemplo para la sección de Precomisionado.
    """
    proyectos = ["Proyecto A"] * 20 + ["Proyecto B"] * 20
    rows = []
    for i in range(40):
        item_id = f"ITM-{i+1:03d}"
        desc = "Item Ejemplo " + "".join(random.choices(string.ascii_uppercase, k=2))
        rows.append({"Proyecto": proyectos[i], "ItemID": item_id, "Descripcion": desc})
    return pd.DataFrame(rows)

# =============================================================================
# NUEVAS UTILIDADES PARA SIMOPS
# =============================================================================
def load_simops_data():
    """
    Carga los datos de SIMOPS desde un archivo Excel, o genera datos de ejemplo si no existe.
    """
    if not os.path.exists(EXCEL_FILE_SIMOPS):
        df = prepopulate_simops(n=5)
        df.to_excel(EXCEL_FILE_SIMOPS, index=False)
    else:
        df = pd.read_excel(EXCEL_FILE_SIMOPS)
        needed_cols = [
            "SIMOPS_ID","Descripción","Área","PTWs_Involucrados","Fecha_Inicio",
            "Fecha_Fin","Encargado","Estado","Riesgos","Acciones_Mitigación"
        ]
        for col in needed_cols:
            if col not in df.columns:
                df[col] = ""
    return df

def save_simops_data(df):
    """
    Guarda los datos de SIMOPS en un archivo Excel.
    """
    df.to_excel(EXCEL_FILE_SIMOPS, index=False)

def prepopulate_simops(n=5):
    """
    Genera datos de ejemplo para SIMOPS.
    """
    rows = []
    today = date.today()
    for i in range(n):
        simops_id = f"SIMOPS-{i+1:03d}"
        desc = f"Operación Simultánea Ejemplo {i+1}"
        area = random.choice(["Planta Compresión", "Tanques de Almacenamiento", "Sala de Control"])
        ptws = f"PTW-{random.randint(10,99)}, PTW-{random.randint(100,999)}"
        f_inicio = today + timedelta(days=random.randint(-10,10))
        f_fin = f_inicio + timedelta(days=random.randint(1,5))
        encargado = random.choice(["Juan Pérez", "María García", "Pedro Rodríguez"])
        estado = random.choice(["Planificado", "En Ejecución", "Finalizado", "Suspendido"])
        riesgos = "Riesgo de incendio, Exposición a químicos."
        acciones = "Uso de EPP, Aislamiento de energía, Vigilancia"
        rows.append({
            "SIMOPS_ID": simops_id,
            "Descripción": desc,
            "Área": area,
            "PTWs_Involucrados": ptws,
            "Fecha_Inicio": str(f_inicio),
            "Fecha_Fin": str(f_fin),
            "Encargado": encargado,
            "Estado": estado,
            "Riesgos": riesgos,
            "Acciones_Mitigación": acciones
        })
    return pd.DataFrame(rows)

# =============================================================================
# ESTILOS Y FUNCIONES VARIAS
# =============================================================================
def apply_custom_styles():
    """
    Aplica estilos CSS personalizados a la aplicación.
    """
    st.markdown("""
    <style>
        [data-testid="stAppViewContainer"] { background-color: #0e1a2b !important; }
        [data-testid="stHeader"] { background-color: #0e1a2b !important; }
        html, body, [class*="css"]  { color: #ffffff !important; }
        .stTabs [role="tablist"] button [data-baseweb="tab"] { 
            color: #ffffff !important; 
            border: 1px solid #4dd0e1 !important; 
        }
        .stTabs [role="tablist"] button[aria-selected="true"] { 
            background-color: #1c2b3a !important;
            color: #4dd0e1 !important;
        }
        .stMetric { background: #1a2b3c; border-radius: 10px; padding: 15px; }
    </style>
    """, unsafe_allow_html=True)

# =============================================================================
# EJECUCIÓN
# =============================================================================
if __name__ == "__main__":
    main()