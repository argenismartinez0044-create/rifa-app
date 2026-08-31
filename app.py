import datetime
import os
import random
import sqlite3
from PIL import Image
import streamlit as st

DB_FILE = "rifas_v4.db"
WHATSAPP_NUMERO = "8294835217"

st.set_page_config(
    page_title="Rifas Sirio RD",
    page_icon="🎲",
    layout="wide"
)

# =========================================================
# BASE DE DATOS (NO BORRA DATOS EXISTENTES)
# =========================================================

def conectar():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def agregar_columna_si_no_existe(conn, tabla, columna, definicion):
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({tabla})")
    columnas = [x[1] for x in cur.fetchall()]
    if columna not in columnas:
        cur.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna} {definicion}")

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
            fecha TEXT
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

    agregar_columna_si_no_existe(conn, "rifas", "activa", "INTEGER DEFAULT 1")

    c.execute("""
        CREATE TABLE IF NOT EXISTS ofertas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rifa_id INTEGER NOT NULL,
            numero TEXT NOT NULL,
            premio TEXT NOT NULL,
            valor_premio REAL DEFAULT 0,
            estado TEXT DEFAULT 'disponible',
            UNIQUE(rifa_id, numero)
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
            ("PlayStation 5 Pro", "Juego", 5.0, 15, 100000, "play.jpg", "Fecha pendiente"),
            ("5 iPhone 17 Pro Max", "TELÉFONO", 15.0, 10, 100000, "iphone.jpg", "Al vender el 80%"),
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

def liberar_expirados():
    conn = conectar()
    conn.execute("""
        UPDATE boletos
        SET estado='disponible', usuario_nombre=NULL, usuario_telefono=NULL,
            metodo_pago=NULL, comprobante=NULL, fecha_reserva=NULL
        WHERE estado='reservado' AND fecha_reserva < ?
    """, (datetime.datetime.now() - datetime.timedelta(minutes=15),))
    conn.commit()
    conn.close()

init_db()
liberar_expirados()

# =========================================================
# ESTADO DE SESIÓN
# =========================================================

if "tema_claro" not in st.session_state:
    st.session_state["tema_claro"] = False
if "vista_actual" not in st.session_state:
    st.session_state["vista_actual"] = "rifas"
if "verificador_paso" not in st.session_state:
    st.session_state["verificador_paso"] = 1
if "verificador_rifa" not in st.session_state:
    st.session_state["verificador_rifa"] = None
if "telefono_verificador" not in st.session_state:
    st.session_state["telefono_verificador"] = ""
if "resultados_verificador" not in st.session_state:
    st.session_state["resultados_verificador"] = None
if "mostrar_soporte_ia" not in st.session_state:
    st.session_state["mostrar_soporte_ia"] = False
if "rifa_activa_modal" not in st.session_state:
    st.session_state["rifa_activa_modal"] = None

# =========================================================
# FUNCIONES AUXILIARES
# =========================================================

def archivo_existe(nombre):
    return bool(nombre) and os.path.exists(nombre)

def guardar_imagen(uploaded, carpeta, base):
    os.makedirs(carpeta, exist_ok=True)
    ext = os.path.splitext(uploaded.name)[1].lower()
    if ext not in (".png", ".jpg", ".jpeg"):
        ext = ".png"
    limpio = "".join(ch if ch.isalnum() else "_" for ch in base)
    ruta = os.path.join(carpeta, f"{limpio}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}{ext}")
    with open(ruta, "wb") as f:
        f.write(uploaded.getbuffer())
    return ruta

def obtener_metodos_pago(activos_solo=True):
    conn = conectar()
    q = "SELECT id, nombre, titular, tipo_cuenta, numero_cuenta, imagen, activo FROM metodos_pago"
    if activos_solo:
        q += " WHERE COALESCE(activo,1)=1"
    q += " ORDER BY id"
    filas = conn.execute(q).fetchall()
    conn.close()
    return filas

def normalizar_telefono(telefono):
    return telefono.replace(" ", "").replace("-", "").replace("(", "").replace(")", "").replace("+", "").strip()

# =========================================================
# MODAL DE PARTICIPACIÓN / COMPRA (DESPLEGABLE FLOTANTE)
# =========================================================

@st.dialog("🎲 Proceso de Participación", width="large")
def modal_participar(rifa_datos):
    rifa_id, nombre, categoria, precio, min_boletos, total_boletos, imagen, fecha = rifa_datos

    st.markdown(f"### {nombre}")
    st.caption(f"Categoría: {categoria} | Precio por boleto: **RD$ {precio:.2f}**")

    # Tabs por funciones
    tab1, tab2, tab3 = st.tabs(["1️⃣ Boletos / Combos", "2️⃣ Mis Datos", "3️⃣ Pago y Verificación"])

    with tab1:
        st.subheader("Selecciona tus boletos")
        modo_seleccion = st.radio("Modo de selección", ["Combos populares", "Selección manual"], horizontal=True)
        
        cant_boletos = min_boletos
        if modo_seleccion == "Combos populares":
            c1, c2, c3, c4 = st.columns(4)
            if c1.button(f"+{min_boletos} Boletos", use_container_width=True):
                st.session_state["temp_cant"] = min_boletos
            if c2.button(f"+{min_boletos * 2} Boletos", use_container_width=True):
                st.session_state["temp_cant"] = min_boletos * 2
            if c3.button(f"+{min_boletos * 5} Boletos", use_container_width=True):
                st.session_state["temp_cant"] = min_boletos * 5
            if c4.button(f"+{min_boletos * 10} Boletos", use_container_width=True):
                st.session_state["temp_cant"] = min_boletos * 10
            
            cant_boletos = st.session_state.get("temp_cant", min_boletos)
        else:
            cant_boletos = st.number_input("Cantidad de boletos a comprar:", min_value=int(min_boletos), max_value=1000, value=int(min_boletos), step=1)
            st.session_state["temp_cant"] = cant_boletos

        total_pagar = cant_boletos * precio
        st.info(f"📊 Boletos a comprar: **{cant_boletos}** | Total a pagar: **RD$ {total_pagar:,.2f}**")

    with tab2:
        st.subheader("Información Personal")
        nombre_cliente = st.text_input("Nombre completo:", key="m_nombre")
        telefono_cliente = st.text_input("Número de WhatsApp:", key="m_telefono", placeholder="8291234567")

    with tab3:
        st.subheader("Método de Pago")
        metodos = obtener_metodos_pago(activos_solo=True)
        if not metodos:
            st.warning("No hay métodos de pago configurados.")
        else:
            opciones_bancos = [m[1] for m in metodos]
            banco_sel = st.selectbox("Selecciona tu banco:", opciones_bancos)

            detalles = next(m for m in metodos if m[1] == banco_sel)
            m_id, m_nombre, m_titular, m_tipo, m_cuenta, m_img, _ = detalles

            st.markdown(f"""
            **Titular:** {m_titular}  
            **Tipo de Cuenta:** {m_tipo}  
            **Número de Cuenta:** `{m_cuenta}`
            """)
            st.code(m_cuenta, language=None)

            comprobante_img = st.file_uploader("Sube tu comprobante de pago (Imagen)", type=["png", "jpg", "jpeg"])
            acepta_terminos = st.checkbox("Acepto los términos y condiciones de Rifas Sirio RD")

            # Botón final activable solo si se cumplen los requisitos
            requisitos_completos = bool(nombre_cliente and telefono_cliente and comprobante_img and acepta_terminos)
            
            if st.button("🚀 FINALIZAR Y RESERVAR BOLETOS", disabled=not requisitos_completos, use_container_width=True):
                conn = conectar()
                cursor = conn.cursor()

                # Buscar boletos disponibles sin repetir
                cursor.execute("""
                    SELECT id, numero FROM boletos 
                    WHERE rifa_id=? AND estado='disponible' 
                    LIMIT ?
                """, (rifa_id, cant_boletos))
                
                disponibles = cursor.fetchall()

                if len(disponibles) < cant_boletos:
                    st.error("No hay suficientes boletos disponibles para esta rifa.")
                    conn.close()
                else:
                    ruta_comp = guardar_imagen(comprobante_img, "comprobantes", telefono_cliente)
                    ids_reservar = [b[0] for b in disponibles]
                    numeros_asignados = [b[1] for b in disponibles]

                    cursor.executemany("""
                        UPDATE boletos
                        SET estado='reservado',
                            usuario_nombre=?,
                            usuario_telefono=?,
                            metodo_pago=?,
                            comprobante=?,
                            fecha_reserva=?
                        WHERE id=?
                    """, [
                        (nombre_cliente, normalizar_telefono(telefono_cliente), banco_sel, ruta_comp, datetime.datetime.now(), bid)
                        for bid in ids_reservar
                    ])
                    conn.commit()
                    conn.close()

                    st.success("🎉 ¡Reserva completada con éxito!")
                    st.warning("Sus boletos están **EN VERIFICACIÓN**. El administrador validará el pago para la aprobación final.")
                    st.write(f"**Tus números asignados:** {', '.join(numeros_asignados)}")

# =========================================================
# VISTA PÚBLICA: VERIFICADOR DE BOLETOS
# =========================================================

def render_verificador():
    st.markdown("""
    <div class="verificador-card">
        <h2 style="color:#F5C518;">🔎 Verificar mis boletos</h2>
        <p>Consulta los boletos registrados a tu número de WhatsApp para una rifa específica.</p>
    </div>
    """, unsafe_allow_html=True)

    paso = st.session_state.get("verificador_paso", 1)

    if paso == 1:
        st.markdown("### 🟡 PASO 1 — Selecciona la rifa")
        conn = conectar()
        rifas_verificador = conn.execute("SELECT id, nombre, categoria, imagen FROM rifas WHERE COALESCE(activa,1)=1 ORDER BY id").fetchall()
        conn.close()

        if not rifas_verificador:
            st.info("No hay rifas activas disponibles.")
        else:
            opciones_rifas = {f"{r[1]} — {r[2]}": r[0] for r in rifas_verificador}
            rifa_elegida = st.selectbox("Selecciona la rifa que deseas consultar:", list(opciones_rifas.keys()))
            rid_verificador = opciones_rifas[rifa_elegida]

            if st.button("➡️ CONTINUAR", use_container_width=True):
                st.session_state["verificador_rifa"] = rid_verificador
                st.session_state["verificador_paso"] = 2
                st.rerun()

    elif paso == 2:
        st.markdown("### 🟡 PASO 2 — Introduce tu teléfono")
        rid_verificador = st.session_state.get("verificador_rifa")
        telefono_ver = st.text_input("📱 Número de WhatsApp registrado", placeholder="Ejemplo: 8294835217")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("⬅️ CAMBIAR RIFA", use_container_width=True):
                st.session_state["verificador_paso"] = 1
                st.rerun()
        with c2:
            if st.button("🔎 BUSCAR MIS BOLETOS", use_container_width=True):
                telefono_limpio = normalizar_telefono(telefono_ver)
                if not telefono_limpio:
                    st.error("Introduce tu número de teléfono.")
                else:
                    conn = conectar()
                    boletos_ver = conn.execute("""
                        SELECT b.numero, b.estado, b.usuario_nombre, r.nombre
                        FROM boletos b
                        INNER JOIN rifas r ON b.rifa_id = r.id
                        WHERE b.rifa_id=? AND b.usuario_telefono=? AND b.estado IN ('reservado', 'confirmado')
                        ORDER BY b.numero
                    """, (rid_verificador, telefono_limpio)).fetchall()
                    conn.close()
                    st.session_state["resultados_verificador"] = boletos_ver

        if st.session_state.get("resultados_verificador") is not None:
            res = st.session_state["resultados_verificador"]
            if not res:
                st.warning("No se encontraron boletos registrados con este número.")
            else:
                st.success(f"Se encontraron {len(res)} boletos:")
                for b in res:
                    estado_tag = "🟡 En Verificación" if b[1] == "reservado" else "🟢 Confirmado"
                    st.write(f"- Boleto **#{b[0]}** | Estado: {estado_tag}")

# =========================================================
# VISTA PRINCIPAL DE RIFAS Y CATÁLOGO
# =========================================================

def render_catalogo():
    st.markdown("## 🎲 Rifas Disponibles")
    conn = conectar()
    rifas = conn.execute("SELECT id, nombre, categoria, precio_boleto, min_boletos, total_boletos, imagen, fecha FROM rifas WHERE COALESCE(activa,1)=1").fetchall()
    conn.close()

    for r in rifas:
        with st.container():
            col1, col2 = st.columns([1, 2])
            with col1:
                if archivo_existe(r[6]):
                    st.image(r[6], use_container_width=True)
                else:
                    st.write("🖼️ *Sin imagen*")
            with col2:
                st.markdown(f"### {r[1]}")
                st.caption(f"Categoría: {r[2]} | Sorteo: {r[7]}")
                st.markdown(f"**Precio por boleto:** RD$ {r[3]:,.2f}")

                if st.button(f"🎟️ PARTICIPAR EN {r[1].upper()}", key=f"btn_part_{r[0]}", use_container_width=True):
                    modal_participar(r)

# =========================================================
# PANEL DE ADMINISTRACIÓN (SOLO CON ?admin=true)
# =========================================================

def render_admin():
    st.title("⚙️ Panel de Administración")
    tab_boletos, tab_rifas, tab_pagos = st.tabs(["📋 Aprobar Pagos", "🎟️ Gestionar Rifas", "🏦 Métodos de Pago"])

    conn = conectar()
    
    with tab_boletos:
        st.subheader("Boletos en Verificación (Pendientes de aprobación)")
        pendientes = conn.execute("""
            SELECT b.id, r.nombre, b.numero, b.usuario_nombre, b.usuario_telefono, b.metodo_pago, b.comprobante
            FROM boletos b
            JOIN rifas r ON b.rifa_id = r.id
            WHERE b.estado = 'reservado'
        """).fetchall()

        if not pendientes:
            st.info("No hay pagos pendientes de aprobación.")
        else:
            for p in pendientes:
                st.markdown(f"**Rifa:** {p[1]} | **Boleto:** #{p[2]} | **Cliente:** {p[3]} ({p[4]}) | **Banco:** {p[5]}")
                if p[6] and archivo_existe(p[6]):
                    st.image(p[6], width=250)
                
                c1, c2 = st.columns(2)
                if c1.button(f"✅ Aprobar Boleto #{p[2]}", key=f"ap_{p[0]}"):
                    conn.execute("UPDATE boletos SET estado='confirmado' WHERE id=?", (p[0],))
                    conn.commit()
                    st.rerun()
                if c2.button(f"❌ Rechazar boleto #{p[2]}", key=f"rec_{p[0]}"):
                    conn.execute("UPDATE boletos SET estado='disponible', usuario_nombre=NULL, usuario_telefono=NULL WHERE id=?", (p[0],))
                    conn.commit()
                    st.rerun()

    conn.close()

# =========================================================
# CONTROL DE RUTAS Y NAVEGACIÓN
# =========================================================

query_params = st.query_params
es_admin_url = query_params.get("admin", "").lower() in ["true", "1"]

if es_admin_url:
    render_admin()
else:
    vista = st.session_state.get("vista_actual", "rifas")
    if vista == "verificador":
        render_verificador()
    else:
        render_catalogo()
