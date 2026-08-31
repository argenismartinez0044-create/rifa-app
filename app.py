import datetime
import os
import sqlite3
import streamlit as st

DB_FILE = "rifas_v4.db"

st.set_page_config(
    page_title="Rifas Sirio RD",
    page_icon="🎲",
    layout="wide"
)

# =========================================================
# ESTILOS CSS PERSONALIZADOS (MODO OSCURO + GLOW DEL LOGO)
# =========================================================
st.markdown("""
<style>
    /* Efecto de resplandor parpadeante dorado/plateado para el logo */
    @keyframes goldGlow {
        0% { box-shadow: 0 0 15px rgba(245, 197, 24, 0.4), 0 0 30px rgba(212, 175, 55, 0.2); }
        50% { box-shadow: 0 0 30px rgba(255, 215, 0, 0.8), 0 0 50px rgba(192, 192, 192, 0.6); }
        100% { box-shadow: 0 0 15px rgba(245, 197, 24, 0.4), 0 0 30px rgba(212, 175, 55, 0.2); }
    }
    
    .logo-hero-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 20px;
    }
    
    .logo-hero-img {
        max-width: 280px;
        border-radius: 18px;
        animation: goldGlow 3s infinite alternate;
        border: 2px solid rgba(245, 197, 24, 0.6);
    }
    
    /* Tarjetas de Combos arregladas */
    .combo-card {
        border: 1px solid #2a2e3d;
        border-radius: 12px;
        padding: 15px;
        text-align: center;
        background-color: #121620;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# BASE DE DATOS
# =========================================================

def conectar():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

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
            fecha_reserva DATETIME
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
    
    c.execute("SELECT COUNT(*) FROM metodos_pago")
    if c.fetchone()[0] == 0:
        c.executemany("""
            INSERT INTO metodos_pago (nombre, titular, tipo_cuenta, numero_cuenta, imagen, activo)
            VALUES (?,?,?,?,?,1)
        """, [
            ("Banreservas", "ARGENIS MARTINEZ C.", "Ahorros", "9606561652", "banreservas.png"),
            ("Banco Popular", "ARGENIS MARTINEZ", "Ahorros", "821794971", "popular.png"),
        ])

    c.execute("SELECT COUNT(*) FROM rifas")
    if c.fetchone()[0] == 0:
        iniciales = [
            ("PlayStation 5 Pro", "JUEGOS", 5.0, 10, 100000, "play.jpg", "Fecha pendiente"),
            ("5 iPhone 17 Pro Max", "TECNOLOGÍA", 15.0, 10, 100000, "iphone.jpg", "Al vender el 80%"),
        ]
        for rifa in iniciales:
            c.execute("""
                INSERT INTO rifas (nombre, categoria, precio_boleto, min_boletos, total_boletos, imagen, fecha, activa)
                VALUES (?,?,?,?,?,?,?,1)
            """, rifa)
        for rifa_id in (1, 2):
            numeros = [(rifa_id, f"{i:05d}") for i in range(1, 100001)]
            c.executemany("INSERT INTO boletos (rifa_id, numero) VALUES (?,?)", numeros)

    conn.commit()
    conn.close()

def guardar_imagen(uploaded, carpeta, base):
    os.makedirs(carpeta, exist_ok=True)
    ext = os.path.splitext(uploaded.name)[1].lower()
    if ext not in (".png", ".jpg", ".jpeg", ".pdf"):
        ext = ".png"
    limpio = "".join(ch if ch.isalnum() else "_" for ch in base)
    ruta = os.path.join(carpeta, f"{limpio}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}{ext}")
    with open(ruta, "wb") as f:
        f.write(uploaded.getbuffer())
    return ruta

def obtener_metodos_pago():
    conn = conectar()
    filas = conn.execute("SELECT id, nombre, titular, tipo_cuenta, numero_cuenta, imagen FROM metodos_pago WHERE COALESCE(activo,1)=1").fetchall()
    conn.close()
    return filas

def normalizar_telefono(telefono):
    return telefono.replace(" ", "").replace("-", "").replace("(", "").replace(")", "").replace("+", "").strip()

init_db()

# =========================================================
# GESTIÓN DE MODALES SECUENCIALES (SIN NIDIFICACIÓN)
# =========================================================

if "active_dialog" not in st.session_state:
    st.session_state["active_dialog"] = None
if "selected_rifa" not in st.session_state:
    st.session_state["selected_rifa"] = None
if "selected_boletos_qty" not in st.session_state:
    st.session_state["selected_boletos_qty"] = 10

@st.dialog("Elige tu paquete de números", width="large")
def modal_combos():
    rifa_datos = st.session_state["selected_rifa"]
    if not rifa_datos:
        return

    rifa_id, nombre, categoria, precio, min_boletos, total_boletos, imagen, fecha = rifa_datos

    st.markdown("<h4 style='text-align: center;'>Selecciona un paquete o elige cantidad personalizada</h4>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>A mayor cantidad, más oportunidades de ganar</p>", unsafe_allow_html=True)

    paquetes = [
        {"nombre": "ROOKIE", "boletos": 2, "icon": "🪖", "badge": None},
        {"nombre": "AMATEUR", "boletos": 5, "icon": "🏁", "badge": None},
        {"nombre": "PRO", "boletos": 10, "icon": "🚀", "badge": "⭐ POPULAR"},
        {"nombre": "ELITE", "boletos": 15, "icon": "🏆", "badge": None},
        {"nombre": "CAMPEÓN", "boletos": 25, "icon": "👑", "badge": None},
        {"nombre": "LEYENDA", "boletos": 50, "icon": "⚡", "badge": "⭐ VIP"},
        {"nombre": "MÍTICO", "boletos": 100, "icon": "🔥", "badge": "🔥 MÁXIMO"},
    ]

    col1, col2 = st.columns(2)

    for idx, pkg in enumerate(paquetes):
        col_dest = col1 if idx % 2 == 0 else col2
        with col_dest:
            costo = pkg["boletos"] * precio
            badge_html = f"<span style='background-color:#E5A93C; color:black; padding:2px 6px; border-radius:4px; font-size:11px;'>{pkg['badge']}</span><br>" if pkg['badge'] else ""
            
            st.markdown(f"""
            <div class="combo-card">
                {badge_html}
                <span style="font-size: 26px;">{pkg['icon']}</span>
                <h4 style="margin:4px 0;">{pkg['nombre']}</h4>
                <h2 style="margin:2px 0; color: #F5C518;">{pkg['boletos']}</h2>
                <p style="margin:0; font-size: 12px; color: #aaa;">NÚMEROS</p>
                <hr style="border-color:#333; margin:8px 0;">
                <strong>RD$ {costo:,.2f}</strong>
            </div>
            """, unsafe_allow_html=True)

            if st.button(f"Elegir {pkg['nombre']}", key=f"btn_pkg_{idx}", use_container_width=True):
                st.session_state["selected_boletos_qty"] = pkg["boletos"]
                st.session_state["active_dialog"] = "pago"
                st.rerun()

    st.divider()
    if st.button("✏️ ELEGIR CANTIDAD PERSONALIZADA", use_container_width=True):
        st.session_state["selected_boletos_qty"] = min_boletos
        st.session_state["active_dialog"] = "pago"
        st.rerun()

@st.dialog("Completa tu compra de boletos", width="large")
def modal_pago_detalles():
    rifa_datos = st.session_state["selected_rifa"]
    if not rifa_datos:
        return

    rifa_id, nombre, categoria, precio, min_boletos, total_boletos, imagen, fecha = rifa_datos

    st.markdown(f"### {nombre}")
    st.caption("TU PARTICIPACIÓN · CÓMO QUIERES PARTICIPAR")

    modo_p = st.radio("Modo", ["PAQUETES", "CANTIDAD LIBRE"], horizontal=True, label_visibility="collapsed")

    if modo_p == "CANTIDAD LIBRE":
        st.caption(f"Selección aleatoria del sistema. (Mínimo: {min_boletos})")
        c1, c2, c3 = st.columns([1, 2, 1])
        with c1:
            if st.button("➖", use_container_width=True):
                if st.session_state["selected_boletos_qty"] > min_boletos:
                    st.session_state["selected_boletos_qty"] -= 1
                    st.rerun()
        with c2:
            st.markdown(f"<h2 style='text-align: center;'>{st.session_state['selected_boletos_qty']}</h2>", unsafe_allow_html=True)
        with c3:
            if st.button("➕", use_container_width=True):
                st.session_state["selected_boletos_qty"] += 1
                st.rerun()

    cant_final = st.session_state["selected_boletos_qty"]
    total_pagar = cant_final * precio

    st.markdown(f"### TOTAL A PAGAR: **RD$ {total_pagar:,.2f}**")
    st.caption(f"Compra mínima: {min_boletos} boletos · Máximo: 10,000 por usuario")

    st.info("ℹ️ Los números de boletos se **asignarán automáticamente al azar** tras validar tu pago. ¡Mayor cantidad = más oportunidades de ganar!")

    st.divider()

    nombre_c = st.text_input("Nombre *", placeholder="Ej: Juan Pérez")
    telefono_c = st.text_input("Teléfono (WhatsApp) *", placeholder="+1 (829) 000-0000")
    correo_c = st.text_input("Correo electrónico (opcional)", placeholder="correo@ejemplo.com")

    st.divider()

    st.markdown("#### Banco a transferir *")
    st.caption("Selecciona el banco al que transferirás para ver el número de cuenta y titular.")

    metodos = obtener_metodos_pago()
    banco_seleccionado = None

    if "banco_activo_id" not in st.session_state:
        st.session_state["banco_activo_id"] = None

    cols = st.columns(len(metodos) if metodos else 1)
    for idx, m in enumerate(metodos):
        m_id, m_nombre, m_titular, m_tipo, m_cuenta, m_img = m
        with cols[idx]:
            if st.button(f"🏦 {m_nombre}", key=f"btn_banco_{m_id}", use_container_width=True):
                st.session_state["banco_activo_id"] = m_id

    if st.session_state["banco_activo_id"]:
        banco_sel = next((m for m in metodos if m[0] == st.session_state["banco_activo_id"]), None)
        if banco_sel:
            st.success(f"**Cuenta {banco_sel[1]}**")
            st.write(f"📌 **Titular:** {banco_sel[2]}")
            st.write(f"📌 **Tipo:** {banco_sel[3]}")
            st.code(banco_sel[4], language=None)
            banco_seleccionado = banco_sel[1]

    st.divider()

    comprobante_file = st.file_uploader("Haz clic para subir tu comprobante (JPG, PNG o PDF)", type=["png", "jpg", "jpeg", "pdf"])
    acepta = st.toggle("Confirmo que mis datos son correctos. Se enviarán correos de confirmación y seguimiento.")

    listo = bool(nombre_c and telefono_c and banco_seleccionado and comprobante_file and acepta)

    if st.button("🛒 CONFIRMAR COMPRA", disabled=not listo, use_container_width=True):
        conn = conectar()
        c = conn.cursor()

        c.execute("SELECT id FROM boletos WHERE rifa_id=? AND estado='disponible' LIMIT ?", (rifa_id, cant_final))
        disponibles = c.fetchall()

        if len(disponibles) < cant_final:
            st.error("No hay suficientes boletos disponibles en este momento.")
            conn.close()
        else:
            ruta_comp = guardar_imagen(comprobante_file, "comprobantes", telefono_c)
            ids = [b[0] for b in disponibles]

            c.executemany("""
                UPDATE boletos
                SET estado='reservado',
                    usuario_nombre=?,
                    usuario_telefono=?,
                    metodo_pago=?,
                    comprobante=?,
                    fecha_reserva=?
                WHERE id=?
            """, [
                (nombre_c, normalizar_telefono(telefono_c), banco_seleccionado, ruta_comp, datetime.datetime.now(), bid)
                for bid in ids
            ])
            conn.commit()
            conn.close()

            st.session_state["active_dialog"] = None
            st.success("🎉 ¡Solicitud recibida correctamente!")
            st.warning("⏳ Tus boletos están en proceso de revisión. La validación toma entre 24 horas para ser aprobados. ¡Mucho éxito!")

# Control de renderizado de modales
if st.session_state["active_dialog"] == "combos":
    modal_combos()
elif st.session_state["active_dialog"] == "pago":
    modal_pago_detalles()

# =========================================================
# VISTA PRINCIPAL CON HERO SECTION Y LOGO SIRIO RD
# =========================================================

# Barra Superior / Navegación
top_c1, top_c2, top_c3, top_c4 = st.columns([3, 1, 1, 2])
with top_c1:
    st.markdown("### 🎲 **RIFAS SIRIO RD**")
with top_c2:
    if st.button("📋 Rifas", use_container_width=True):
        pass
with top_c3:
    if st.button("🏆 Ganadores", use_container_width=True):
        st.info("Próximamente sección de ganadores.")
with top_c4:
    if st.button("🔍 Verificar boleto", use_container_width=True):
        st.session_state["verificar_open"] = not st.session_state.get("verificar_open", False)

if st.session_state.get("verificar_open", False):
    with st.expander("🔎 Verificador de Boletos", expanded=True):
        tel_ver = st.text_input("Ingresa tu teléfono para buscar tus boletos:")
        if st.button("Consultar"):
            conn = conectar()
            res = conn.execute("SELECT numero, estado, rifa_id FROM boletos WHERE usuario_telefono=?", (normalizar_telefono(tel_ver),)).fetchall()
            conn.close()
            if res:
                st.write(f"Boletos encontrados: {len(res)}")
                for b in res:
                    st.write(f"• Número: **{b[0]}** | Estado: `{b[1]}`")
            else:
                st.warning("No se encontraron boletos asociados a ese número.")

st.divider()

# Hero Section Centrada con el Logo Sirio RD y Glow
st.markdown("""
<div class="logo-hero-container">
    <div style="text-align: center;">
        <h1 style="color: #F5C518; font-size: 42px; font-weight: 800; margin-bottom: 5px;">RIFAS SIRIO RD</h1>
        <p style="color: #E0E0E0; font-size: 18px; margin-bottom: 15px;">Experiencia exclusiva · La plataforma más lujosa para participar y ganar.</p>
        <h2 style="color: #FFFFFF; font-size: 32px; font-weight: 700; margin-bottom: 25px;">Premios extraordinarios garantizados</h2>
    </div>
</div>
""", unsafe_allow_html=True)

# Sección de "¿Cómo Jugar?" (Desplegable o información)
with st.expander("❓ ¿CÓMO JUGAR? — 5 pasos simples para participar y ganar", expanded=False):
    st.markdown("""
    1. **Selecciona tu Rifa:** Elige la rifa activa de tu preferencia.
    2. **Elige tu Paquete:** Selecciona un combo de boletos o ingresa una cantidad libre.
    3. **Ingresa tus Datos:** Completa tu nombre y WhatsApp de contacto.
    4. **Realiza la Transferencia:** Transfiere al banco seleccionado y adjunta el comprobante.
    5. **¡Listo!:** Tus boletos serán asignados al azar y puestos en revisión (máx. 24 horas).
    """)

st.divider()

# Catálogo de Rifas (Ubicado más abajo)
st.subheader("🔥 Rifas Activas")

conn = conectar()
rifas = conn.execute("SELECT id, nombre, categoria, precio_boleto, min_boletos, total_boletos, imagen, fecha FROM rifas WHERE COALESCE(activa,1)=1").fetchall()
conn.close()

col_rifas = st.columns(2)
for idx, r in enumerate(rifas):
    with col_rifas[idx % 2]:
        with st.container(border=True):
            if r[6] and os.path.exists(r[6]):
                st.image(r[6], use_container_width=True)
            else:
                st.markdown("### 🎲 Rifa Exclusiva")
            
            st.markdown(f"### {r[1]}")
            st.caption(f"Categoría: {r[2]} | Sorteo: {r[7]}")
            st.markdown(f"**Precio por boleto:** RD$ {r[3]:,.2f}")

            if st.button("🎟️ QUIERO PARTICIPAR", key=f"part_hero_{r[0]}", use_container_width=True):
                st.session_state["selected_rifa"] = r
                st.session_state["active_dialog"] = "combos"
                st.rerun()
