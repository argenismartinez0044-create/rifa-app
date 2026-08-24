import os
import random
import sqlite3
import datetime

from PIL import Image
import streamlit as st


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "rifas_v4.db")

WHATSAPP_NUMERO = "8294835217"

st.set_page_config(
    page_title="Rifas Sirio RD",
    page_icon="🎲",
    layout="wide"
)


# ============================================================
# FUNCIONES GENERALES
# ============================================================

def conectar():
    return sqlite3.connect(DB_FILE)


def archivo(nombre):
    return os.path.join(BASE_DIR, nombre)


# ============================================================
# BASE DE DATOS
# ============================================================

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

    # --------------------------------------------------------
    # Crear las rifas solamente si la base está vacía
    # --------------------------------------------------------

    c.execute("SELECT COUNT(*) FROM rifas")
    cantidad = c.fetchone()[0]

    if cantidad == 0:

        c.execute("""
            INSERT INTO rifas
            (nombre, categoria, precio_boleto, min_boletos,
             total_boletos, imagen, fecha)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            "PlayStation 5 Pro",
            "Juego",
            5.0,
            15,
            100000,
            "play.jpg",
            "Fecha pendiente"
        ))

        c.execute("""
            INSERT INTO rifas
            (nombre, categoria, precio_boleto, min_boletos,
             total_boletos, imagen, fecha)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            "5 iPhone 17 Pro Max",
            "TELÉFONO",
            15.0,
            10,
            100000,
            "iphone.jpg",
            "Al vender el 80%"
        ))

        conn.commit()

        # Obtener los IDs reales
        c.execute("SELECT id FROM rifas ORDER BY id")
        ids = [fila[0] for fila in c.fetchall()]

        # Crear los 100,000 boletos por rifa
        for rifa_id in ids:

            c.executemany(
                "INSERT INTO boletos (rifa_id, numero) VALUES (?, ?)",
                [
                    (rifa_id, f"{n:05d}")
                    for n in range(1, 100001)
                ]
            )

        conn.commit()

    # Mantener valores correctos
    c.execute("""
        UPDATE rifas
        SET min_boletos = 15
        WHERE nombre = 'PlayStation 5 Pro'
    """)

    c.execute("""
        UPDATE rifas
        SET min_boletos = 10
        WHERE nombre = '5 iPhone 17 Pro Max'
    """)

    conn.commit()
    conn.close()


def liberar_expirados():

    conn = conectar()
    c = conn.cursor()

    # 24 horas para confirmar
    limite = (
        datetime.datetime.now()
        - datetime.timedelta(hours=24)
    )

    c.execute("""
        UPDATE boletos
        SET
            estado = 'disponible',
            usuario_nombre = NULL,
            usuario_telefono = NULL,
            metodo_pago = NULL,
            comprobante = NULL,
            fecha_reserva = NULL
        WHERE estado = 'reservado'
        AND fecha_reserva < ?
    """, (limite,))

    conn.commit()
    conn.close()


init_db()
liberar_expirados()


# ============================================================
# ESTILOS
# ============================================================

