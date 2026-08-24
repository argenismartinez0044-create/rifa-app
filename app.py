import datetime
import os
import random
import sqlite3
import streamlit as st
from PIL import Image

# ---------------------------------------------------------
# 1. CONFIGURACIÓN Y BASE DE DATOS
# ---------------------------------------------------------
st.set_page_config(
    page_title="Sirio Rifas RD",
    page_icon="🎟️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

DB_FILE = "rifa_sirio.db"


def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Tabla de Rifas
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS rifas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            categoria TEXT,
            precio_boleto REAL,
            min_boletos INTEGER,
            total_boletos INTEGER,
            imagen_path TEXT,
            fecha_sorteo TEXT
        )
    """
    )

    # Tabla de Boletos
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS boletos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rifa_id INTEGER,
            numero TEXT,
            estado TEXT DEFAULT 'disponible',
            nombre_cliente TEXT,
            telefono TEXT,
            metodo_pago TEXT,
            comprobante_path TEXT,
            fecha_reserva TIMESTAMP,
            FOREIGN KEY (rifa_id) REFERENCES rifas (id)
        )
    """
    )

    # Insertar Rifa inicial si no existe ninguna
    c.execute("SELECT COUNT(*) FROM rifas")
    if c.fetchone()[0] == 0:
        c.execute(
            """
            INSERT INTO rifas (nombre, categoria, precio_boleto, min_boletos, total_boletos, imagen_path, fecha_sorteo)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                "Play Play station 5 pro",
                "Juego",
                5.0,
                15,
                10000,
                "play.jpg",
                "Fecha pendiente de asignar",
            ),
        )

        c.execute(
            """
            INSERT INTO rifas (nombre, categoria, precio_boleto, min_boletos, total_boletos, imagen_path, fecha_sorteo)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                "5 iPhone 17 Pro Max",
                "TELÉFONO",
                15.0,
                10,
                10000,
                "iphone.jpg",
                "Se coloca con el 80% vendido",
            ),
        )

        conn.commit()

        # Generar boletos para las rifas iniciales
        for rifa_id in [1, 2]:
            numeros = [f"{i:05d}" for i in range(1, 1001)]
            c.executemany(
                "INSERT INTO boletos (rifa_id, numero) VALUES (?, ?)",
                [(rifa_id, n) for n in numeros],
            )
        conn.commit()

    conn.close()


def liberar_expirados():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    limite = datetime.datetime.now() - datetime.timedelta(hours=24)
    c.execute(
        """
        UPDATE boletos 
        SET estado = 'disponible', nombre_cliente = NULL, telefono = NULL, 
            metodo_pago = NULL, comprobante_path = NULL, fecha_reserva = NULL
        WHERE estado = 'reservado' AND fecha_reserva < ?
    """,
        (limite,),
    )
    conn.commit()
    conn.close()


init_db()
liberar_expirados()

