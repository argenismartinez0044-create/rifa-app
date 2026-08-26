import datetime
import os
import random
import sqlite3
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image

# ---------------------------------------------------------
# CONFIGURACIÓN INICIAL DE PÁGINA (SIEMPRE PRIMERA LÍNEA)
# ---------------------------------------------------------
st.set_page_config(
    page_title="Rifas Sirio RD",
    page_icon="🎲",
    layout="wide",
    initial_sidebar_state="collapsed",
)

DB_FILE = "rifas_v4.db"
WHATSAPP_NUMERO = "8294835217"

# Inicialización de Estados
if "paso_compra" not in st.session_state:
    st.session_state["paso_compra"] = 0
if "tema_claro" not in st.session_state:
    st.session_state["tema_claro"] = False
if "vista_actual" not in st.session_state:
    st.session_state["vista_actual"] = "rifas"
if "chat_abierto" not in st.session_state:
    st.session_state["chat_abierto"] = False
if "esperando_telefono_ia" not in st.session_state:
    st.session_state["esperando_telefono_ia"] = False

# ---------------------------------------------------------
# ESTILOS CSS PROFESIONALES (TEMA DINÁMICO & NEÓN)
# ---------------------------------------------------------
bg_color = (
    "#f8fafc"
    if st.session_state["tema_claro"]
    else "linear-gradient(135deg, #070913 0%, #0c1021 50%, #05060b 100%)"
)
text_color = "#0f172a" if st.session_state["tema_claro"] else "#FFFFFF"
card_bg = (
    "#ffffff"
    if st.session_state["tema_claro"]
    else "rgba(15, 23, 42, 0.85)"
)
card_border = "#e2e8f0" if st.session_state["tema_claro"] else "#1e293b"

