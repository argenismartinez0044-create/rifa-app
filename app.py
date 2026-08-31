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

# Paleta de colores y fondo dinámico
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
# ESTILOS CSS PERSONALIZADOS Y TARJETAS DE BANCOS COMPACTAS
# =========================================================
st.markdown(f"""
<style>
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

    .bcrd-seal {{
        position: absolute;
        top: 15px;
        right: 15px;
        width: 50px;
        opacity: 0.9;
    }}

    .badge-pop {{
        background: linear-gradient(90deg, #f5c518, #ff8c00);
        color: #000;
        font-weight: bold;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
    }}

    /* Estilos específicos ÚNICAMENTE para ocultar el botón transparente de las tarjetas de banco */
    .bank-card-wrapper div[data-testid="stButton"] button {{
        background: transparent !important;
        border: none !important;
        color: transparent !important;
        box-shadow: none !important;
        height: 110px !important;
        width: 135px !important;
        padding: 0 !important;
    }}

    /* Estilos visuales exactos a la Imagen 2 para las tarjetas de banco */
    .bank-card-btn {{
        background-color: #131927;
        border: 1.5px solid #2a364f;
        border-radius: 12px;
        padding: 12px 8px;
        width: 135px;
        height: 110px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        transition: all 0.2s ease-in-out;
    }}
    .bank-card-btn:hover {{
        border-color: #38bdf8;
        background-color: #1e293b;
    }}
    .bank-card-selected {{
        border: 2px solid #38bdf8 !important;
        background-color: #172554 !important;
        box-shadow: 0 0 10px rgba(56, 189, 248, 0.3);
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

    /* Indicador de porcentaje */
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
            ("PlayStation 5 Pro", "JUEGOS", 5.0, 10, 10000, "play.jpg", "Fecha pendiente"),
            ("5 iPhone 17 Pro Max", "TECNOLOGÍA", 15.0, 10, 10000, "iphone.jpg", "Al vender el 80%"),
        ]
        for rifa in iniciales:
            c.execute("""
                INSERT INTO rifas (nombre, categoria, precio_boleto, min_boletos, total_boletos, imagen, fecha, activa)
                VALUES (?,?,?,?,?,?,?,1)
            """, rifa)
        for rifa_id in (1, 2):
            numeros = [(rifa_id, f"{i:05d}") for i in range(1, 10001)]
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

def obtener_progreso_rifa(rifa_id, total_boletos):
    conn = conectar()
    vendidos = conn.execute("SELECT COUNT(*) FROM boletos WHERE rifa_id=? AND estado!='disponible'", (rifa_id,)).fetchone()[0]
    conn.close()
    
    total = total_boletos if total_boletos and total_boletos > 0 else 10000
    porcentaje = min(100.0, (vendidos / total) * 100)
    return vendidos, total, porcentaje

init_db()

# =========================================================
# ESTADOS Y MODALES
# =========================================================

if "active_dialog" not in st.session_state:
    st.session_state["active_dialog"] = None
if "selected_rifa" not in st.session_state:
    st.session_state["selected_rifa"] = None
if "selected_boletos_qty" not in st.session_state:
    st.session_state["selected_boletos_qty"] = 10
if "banco_activo_id" not in st.session_state:
    st.session_state["banco_activo_id"] = None

@st.dialog("Elige tu paquete de números", width="large")
def modal_combos():
    rifa_datos = st.session_state["selected_rifa"]
    if not rifa_datos:
        return

    rifa_id, nombre, categoria, precio, min_boletos, total_boletos, imagen, fecha = rifa_datos

    st.markdown("<h3 style='text-align: center;'>Selecciona un paquete o elige cantidad personalizada</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #f5c518;'>A mayor cantidad, más oportunidades de ganar</p>", unsafe_allow_html=True)

    paquetes = [
        {"nombre": "ROOKIE", "boletos": 2, "icon": "🪖", "badge": ""},
        {"nombre": "AMATEUR", "boletos": 5, "icon": "🏁", "badge": ""},
        {"nombre": "PRO", "boletos": 10, "icon": "🚀", "badge": "⭐ POPULAR"},
        {"nombre": "ELITE", "boletos": 15, "icon": "🏆", "badge": ""},
        {"nombre": "CAMPEÓN", "boletos": 25, "icon": "👑", "badge": ""},
        {"nombre": "LEYENDA", "boletos": 50, "icon": "⚡", "badge": "⭐ VIP"},
        {"nombre": "MÍTICO", "boletos": 100, "icon": "🔥", "badge": "🔥 MÁXIMO"},
    ]

    col1, col2 = st.columns(2)

    for idx, pkg in enumerate(paquetes):
        col_dest = col1 if idx % 2 == 0 else col2
        with col_dest:
            with st.container(border=True):
                if pkg["badge"]:
                    st.markdown(f'<span class="badge-pop">{pkg["badge"]}</span>', unsafe_allow_html=True)
                
                st.markdown(f"### {pkg['icon']} {pkg['nombre']}")
                st.markdown(f"## {pkg['boletos']} <small style='font-size:14px;'>NÚMEROS</small>", unsafe_allow_html=True)
                costo = pkg["boletos"] * precio
                st.markdown(f"**RD$ {costo:,.2f}**")

                if st.button(f"Elegir {pkg['nombre']}", key=f"btn_pkg_{idx}", use_container_width=True):
                    st.session_state["selected_boletos_qty"] = pkg["boletos"]
                    st.session_state["banco_activo_id"] = None  # Banco oculto al inicio
                    st.session_state["active_dialog"] = "pago"
                    st.rerun()

    st.divider()
    if st.button("✏️ ELEGIR CANTIDAD PERSONALIZADA", use_container_width=True):
        st.session_state["selected_boletos_qty"] = min_boletos
        st.session_state["banco_activo_id"] = None  # Banco oculto al inicio
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
            if st.button("➖", key="btn_minus_qty", use_container_width=True):
                if st.session_state["selected_boletos_qty"] > min_boletos:
                    st.session_state["selected_boletos_qty"] -= 1
                    st.rerun()
        with c2:
            st.markdown(f"<h2 style='text-align: center; color: #f5c518;'>{st.session_state['selected_boletos_qty']}</h2>", unsafe_allow_html=True)
        with c3:
            if st.button("➕", key="btn_plus_qty", use_container_width=True):
                st.session_state["selected_boletos_qty"] += 1
                st.rerun()

    cant_final = st.session_state["selected_boletos_qty"]
    total_pagar = cant_final * precio

    st.markdown(f"### TOTAL A PAGAR: **RD$ {total_pagar:,.2f}**")
    st.caption(f"Compra mínima: {min_boletos} boletos · Máximo: 10,000 por usuario")

    st.info("ℹ️ Los números de boletos se **asignarán automáticamente al azar** tras validar tu pago.")

    st.divider()

    nombre_c = st.text_input("Nombre completo *", placeholder="Ej: Juan Pérez")
    telefono_c = st.text_input("Teléfono (WhatsApp) *", placeholder="+1 (829) 000-0000")

    st.divider()

    # =========================================================
    # SELECCIÓN DE BANCOS CON EL DISEÑO EXACTO A LA IMAGEN 2
    # =========================================================
    st.markdown("#### Método de Pago *")

    metodos = obtener_metodos_pago()
    banco_seleccionado = None

    cols_bancos = st.columns(len(metodos) if metodos else 1)

    for idx, m in enumerate(metodos):
        m_id, m_nombre, m_titular, m_tipo, m_cuenta, m_img = m
        es_seleccionado = (st.session_state.get("banco_activo_id") == m_id)

        with cols_bancos[idx]:
            st.markdown('<div class="bank-card-wrapper">', unsafe_allow_html=True)
            
            # Convertir imagen a Base64 para incrustarla limpiamente
            if m_img and os.path.exists(m_img):
                with open(m_img, "rb") as img_f:
                    encoded = base64.b64encode(img_f.read()).decode()
                img_element = f'<img src="data:image/png;base64,{encoded}" class="bank-icon-img"/>'
            else:
                img_element = '<div style="font-size:28px; margin-bottom:4px;">🏦</div>'

            # Botón Streamlit invisible para capturar clic sobre la tarjeta de banco
            if st.button(" ", key=f"btn_card_{m_id}"):
                st.session_state["banco_activo_id"] = m_id
                st.rerun()

            # Renderizado visual compacto (Estilo tarjeta idéntico a la imagen 2)
            selected_class = "bank-card-selected" if es_seleccionado else ""
            st.markdown(f"""
            <div style="margin-top: -110px; pointer-events: none;">
                <div class="bank-card-btn {selected_class}">
                    {img_element}
                    <span class="bank-title-text">{m_nombre}<br><small style="font-size:9px; color:#94a3b8;">({m_tipo.upper()})</small></span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # La información bancaria está OCULTA por defecto y SOLO aparece al presionar una tarjeta
    if st.session_state.get("banco_activo_id"):
        banco_sel = next((m for m in metodos if m[0] == st.session_state["banco_activo_id"]), None)
        if banco_sel:
            banco_seleccionado = banco_sel[1]
            st.markdown(f"""
            <div class="bank-card-container">
                <h4 style="color: #38bdf8; margin-top:0;">🏦 {banco_sel[1]}</h4>
                <p style="margin: 4px 0;"><strong>Titular:</strong> {banco_sel[2]}</p>
                <p style="margin: 4px 0;"><strong>Tipo de cuenta:</strong> {banco_sel[3]}</p>
                <p style="margin: 4px 0; font-size: 15px;"><strong>Número de cuenta:</strong></p>
            </div>
            """, unsafe_allow_html=True)
            
            c_acc, c_btn = st.columns([3, 1])
            with c_acc:
                st.code(banco_sel[4], language=None)
            with c_btn:
                if st.button("📋 Copiar", key="btn_copy_acc", use_container_width=True):
                    st.toast(f"¡Número de cuenta {banco_sel[4]} copiado!", icon="📋")

    st.divider()

    comprobante_file = st.file_uploader("Subir foto o PDF del comprobante", type=["png", "jpg", "jpeg", "pdf"])
    acepta = st.toggle("Confirmo que mis datos son correctos.")

    listo = bool(nombre_c and telefono_c and banco_seleccionado and comprobante_file and acepta)

    if st.button("🛒 CONFIRMAR COMPRA", disabled=not listo, use_container_width=True):
        conn = conectar()
        c = conn.cursor()

        c.execute("SELECT id FROM boletos WHERE rifa_id=? AND estado='disponible' LIMIT ?", (rifa_id, cant_final))
        disponibles = c.fetchall()

        if len(disponibles) < cant_final:
            st.error("No hay suficientes boletos disponibles.")
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
            st.session_state["banco_activo_id"] = None
            st.success("🎉 ¡Solicitud recibida!")
            st.warning("⏳ Boletos en revisión (máximo 24 hrs). Al aprobarse, se asignan tus números al azar.")

# Apertura de modales
if st.session_state["active_dialog"] == "combos":
    modal_combos()
elif st.session_state["active_dialog"] == "pago":
    modal_pago_detalles()

# =========================================================
# BARRA SUPERIOR DE NAVEGACIÓN
# =========================================================

n1, n2, n3, n4 = st.columns([2, 1, 1, 2])

with n1:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=140)
    else:
        st.markdown("## 🎲 **RIFAS SIRIO RD**")

