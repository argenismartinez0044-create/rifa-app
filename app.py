import datetime
import os
import sqlite3
import base64
import streamlit as st

DB_FILE = "rifas_v4.db"

st.set_page_config(
    page_title="Rifas Sirio RD",
    page_icon="logo.png" if os.path.exists("logo.png") else "🎲",
    layout="wide"
)

# =========================================================
# GESTIÓN DE TEMA (CLARO / OSCURO)
# =========================================================
if "theme_mode" not in st.session_state:
    st.session_state["theme_mode"] = "dark"

def toggle_theme():
    st.session_state["theme_mode"] = "light" if st.session_state["theme_mode"] == "dark" else "dark"

is_dark = st.session_state["theme_mode"] == "dark"

bg_style = """
    background-color: #0b0f17;
    background-image: 
        radial-gradient(#d4af37 0.75px, transparent 0.75px), 
        repeating-linear-gradient(45deg, rgba(212, 175, 55, 0.05) 0, rgba(212, 175, 55, 0.05) 10px, transparent 0, transparent 20px);
    background-size: 15px 15px, 40px 40px;
    color: #FFFFFF;
""" if is_dark else """
    background-color: #f8fafc;
    background-image: 
        radial-gradient(#c0a028 0.85px, transparent 0.85px), 
        repeating-linear-gradient(45deg, rgba(212, 175, 55, 0.08) 0, rgba(212, 175, 55, 0.08) 10px, transparent 0, transparent 20px);
    background-size: 15px 15px, 40px 40px;
    color: #0f172a;
"""

text_color = "#FFFFFF" if is_dark else "#0f172a"

# =========================================================
# ESTILOS CSS PERSONALIZADOS (BANCOS Y BARRA)
# =========================================================
st.markdown(f"""
<style>
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}

    .stApp {{
        {bg_style}
    }}
    
    .logo-hero-container {{
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 15px 0;
    }}

    .bank-card-container {{
        position: relative;
        background: linear-gradient(145deg, #1e293b, #0f172a);
        border: 2px solid #38bdf8;
        border-radius: 12px;
        padding: 20px;
        margin-top: 15px;
        color: #ffffff;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
    }}

    .badge-pop {{
        background: linear-gradient(90deg, #f5c518, #ff8c00);
        color: #000;
        font-weight: bold;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
    }}

    /* Contenedor interactivo para los botones de banco */
    .bank-card-wrapper {{
        position: relative;
        width: 135px;
        height: 110px;
        margin: 0 auto;
    }}

    /* Superposición transparente táctil y de clic sobre el 100% de la tarjeta */
    .bank-card-wrapper div[data-testid="stButton"] {{
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        width: 100% !important;
        height: 100% !important;
        z-index: 10 !important;
    }}

    .bank-card-wrapper div[data-testid="stButton"] button {{
        background: transparent !important;
        border: none !important;
        color: transparent !important;
        box-shadow: none !important;
        width: 100% !important;
        height: 100% !important;
        padding: 0 !important;
        cursor: pointer !important;
    }}

    /* Apariencia visual de la tarjeta de banco */
    .bank-card-btn {{
        position: absolute;
        top: 0;
        left: 0;
        width: 135px;
        height: 110px;
        background-color: #131927;
        border: 1.5px solid #2a364f;
        border-radius: 12px;
        padding: 12px 8px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        transition: all 0.2s ease-in-out;
        z-index: 1;
        box-sizing: border-box;
    }}

    .bank-card-selected {{
        border: 2px solid #38bdf8 !important;
        background-color: #172554 !important;
        box-shadow: 0 0 10px rgba(56, 189, 248, 0.4);
    }}

    .bank-icon-img {{
        width: 42px;
        height: 42px;
        object-fit: contain;
        border-radius: 8px;
        margin-bottom: 8px;
    }}

    .bank-title-text {{
        color: #e2e8f0;
        font-size: 11px;
        font-weight: 700;
        text-align: center;
        line-height: 1.2;
        text-transform: uppercase;
    }}

    /* Indicador de porcentaje simple */
    .progress-text {{
        display: flex;
        justify-content: space-between;
        font-size: 13px;
        font-weight: bold;
        color: #f5c518;
        margin-bottom: 4px;
    }}
</style>
""", unsafe_allow_html=True)


# =========================================================
# BASE DE DATOS
# =========================================================

def conectar():
    return sqlite3.connect(DB_FILE, check_same_thread=False)


def agregar_columna_si_no_existe(conn, tabla, columna, tipo):
    columnas = [fila[1] for fila in conn.execute(f"PRAGMA table_info({tabla})").fetchall()]
    if columna not in columnas:
        conn.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna} {tipo}")


