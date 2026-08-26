import datetime
import os
import random
import sqlite3
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image

DB_FILE = "rifas_v4.db"
WHATSAPP_NUMERO = "8294835217"

st.set_page_config(page_title="Rifas Sirio RD", page_icon="🎲", layout="wide")


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
# INICIALIZACIÓN DE BASE DE DATOS
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
# ESTILOS PROFESIONALES (TEMA OSCURO FUTURISTA - NEÓN)
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    .stApp { background: linear-gradient(135deg, #070913 0%, #0c1021 50%, #05060b 100%) !important; color: #FFFFFF; }
    
    /* Modales y Tarjetas */
    .modal-card {
        background: rgba(15, 23, 42, 0.75);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 24px;
        backdrop-filter: blur(10px);
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
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
    
    /* Botón Bancos Activo */
    .bank-card-active {
        border: 2px solid #00d2ff !important;
        box-shadow: 0 0 15px rgba(0, 210, 255, 0.4) !important;
        background: rgba(0, 210, 255, 0.1) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

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
# SECCIÓN: INICIO Y CATÁLOGO
# ---------------------------------------------------------
if seccion == "🏠 Inicio & Catálogo":
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

    # Cargar rifas de la base de datos
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

            def seleccionar_rifa(rifa_id=r_id, nombre=r_nombre, precio=r_precio, minimo=r_min):
                st.session_state["rifa_seleccionada"] = rifa_id
                st.session_state["nombre_rifa"] = nombre
                st.session_state["precio_rifa"] = precio
                st.session_state["min_rifa"] = minimo
                st.session_state["paso_compra"] = 1
                st.session_state["cant_boletos"] = minimo
                st.session_state["banco_pago"] = "Banreservas"

            st.button(
                label_btn,
                key=f"btn_jugar_{r_id}",
                on_click=seleccionar_rifa,
                use_container_width=True,
            )
    conn.close()

    # ---------------------------------------------------------
    # FLUJO DE COMPRA INTEGRADO Y PROFESIONAL
    # ---------------------------------------------------------
    if "rifa_seleccionada" in st.session_state:
        st.markdown("---")

        nombre = st.session_state["nombre_rifa"]
        precio = st.session_state["precio_rifa"]
        minimo = int(st.session_state["min_rifa"])
        paso = st.session_state.get("paso_compra", 1)

        # Encabezado Tipo Modal Flash
        st.markdown(
            f"""
            <div style="background: linear-gradient(90deg, #0b1120 0%, #111c35 100%);
                        border: 1px solid #1e293b; border-radius: 12px; padding: 15px; text-align: center; margin-bottom: 20px;">
                <h3 style="color: #38bdf8; margin: 0; font-size: 1.5rem;">{nombre.upper()} POR {int(precio)} PESITOS FLASH</h3>
                <p style="color: #94a3b8; margin: 5px 0 0 0; font-size: 0.9rem;">Elige tu paquete de números o personaliza tu compra</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ---------------------------------------------------------
        # PASO 1: SELECCIÓN DE COMBOS (ESTILO TARJETAS ILUMINADAS)
        # ---------------------------------------------------------
        if paso == 1:
            st.markdown("<h4 style='text-align: center; color: #f8fafc;'>Selecciona un paquete o elige cantidad personalizada</h4>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #64748b; font-size: 0.85rem;'>A mayor cantidad, más oportunidades de ganar</p>", unsafe_allow_html=True)

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
                    if st.button("Seleccionar", key=f"btn_ combo_{i}", use_container_width=True):
                        st.session_state["cant_boletos"] = cant_c
                        st.session_state["paso_compra"] = 2
                        st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("⚙️ ELEGIR CANTIDAD PERSONALIZADA", key="btn_custom_qty", use_container_width=True):
                st.session_state["cant_boletos"] = minimo
                st.session_state["paso_compra"] = 2
                st.rerun()

            st.markdown(f"<p style='text-align: center; color: #64748b; font-size: 0.8rem;'>Mínimo {minimo} números</p>", unsafe_allow_html=True)

        # ---------------------------------------------------------
        # PASO 2: FORMULARIO COMPLETO Y MÉTODOS DE PAGO
        # ---------------------------------------------------------
        elif paso == 2:
            if st.button("⬅️ Cambiar Paquete / Volver"):
                st.session_state["paso_compra"] = 1
                st.rerun()

            st.markdown("### 🎟️ CANTIDAD DE NÚMEROS")

            # Selector Incremental (- / +)
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

            # Cuadro Informativo de Asignación Automática
            st.markdown(
                f"""
                <div class="info-box-blue">
                    ℹ️ Los números se <strong>asignarán automáticamente al azar</strong> tras validar tu pago.
                    ¡Mayor cantidad = más oportunidades de ganar!
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Formulario de Datos Personales
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

            # Selección de Banco como Botones de Imagen Integrados
            st.markdown("### 💳 Método de Pago *")
            
            col_b1, col_b2 = st.columns(2)
            
            banco_sel = st.session_state.get("banco_pago", "Banreservas")

            with col_b1:
                b_banres = st.button(
                    "🏦 RESERVAS (AHORRO) 🟣",
                    use_container_width=True,
                    type="primary" if banco_sel == "Banreservas" else "secondary",
                )
                if b_banres:
                    st.session_state["banco_pago"] = "Banreservas"
                    st.rerun()

            with col_b2:
                b_pop = st.button(
                    "🏦 POPULAR (AHORRO) 🔵",
                    use_container_width=True,
                    type="primary" if banco_sel == "Banco Popular" else "secondary",
                )
                if b_pop:
                    st.session_state["banco_pago"] = "Banco Popular"
                    st.rerun()

            # Datos del Banco Seleccionado (Como en la Imagen 5)
            if banco_sel == "Banreservas":
                titular = "ARGENIS MARTINEZ C."
                cuenta = "9606561652"
            else:
                titular = "ARGENIS MARTINEZ"
                cuenta = "821794971"

            st.markdown(
                f"""
                <div style="background: #090d16; border: 1px solid #1e3a8a; border-radius: 12px; padding: 20px; margin: 15px 0;">
                    <div style="display: flex; align-items: center; justify-content: space-between;">
                        <div>
                            <h4 style="color: #ffffff; margin: 0;">🏦 {banco_sel.upper()} (AHORRO)</h4>
                            <p style="color: #94a3b8; font-size: 0.85rem; margin: 10px 0 2px 0;">Número de cuenta:</p>
                            <h2 style="color: #38bdf8; margin: 0; font-family: monospace;">{cuenta}</h2>
                            <p style="color: #94a3b8; font-size: 0.85rem; margin: 10px 0 0 0;">Titular: <strong style="color: #ffffff;">{titular}</strong></p>
                        </div>
                    </div>
                    <p style="color: #60a5fa; font-size: 0.8rem; margin-top: 15px;">
                        ℹ️ Realiza la transferencia y sube el comprobante abajo para validar tu compra.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Botón copiar interactivo de 1 Clic
            html_copiar = f"""
            <button onclick="navigator.clipboard.writeText('{cuenta}').then(() => {{
                this.innerText='✅ ¡NÚMERO DE CUENTA COPIADO!';
                this.style.background='#22c55e';
            }})" 
            style="width:100%; padding:10px; border:0; border-radius:8px; 
                   background:#f59e0b; color:#000; font-weight:800; cursor:pointer; font-size: 0.9rem; margin-bottom: 15px;">
                📋 COPIAR NÚMERO DE CUENTA ({cuenta})
            </button>
            """
            components.html(html_copiar, height=45)

            # Subida de Comprobante
            st.markdown("### 📤 Comprobante de Pago *")
            comprobante_file = st.file_uploader(
                "Haz clic para subir tu comprobante (JPG, PNG)",
                type=["png", "jpg", "jpeg"],
                key="comprobante_file_p2",
            )

            total_pagar = st.session_state["cant_boletos"] * precio

            # Barra Inferior de Pago y Confirmación
            st.markdown("---")
            c_tot, c_btn = st.columns([1, 1])

            with c_tot:
                st.markdown("<p style='color: #94a3b8; margin: 0; font-size: 0.85rem;'>TOTAL A PAGAR</p>", unsafe_allow_html=True)
                st.markdown(f"<h2 style='color: #38bdf8; margin: 0;'>RD$ {total_pagar:,.2f}</h2>", unsafe_allow_html=True)

            with c_btn:
                confirmar = st.button("CONFIRMAR COMPRA ✅", use_container_width=True, type="primary")

            if confirmar:
                if not nombre_cliente.strip() or not telefono_cliente.strip():
                    st.error("Por favor completa tu Nombre y Teléfono antes de continuar.")
                elif not comprobante_file:
                    st.error("Debes adjuntar la foto del comprobante de transferencia.")
                else:
                    # Lógica de asignación e inserción en DB
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

                        ext = os.path.splitext(comprobante_file.name)[1].lower()
                        if ext not in [".png", ".jpg", ".jpeg"]:
                            ext = ".png"

                        path_comp = f"comprobantes/{telefono_cliente}_{datetime.datetime.now().timestamp()}{ext}"

                        imagen_comp = Image.open(comprobante_file)
                        if imagen_comp.mode in ("RGBA", "LA", "P"):
                            imagen_comp = imagen_comp.convert("RGB")
                        imagen_comp.save(path_comp)

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

                        st.success("🎉 ¡Tu compra ha sido registrada con éxito!")
                        st.info("Tus números han sido asignados temporalmente mientras validamos el comprobante.")

                        st.markdown("### 🎟️ Tus Números Asignados:")
                        cols_num = st.columns(min(len(num_asignados), 5))
                        for i, n in enumerate(num_asignados):
                            cols_num[i % 5].metric("Boleto", n)

                        # Limpiar Estado
                        st.session_state.pop("rifa_seleccionada", None)
                        st.session_state.pop("paso_compra", None)

# ---------------------------------------------------------
# SECCIÓN: VERIFICADOR
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
                st.success(f"Se encontraron {len(mis_boletos)} boletos asociados a tu número:")
                for num, est, rifa_nom in mis_boletos:
                    c1, c2, c3 = st.columns(3)
                    c1.write(f"🎟️ **Boleto:** `{num}`")
                    c2.write(f"🏆 **Rifa:** {rifa_nom}")

                    if est == "reservado":
                        c3.markdown("📌 **Estado:** ⏳ *PENDIENTE (En revisión max 24h)*")
                    elif est == "confirmado":
                        c3.markdown("📌 **Estado:** ✅ *CONFIRMADO Y VÁLIDO*")
                    else:
                        c3.markdown(f"📌 **Estado:** `{est.upper()}`")

                    st.markdown("---")
            else:
                st.info("No se encontraron registros con este número.")

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
