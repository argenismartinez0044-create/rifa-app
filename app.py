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
    st.session_state["modo_tema"] = "oscuro"  # Por defecto oscuro

def cambiar_tema():
    if st.session_state["modo_tema"] == "oscuro":
        st.session_state["modo_tema"] = "claro"
    else:
        st.session_state["modo_tema"] = "oscuro"

es_oscuro = st.session_state["modo_tema"] == "oscuro"

# Definición de colores según el tema
bg_app = "linear-gradient(180deg, #090b14 0%, #05060a 100%)" if es_oscuro else "#F8FAFC"
txt_color = "#FFFFFF" if es_oscuro else "#0F172A"
card_bg = "#0e1222" if es_oscuro else "#FFFFFF"
card_border = "#1e293b" if es_oscuro else "#E2E8F0"
subtxt_color = "#a0aabf" if es_oscuro else "#475569"
input_bg = "#0e1222" if es_oscuro else "#F1F5F9"

st.markdown(
    f"""
    <style>
    /* Fondo principal cibernético / adaptable */
    .stApp {{
        background: {bg_app} !important;
        color: {txt_color};
        font-family: 'Segoe UI', Roboto, sans-serif;
    }}

    header {{visibility: hidden;}}
    .block-container {{ padding-top: 1rem; padding-bottom: 2rem; }}

    /* Botón general */
    div.stButton > button {{
        background: linear-gradient(90deg, #1b2238 0%, #111525 100%);
        color: #FFFFFF;
        border: 1px solid #00f0ff;
        border-radius: 8px;
        font-weight: bold;
        transition: all 0.3s ease;
    }}
    div.stButton > button:hover {{
        border-color: #ff0055;
        box-shadow: 0 0 10px #ff0055;
        color: #ffffff;
    }}

    /* Botones de Acción / Comprar */
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

    /* Inputs y Selectboxes */
    .stSelectbox > div > div, .stTextInput > div > div > input, .stNumberInput > div > div > input {{
        background-color: {input_bg} !important;
        border: 1px solid #ff0055 !important;
        border-radius: 10px !important;
        color: {txt_color} !important;
    }}

    /* --- TARJETA DE DINÁMICA CON HOVER Y BORDE AZUL --- */
    .raffle-card-wrapper {{
        position: relative;
        background: {card_bg};
        border: 1px solid {card_border};
        border-radius: 16px;
        padding: 16px;
        margin-bottom: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
        transition: transform 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease;
    }}

    .raffle-card-wrapper:hover {{
        transform: translateY(-6px);
        border-color: #00f0ff !important;
        box-shadow: 0 0 20px rgba(0, 240, 255, 0.4) !important;
    }}

    /* Badge de Categoría no cliqueable arriba */
    .category-badge {{
        position: absolute;
        top: 24px;
        right: 24px;
        background: rgba(15, 23, 42, 0.85);
        color: #f59e0b;
        border: 1px solid #f59e0b;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 800;
        letter-spacing: 1px;
        text-transform: uppercase;
        z-index: 10;
        pointer-events: none;
    }}

    /* Frases motivacionales */
    .motivational-text {{
        color: {txt_color};
        font-size: 0.95rem;
        font-weight: 600;
        margin: 10px 0;
        line-height: 1.4;
    }}

    .motivational-subtext {{
        color: #00f0ff;
        font-size: 0.88rem;
        font-weight: bold;
        margin-bottom: 12px;
    }}

    /* Tarjetas de Verificador */
    .ticket-card {{
        background: {card_bg};
        border: 1px solid {card_border};
        border-radius: 12px;
        padding: 15px;
        text-align: center;
        margin-bottom: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }}
    .ticket-number {{
        font-size: 1.8rem;
        font-weight: 900;
        color: #fce205;
        letter-spacing: 2px;
    }}
    .ticket-user {{
        color: {subtxt_color};
        font-size: 0.85rem;
    }}

    .step-pill {{
        background: #172554;
        color: #60a5fa;
        font-size: 0.8rem;
        font-weight: bold;
        padding: 4px 12px;
        border-radius: 6px;
        display: inline-block;
        margin-bottom: 8px;
    }}
    </style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# DIÁLOGO DE CHAT IA
# ---------------------------------------------------------
@st.dialog("🤖 Asistente Virtual - Rifas Sirio RD")
def abrir_soporte_ia():
    st.caption("Respuestas instantáneas las 24 horas.")

    if "mensajes_chat" not in st.session_state:
        st.session_state["mensajes_chat"] = [
            {
                "role": "assistant",
                "content": "¡Hola! Soy tu asistente de **Rifas Luxury** 🎲.\n\n¿En qué te puedo ayudar hoy?",
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

        if any(
            w in txt
            for w in [
                "jugar",
                "participar",
                "funciona",
                "pasos",
                "comprar",
                "instrucciones",
            ]
        ):
            resp = (
                "**Pasos para participar:**\n"
                "1. Selecciona un premio en **🏠 Inicio & Catálogo**.\n"
                "2. Elige tus boletos/combo y realiza la transferencia.\n"
                "3. Adjunta la foto del comprobante.\n"
                "4. ¡Tus números quedan reservados!"
            )
        elif any(
            w in txt
            for w in [
                "pago",
                "banco",
                "transferencia",
                "banreservas",
                "popular",
                "cuenta",
            ]
        ):
            resp = (
                "**Cuentas bancarias oficiales:**\n\n"
                "🔴 **Banreservas (Ahorros):** `9606561652` (Argenis Martinez C.)\n"
                "🔵 **Banco Popular (Ahorros):** `821794971` (Argenis Martinez)"
            )
        elif any(
            w in txt for w in ["verificar", "consultar", "mi boleto", "numeros"]
        ):
            resp = "Ingresa a la sección **🔎 Verificador de boletos** e introduce tu número telefónico."
        elif any(w in txt for w in ["ganador", "sorteo", "fecha", "cuando"]):
            resp = "Los premios se rifan al alcanzar la meta de boletos indicadas en la ficha de la rifa."
        elif any(w in txt for w in ["precio", "costo", "minimo", "mínimo", "combo"]):
            resp = (
                "• **PlayStation 5 Pro:** RD$ 5.00 / boleto (Mínimo 15 boletos).\n"
                "• **5 iPhone 17 Pro Max:** RD$ 15.00 / boleto (Mínimo 10 boletos)."
            )
        else:
            resp = "¿Necesitas ayuda personalizada? Puedes hablar con un asesor por WhatsApp."
            mostrar_wa = True

        st.session_state["mensajes_chat"].append(
            {"role": "assistant", "content": resp}
        )
        if mostrar_wa:
            st.markdown(
                f"[💬 Hablar con soporte en WhatsApp](https://wa.me/{WHATSAPP_NUMERO})"
            )
        st.rerun()


# ---------------------------------------------------------
# INICIALIZACIÓN DE BASE DE DATOS Y FUNCIONES AUXILIARES
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

    c.execute("UPDATE rifas SET min_boletos = 15, precio_boleto = 5.0, categoria = 'JUEGO' WHERE id = 1")
    c.execute(
        "UPDATE rifas SET min_boletos = 10, precio_boleto = 15.0, nombre = '5 iPhone 17 Pro Max', categoria = 'TELÉFONO' WHERE id = 2"
    )
    conn.commit()
    conn.close()


def liberar_expirados():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    hace_15_min = datetime.datetime.now() - datetime.timedelta(minutes=15)
    c.execute(
        """
        UPDATE boletos 
        SET estado = 'disponible', usuario_nombre = NULL, usuario_telefono = NULL,
            metodo_pago = NULL, comprobante = NULL, fecha_reserva = NULL
        WHERE estado = 'reservado' AND fecha_reserva < ?
        """,
        (hace_15_min,),
    )
    conn.commit()
    conn.close()


init_db()
liberar_expirados()

# ---------------------------------------------------------
# BARRA SUPERIOR (MODO CLARO / OSCURO + MENÚ)
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
        st.button(icono_tema, on_click=cambiar_tema, key="btn_theme_toggle", help="Cambiar Modo Claro/Oscuro", use_container_width=True)

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

    # Cargar las 2 dinámicas
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

        # Frases motivacionales personalizadas por dinámica
        if "iPhone" in r_nombre:
            frase_motivacional = "Por tan solo $15 pesos participas por 5 iPhone 17 Pro Max 📱🔥"
            subfrase_motivacional = "¡Cualquiera de esos 5 puede ser tuyo! 🤩"
        else:
            frase_motivacional = "Por tan solo $5 pesitos participas por una PlayStation 5 Pro 🎮🔥"
            subfrase_motivacional = "¡Llévatela a casa hoy mismo! 🥳"

        with cols_dinamicas[idx]:
            # Contenedor principal con efecto HOVER cibernético y borde azul
            st.markdown(
                f"""
                <div class="raffle-card-wrapper">
                    <div class="category-badge">{r_cat}</div>
                """,
                unsafe_allow_html=True,
            )

            # Imagen de la Rifa
            if r_img and os.path.exists(r_img):
                st.image(r_img, use_container_width=True)

            # Título y Frases motivacionales
            st.markdown(
                f"""
                <h3 style="color:#ffffff if {es_oscuro} else #0f172a; margin-top:10px; margin-bottom:5px; font-weight:800;">{r_nombre}</h3>
                <p class="motivational-text">{frase_motivacional}</p>
                <p class="motivational-subtext">{subfrase_motivacional}</p>
                <p style="color:#00f0ff; font-size:0.8rem; font-weight:bold; margin-bottom:2px;">PROGRESO: {progreso}%</p>
                """,
                unsafe_allow_html=True,
            )

            st.progress(progreso / 100)

            # Precio, Mínimo y Botón JUGAR en la misma fila
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

                def seleccionar_rifa(
                    rifa_id=r_id,
                    nombre=r_nombre,
                    precio=r_precio,
                    minimo=r_min,
                ):
                    st.session_state["rifa_seleccionada"] = rifa_id
                    st.session_state["nombre_rifa"] = nombre
                    st.session_state["precio_rifa"] = precio
                    st.session_state["min_rifa"] = minimo
                    st.session_state["paso_compra"] = 1
                    st.session_state["modo_paquete"] = "PAQUETES"
                    st.session_state["cant_boletos"] = minimo

                st.button(
                    "JUGAR",
                    key=f"btn_jugar_{r_id}",
                    on_click=seleccionar_rifa,
                    use_container_width=True,
                )
                st.markdown("</div>", unsafe_allow_html=True)

            # Cierre de la tarjeta
            st.markdown("</div>", unsafe_allow_html=True)

    conn.close()

    # ---------------------------------------------------------
    # FLUJO DE COMPRA: SELECCIÓN DE PAQUETES O CANTIDAD LIBRE
    # ---------------------------------------------------------
    if "rifa_seleccionada" in st.session_state:
        st.markdown("---")

        nombre = st.session_state["nombre_rifa"]
        precio = st.session_state["precio_rifa"]
        minimo = int(st.session_state["min_rifa"])
        paso = st.session_state.get("paso_compra", 1)

        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
                        border-radius: 16px; padding: 20px; text-align: center;">
                <span style="background-color: #F5C518; color: #000; font-weight: 800;
                             padding: 4px 12px; border-radius: 20px;">COMPLETA TU COMPRA</span>
                <h2 style="color: #FFFFFF; margin: 10px 0;">🎉 {nombre} 🎉</h2>
                <p style="color: #E0E0E0; margin: 0;">
                    Precio unitario: <strong style="color: #F5C518;">RD$ {precio:.2f}</strong>
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # PASO 1: Selección PAQUETES vs CANTIDAD LIBRE + Datos
        if paso == 1:
            st.subheader("🎟️ 1. ¿Cómo quieres participar?")

            col_modo1, col_modo2 = st.columns(2)
            with col_modo1:
                if st.button("📦 PAQUETES (COMBOS)", use_container_width=True, type="primary" if st.session_state.get("modo_paquete") == "PAQUETES" else "secondary"):
                    st.session_state["modo_paquete"] = "PAQUETES"
                    st.rerun()
            with col_modo2:
                if st.button("🔢 CANTIDAD LIBRE", use_container_width=True, type="primary" if st.session_state.get("modo_paquete") == "LIBRE" else "secondary"):
                    st.session_state["modo_paquete"] = "LIBRE"
                    st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)

            if st.session_state.get("modo_paquete") == "PAQUETES":
                st.caption("Selecciona uno de nuestros paquetes preferidos:")

                combos_def = [
                    (f"{minimo} BOLETOS", minimo),
                    (f"{minimo * 2} BOLETOS", minimo * 2),
                    (f"{minimo * 3} BOLETOS", minimo * 3),
                    (f"{minimo * 5} BOLETOS", minimo * 5),
                    (f"{minimo * 10} BOLETOS", minimo * 10),
                ]

                c_cols = st.columns(len(combos_def))
                for i, (nombre_combo, cant_combo) in enumerate(combos_def):
                    cant_combo = min(100, cant_combo)
                    costo_combo = cant_combo * precio
                    with c_cols[i]:
                        st.markdown(
                            f"""
                            <div style="background: rgba(0, 240, 255, 0.08); border: 1px solid #00f0ff; padding: 12px; border-radius: 10px; text-align: center; margin-bottom: 8px;">
                                <strong style="color:#00f0ff;">🎟️ {cant_combo}</strong><br/>
                                <small style="color:{txt_color}; font-size:0.75rem;">BOLETOS</small><br/>
                                <span style="color:#f59e0b; font-weight:800;">RD$ {costo_combo:,.2f}</span>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        if st.button(
                            "SELECCIONAR",
                            key=f"btn_set_combo_{i}",
                            use_container_width=True,
                        ):
                            st.session_state["cant_boletos"] = cant_combo
                            st.rerun()
            else:
                st.caption("Ingresa manualmente el número de boletos que deseas comprar:")
                cant_libre = st.number_input(
                    "Cantidad de boletos:",
                    min_value=minimo,
                    max_value=500,
                    value=int(st.session_state.get("cant_boletos", minimo)),
                    step=1,
                )
                st.session_state["cant_boletos"] = cant_libre

            st.markdown("---")

            with st.form("form_datos_cliente"):
                st.markdown("### 👤 Tus Datos de Contacto")
                nombre_cliente = st.text_input(
                    "Nombre Completo",
                    value=st.session_state.get("nombre_cliente", ""),
                )
                telefono_cliente = st.text_input(
                    "Teléfono / WhatsApp (Ej: 8091234567)",
                    value=st.session_state.get("telefono_cliente", ""),
                )

                total_pagar = st.session_state["cant_boletos"] * precio
                st.markdown(
                    f"### 💰 Total a pagar: **{int(st.session_state['cant_boletos'])} boletos** × RD$ {precio:.2f} = <span style='color:#f59e0b;'>RD$ {total_pagar:,.2f}</span>",
                    unsafe_allow_html=True
                )

                continuar_datos = st.form_submit_button(
                    "➡️ CONTINUAR AL PAGO",
                    use_container_width=True,
                )

            if continuar_datos:
                if not nombre_cliente.strip() or not telefono_cliente.strip():
                    st.error("Por favor completa tu nombre y teléfono/WhatsApp.")
                else:
                    st.session_state["nombre_cliente"] = nombre_cliente.strip()
                    st.session_state["telefono_cliente"] = telefono_cliente.strip()
                    st.session_state["paso_compra"] = 2
                    st.rerun()

        # PASO 2: Banco, cuentas e imagen
        elif paso == 2:
            st.subheader("💳 2. Selecciona el banco para realizar el depósito")

            banco_pago = st.radio(
                "¿Dónde deseas depositar?",
                ["Banreservas", "Banco Popular"],
                horizontal=True,
                key="banco_pago",
            )

            if banco_pago == "Banreservas":
                titular = "ARGENIS MARTINEZ C."
                cuenta = "9606561652"
                img_banco = (
                    "banreservas.png"
                    if os.path.exists("banreservas.png")
                    else (
                        "barreserva.png"
                        if os.path.exists("barreserva.png")
                        else None
                    )
                )
            else:
                titular = "ARGENIS MARTINEZ"
                cuenta = "821794971"
                img_banco = (
                    "popular.png" if os.path.exists("popular.png") else None
                )

            st.markdown(
                f"""
                <div style="background: rgba(255,255,255,0.08); border-radius: 12px;
                            padding: 18px; margin-top: 10px; margin-bottom: 10px;">
                    <h4>🏦 {banco_pago}</h4>
                    <p>Tipo: <strong>Ahorros</strong></p>
                    <p>Titular: <strong>{titular}</strong></p>
                    <p>Número de cuenta:</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.code(cuenta, language=None)

            html_copiar = f"""
            <button onclick="navigator.clipboard.writeText('{cuenta}').then(() => {{
                this.innerText='✅ ¡CUENTA COPIADA!';
                this.style.background='#28a745';
                this.style.color='#fff';
            }})" 
            style="width:100%; padding:12px; border:0; border-radius:8px; 
                   background:#F5C518; color:#000; font-weight:800; cursor:pointer; font-size: 1rem;">
                📋 COPIAR NÚMERO DE CUENTA ({cuenta})
            </button>
            """
            components.html(html_copiar, height=55)

            if img_banco and os.path.exists(img_banco):
                st.image(img_banco, width=200)

            total_pagar = st.session_state["cant_boletos"] * precio
            st.markdown(f"### 💰 Total a pagar: **RD$ {total_pagar:,.2f}**")
            st.info("Realiza el depósito y luego sube la foto del volante/comprobante.")

            col1, col2 = st.columns(2)
            with col1:
                if st.button(
                    "⬅️ VOLVER A SELECCIÓN",
                    key="volver_datos",
                    use_container_width=True,
                ):
                    st.session_state["paso_compra"] = 1
                    st.rerun()

            with col2:
                if st.button(
                    "➡️ CONTINUAR Y SUBIR COMPROBANTE",
                    key="continuar_comprobante",
                    use_container_width=True,
                ):
                    st.session_state["paso_compra"] = 3
                    st.rerun()

        # PASO 3: Subida de comprobante
        elif paso == 3:
            st.subheader("📤 3. Sube el volante/comprobante del depósito")

            banco_sel = st.session_state.get("banco_pago", "Banco Seleccionado")
            st.info(
                f"Banco seleccionado: **{banco_sel}** · "
                f"Total a pagar: **RD$ {st.session_state['cant_boletos'] * precio:,.2f}**"
            )

            comprobante_file = st.file_uploader(
                "Selecciona la imagen del volante/comprobante",
                type=["png", "jpg", "jpeg"],
                key="comprobante_file",
            )

            col1, col2 = st.columns(2)
            with col1:
                if st.button(
                    "⬅️ VOLVER AL BANCO",
                    key="volver_banco",
                    use_container_width=True,
                ):
                    st.session_state["paso_compra"] = 2
                    st.rerun()

            with col2:
                reservar = st.button(
                    "✅ RESERVAR MIS BOLETOS",
                    key="reservar_final",
                    use_container_width=True,
                )

            if reservar:
                if not comprobante_file:
                    st.error(
                        "Debes subir la imagen del volante/comprobante antes de continuar."
                    )
                else:
                    conn = sqlite3.connect(DB_FILE)
                    c = conn.cursor()
                    c.execute(
                        "SELECT id, numero FROM boletos WHERE rifa_id = ? AND estado = 'disponible'",
                        (st.session_state["rifa_seleccionada"],),
                    )
                    disp = c.fetchall()

                    cant_boletos = st.session_state["cant_boletos"]

                    if len(disp) < cant_boletos:
                        st.error("No hay suficientes boletos disponibles.")
                        conn.close()
                    else:
                        asignados = random.sample(disp, cant_boletos)
                        os.makedirs("comprobantes", exist_ok=True)

                        extension = os.path.splitext(comprobante_file.name)[1].lower()
                        if extension not in [".png", ".jpg", ".jpeg"]:
                            extension = ".png"

                        path_comp = (
                            f"comprobantes/{st.session_state['telefono_cliente']}_"
                            f"{datetime.datetime.now().timestamp()}{extension}"
                        )

                        imagen_comprobante = Image.open(comprobante_file)
                        if imagen_comprobante.mode in ("RGBA", "LA", "P"):
                            imagen_comprobante = imagen_comprobante.convert("RGB")
                        imagen_comprobante.save(path_comp)

                        ahora = datetime.datetime.now()
                        num_asignados = []

                        for b_id, b_num in asignados:
                            num_asignados.append(b_num)
                            c.execute(
                                """
                                UPDATE boletos
                                SET estado = 'reservado', usuario_nombre = ?, usuario_telefono = ?,
                                    metodo_pago = ?, comprobante = ?, fecha_reserva = ?
                                WHERE id = ?
                                """,
                                (
                                    st.session_state["nombre_cliente"],
                                    st.session_state["telefono_cliente"],
                                    st.session_state.get(
                                        "banco_pago", "No especificado"
                                    ),
                                    path_comp,
                                    ahora,
                                    b_id,
                                ),
                            )

                        conn.commit()
                        conn.close()

                        st.success("🎉 ¡Boletos asignados temporalmente!")
                        st.info(
                            "Tus boletos quedan reservados temporalmente mientras se valida el comprobante."
                        )

                        st.subheader(
                            "🎟️ Tus Números Asignados (Pendientes de Validación):"
                        )
                        cols_num = st.columns(min(len(num_asignados), 5))
                        for i, n in enumerate(num_asignados):
                            cols_num[i % 5].metric(
                                "Boleto", n, delta="Pendiente", delta_color="off"
                            )

                        st.session_state["compra_completada"] = True
                        st.session_state.pop("rifa_seleccionada", None)
                        st.session_state.pop("paso_compra", None)

# ---------------------------------------------------------
# SECCIÓN: VERIFICADOR
# ---------------------------------------------------------
elif seccion == "🔎 Verificador de boletos":
    st.markdown(
        f"""
        <div style="text-align: center;">
            <h1 style="color: {txt_color}; font-weight: 900; letter-spacing: 2px;">🔎 VERIFICADOR DE BOLETOS</h1>
            <p style="color: {subtxt_color}; font-size: 0.9rem;">Ingresa tu número de teléfono o tu número asignado para consultar tus participaciones</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, nombre FROM rifas")
    lista_rifas = c.fetchall()
    conn.close()

    dict_rifas = {r[1]: r[0] for r in lista_rifas}

    st.markdown(
        '<div class="step-pill">🔹 PASO 1 DE 2</div>', unsafe_allow_html=True
    )
    rifa_seleccionada_nom = st.selectbox(
        "▼ Selecciona la Dinámica",
        options=list(dict_rifas.keys()),
        index=0,
        key="verif_rifa_sel",
    )

    st.markdown(
        '<div class="step-pill" style="background:#831843; color:#f472b6;">🔹 PASO 2 DE 2</div>',
        unsafe_allow_html=True,
    )
    tel_input = st.text_input(
        "Número de Teléfono o #Número",
        placeholder="Ej: 8091234567 o 00001",
        key="verif_tel_input",
    )

    btn_buscar = st.button(
        "🔍 BUSCAR BOLETOS", use_container_width=True, type="primary"
    )

    if btn_buscar:
        if not tel_input:
            st.warning("Por favor ingresa un número telefónico o número de boleto.")
        else:
            rifa_id = dict_rifas[rifa_seleccionada_nom]

            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute(
                """
                SELECT numero, usuario_nombre, usuario_telefono, estado 
                FROM boletos 
                WHERE rifa_id = ? AND (usuario_telefono LIKE ? OR numero = ?) AND estado != 'disponible'
            """,
                (rifa_id, f"%{tel_input}%", tel_input),
            )
            resultados = c.fetchall()
            conn.close()

            if not resultados:
                st.markdown(
                    """
                    <div style="text-align: center; padding: 40px;">
                        <h2 style="color: #a0aabf;">🚫 No se encontraron números</h2>
                        <p style="color: #64748b;">Intenta con otro número de teléfono o número asignado.</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"<h4 style='color:#00f0ff;'>Resultados para: {rifa_seleccionada_nom}</h4>",
                    unsafe_allow_html=True,
                )
                cols = st.columns(2)

                for i, row in enumerate(resultados):
                    num, nom_u, tel_u, est = row
                    nom_censurado = censurar_nombre(nom_u)
                    tel_censurado = censurar_telefono(tel_u)

                    with cols[i % 2]:
                        st.markdown(
                            f"""
                            <div class="ticket-card">
                                <small style="color:{subtxt_color};">{rifa_seleccionada_nom}</small>
                                <div class="ticket-number">{num}</div>
                                <div class="ticket-user">👤 {nom_censurado}</div>
                                <div class="ticket-user">📞 {tel_censurado}</div>
                                <div class="step-pill" style="margin-top:8px;">● {est.upper()}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

# ---------------------------------------------------------
# OTRAS SECCIONES
# ---------------------------------------------------------
elif seccion == "❓ Cómo jugar":
    st.header("❓ Cómo Participar")
    st.markdown(
        "1. Selecciona tu premio deseado en el catálogo.\n2. Compra tus boletos seleccionando un paquete o eligiendo una cantidad libre.\n3. Transfiere el monto total a Banreservas o Banco Popular.\n4. Sube la foto del comprobante.\n5. ¡Listo! Puedes verificar tus números en el buscador."
    )

elif seccion == "🤖 Soporte IA":
    abrir_soporte_ia()

elif seccion == "🏆 Ganadores":
    st.header("🏆 Ganadores Anteriores")
    st.info("Próximamente publicaremos aquí los ganadores oficiales de nuestras dinámicas.")

elif seccion == "⚙️ Administración":
    st.header("⚙️ Panel de Administración")
    pass_admin = st.text_input("Contraseña Administrador", type="password")

    if pass_admin == "admin123":
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute(
            """
            SELECT b.id, b.numero, b.usuario_nombre, b.usuario_telefono, b.metodo_pago, b.comprobante, b.fecha_reserva, r.nombre
            FROM boletos b JOIN rifas r ON b.rifa_id = r.id
            WHERE b.estado = 'reservado'
            """
        )
        pendientes = c.fetchall()

        if not pendientes:
            st.info("No hay pagos pendientes por confirmar.")
        else:
            for boleto in pendientes:
                b_id, num, nombre, tel, pago, comp, fecha, rifa_nom = boleto
                st.markdown(f"#### 🎟️ Boleto `{num}` — {rifa_nom}")
                st.write(f"👤 {nombre} | 📱 {tel} | 💳 {pago}")

                if comp and os.path.exists(comp):
                    st.image(comp, width=250)

                c1, c2 = st.columns(2)
                if c1.button(f"Aceptar {num}", key=f"acc_{b_id}"):
                    c.execute(
                        "UPDATE boletos SET estado = 'confirmado' WHERE id = ?",
                        (b_id,),
                    )
                    conn.commit()
                    st.rerun()

                if c2.button(f"Rechazar {num}", key=f"rec_{b_id}"):
                    c.execute(
                        "UPDATE boletos SET estado = 'disponible', usuario_nombre = NULL, usuario_telefono = NULL, metodo_pago = NULL, comprobante = NULL, fecha_reserva = NULL WHERE id = ?",
                        (b_id,),
                    )
                    conn.commit()
                    st.rerun()
                st.markdown("---")
        conn.close()
    elif pass_admin != "":
        st.error("Contraseña incorrecta.")
