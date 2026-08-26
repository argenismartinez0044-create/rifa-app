import datetime
import os
import random
import sqlite3
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image

DB_FILE = "rifas_v4.db"
WHATSAPP_NUMERO = "8294835217"

st.set_page_config(
    page_title="Rifas Sirio RD",
    page_icon="🎲",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------
# ESTADO DE TEMA (MODO CLARO / MODO OSCURO)
# ---------------------------------------------------------
if "modo_tema" not in st.session_state:
    st.session_state["modo_tema"] = "oscuro"

def cambiar_tema():
    if st.session_state["modo_tema"] == "oscuro":
        st.session_state["modo_tema"] = "claro"
    else:
        st.session_state["modo_tema"] = "oscuro"

es_oscuro = st.session_state["modo_tema"] == "oscuro"

# Definición de colores
bg_app = "linear-gradient(180deg, #090b14 0%, #05060a 100%)" if es_oscuro else "#F8FAFC"
txt_color = "#FFFFFF" if es_oscuro else "#0F172A"
card_bg = "#0e1222" if es_oscuro else "#FFFFFF"
card_border = "#1e293b" if es_oscuro else "#E2E8F0"
subtxt_color = "#a0aabf" if es_oscuro else "#475569"

st.markdown(
    f"""
    <style>
    /* Fondo principal cibernético */
    .stApp {{
        background: {bg_app} !important;
        color: {txt_color};
        font-family: 'Segoe UI', Roboto, sans-serif;
    }}

    header {{visibility: hidden;}}
    .block-container {{ padding-top: 1rem; padding-bottom: 2rem; }}

    /* Botones generales */
    div.stButton > button {{
        background: linear-gradient(90deg, #1b2238 0%, #111525 100%);
        color: #FFFFFF;
        border: 1px solid #00f0ff;
        border-radius: 8px;
        font-weight: bold;
        transition: all 0.3s ease;
    }}
    div.stButton > button:hover {{
        border-color: #00f0ff;
        box-shadow: 0 0 12px #00f0ff;
        color: #ffffff;
    }}

    /* Botones de Acción / Jugar */
    .btn-buy-container div.stButton > button {{
        background: linear-gradient(90deg, #f59e0b 0%, #d97706 100%) !important;
        border: 1px solid #f59e0b !important;
        color: #ffffff !important;
        font-size: 1.1rem !important;
        font-weight: 800 !important;
        border-radius: 10px !important;
        height: 48px !important;
    }}
    .btn-buy-container div.stButton > button:hover {{
        box-shadow: 0 0 15px #f59e0b !important;
    }}

    /* --- TARJETA DE LA DINÁMICA DE JUEGO --- */
    .raffle-card-wrapper {{
        position: relative;
        background: {card_bg};
        border: 1.5px solid {card_border};
        border-radius: 16px;
        padding: 16px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4);
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        overflow: hidden;
    }}

    .raffle-card-wrapper:hover {{
        transform: translateY(-6px);
        border-color: #00f0ff !important;
        box-shadow: 0 0 20px rgba(0, 240, 255, 0.6), inset 0 0 10px rgba(0, 240, 255, 0.2) !important;
    }}

    .image-container-relative {{
        position: relative;
        width: 100%;
        border-radius: 12px;
        overflow: hidden;
        margin-bottom: 12px;
    }}

    /* Badge de Categoría dentro de la Imagen */
    .category-badge-overlay {{
        position: absolute;
        top: 12px;
        right: 12px;
        background: rgba(30, 41, 59, 0.85);
        backdrop-filter: blur(4px);
        color: #00f0ff;
        border: 1px solid #00f0ff;
        padding: 6px 16px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 800;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        z-index: 10;
        pointer-events: none;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
    }}

    /* ESTILOS DE LA VENTANA DE COMPRA ESTILO FUTURISTA */
    .counter-box {{
        background: #020617;
        border: 2px solid #1e293b;
        border-radius: 12px;
        padding: 15px;
        text-align: center;
    }}

    .counter-display {{
        font-size: 2.5rem;
        font-weight: 900;
        color: #00f0ff;
        letter-spacing: 2px;
    }}

    .info-callout-box {{
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid #1d4ed8;
        border-radius: 10px;
        padding: 12px;
        margin-top: 12px;
        color: #93c5fd;
        font-size: 0.85rem;
    }}

    /* BANCOS ESTILO RETRO / FUTURISTA */
    .bank-card-selectable {{
        background: #0e1222;
        border: 1.5px solid #1e293b;
        border-radius: 12px;
        padding: 10px;
        text-align: center;
        cursor: pointer;
        transition: all 0.2s ease;
    }}

    .bank-card-selected {{
        background: #111827 !important;
        border: 2px solid #00f0ff !important;
        box-shadow: 0 0 15px rgba(0, 240, 255, 0.4) !important;
    }}

    .bank-info-panel {{
        background: #090d16;
        border: 1.5px solid #00f0ff;
        border-radius: 12px;
        padding: 16px;
        margin-top: 15px;
        margin-bottom: 15px;
    }}

    /* Verificador Ticket */
    .ticket-card {{
        background: {card_bg};
        border: 1px solid {card_border};
        border-radius: 12px;
        padding: 15px;
        text-align: center;
        margin-bottom: 15px;
    }}
    .ticket-number {{
        font-size: 1.8rem;
        font-weight: 900;
        color: #fce205;
    }}
    </style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# DIÁLOGO DE SOPORTE IA
# ---------------------------------------------------------
@st.dialog("🤖 Asistente Virtual - Rifas Sirio RD")
def abrir_soporte_ia():
    st.caption("Respuestas instantáneas las 24 horas.")

    if "mensajes_chat" not in st.session_state:
        st.session_state["mensajes_chat"] = [
            {
                "role": "assistant",
                "content": "¡Hola! Soy tu asistente de **Rifas Sirio RD** 🎲.\n\n¿En qué te puedo ayudar hoy?",
            }
        ]

    c1, c2, c3, c4 = st.columns(4)
    opcion_rapida = None
    if c1.button("🎲 ¿Cómo jugar?", key="dlg_c1"):
        opcion_rapida = "¿Cómo participar?"
    if c2.button("💳 Bancos", key="dlg_c2"):
        opcion_rapida = "cuentas de banco"
    if c3.button("🔎 Mis boletos", key="dlg_c3"):
        opcion_rapida = "verificar mis boletos"
    if c4.button("📅 Sorteos", key="dlg_c4"):
        opcion_rapida = "fecha del sorteo"

    for msg in st.session_state["mensajes_chat"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Escribe tu duda...")
    prompt = user_input or opcion_rapida

    if prompt:
        if user_input:
            st.session_state["mensajes_chat"].append(
                {"role": "user", "content": prompt}
            )

        txt = prompt.lower()
        mostrar_wa = False

        if any(w in txt for w in ["jugar", "participar", "funciona", "pasos"]):
            resp = "1. Selecciona tu juego.\n2. Selecciona la cantidad de boletos.\n3. Selecciona tu banco e ingresa el comprobante."
        elif any(w in txt for w in ["pago", "banco", "transferencia"]):
            resp = "Aceptamos Banreservas, Banco Popular, BHD y Banco Santa Cruz."
        elif any(w in txt for w in ["verificar", "consultar", "mi boleto"]):
            resp = "Ingresa a **🔎 Verificador de boletos** e introduce tu teléfono."
        else:
            resp = "¿Deseas asistencia por WhatsApp?"
            mostrar_wa = True

        st.session_state["mensajes_chat"].append(
            {"role": "assistant", "content": resp}
        )
        if mostrar_wa:
            st.markdown(
                f"[💬 Hablar con soporte](https://wa.me/{WHATSAPP_NUMERO})"
            )
        st.rerun()


# ---------------------------------------------------------
# DIÁLOGO DE PROCESO DE COMPRA (INTERFAZ DE 2DA Y 3RA FOTO)
# ---------------------------------------------------------
@st.dialog("🛒 COMPLETAR COMPRA DE NÚMEROS", width="large")
def ventana_compra_dialogo():
    rifa_id = st.session_state["rifa_seleccionada"]
    r_nom = st.session_state["nombre_rifa"]
    r_precio = st.session_state["precio_rifa"]
    r_min = st.session_state["min_rifa"]

    st.markdown(
        f"""
        <div style="border-bottom: 1px solid #1e293b; padding-bottom: 10px; margin-bottom: 15px;">
            <h2 style="color: #00f0ff; margin: 0; font-size: 1.5rem;">{r_nom.upper()}</h2>
            <small style="color: #a0aabf;">Completa tu compra de números</small>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "cant_boletos_dialog" not in st.session_state:
        st.session_state["cant_boletos_dialog"] = int(r_min)

    # 1. CONTADOR DE CANTIDAD DE NÚMEROS (+ / -)
    st.markdown("### 🎫 CANTIDAD DE NÚMEROS")

    col_dec, col_dis, col_inc = st.columns([1, 2, 1], vertical_alignment="center")

    with col_dec:
        if st.button("➖", key="btn_dec_num", use_container_width=True):
            if st.session_state["cant_boletos_dialog"] > r_min:
                st.session_state["cant_boletos_dialog"] -= 1
                st.rerun()

    with col_dis:
        st.markdown(
            f"""
            <div class="counter-box">
                <div class="counter-display">{st.session_state['cant_boletos_dialog']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_inc:
        if st.button("➕", key="btn_inc_num", use_container_width=True):
            st.session_state["cant_boletos_dialog"] += 1
            st.rerun()

    st.markdown(
        f"<p style='text-align:center; color:#f59e0b; font-weight:bold; margin-top:5px;'>Compra mínima: {r_min} números</p>",
        unsafe_allow_html=True,
    )

    # Mensaje Informativo exacto
    st.markdown(
        """
        <div class="info-callout-box">
            ℹ️ Los números se <strong>asignarán automáticamente al azar</strong> tras validar tu pago. ¡Mayor cantidad = más oportunidades de ganar!
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # DATOS DEL CLIENTE
    st.markdown("### 👤 TUS DATOS DE CONTACTO")
    c_nom, c_tel = st.columns(2)
    with c_nom:
        nombre_u = st.text_input("Nombre Completo *", placeholder="Ej: Juan Pérez", key="input_dialog_nom")
    with c_tel:
        telefono_u = st.text_input("Teléfono (WhatsApp) *", placeholder="+1 809-555-5555", key="input_dialog_tel")

    st.markdown("---")

    # 2. SELECCIÓN DE MÉTODO DE PAGO / BANCO (CON IMÁGENES/BOTONES)
    st.markdown("### 💳 MÉTODO DE PAGO *")

    bancos_info = {
        "Banreservas": {
            "titular": "ARGENIS MARTINEZ C.",
            "cuenta": "9606561652",
            "tipo": "Ahorros",
            "img": "banreservas.png",
        },
        "Banco Popular": {
            "titular": "ARGENIS MARTINEZ",
            "cuenta": "821794971",
            "tipo": "Ahorros",
            "img": "popular.png",
        },
        "BHD": {
            "titular": "ARGENIS MARTINEZ",
            "cuenta": "1098273645",
            "tipo": "Ahorros",
            "img": "bhd.png",
        },
        "Banco Santa Cruz": {
            "titular": "ARGENIS MARTINEZ",
            "cuenta": "4029182736",
            "tipo": "Ahorros",
            "img": "santacruz.png",
        },
    }

    if "banco_seleccionado_dialog" not in st.session_state:
        st.session_state["banco_seleccionado_dialog"] = None

    cols_bancos = st.columns(4)
    for i, (b_name, b_data) in enumerate(bancos_info.items()):
        es_sel = st.session_state["banco_seleccionado_dialog"] == b_name
        
        with cols_bancos[i]:
            # Botón estilizado para seleccionar el banco
            lbl = f"✅ {b_name}" if es_sel else f"🏦 {b_name}"
            if st.button(lbl, key=f"btn_sel_banco_{i}", use_container_width=True, type="primary" if es_sel else "secondary"):
                st.session_state["banco_seleccionado_dialog"] = b_name
                st.rerun()

    # Si NO ha seleccionado ningún banco, NO se muestra la información
    banco_activo = st.session_state["banco_seleccionado_dialog"]

    if banco_activo:
        info_b = bancos_info[banco_activo]

        st.markdown(
            f"""
            <div class="bank-info-panel">
                <h4 style="color:#00f0ff; margin-top:0;">🏦 {banco_activo.upper()} ({info_b['tipo'].upper()})</h4>
                <p style="margin-bottom: 4px;">Tipo: <strong>{info_b['tipo']}</strong></p>
                <p style="margin-bottom: 4px;">Titular: <strong>{info_b['titular']}</strong></p>
                <p style="margin-bottom: 4px;">Número de cuenta:</p>
                <h2 style="color:#ffffff; margin:5px 0; letter-spacing:2px;">{info_b['cuenta']}</h2>
            </div>
            """,
            unsafe_allow_html=True,
        )

        html_copiar = f"""
        <button onclick="navigator.clipboard.writeText('{info_b['cuenta']}').then(() => {{
            this.innerText='✅ ¡CUENTA COPIADA!';
            this.style.background='#28a745';
            this.style.color='#fff';
        }})" 
        style="width:100%; padding:14px; border:0; border-radius:8px; 
               background:#FFD700; color:#000; font-weight:900; cursor:pointer; font-size: 1rem; margin-bottom:15px;">
            📋 COPIAR NÚMERO DE CUENTA ({info_b['cuenta']})
        </button>
        """
        components.html(html_copiar, height=55)

        st.info("💡 Puedes minimizar la página para realizar tu transferencia y luego adjuntar el comprobante abajo.")

    # 3. SUBIDA DEL COMPROBANTE Y CONFIRMACIÓN
    st.markdown("### 📄 COMPROBANTE DE PAGO *")
    comprobante_dialog = st.file_uploader(
        "Adjunta la imagen de tu transferencia o depósito:",
        type=["png", "jpg", "jpeg"],
        key="file_comp_dialog",
    )

    total_calculado = st.session_state["cant_boletos_dialog"] * r_precio
    st.markdown(
        f"<h3 style='color:#f59e0b; text-align:right;'>Total: RD$ {total_calculado:,.2f}</h3>",
        unsafe_allow_html=True,
    )

    if st.button("🚀 ENVIAR Y RESERVAR NÚMEROS", use_container_width=True, type="primary"):
        if not nombre_u.strip() or not telefono_u.strip():
            st.error("Por favor completa tu nombre y teléfono.")
        elif not banco_activo:
            st.error("Por favor selecciona un banco de pago.")
        elif not comprobante_dialog:
            st.error("Debes subir la foto del comprobante de pago.")
        else:
            # Procesamiento de la reserva
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute(
                "SELECT id, numero FROM boletos WHERE rifa_id = ? AND estado = 'disponible'",
                (rifa_id,),
            )
            disp = c.fetchall()

            cant_req = st.session_state["cant_boletos_dialog"]

            if len(disp) < cant_req:
                st.error("No hay suficientes números disponibles.")
                conn.close()
            else:
                asignados = random.sample(disp, cant_req)
                os.makedirs("comprobantes", exist_ok=True)

                path_comp = f"comprobantes/{telefono_u}_{datetime.datetime.now().timestamp()}.png"
                img = Image.open(comprobante_dialog)
                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGB")
                img.save(path_comp)

                ahora = datetime.datetime.now()
                for b_id, b_num in asignados:
                    c.execute(
                        """
                        UPDATE boletos
                        SET estado = 'reservado', usuario_nombre = ?, usuario_telefono = ?,
                            metodo_pago = ?, comprobante = ?, fecha_reserva = ?
                        WHERE id = ?
                        """,
                        (
                            nombre_u.strip(),
                            telefono_u.strip(),
                            banco_activo,
                            path_comp,
                            ahora,
                            b_id,
                        ),
                    )

                conn.commit()
                conn.close()

                st.session_state["compra_dialog_exitosa"] = True
                st.rerun()


# ---------------------------------------------------------
# INICIALIZACIÓN DE BASE DE DATOS
# ---------------------------------------------------------
def censurar_nombre(nombre):
    if not nombre or len(nombre) < 3:
        return "Usu***io"
    return f"{nombre[:3]}***{nombre[-2:] if len(nombre) > 4 else ''}"


def censurar_telefono(telefono):
    if not telefono or len(telefono) < 7:
        return "829***17"
    return f"{telefono[:3]}***{telefono[-2:]}"


def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS rifas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT, categoria TEXT, precio_boleto REAL,
            min_boletos INTEGER, total_boletos INTEGER, imagen TEXT, fecha TEXT
        )
        """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS boletos (
            id INTEGER PRIMARY KEY AUTOINCREMENT, rifa_id INTEGER, numero TEXT,
            estado TEXT DEFAULT 'disponible', usuario_nombre TEXT, usuario_telefono TEXT,
            metodo_pago TEXT, comprobante TEXT, fecha_reserva DATETIME
        )
        """
    )

    c.execute("SELECT COUNT(*) FROM rifas")
    if c.fetchone()[0] == 0:
        c.execute(
            "INSERT INTO rifas (nombre, categoria, precio_boleto, min_boletos, total_boletos, imagen, fecha) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                "PlayStation 5 Pro",
                "JUEGO",
                5.0,
                15,
                100000,
                "play.jpg",
                "Fecha pendiente",
            ),
        )
        c.execute(
            "INSERT INTO rifas (nombre, categoria, precio_boleto, min_boletos, total_boletos, imagen, fecha) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                "5 iPhone 17 Pro Max",
                "TELÉFONO",
                15.0,
                10,
                100000,
                "iphone.jpg",
                "Al vender el 80%",
            ),
        )

        for rifa_id in [1, 2]:
            numeros = [(rifa_id, f"{i:05d}") for i in range(1, 100001)]
            c.executemany(
                "INSERT INTO boletos (rifa_id, numero) VALUES (?, ?)", numeros
            )
        conn.commit()

    conn.close()


