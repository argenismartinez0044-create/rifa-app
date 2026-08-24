import datetime
import os
import random
import sqlite3
from PIL import Image
import streamlit as st

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
# ESTILOS Y NAVEGACIÓN
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    .stApp { background: linear-gradient(135deg, #0b0d17 0%, #171b2e 50%, #080910 100%) !important; color: #FFFFFF; }
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
           # PASO 2: Banco, imágenes y número de cuenta
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
                img_banco = "banreservas.png" if os.path.exists("banreservas.png") else ("barreserva.png" if os.path.exists("barreserva.png") else None)
            else:
                titular = "ARGENIS MARTINEZ"
                cuenta = "821794971"
                img_banco = "popular.png" if os.path.exists("popular.png") else None

            st.markdown(
                f"""
                <div style="background: rgba(255,255,255,0.08); border-radius: 12px;
                            padding: 18px; margin-top: 10px; margin-bottom: 10px;">
                    <h4>🏦 {banco_pago}</h4>
                    <p>Tipo: <strong>Ahorros</strong></p>
                    <p>Titular: <strong>{titular}</strong></p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.caption("📋 Haz clic en el icono a la derecha del número para copiar:")
            st.code(cuenta, language=None)

            if img_banco and os.path.exists(img_banco):
                st.image(img_banco, width=200)

            total_pagar = st.session_state["cant_boletos"] * precio
            st.markdown(f"### 💰 Total a pagar: **RD$ {total_pagar:.2f}**")
            st.info("Realiza el depósito y luego sube la foto del volante/comprobante.")

            col1, col2 = st.columns(2)
            with col1:
                if st.button(
                    "⬅️ VOLVER A DATOS Y COMBOS",
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

            def seleccionar_rifa(rifa_id, nombre, precio, minimo):
                st.session_state["rifa_seleccionada"] = rifa_id
                st.session_state["nombre_rifa"] = nombre
                st.session_state["precio_rifa"] = precio
                st.session_state["min_rifa"] = minimo
                st.session_state["paso_compra"] = 1
                st.session_state["cant_boletos"] = minimo

            st.button(
                label_btn,
                key=f"btn_jugar_{r_id}",
                on_click=seleccionar_rifa,
                args=(r_id, r_nombre, r_precio, r_min),
                use_container_width=True,
            )

    # ---------------------------------------------------------
    # FLUJO DE COMPRA PASO A PASO
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
                             padding: 4px 12px; border-radius: 20px;">Rifa seleccionada</span>
                <h2 style="color: #FFFFFF; margin: 10px 0;">🎉 {nombre} 🎉</h2>
                <p style="color: #E0E0E0; margin: 0;">
                    Precio por boleto:
                    <strong style="color: #F5C518;">RD$ {precio:.2f}</strong>
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # PASO 1: Datos del participante + Selección interactiva de combos
        if paso == 1:
            st.subheader("📝 1. Completa tus datos y selecciona tu combo")

            if "cant_boletos" not in st.session_state:
                st.session_state["cant_boletos"] = minimo

            st.markdown("### 💥 SELECCIÓN DE COMBOS DE BOLETOS")
            st.caption("Haz clic en un combo para seleccionarlo:")

            combos_def = [
                ("🟢 COMBO BÁSICO", minimo),
                ("🔵 COMBO DOBLE", minimo * 2),
                ("🟣 COMBO INTERMEDIO", minimo * 3),
                ("🟠 COMBO PROFESIONAL", minimo * 5),
                ("🔴 COMBO PRO VIP", minimo * 10),
            ]

            c_cols = st.columns(len(combos_def))
            for i, (nombre_combo, cant_combo) in enumerate(combos_def):
                cant_combo = min(100, cant_combo)
                costo_combo = cant_combo * precio
                with c_cols[i]:
                    st.markdown(
                        f"""
                        <div style="background: rgba(255,255,255,0.05); padding: 10px; border-radius: 8px; text-align: center; margin-bottom: 8px;">
                            <strong>{nombre_combo}</strong><br/>
                            <span style="color: #F5C518;">🎟️ {cant_combo} boletos</span><br/>
                            <small>RD$ {costo_combo:.2f}</small>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    if st.button(f"Seleccionar", key=f"btn_set_combo_{i}", use_container_width=True):
                        st.session_state["cant_boletos"] = cant_combo
                        st.rerun()

            st.markdown("---")

            with st.form("form_datos_cliente"):
                nombre_cliente = st.text_input(
                    "Nombre Completo",
                    value=st.session_state.get("nombre_cliente", ""),
                )
                telefono_cliente = st.text_input(
                    "Teléfono / WhatsApp (Ej: 8091234567)",
                    value=st.session_state.get("telefono_cliente", ""),
                )

                cant_boletos_input = st.number_input(
                    "✏️ Boletos seleccionados (puedes ajustar el número manualmente):",
                    min_value=minimo,
                    max_value=100,
                    value=int(st.session_state["cant_boletos"]),
                    step=1,
                )

                total_pagar = cant_boletos_input * precio
                st.markdown(
                    f"### 💰 Total a pagar: **{int(cant_boletos_input)} boletos** × RD$ {precio:.2f} = **RD$ {total_pagar:.2f}**"
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
                    st.session_state["cant_boletos"] = int(cant_boletos_input)
                    st.session_state["paso_compra"] = 2
                    st.rerun()

        # PASO 2: Banco, imágenes y número de cuenta
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
                img_banco = "banreservas.png" if os.path.exists("banreservas.png") else ("barreserva.png" if os.path.exists("barreserva.png") else None)
            else:
                titular = "ARGENIS MARTINEZ"
                cuenta = "821794971"
                img_banco = "popular.png" if os.path.exists("popular.png") else None

            st.markdown(
                f"""
                <div style="background: rgba(255,255,255,0.08); border-radius: 12px;
                            padding: 18px; margin-top: 10px;">
                    <h4>🏦 {banco_pago}</h4>
                    <p>Tipo: <strong>Ahorros</strong></p>
                    <p>Titular: <strong>{titular}</strong></p>
                    <p>Número de cuenta:</p>
                    <div style="font-size: 1.6rem; font-weight: 800;
                                letter-spacing: 2px;">{cuenta}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if img_banco and os.path.exists(img_banco):
                st.image(img_banco, width=200)

            st.markdown(
                f"""
                <button onclick="navigator.clipboard.writeText('{cuenta}').then(
                    () => this.innerText='✅ CUENTA COPIADA'
                )"
                style="width:100%; padding:12px; margin-top:10px; border:0;
                       border-radius:8px; background:#F5C518; color:#000;
                       font-weight:800; cursor:pointer;">
                    📋 COPIAR NÚMERO DE CUENTA
                </button>
                """,
                unsafe_allow_html=True,
            )

            total_pagar = st.session_state["cant_boletos"] * precio
            st.markdown(f"### 💰 Total a pagar: **RD$ {total_pagar:.2f}**")
            st.info("Realiza el depósito y luego sube la foto del volante/comprobante.")

            col1, col2 = st.columns(2)
            with col1:
                if st.button(
                    "⬅️ VOLVER A DATOS Y COMBOS",
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

            st.info(
                f"Banco seleccionado: **{st.session_state['banco_pago']}** · "
                f"Total a pagar: **RD$ {st.session_state['cant_boletos'] * precio:.2f}**"
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
                    st.error("Debes subir la imagen del volante/comprobante antes de continuar.")
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
                                    st.session_state["banco_pago"],
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

                        st.subheader("🎟️ Tus Números Asignados (Pendientes de Validación):")
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
