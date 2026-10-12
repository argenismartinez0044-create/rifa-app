import datetime
import os
import sqlite3
import base64
import streamlit as st
import streamlit.components.v1 as components

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
    /* Oculta elementos de marca/interfaz de Streamlit en la vista pública. */
    #MainMenu {{visibility: hidden !important;}}
    footer {{display: none !important; visibility: hidden !important;}}
    header {{visibility: hidden !important;}}
    #stDecoration,
    .stDeployButton,
    [data-testid="stAppDeployButton"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"],
    .viewerBadge_container,
    .viewerBadge_container__1QSob,
    a[href*="streamlit.io"] {{
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }}

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

    /* Animaciones sutiles de marca e imágenes */
    @keyframes haloAzul {{
        0% {{ box-shadow: 0 0 5px rgba(56,189,248,.45), 0 0 12px rgba(255,255,255,.2); }}
        50% {{ box-shadow: 0 0 18px rgba(56,189,248,.95), 0 0 28px rgba(255,255,255,.65); }}
        100% {{ box-shadow: 0 0 5px rgba(56,189,248,.45), 0 0 12px rgba(255,255,255,.2); }}
    }}
    @keyframes bordeLuz {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    .logo-lightning {{
        position: relative;
        display: flex;
        align-items: center;
        justify-content: center;
        width: fit-content;
        max-width: 100%;
        margin: 12px auto;
        padding: 5px;
        border-radius: 18px;
        animation: haloAzul 2.4s ease-in-out infinite;
    }}
    .logo-lightning img {{ display:block; max-width:100%; height:auto; border-radius:12px; }}
    .stApp div[data-testid="stImage"] img {{
        transition: transform .22s ease, filter .22s ease;
    }}
    .stApp div[data-testid="stImage"] img:hover {{
        transform: scale(1.035);
        filter: drop-shadow(0 0 7px rgba(56,189,248,.35));
    }}
    div.st-key-btn_ayuda button {{
        position: fixed !important;
        right: 24px !important;
        bottom: 24px !important;
        z-index: 999 !important;
        width: 76px !important;
        height: 76px !important;
        min-height: 76px !important;
        border-radius: 50% !important;
        border: 2px solid #ffe08a !important;
        background: radial-gradient(circle at 30% 25%, #fff1b8, #d4af37 55%, #8b6914) !important;
        color: #101010 !important;
        font-weight: 800 !important;
        white-space: normal !important;
        line-height: 1.05 !important;
        padding: 7px !important;
        animation: haloAzul 2s ease-in-out infinite;
    }}
    .bank-card-button button {{
        width: 100%;
        min-height: 92px;
        border: 1px solid #334155;
        border-radius: 12px;
    }}
    .bank-card-button button:hover {{
        border-color: #38bdf8;
        box-shadow: 0 0 14px rgba(56,189,248,.35);
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
    agregar_columna_si_no_existe(conn, "rifas", "descripcion", "TEXT DEFAULT ''")

    # Actualiza los precios y las descripciones también en bases de datos existentes.
    c.execute("""
        UPDATE rifas
        SET precio_boleto=5, min_boletos=20,
            descripcion='Compra mínima: 20 boletos. Primer ganador: una PlayStation 5 Pro. Segundo ganador: quince mil pesos (RD$15,000) en efectivo. Tercer ganador: diez mil pesos (RD$10,000) en efectivo.'
        WHERE LOWER(nombre) LIKE '%playstation%'
    """)
    c.execute("""
        UPDATE rifas
        SET precio_boleto=15, min_boletos=10,
            descripcion='Rifa de 5 iPhone 17 Pro Max. Compra un mínimo de 10 boletos; puedes comprar 10 o más.'
        WHERE LOWER(nombre) LIKE '%iphone%'
    """)

    c.execute("SELECT COUNT(*) FROM metodos_pago")
    if c.fetchone()[0] == 0:
        c.executemany("""
            INSERT INTO metodos_pago
            (nombre, titular, tipo_cuenta, numero_cuenta, imagen, activo)
            VALUES (?,?,?,?,?,1)
        """, [
            ("Banreservas", "Ariel Martínez", "Ahorro", "9606561652", "banreservas.png"),
            ("Banco Popular", "Ariel Martínez", "Ahorro", "821794971", "popular.png")
        ])

    # Mantiene los datos indicados para las cuentas bancarias principales.
    c.execute("""
        UPDATE metodos_pago
        SET titular='Ariel Martínez', tipo_cuenta='Ahorro'
        WHERE LOWER(nombre) LIKE '%banreservas%'
           OR LOWER(nombre) LIKE '%popular%'
    """)

    c.execute("SELECT COUNT(*) FROM rifas")
    if c.fetchone()[0] == 0:
        iniciales = [
            ("PlayStation 5 Pro", "JUEGOS", 5.0, 20, 10000, "play.jpg", "Fecha pendiente"),
            ("5 iPhone 17 Pro Max", "TECNOLOGÍA", 15.0, 10, 10000, "iphone.jpg", "Al vender el 80%")
        ]

        for rifa in iniciales:
            c.execute("""
                INSERT INTO rifas
                (nombre, categoria, precio_boleto, min_boletos, total_boletos, imagen, fecha, activa)
                VALUES (?,?,?,?,?,?,?,1)
            """, rifa)

        c.execute("""
            UPDATE rifas SET descripcion=?
            WHERE LOWER(nombre) LIKE '%playstation%'
        """, ("Compra mínima: 20 boletos. Primer ganador: una PlayStation 5 Pro. Segundo ganador: quince mil pesos (RD$15,000) en efectivo. Tercer ganador: diez mil pesos (RD$10,000) en efectivo.",))
        c.execute("""
            UPDATE rifas SET descripcion=?
            WHERE LOWER(nombre) LIKE '%iphone%'
        """, ("Rifa de 5 iPhone 17 Pro Max. Compra un mínimo de 10 boletos; puedes comprar 10 o más.",))

        for rifa_id in (1, 2):
            numeros = [(rifa_id, f"{i:05d}") for i in range(1, 10001)]
            c.executemany(
                "INSERT INTO boletos (rifa_id, numero) VALUES (?,?)",
                numeros
            )

    conn.commit()
    conn.close()


def mostrar_logo(ancho=220):
    """Muestra el logo con un halo azul/blanco animado, sin marcas adicionales."""
    if os.path.exists("logo.png"):
        with open("logo.png", "rb") as archivo_logo:
            imagen_codificada = base64.b64encode(archivo_logo.read()).decode("utf-8")
        st.markdown(
            f'<div class="logo-lightning"><img src="data:image/png;base64,{imagen_codificada}" '
            f'alt="Logo Rifas Sirio RD" style="width:{ancho}px;"></div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown("## 🎲 RIFAS SIRIO RD")


def ocultar_telefono(telefono):
    digitos = "".join(ch for ch in str(telefono) if ch.isdigit())
    if len(digitos) >= 10:
        digitos = digitos[-10:]
        return "******" + digitos[-4:]
    if len(digitos) > 4:
        return "*" * (len(digitos) - 4) + digitos[-4:]
    return "*" * len(digitos)


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
    "ayuda_open": False,
    "compra_numeros": [],
    "compra_rifa_nombre": "",
    "solo_numeros_compra": False,
    "solo_numeros_verificador": False,
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
    mostrar_logo(180)

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
        {"nombre": "INICIAL", "boletos": 20, "icon": "🎟️"},
        {"nombre": "CAMPEÓN", "boletos": 25, "icon": "👑"},
        {"nombre": "LEYENDA", "boletos": 50, "icon": "⚡"},
        {"nombre": "MÍTICO", "boletos": 100, "icon": "🔥"}
    ]

    paquetes = [pkg for pkg in paquetes if pkg["boletos"] >= min_boletos]
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

    # Evita que una cantidad guardada de otra rifa quede por debajo del mínimo.
    if st.session_state["selected_boletos_qty"] < min_boletos:
        st.session_state["selected_boletos_qty"] = min_boletos

    st.markdown(f"### {nombre}")
    st.caption(f"Compra mínima: {min_boletos} boletos.")

    # El contador siempre aparece después de elegir un paquete.
    # El cliente puede ajustar la cantidad, pero nunca bajar del mínimo de la rifa.
    cantidad_actual = st.session_state["selected_boletos_qty"]
    c1, c2, c3 = st.columns([1, 2, 1])

    with c1:
        if st.button(
            "➖",
            key=f"restar_boleto_{rifa_id}",
            use_container_width=True,
            disabled=cantidad_actual <= min_boletos
        ):
            st.session_state["selected_boletos_qty"] = max(
                min_boletos, cantidad_actual - 1
            )
            st.rerun()

    with c2:
        st.markdown(
            f"<div style='text-align:center;'>"
            f"<div style='font-size:13px;color:#9ca3af;'>Cantidad de boletos</div>"
            f"<h2 style='color:#f5c518;margin:2px 0;'>{cantidad_actual}</h2>"
            f"</div>",
            unsafe_allow_html=True
        )

    with c3:
        if st.button(
            "➕",
            key=f"sumar_boleto_{rifa_id}",
            use_container_width=True,
            disabled=cantidad_actual >= 10000
        ):
            st.session_state["selected_boletos_qty"] = min(
                10000, cantidad_actual + 1
            )
            st.rerun()

    cantidad = st.session_state["selected_boletos_qty"]
    total_pagar = cantidad * precio

    st.markdown(f"### TOTAL A PAGAR: **RD$ {total_pagar:,.2f}**")

    st.info(
        "Al enviar tu compra, el sistema asignará tus números al azar y los mostrará "
        "como **En verificación** mientras revisamos el comprobante. "
        "La confirmación puede tardar entre 24 y 48 horas."
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

    if metodos:
        cols_bancos = st.columns(min(len(metodos), 3))
        for idx, m in enumerate(metodos):
            m_id, m_nombre, m_titular, m_tipo, m_cuenta, m_img = m
            es_seleccionado = st.session_state.get("banco_activo_id") == m_id

            with cols_bancos[idx % len(cols_bancos)]:
                # El control para seleccionar el banco queda justo debajo de su logo.
                if m_img and os.path.exists(m_img):
                    st.image(m_img, width=120)
                else:
                    st.markdown(f"### 🏦 {m_nombre}")

                if st.button(
                    f"✓ {m_nombre}" if es_seleccionado else f"Seleccionar {m_nombre}",
                    key=f"btn_card_{m_id}",
                    use_container_width=True,
                    type="primary" if es_seleccionado else "secondary"
                ):
                    st.session_state["banco_activo_id"] = m_id
                    st.rerun()

    else:
        st.warning("No hay métodos de pago activos en este momento.")

    if st.session_state.get("banco_activo_id"):
        banco_sel = next(
            (m for m in metodos if m[0] == st.session_state["banco_activo_id"]),
            None
        )

        if banco_sel:
            banco_seleccionado = banco_sel[1]
            st.markdown(f"#### Datos de {banco_sel[1]}")

            st.markdown(
                f"**Titular:** {banco_sel[2]}  \n"
                f"**Tipo de cuenta:** {banco_sel[3]}",
            )

            cuenta_col, copiar_col = st.columns([4, 1])
            with cuenta_col:
                st.text_input(
                    "Número de cuenta",
                    value=str(banco_sel[4]),
                    disabled=True,
                    key=f"cuenta_visible_{banco_sel[0]}"
                )
            with copiar_col:
                st.markdown("<div style='height:27px'></div>", unsafe_allow_html=True)
                # Botón real dentro de un pequeño componente para copiar al portapapeles.
                cuenta_segura = str(banco_sel[4]).replace("\\", "\\\\").replace("'", "\\'")
                components.html(
                    f"""
                    <button onclick="navigator.clipboard.writeText('{cuenta_segura}').then(() => {{
                        this.innerText = 'Copiado';
                    }}).catch(() => {{
                        this.innerText = 'Selecciona el número';
                    }});"
                    style="width:100%;padding:8px 6px;border:1px solid #64748b;
                    border-radius:8px;background:#172033;color:white;cursor:pointer;">
                    📋 Copiar
                    </button>
                    """,
                    height=44
                )

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
        "🛒 COMPRAR BOLETOS",
        disabled=not listo,
        use_container_width=True
    ):
        if cantidad < min_boletos:
            st.error(f"Debes comprar al menos {min_boletos} boletos en esta rifa.")
            return

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

        st.session_state["compra_numeros"] = sorted(numeros)
        st.session_state["compra_rifa_nombre"] = nombre
        st.session_state["solo_numeros_compra"] = False
        st.session_state["active_dialog"] = "resultado_compra"
        st.session_state["banco_activo_id"] = None
        st.rerun()


# =========================================================
# VENTANAS DE RESULTADO, AYUDA Y VERIFICADOR
# =========================================================

@st.dialog("Compra registrada", width="large")
def modal_resultado_compra():
    numeros = st.session_state.get("compra_numeros", [])
    if st.session_state.get("solo_numeros_compra"):
        st.markdown("### Solo números")
        st.code(" · ".join(numeros) if numeros else "No hay números guardados.")
    else:
        st.success("Tu solicitud fue recibida correctamente.")
        st.write(f"**Rifa:** {st.session_state.get('compra_rifa_nombre', '')}")
        st.info("Tus boletos están **En verificación**. La revisión del pago puede tardar entre 24 y 48 horas.")
        st.markdown("### 🎟️ Números asignados")
        if numeros:
            cols = st.columns(4)
            for i, numero in enumerate(numeros):
                with cols[i % 4]:
                    with st.container(border=True):
                        st.markdown(f"### {numero}")
                        st.warning("En verificación")
    b1, b2 = st.columns(2)
    with b1:
        if st.button("Solo números", key="solo_numeros_compra_btn", use_container_width=True):
            st.session_state["solo_numeros_compra"] = not st.session_state.get("solo_numeros_compra", False)
            st.rerun()
    with b2:
        if st.button("Cerrar", key="cerrar_resultado_compra", use_container_width=True):
            st.session_state["active_dialog"] = None
            st.rerun()


@st.dialog("¿Necesitas ayuda?", width="small")
def modal_ayuda():
    st.write("Te llevaremos a WhatsApp para que puedas escribir a nuestro equipo de soporte.")
    if st.button("Cómo jugar", key="boton_como_jugar_ayuda", use_container_width=True):
        st.session_state["mostrar_pasos_ayuda"] = not st.session_state.get("mostrar_pasos_ayuda", False)
        st.rerun()
    if st.session_state.get("mostrar_pasos_ayuda", False):
        st.markdown(
            "1. Elige una rifa activa.\n"
            "2. Selecciona un paquete o la cantidad que deseas comprar.\n"
            "3. Completa tu nombre y teléfono.\n"
            "4. Selecciona el banco y realiza el pago.\n"
            "5. Sube el comprobante y acepta los términos.\n"
            "6. Pulsa **Comprar boletos**. Guarda los números asignados y consulta su estado.\n"
            "7. Los números estarán **En verificación** hasta que el administrador apruebe el pago; puede tardar de 24 a 48 horas."
        )
    a1, a2 = st.columns(2)
    with a1:
        if st.button("Cancelar", key="cerrar_ayuda", use_container_width=True):
            st.session_state["ayuda_open"] = False
            st.rerun()
    with a2:
        st.link_button("Abrir WhatsApp", "https://wa.me/18294835217", use_container_width=True)


@st.dialog("🔎 Verificador", width="large")
def modal_verificador():
    st.write("Elige la rifa e ingresa tu teléfono (10 números) o el número de boleto.")
    conn = conectar()
    rifas_disponibles = conn.execute("SELECT id, nombre FROM rifas ORDER BY nombre").fetchall()
    conn.close()
    if not rifas_disponibles:
        st.warning("No hay rifas registradas.")
        return
    nombres_rifas = {nombre: rid for rid, nombre in rifas_disponibles}
    rifa_nombre = st.selectbox("Selecciona una rifa", list(nombres_rifas.keys()), key="verificador_rifa")
    busqueda = st.text_input("Teléfono (10 números) o número de boleto", key="verificador_busqueda")
    if st.button("Consultar", key="btn_consultar_verificador", use_container_width=True):
        conn = conectar()
        rifa_id = nombres_rifas[rifa_nombre]
        busqueda_limpia = normalizar_telefono(busqueda)
        digitos = "".join(ch for ch in busqueda_limpia if ch.isdigit())
        resultados = []
        if len(digitos) >= 10:
            telefono = digitos[-10:]
            resultados = conn.execute("""
                SELECT b.numero, b.estado, b.usuario_nombre, b.usuario_telefono,
                       b.solicitud_id, b.fecha_reserva, s.fecha_solicitud
                FROM boletos b
                LEFT JOIN solicitudes s ON s.id=b.solicitud_id
                WHERE b.rifa_id=?
                  AND (b.usuario_telefono=? OR b.usuario_telefono LIKE '%' || ?)
                  AND b.estado IN ('reservado','confirmado')
                ORDER BY b.numero
            """, (rifa_id, telefono, telefono)).fetchall()
            st.session_state["solo_numeros_verificador"] = False
            st.session_state["verificador_resultados"] = resultados
            st.session_state["verificador_modo"] = "telefono"
        elif busqueda.strip():
            numero = busqueda.strip()
            if numero.isdigit() and len(numero) <= 5:
                numero = numero.zfill(5)
            resultado = conn.execute("""
                SELECT b.numero, b.estado, b.usuario_nombre, b.usuario_telefono,
                       b.solicitud_id, b.fecha_reserva, s.fecha_solicitud
                FROM boletos b
                LEFT JOIN solicitudes s ON s.id=b.solicitud_id
                WHERE b.rifa_id=? AND b.numero=?
                LIMIT 1
            """, (rifa_id, numero)).fetchone()
            st.session_state["verificador_resultados"] = [resultado] if resultado else []
            st.session_state["solo_numeros_verificador"] = False
            st.session_state["verificador_modo"] = "boleto"
        else:
            st.session_state["verificador_resultados"] = []
            st.warning("Escribe un teléfono o un número de boleto.")
        conn.close()
        st.rerun()

    resultados = st.session_state.get("verificador_resultados", [])
    if resultados:
        modo = st.session_state.get("verificador_modo", "telefono")
        if st.session_state.get("solo_numeros_verificador"):
            st.subheader("Solo números")
            st.code(" · ".join(str(x[0]) for x in resultados))
        elif modo == "telefono":
            st.subheader("Todos tus números en esta rifa")
            st.caption("Los números pendientes aparecerán como En verificación y los confirmados como Aprobados.")
            cols = st.columns(4)
            for i, fila in enumerate(resultados):
                numero, estado, nombre, telefono, orden, fecha_reserva, fecha_solicitud = fila
                with cols[i % 4]:
                    with st.container(border=True):
                        st.markdown(f"### {numero}")
                        if estado == "confirmado":
                            st.success("Aprobados")
                        else:
                            st.warning("En verificación")
        else:
            numero, estado, nombre, telefono, orden, fecha_reserva, fecha_solicitud = resultados[0]
            if estado == "disponible" or not nombre:
                st.info(f"El boleto {numero} aún no se le ha asignado a nadie.")
            else:
                st.markdown(f"### Boleto {numero} · Adquirido")
                st.write(f"**# de orden:** {orden if orden else 'Pendiente de registro'}")
                st.write(f"**Nombre del participante:** {nombre}")
                st.write(f"**Teléfono:** {ocultar_telefono(telefono)}")
                st.write(f"**Fecha de registro:** {fecha_solicitud or fecha_reserva or 'No disponible'}")
                st.write(f"**Estado:** {'Aprobados' if estado == 'confirmado' else 'En verificación'}")
    elif "verificador_resultados" in st.session_state:
        if st.session_state.get("verificador_busqueda", "").strip():
            st.info("No se encontraron boletos asignados con esos datos para esta rifa.")

    if st.session_state.get("verificador_resultados"):
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Solo números", key="verificador_solo_numeros", use_container_width=True):
                st.session_state["solo_numeros_verificador"] = not st.session_state.get("solo_numeros_verificador", False)
                st.rerun()
        with c2:
            if st.button("Cerrar verificador", key="cerrar_verificador", use_container_width=True):
                st.session_state["verificar_open"] = False
                st.session_state.pop("verificador_resultados", None)
                st.rerun()


if st.session_state["active_dialog"] == "combos":
    modal_combos()
elif st.session_state["active_dialog"] == "pago":
    modal_pago_detalles()
elif st.session_state["active_dialog"] == "resultado_compra":
    modal_resultado_compra()

if st.session_state.get("ayuda_open", False):
    modal_ayuda()
if st.session_state.get("verificar_open", False):
    modal_verificador()


# =========================================================
# BARRA SUPERIOR
# =========================================================

n1, n2, n3, n4 = st.columns([2, 1, 1, 2])

with n1:
    mostrar_logo(140)

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
    if st.button("🔎 Verificador de boletos", use_container_width=True):
        st.session_state["verificar_open"] = True
        st.rerun()


if st.button("¿Necesitas\nayuda?", key="btn_ayuda", help="Abrir ayuda y soporte"):
    st.session_state["ayuda_open"] = True
    st.rerun()


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

# El verificador se presenta en una ventana modal definida anteriormente.


# =========================================================
# PRESENTACIÓN PRINCIPAL
# =========================================================

mostrar_logo(260)

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
    5. **Pulsa Comprar boletos:** el sistema asignará números al azar al enviar la solicitud.
    6. **Verificación:** tus números aparecerán como En verificación durante 24 a 48 horas.
    7. **Aprobación:** al aprobar el pago, los números cambiarán a Aprobados.
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

descripciones = dict(conn.execute(
    "SELECT id, COALESCE(descripcion, '') FROM rifas"
).fetchall())

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
            if descripciones.get(r_id):
                st.write(descripciones[r_id])
            st.caption(f"Compra mínima: {r_min} boletos.")

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