init_db()

# ---------------------------------------------------------
# BARRA SUPERIOR
# ---------------------------------------------------------
col_head1, col_head2 = st.columns([3, 2], vertical_alignment="center")

with col_head1:
    st.markdown(
        "<h2 style='color:#00f0ff; margin:0;'>SIRIO<span style='color:#ff0055;'>RIFAS</span> RD</h2>",
        unsafe_allow_html=True,
    )

with col_head2:
    c_btn_theme, c_btn_menu = st.columns([1, 2])

    with c_btn_theme:
        icono_tema = "☀️" if es_oscuro else "🌙"
        st.button(
            icono_tema,
            on_click=cambiar_tema,
            key="btn_theme_toggle",
            use_container_width=True,
        )

    with c_btn_menu:
        with st.popover("☰ MENÚ", use_container_width=True):
            st.markdown("### 🎯 Navegación")
            seccion_menu = st.radio(
                "Selecciona una opción:",
                [
                    "🏠 Inicio & Catálogo",
                    "🔎 Verificador de boletos",
                    "❓ Cómo jugar",
                    "🤖 Soporte IA",
                    "🏆 Ganadores",
                    "⚙️ Administración",
                ],
                label_visibility="collapsed",
            )

if "seccion_activa" not in st.session_state:
    st.session_state["seccion_activa"] = "🏠 Inicio & Catálogo"