with n2:
    st.markdown('<a href="#rifas-activas" style="text-decoration:none;"><button style="width:100%; padding:8px; border-radius:8px; border:1px solid #d4af37; background:transparent; color:#d4af37; font-weight:bold; cursor:pointer;">🎟️ Rifas</button></a>', unsafe_allow_html=True)

with n3:
    theme_icon = "☀️ Modo Claro" if is_dark else "🌙 Modo Oscuro"
    if st.button(theme_icon, key="btn_theme_toggle", use_container_width=True):
        toggle_theme()
        st.rerun()

with n4:
    if st.button("🔍 Verificador de boletos", use_container_width=True):
        st.session_state["verificar_open"] = not st.session_state.get("verificar_open", False)

# Panel de Verificación de Boletos
if st.session_state.get("verificar_open", False):
    with st.expander("🔎 CONSULTAR MIS BOLETOS REGISTRADOS", expanded=True):
        tel_ver = st.text_input("Ingresa tu número de teléfono / WhatsApp registrado:")
        if st.button("Consultar Ahora"):
            if tel_ver:
                conn = conectar()
                query = """
                    SELECT b.numero, b.estado, r.nombre, b.fecha_reserva 
                    FROM boletos b
                    JOIN rifas r ON b.rifa_id = r.id
                    WHERE b.usuario_telefono = ?
                """
                res = conn.execute(query, (normalizar_telefono(tel_ver),)).fetchall()
                conn.close()
                
                if res:
                    st.success(f"Se encontraron **{len(res)}** boletos asociados al número.")
                    cols_ver = st.columns(3)
                    for idx, b in enumerate(res):
                        num, est, rifa_nom, fecha_res = b
                        with cols_ver[idx % 3]:
                            with st.container(border=True):
                                st.markdown(f"🎟️ **Boleto:** `{num}`")
                                st.caption(f"Rifa: {rifa_nom}")
                                st.write(f"Estado: **{est.upper()}**")
                else:
                    st.warning("No se encontraron boletos registrados con este número.")