def init_db():
    conn = conectar()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS rifas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            categoria TEXT,
            precio_boleto REAL,
            min_boletos INTEGER,
            total_boletos INTEGER,
            imagen TEXT,
            fecha TEXT,
            activa INTEGER DEFAULT 1
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS boletos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rifa_id INTEGER,
            numero TEXT,
            estado TEXT DEFAULT 'disponible',
            usuario_nombre TEXT,
            usuario_telefono TEXT,
            metodo_pago TEXT,
            comprobante TEXT,
            fecha_reserva DATETIME,
            solicitud_id INTEGER
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS metodos_pago (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            titular TEXT NOT NULL,
            tipo_cuenta TEXT NOT NULL DEFAULT 'Ahorros',
            numero_cuenta TEXT NOT NULL,
            imagen TEXT DEFAULT '',
            activo INTEGER DEFAULT 1
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS solicitudes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rifa_id INTEGER NOT NULL,
            nombre TEXT NOT NULL,
            telefono TEXT NOT NULL,
            cantidad INTEGER NOT NULL,
            metodo_pago TEXT NOT NULL,
            comprobante TEXT NOT NULL,
            fecha_solicitud DATETIME,
            estado TEXT DEFAULT 'pendiente',
            terminos_aceptados INTEGER DEFAULT 0,
            fecha_terminos DATETIME,
            motivo_rechazo TEXT DEFAULT ''
        )
    """)

    # Compatibilidad con la base de datos anterior.
    agregar_columna_si_no_existe(conn, "boletos", "solicitud_id", "INTEGER")
    agregar_columna_si_no_existe(conn, "rifas", "activa", "INTEGER DEFAULT 1")

    c.execute("SELECT COUNT(*) FROM metodos_pago")
    if c.fetchone()[0] == 0:
        c.executemany("""
            INSERT INTO metodos_pago
            (nombre, titular, tipo_cuenta, numero_cuenta, imagen, activo)
            VALUES (?,?,?,?,?,1)
        """, [
            ("Banreservas", "ARGENIS MARTINEZ C.", "Ahorros", "9606561652", "banreservas.png"),
            ("Banco Popular", "ARGENIS MARTINEZ", "Ahorros", "821794971", "popular.png")
        ])

    c.execute("SELECT COUNT(*) FROM rifas")
    if c.fetchone()[0] == 0:
        iniciales = [
            ("PlayStation 5 Pro", "JUEGOS", 5.0, 10, 10000, "play.jpg", "Fecha pendiente"),
            ("5 iPhone 17 Pro Max", "TECNOLOGÍA", 15.0, 10, 10000, "iphone.jpg", "Al vender el 80%")
        ]

        for rifa in iniciales:
            c.execute("""
                INSERT INTO rifas
                (nombre, categoria, precio_boleto, min_boletos, total_boletos, imagen, fecha, activa)
                VALUES (?,?,?,?,?,?,?,1)
            """, rifa)

        for rifa_id in (1, 2):
            numeros = [(rifa_id, f"{i:05d}") for i in range(1, 10001)]
            c.executemany(
                "INSERT INTO boletos (rifa_id, numero) VALUES (?,?)",
                numeros
            )

    conn.commit()
    conn.close()


def guardar_imagen(uploaded, carpeta, base):
    os.makedirs(carpeta, exist_ok=True)
    ext = os.path.splitext(uploaded.name)[1].lower()

    if ext not in (".png", ".jpg", ".jpeg", ".pdf"):
        ext = ".png"

    limpio = "".join(ch if ch.isalnum() else "_" for ch in base)
    nombre = f"{limpio}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}{ext}"
    ruta = os.path.join(carpeta, nombre)

    with open(ruta, "wb") as f:
        f.write(uploaded.getbuffer())

    return ruta


def obtener_metodos_pago():
    conn = conectar()
    filas = conn.execute("""
        SELECT id, nombre, titular, tipo_cuenta, numero_cuenta, imagen
        FROM metodos_pago
        WHERE COALESCE(activo,1)=1
    """).fetchall()
    conn.close()
    return filas


def normalizar_telefono(telefono):
    return (
        telefono.replace(" ", "")
        .replace("-", "")
        .replace("(", "")
        .replace(")", "")
        .replace("+", "")
        .strip()
    )


def obtener_porcentaje_rifa(rifa_id, total_boletos):
    conn = conectar()
    vendidos = conn.execute("""
        SELECT COUNT(*)
        FROM boletos
        WHERE rifa_id=? AND estado='confirmado'
    """, (rifa_id,)).fetchone()[0]
    conn.close()

    total = total_boletos if total_boletos > 0 else 1
    return min(100.0, (vendidos / total) * 100)


def obtener_cantidad_comprometida(rifa_id):
    conn = conectar()

    confirmados = conn.execute("""
        SELECT COUNT(*)
        FROM boletos
        WHERE rifa_id=? AND estado='confirmado'
    """, (rifa_id,)).fetchone()[0]

    pendientes = conn.execute("""
        SELECT COALESCE(SUM(cantidad), 0)
        FROM solicitudes
        WHERE rifa_id=? AND estado='pendiente'
    """, (rifa_id,)).fetchone()[0]

    conn.close()
    return confirmados + pendientes


def reservar_numeros_temporales(solicitud_id):
    """Asigna números inmediatamente, pero quedan reservados hasta verificar el pago."""
    conn = conectar()
    c = conn.cursor()
    try:
        c.execute("BEGIN IMMEDIATE")
        solicitud = c.execute("""
            SELECT rifa_id, nombre, telefono, cantidad, metodo_pago, comprobante
            FROM solicitudes
            WHERE id=? AND estado='pendiente'
        """, (solicitud_id,)).fetchone()

        if not solicitud:
            conn.rollback()
            return False, "La solicitud no existe o ya fue procesada."

        rifa_id, nombre, telefono, cantidad, metodo, comprobante = solicitud
        disponibles = c.execute("""
            SELECT id, numero
            FROM boletos
            WHERE rifa_id=? AND estado='disponible'
            ORDER BY RANDOM()
            LIMIT ?
        """, (rifa_id, cantidad)).fetchall()

        if len(disponibles) < cantidad:
            conn.rollback()
            return False, "No hay suficientes números disponibles para esta solicitud."

        ahora = datetime.datetime.now()
        for boleto_id, numero in disponibles:
            c.execute("""
                UPDATE boletos
                SET estado='reservado', usuario_nombre=?, usuario_telefono=?,
                    metodo_pago=?, comprobante=?, fecha_reserva=?, solicitud_id=?
                WHERE id=? AND estado='disponible'
            """, (nombre, telefono, metodo, comprobante, ahora, solicitud_id, boleto_id))

        conn.commit()
        return True, [numero for _, numero in disponibles]
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()


def aprobar_solicitud(solicitud_id):
    conn = conectar()
    c = conn.cursor()
    try:
        c.execute("BEGIN IMMEDIATE")
        solicitud = c.execute("SELECT estado FROM solicitudes WHERE id=?", (solicitud_id,)).fetchone()
        if not solicitud or solicitud[0] != 'pendiente':
            conn.rollback()
            return False, "La solicitud no está pendiente."

        # Los números ya fueron asignados temporalmente al enviar la solicitud.
        c.execute("""
            UPDATE boletos SET estado='confirmado'
            WHERE solicitud_id=? AND estado='reservado'
        """, (solicitud_id,))
        c.execute("UPDATE solicitudes SET estado='aprobada' WHERE id=?", (solicitud_id,))
        conn.commit()
        return True, "Solicitud aprobada correctamente."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()


def rechazar_solicitud(solicitud_id, motivo):
    conn = conectar()
    c = conn.cursor()
    try:
        c.execute("BEGIN IMMEDIATE")
        # Al rechazar, los números temporales vuelven a estar disponibles.
        c.execute("""
            UPDATE boletos SET estado='disponible', usuario_nombre=NULL,
                usuario_telefono=NULL, metodo_pago=NULL, comprobante=NULL,
                fecha_reserva=NULL, solicitud_id=NULL
            WHERE solicitud_id=? AND estado='reservado'
        """, (solicitud_id,))
        c.execute("""
            UPDATE solicitudes SET estado='rechazada', motivo_rechazo=?
            WHERE id=? AND estado='pendiente'
        """, (motivo, solicitud_id))
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()


init_db()

# =========================================================
# SESIÓN
# =========================================================

for clave, valor in {
    "active_dialog": None,
    "selected_rifa": None,
    "selected_boletos_qty": 10,
    "banco_activo_id": None,
    "verificar_open": False,
    "admin_autenticado": False
}.items():
    if clave not in st.session_state:
        st.session_state[clave] = valor


# =========================================================
# ACCESO ADMINISTRADOR
# =========================================================

# Para entrar al administrador usa:
# tu-dominio/?admin=1
# La contraseña se configura en .streamlit/secrets.toml:
# ADMIN_PASSWORD = "TU_CONTRASEÑA"

admin_param = str(st.query_params.get("admin", "")).lower()
admin_mode = admin_param in ("1", "true", "si", "sí", "administrador", "admin")

if admin_mode:
    st.markdown('<div class="logo-hero-container">', unsafe_allow_html=True)

    if os.path.exists("logo.png"):
        st.image("logo.png", width=180)

    st.markdown("</div>", unsafe_allow_html=True)

    if not st.session_state["admin_autenticado"]:
        st.title("Acceso privado")

        password = st.text_input(
            "Contraseña de administrador",
            type="password"
        )

        if st.button("Entrar", use_container_width=True):
            try:
                clave_correcta = st.secrets["ADMIN_PASSWORD"]
            except Exception:
                clave_correcta = ""

            if clave_correcta and password == clave_correcta:
                st.session_state["admin_autenticado"] = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta o no configurada.")

        st.stop()


# =========================================================
# PANEL DE ADMINISTRACIÓN
# =========================================================

if admin_mode and st.session_state["admin_autenticado"]:

    st.title("⚙️ Panel de administración")
    st.caption("Control privado de Rifas Sirio RD")

    menu_admin = st.radio(
        "☰ Menú de administración",
        ["📊 Resumen", "🧾 Pagos pendientes", "🎟️ Boletos", "🎲 Rifas", "🏦 Métodos de pago", "⚙️ Configuración"],
        horizontal=True,
        key="menu_admin"
    )

    if menu_admin != "🧾 Pagos pendientes":
        conn = conectar()
        if menu_admin == "📊 Resumen":
            pendientes_n = conn.execute("SELECT COUNT(*) FROM solicitudes WHERE estado='pendiente'").fetchone()[0]
            aprobadas_n = conn.execute("SELECT COUNT(*) FROM solicitudes WHERE estado='aprobada'").fetchone()[0]
            rechazadas_n = conn.execute("SELECT COUNT(*) FROM solicitudes WHERE estado='rechazada'").fetchone()[0]
            reservados_n = conn.execute("SELECT COUNT(*) FROM boletos WHERE estado='reservado'").fetchone()[0]
            confirmados_n = conn.execute("SELECT COUNT(*) FROM boletos WHERE estado='confirmado'").fetchone()[0]
            c1,c2,c3 = st.columns(3)
            c1.metric("🕐 Pagos pendientes", pendientes_n)
            c2.metric("🟢 Aprobadas", aprobadas_n)
            c3.metric("🔴 Rechazadas", rechazadas_n)
            c4,c5 = st.columns(2)
            c4.metric("🟡 Boletos pendientes", reservados_n)
            c5.metric("🎟️ Boletos aprobados", confirmados_n)
            st.info("En '🧾 Pagos pendientes' puedes revisar el comprobante y aprobar o rechazar cada solicitud.")
        elif menu_admin == "🎟️ Boletos":
            st.subheader("🎟️ Control de boletos")
            filtro = st.selectbox("Estado", ["Todos", "reservado", "confirmado", "disponible"])
            if filtro == "Todos":
                filas = conn.execute("SELECT b.numero,b.estado,r.nombre,b.usuario_nombre,b.usuario_telefono FROM boletos b JOIN rifas r ON b.rifa_id=r.id ORDER BY r.nombre,b.numero LIMIT 500").fetchall()
            else:
                filas = conn.execute("SELECT b.numero,b.estado,r.nombre,b.usuario_nombre,b.usuario_telefono FROM boletos b JOIN rifas r ON b.rifa_id=r.id WHERE b.estado=? ORDER BY r.nombre,b.numero LIMIT 500", (filtro,)).fetchall()
            st.dataframe(filas, use_container_width=True, hide_index=True)
        elif menu_admin == "🎲 Rifas":
            st.subheader("🎲 Rifas")
            filas = conn.execute("SELECT id,nombre,categoria,precio_boleto,total_boletos,fecha,activa FROM rifas ORDER BY id DESC").fetchall()
            for rid,nombre,cat,precio,total,fecha,activa in filas:
                with st.container(border=True):
                    st.write(f"**{nombre}** · {cat} · RD$ {precio:,.2f} · {total} boletos")
                    st.write(f"Sorteo: {fecha} · {'🟢 ACTIVA' if activa else '🔴 INACTIVA'}")
                    if st.button("🔴 Desactivar" if activa else "🟢 Activar", key=f"rifa_admin_{rid}"):
                        conn.execute("UPDATE rifas SET activa=? WHERE id=?", (0 if activa else 1,rid)); conn.commit(); st.rerun()
        elif menu_admin == "🏦 Métodos de pago":
            st.subheader("🏦 Métodos de pago")
            filas = conn.execute("SELECT id,nombre,titular,tipo_cuenta,numero_cuenta,activo FROM metodos_pago ORDER BY nombre").fetchall()
            for mid,nombre,titular,tipo,cuenta,activo in filas:
                st.write(f"**{nombre}** · {tipo} · {cuenta} · Titular: {titular}")
                if st.button("Desactivar" if activo else "Activar", key=f"metodo_admin_{mid}"):
                    conn.execute("UPDATE metodos_pago SET activo=? WHERE id=?", (0 if activo else 1,mid)); conn.commit(); st.rerun()
        elif menu_admin == "⚙️ Configuración":
            st.subheader("⚙️ Configuración")
            st.info("La contraseña se configura mediante ADMIN_PASSWORD en .streamlit/secrets.toml.")
            st.write("**Soporte:** 829-483-5217")
            st.write("**Estados:** disponible → reservado → confirmado")
        conn.close()
        if st.button("🚪 Cerrar sesión", key="admin_logout_menu"):
            st.session_state["admin_autenticado"] = False; st.query_params.clear(); st.rerun()
        st.stop()

    if st.button("🚪 Cerrar sesión"):
        st.session_state["admin_autenticado"] = False
        st.query_params.clear()
        st.rerun()

    conn = conectar()

    pendientes = conn.execute("""
        SELECT
            s.id,
            s.nombre,
            s.telefono,
            s.cantidad,
            s.metodo_pago,
            s.comprobante,
            s.fecha_solicitud,
            r.nombre
        FROM solicitudes s
        JOIN rifas r ON s.rifa_id = r.id
        WHERE s.estado='pendiente'
        ORDER BY s.fecha_solicitud ASC
    """).fetchall()

    conn.close()

    st.subheader(f"🕐 Solicitudes pendientes: {len(pendientes)}")

    if not pendientes:
        st.success("No hay solicitudes pendientes de revisión.")
    else:
        for solicitud in pendientes:
            (
                solicitud_id,
                nombre,
                telefono,
                cantidad,
                metodo,
                comprobante,
                fecha,
                rifa_nombre
            ) = solicitud

            with st.container(border=True):
                st.markdown(f"### Solicitud #{solicitud_id}")
                st.write(f"**Cliente:** {nombre}")
                st.write(f"**WhatsApp:** {telefono}")
                st.write(f"**Rifa:** {rifa_nombre}")
                st.write(f"**Cantidad:** {cantidad} boletos")
                st.write(f"**Método de pago:** {metodo}")
                st.write(f"**Fecha:** {fecha}")
                st.write("**Estado:** 🟡 Pendiente de verificación")

                if comprobante and os.path.exists(comprobante):
                    ext = os.path.splitext(comprobante)[1].lower()

                    if ext == ".pdf":
                        st.info("El comprobante recibido es un PDF.")
                        with open(comprobante, "rb") as archivo:
                            st.download_button(
                                "📄 Ver / descargar comprobante",
                                archivo.read(),
                                file_name=os.path.basename(comprobante),
                                key=f"pdf_{solicitud_id}"
                            )
                    else:
                        st.image(comprobante, caption="Comprobante recibido")

                c1, c2 = st.columns(2)

                with c1:
                    if st.button(
                        "✅ APROBAR PAGO Y ASIGNAR NÚMEROS",
                        key=f"aprobar_{solicitud_id}",
                        use_container_width=True
                    ):
                        ok, mensaje = aprobar_solicitud(solicitud_id)

                        if ok:
                            st.success(
                                "Pago aprobado. Los números fueron asignados automáticamente."
                            )
                            st.rerun()
                        else:
                            st.error(mensaje)

                with c2:
                    if st.button(
                        "❌ RECHAZAR",
                        key=f"rechazar_{solicitud_id}",
                        use_container_width=True
                    ):
                        st.session_state[f"confirmar_rechazo_{solicitud_id}"] = True

                if st.session_state.get(f"confirmar_rechazo_{solicitud_id}", False):
                    motivo = st.text_input(
                        "Motivo del rechazo",
                        key=f"motivo_{solicitud_id}"
                    )

                    if st.button(
                        "Confirmar rechazo",
                        key=f"confirmar_{solicitud_id}"
                    ):
                        rechazar_solicitud(solicitud_id, motivo)
                        st.rerun()

    st.stop()


# =========================================================
# MODAL DE PAQUETES
# =========================================================

@st.dialog("Elige tu paquete de números", width="large")
def modal_combos():
    rifa_datos = st.session_state["selected_rifa"]

    if not rifa_datos:
        return

    (
        rifa_id,
        nombre,
        categoria,
        precio,
        min_boletos,
        total_boletos,
        imagen,
        fecha
    ) = rifa_datos

    st.markdown(
        "<h3 style='text-align:center;'>Selecciona un paquete</h3>",
        unsafe_allow_html=True
    )

    paquetes = [
        {"nombre": "ROOKIE", "boletos": 2, "icon": "🪖"},
        {"nombre": "AMATEUR", "boletos": 5, "icon": "🏁"},
        {"nombre": "PRO", "boletos": 10, "icon": "🚀"},
        {"nombre": "ELITE", "boletos": 15, "icon": "🏆"},
        {"nombre": "CAMPEÓN", "boletos": 25, "icon": "👑"},
        {"nombre": "LEYENDA", "boletos": 50, "icon": "⚡"},
        {"nombre": "MÍTICO", "boletos": 100, "icon": "🔥"}
    ]

    col1, col2 = st.columns(2)

    for idx, pkg in enumerate(paquetes):
        col_dest = col1 if idx % 2 == 0 else col2

        with col_dest:
            with st.container(border=True):
                st.markdown(f"### {pkg['icon']} {pkg['nombre']}")
                st.markdown(f"## {pkg['boletos']} NÚMEROS")

                costo = pkg["boletos"] * precio
                st.markdown(f"**RD$ {costo:,.2f}**")

                if st.button(
                    f"Elegir {pkg['nombre']}",
                    key=f"btn_pkg_{idx}",
                    use_container_width=True
                ):
                    st.session_state["selected_boletos_qty"] = pkg["boletos"]
                    st.session_state["banco_activo_id"] = None
                    st.session_state["active_dialog"] = "pago"
                    st.rerun()

    st.divider()

    if st.button(
        "✏️ ELEGIR CANTIDAD PERSONALIZADA",
        use_container_width=True
    ):
        st.session_state["selected_boletos_qty"] = min_boletos
        st.session_state["banco_activo_id"] = None
        st.session_state["active_dialog"] = "pago"
        st.rerun()


# =========================================================
# MODAL DE COMPRA
# =========================================================

@st.dialog("Completa tu solicitud", width="large")
def modal_pago_detalles():
    rifa_datos = st.session_state["selected_rifa"]

    if not rifa_datos:
        return

    (
        rifa_id,
        nombre,
        categoria,
        precio,
        min_boletos,
        total_boletos,
        imagen,
        fecha
    ) = rifa_datos

    st.markdown(f"### {nombre}")

    modo_p = st.radio(
        "Modo",
        ["PAQUETES", "CANTIDAD LIBRE"],
        horizontal=True,
        label_visibility="collapsed"
    )

    if modo_p == "CANTIDAD LIBRE":
        c1, c2, c3 = st.columns([1, 2, 1])

        with c1:
            if st.button("➖", use_container_width=True):
                if st.session_state["selected_boletos_qty"] > min_boletos:
                    st.session_state["selected_boletos_qty"] -= 1
                    st.rerun()

        with c2:
            st.markdown(
                f"<h2 style='text-align:center;color:#f5c518;'>"
                f"{st.session_state['selected_boletos_qty']}</h2>",
                unsafe_allow_html=True
            )

        with c3:
            if st.button("➕", use_container_width=True):
                if st.session_state["selected_boletos_qty"] < 10000:
                    st.session_state["selected_boletos_qty"] += 1
                    st.rerun()

    cantidad = st.session_state["selected_boletos_qty"]
    total_pagar = cantidad * precio

    st.markdown(f"### TOTAL A PAGAR: **RD$ {total_pagar:,.2f}**")

    st.info(
        "Los números NO se asignan todavía. "
        "Primero revisaremos tu comprobante. "
        "Después de aprobar el pago, el sistema asignará tus números automáticamente."
    )

    st.divider()

    nombre_c = st.text_input(
        "Nombre completo *",
        placeholder="Ej: Juan Pérez"
    )

    telefono_c = st.text_input(
        "Teléfono / WhatsApp *",
        placeholder="+1 (829) 000-0000"
    )

    st.divider()
    st.markdown("#### Método de pago *")

    metodos = obtener_metodos_pago()
    banco_seleccionado = None

    cols_bancos = st.columns(len(metodos) if metodos else 1)

    for idx, m in enumerate(metodos):
        m_id, m_nombre, m_titular, m_tipo, m_cuenta, m_img = m
        es_seleccionado = (
            st.session_state.get("banco_activo_id") == m_id
        )

        with cols_bancos[idx]:
            st.markdown(
                '<div class="bank-card-wrapper">',
                unsafe_allow_html=True
            )

            if m_img and os.path.exists(m_img):
                with open(m_img, "rb") as img_f:
                    encoded = base64.b64encode(img_f.read()).decode()

                img_element = (
                    f'<img src="data:image/png;base64,{encoded}" '
                    f'class="bank-icon-img"/>'
                )
            else:
                img_element = '<div style="font-size:28px;">🏦</div>'

            if st.button(" ", key=f"btn_card_{m_id}"):
                st.session_state["banco_activo_id"] = m_id
                st.rerun()

            selected_class = (
                "bank-card-selected" if es_seleccionado else ""
            )

            st.markdown(
                f"""
                <div class="bank-card-btn {selected_class}">
                    {img_element}
                    <span class="bank-title-text">
                        {m_nombre}<br>
                        <small>({m_tipo.upper()})</small>
                    </span>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.get("banco_activo_id"):
        banco_sel = next(
            (
                m for m in metodos
                if m[0] == st.session_state["banco_activo_id"]
            ),
            None
        )

        if banco_sel:
            banco_seleccionado = banco_sel[1]

            st.markdown(
                f"""
                <div class="bank-card-container">
                    <h4 style="color:#38bdf8;">🏦 {banco_sel[1]}</h4>
                    <p><strong>Titular:</strong> {banco_sel[2]}</p>
                    <p><strong>Tipo de cuenta:</strong> {banco_sel[3]}</p>
                    <p><strong>Número de cuenta:</strong></p>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.code(banco_sel[4])

    st.divider()

    comprobante_file = st.file_uploader(
        "Subir foto o PDF del comprobante *",
        type=["png", "jpg", "jpeg", "pdf"]
    )

    st.markdown("#### Términos y condiciones")

    acepta_terminos = st.checkbox(
        "Acepto los términos, condiciones y política de privacidad."
    )

    confirma_datos = st.checkbox(
        "Confirmo que mis datos y comprobante son correctos."
    )

    st.caption(
        "El comprobante será revisado por el administrador. "
        "La aprobación puede tardar entre 24 y 48 horas."
    )

    listo = all([
        nombre_c.strip(),
        telefono_c.strip(),
        banco_seleccionado,
        comprobante_file,
        acepta_terminos,
        confirma_datos
    ])

    if st.button(
        "🛒 ENVIAR SOLICITUD DE COMPRA",
        disabled=not listo,
        use_container_width=True
    ):
        telefono_normalizado = normalizar_telefono(telefono_c)

        conn = conectar()

        comprometidos = obtener_cantidad_comprometida(rifa_id)

        if comprometidos + cantidad > total_boletos:
            conn.close()
            st.error(
                "No hay suficientes cupos disponibles para esta solicitud."
            )
            return

        ruta_comp = guardar_imagen(
            comprobante_file,
            "comprobantes",
            telefono_normalizado
        )

        ahora = datetime.datetime.now()

        cursor = conn.execute("""
            INSERT INTO solicitudes
            (rifa_id, nombre, telefono, cantidad, metodo_pago, comprobante,
             fecha_solicitud, estado, terminos_aceptados, fecha_terminos)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (rifa_id, nombre_c.strip(), telefono_normalizado, cantidad,
              banco_seleccionado, ruta_comp, ahora, "pendiente", 1, ahora))
        solicitud_id = cursor.lastrowid
        conn.commit()
        conn.close()

        ok, numeros = reservar_numeros_temporales(solicitud_id)
        if not ok:
            st.error(str(numeros))
            return

        st.session_state["active_dialog"] = None
        st.session_state["banco_activo_id"] = None

        st.success("🎉 Solicitud enviada correctamente.")
        st.warning(
            "⏳ Tus números ya fueron asignados temporalmente y aparecen como "
            "PENDIENTES DE VERIFICACIÓN. La revisión puede tardar entre 24 y 48 horas."
        )