if "seccion_menu" in locals() and seccion_menu:
    st.session_state["seccion_activa"] = seccion_menu

seccion = st.session_state["seccion_activa"]

st.markdown("---")

# Mensaje de confirmación si completó la compra
if st.session_state.get("compra_dialog_exitosa"):
    st.success("🎉 ¡Felicidades! Tu compra ha sido enviada y está en proceso de validación.")
    st.info("Puedes verificar tus boletos en la sección **🔎 Verificador de boletos**.")
    st.session_state.pop("compra_dialog_exitosa", None)

# ---------------------------------------------------------
# SECCIÓN: INICIO Y CATÁLOGO
# ---------------------------------------------------------
if seccion == "🏠 Inicio & Catálogo":
    col_logo, col_titulo = st.columns([1, 2], vertical_alignment="center")
    with col_logo:
        if os.path.exists("logo.png"):
            st.image("logo.png", width=180)
    with col_titulo:
        st.markdown(
            "<p style='color: #F5C518; font-weight: bold; margin-bottom: 0;'>Plataforma Exclusiva de Rifas</p>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<h1 style='color: {txt_color}; font-size: 2rem; margin-top: 0;'>CATÁLOGO DE RIFAS</h1>",
            unsafe_allow_html=True,
        )

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "SELECT id, nombre, categoria, precio_boleto, min_boletos, total_boletos, imagen, fecha FROM rifas"
    )
    rifas_list = c.fetchall()

    cols_dinamicas = st.columns(len(rifas_list))

    for idx, r in enumerate(rifas_list):
        r_id, r_nombre, r_cat, r_precio, r_min, r_tot, r_img, r_fecha = r

        c.execute(
            "SELECT COUNT(*) FROM boletos WHERE rifa_id = ? AND estado != 'disponible'",
            (r_id,),
        )
        vendidos = c.fetchone()[0]
        progreso = round((vendidos / r_tot) * 100, 2)

        if "iPhone" in r_nombre:
            frase_motivacional = "Por tan solo $15 pesos participas por 5 iPhone 17 Pro Max 📱🔥"
            subfrase_motivacional = "¡Cualquiera de esos 5 puede ser tuyo! 🤩"
        else:
            frase_motivacional = "Por tan solo $5 pesitos participas por una PlayStation 5 Pro 🎮🔥"
            subfrase_motivacional = "¡Llévatela a casa hoy mismo! 🥳"

        with cols_dinamicas[idx]:
            st.markdown('<div class="raffle-card-wrapper">', unsafe_allow_html=True)

            st.markdown(
                f"""
                <div class="image-container-relative">
                    <div class="category-badge-overlay">{r_cat}</div>
                """,
                unsafe_allow_html=True,
            )

            if r_img and os.path.exists(r_img):
                st.image(r_img, use_container_width=True)

            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown(
                f"""
                <h3 style="color:{txt_color}; margin-top:5px; margin-bottom:5px; font-weight:800;">{r_nombre}</h3>
                <p style="color:{txt_color}; font-size:0.95rem; font-weight:600; margin:8px 0;">{frase_motivacional}</p>
                <p style="color:#00f0ff; font-size:0.88rem; font-weight:bold; margin-bottom:12px;">{subfrase_motivacional}</p>
                <p style="color:#00f0ff; font-size:0.8rem; font-weight:bold; margin-bottom:2px;">PROGRESO: {progreso}%</p>
                """,
                unsafe_allow_html=True,
            )

            st.progress(progreso / 100)

            col_precio, col_boton = st.columns([1.1, 1], vertical_alignment="center")

            with col_precio:
                st.markdown(
                    f"""
                    <div>
                        <span style="color:#00f0ff; font-size:1.5rem; font-weight:900;">RD$ {r_precio:,.2f}</span><br/>
                        <span style="color:{subtxt_color}; font-size:0.75rem;">Min {r_min} boletos</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with col_boton:
                st.markdown('<div class="btn-buy-container">', unsafe_allow_html=True)

                def preparar_y_abrir_modal(r_id=r_id, r_nombre=r_nombre, r_precio=r_precio, r_min=r_min):
                    st.session_state["rifa_seleccionada"] = r_id
                    st.session_state["nombre_rifa"] = r_nombre
                    st.session_state["precio_rifa"] = r_precio
                    st.session_state["min_rifa"] = r_min
                    st.session_state["abrir_modal_compra"] = True

                st.button(
                    "JUGAR",
                    key=f"btn_jugar_{r_id}",
                    on_click=preparar_y_abrir_modal,
                    use_container_width=True,
                )
                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

    conn.close()

    # Si se presionó JUGAR, se despliega la ventana
    if st.session_state.get("abrir_modal_compra"):
        st.session_state.pop("abrir_modal_compra", None)
        ventana_compra_dialogo()

# ---------------------------------------------------------
# OTRAS SECCIONES
# ---------------------------------------------------------
elif seccion == "🔎 Verificador de boletos":
    st.header("🔎 Verificador de Boletos")
    tel_input = st.text_input("Número de teléfono o boleto:", placeholder="8091234567")
    if st.button("BUSCAR"):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute(
            "SELECT numero, usuario_nombre, usuario_telefono, estado FROM boletos WHERE usuario_telefono LIKE ? OR numero = ?",
            (f"%{tel_input}%", tel_input),
        )
        res = c.fetchall()
        conn.close()
        if not res:
            st.warning("No se encontraron resultados.")
        else:
            for row in res:
                st.write(f"🎟️ Boleto: **{row[0]}** | Estado: `{row[3]}`")

elif seccion == "❓ Cómo jugar":
    st.header("❓ Cómo Participar")
    st.markdown("1. Presiona JUGAR en el catálogo.\n2. Selecciona la cantidad de números con los botones `+` / `-`.\n3. Selecciona tu banco, copia la cuenta y sube el comprobante.")

elif seccion == "🤖 Soporte IA":
    abrir_soporte_ia()

elif seccion == "🏆 Ganadores":
    st.header("🏆 Ganadores")
    st.info("Próximamente.")

elif seccion == "⚙️ Administración":
    st.header("⚙️ Administración")
    pass_admin = st.text_input("Contraseña", type="password")
    if pass_admin == "admin123":
        st.success("Acceso concedido.")