st.divider()

# =========================================================
# PRESENTACIÓN PRINCIPAL (HERO SECTION)
# =========================================================

st.markdown('<div class="logo-hero-container">', unsafe_allow_html=True)
if os.path.exists("logo.png"):
    st.image("logo.png", width=260)
else:
    st.warning("Coloca el archivo 'logo.png' en la misma carpeta del script.")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown(f"""
<div style="text-align: center; margin-bottom: 25px;">
    <p style="color: #F5C518; font-weight: bold; letter-spacing: 1px; margin-bottom: 5px;">EXPERIENCIA EXCLUSIVA</p>
    <h1 style="color: {text_color}; font-size: 34px; font-weight: 800; margin-top: 0;">Premios extraordinarios garantizados</h1>
    <p style="color: #888888; font-size: 16px;">La plataforma más lujosa para participar y ganar de República Dominicana.</p>
</div>
""", unsafe_allow_html=True)

# Sección informativa ¿Cómo Jugar?
with st.expander("❓ ¿CÓMO JUGAR? — 5 pasos simples para participar y ganar", expanded=False):
    st.markdown("""
    1. **Elige tu Rifa:** Selecciona el premio que deseas ganar en el catálogo.
    2. **Haz clic en JUGAR:** Abre el panel de selección de paquetes.
    3. **Selecciona tu Paquete:** Elige la cantidad de números deseada.
    4. **Envía tu Comprobante:** Realiza tu transferencia bancaria y sube la foto.
    5. **Asignación Aleatoria:** Al validar tu pago, se te asignan tus números al azar (revisión en un máximo de 24 horas).
    """)

