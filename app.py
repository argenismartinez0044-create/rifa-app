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
                "content": "¡Hola! Soy tu asistente de **Rifas Luxury** 🎲.\n\n¿En qué te puedo ayudar hoy? (Comprar boletos, datos de banco, verificar tus números...)",
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
                "2. Elige tus boletos y realiza la transferencia.\n"
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
        elif any(w in txt for w in ["precio", "costo", "minimo", "mínimo"]):
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

    # Actualizaciones explícitas para asegurar los valores correctos
    c.execute("UPDATE rifas SET min_boletos = 15 WHERE id = 1")
    c.execute("UPDATE rifas SET min_boletos = 10 WHERE id = 2")
    c.execute(
        "UPDATE rifas SET nombre = '5 iPhone 17 Pro Max' WHERE id = 2"
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
# ESTILOS Y BOTÓN FLOTANTE ROBOT 🤖
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
# Botón visible tipo robot flotante
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

    st.markdown("---")

    with st.expander("📺 **¿CÓMO PARTICIPAR?** — 5 pasos simples"):
        st.write(
            "1. Selecciona un premio del catálogo.\n"
            "2. Elige la cantidad de boletos que deseas comprar.\n"
            "3. Haz la transferencia a Banreservas o Banco Popular.\n"
            "4. Sube la captura de tu comprobante de pago.\n"
            "5. Consulta tus números en el **Verificador de Boletos**."
        )

    st.markdown("---")
    st.subheader("🛍️ CATÁLOGO DE RIFAS")

    cat_filtro = st.radio(
        "Categoría:",
        ["TODOS", "Juego", "TELÉFONO", "DINERO", "VEHÍCULOS"],
        horizontal=True,
    )

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if cat_filtro == "TODOS":
        c.execute("SELECT * FROM rifas")
    else:
        c.execute("SELECT * FROM rifas WHERE categoria = ?", (cat_filtro,))
    rifas = c.fetchall()
    conn.close()

    cols = st.columns(2)
    for idx, r in enumerate(rifas):
        r_id, r_nombre, r_cat, r_precio, r_min, r_total, r_img, r_fecha = r

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute(
            "SELECT COUNT(*) FROM boletos WHERE rifa_id = ? AND estado IN ('reservado', 'confirmado')",
            (r_id,),
        )
        vendidos = c.fetchone()[0]
        conn.close()

        progreso = int((vendidos / r_total) * 100) if r_total > 0 else 0

        with cols[idx % 2]:
            st.markdown(f"### 🏷️ {r_nombre}")
            st.caption(f"Categoría: **{r_cat}**")
            if os.path.exists(r_img):
                st.image(r_img, use_container_width=True)

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

            if st.button(label_btn, key=f"btn_jugar_{r_id}"):
                st.session_state["rifa_seleccionada"] = r_id
                st.session_state["nombre_rifa"] = r_nombre
                st.session_state["precio_rifa"] = r_precio
                st.session_state["min_rifa"] = r_min

    if "rifa_seleccionada" in st.session_state:
        st.markdown("---")
        nombre = st.session_state["nombre_rifa"]
        precio = st.session_state["precio_rifa"]

        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%); border-radius: 16px; padding: 20px; text-align: center;">
                <span style="background-color: #F5C518; color: #000; font-weight: 800; padding: 4px 12px; border-radius: 20px;">Participando por</span>
                <h2 style="color: #FFFFFF; margin: 10px 0;">🎉 {nombre} 🎉</h2>
                <p style="color: #E0E0E0; margin: 0;">Precio por boleto: <strong style="color: #F5C518;">RD$ {precio:.2f}</strong></p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.subheader("💳 Cuentas Bancarias para Transferir")
        tab_banres, tab_pop = st.tabs(["Banreservas", "Banco Popular"])
        with tab_banres:
            st.write("**Banreservas (Ahorros):** ARGENIS MARTINEZ C.")
            st.code("9606561652", language="text")
        with tab_pop:
            st.write("**Banco Popular (Ahorros):** ARGENIS MARTINEZ")
            st.code("821794971", language="text")

        st.markdown("---")
        st.subheader("📝 Registrar Boletos")

        with st.form("form_compra"):
            nombre_cliente = st.text_input("Nombre Completo")
            telefono_cliente = st.text_input(
                "Teléfono / WhatsApp (Ej: 8091234567)"
            )
            cant_boletos = st.number_input(
                "Cantidad de boletos",
                min_value=int(st.session_state["min_rifa"]),
                max_value=100,
                value=int(st.session_state["min_rifa"]),
            )
            banco_pago = st.selectbox(
                "Banco donde transferiste", ["Banreservas", "Banco Popular"]
            )
            comprobante_file = st.file_uploader(
                "Subir foto del comprobante", type=["png", "jpg", "jpeg"]
            )

            total_pagar = cant_boletos * st.session_state["precio_rifa"]
            st.markdown(f"### Total a pagar: **RD$ {total_pagar:.2f}**")

            btn_confirmar = st.form_submit_button("✅ RESERVAR MIS BOLETOS")

        if btn_confirmar:
            if not nombre_cliente or not telefono_cliente or not comprobante_file:
                st.error("Por favor completa todos los campos.")
            else:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute(
                    "SELECT id, numero FROM boletos WHERE rifa_id = ? AND estado = 'disponible'",
                    (st.session_state["rifa_seleccionada"],),
                )
                disp = c.fetchall()

                if len(disp) < cant_boletos:
                    st.error("No hay suficientes boletos disponibles.")
                    conn.close()
                else:
                    asignados = random.sample(disp, cant_boletos)
                    os.makedirs("comprobantes", exist_ok=True)
                    path_comp = f"comprobantes/{telefono_cliente}_{datetime.datetime.now().timestamp()}.png"
                    Image.open(comprobante_file).save(path_comp)

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
                                nombre_cliente,
                                telefono_cliente,
                                banco_pago,
                                path_comp,
                                ahora,
                                b_id,
                            ),
                        )
                    conn.commit()
                    conn.close()

               st.success("🎉 ¡Boletos asignados temporalmente!")
st.info(...)

st.subheader("🎟️ Tus Números Asignados (Pendientes de Validación):")
cols_num = st.columns(min(len(num_asignados), 5))
for i, n in enumerate(num_asignados):
    cols_num[i % 5].metric("Boleto", n, delta="Pendiente", delta_color="off")

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