# =========================================================
# ABRIR MODALES
# =========================================================

if st.session_state["active_dialog"] == "combos":
    modal_combos()

elif st.session_state["active_dialog"] == "pago":
    modal_pago_detalles()


# =========================================================
# BARRA SUPERIOR
# =========================================================

n1, n2, n3, n4 = st.columns([2, 1, 1, 2])

with n1:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=140)
    else:
        st.markdown("## 🎲 RIFAS SIRIO RD")

with n2:
    st.markdown(
        '<a href="#rifas-activas" style="text-decoration:none;">'
        '<button style="width:100%;padding:8px;border-radius:8px;'
        'border:1px solid #d4af37;background:transparent;'
        'color:#d4af37;font-weight:bold;cursor:pointer;">'
        '🎟️ Rifas</button></a>',
        unsafe_allow_html=True
    )

with n3:
    theme_icon = "☀️ Modo Claro" if is_dark else "🌙 Modo Oscuro"

    if st.button(
        theme_icon,
        key="btn_theme_toggle",
        use_container_width=True
    ):
        toggle_theme()
        st.rerun()

with n4:
    if st.button(
        "🔍 Verificador de boletos",
        use_container_width=True
    ):
        st.session_state["verificar_open"] = not st.session_state.get(
            "verificar_open",
            False
        )