st.divider()

# =========================================================
# CATÁLOGO DE RIFAS ACTIVAS CON BARRA DE PROGRESO DE 0% A 100%
# =========================================================

st.markdown('<div id="rifas-activas"></div>', unsafe_allow_html=True)
st.markdown(f"<h2 style='color: {text_color};'>🔥 Rifas Activas</h2>", unsafe_allow_html=True)

conn = conectar()
rifas = conn.execute("SELECT id, nombre, categoria, precio_boleto, min_boletos, total_boletos, imagen, fecha FROM rifas WHERE COALESCE(activa,1)=1").fetchall()
conn.close()

cols_rifas = st.columns(2)
for idx, r in enumerate(rifas):
    r_id, r_nombre, r_categoria, r_precio, r_min, r_total, r_img, r_fecha = r
    
    vendidos, total, porcentaje = obtener_progreso_rifa(r_id, r_total)

    with cols_rifas[idx % 2]:
        with st.container(border=True):
            if r_img and os.path.exists(r_img):
                st.image(r_img, use_container_width=True)
            
            st.markdown(f"### {r_nombre}")
            st.caption(f"Categoría: {r_categoria} | Sorteo: {r_fecha}")
            st.markdown(f"**Precio por boleto:** <span style='color:#f5c518; font-size:18px;'>RD$ {r_precio:,.2f}</span>", unsafe_allow_html=True)

            # Barra de Progreso de 0% a 100% (10,000 boletos)
            st.markdown(f"""
            <div class="progress-text">
                <span>Progreso de venta</span>
                <span>{porcentaje:.2f}% ({vendidos:,} / {total:,} boletos)</span>
            </div>
            """, unsafe_allow_html=True)
            st.progress(porcentaje / 100.0)

            st.write("") # Espaciado

            # Botón JUGAR visible y totalmente funcional
            if st.button("🎮 JUGAR", key=f"btn_jugar_{r_id}", use_container_width=True):
                st.session_state["selected_rifa"] = r
                st.session_state["active_dialog"] = "combos"
                st.rerun()
