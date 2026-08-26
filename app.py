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
st.set_page_config(page_title="Rifas Sirio RD", page_icon="🎲", layout="wide")

DB_FILE = "rifas_v4.db"
WHATSAPP_NUMERO = "8294835217"


# ---------------------------------------------------------
# ESTILOS CSS PROFESIONALES Y ANIMACIONES PARPADEANTES
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    .stApp { background: linear-gradient(135deg, #070913 0%, #0c1021 50%, #05060b 100%) !important; color: #FFFFFF; }
    
    /* Animación Parpadeante para Estados */
    @keyframes pulse-gold {
        0% { box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.7); opacity: 0.8; }
        70% { box-shadow: 0 0 0 10px rgba(245, 158, 11, 0); opacity: 1; }
        100% { box-shadow: 0 0 0 0 rgba(245, 158, 11, 0); opacity: 0.8; }
    }
    
    @keyframes pulse-green {
        0% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7); opacity: 0.8; }
        70% { box-shadow: 0 0 0 10px rgba(34, 197, 94, 0); opacity: 1; }
        100% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); opacity: 0.8; }
    }

    /* Etiqueta Pendiente a Confirmar */
    .badge-pending {
        display: inline-block;
        background: linear-gradient(90deg, #b45309 0%, #d97706 100%);
        color: #ffffff;
        font-weight: bold;
        font-size: 0.75rem;
        padding: 4px 10px;
        border-radius: 20px;
        text-align: center;
        margin-top: 6px;
        animation: pulse-gold 1.8s infinite;
        border: 1px solid #f59e0b;
        user-select: none;
    }

    /* Etiqueta Aprobado */
    .badge-approved {
        display: inline-block;
        background: linear-gradient(90deg, #15803d 0%, #16a34a 100%);
        color: #ffffff;
        font-weight: bold;
        font-size: 0.75rem;
        padding: 4px 10px;
        border-radius: 20px;
        text-align: center;
        margin-top: 6px;
        animation: pulse-green 1.8s infinite;
        border: 1px solid #22c55e;
        user-select: none;
    }

    /* Tarjetas de Boletos */
    .ticket-card {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 15px;
        text-align: center;
        margin-bottom: 12px;
    }

    /* Cajas Informativas Azules */
    .info-box-blue {
        background: rgba(30, 58, 138, 0.25);
        border: 1px solid #2563eb;
        border-radius: 12px;
        padding: 14px 18px;
        color: #93c5fd;
        font-size: 0.92rem;
        margin: 15px 0;
    }
    
    /* Contador (+ / -) */
    .counter-display {
        background: #090d16;
        border: 2px solid #2563eb;
        border-radius: 16px;
        padding: 15px 30px;
        font-size: 2.8rem;
        font-weight: 800;
        color: #38bdf8;
        text-align: center;
        box-shadow: 0 0 20px rgba(37, 99, 235, 0.3);
    }
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

    c.execute("UPDATE rifas SET min_boletos = 15, precio_boleto = 5.0 WHERE id = 1")
    c.execute("UPDATE rifas SET min_boletos = 10, precio_boleto = 15.0, nombre = '5 iPhone 17 Pro Max' WHERE id = 2")
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
# NAVEGACIÓN PRINCIPAL
# ---------------------------------------------------------
seccion = st.sidebar.radio(
    "Navegación",
    [
        "🏠 Inicio & Catálogo",
        "🔎 Verificador de boletos",
        "❓ Cómo jugar",
        "🤖 Soporte IA",
        "🏆 Ganadores",
        "⚙️ Administración",
    ],
)

st.sidebar.markdown("---")
if st.sidebar.button("🤖 Abrir Chat de Soporte IA"):
    abrir_soporte_ia()

# ---------------------------------------------------------
# SECCIÓN: INICIO Y CATÁLOGOS CON VISTAS PASO A PASO
# ---------------------------------------------------------
if seccion == "🏠 Inicio & Catálogo":
    paso = st.session_state.get("paso_compra", 0)

    # ---------------------------------------------------------
    # PASO 0: EXCLUSIVAMENTE VER EL CATÁLOGO DE PREMIOS
    # ---------------------------------------------------------
    if paso == 0:
        col_logo, col_titulo = st.columns([1, 2])
        with col_logo:
            if os.path.exists("logo.png"):
                st.image("logo.png", width=220)
        with col_titulo:
            st.markdown(
                "<p style='color: #F5C518; font-weight: bold; margin-bottom: 0;'>Plataforma Exclusiva de Rifas</p>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<h1 style='color: #FFFFFF; font-size: 2.2rem; margin-top: 0;'>Premios Exclusivos Garantizados</h1>",
                unsafe_allow_html=True,
            )

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT id, nombre, categoria, precio_boleto, min_boletos, total_boletos, imagen, fecha FROM rifas")
        rifas_list = c.fetchall()
        
        cols_rifa = st.columns(len(rifas_list))
        
        for idx, r in enumerate(rifas_list):
            r_id, r_nombre, r_cat, r_precio, r_min, r_tot, r_img, r_fecha = r
            c.execute("SELECT COUNT(*) FROM boletos WHERE rifa_id = ? AND estado != 'disponible'", (r_id,))
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

                label_btn = (
                    f"🎮 JUGAR POR {r_nombre.upper()}"
                    if "PlayStation" in r_nombre
                    else f"📱 PARTICIPAR POR {r_nombre.upper()}"
                )

                def iniciar_jugada(rifa_id=r_id, nombre=r_nombre, precio=r_precio, minimo=r_min):
                    st.session_state["rifa_seleccionada"] = rifa_id
                    st.session_state["nombre_rifa"] = nombre
                    st.session_state["precio_rifa"] = precio
                    st.session_state["min_rifa"] = minimo
                    st.session_state["paso_compra"] = 1
                    st.session_state["cant_boletos"] = minimo

                st.button(
                    label_btn,
                    key=f"btn_jugar_{r_id}",
                    on_click=iniciar_jugada,
                    use_container_width=True,
                )
        conn.close()

    # ---------------------------------------------------------
    # PASO 1: EXCLUSIVAMENTE LA SELECCIÓN DE COMBOS
    # ---------------------------------------------------------
    elif paso == 1:
        nombre = st.session_state["nombre_rifa"]
        precio = st.session_state["precio_rifa"]
        minimo = int(st.session_state["min_rifa"])

        c_top1, c_top2 = st.columns([4, 1])
        with c_top1:
            st.markdown(f"## 🎁 Elige tu Paquete - {nombre}")
        with c_top2:
            if st.button("❌ Cancelar"):
                st.session_state["paso_compra"] = 0
                st.rerun()

        st.markdown(
            f"""
            <div style="background: linear-gradient(90deg, #0b1120 0%, #111c35 100%);
                        border: 1px solid #1e293b; border-radius: 12px; padding: 15px; text-align: center; margin-bottom: 20px;">
                <h3 style="color: #38bdf8; margin: 0; font-size: 1.4rem;">{nombre.upper()} POR RD$ {int(precio)}</h3>
                <p style="color: #94a3b8; margin: 5px 0 0 0; font-size: 0.9rem;">Selecciona un combo o define la cantidad manualmente</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

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
                if st.button("Seleccionar", key=f"btn_combo_{i}", use_container_width=True):
                    st.session_state["cant_boletos"] = cant_c
                    st.session_state["paso_compra"] = 2
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⚙️ ELEGIR CANTIDAD PERSONALIZADA", key="btn_custom_qty", use_container_width=True):
            st.session_state["cant_boletos"] = minimo
            st.session_state["paso_compra"] = 2
            st.rerun()

        st.markdown(f"<p style='text-align: center; color: #64748b; font-size: 0.8rem5;'>Compra mínima: {minimo} números</p>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # PASO 2: EXCLUSIVAMENTE CANTIDADES, DATOS Y FORMULARIO DE PAGO
    # ---------------------------------------------------------
    elif paso == 2:
        nombre = st.session_state["nombre_rifa"]
        precio = st.session_state["precio_rifa"]
        minimo = int(st.session_state["min_rifa"])

        c_top1, c_top2 = st.columns([4, 1])
        with c_top1:
            st.markdown(f"## 📝 Completa tu Registro - {nombre}")
        with c_top2:
            if st.button("⬅️ Cambiar Combo"):
                st.session_state["paso_compra"] = 1
                st.rerun()

        st.markdown("### 🎟️ AJUSTAR CANTIDAD DE NÚMEROS")

        c_restar, c_num, c_sumar = st.columns([1, 2, 1])
        with c_restar:
            if st.button("➖ Restar", use_container_width=True, key="btn_minus"):
                if st.session_state["cant_boletos"] > minimo:
                    st.session_state["cant_boletos"] -= 1
                    st.rerun()

        with c_num:
            st.markdown(
                f"""
                <div class="counter-display">
                    {st.session_state['cant_boletos']}
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c_sumar:
            if st.button("➕ Sumar", use_container_width=True, key="btn_plus"):
                st.session_state["cant_boletos"] += 1
                st.rerun()

        st.markdown(
            f"""
            <p style="text-align: center; color: #facc15; font-size: 0.85rem; font-weight: bold; margin-top: 8px;">
                Compra mínima: {minimo} números
            </p>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="info-box-blue">
                ℹ️ Los números se <strong>asignarán automáticamente al azar</strong> tras validar tu pago.
                ¡Mayor cantidad = más oportunidades de ganar!
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### 👤 Datos del Participante")
        col_nom, col_tel = st.columns(2)
        with col_nom:
            nombre_cliente = st.text_input(
                "Nombre Completo *",
                placeholder="Ej: Juan Pérez",
                value=st.session_state.get("nombre_cliente", ""),
            )
        with col_tel:
            telefono_cliente = st.text_input(
                "Teléfono (WhatsApp) *",
                placeholder="+1 809-555-5555",
                value=st.session_state.get("telefono_cliente", ""),
            )

        st.session_state["nombre_cliente"] = nombre_cliente
        st.session_state["telefono_cliente"] = telefono_cliente

        st.markdown("### 💳 Método de Pago *")
        banco_sel = st.session_state.get("banco_pago", "Banreservas")
        col_b1, col_b2 = st.columns(2)

        with col_b1:
            if st.button(
                "🏦 RESERVAS (AHORRO) 🟣",
                use_container_width=True,
                type="primary" if banco_sel == "Banreservas" else "secondary",
            ):
                st.session_state["banco_pago"] = "Banreservas"
                st.rerun()

        with col_b2:
            if st.button(
                "🏦 POPULAR (AHORRO) 🔵",
                use_container_width=True,
                type="primary" if banco_sel == "Banco Popular" else "secondary",
            ):
                st.session_state["banco_pago"] = "Banco Popular"
                st.rerun()

        if banco_sel == "Banreservas":
            titular = "ARGENIS MARTINEZ C."
            cuenta = "9606561652"
        else:
            titular = "ARGENIS MARTINEZ"
            cuenta = "821794971"

        st.markdown(
            f"""
            <div style="background: #090d16; border: 1px solid #1e3a8a; border-radius: 12px; padding: 20px; margin: 15px 0;">
                <h4 style="color: #ffffff; margin: 0;">🏦 {banco_sel.upper()} (AHORRO)</h4>
                <p style="color: #94a3b8; font-size: 0.85rem; margin: 10px 0 2px 0;">Número de cuenta:</p>
                <h2 style="color: #38bdf8; margin: 0; font-family: monospace;">{cuenta}</h2>
                <p style="color: #94a3b8; font-size: 0.85rem; margin: 10px 0 0 0;">Titular: <strong style="color: #ffffff;">{titular}</strong></p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        html_copiar_cuenta = f"""
        <button onclick="navigator.clipboard.writeText('{cuenta}').then(() => {{
            this.innerText='✅ ¡CUENTA COPIADA!';
            this.style.background='#22c55e';
        }})" 
        style="width:100%; padding:10px; border:0; border-radius:8px; 
               background:#f59e0b; color:#000; font-weight:800; cursor:pointer; font-size: 0.9rem; margin-bottom: 15px;">
            📋 COPIAR NÚMERO DE CUENTA ({cuenta})
        </button>
        """
        components.html(html_copiar_cuenta, height=45)

        st.markdown("### 📤 Comprobante de Pago *")
        comprobante_file = st.file_uploader(
            "Subir captura del comprobante",
            type=["png", "jpg", "jpeg"],
            key="comp_p2",
        )

        total_pagar = st.session_state["cant_boletos"] * precio

        st.markdown("---")
        c_tot, c_btn = st.columns([1, 1])
        with c_tot:
            st.markdown("<p style='color: #94a3b8; margin: 0;'>TOTAL A PAGAR</p>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='color: #38bdf8; margin: 0;'>RD$ {total_pagar:,.2f}</h2>", unsafe_allow_html=True)

        with c_btn:
            confirmar = st.button("CONFIRMAR COMPRA ✅", use_container_width=True, type="primary")

        if confirmar:
            if not nombre_cliente.strip() or not telefono_cliente.strip():
                st.error("Por favor completa tu Nombre y Teléfono.")
            elif not comprobante_file:
                st.error("Por favor sube la foto del comprobante.")
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
                    st.error("No quedan suficientes números disponibles.")
                    conn.close()
                else:
                    asignados = random.sample(disp, cant_boletos)
                    os.makedirs("comprobantes", exist_ok=True)

                    ext = os.path.splitext(comprobante_file.name)[1].lower()
                    if ext not in [".png", ".jpg", ".jpeg"]:
                        ext = ".png"

                    path_comp = f"comprobantes/{telefono_cliente}_{datetime.datetime.now().timestamp()}{ext}"

                    imagen_comp = Image.open(comprobante_file)
                    if imagen_comp.mode in ("RGBA", "LA", "P"):
                        imagen_comp = imagen_comp.convert("RGB")
                    imagen_comp.save(path_comp)

                    ahora = datetime.datetime.now()
                    num_list = []

                    for b_id, b_num in asignados:
                        num_list.append(b_num)
                        c.execute(
                            """
                            UPDATE boletos
                            SET estado = 'reservado', usuario_nombre = ?, usuario_telefono = ?,
                                metodo_pago = ?, comprobante = ?, fecha_reserva = ?
                            WHERE id = ?
                            """,
                            (
                                nombre_cliente.strip(),
                                telefono_cliente.strip(),
                                banco_sel,
                                path_comp,
                                ahora,
                                b_id,
                            ),
                        )

                    conn.commit()
                    conn.close()

                    st.session_state["boletos_asignados_resumen"] = num_list
                    st.session_state["paso_compra"] = 3
                    st.rerun()

    # ---------------------------------------------------------
    # PASO 3: EXCLUSIVAMENTE PANTALLA FINAL DE ASIGNACIÓN
    # ---------------------------------------------------------
    elif paso == 3:
        c_top1, c_top2 = st.columns([4, 1])
        with c_top1:
            st.markdown("## 🎉 ¡Boletos Reservados Exitosamente!")
        with c_top2:
            if st.button("❌ Cerrar [X]"):
                st.session_state["paso_compra"] = 0
                st.rerun()

        st.success("Tus datos y comprobante han sido recibidos.")
        st.info("🕒 Tus números serán validados en un plazo máximo de 24 horas.")

        boletos = st.session_state.get("boletos_asignados_resumen", [])

        st.markdown("### 🎟️ Tus Números Asignados:")

        cols = st.columns(5)
        for i, n in enumerate(boletos):
            with cols[i % 5]:
                st.markdown(
                    f"""
                    <div class="ticket-card">
                        <div style="font-size: 1.5rem; font-weight: bold; color: #38bdf8;">{n}</div>
                        <div class="badge-pending">PENDIENTE A CONFIRMAR</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown("<br>", unsafe_allow_html=True)
        string_boletos = ", ".join(boletos)

        # Botón para Copiar Boletos
        html_copiar_boletos = f"""
        <button onclick="navigator.clipboard.writeText('{string_boletos}').then(() => {{
            this.innerText='✅ ¡BOLETOS COPIADOS AL PORTAPAPELES!';
            this.style.background='#22c55e';
        }})" 
        style="width:100%; padding:14px; border:0; border-radius:10px; 
               background:#38bdf8; color:#000; font-weight:800; cursor:pointer; font-size: 1rem;">
            📋 COPIAR NÚMERO(S) ({len(boletos)})
        </button>
        """
        components.html(html_copiar_boletos, height=55)

        if st.button("ENTIENDO Y CERRAR ✅", use_container_width=True, type="primary"):
            st.session_state["paso_compra"] = 0
            st.rerun()


# ---------------------------------------------------------
# SECCIÓN: VERIFICADOR DE BOLETOS
# ---------------------------------------------------------
elif seccion == "🔎 Verificador de boletos":
    st.header("🔎 Verificador de Boletos")
    tel_buscar = st.text_input("Ingresa tu número de WhatsApp registrado:")

    if st.button("Buscar Mis Boletos"):
        if tel_buscar:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute(
                "SELECT b.numero, b.estado, r.nombre FROM boletos b JOIN rifas r ON b.rifa_id = r.id WHERE b.usuario_telefono = ?",
                (tel_buscar,),
            )
            mis_boletos = c.fetchall()
            conn.close()

            if mis_boletos:
                st.success(f"Se encontraron {len(mis_boletos)} boletos para tu número:")
                
                cols = st.columns(4)
                for idx, (num, est, rifa_nom) in enumerate(mis_boletos):
                    with cols[idx % 4]:
                        if est == "confirmado":
                            badge_html = '<div class="badge-approved">APROBADO</div>'
                        else:
                            badge_html = '<div class="badge-pending">PENDIENTE A CONFIRMAR</div>'

                        st.markdown(
                            f"""
                            <div class="ticket-card">
                                <div style="font-size: 0.8rem; color: #94a3b8;">{rifa_nom}</div>
                                <div style="font-size: 1.6rem; font-weight: bold; color: #ffffff; margin: 4px 0;">{num}</div>
                                {badge_html}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
            else:
                st.info("No se encontraron registros activos para ese número.")


# ---------------------------------------------------------
# OTRAS SECCIONES
# ---------------------------------------------------------
elif seccion == "❓ Cómo jugar":
    st.header("❓ Cómo Participar")
    st.markdown(
        "1. Selecciona tu premio.\n2. Compra tus boletos.\n3. Transfiere por banco.\n4. Sube la foto del comprobante.\n5. Verifica tus números."
    )

elif seccion == "🤖 Soporte IA":
    abrir_soporte_ia()

elif seccion == "🏆 Ganadores":
    st.header("🏆 Ganadores Anteriores")
    st.info("Próximamente publicaremos aquí los ganadores oficiales.")

elif seccion == "⚙️ Administración":
    st.header("⚙️ Administración")
    pass_admin = st.text_input("Contraseña", type="password")

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