# =========================================================
# MENÚ DEL CLIENTE
# =========================================================

with st.expander("☰ Menú de ayuda y configuración", expanded=False):
    st.write("**🤖 Asistente rápido**")
    pregunta = st.text_input("¿En qué podemos ayudarte?", placeholder="Ej.: ¿Cómo juego?", key="pregunta_cliente")
    if pregunta:
        q = pregunta.lower()
        if "jugar" in q or "compr" in q:
            respuesta = "Elige una rifa, selecciona la cantidad, completa tus datos, acepta los términos, realiza el pago y sube el comprobante."
        elif "número" in q or "boleto" in q:
            respuesta = "Tus números se asignan temporalmente al enviar la solicitud y aparecen como PENDIENTES DE VERIFICACIÓN hasta que el administrador revise el pago."
        elif "aproba" in q or "pago" in q:
            respuesta = "El administrador revisa el comprobante. El plazo informado es de 24 a 48 horas."
        elif "rechaz" in q:
            respuesta = "Si se rechaza el pago, los números temporales desaparecen de tu consulta y vuelven a estar disponibles."
        else:
            respuesta = "Puedo ayudarte con cómo jugar, comprar boletos, verificar números, pagos y estados. Si necesitas asistencia adicional, llama o escribe al 829-483-5217."
        st.success(respuesta)

    st.divider()
    st.write("**❓ Cómo jugar**")
    st.caption("1. Elige una rifa. 2. Selecciona tus boletos. 3. Completa tus datos. 4. Acepta los términos. 5. Realiza el pago y sube el comprobante. 6. Consulta tus números y su estado en 'Verificador de boletos'.")
    st.write("**🔒 Privacidad**")
    st.caption("Tus datos se utilizan para gestionar tu participación y verificar el pago.")
    st.write("**📞 Soporte humano**")
    st.caption("Si el asistente no puede resolver tu pregunta: 829-483-5217")

