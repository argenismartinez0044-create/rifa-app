import datetime
import hashlib
import os
import random
import sqlite3
import requests
import streamlit as st
from PIL import Image

# ---------------------------------------------------------
# CONFIGURACIÓN INICIAL DE PÁGINA
# ---------------------------------------------------------
st.set_page_config(
    page_title="Rifas Sirio RD",
    page_icon="🎲",
    layout="wide",
    initial_sidebar_state="collapsed",
)

DB_FILE = "rifas_v4.db"
WHATSAPP_NUMERO = "8294835217"
ADMIN_PASSWORD = "admin"  # 🔑 Cambia esta contraseña

# Configuración de Telegram (Opcional)
TELEGRAM_BOT_TOKEN = "TU_BOT_TOKEN_AQUI"
TELEGRAM_CHAT_ID = "TU_CHAT_ID_AQUI"

# ---------------------------------------------------------
# FUNCIONES AUXILIARES
# ---------------------------------------------------------
def calcular_hash_imagen(file_bytes):
    """Genera una huella digital única SHA-256 para evitar duplicados de comprobantes"""
    return hashlib.sha256(file_bytes).hexdigest()

def enviar_notificacion_telegram(mensaje, ruta_imagen=None):
    if TELEGRAM_BOT_TOKEN == "TU_BOT_TOKEN_AQUI":
        return
    try:
        url_msg = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url_msg, data={"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "Markdown"})
        
        if ruta_imagen and os.path.exists(ruta_imagen):
            url_photo = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
            with open(ruta_imagen, "rb") as foto:
                requests.post(url_photo, data={"chat_id": TELEGRAM_CHAT_ID}, files={"photo": foto})
    except Exception as e:
        print(f"Error en Telegram: {e}")

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
            metodo_pago TEXT, comprobante TEXT, hash_comprobante TEXT, fecha_reserva DATETIME
        )
        """
    )
    
    # Migración de columna hash
    try:
        c.execute("ALTER TABLE boletos ADD COLUMN hash_comprobante TEXT")
    except sqlite3.OperationalError:
        pass

    c.execute("SELECT COUNT(*) FROM rifas")
    if c.fetchone()[0] == 0:
        c.execute(
            "INSERT INTO rifas (nombre, categoria, precio_boleto, min_boletos, total_boletos, imagen, fecha) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("PlayStation 5 Pro", "Juego", 5.0, 15, 100000, "play.jpg", "Fecha pendiente"),
        )
        c.execute(
            "INSERT INTO rifas (nombre, categoria, precio_boleto, min_boletos, total_boletos, imagen, fecha) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("5 iPhone 17 Pro Max", "TELÉFONO", 15.0, 10, 100000, "iphone.jpg", "Al vender el 80%"),
        )
        for rifa_id in [1, 2]:
            numeros = [(rifa_id, f"{i:05d}") for i in range(1, 100001)]
            c.executemany("INSERT INTO boletos (rifa_id, numero) VALUES (?, ?)", numeros)
        conn.commit()
    conn.close()

init_db()

# ---------------------------------------------------------
# ESTADOS GLOBAL DE LA APP
# ---------------------------------------------------------
if "tema_claro" not in st.session_state:
    st.session_state["tema_claro"] = False
if "vista_actual" not in st.session_state:
    st.session_state["vista_actual"] = "rifas"
if "paso_compra" not in st.session_state:
    st.session_state["paso_compra"] = 0
if "cant_boletos" not in st.session_state:
    st.session_state["cant_boletos"] = 15
if "banco_pago" not in st.session_state:
    st.session_state["banco_pago"] = "Banreservas"
if "admin_logueado" not in st.session_state:
    st.session_state["admin_logueado"] = False

# ---------------------------------------------------------
# ESTILOS CSS
# ---------------------------------------------------------
bg_color = "#f8fafc" if st.session_state["tema_claro"] else "linear-gradient(135deg, #070913 0%, #0c1021 50%, #05060b 100%)"
text_color = "#0f172a" if st.session_state["tema_claro"] else "#FFFFFF"
card_bg = "#ffffff" if st.session_state["tema_claro"] else "rgba(15, 23, 42, 0.85)"
card_border = "#e2e8f0" if st.session_state["tema_claro"] else "#1e293b"

st.markdown(
    f"""
    <style>
    .stApp {{ background: {bg_color} !important; color: {text_color}; }}
    .ticket-card {{ background: {card_bg}; border: 1px solid {card_border}; border-radius: 12px; padding: 15px; text-align: center; margin-bottom: 12px; }}
    .badge-pending {{ display: inline-block; background: #b45309; color: #ffffff; font-weight: bold; font-size: 0.75rem; padding: 4px 10px; border-radius: 20px; }}
    .badge-approved {{ display: inline-block; background: #15803d; color: #ffffff; font-weight: bold; font-size: 0.75rem; padding: 4px 10px; border-radius: 20px; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# NAVBAR SUPERIOR
# ---------------------------------------------------------
c_head1, c_head2, c_head3, c_head4, c_head5, c_head6 = st.columns([2.5, 1, 1, 0.6, 1.5, 1.2])

with c_head1:
    st.markdown("### 🎲 **RIFAS SIRIO RD**", unsafe_allow_html=True)
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
with c_head6:
    if st.button("⚙️ Admin", use_container_width=True):
        st.session_state["vista_actual"] = "admin"
        st.rerun()

st.markdown("---")

# ---------------------------------------------------------
# VISTA 1: CATÁLOGO Y PROCESO DE COMPRA DE RIFAS
# ---------------------------------------------------------
if st.session_state["vista_actual"] == "rifas":
    paso = st.session_state.get("paso_compra", 0)

    # PASO 0: LISTADO DE RIFAS DISPONIBLES
    if paso == 0:
        st.subheader("🎉 Rifas Activas")
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT id, nombre, categoria, precio_boleto, min_boletos, total_boletos, fecha FROM rifas")
        rifas = c.fetchall()
        conn.close()

        cols = st.columns(len(rifas) if rifas else 1)
        for idx, (r_id, nombre, cat, precio, min_b, tot_b, fecha) in enumerate(rifas):
            with cols[idx % len(cols)]:
                st.markdown(f"### {nombre}")
                st.write(f"🏷️ **Categoría:** {cat}")
                st.write(f"💵 **Precio boleto:** RD${precio:.2f}")
                st.write(f"📌 **Mínimo a comprar:** {min_b} boletos")
                st.write(f"📅 **Sorteo:** {fecha}")

                if st.button(f"Participar en {nombre}", key=f"rifa_{r_id}", type="primary", use_container_width=True):
                    st.session_state["rifa_seleccionada"] = r_id
                    st.session_state["nombre_rifa"] = nombre
                    st.session_state["precio_rifa"] = precio
                    st.session_state["min_rifa"] = min_b
                    st.session_state["cant_boletos"] = min_b
                    st.session_state["paso_compra"] = 1
                    st.rerun()

    # PASO 1: SELECCIÓN DE CANTIDAD DE BOLETOS
    elif paso == 1:
        st.button("⬅️ Volver a rifas", on_click=lambda: st.session_state.update({"paso_compra": 0}))
        st.title(f"🎰 {st.session_state['nombre_rifa']}")

        cant = st.number_input(
            "Cantidad de boletos a comprar:",
            min_value=st.session_state["min_rifa"],
            max_value=1000,
            value=st.session_state["cant_boletos"],
            step=1,
        )
        st.session_state["cant_boletos"] = cant
        total = cant * st.session_state["precio_rifa"]

        st.markdown(f"### **Total a pagar:** RD${total:.2f}")

        if st.button("CONTINUAR AL PAGO ➡️", type="primary", use_container_width=True):
            st.session_state["paso_compra"] = 2
            st.rerun()

    # PASO 2: DATOS, DATOS BANCARIOS Y CARGA DE COMPROBANTE CON SHA-256
    elif paso == 2:
        st.button("⬅️ Cambiar cantidad", on_click=lambda: st.session_state.update({"paso_compra": 1}))
        st.title("💳 Método de Pago y Registro")

        total = st.session_state["cant_boletos"] * st.session_state["precio_rifa"]
        st.info(f"Monto total: **RD${total:.2f}** por **{st.session_state['cant_boletos']} boletos**.")

        banco = st.selectbox("Selecciona tu banco para transferencia:", ["Banreservas", "Banco BHD", "Banco Popular"])
        st.session_state["banco_pago"] = banco

        st.markdown(
            f"""
            **Cuentas para Transferencia:**
            - **{banco}:** `960-XXXXXXX-X` a nombre de **Sirio Rifas RD**
            """
        )
        st.markdown("---")

        nombre_cliente = st.text_input("Nombre Completo *")
        telefono_cliente = st.text_input("Teléfono (WhatsApp) *")
        comprobante_file = st.file_uploader("Subir Comprobante de Pago *", type=["png", "jpg", "jpeg"])
        acepta_terminos = st.checkbox("Confirmo que mis datos y el comprobante ingresado son correctos.")

        if st.button("CONFIRMAR COMPRA ✅", type="primary", use_container_width=True):
            if not nombre_cliente.strip() or not telefono_cliente.strip() or not comprobante_file or not acepta_terminos:
                st.error("⚠️ Completa todos los campos obligatorios.")
            else:
                # 🔒 VALIDACIÓN DE HASH ANTI-DUPLICADOS
                bytes_imagen = comprobante_file.getvalue()
                hash_foto = calcular_hash_imagen(bytes_imagen)

                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM boletos WHERE hash_comprobante = ?", (hash_foto,))
                if c.fetchone()[0] > 0:
                    conn.close()
                    st.error("⛔ **COMPROBANTE RECHAZADO:** Este comprobante de pago ya fue utilizado en otra transacción.")
                else:
                    c.execute("SELECT id, numero FROM boletos WHERE rifa_id = ? AND estado = 'disponible'", (st.session_state["rifa_seleccionada"],))
                    disp = c.fetchall()
                    cant = st.session_state["cant_boletos"]

                    if len(disp) >= cant:
                        asignados = random.sample(disp, cant)
                        os.makedirs("comprobantes", exist_ok=True)
                        fecha_ahora = datetime.datetime.now()
                        path_comp = f"comprobantes/{telefono_cliente}_{fecha_ahora.timestamp()}.png"
                        Image.open(comprobante_file).convert("RGB").save(path_comp)

                        num_list = [b_num for _, b_num in asignados]
                        for b_id, _ in asignados:
                            c.execute(
                                """UPDATE boletos 
                                   SET estado = 'reservado', usuario_nombre = ?, usuario_telefono = ?, 
                                       metodo_pago = ?, comprobante = ?, hash_comprobante = ?, fecha_reserva = ? 
                                   WHERE id = ?""",
                                (
                                    nombre_cliente.strip(),
                                    telefono_cliente.strip(),
                                    st.session_state["banco_pago"],
                                    path_comp,
                                    hash_foto,
                                    fecha_ahora,
                                    b_id,
                                ),
                            )
                        conn.commit()
                        conn.close()

                        # Alerta a Telegram
                        msg_admin = (
                            f"🚨 *¡NUEVA COMPRA RECIBIDA!*\n\n"
                            f"👤 *Cliente:* {nombre_cliente}\n"
                            f"📱 *Teléfono:* {telefono_cliente}\n"
                            f"💳 *Banco:* {st.session_state['banco_pago']}\n"
                            f"🎟️ *Boletos ({cant}):* {', '.join(num_list)}"
                        )
                        enviar_notificacion_telegram(msg_admin, path_comp)

                        st.session_state["boletos_asignados_resumen"] = num_list
                        st.session_state["paso_compra"] = 3
                        st.rerun()

    # PASO 3: CONFIRMACIÓN DE BOLETOS ASIGNADOS
    elif paso == 3:
        st.success("🎉 ¡Boletos Reservados Exitosamente!")
        st.write("Tus boletos se encuentran en estado **PENDIENTE** hasta que validemos tu comprobante.")
        
        boletos = st.session_state.get("boletos_asignados_resumen", [])
        cols = st.columns(5)
        for i, n in enumerate(boletos):
            with cols[i % 5]:
                st.markdown(f'<div class="ticket-card"><div style="font-size:1.4rem; color:#38bdf8;">{n}</div><div class="badge-pending">PENDIENTE</div></div>', unsafe_allow_html=True)

        if st.button("ENTIENDO Y CERRAR ✅", use_container_width=True):
            st.session_state["paso_compra"] = 0
            st.rerun()

# ---------------------------------------------------------
# VISTA 2: VERIFICADOR DE BOLETOS (CONSULTA POR TELÉFONO)
# ---------------------------------------------------------
elif st.session_state["vista_actual"] == "verificador":
    st.title("🔍 Verificador de Boletos")
    st.write("Consulta el estado de tus boletos ingresando tu número de teléfono registrado.")

    telefono_buscar = st.text_input("Ingresa tu número de teléfono (WhatsApp):")
    if st.button("Consultar Boletos", type="primary"):
        if not telefono_buscar.strip():
            st.warning("Por favor ingresa un número de teléfono válido.")
        else:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute(
                """SELECT b.numero, b.estado, r.nombre 
                   FROM boletos b JOIN rifas r ON b.rifa_id = r.id 
                   WHERE b.usuario_telefono = ? AND b.estado IN ('reservado', 'confirmado')""",
                (telefono_buscar.strip(),),
            )
            resultados = c.fetchall()
            conn.close()

            if not resultados:
                st.error("No se encontraron boletos registrados para este número.")
            else:
                st.success(f"Se encontraron {len(resultados)} boletos registrados.")
                cols = st.columns(4)
                for idx, (num, estado, r_nombre) in enumerate(resultados):
                    badge = '<div class="badge-approved">APROBADO</div>' if estado == "confirmado" else '<div class="badge-pending">PENDIENTE</div>'
                    with cols[idx % 4]:
                        st.markdown(
                            f"""
                            <div class="ticket-card">
                                <div style="font-size: 0.9rem; color: #94a3b8;">{r_nombre}</div>
                                <div style="font-size: 1.5rem; font-weight: bold; color: #38bdf8; margin: 5px 0;">{num}</div>
                                {badge}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

# ---------------------------------------------------------
# VISTA 3: PANEL DE ADMINISTRACIÓN (APROBACIÓN DE COMPRAS)
# ---------------------------------------------------------
elif st.session_state["vista_actual"] == "admin":
    st.title("⚙️ Panel de Administración")
    
    if not st.session_state["admin_logueado"]:
        clave = st.text_input("Contraseña de acceso:", type="password")
        if st.button("Ingresar"):
            if clave == ADMIN_PASSWORD:
                st.session_state["admin_logueado"] = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta.")
    else:
        st.subheader("📋 Comprobantes Pendientes de Confirmación")

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute(
            """SELECT usuario_nombre, usuario_telefono, metodo_pago, comprobante, fecha_reserva, GROUP_CONCAT(numero), r.nombre
               FROM boletos b JOIN rifas r ON b.rifa_id = r.id WHERE b.estado = 'reservado'
               GROUP BY usuario_telefono, fecha_reserva ORDER BY fecha_reserva DESC"""
        )
        pendientes = c.fetchall()
        conn.close()

        if not pendientes:
            st.info("✅ No hay compras pendientes por verificar en este momento.")
        else:
            for nom, tel, banco, comp, fecha, nums, r_nom in pendientes:
                lista_nums = nums.split(",")
                with st.expander(f"🔴 {nom} — {tel} ({len(lista_nums)} boletos para {r_nom})"):
                    col_det, col_img = st.columns([1, 1])
                    with col_det:
                        st.write(f"👤 **Cliente:** {nom}")
                        st.write(f"📱 **Teléfono:** {tel}")
                        st.write(f"💳 **Banco:** {banco}")
                        st.write(f"📅 **Fecha:** {fecha}")
                        st.write(f"🎟️ **Boletos:** {', '.join(lista_nums)}")

                        c_btn1, c_btn2 = st.columns(2)
                        with c_btn1:
                            if st.button("✅ APROBAR", key=f"ap_{tel}_{fecha}", type="primary", use_container_width=True):
                                conn = sqlite3.connect(DB_FILE)
                                c = conn.cursor()
                                c.execute("UPDATE boletos SET estado = 'confirmado' WHERE usuario_telefono = ? AND fecha_reserva = ?", (tel, fecha))
                                conn.commit()
                                conn.close()
                                st.rerun()

                        with c_btn2:
                            if st.button("❌ RECHAZAR", key=f"rec_{tel}_{fecha}", use_container_width=True):
                                conn = sqlite3.connect(DB_FILE)
                                c = conn.cursor()
                                c.execute(
                                    """UPDATE boletos SET estado = 'disponible', usuario_nombre = NULL, 
                                       usuario_telefono = NULL, metodo_pago = NULL, comprobante = NULL, 
                                       hash_comprobante = NULL, fecha_reserva = NULL 
                                       WHERE usuario_telefono = ? AND fecha_reserva = ?""",
                                    (tel, fecha),
                                )
                                conn.commit()
                                conn.close()
                                st.rerun()

                    with col_img:
                        if comp and os.path.exists(comp):
                            st.image(comp, caption="Comprobante de pago", use_container_width=True)

# ---------------------------------------------------------
# VISTA 4: CÓMO JUGAR
# ---------------------------------------------------------
elif st.session_state["vista_actual"] == "como_jugar":
    st.title("ℹ️ Cómo Jugar")
    st.markdown(
        """
        1. **Selecciona tu Rifa:** Elige el premio que deseas ganar en nuestra página principal.
        2. **Elige la Cantidad:** Define cuántos boletos quieres adquirir.
        3. **Realiza el Pago:** Transfiere el monto a nuestras cuentas bancarias oficiales.
        4. **Sube tu Comprobante:** Completa tus datos e ingresa la foto del pago.
        5. **Verificación:** Tu boleto pasará a revisión y una vez verificado podrás consultarlo en la opción **Verificar Boleto**.
        """
    )