# ---------------------------------------------------------
# 2. NAV Y HEADER PRINCIPAL
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    /* Fondo degradado oscuro premium */
    .stApp {
        background: linear-gradient(135deg, #0b0d17 0%, #171b2e 50%, #080910 100%) !important;
        color: #FFFFFF;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- MENÚ LATERAL ---
seccion = st.sidebar.radio("Navegación", ["🏠 Inicio & Catálogo", "🎟️ Mis Boletos", "🏆 Ganadores"])

# ---------------------------------------------------------
# 3. SECCIÓN: INICIO Y CATÁLOGO DE RIFAS
# ---------------------------------------------------------
if seccion == "🏠 Inicio & Catálogo":
   # Encabezado con Logo en la esquina izquierda y Título a la derecha
    col_logo, col_titulo = st.columns([1, 2])

    with col_logo:
        st.image("logo.png", width=250)

    with col_titulo:
        st.markdown(
            "<p style='color: #F5C518; font-weight: bold; margin-bottom: 0;'>Experiencia exclusiva — La plataforma más lujosa para participar y ganar.</p>", 
            unsafe_allow_html=True
        )
        st.markdown(
            "<h1 style='color: #FFFFFF; font-size: 2.2rem; margin-top: 0;'>Premios extraordinarios garantizados</h1>", 
            unsafe_allow_html=True
        )

    st.markdown("---")

    # Botones desplegables informativos
    with st.expander("📺 **¿CÓMO JUGAR?** — 5 pasos simples para participar y ganar"):
        st.write(
            "1. Selecciona la rifa en la que deseas participar del catálogo."
        )
        st.write(
            "2. Elige la cantidad de boletos que deseas comprar y completa tus datos."
        )
        st.write(
            "3. Realiza la transferencia bancaria al banco de tu preferencia (Banreservas o Banco Popular)."
        )
        st.write("4. Sube la foto del comprobante de pago.")
        st.write(
            "5. Tu boleto quedará reservado e inmediatamente podrás consultarlo en el **Verificador de Boletos**."
        )

    st.markdown("---")
    st.subheader("🛍️ CATÁLOGO DE RIFAS")

    # Filtros de Categorías
    cat_filtro = st.radio(
        "Filtrar por categoría:",
        ["TODOS", "DINERO", "TELÉFONO", "VEHÍCULOS"],
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

    # Despliegue de tarjetas de rifa en cuadrícula
    cols = st.columns(2)
    for idx, r in enumerate(rifas):
        (
            r_id,
            r_nombre,
            r_cat,
            r_precio,
            r_min,
            r_total,
            r_img,
            r_fecha,
        ) = r

        # Calcular progreso de ventas (%)
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

            if st.button(
                f"🎮 JUGAR EN {r_nombre.upper()}", key=f"btn_jugar_{r_id}"
            ):
                st.session_state["rifa_seleccionada"] = r_id
                st.session_state["nombre_rifa"] = r_nombre
                st.session_state["precio_rifa"] = r_precio
                st.session_state["min_rifa"] = r_min

    # Formulario de compra si selecciona una rifa
    if "rifa_seleccionada" in st.session_state:
        st.markdown("---")
        
        nombre = st.session_state['nombre_rifa']
        precio = st.session_state['precio_rifa']
        
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
                border-radius: 16px;
                padding: 25px 30px;
                text-align: center;
                box-shadow: 0px 8px 24px rgba(0, 0, 0, 0.4);
                border: 1px solid rgba(255, 255, 255, 0.1);
                margin-bottom: 25px;
            ">
                <span style="
                    background-color: #F5C518;
                    color: #000;
                    font-size: 0.85rem;
                    font-weight: 800;
                    padding: 4px 12px;
                    border-radius: 20px;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                ">Estás participando en</span>
                <h1 style="
                    color: #FFFFFF;
                    font-size: 2.5rem;
                    font-weight: 900;
                    margin: 10px 0 5px 0;
                    text-shadow: 2px 2px 10px rgba(0,0,0,0.5);
                ">🎉 {nombre} 🎉</h1>
                <p style="
                    color: #E0E0E0;
                    font-size: 1.2rem;
                    margin: 0;
                ">Precio por boleto: <strong style="color: #F5C518;">RD$ {precio:.2f}</strong></p>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.subheader("💳 Métodos de Pago")
        st.caption(
            "Selecciona tu banco para ver la cuenta de transferencia:"
        )

        tab_banres, tab_pop = st.tabs(["Banreservas", "Banco Popular"])

        with tab_banres:
            st.markdown("### 🔴 Banreservas")
            c1, c2 = st.columns(2)
            with c1:
                st.write("**Tipo de Cuenta:** Ahorros")
                st.write("**Titular:** ARGENIS MARTINEZ C.")
            with c2:
                st.write("**Número de Cuenta:** (Toca para copiar)")
                st.code("9606561652", language="text")

        with tab_pop:
            st.markdown("### 🔵 Banco Popular")
            c1, c2 = st.columns(2)
            with c1:
                st.write("**Tipo de Cuenta:** Ahorros")
                st.write("**Titular:** ARGENIS MARTINEZ")
            with c2:
                st.write("**Número de Cuenta:** (Toca para copiar)")
                st.code("821794971", language="text")

        st.markdown("---")
        st.subheader("📝 Registrar Boletos")

        with st.form("form_compra"):
            nombre_cliente = st.text_input("Nombre Completo")
            telefono_cliente = st.text_input(
                "Número de Teléfono / WhatsApp (Ej: 8091234567)"
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
                "Subir foto del comprobante de pago",
                type=["png", "jpg", "jpeg"],
            )

            total_pagar = cant_boletos * st.session_state["precio_rifa"]
            st.markdown(f"### Total a pagar: **RD$ {total_pagar:.2f}**")

            btn_confirmar = st.form_submit_button("✅ RESERVAR MIS BOLETOS")

        if btn_confirmar:
            if not nombre_cliente or not telefono_cliente or not comprobante_file:
                st.error("Por favor completa todos los campos requeridos.")
            else:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()

                # Buscar boletos disponibles
                c.execute(
                    "SELECT id, numero FROM boletos WHERE rifa_id = ? AND estado = 'disponible'",
                    (st.session_state["rifa_seleccionada"],),
                )
                disp = c.fetchall()

                if len(disp) < cant_boletos:
                    st.error("No hay suficientes boletos disponibles.")
                else:
                    asignados = random.sample(disp, cant_boletos)

                    os.makedirs("comprobantes", exist_ok=True)
                    path_comp = f"comprobantes/{telefono_cliente}_{datetime.datetime.now().timestamp()}.jpg"
                    img = Image.open(comprobante_file)
                    img.save(path_comp)

                    ahora = datetime.datetime.now()
                    num_asignados = []

                    for b_id, b_num in asignados:
                        num_asignados.append(b_num)
                        c.execute(
                            """
                            UPDATE boletos 
                            SET estado = 'reservado', nombre_cliente = ?, telefono = ?, 
                                metodo_pago = ?, comprobante_path = ?, fecha_reserva = ?
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

                    st.success("🎉 ¡Boletos asignados exitosamente!")
                    st.warning(
                        "⚠️ Tus números están reservados. Serán confirmados tras la verificación de tu transferencia."
                    )

                    st.subheader("🎟️ Tus Números Asignados:")
                    cols_num = st.columns(min(len(num_asignados), 5))
                    for i, n in enumerate(num_asignados):
                        cols_num[i % 5].metric("Boleto", n)

# ---------------------------------------------------------
# 4. SECCIÓN: VERIFICADOR DE BOLETOS
# ---------------------------------------------------------
elif seccion == "🔎 Verificador de boletos":
    st.header("🔎 Verificador de Boletos")
    st.write(
        "Consulta instantáneamente todos los boletos asignados a tu número de teléfono."
    )

    tel_buscar = st.text_input(
        "Ingresa tu número de teléfono / WhatsApp registrado:"
    )

    if st.button("Buscar Mis Boletos"):
        if not tel_buscar:
            st.warning("Por favor ingresa un número de teléfono.")
        else:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute(
                """
                SELECT b.numero, b.estado, r.nombre, b.fecha_reserva 
                FROM boletos b
                JOIN rifas r ON b.rifa_id = r.id
                WHERE b.telefono = ?
            """,
                (tel_buscar,),
            )
            mis_boletos = c.fetchall()
            conn.close()

            if not mis_boletos:
                st.info(
                    "No se encontraron boletos registrados con este número."
                )
            else:
                st.success(f"Se encontraron {len(mis_boletos)} boletos:")

                for num, est, rifa_nom, fecha in mis_boletos:
                    col_a, col_b, col_c = st.columns(3)
                    col_a.write(f"🎟️ **Boleto:** `{num}`")
                    col_b.write(f"🏆 **Rifa:** {rifa_nom}")
                    col_c.write(f"📌 **Estado:** `{est.upper()}`")
                    st.markdown("---")

# ---------------------------------------------------------
# 5. SECCIÓN: CÓMO JUGAR
# ---------------------------------------------------------
elif seccion == "❓ Cómo jugar":
    st.header("❓ Cómo Jugar en Rifas Luxury RD")
    st.markdown(
        """
    1. **Explora el catálogo:** Elige tu premio preferido (autos, celulares, dinero).
    2. **Selecciona tus números:** Elige la cantidad de boletos que deseas comprar.
    3. **Haz tu pago:** Realiza la transferencia a nuestras cuentas de **Banreservas** o **Banco Popular**.
    4. **Sube tu comprobante:** Adjunta la imagen de tu transferencia en el formulario.
    5. **Consulta tus boletos:** Usa nuestro **Verificador de Boletos** con tu número telefónico para confirmar tus números en tiempo real.
    """
    )

# ---------------------------------------------------------
# 6. SECCIÓN: GANADORES
# ---------------------------------------------------------
elif seccion == "🏆 Ganadores":
    st.header("🏆 Galería de Ganadores")
    st.write("Próximamente estaremos publicando las entregas directas a nuestros ganadores.")

# ---------------------------------------------------------
# 7. SECCIÓN: ADMINISTRACIÓN
# ---------------------------------------------------------
elif seccion == "⚙️ Administración":
    st.header("⚙️ Panel de Administración")
    clave = st.text_input("Contraseña de administrador", type="password")

    if clave == "admin123":
        st.success("Acceso concedido")

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()

        st.subheader("📌 Reservas Pendientes por Verificar")
        c.execute(
            """
            SELECT b.id, b.numero, b.nombre_cliente, b.telefono, b.metodo_pago, b.comprobante_path, r.nombre 
            FROM boletos b
            JOIN rifas r ON b.rifa_id = r.id
            WHERE b.estado = 'reservado'
        """
        )
        pendientes = c.fetchall()

        if not pendientes:
            st.info("No hay pagos pendientes de revisión.")
        else:
            for b_id, num, nom, tel, met, img_p, r_nom in pendientes:
                st.write(
                    f"**Rifa:** {r_nom} | **Boleto:** `{num}` | **Cliente:** {nom} | **Tel:** {tel} | **Banco:** {met}"
                )
                if os.path.exists(img_p):
                    st.image(img_p, width=250)

                c1, c2 = st.columns(2)
                if c1.button(f"Aprobar {num}", key=f"ap_{b_id}"):
                    c.execute(
                        "UPDATE boletos SET estado = 'confirmado' WHERE id = ?",
                        (b_id,),
                    )
                    conn.commit()
                    st.rerun()

                if c2.button(f"Rechazar {num}", key=f"rec_{b_id}"):
                    c.execute(
                        """
                        UPDATE boletos 
                        SET estado = 'disponible', nombre_cliente = NULL, telefono = NULL, 
                            metodo_pago = NULL, comprobante_path = NULL, fecha_reserva = NULL
                        WHERE id = ?
                    """,
                        (b_id,),
                    )
                    conn.commit()
                    st.rerun()
                st.markdown("---")

        conn.close()