# =========================================================
# VERIFICADOR
# =========================================================

if st.session_state.get("verificar_open", False):
    with st.expander(
        "🔎 CONSULTAR MIS BOLETOS",
        expanded=True
    ):
        tel_ver = st.text_input(
            "Ingresa tu número de teléfono / WhatsApp registrado:"
        )

        if st.button("Consultar Ahora"):
            if tel_ver.strip():
                telefono_busqueda = normalizar_telefono(tel_ver)

                conn = conectar()

                solicitudes = conn.execute("""
                    SELECT
                        s.id,
                        s.nombre,
                        s.cantidad,
                        s.estado,
                        s.fecha_solicitud,
                        r.nombre
                    FROM solicitudes s
                    JOIN rifas r ON s.rifa_id = r.id
                    WHERE s.telefono=?
                    ORDER BY s.fecha_solicitud DESC
                """, (telefono_busqueda,)).fetchall()

                boletos = conn.execute("""
                    SELECT
                        b.numero,
                        b.estado,
                        r.nombre
                    FROM boletos b
                    JOIN rifas r ON b.rifa_id=r.id
                    WHERE b.usuario_telefono=?
                    ORDER BY r.nombre, b.numero
                """, (telefono_busqueda,)).fetchall()

                conn.close()

                if solicitudes or boletos:
                    if solicitudes:
                        st.subheader("Solicitudes")

                        for sol in solicitudes:
                            (
                                sol_id,
                                sol_nombre,
                                sol_cantidad,
                                sol_estado,
                                sol_fecha,
                                sol_rifa
                            ) = sol

                            if sol_estado == "pendiente":
                                st.warning(
                                    f"🟡 Solicitud #{sol_id} · "
                                    f"{sol_rifa} · "
                                    f"{sol_cantidad} boletos · "
                                    f"PENDIENTE DE VERIFICACIÓN"
                                )
                                st.caption(
                                    "Los números mostrados abajo están reservados temporalmente. "
                                    "Si el pago es rechazado, volverán a estar disponibles."
                                )

                            elif sol_estado == "aprobada":
                                st.success(
                                    f"🟢 Solicitud #{sol_id} · {sol_rifa} · "
                                    f"APROBADA"
                                )

                            elif sol_estado == "rechazada":
                                st.error(
                                    f"🔴 Solicitud #{sol_id} · "
                                    f"{sol_rifa} · RECHAZADA"
                                )

                    if boletos:
                        st.subheader("🎟️ Números asignados")

                        cols = st.columns(3)

                        for idx, boleto in enumerate(boletos):
                            numero, estado, rifa_nom = boleto

                            with cols[idx % 3]:
                                with st.container(border=True):
                                    st.markdown(
                                        f"🎟️ **{numero}**"
                                    )
                                    st.caption(rifa_nom)
                                    if estado == "reservado":
                                        st.warning("🟡 PENDIENTE DE VERIFICACIÓN")
                                    elif estado == "confirmado":
                                        st.success("🟢 APROBADO")
                                    else:
                                        st.write(f"Estado: **{estado.upper()}**")

                    if not boletos:
                        st.info(
                            "No tienes números activos en este momento. "
                            "Si una solicitud fue rechazada, los números temporales "
                            "fueron liberados y pueden ser asignados a otro usuario."
                        )
                else:
                    st.warning(
                        "No se encontraron solicitudes o boletos "
                        "con este número."
                    )


