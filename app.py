import datetime
import os
import random
import sqlite3
from PIL import Image
import streamlit as st

DB_FILE = "rifas_v4.db"
WHATSAPP_NUMERO = "8294835217"

st.set_page_config(page_title="Rifas Sirio RD", page_icon="🎲", layout="wide")


# =========================================================
# BASE DE DATOS (NO BORRA LOS DATOS EXISTENTES)
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
            nombre TEXT, categoria TEXT, precio_boleto REAL,
            min_boletos INTEGER, total_boletos INTEGER, imagen TEXT, fecha TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS boletos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rifa_id INTEGER, numero TEXT,
            estado TEXT DEFAULT 'disponible',
            usuario_nombre TEXT, usuario_telefono TEXT,
            metodo_pago TEXT, comprobante TEXT, fecha_reserva DATETIME
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

    # Métodos de pago administrables desde el panel.
    # Se agregan sin borrar ni modificar los datos existentes.
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

    # Solo crea los 2 métodos originales si la tabla está vacía.
    c.execute("SELECT COUNT(*) FROM metodos_pago")
    if c.fetchone()[0] == 0:
        c.executemany("""
            INSERT INTO metodos_pago
            (nombre,titular,tipo_cuenta,numero_cuenta,imagen,activo)
            VALUES (?,?,?,?,?,1)
        """, [
            ("Banreservas", "ARGENIS MARTINEZ C.", "Ahorros", "9606561652", "banreservas.png"),
            ("Banco Popular", "ARGENIS MARTINEZ", "Ahorros", "821794971", "popular.png"),
        ])

    # Solo crea las 2 rifas originales si la base está vacía.
    # Se eliminó el UPDATE que forzaba sus precios/nombres en cada ejecución.
    c.execute("SELECT COUNT(*) FROM rifas")
    if c.fetchone()[0] == 0:
        iniciales = [
            ("PlayStation 5 Pro", "Juego", 5.0, 15, 100000, "play.jpg", "Fecha pendiente"),
            ("5 iPhone 17 Pro Max", "TELÉFONO", 15.0, 10, 100000, "iphone.jpg", "Al vender el 80%"),
        ]
        for rifa in iniciales:
            c.execute("""
                INSERT INTO rifas
                (nombre,categoria,precio_boleto,min_boletos,total_boletos,imagen,fecha,activa)
                VALUES (?,?,?,?,?,?,?,1)
            """, rifa)

        for rifa_id in (1, 2):
            numeros = [(rifa_id, f"{i:05d}") for i in range(1, 100001)]
            c.executemany(
                "INSERT INTO boletos (rifa_id,numero) VALUES (?,?)", numeros
            )

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
# FUNCIONES
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


def guardar_comprobante(uploaded):
    base = st.session_state.get("telefono_cliente", "cliente")
    return guardar_imagen(uploaded, "comprobantes", base)


def seleccionar_rifa(rifa_id, nombre, precio, minimo):
    st.session_state.update({
        "rifa_seleccionada": rifa_id,
        "nombre_rifa": nombre,
        "precio_rifa": float(precio),
        "min_rifa": int(minimo),
        "paso_compra": 1,
        "cant_boletos": int(minimo),
    })


def contar_estados(rifa_id):
    conn = conectar()
    fila = conn.execute("""
        SELECT COUNT(*),
               SUM(CASE WHEN estado='disponible' THEN 1 ELSE 0 END),
               SUM(CASE WHEN estado='reservado' THEN 1 ELSE 0 END),
               SUM(CASE WHEN estado='confirmado' THEN 1 ELSE 0 END)
        FROM boletos WHERE rifa_id=?
    """, (rifa_id,)).fetchone()
    conn.close()
    return tuple(x or 0 for x in fila)


def crear_boletos(conn, rifa_id, cantidad):
    conn.executemany(
        "INSERT INTO boletos (rifa_id,numero,estado) VALUES (?,?,'disponible')",
        [(rifa_id, f"{i:05d}") for i in range(1, cantidad + 1)]
    )


def obtener_metodos_pago(activos_solo=True):
    conn = conectar()
    if activos_solo:
        filas = conn.execute("""
            SELECT id,nombre,titular,tipo_cuenta,numero_cuenta,imagen,activo
            FROM metodos_pago
            WHERE COALESCE(activo,1)=1
            ORDER BY id
        """).fetchall()
    else:
        filas = conn.execute("""
            SELECT id,nombre,titular,tipo_cuenta,numero_cuenta,imagen,activo
            FROM metodos_pago
            ORDER BY id
        """).fetchall()
    conn.close()
    return filas


def limpiar_compra():
    for k in (
        "rifa_seleccionada", "nombre_rifa", "precio_rifa", "min_rifa",
        "cant_boletos", "paso_compra", "nombre_cliente",
        "telefono_cliente", "banco_pago", "compra_completada"
    ):
        st.session_state.pop(k, None)


