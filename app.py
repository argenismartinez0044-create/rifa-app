import datetime
import hashlib
import os
import random
import sqlite3
import requests
import streamlit as st
import streamlit.components.v1 as components
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
ADMIN_PASSWORD = "admin"  # 🔑 CAMBIA ESTA CONTRASEÑA

TELEGRAM_BOT_TOKEN = "TU_BOT_TOKEN_AQUI"
TELEGRAM_CHAT_ID = "TU_CHAT_ID_AQUI"

# ---------------------------------------------------------
# FUNCIÓN PARA CALCULAR HASH ÚNICO DE LA IMAGEN
# ---------------------------------------------------------
def calcular_hash_imagen(file_bytes):
    """Genera una huella digital única SHA-256 a partir de los bytes de la imagen"""
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
        print(f"Error enviando notificación: {e}")

# ---------------------------------------------------------
# BASE DE DATOS CON COLUMNA DE HASH
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
    
    # Migración de BD por si la tabla ya existía sin la columna hash_comprobante
    try:
        c.execute("ALTER TABLE boletos ADD COLUMN hash_comprobante TEXT")
    except sqlite3.OperationalError:
        pass  # La columna ya existe

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
# ESTILOS CSS
# ---------------------------------------------------------
if "tema_claro" not in st.session_state:
    st.session_state["tema_claro"] = False
if "vista_actual" not in st.session_state:
    st.session_state["vista_actual"] = "rifas"
if "paso_compra" not in st.session_state:
    st.session_state["paso_compra"] = 0
if "banco_pago" not in st.session_state:
    st.session_state["banco_pago"] = "Banreservas"
if "admin_logueado" not in st.session_state:
    st.session_state["admin_logueado"] = False

bg_color = "#f8fafc" if st.session_state["tema_claro"] else "linear-gradient(135deg, #070913 0%, #0c1021 50%, #05060b 100%)"
text_color = "#0f172a" if st.session_state["tema_claro"] else "#FFFFFF"