# =========================================================
# PRESENTACIÓN PRINCIPAL
# =========================================================

st.markdown(
    '<div class="logo-hero-container">',
    unsafe_allow_html=True
)

if os.path.exists("logo.png"):
    st.image("logo.png", width=260)
else:
    st.warning("Coloca el archivo 'logo.png' en la misma carpeta.")

st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    f"""
    <div style="text-align:center;margin-bottom:25px;">
        <p style="color:#F5C518;font-weight:bold;letter-spacing:1px;">
            EXPERIENCIA EXCLUSIVA
        </p>
        <h1 style="color:{text_color};font-size:34px;font-weight:800;">
            Premios extraordinarios garantizados
        </h1>
        <p style="color:#888888;font-size:16px;">
            Participa de forma sencilla y segura.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)


with st.expander(
    "❓ ¿CÓMO JUGAR? — 5 pasos simples",
    expanded=False
):
    st.markdown("""
    1. **Elige tu Rifa:** selecciona el premio que deseas.
    2. **Selecciona tus boletos:** elige un paquete o cantidad.
    3. **Completa tus datos:** nombre y WhatsApp.
    4. **Realiza el pago:** selecciona el banco y sube tu comprobante.
    5. **Espera la aprobación:** después de verificar el pago,
       el sistema asignará tus números automáticamente.
    """)


st.divider()


# =========================================================
# CATÁLOGO DE RIFAS ACTIVAS
# =========================================================

st.markdown(
    '<div id="rifas-activas"></div>',
    unsafe_allow_html=True
)

st.markdown(
    f"<h2 style='color:{text_color};'>🔥 Rifas Activas</h2>",
    unsafe_allow_html=True
)

conn = conectar()

rifas = conn.execute("""
    SELECT
        id,
        nombre,
        categoria,
        precio_boleto,
        min_boletos,
        total_boletos,
        imagen,
        fecha
    FROM rifas
    WHERE COALESCE(activa,1)=1