# =========================================================
# SOPORTE IA
# =========================================================
@st.dialog("🤖 Asistente Virtual - Rifas Sirio RD")
def abrir_soporte_ia():
    st.caption("Respuestas instantáneas las 24 horas.")
    if "mensajes_chat" not in st.session_state:
        st.session_state["mensajes_chat"] = [{
            "role": "assistant",
            "content": "¡Hola! Soy tu asistente de **Rifas Sirio RD** 🎲.\n\n¿En qué te puedo ayudar?"
        }]

    c1, c2, c3, c4 = st.columns(4)
    opcion = None
    if c1.button("🎲 ¿Cómo jugar?", key="dlg_c1"): opcion = "¿Cómo participar?"
    if c2.button("💳 Bancos", key="dlg_c2"): opcion = "cuentas de banco"
    if c3.button("🔎 Mis boletos", key="dlg_c3"): opcion = "verificar mis boletos"
    if c4.button("📅 Sorteos", key="dlg_c4"): opcion = "fecha del sorteo"

    for msg in st.session_state["mensajes_chat"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    entrada = st.chat_input("Escribe tu duda...")
    prompt = entrada or opcion
    if prompt:
        if entrada:
            st.session_state["mensajes_chat"].append({"role": "user", "content": prompt})
        txt = prompt.lower()
        if any(w in txt for w in ["jugar","participar","funciona","pasos","comprar","instrucciones"]):
            resp = "1. Selecciona una rifa.\n2. Elige boletos/combo.\n3. Realiza la transferencia.\n4. Sube el comprobante.\n5. Espera la validación."
        elif any(w in txt for w in ["pago","banco","transferencia","banreservas","popular","cuenta"]):
            resp = "Los métodos de pago disponibles aparecen después de completar los datos de la rifa. El administrador puede agregar o actualizar bancos desde **⚙️ Administración → 🏦 Métodos de pago**."
        elif any(w in txt for w in ["verificar","consultar","mi boleto","numeros"]):
            resp = "Usa **🔎 Verificador de boletos** e introduce tu teléfono."
        elif any(w in txt for w in ["ganador","sorteo","fecha","cuando"]):
            resp = "La condición del sorteo aparece en la ficha de cada rifa."
        elif any(w in txt for w in ["precio","costo","minimo","mínimo","combo"]):
            resp = "PlayStation 5 Pro: RD$5.00, mínimo 15.\n5 iPhone 17 Pro Max: RD$15.00, mínimo 10."
        else:
            resp = f"Puedes contactar soporte por WhatsApp: https://wa.me/{WHATSAPP_NUMERO}"
        st.session_state["mensajes_chat"].append({"role": "assistant", "content": resp})
        st.rerun()


# =========================================================
# ESTILO Y NAVEGACIÓN
# =========================================================
st.markdown("""
<style>
.stApp { background:linear-gradient(135deg,#0b0d17 0%,#171b2e 50%,#080910 100%) !important; color:#fff; }
</style>
""", unsafe_allow_html=True)

seccion = st.sidebar.radio("Navegación", [
    "🏠 Inicio & Catálogo", "🔎 Verificador de boletos",
    "❓ Cómo jugar", "🤖 Soporte IA", "🏆 Ganadores", "⚙️ Administración"
])
st.sidebar.markdown("---")
if st.sidebar.button("🤖 Abrir Chat de Soporte IA"):
    abrir_soporte_ia()


# =========================================================
# CATÁLOGO + COMPRA
# =========================================================
if seccion == "🏠 Inicio & Catálogo":
    a, b = st.columns([1, 2])
    with a:
        if archivo_existe("logo.png"): st.image("logo.png", width=220)
    with b:
        st.markdown("<p style='color:#F5C518;font-weight:bold;'>Plataforma Exclusiva de Rifas</p>", unsafe_allow_html=True)
        st.markdown("<h1 style='color:#FFF;'>Premios Exclusivos Garantizados</h1>", unsafe_allow_html=True)

    conn = conectar()
    rifas = conn.execute("""
        SELECT id,nombre,categoria,precio_boleto,min_boletos,total_boletos,imagen,fecha
        FROM rifas WHERE COALESCE(activa,1)=1 ORDER BY id
    """).fetchall()
    conn.close()

    for rid, nombre, categoria, precio, minimo, total, imagen, fecha in rifas:
        total_db, disponibles, reservados, confirmados = contar_estados(rid)
        progreso = ((reservados + confirmados) / total_db * 100) if total_db else 0

        with st.container(border=True):
            c1, c2 = st.columns([1, 2])
            with c1:
                if archivo_existe(imagen): st.image(imagen, use_container_width=True)
                else: st.info("Imagen no disponible")
            with c2:
                st.markdown(f"### {nombre}")
                st.caption(f"Categoría: {categoria}")
                st.markdown(f"### RD$ {precio:.2f}")
                st.caption(f"Mínimo {minimo} boletos")
                st.write(f"📅 **Fecha:** {fecha}")
                st.write(f"📊 **Progreso:** {progreso:.2f}%")
                st.progress(min(1, progreso / 100))
                st.button(
                    f"🎟️ PARTICIPAR POR {nombre.upper()}",
                    key=f"jugar_{rid}",
                    on_click=seleccionar_rifa,
                    args=(rid, nombre, precio, minimo),
                    use_container_width=True
                )

    if "rifa_seleccionada" in st.session_state:
        st.markdown("---")
        nombre = st.session_state["nombre_rifa"]
        precio = st.session_state["precio_rifa"]
        minimo = int(st.session_state["min_rifa"])
        paso = st.session_state.get("paso_compra", 1)

        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#0f2027,#203a43,#2c5364);
                    border-radius:16px;padding:20px;text-align:center;">
            <span style="background:#F5C518;color:#000;font-weight:800;padding:4px 12px;border-radius:20px;">Rifa seleccionada</span>
            <h2 style="color:#fff;">🎉 {nombre} 🎉</h2>
            <p style="color:#eee;">Precio por boleto: <strong style="color:#F5C518;">RD$ {precio:.2f}</strong></p>
        </div>
        """, unsafe_allow_html=True)

        if paso == 1:
            st.subheader("📝 1. Completa tus datos y selecciona tu combo")
            st.markdown("### 💥 SELECCIÓN DE COMBOS DE BOLETOS")
            combos = [
                ("🟢 COMBO BÁSICO", minimo),
                ("🔵 COMBO DOBLE", minimo * 2),
                ("🟣 COMBO INTERMEDIO", minimo * 3),
                ("🟠 COMBO PROFESIONAL", minimo * 5),
                ("🔴 COMBO PRO VIP", minimo * 10),
            ]
            cols = st.columns(5)
            for i, (nom_combo, cantidad) in enumerate(combos):
                cantidad = min(100, cantidad)
                with cols[i]:
                    st.markdown(f"**{nom_combo}**\n\n🎟️ {cantidad} boletos\n\nRD$ {cantidad*precio:.2f}")
                    if st.button("Seleccionar", key=f"combo_{i}", use_container_width=True):
                        st.session_state["cant_boletos"] = cantidad
                        st.rerun()

            with st.form("datos_cliente"):
                nombre_cliente = st.text_input("Nombre Completo", value=st.session_state.get("nombre_cliente",""))
                telefono = st.text_input("Teléfono / WhatsApp", value=st.session_state.get("telefono_cliente",""))
                cantidad = st.number_input(
                    "✏️ Boletos seleccionados:",
                    min_value=minimo, max_value=100,
                    value=int(st.session_state.get("cant_boletos", minimo)), step=1
                )
                st.markdown(f"### 💰 Total: **RD$ {cantidad*precio:.2f}**")
                continuar = st.form_submit_button("➡️ CONTINUAR AL PAGO", use_container_width=True)

            if continuar:
                if not nombre_cliente.strip() or not telefono.strip():
                    st.error("Completa tu nombre y teléfono/WhatsApp.")
                else:
                    st.session_state.update({
                        "nombre_cliente": nombre_cliente.strip(),
                        "telefono_cliente": telefono.strip(),
                        "cant_boletos": int(cantidad),
                        "paso_compra": 2
                    })
                    st.rerun()

        elif paso == 2:
            st.subheader("💳 2. Selecciona el método de pago")
            metodos = obtener_metodos_pago(True)

            if not metodos:
                st.error("No hay métodos de pago activos. El administrador debe agregar uno desde ⚙️ Administración.")
            else:
                nombres_metodos = [fila[1] for fila in metodos]
                metodo = st.radio(
                    "¿Dónde deseas realizar el pago?",
                    nombres_metodos,
                    horizontal=True,
                    key="banco_pago"
                )

                seleccionado = next(fila for fila in metodos if fila[1] == metodo)
                metodo_id, banco, titular, tipo_cuenta, cuenta, imagen_banco, activo = seleccionado

                if imagen_banco and archivo_existe(imagen_banco):
                    st.image(imagen_banco, width=180)
                elif banco == "Banreservas" and archivo_existe("barreserva.png"):
                    st.image("barreserva.png", width=180)
                else:
                    st.info("Logo no disponible para este método.")

                st.markdown(f"### 🏦 {banco}")
                st.write(f"**Tipo:** {tipo_cuenta}")
                st.write(f"**Titular:** {titular}")
                st.write("**Número de cuenta:**")
                st.code(str(cuenta), language=None)  # botón COPIAR funcional de Streamlit
                st.caption("💡 Usa el icono de copiar que aparece en el recuadro para copiar el número de cuenta.")

                st.markdown(f"### 💰 Total a pagar: **RD$ {st.session_state['cant_boletos']*precio:.2f}**")
                st.info("Realiza el depósito y luego sube la foto del volante/comprobante.")

            x, y = st.columns(2)
            with x:
                if st.button("⬅️ VOLVER A DATOS Y COMBOS", key="volver_datos", use_container_width=True):
                    st.session_state["paso_compra"] = 1
                    st.rerun()
            with y:
                if st.button("➡️ CONTINUAR Y SUBIR COMPROBANTE", key="continuar_comprobante", use_container_width=True):
                    st.session_state["paso_compra"] = 3
                    st.rerun()

        elif paso == 3:
            st.subheader("📤 3. Sube el volante/comprobante del depósito")
            st.info(f"Banco: **{st.session_state['banco_pago']}** · Total: **RD$ {st.session_state['cant_boletos']*precio:.2f}**")
            comprobante = st.file_uploader("Selecciona la imagen del volante/comprobante", type=["png","jpg","jpeg"], key="comprobante_file")

            x, y = st.columns(2)
            with x:
                if st.button("⬅️ VOLVER AL BANCO", key="volver_banco", use_container_width=True):
                    st.session_state["paso_compra"] = 2
                    st.rerun()
            with y:
                reservar = st.button("✅ RESERVAR MIS BOLETOS", key="reservar_final", use_container_width=True)

            if reservar:
                if not comprobante:
                    st.error("Debes subir el comprobante.")
                else:
                    conn = conectar()
                    cur = conn.cursor()
                    cur.execute("""
                        SELECT id,numero FROM boletos
                        WHERE rifa_id=? AND estado='disponible'
                    """, (st.session_state["rifa_seleccionada"],))
                    disponibles = cur.fetchall()
                    cantidad = int(st.session_state["cant_boletos"])

                    if len(disponibles) < cantidad:
                        st.error("No hay suficientes boletos disponibles.")
                        conn.close()
                    else:
                        asignados = random.sample(disponibles, cantidad)
                        ruta = guardar_comprobante(comprobante)
                        ahora = datetime.datetime.now()
                        numeros = []
                        for bid, numero in asignados:
                            numeros.append(numero)
                            cur.execute("""
                                UPDATE boletos SET estado='reservado',
                                usuario_nombre=?,usuario_telefono=?,metodo_pago=?,
                                comprobante=?,fecha_reserva=? WHERE id=?
                            """, (
                                st.session_state["nombre_cliente"],
                                st.session_state["telefono_cliente"],
                                st.session_state["banco_pago"],
                                ruta, ahora, bid
                            ))
                        conn.commit()
                        conn.close()

                        st.success("🎉 ¡Boletos asignados temporalmente!")
                        st.info("Quedan pendientes de validación del comprobante.")
                        st.subheader("🎟️ Tus números asignados:")
                        cols = st.columns(min(5, len(numeros)))
                        for i, n in enumerate(numeros):
                            cols[i % 5].metric("Boleto", n, delta="Pendiente", delta_color="off")

                        for k in ("rifa_seleccionada","nombre_rifa","precio_rifa","min_rifa","paso_compra","banco_pago"):
                            st.session_state.pop(k, None)


# =========================================================
# VERIFICADOR
# =========================================================
elif seccion == "🔎 Verificador de boletos":
    st.header("🔎 Verificador de Boletos")
    telefono = st.text_input("Ingresa tu número de WhatsApp registrado:")
    if st.button("Buscar Mis Boletos"):
        if telefono:
            conn = conectar()
            datos = conn.execute("""
                SELECT b.numero,b.estado,r.nombre
                FROM boletos b JOIN rifas r ON b.rifa_id=r.id
                WHERE b.usuario_telefono=? ORDER BY r.id,b.numero
            """, (telefono,)).fetchall()
            conn.close()
            if datos:
                st.success(f"Se encontraron {len(datos)} boletos.")
                for numero, estado, rifa in datos:
                    a,b,c = st.columns(3)
                    a.write(f"🎟️ **Boleto:** `{numero}`")
                    b.write(f"🏆 **Rifa:** {rifa}")
                    c.write("📌 **PENDIENTE**" if estado=="reservado" else "📌 **CONFIRMADO Y VÁLIDO**" if estado=="confirmado" else f"📌 **{estado.upper()}**")
                    st.markdown("---")
            else:
                st.info("No se encontraron registros con este número.")


elif seccion == "❓ Cómo jugar":
    st.header("❓ Cómo Participar")
    st.markdown("1. Selecciona tu premio.\n2. Compra tus boletos.\n3. Transfiere por banco.\n4. Sube el comprobante.\n5. Verifica tus números.")

elif seccion == "🤖 Soporte IA":
    abrir_soporte_ia()

elif seccion == "🏆 Ganadores":
    st.header("🏆 Ganadores Anteriores")
    st.info("Próximamente publicaremos aquí los ganadores oficiales.")


# =========================================================
# ADMINISTRACIÓN
# =========================================================
elif seccion == "⚙️ Administración":
    st.header("⚙️ Administración")
    st.caption("Panel para propietario y administrador.")

    admin_password = st.text_input("Contraseña de administrador", type="password")

    # Recomendado: guardar estas dos claves en Streamlit Secrets.
    ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "admin123")
    OWNER_PASSWORD = st.secrets.get("OWNER_PASSWORD", "sirio2026")

    if admin_password in (ADMIN_PASSWORD, OWNER_PASSWORD):
        rol = "Propietario" if admin_password == OWNER_PASSWORD else "Administrador"
        st.success(f"Acceso autorizado: **{rol}**")

       t1,t2,t3,t4 = st.tabs([
    "💳 Pagos pendientes",
    "🎟️ Boletos",
    "🎁 Rifas",
    "⭐ Ofertas",
    "🏦 Métodos de pago"
])

        # -------------------------------------------------
        # PAGOS
        # -------------------------------------------------
        with t1:
            st.subheader("💳 Volantes/comprobantes pendientes")
            conn = conectar()
            pendientes = conn.execute("""
                SELECT b.id,b.numero,b.usuario_nombre,b.usuario_telefono,
                       b.metodo_pago,b.comprobante,b.fecha_reserva,r.nombre
                FROM boletos b JOIN rifas r ON b.rifa_id=r.id
                WHERE b.estado='reservado'
                ORDER BY b.fecha_reserva DESC
            """).fetchall()

            if not pendientes:
                st.info("No hay pagos pendientes.")
            else:
                for bid, numero, cliente, telefono, metodo, comp, fecha, rifa in pendientes:
                    st.markdown(f"### 🎟️ Boleto `{numero}` — {rifa}")
                    st.write(f"👤 {cliente} | 📱 {telefono} | 💳 {metodo} | 🕒 {fecha}")
                    if comp and os.path.exists(comp): st.image(comp, width=350)
                    else: st.warning("Comprobante no disponible.")

                    a,b = st.columns(2)
                    if a.button(f"✅ Aprobar {numero}", key=f"aprobar_{bid}", use_container_width=True):
                        conn.execute("UPDATE boletos SET estado='confirmado' WHERE id=?", (bid,))
                        conn.commit()
                        st.rerun()
                    if b.button(f"❌ Rechazar/Eliminar {numero}", key=f"rechazar_{bid}", use_container_width=True):
                        conn.execute("""
                            UPDATE boletos SET estado='disponible',
                            usuario_nombre=NULL,usuario_telefono=NULL,metodo_pago=NULL,
                            comprobante=NULL,fecha_reserva=NULL WHERE id=?
                        """, (bid,))
                        conn.commit()
                        st.rerun()
                    st.markdown("---")
            conn.close()

        # -------------------------------------------------
        # BOLETOS
        # -------------------------------------------------
        with t2:
            st.subheader("🎟️ Control de boletos por rifa")
            conn = conectar()
            rifas = conn.execute("SELECT id,nombre FROM rifas ORDER BY id").fetchall()
            conn.close()

            for rid, nombre in rifas:
                total, disponibles, reservados, confirmados = contar_estados(rid)
                with st.expander(f"🎟️ {nombre}"):
                    a,b,c,d = st.columns(4)
                    a.metric("Total", total)
                    b.metric("Disponibles", disponibles)
                    c.metric("Pendientes", reservados)
                    d.metric("Confirmados", confirmados)

                    if st.button(f"🧹 VACIAR RIFA: {nombre}", key=f"vaciar_{rid}", use_container_width=True):
                        conn = conectar()
                        conn.execute("""
                            UPDATE boletos SET estado='disponible',
                            usuario_nombre=NULL,usuario_telefono=NULL,metodo_pago=NULL,
                            comprobante=NULL,fecha_reserva=NULL WHERE rifa_id=?
                        """, (rid,))
                        conn.execute("UPDATE ofertas SET estado='disponible' WHERE rifa_id=?", (rid,))
                        conn.commit()
                        conn.close()
                        st.success("Rifa vaciada.")
                        st.rerun()

        # -------------------------------------------------
        # RIFAS: CREAR, EDITAR, ACTIVAR, ELIMINAR
        # -------------------------------------------------
        with t3:
            st.subheader("🎁 Crear, actualizar y administrar rifas")

            conn = conectar()
            rifas = conn.execute("""
                SELECT id,nombre,categoria,precio_boleto,min_boletos,total_boletos,
                       imagen,fecha,COALESCE(activa,1)
                FROM rifas ORDER BY id
            """).fetchall()
            conn.close()

            for rid,nombre,categoria,precio,minimo,total,imagen,fecha,activa in rifas:
                with st.expander(f"✏️ {nombre}"):
                    with st.form(f"editar_{rid}"):
                        n = st.text_input("Nombre", value=nombre)
                        cat = st.text_input("Categoría", value=categoria)
                        p = st.number_input("Precio por boleto", min_value=0.0, value=float(precio), step=0.50)
                        m = st.number_input("Mínimo de boletos", min_value=1, value=int(minimo), step=1)
                        f = st.text_input("Fecha/condición", value=fecha)
                        act = st.checkbox("Rifa activa", value=bool(activa))
                        guardar = st.form_submit_button("💾 GUARDAR CAMBIOS", use_container_width=True)

                    if guardar:
                        conn = conectar()
                        conn.execute("""
                            UPDATE rifas SET nombre=?,categoria=?,precio_boleto=?,
                            min_boletos=?,fecha=?,activa=? WHERE id=?
                        """, (n.strip(),cat.strip(),float(p),int(m),f.strip(),1 if act else 0,rid))
                        conn.commit()
                        conn.close()
                        st.success("Rifa actualizada.")
                        st.rerun()

                    if st.button(f"🗑️ Eliminar rifa: {nombre}", key=f"del_rifa_{rid}", use_container_width=True):
                        conn = conectar()
                        cur = conn.cursor()
                        estados = cur.execute(
                            "SELECT COUNT(*) FROM boletos WHERE rifa_id=? AND estado IN ('reservado','confirmado')",
                            (rid,)
                        ).fetchone()[0]
                        if estados:
                            conn.close()
                            st.error("No se puede eliminar: primero vacía la rifa y verifica los pagos.")
                        else:
                            cur.execute("DELETE FROM ofertas WHERE rifa_id=?", (rid,))
                            cur.execute("DELETE FROM boletos WHERE rifa_id=?", (rid,))
                            cur.execute("DELETE FROM rifas WHERE id=?", (rid,))
                            conn.commit()
                            conn.close()
                            st.success("Rifa eliminada.")
                            st.rerun()

            st.markdown("---")
            st.subheader("➕ Subir nueva rifa")

            with st.form("nueva_rifa"):
                nombre_n = st.text_input("Nombre de la nueva rifa")
                cat_n = st.text_input("Categoría", value="Premio")
                precio_n = st.number_input("Precio por boleto (RD$)", min_value=0.0, value=5.0, step=0.50)
                minimo_n = st.number_input("Mínimo de boletos", min_value=1, value=10, step=1)
                total_n = st.number_input("Cantidad total de boletos", min_value=1, max_value=1000000, value=1000, step=100)
                fecha_n = st.text_input("Fecha/condición", value="Fecha pendiente")
                imagen_n = st.file_uploader("Imagen de la nueva rifa", type=["png","jpg","jpeg"], key="imagen_nueva")
                crear = st.form_submit_button("🚀 CREAR NUEVA RIFA", use_container_width=True)

            if crear:
                if not nombre_n.strip():
                    st.error("Escribe el nombre de la rifa.")
                else:
                    ruta_imagen = guardar_imagen(imagen_n, "rifas", nombre_n) if imagen_n else ""
                    conn = conectar()
                    cur = conn.cursor()
                    cur.execute("""
                        INSERT INTO rifas(nombre,categoria,precio_boleto,min_boletos,total_boletos,imagen,fecha,activa)
                        VALUES(?,?,?,?,?,?,?,1)
                    """, (nombre_n.strip(),cat_n.strip(),float(precio_n),int(minimo_n),int(total_n),ruta_imagen,fecha_n.strip()))
                    nuevo_id = cur.lastrowid
                    crear_boletos(conn, nuevo_id, int(total_n))
                    conn.commit()
                    conn.close()
                    st.success("🎉 Nueva rifa creada.")
                    st.rerun()

        # -------------------------------------------------
        # OFERTAS: MANUAL Y ALEATORIAS CON PREMIOS DIFERENTES
        # -------------------------------------------------
        with t4:
            st.subheader("⭐ Números de oferta y premios")

            conn = conectar()
            lista = conn.execute("SELECT id,nombre FROM rifas ORDER BY id").fetchall()
            conn.close()

            if lista:
                mapa = {nombre: rid for rid,nombre in lista}
                elegido = st.selectbox("Selecciona la rifa", list(mapa.keys()))
                rid = mapa[elegido]

                st.markdown("#### ➕ Oferta manual")
                with st.form("oferta_manual"):
                    numero = st.text_input("Número de boleto, ejemplo 00025")
                    premio = st.text_input("Premio", placeholder="RD$ 500 en efectivo")
                    valor = st.number_input("Valor del premio (RD$)", min_value=0.0, value=500.0, step=50.0)
                    guardar_oferta = st.form_submit_button("⭐ GUARDAR OFERTA", use_container_width=True)

                if guardar_oferta:
                    numero = numero.strip().zfill(5)
                    conn = conectar()
                    existe = conn.execute("SELECT id FROM boletos WHERE rifa_id=? AND numero=?", (rid,numero)).fetchone()
                    if not existe:
                        conn.close()
                        st.error("Ese número no existe.")
                    else:
                        try:
                            conn.execute("""
                                INSERT INTO ofertas(rifa_id,numero,premio,valor_premio,estado)
                                VALUES(?,?,?,?, 'disponible')
                            """, (rid,numero,premio.strip(),float(valor)))
                            conn.commit()
                            conn.close()
                            st.success("Oferta guardada.")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            conn.rollback()
                            conn.close()
                            st.error("Ese número ya tiene una oferta.")

                st.markdown("#### 🎲 Generar ofertas al azar")
                with st.form("ofertas_azar"):
                    cantidad_azar = st.number_input("Cantidad de números", min_value=1, max_value=1000, value=5, step=1)
                    premios = st.text_area(
                        "Premios, uno por línea con formato: descripción | valor",
                        value="RD$ 1,000 en efectivo | 1000\nRD$ 500 en efectivo | 500\nRD$ 250 en efectivo | 250"
                    )
                    generar = st.form_submit_button("🎲 GENERAR NÚMEROS AL AZAR", use_container_width=True)

                if generar:
                    filas_premio = [x.strip() for x in premios.splitlines() if x.strip()]
                    lista_premios = []
                    for fila in filas_premio:
                        partes = [x.strip() for x in fila.split("|", 1)]
                        descripcion = partes[0]
                        try:
                            valor_num = float(partes[1].replace(",", "")) if len(partes) == 2 else 0.0
                        except ValueError:
                            valor_num = 0.0
                        lista_premios.append((descripcion, valor_num))

                    if not lista_premios:
                        st.error("Escribe al menos un premio.")
                    else:
                        conn = conectar()
                        cur = conn.cursor()
                        cur.execute("""
                            SELECT b.numero FROM boletos b
                            LEFT JOIN ofertas o ON o.rifa_id=b.rifa_id AND o.numero=b.numero
                            WHERE b.rifa_id=? AND o.id IS NULL
                            ORDER BY RANDOM() LIMIT ?
                        """, (rid,int(cantidad_azar)))
                        numeros = [x[0] for x in cur.fetchall()]
                        for i,num in enumerate(numeros):
                            descripcion, valor_num = lista_premios[i % len(lista_premios)]
                            cur.execute("""
                                INSERT INTO ofertas(rifa_id,numero,premio,valor_premio,estado)
                                VALUES(?,?,?,?, 'disponible')
                            """, (rid,num,descripcion,float(valor_num)))
                        conn.commit()
                        conn.close()
                        st.success(f"Se generaron {len(numeros)} números de oferta al azar.")
                        if numeros: st.write("Números:", ", ".join(numeros))
                        st.rerun()

                st.markdown("#### 📋 Ofertas existentes")
                conn = conectar()
                ofertas = conn.execute("""
                    SELECT id,numero,premio,valor_premio,estado
                    FROM ofertas WHERE rifa_id=? ORDER BY numero
                """, (rid,)).fetchall()
                conn.close()

                for oid,num,premio,valor,estado in ofertas:
                    a,b,c,d = st.columns([1,2,1,1])
                    a.write(f"🎟️ **{num}**")
                    b.write(premio)
                    c.write(f"RD$ {valor:.2f}" if valor else "Valor no indicado")
                    if d.button("🗑️ Eliminar", key=f"del_oferta_{oid}"):
                        conn = conectar()
                        conn.execute("DELETE FROM ofertas WHERE id=?", (oid,))
                        conn.commit()
                        conn.close()
                        st.rerun()

        # -------------------------------------------------
        # MÉTODOS DE PAGO: AGREGAR, EDITAR, ACTIVAR/DESACTIVAR
        # -------------------------------------------------
        with t5:
            st.subheader("🏦 Métodos de pago")
            st.caption("Agrega bancos o métodos nuevos sin tocar las rifas ni los boletos existentes.")

            metodos_admin = obtener_metodos_pago(False)

            for mid, nombre_m, titular_m, tipo_m, cuenta_m, imagen_m, activo_m in metodos_admin:
                with st.expander(f"{'🟢' if activo_m else '⚪'} {nombre_m}"):
                    with st.form(f"editar_metodo_{mid}"):
                        nuevo_nombre = st.text_input("Nombre del banco/método", value=nombre_m)
                        nuevo_titular = st.text_input("Titular", value=titular_m)
                        nuevo_tipo = st.text_input("Tipo de cuenta", value=tipo_m)
                        nueva_cuenta = st.text_input("Número de cuenta", value=cuenta_m)
                        nueva_imagen = st.file_uploader(
                            "Cambiar logo (opcional)",
                            type=["png","jpg","jpeg"],
                            key=f"logo_metodo_{mid}"
                        )
                        activo = st.checkbox("Método activo para los clientes", value=bool(activo_m))
                        guardar_metodo = st.form_submit_button("💾 GUARDAR CAMBIOS", use_container_width=True)

                    if guardar_metodo:
                        if not nuevo_nombre.strip() or not nuevo_titular.strip() or not nueva_cuenta.strip():
                            st.error("Nombre, titular y número de cuenta son obligatorios.")
                        else:
                            ruta_logo = imagen_m or ""
                            if nueva_imagen:
                                ruta_logo = guardar_imagen(nueva_imagen, "metodos_pago", nuevo_nombre)

                            conn = conectar()
                            try:
                                conn.execute("""
                                    UPDATE metodos_pago
                                    SET nombre=?, titular=?, tipo_cuenta=?, numero_cuenta=?, imagen=?, activo=?
                                    WHERE id=?
                                """, (
                                    nuevo_nombre.strip(),
                                    nuevo_titular.strip(),
                                    nuevo_tipo.strip() or "Ahorros",
                                    nueva_cuenta.strip(),
                                    ruta_logo,
                                    1 if activo else 0,
                                    mid
                                ))
                                conn.commit()
                                st.success("Método de pago actualizado.")
                            except sqlite3.IntegrityError:
                                conn.rollback()
                                st.error("Ya existe otro método con ese nombre.")
                            finally:
                                conn.close()
                            st.rerun()

                    if st.button(
                        "🗑️ ELIMINAR MÉTODO",
                        key=f"eliminar_metodo_{mid}",
                        use_container_width=True
                    ):
                        conn = conectar()
                        usos = conn.execute(
                            "SELECT COUNT(*) FROM boletos WHERE metodo_pago=?",
                            (nombre_m,)
                        ).fetchone()[0]

                        if usos:
                            # No borramos el registro si tiene historial de pagos.
                            conn.execute(
                                "UPDATE metodos_pago SET activo=0 WHERE id=?",
                                (mid,)
                            )
                            conn.commit()
                            conn.close()
                            st.warning("El método tiene historial de pagos, por seguridad se desactivó en vez de borrarlo.")
                        else:
                            conn.execute("DELETE FROM metodos_pago WHERE id=?", (mid,))
                            conn.commit()
                            conn.close()
                            st.success("Método de pago eliminado.")
                        st.rerun()

            st.markdown("---")
            st.subheader("➕ Agregar nuevo método de pago")

            with st.form("nuevo_metodo_pago"):
                nombre_pago = st.text_input("Banco / método de pago", placeholder="Ej.: Banco BHD")
                titular_pago = st.text_input("Titular de la cuenta")
                tipo_pago = st.text_input("Tipo de cuenta", value="Ahorros")
                cuenta_pago = st.text_input("Número de cuenta")
                logo_pago = st.file_uploader(
                    "Logo del banco/método",
                    type=["png","jpg","jpeg"],
                    key="nuevo_logo_metodo"
                )
                crear_metodo = st.form_submit_button("➕ AGREGAR MÉTODO DE PAGO", use_container_width=True)

            if crear_metodo:
                if not nombre_pago.strip() or not titular_pago.strip() or not cuenta_pago.strip():
                    st.error("Completa banco/método, titular y número de cuenta.")
                else:
                    ruta_logo = guardar_imagen(logo_pago, "metodos_pago", nombre_pago) if logo_pago else ""
                    conn = conectar()
                    try:
                        conn.execute("""
                            INSERT INTO metodos_pago
                            (nombre,titular,tipo_cuenta,numero_cuenta,imagen,activo)
                            VALUES (?,?,?,?,?,1)
                        """, (
                            nombre_pago.strip(),
                            titular_pago.strip(),
                            tipo_pago.strip() or "Ahorros",
                            cuenta_pago.strip(),
                            ruta_logo
                        ))
                        conn.commit()
                        st.success("🎉 Nuevo método de pago agregado y activado.")
                    except sqlite3.IntegrityError:
                        conn.rollback()
                        st.error("Ese método de pago ya existe. Puedes editarlo arriba.")
                    finally:
                        conn.close()
                    st.rerun()

    elif admin_password:
        st.error("Contraseña incorrecta.")