st.markdown(
    f"""
    <style>
    .stApp {{ background: {bg_color} !important; color: {text_color}; }}
    .ticket-card {{ background: rgba(15, 23, 42, 0.85); border: 1px solid #1e293b; border-radius: 12px; padding: 15px; text-align: center; margin-bottom: 12px; }}
    .badge-pending {{ display: inline-block; background: #b45309; color: #ffffff; font-weight: bold; font-size: 0.75rem; padding: 4px 10px; border-radius: 20px; }}
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
# PROCESO DE COMPRA (VALIDACIÓN DE COMPROBANTE ÚNICO)
# ---------------------------------------------------------
if st.session_state["vista_actual"] == "rifas":
    paso = st.session_state.get("paso_compra", 0)

    if paso == 2:
        st.markdown("### 📝 Datos del Participante")
        nombre_cliente = st.text_input("Nombre Completo *")
        telefono_cliente = st.text_input("Teléfono (WhatsApp) *")
        comprobante_file = st.file_uploader("Subir Comprobante de Pago *", type=["png", "jpg", "jpeg"])
        acepta_terminos = st.checkbox("Confirmo que mis datos y el comprobante ingresado son correctos.")

        if st.button("CONFIRMAR COMPRA ✅", type="primary", use_container_width=True):
            faltantes = []
            if not nombre_cliente.strip(): faltantes.append("Nombre Completo")
            if not telefono_cliente.strip(): faltantes.append("Teléfono / WhatsApp")
            if comprobante_file is None: faltantes.append("Comprobante de Pago")
            if not acepta_terminos: faltantes.append("Aceptar los Términos y Condiciones")

            if faltantes:
                st.error("⚠️ **Faltan campos obligatorios:**\n- " + "\n- ".join(faltantes))
            else:
                # 🔍 1. OBTENER BYTES Y CALCULAR HASH DE LA IMAGEN
                bytes_imagen = comprobante_file.getvalue()
                hash_foto = calcular_hash_imagen(bytes_imagen)

                # 🚫 2. VERIFICAR SI EL HASH YA EXISTE EN LA BASE DE DATOS
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM boletos WHERE hash_comprobante = ?", (hash_foto,))
                existe_duplicado = c.fetchone()[0]

                if existe_duplicado > 0:
                    conn.close()
                    st.error(
                        "⛔ **COMPROBANTE RECHAZADO:** Este comprobante de pago ya fue utilizado en el sistema. "
                        "No se permite subir la misma captura de pantalla más de una vez."
                    )
                else:
                    # 3. PROCESAR LA RESERVA SI ES UN COMPROBANTE ÚNICO
                    c.execute("SELECT id, numero FROM boletos WHERE rifa_id = ? AND estado = 'disponible'", (st.session_state["rifa_seleccionada"],))
                    disp = c.fetchall()
                    cant = st.session_state["cant_boletos"]

                    if len(disp) >= cant:
                        asignados = random.sample(disp, cant)
                        os.makedirs("comprobantes", exist_ok=True)
                        fecha_ahora = datetime.datetime.now()
                        path_comp = f"comprobantes/{telefono_cliente}_{fecha_ahora.timestamp()}.png"
                        
                        # Guardar imagen en disco
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
                                    hash_foto,  # 🔒 Guardamos la huella digital única
                                    fecha_ahora,
                                    b_id,
                                ),
                            )
                        conn.commit()
                        conn.close()

                        # Notificación en tiempo real
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

    elif paso == 3:
        st.success("🎉 ¡Boletos Reservados Exitosamente!")
        boletos = st.session_state.get("boletos_asignados_resumen", [])
        cols = st.columns(5)
        for i, n in enumerate(boletos):
            with cols[i % 5]:
                st.markdown(f'<div class="ticket-card"><div style="font-size:1.4rem; color:#38bdf8;">{n}</div><div class="badge-pending">PENDIENTE</div></div>', unsafe_allow_html=True)
        if st.button("ENTIENDO Y CERRAR ✅", use_container_width=True):
            st.session_state["paso_compra"] = 0
            st.rerun()

# ---------------------------------------------------------
# PANEL DE ADMINISTRACIÓN
# ---------------------------------------------------------
elif st.session_state["vista_actual"] == "admin":
    st.title("⚙️ Panel de Administración")
    if not st.session_state["admin_logueado"]:
        clave = st.text_input("Contraseña admin:", type="password")
        if st.button("Ingresar"):
            if clave == ADMIN_PASSWORD:
                st.session_state["admin_logueado"] = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta")
    else:
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
            st.info("✅ No hay boletos pendientes.")
        else:
            for nom, tel, banco, comp, fecha, nums, r_nom in pendientes:
                lista_nums = nums.split(",")
                with st.expander(f"🔴 {nom} — {tel} ({len(lista_nums)} boletos)"):
                    st.write(f"👤 **Cliente:** {nom} | 📱 **Teléfono:** {tel} | 💳 **Banco:** {banco}")
                    st.write(f"🎟️ **Boletos:** {', '.join(lista_nums)}")
                    if comp and os.path.exists(comp):
                        st.image(comp, width=300)

                    col_a, col_r = st.columns(2)
                    with col_a:
                        if st.button("✅ APROBAR PAGO", key=f"ap_{tel}_{fecha}", type="primary"):
                            conn = sqlite3.connect(DB_FILE)
                            c = conn.cursor()
                            c.execute("UPDATE boletos SET estado = 'confirmado' WHERE usuario_telefono = ? AND fecha_reserva = ?", (tel, fecha))
                            conn.commit()
                            conn.close()
                            st.rerun()
                    with col_r:
                        if st.button("❌ RECHAZAR", key=f"rec_{tel}_{fecha}"):
                            conn = sqlite3.connect(DB_FILE)
                            c = conn.cursor()
                            # Liberar boletos y borrar hash para permitir correcciones si fue rechazada por error
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