st.markdown(
    f"""
    <style>
    .stApp {{ background: {bg_color} !important; color: {text_color}; }}
    
    /* Animación Parpadeante */
    @keyframes pulse-gold {{
        0% {{ box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.7); opacity: 0.8; }}
        70% {{ box-shadow: 0 0 0 10px rgba(245, 158, 11, 0); opacity: 1; }}
        100% {{ box-shadow: 0 0 0 0 rgba(245, 158, 11, 0); opacity: 0.8; }}
    }}
    
    @keyframes pulse-green {{
        0% {{ box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7); opacity: 0.8; }}
        70% {{ box-shadow: 0 0 0 10px rgba(34, 197, 94, 0); opacity: 1; }}
        100% {{ box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); opacity: 0.8; }}
    }}

    .badge-pending {{
        display: inline-block;
        background: linear-gradient(90deg, #b45309 0%, #d97706 100%);
        color: #ffffff;
        font-weight: bold;
        font-size: 0.75rem;
        padding: 4px 10px;
        border-radius: 20px;
        text-align: center;
        animation: pulse-gold 1.8s infinite;
        border: 1px solid #f59e0b;
    }}

    .badge-approved {{
        display: inline-block;
        background: linear-gradient(90deg, #15803d 0%, #16a34a 100%);
        color: #ffffff;
        font-weight: bold;
        font-size: 0.75rem;
        padding: 4px 10px;
        border-radius: 20px;
        text-align: center;
        animation: pulse-green 1.8s infinite;
        border: 1px solid #22c55e;
    }}

    .ticket-card {{
        background: {card_bg};
        border: 1px solid {card_border};
        border-radius: 12px;
        padding: 15px;
        text-align: center;
        margin-bottom: 12px;
    }}

    /* Estilos Verificador Modal */
    .verificador-box {{
        background: #090d16;
        border: 1px solid #1e3a8a;
        border-radius: 20px;
        padding: 30px;
        max-width: 650px;
        margin: 0 auto;
        box-shadow: 0 10px 30px rgba(0,0,0,0.8);
    }}
    
    /* Contador (+ / -) */
    .counter-display {{
        background: #090d16;
        border: 2px solid #2563eb;
        border-radius: 16px;
        padding: 15px 30px;
        font-size: 2.8rem;
        font-weight: 800;
        color: #38bdf8;
        text-align: center;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# BASE DE DATOS
# ---------------------------------------------------------
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
                "Juego",
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

    c.execute(
        "UPDATE rifas SET min_boletos = 15, precio_boleto = 5.0 WHERE id = 1"
    )
    c.execute(
        "UPDATE rifas SET min_boletos = 10, precio_boleto = 15.0, nombre = '5 iPhone 17 Pro Max' WHERE id = 2"
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
# BARRA DE NAVEGACIÓN SUPERIOR (NAVBAR HEADER - IMAGEN 1)
# ---------------------------------------------------------
c_head1, c_head2, c_head3, c_head4, c_head5 = st.columns([2.5, 1, 1, 0.6, 1.5])

with c_head1:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=180)
    else:
        st.markdown(
            "### 🎲 **RIFAS SIRIO RD**", unsafe_allow_html=True
        )

with c_head2:
    if st.button("Rifas", use_container_width=True):
        st.session_state["vista_actual"] = "rifas"
        st.session_state["paso_compra"] = 0
        st.rerun()

with c_head3:
    if st.button("Cómo jugar", use_container_width=True):
        st.session_state["vista_actual"] = "como_jugar"
        st.rerun()

with c_head4:
    ico_tema = "🌙" if st.session_state["tema_claro"] else "☀️"
    if st.button(ico_tema, use_container_width=True):
        st.session_state["tema_claro"] = not st.session_state["tema_claro"]
        st.rerun()

with c_head5:
    if st.button("🔍 Verificar boleto", type="primary", use_container_width=True):
        st.session_state["vista_actual"] = "verificador"
        st.rerun()

st.markdown("---")

# ---------------------------------------------------------
# VISTA: VERIFICADOR DE BOLETOS (IMAGEN 3)
# ---------------------------------------------------------
if st.session_state["vista_actual"] == "verificador":
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 25px;">
            <h1 style="color: #38bdf8; font-size: 2.2rem; margin-bottom: 0;">🔍 VERIFICADOR</h1>
            <p style="color: #f59e0b; font-weight: bold; letter-spacing: 2px; margin-top: 0;">DE BOLETOS</p>
            <p style="color: #94a3b8; font-size: 0.9rem;">Elige la rifa e ingresa tu teléfono (10 dígitos) o el número de boleto.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, nombre FROM rifas")
    rifas_db = c.fetchall()
    conn.close()

    dict_rifas = {r[1]: r[0] for r in rifas_db}

    st.markdown('<div class="verificador-box">', unsafe_allow_html=True)

    # Paso 1: Seleccionar Rifa
    st.markdown("##### 🎛️ Selecciona la rifa")
    rifa_sel_nom = st.selectbox(
        "Selecciona una rifa...",
        options=["Todas las rifas"] + list(dict_rifas.keys()),
        label_visibility="collapsed",
    )

    # Paso 2: Teléfono o # de Boleto
    st.markdown("##### 🎟️ Teléfono o # de boleto")
    c_input, c_btn_buscar = st.columns([3, 1])

    with c_input:
        query_buscar = st.text_input(
            "Ej: 8091234567 o 00125",
            placeholder="8091234567 • 0001",
            label_visibility="collapsed",
        )

    with c_btn_buscar:
        btn_ejecutar_buscar = st.button(
            "🔍 BUSCAR", type="primary", use_container_width=True
        )

    st.caption(
        "ℹ️ Ingrese el **teléfono** (10 dígitos, solo números sin espacios ni guiones). El **número de boleto** debe coincidir exactamente."
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if btn_ejecutar_buscar and query_buscar:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()

        q_clean = query_buscar.strip()

        if rifa_sel_nom != "Todas las rifas":
            r_id_filter = dict_rifas[rifa_sel_nom]
            c.execute(
                """
                SELECT b.numero, b.estado, r.nombre, b.usuario_nombre, b.usuario_telefono 
                FROM boletos b JOIN rifas r ON b.rifa_id = r.id 
                WHERE b.rifa_id = ? AND (b.usuario_telefono = ? OR b.numero = ?)
                """,
                (r_id_filter, q_clean, q_clean),
            )
        else:
            c.execute(
                """
                SELECT b.numero, b.estado, r.nombre, b.usuario_nombre, b.usuario_telefono 
                FROM boletos b JOIN rifas r ON b.rifa_id = r.id 
                WHERE b.usuario_telefono = ? OR b.numero = ?
                """,
                (q_clean, q_clean),
            )

        resultados = c.fetchall()
        conn.close()

        st.markdown("<br>", unsafe_allow_html=True)
        if resultados:
            st.success(f"🎉 Se encontraron **{len(resultados)} boletos** registrados:")
            cols_res = st.columns(4)
            for idx, res in enumerate(resultados):
                b_num, b_est, r_nom, u_nom, u_tel = res
                badge = (
                    '<div class="badge-approved">APROBADO</div>'
                    if b_est == "confirmado"
                    else '<div class="badge-pending">PENDIENTE A CONFIRMAR</div>'
                )

                with cols_res[idx % 4]:
                    st.markdown(
                        f"""
                        <div class="ticket-card">
                            <div style="font-size: 0.75rem; color: #94a3b8;">{r_nom}</div>
                            <div style="font-size: 1.6rem; font-weight: bold; color: #38bdf8; margin: 5px 0;">{b_num}</div>
                            {badge}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
        else:
            st.warning("⚠️ No se encontraron boletos asociados con esa información.")

# ---------------------------------------------------------
# VISTA: CÓMO JUGAR
# ---------------------------------------------------------
elif st.session_state["vista_actual"] == "como_jugar":
    st.header("❓ Cómo Participar en Rifas Sirio RD")
    st.markdown(
        """
        1. **Elige tu Premio:** Revisa nuestro catálogo e ingresa a la jugada.
        2. **Selecciona tu Combo:** Escoge un paquete o la cantidad de números deseada.
        3. **Realiza la Transferencia:** Utiliza Banreservas o Banco Popular.
        4. **Sube tu Comprobante:** Completa tus datos y adjunta la imagen del pago.
        5. **Verifica tus Boletos:** Consulta con tu número telefónico en el Verificador.
        """
    )
    if st.button("🎮 Ir al Catálogo"):
        st.session_state["vista_actual"] = "rifas"
        st.rerun()

# ---------------------------------------------------------
# VISTA: CATÁLOGO Y COMPRA EN PASOS
# ---------------------------------------------------------
elif st.session_state["vista_actual"] == "rifas":
    paso = st.session_state.get("paso_compra", 0)

    if paso == 0:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute(
            "SELECT id, nombre, categoria, precio_boleto, min_boletos, total_boletos, imagen, fecha FROM rifas"
        )
        rifas_list = c.fetchall()

        cols_rifa = st.columns(len(rifas_list))
        for idx, r in enumerate(rifas_list):
            r_id, r_nombre, r_cat, r_precio, r_min, r_tot, r_img, r_fecha = r
            c.execute(
                "SELECT COUNT(*) FROM boletos WHERE rifa_id = ? AND estado != 'disponible'",
                (r_id,),
            )
            vendidos = c.fetchone()[0]
            progreso = round((vendidos / r_tot) * 100, 2)

            with cols_rifa[idx]:
                if r_img and os.path.exists(r_img):
                    st.image(r_img, use_container_width=True)
                st.subheader(r_nombre)
                st.write(f"📅 **Fecha:** {r_fecha}")
                st.write(f"📊 **PROGRESO: {progreso}%**")
                st.progress(progreso / 100)
                st.markdown(f"### **RD$ {r_precio:.2f}**")
                st.caption(f"Mínimo {r_min} boletos")

                def iniciar_jugada(
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
                    st.session_state["cant_boletos"] = minimo

                st.button(
                    f"🎮 JUGAR POR {r_nombre.upper()}",
                    key=f"btn_jugar_{r_id}",
                    on_click=iniciar_jugada,
                    use_container_width=True,
                )
        conn.close()

    elif paso == 1:
        nombre = st.session_state["nombre_rifa"]
        precio = st.session_state["precio_rifa"]
        minimo = int(st.session_state["min_rifa"])

        st.markdown(f"## 🎁 Selecciona un Paquete - {nombre}")

        combos_def = [
            ("⭐ POPULAR", "PRO", minimo, "🚀"),
            ("ELITE", "ELITE", int(minimo * 1.5), "🏆"),
            ("CAMPEÓN", "CAMPEÓN", minimo * 25 // 10, "👑"),
            ("⭐ VIP", "LEYENDA", minimo * 5, "⚡"),
            ("🔥 MÁXIMO", "MÍTICO", minimo * 10, "🦅"),
        ]

        c_cols = st.columns(len(combos_def))
        for i, (tag, titulo_combo, cant_c, icono) in enumerate(combos_def):
            costo_c = cant_c * precio
            with c_cols[i]:
                st.markdown(
                    f"""
                    <div style="background: #0f172a; border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 12px; padding: 12px; text-align: center; margin-bottom: 10px;">
                        <span style="font-size: 0.7rem; background: #1e293b; color: #f59e0b; padding: 2px 6px; border-radius: 6px; font-weight: bold;">{tag}</span>
                        <div style="font-size: 1.8rem; margin: 8px 0;">{icono}</div>
                        <div style="font-size: 0.8rem; color: #94a3b8;">{titulo_combo}</div>
                        <div style="font-size: 1.6rem; font-weight: bold; color: #38bdf8;">{cant_c}</div>
                        <div style="font-size: 0.75rem; color: #64748b;">NÚMEROS</div>
                        <div style="font-size: 1rem; font-weight: bold; color: #ffffff; margin-top: 5px;">RD$ {int(costo_c):,}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button(
                    "Seleccionar", key=f"btn_combo_{i}", use_container_width=True
                ):
                    st.session_state["cant_boletos"] = cant_c
                    st.session_state["paso_compra"] = 2
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(
            "⚙️ ELEGIR CANTIDAD PERSONALIZADA",
            key="btn_custom_qty",
            use_container_width=True,
        ):
            st.session_state["cant_boletos"] = minimo
            st.session_state["paso_compra"] = 2
            st.rerun()

    elif paso == 2:
        nombre = st.session_state["nombre_rifa"]
        precio = st.session_state["precio_rifa"]
        minimo = int(st.session_state["min_rifa"])

        st.markdown(f"## 📝 Completa tu Registro - {nombre}")

        c_restar, c_num, c_sumar = st.columns([1, 2, 1])
        with c_restar:
            if st.button("➖ Restar", use_container_width=True):
                if st.session_state["cant_boletos"] > minimo:
                    st.session_state["cant_boletos"] -= 1
                    st.rerun()
        with c_num:
            st.markdown(
                f'<div class="counter-display">{st.session_state["cant_boletos"]}</div>',
                unsafe_allow_html=True,
            )
        with c_sumar:
            if st.button("➕ Sumar", use_container_width=True):
                st.session_state["cant_boletos"] += 1
                st.rerun()

        st.markdown("### 👤 Datos del Participante")
        col_nom, col_tel = st.columns(2)
        with col_nom:
            nombre_cliente = st.text_input("Nombre Completo *")
        with col_tel:
            telefono_cliente = st.text_input("Teléfono (WhatsApp) *")

        banco_sel = st.session_state.get("banco_pago", "Banreservas")
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("🏦 RESERVAS (AHORRO)", use_container_width=True):
                st.session_state["banco_pago"] = "Banreservas"
                st.rerun()
        with col_b2:
            if st.button("🏦 POPULAR (AHORRO)", use_container_width=True):
                st.session_state["banco_pago"] = "Banco Popular"
                st.rerun()

        comprobante_file = st.file_uploader(
            "Subir Comprobante", type=["png", "jpg", "jpeg"]
        )

        if st.button(
            "CONFIRMAR COMPRA ✅", type="primary", use_container_width=True
        ):
            if nombre_cliente and telefono_cliente and comprobante_file:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute(
                    "SELECT id, numero FROM boletos WHERE rifa_id = ? AND estado = 'disponible'",
                    (st.session_state["rifa_seleccionada"],),
                )
                disp = c.fetchall()
                cant = st.session_state["cant_boletos"]

                if len(disp) >= cant:
                    asignados = random.sample(disp, cant)
                    os.makedirs("comprobantes", exist_ok=True)
                    path_comp = f"comprobantes/{telefono_cliente}_{datetime.datetime.now().timestamp()}.png"
                    Image.open(comprobante_file).convert("RGB").save(path_comp)

                    num_list = []
                    for b_id, b_num in asignados:
                        num_list.append(b_num)
                        c.execute(
                            "UPDATE boletos SET estado = 'reservado', usuario_nombre = ?, usuario_telefono = ?, metodo_pago = ?, comprobante = ?, fecha_reserva = ? WHERE id = ?",
                            (
                                nombre_cliente,
                                telefono_cliente,
                                banco_sel,
                                path_comp,
                                datetime.datetime.now(),
                                b_id,
                            ),
                        )
                    conn.commit()
                    conn.close()

                    st.session_state["boletos_asignados_resumen"] = num_list
                    st.session_state["paso_compra"] = 3
                    st.rerun()

    elif paso == 3:
        st.success("🎉 ¡Boletos Reservados Exitosamente!")
        boletos = st.session_state.get("boletos_asignados_resumen", [])

        cols = st.columns(5)
        for i, n in enumerate(boletos):
            with cols[i % 5]:
                st.markdown(
                    f'<div class="ticket-card"><div style="font-size:1.4rem; color:#38bdf8;">{n}</div><div class="badge-pending">PENDIENTE A CONFIRMAR</div></div>',
                    unsafe_allow_html=True,
                )

        if st.button("ENTIENDO Y CERRAR ✅", use_container_width=True):
            st.session_state["paso_compra"] = 0
            st.rerun()

# ---------------------------------------------------------
# CHAT IA FLOTANTE Y WIDGET INTERACTIVO (IMAGEN 2)
# ---------------------------------------------------------
st.markdown("---")
if st.button("💬 Chat Virtual - Rifas Sirio RD", type="primary"):
    st.session_state["chat_abierto"] = not st.session_state["chat_abierto"]

if st.session_state["chat_abierto"]:
    st.markdown(
        """
        <div style="background: #0d111e; border: 1px solid #1e293b; border-radius: 16px; padding: 20px; margin-top: 10px;">
            <div style="display: flex; align-items: center; margin-bottom: 15px;">
                <div style="background: #2563eb; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; margin-right: 12px;">🤖</div>
                <div>
                    <h4 style="color: #ffffff; margin: 0;">RIFAS SIRIO RD</h4>
                    <p style="color: #38bdf8; font-size: 0.8rem; margin: 0;">● Asistente Virtual 24/7</p>
                </div>
            </div>
            <p style="color: #cbd5e1; font-size: 0.95rem;">
                ¡Hola! 🖐️ Soy el asistente virtual de <strong>Rifas Sirio RD</strong>. Puedo ayudarte con tus boletos, rifas activas, métodos de pago y más.
            </p>
            <p style="color: #f59e0b; font-weight: bold; font-size: 0.9rem;">¿En qué te puedo ayudar hoy?</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c_ia1, c_ia2 = st.columns(2)
    with c_ia1:
        if st.button("🎰 Estado de mi compra", use_container_width=True):
            st.session_state["esperando_telefono_ia"] = True
            st.session_state["respuesta_ia_msg"] = (
                "Por favor, ingresa tu número de teléfono de WhatsApp (el mismo que usaste al comprar):"
            )

        if st.button("💳 Métodos de pago", use_container_width=True):
            st.session_state["esperando_telefono_ia"] = False
            st.session_state["respuesta_ia_msg"] = (
                "**Cuentas bancarias oficiales:**\n\n"
                "🟣 **Banreservas (Ahorros):** `9606561652`\n"
                "🔵 **Banco Popular (Ahorros):** `821794971`"
            )

    with c_ia2:
        if st.button("🎰 Rifas activas", use_container_width=True):
            st.session_state["esperando_telefono_ia"] = False
            st.session_state["respuesta_ia_msg"] = (
                "🔥 **Rifas Activas Actualmente:**\n"
                "1. PlayStation 5 Pro — RD$ 5.00/boleto\n"
                "2. 5 iPhone 17 Pro Max — RD$ 15.00/boleto"
            )

        if st.button("🛒 Cómo comprar", use_container_width=True):
            st.session_state["esperando_telefono_ia"] = False
            st.session_state["respuesta_ia_msg"] = (
                "1. Selecciona tu rifa en el catálogo.\n"
                "2. Elige tu combo de boletos.\n"
                "3. Realiza la transferencia bancaria y sube tu foto comprobante."
            )

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("📱 Hablar con soporte humano", use_container_width=True):
        st.markdown(
            f"[💬 Haz clic aquí para chatear por WhatsApp](https://wa.me/{WHATSAPP_NUMERO})"
        )

    if "respuesta_ia_msg" in st.session_state:
        st.info(st.session_state["respuesta_ia_msg"])

    if st.session_state.get("esperando_telefono_ia"):
        tel_ia = st.text_input("Ingresa tu número aquí:")
        if st.button("Consultar Estado"):
            if tel_ia:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute(
                    """
                    SELECT b.numero, b.estado, r.nombre 
                    FROM boletos b JOIN rifas r ON b.rifa_id = r.id 
                    WHERE b.usuario_telefono = ?
                    """,
                    (tel_ia.strip(),),
                )
                boletos_ia = c.fetchall()
                conn.close()

                if boletos_ia:
                    rifas_dict = {}
                    for num, est, r_nom in boletos_ia:
                        if r_nom not in rifas_dict:
                            rifas_dict[r_nom] = []
                        rifas_dict[r_nom].append((num, est))

                    st.success(
                        f"📊 **Resumen de Compra Encontrado ({len(boletos_ia)} boletos en total):**"
                    )
                    for r_nom, items in rifas_dict.items():
                        st.markdown(f"🏆 **Rifa:** `{r_nom}`")
                        st.markdown(
                            f"🎟️ **Cantidad de boletos:** `{len(items)}`"
                        )

                        nums_str = ", ".join([it[0] for it in items])
                        est_general = (
                            "✅ Aprobado"
                            if any(it[1] == "confirmado" for it in items)
                            else "⏳ Verificándose (Pendiente)"
                        )

                        st.markdown(f"📌 **Estado:** {est_general}")
                        st.markdown(f"🔢 **Números:** `{nums_str}`")
                        st.markdown("---")
                else:
                    st.warning(
                        "No encontramos boletos registrados con ese número telefónico."
                    )