st.markdown("""
<style>

.stApp {
    background:
    linear-gradient(
        135deg,
        #0b0d17 0%,
        #171b2e 50%,
        #080910 100%
    );
}

.combo-titulo {
    text-align: center;
    font-size: 18px;
    font-weight: 800;
    margin-bottom: 10px;
}

.paso {
    background:
    linear-gradient(
        135deg,
        #0f2027,
        #203a43,
        #2c5364
    );
    padding: 20px;
    border-radius: 18px;
    margin: 15px 0;
    text-align: center;
}

.cuenta-box {
    background: rgba(255,255,255,0.08);
    padding: 20px;
    border-radius: 15px;
    margin-top: 15px;
}

.numero-cuenta {
    font-size: 28px;
    font-weight: 900;
    letter-spacing: 3px;
    text-align: center;
    margin: 15px 0;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# LIMPIAR COMPRA
# ============================================================

def limpiar_compra():

    claves = [
        "rifa_seleccionada",
        "nombre_rifa",
        "precio_rifa",
        "min_rifa",
        "paso_compra",
        "nombre_cliente",
        "telefono_cliente",
        "cant_boletos",
        "nivel_boletos",
        "banco_pago",
        "boletos_confirmados",
        "mostrar_confirmacion"
    ]

    for clave in claves:
        st.session_state.pop(clave, None)


# ============================================================
# SELECCIONAR RIFA
# ============================================================

def seleccionar_rifa(
    rifa_id,
    nombre,
    precio,
    minimo
):

    st.session_state["rifa_seleccionada"] = rifa_id
    st.session_state["nombre_rifa"] = nombre
    st.session_state["precio_rifa"] = precio
    st.session_state["min_rifa"] = minimo

    # Siempre comienza desde los datos
    st.session_state["paso_compra"] = 1

    # Borrar cualquier selección anterior
    st.session_state.pop("banco_pago", None)
    st.session_state.pop("cant_boletos", None)
    st.session_state.pop("nivel_boletos", None)


# ============================================================
# SELECCIONAR COMBO
# ============================================================

def seleccionar_combo(
    cantidad,
    nombre
):

    st.session_state["cant_boletos"] = cantidad
    st.session_state["nivel_boletos"] = nombre


# ============================================================
# SELECCIONAR BANCO
# ============================================================

def seleccionar_banco(nombre_banco):

    st.session_state["banco_pago"] = nombre_banco


# ============================================================
# DATOS BANCARIOS
# ============================================================

BANCOS = {

    "Banreservas": {
        "logo": "barreserva.png",
        "titular": "ARGENIS MARTINEZ C.",
        "tipo": "Ahorros",
        "cuenta": "9606561652"
    },

    "Banco Popular": {
        "logo": "popular.png",
        "titular": "ARGENIS MARTINEZ",
        "tipo": "Ahorros",
        "cuenta": "821794971"
    }
}


# ============================================================
# VENTANA DE CONFIRMACIÓN
# ============================================================

@st.dialog("🎟️ Boletos registrados")
def confirmacion():

    numeros = st.session_state.get(
        "boletos_confirmados",
        []
    )

    st.success(
        "🎉 ¡Tus boletos fueron registrados correctamente!"
    )

    st.markdown("### 🎟️ Tus números")

    texto = ", ".join(numeros)

    st.code(texto)

    st.markdown(
        f"""
        <button
            onclick="navigator.clipboard.writeText('{texto}')"
            style="
                width:100%;
                padding:12px;
                border:0;
                border-radius:10px;
                font-weight:800;
                cursor:pointer;
            "
        >
        📋 COPIAR BOLETOS
        </button>
        """,
        unsafe_allow_html=True
    )

    st.warning(
        "⏳ Tus boletos quedan reservados durante "
        "un máximo de 24 horas mientras se valida "
        "el comprobante."
    )

    st.info(
        "Guarda tus números para poder verificarlos "
        "posteriormente."
    )

    if st.button(
        "✅ ENTENDIDO",
        use_container_width=True
    ):

        limpiar_compra()

        st.session_state.pop(
            "mostrar_confirmacion",
            None
        )

        st.rerun()


if st.session_state.get("mostrar_confirmacion"):
    confirmacion()


# ============================================================
# SOPORTE IA
# ============================================================

@st.dialog("🤖 Asistente Virtual")
def soporte_ia():

    st.caption(
        "Asistente de Rifas Sirio RD"
    )

    if "chat" not in st.session_state:

        st.session_state["chat"] = [
            {
                "role": "assistant",
                "content":
                "¡Hola! 👋 ¿En qué puedo ayudarte?"
            }
        ]

    for mensaje in st.session_state["chat"]:

        with st.chat_message(
            mensaje["role"]
        ):
            st.markdown(
                mensaje["content"]
            )

    pregunta = st.chat_input(
        "Escribe tu pregunta..."
    )

    if pregunta:

        st.session_state["chat"].append({
            "role": "user",
            "content": pregunta
        })

        texto = pregunta.lower()

        if any(
            x in texto
            for x in [
                "jugar",
                "participar",
                "comprar"
            ]
        ):

            respuesta = """
**Cómo jugar:**

1. Selecciona una rifa.
2. Selecciona la cantidad de boletos.
3. Completa tus datos.
4. Selecciona el banco.
5. Realiza el pago.
6. Sube el comprobante.
7. Guarda tus números.
"""

        elif any(
            x in texto
            for x in [
                "banco",
                "cuenta",
                "banreservas",
                "popular"
            ]
        ):

            respuesta = (
                "Los bancos aparecen después de "
                "completar los datos de la compra. "
                "Podrás elegir Banreservas o Banco Popular."
            )

        elif any(
            x in texto
            for x in [
                "boleto",
                "numero",
                "número",
                "verificar"
            ]
        ):

            respuesta = (
                "Puedes consultar tus boletos en "
                "🔎 Verificador de boletos."
            )

        else:

            respuesta = (
                f"Para ayuda personalizada puedes "
                f"contactar por WhatsApp: "
                f"{WHATSAPP_NUMERO}"
            )

        st.session_state["chat"].append({
            "role": "assistant",
            "content": respuesta
        })

        st.rerun()


# ============================================================
# SIDEBAR
# ============================================================

seccion = st.sidebar.radio(
    "Navegación",
    [
        "🏠 Inicio & Catálogo",
        "🔎 Verificador de boletos",
        "❓ Cómo jugar",
        "🤖 Soporte IA",
        "🏆 Ganadores",
        "⚙️ Administración"
    ]
)

st.sidebar.markdown("---")

if st.sidebar.button(
    "🤖 Abrir Soporte IA",
    use_container_width=True
):
    soporte_ia()


# ============================================================
# INICIO
# ============================================================

if seccion == "🏠 Inicio & Catálogo":

    col1, col2 = st.columns([1, 2])

    with col1:

        logo = archivo("logo.png")

        if os.path.exists(logo):
            st.image(
                logo,
                width=220
            )

    with col2:

        st.markdown(
            "### Plataforma Exclusiva de Rifas"
        )

        st.markdown(
            "# Premios Exclusivos Garantizados"
        )

    st.markdown("---")

    with st.expander(
        "📺 ¿CÓMO PARTICIPAR?"
    ):

        st.write("""
        1. Selecciona una rifa.
        2. Selecciona la cantidad de boletos.
        3. Completa tu nombre y teléfono.
        4. Selecciona el banco.
        5. Realiza el pago.
        6. Sube el comprobante.
        7. Guarda tus números.
        """)

    st.markdown("---")

    st.subheader("🛍️ CATÁLOGO DE RIFAS")

    categoria = st.radio(
        "Categoría",
        [
            "TODOS",
            "Juego",
            "TELÉFONO",
            "DINERO",
            "VEHÍCULOS"
        ],
        horizontal=True
    )

    conn = conectar()
    c = conn.cursor()

    if categoria == "TODOS":

        c.execute(
            "SELECT * FROM rifas ORDER BY id"
        )

    else:

        c.execute(
            """
            SELECT *
            FROM rifas
            WHERE categoria = ?
            ORDER BY id
            """,
            (categoria,)
        )

    rifas = c.fetchall()
    conn.close()

    columnas = st.columns(2)

    for indice, rifa in enumerate(rifas):

        (
            rifa_id,
            nombre,
            categoria_rifa,
            precio,
            minimo,
            total,
            imagen,
            fecha
        ) = rifa

        conn = conectar()
        c = conn.cursor()

        c.execute(
            """
            SELECT COUNT(*)
            FROM boletos
            WHERE rifa_id = ?
            AND estado IN (
                'reservado',
                'confirmado'
            )
            """,
            (rifa_id,)
        )

        vendidos = c.fetchone()[0]
        conn.close()

        progreso = (
            vendidos / total
            if total
            else 0
        )

        with columnas[indice % 2]:

            st.markdown(
                f"### 🏷️ {nombre}"
            )

            st.caption(
                f"Categoría: {categoria_rifa}"
            )

            imagen_path = archivo(imagen)

            if os.path.exists(imagen_path):

                st.image(
                    imagen_path,
                    use_container_width=True
                )

            st.write(
                f"📅 **Fecha:** {fecha}"
            )

            st.write(
                f"📊 **Progreso:** "
                f"{int(progreso * 100)}%"
            )

            st.progress(progreso)

            st.markdown(
                f"### RD$ {precio:.2f}"
            )

            st.caption(
                f"Mínimo: {minimo} boletos"
            )

            if "PlayStation" in nombre:

                texto = (
                    f"🎮 JUGAR POR "
                    f"{nombre.upper()}"
                )

            else:

                texto = (
                    f"📱 PARTICIPAR POR "
                    f"{nombre.upper()}"
                )

            st.button(
                texto,
                key=f"rifa_{rifa_id}",
                on_click=seleccionar_rifa,
                args=(
                    rifa_id,
                    nombre,
                    precio,
                    minimo
                ),
                use_container_width=True
            )


    # ========================================================
    # COMPRA
    # ========================================================

    if "rifa_seleccionada" in st.session_state:

        st.markdown("---")

        nombre = st.session_state[
            "nombre_rifa"
        ]

        precio = float(
            st.session_state[
                "precio_rifa"
            ]
        )

        minimo = int(
            st.session_state[
                "min_rifa"
            ]
        )

        paso = st.session_state.get(
            "paso_compra",
            1
        )

        st.markdown(
            f"""
            <div class="paso">
                <small>RIFA SELECCIONADA</small>
                <h2>{nombre}</h2>
                <p>
                    Precio por boleto:
                    <b>RD$ {precio:.2f}</b>
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )


        # ====================================================
        # PASO 1 - DATOS + COMBOS
        # ====================================================

        if paso == 1:

            st.subheader(
                "📝 1. Completa tus datos"
            )

            st.markdown(
                "### 🎟️ Cantidad de boletos"
            )

            st.caption(
                f"El mínimo es de {minimo} boletos."
            )

            combos = [
                ("🟢 NORMAL", minimo),
                ("🔵 DOBLE", minimo * 2),
                ("🟣 INTERMEDIO", minimo * 3),
                ("🟠 PROFESIONAL", minimo * 5),
                ("🔴 PRO", minimo * 10)
            ]

            combos = [
                (
                    nombre_combo,
                    min(cantidad, 100)
                )
                for nombre_combo, cantidad
                in combos
            ]

            cantidad_actual = st.session_state.get(
                "cant_boletos",
                minimo
            )

            nivel_actual = st.session_state.get(
                "nivel_boletos",
                "🟢 NORMAL"
            )

            columnas_combo = st.columns(5)

            for i, (
                nombre_combo,
                cantidad_combo
            ) in enumerate(combos):

                seleccionado = (
                    cantidad_actual == cantidad_combo
                    and nivel_actual == nombre_combo
                )

                with columnas_combo[i]:

                    if seleccionado:

                        texto = (
                            f"✅ {nombre_combo}\n"
                            f"{cantidad_combo} BOLETOS"
                        )

                    else:

                        texto = (
                            f"{nombre_combo}\n"
                            f"{cantidad_combo} BOLETOS"
                        )

                    st.button(
                        texto,
                        key=(
                            f"combo_"
                            f"{st.session_state['rifa_seleccionada']}_"
                            f"{i}"
                        ),
                        on_click=seleccionar_combo,
                        args=(
                            cantidad_combo,
                            nombre_combo
                        ),
                        use_container_width=True
                    )

            st.success(
                f"🎟️ Cantidad seleccionada: "
                f"**{cantidad_actual} boletos**"
            )

            # ------------------------------------------------
            # DATOS DEL CLIENTE
            # ------------------------------------------------

            with st.form(
                "datos_cliente"
            ):

                nombre_cliente = st.text_input(
                    "👤 Nombre Completo",
                    value=st.session_state.get(
                        "nombre_cliente",
                        ""
                    )
                )

                telefono = st.text_input(
                    "📱 Teléfono / WhatsApp",
                    value=st.session_state.get(
                        "telefono_cliente",
                        ""
                    ),
                    placeholder="Ej: 8091234567"
                )

                cantidad_manual = st.number_input(
                    "✏️ Cantidad manual",
                    min_value=minimo,
                    max_value=100,
                    value=int(cantidad_actual),
                    step=1
                )

                total_pagar = (
                    cantidad_manual * precio
                )

                st.markdown(
                    f"""
                    ### 💰 Total:
                    **RD$ {total_pagar:.2f}**
                    """
                )

                continuar = st.form_submit_button(
                    "➡️ CONTINUAR AL PAGO",
                    use_container_width=True
                )

            if continuar:

                if not nombre_cliente.strip():

                    st.error(
                        "Escribe tu nombre completo."
                    )

                elif not telefono.strip():

                    st.error(
                        "Escribe tu teléfono/WhatsApp."
                    )

                else:

                    st.session_state[
                        "nombre_cliente"
                    ] = nombre_cliente.strip()

                    st.session_state[
                        "telefono_cliente"
                    ] = telefono.strip()

                    st.session_state[
                        "cant_boletos"
                    ] = int(cantidad_manual)

                    if (
                        int(cantidad_manual)
                        != cantidad_actual
                    ):

                        st.session_state[
                            "nivel_boletos"
                        ] = "✏️ MANUAL"

                    st.session_state[
                        "paso_compra"
                    ] = 2

                    st.session_state.pop(
                        "banco_pago",
                        None
                    )

                    st.rerun()


        # ====================================================
        # PASO 2 - BANCOS
        # ====================================================

        elif paso == 2:

            st.subheader(
                "💳 2. Selecciona tu banco"
            )

            st.caption(
                "Selecciona uno de los bancos para "
                "ver los datos de transferencia."
            )

            banco_actual = st.session_state.get(
                "banco_pago"
            )

            columnas_bancos = st.columns(2)

            for i, (
                nombre_banco,
                datos
            ) in enumerate(BANCOS.items()):

                with columnas_bancos[i]:

                    st.markdown(
                        f"### 🏦 {nombre_banco}"
                    )

                    logo_path = archivo(
                        datos["logo"]
                    )

                    # ----------------------------------------
                    # LOGO
                    # ----------------------------------------

                    if os.path.exists(logo_path):

                        st.image(
                            logo_path,
                            use_container_width=True
                        )

                    else:

                        st.error(
                            f"No se encontró "
                            f"{datos['logo']}"
                        )

                    seleccionado = (
                        banco_actual
                        == nombre_banco
                    )

                    st.button(
                        (
                            f"✅ {nombre_banco.upper()} SELECCIONADO"
                            if seleccionado
                            else
                            f"SELECCIONAR {nombre_banco.upper()}"
                        ),
                        key=f"banco_{i}",
                        on_click=seleccionar_banco,
                        args=(nombre_banco,),
                        use_container_width=True
                    )


            # ------------------------------------------------
            # INFORMACIÓN SOLAMENTE DESPUÉS DE SELECCIONAR
            # ------------------------------------------------

            if banco_actual:

                datos = BANCOS[
                    banco_actual
                ]

                logo_path = archivo(
                    datos["logo"]
                )

                st.markdown("---")

                col_logo, col_datos = st.columns(
                    [1, 2]
                )

                with col_logo:

                    if os.path.exists(
                        logo_path
                    ):

                        st.image(
                            logo_path,
                            width=240
                        )

                with col_datos:

                    st.markdown(
                        f"""
                        <div class="cuenta-box">

                        <h2>
                            🏦 {banco_actual}
                        </h2>

                        <p>
                            <b>Titular:</b>
                            {datos["titular"]}
                        </p>

                        <p>
                            <b>Tipo de cuenta:</b>
                            {datos["tipo"]}
                        </p>

                        <p>
                            <b>Número de cuenta:</b>
                        </p>

                        <div class="numero-cuenta">
                            {datos["cuenta"]}
                        </div>

                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                # --------------------------------------------
                # BOTÓN COPIAR CUENTA
                # --------------------------------------------

                cuenta = datos["cuenta"]

                st.markdown(
                    f"""
                    <button
                        onclick="
                        navigator.clipboard
                        .writeText('{cuenta}')
                        .then(() => {{
                            this.innerHTML =
                            '✅ NÚMERO COPIADO';
                        }});
                        "
                        style="
                            width:100%;
                            padding:15px;
                            margin:10px 0;
                            border:0;
                            border-radius:10px;
                            background:#F5C518;
                            color:#000;
                            font-size:16px;
                            font-weight:900;
                            cursor:pointer;
                        "
                    >
                    📋 COPIAR NÚMERO DE CUENTA
                    </button>
                    """,
                    unsafe_allow_html=True
                )

                total = (
                    st.session_state[
                        "cant_boletos"
                    ] * precio
                )

                st.markdown(
                    f"""
                    ### 💰 Total a pagar:
                    **RD$ {total:.2f}**
                    """
                )

                st.info(
                    "Realiza la transferencia y "
                    "después continúa para subir "
                    "el comprobante."
                )

                c1, c2 = st.columns(2)

                with c1:

                    if st.button(
                        "⬅️ VOLVER A MIS DATOS",
                        use_container_width=True
                    ):

                        st.session_state[
                            "paso_compra"
                        ] = 1

                        st.rerun()

                with c2:

                    if st.button(
                        "➡️ SUBIR COMPROBANTE",
                        use_container_width=True
                    ):

                        st.session_state[
                            "paso_compra"
                        ] = 3

                        st.rerun()

            else:

                st.info(
                    "👆 Selecciona Banreservas o "
                    "Banco Popular para mostrar "
                    "el titular y el número de cuenta."
                )

                if st.button(
                    "⬅️ VOLVER A MIS DATOS",
                    use_container_width=True
                ):

                    st.session_state[
                        "paso_compra"
                    ] = 1

                    st.rerun()


        # ====================================================
        # PASO 3 - COMPROBANTE
        # ====================================================

        elif paso == 3:

            st.subheader(
                "📤 3. Sube tu comprobante"
            )

            banco = st.session_state[
                "banco_pago"
            ]

            cantidad = st.session_state[
                "cant_boletos"
            ]

            total = cantidad * precio

            st.info(
                f"""
                🏦 Banco: **{banco}**

                🎟️ Boletos: **{cantidad}**

                💰 Total: **RD$ {total:.2f}**
                """
            )

            comprobante = st.file_uploader(
                "📸 Selecciona la imagen del comprobante",
                type=[
                    "png",
                    "jpg",
                    "jpeg"
                ]
            )

            c1, c2 = st.columns(2)

            with c1:

                if st.button(
                    "⬅️ VOLVER AL BANCO",
                    use_container_width=True
                ):

                    st.session_state[
                        "paso_compra"
                    ] = 2

                    st.rerun()

            with c2:

                reservar = st.button(
                    "✅ RESERVAR MIS BOLETOS",
                    use_container_width=True
                )

            if reservar:

                if not comprobante:

                    st.error(
                        "Debes subir el comprobante."
                    )

                else:

                    conn = conectar()
                    c = conn.cursor()

                    c.execute(
                        """
                        SELECT id, numero
                        FROM boletos
                        WHERE rifa_id = ?
                        AND estado = 'disponible'
                        """,
                        (
                            st.session_state[
                                "rifa_seleccionada"
                            ],
                        )
                    )

                    disponibles = c.fetchall()

                    if len(disponibles) < cantidad:

                        st.error(
                            "No hay suficientes "
                            "boletos disponibles."
                        )

                        conn.close()

                    else:

                        asignados = random.sample(
                            disponibles,
                            cantidad
                        )

                        carpeta = archivo(
                            "comprobantes"
                        )

                        os.makedirs(
                            carpeta,
                            exist_ok=True
                        )

                        extension = os.path.splitext(
                            comprobante.name
                        )[1].lower()

                        if extension not in [
                            ".png",
                            ".jpg",
                            ".jpeg"
                        ]:
                            extension = ".png"

                        nombre_archivo = (
                            f"{st.session_state['telefono_cliente']}_"
                            f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
                            f"{extension}"
                        )

                        ruta_comprobante = os.path.join(
                            carpeta,
                            nombre_archivo
                        )

                        imagen = Image.open(
                            comprobante
                        )

                        if imagen.mode in (
                            "RGBA",
                            "LA",
                            "P"
                        ):
                            imagen = imagen.convert(
                                "RGB"
                            )

                        imagen.save(
                            ruta_comprobante
                        )

                        ahora = datetime.datetime.now()

                        numeros = []

                        for (
                            boleto_id,
                            numero
                        ) in asignados:

                            numeros.append(
                                numero
                            )

                            c.execute(
                                """
                                UPDATE boletos
                                SET
                                    estado = 'reservado',
                                    usuario_nombre = ?,
                                    usuario_telefono = ?,
                                    metodo_pago = ?,
                                    comprobante = ?,
                                    fecha_reserva = ?
                                WHERE id = ?
                                """,
                                (
                                    st.session_state[
                                        "nombre_cliente"
                                    ],
                                    st.session_state[
                                        "telefono_cliente"
                                    ],
                                    banco,
                                    ruta_comprobante,
                                    ahora,
                                    boleto_id
                                )
                            )

                        conn.commit()
                        conn.close()

                        st.session_state[
                            "boletos_confirmados"
                        ] = numeros

                        st.session_state[
                            "mostrar_confirmacion"
                        ] = True

                        st.rerun()


# ============================================================
# VERIFICADOR
# ============================================================

elif seccion == "🔎 Verificador de boletos":

    st.header(
        "🔎 Verificador de Boletos"
    )

    telefono = st.text_input(
        "📱 Número de WhatsApp registrado"
    )

    if st.button(
        "🔎 BUSCAR MIS BOLETOS",
        use_container_width=True
    ):

        if not telefono.strip():

            st.warning(
                "Escribe tu número de teléfono."
            )

        else:

            conn = conectar()
            c = conn.cursor()

            c.execute(
                """
                SELECT
                    b.numero,
                    b.estado,
                    r.nombre
                FROM boletos b
                JOIN rifas r
                    ON b.rifa_id = r.id
                WHERE b.usuario_telefono = ?
                ORDER BY b.numero
                """,
                (telefono.strip(),)
            )

            resultados = c.fetchall()
            conn.close()

            if resultados:

                st.success(
                    f"Se encontraron "
                    f"{len(resultados)} boletos."
                )

                for numero, estado, rifa in resultados:

                    a, b, c = st.columns(3)

                    a.write(
                        f"🎟️ **{numero}**"
                    )

                    b.write(
                        f"🏆 {rifa}"
                    )

                    if estado == "reservado":

                        c.warning(
                            "⏳ PENDIENTE"
                        )

                    elif estado == "confirmado":

                        c.success(
                            "✅ CONFIRMADO"
                        )

                    else:

                        c.write(
                            estado.upper()
                        )

            else:

                st.info(
                    "No se encontraron boletos."
                )


# ============================================================
# CÓMO JUGAR
# ============================================================

elif seccion == "❓ Cómo jugar":

    st.header(
        "❓ Cómo Participar"
    )

    st.markdown("""
    ### 🎟️ Pasos para participar

    **1.** Selecciona una rifa.

    **2.** Elige la cantidad de boletos.

    **3.** Completa tu nombre y teléfono.

    **4.** Selecciona Banreservas o Banco Popular.

    **5.** Copia el número de cuenta.

    **6.** Realiza la transferencia.

    **7.** Sube el comprobante.

    **8.** Guarda tus números.

    **9.** Verifica posteriormente el estado de tus boletos.
    """)


# ============================================================
# SOPORTE
# ============================================================

elif seccion == "🤖 Soporte IA":

    soporte_ia()


# ============================================================
# GANADORES
# ============================================================

elif seccion == "🏆 Ganadores":

    st.header(
        "🏆 Ganadores Anteriores"
    )

    st.info(
        "Próximamente publicaremos aquí "
        "los ganadores oficiales."
    )


# ============================================================
# ADMINISTRACIÓN
# ============================================================

elif seccion == "⚙️ Administración":

    st.header(
        "⚙️ Administración"
    )

    password = st.text_input(
        "Contraseña",
        type="password"
    )

    if password == "admin123":

        conn = conectar()
        c = conn.cursor()

        c.execute(
            """
            SELECT
                b.id,
                b.numero,
                b.usuario_nombre,
                b.usuario_telefono,
                b.metodo_pago,
                b.comprobante,
                b.fecha_reserva,
                r.nombre
            FROM boletos b
            JOIN rifas r
                ON b.rifa_id = r.id
            WHERE b.estado = 'reservado'
            ORDER BY b.fecha_reserva
            """
        )

        pendientes = c.fetchall()

        if not pendientes:

            st.info(
                "No hay pagos pendientes."
            )

        else:

            for (
                boleto_id,
                numero,
                nombre,
                telefono,
                banco,
                comprobante,
                fecha,
                rifa
            ) in pendientes:

                st.markdown(
                    f"### 🎟️ Boleto {numero}"
                )

                st.write(
                    f"🏆 Rifa: {rifa}"
                )

                st.write(
                    f"👤 {nombre}"
                )

                st.write(
                    f"📱 {telefono}"
                )

                st.write(
                    f"🏦 {banco}"
                )

                if (
                    comprobante
                    and os.path.exists(comprobante)
                ):

                    st.image(
                        comprobante,
                        width=350
                    )

                c1, c2 = st.columns(2)

                with c1:

                    if st.button(
                        f"✅ ACEPTAR {numero}",
                        key=f"aceptar_{boleto_id}",
                        use_container_width=True
                    ):

                        c.execute(
                            """
                            UPDATE boletos
                            SET estado = 'confirmado'
                            WHERE id = ?
                            """,
                            (boleto_id,)
                        )

                        conn.commit()
                        conn.close()

                        st.rerun()

                with c2:

                    if st.button(
                        f"❌ RECHAZAR {numero}",
                        key=f"rechazar_{boleto_id}",
                        use_container_width=True
                    ):

                        c.execute(
                            """
                            UPDATE boletos
                            SET
                                estado = 'disponible',
                                usuario_nombre = NULL,
                                usuario_telefono = NULL,
                                metodo_pago = NULL,
                                comprobante = NULL,
                                fecha_reserva = NULL
                            WHERE id = ?
                            """,
                            (boleto_id,)
                        )

                        conn.commit()
                        conn.close()

                        st.rerun()

                st.markdown("---")

        if conn:
            try:
                conn.close()
            except:
                pass

    elif password:

        st.error(
            "Contraseña incorrecta."
        )