""").fetchall()

conn.close()

cols_rifas = st.columns(2)

for idx, r in enumerate(rifas):
    (
        r_id,
        r_nombre,
        r_categoria,
        r_precio,
        r_min,
        r_total,
        r_img,
        r_fecha
    ) = r

    porcentaje = obtener_porcentaje_rifa(r_id, r_total)

    with cols_rifas[idx % 2]:
        with st.container(border=True):

            if r_img and os.path.exists(r_img):
                st.image(r_img, use_container_width=True)

            st.markdown(f"### {r_nombre}")
            st.caption(
                f"Categoría: {r_categoria} | Sorteo: {r_fecha}"
            )

            st.markdown(
                f"**Precio por boleto:** "
                f"<span style='color:#f5c518;font-size:18px;'>"
                f"RD$ {r_precio:,.2f}</span>",
                unsafe_allow_html=True
            )

            st.markdown(
                f"""
                <div class="progress-text">
                    <span>Progreso de venta</span>
                    <span>{porcentaje:.2f}%</span>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.progress(porcentaje / 100.0)

            if st.button(
                "🎮 JUGAR",
                key=f"btn_jugar_{r_id}",
                use_container_width=True
            ):
                st.session_state["selected_rifa"] = r
                st.session_state["active_dialog"] = "combos"
                st.rerun()
