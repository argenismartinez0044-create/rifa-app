# Código completo — Rifas Sirio RD

```python
import datetime
import os
import random
import sqlite3

from PIL import Image
import streamlit as st


# =========================================================
# CONFIGURACIÓN
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "rifas_v4.db")

WHATSAPP_NUMERO = "8294835217"

st.set_page_config(
    page_title="Rifas Sirio RD",
    page_icon="🎲",
    layout="wide",
)


# =========================================================
# FUNCIONES GENERALES
# =========================================================

def ruta_archivo(nombre):
    """Devuelve la ruta absoluta de un archivo dentro de la carpeta del programa."""
    return os.path.join(BASE_DIR, nombre)


def conectar_db():
    return sqlite3.connect(DB_FILE)


# =========================================================
# INICIALIZACIÓN DE BASE DE DATOS
# =========================================================

def init_db():

    conn = conectar_db()
    c = conn.cursor()

    # -----------------------------------------------------
    # Tabla de rifas
    # -----------------------------------------------------

    c.execute(
        """
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
        """
    )

    # -----------------------------------------------------
    # Tabla de boletos
    # -----------------------------------------------------

    c.execute(
        """
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
        """
    )

    # -----------------------------------------------------
    # Crear rifas solamente si no existen
    # -----------------------------------------------------

    c.execute("SELECT COUNT(*) FROM rifas")
    cantidad_rifas = c.fetchone()[0]

    if cantidad_rifas == 0:

        c.execute(
            """
            INSERT INTO rifas
            (
                nombre,
                categoria,
                precio_boleto,
                min_boletos,
                total_boletos,
                imagen,
                fecha
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "PlayStation 5 Pro",
                "Juego",
                5.0,
                15,
                100000,
                "play.jpg",
                "Fecha pendiente",
            ),
        )

        c.execute(
            """
            INSERT INTO rifas
            (
                nombre,
                categoria,
                precio_boleto,
                min_boletos,
                total_boletos,
                imagen,
                fecha
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "5 iPhone 17 Pro Max",
                "TELÉFONO",
                15.0,
                10,
                100000,
                "iphone.jpg",
                "Al vender el 80%",
            ),
        )

        conn.commit()

        # Obtener los IDs reales
        c.execute("SELECT id FROM rifas ORDER BY id")
        ids_rifas = [fila[0] for fila in c.fetchall()]

        # Crear boletos
        for rifa_id in ids_rifas:

            numeros = [
                (rifa_id, f"{numero:05d}")
                for numero in range(1, 100001)
            ]

            c.executemany(
                """
                INSERT INTO boletos
                (
                    rifa_id,
                    numero
                )
                VALUES (?, ?)
                """,
                numeros,
            )

        conn.commit()

    # -----------------------------------------------------
    # Asegurar valores correctos
    # -----------------------------------------------------

    c.execute(
        "UPDATE rifas SET min_boletos = 15 WHERE nombre = 'PlayStation 5 Pro'"
    )

    c.execute(
        "UPDATE rifas SET min_boletos = 10 WHERE nombre = '5 iPhone 17 Pro Max'"
    )

    c.execute(
        """
        UPDATE rifas
        SET nombre = '5 iPhone 17 Pro Max'
        WHERE id = 2
        """
    )

    conn.commit()
    conn.close()


# =========================================================
# LIBERAR BOLETOS EXPIRADOS
# =========================================================

def liberar_expirados():

    conn = conectar_db()
    c = conn.cursor()

    # Mantiene la lógica original de 15 minutos.
    hace_15_minutos = (
        datetime.datetime.now()
        - datetime.timedelta(minutes=15)
    )

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
        WHERE
            estado = 'reservado'
            AND fecha_reserva < ?
        """,
        (hace_15_minutos,),
    )

    conn.commit()
    conn.close()


init_db()
liberar_expirados()


# =========================================================
# ESTILOS
# =========================================================

st.markdown(
    """
    <style>

    .stApp {
        background:
        linear-gradient(
            135deg,
            #0b0d17 0%,
            #171b2e 50%,
            #080910 100%
        ) !important;

        color: #FFFFFF;
    }

    .combo-card {
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 15px;
        padding: 12px;
        margin-bottom: 8px;
        text-align: center;
    }

    .combo-selected {
        background: linear-gradient(
            135deg,
            #f5c518,
            #d9a900
        );
        color: #000000;
        border-radius: 15px;
        padding: 12px;
        margin-bottom: 8px;
        text-align: center;
        font-weight: 800;
    }

    .paso-card {
        background:
        linear-gradient(
            135deg,
            #0f2027 0%,
            #203a43 50%,
            #2c5364 100%
        );

        border-radius: 16px;
        padding: 20px;
        text-align: center;
        margin-bottom: 20px;
    }

    .banco-card {
        background: rgba(255,255,255,0.06);
        border-radius: 16px;
        padding: 20px;
        border: 1px solid rgba(255,255,255,0.10);
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# FUNCIÓN PARA LIMPIAR COMPLETAMENTE UNA COMPRA
# =========================================================

def limpiar_compra():

    claves = [
        "rifa_seleccionada",
        "nombre_rifa",
        "precio_rifa",
        "min_rifa",
        "paso_compra",
        "banco_pago",
        "nombre_cliente",
        "telefono_cliente",
        "cant_boletos",
        "nivel_boletos",
        "compra_completada",
        "boletos_confirmados_ventana",
        "mostrar_confirmacion_boletos",
    ]

    for clave in claves:
        st.session_state.pop(clave, None)

    # Limpiar cantidades manuales de rifas anteriores
    for clave in list(st.session_state.keys()):
        if clave.startswith("cant_manual_"):
            st.session_state.pop(clave, None)


# =========================================================
# SELECCIONAR RIFA
# =========================================================

def seleccionar_rifa(rifa_id, nombre, precio, minimo):

    # -----------------------------------------------------
    # IMPORTANTE:
    # Cada nueva rifa comienza SIEMPRE desde el paso 1.
    # No conserva banco ni selección anterior.
    # -----------------------------------------------------

    st.session_state["rifa_seleccionada"] = rifa_id
    st.session_state["nombre_rifa"] = nombre
    st.session_state["precio_rifa"] = precio
    st.session_state["min_rifa"] = minimo

    st.session_state["paso_compra"] = 1

    st.session_state.pop("banco_pago", None)
    st.session_state.pop("cant_boletos", None)
    st.session_state.pop("nivel_boletos", None)
    st.session_state.pop("comprobante_file", None)


# =========================================================
# SELECCIONAR CANTIDAD
# =========================================================

def seleccionar_cantidad(cantidad, nombre_nivel):

    st.session_state["cant_boletos"] = int(cantidad)
    st.session_state["nivel_boletos"] = nombre_nivel


# =========================================================
# DIÁLOGO DE SOPORTE IA
# =========================================================

@st.dialog("🤖 Asistente Virtual - Rifas Sirio RD")
def abrir_soporte_ia():

    st.caption("Respuestas instantáneas las 24 horas.")

    if "mensajes_chat" not in st.session_state:

        st.session_state["mensajes_chat"] = [
            {
                "role": "assistant",
                "content":
                """
¡Hola! Soy tu asistente de **Rifas Sirio RD** 🎲.

¿En qué te puedo ayudar hoy?

Puedes preguntarme sobre cómo jugar, bancos, boletos o sorteos.
""",
            }
        ]

    c1, c2, c3, c4 = st.columns(4)

    opcion_rapida = None

    if c1.button("🎲 ¿Cómo jugar?", key="dlg_c1"):
        opcion_rapida = "¿Cómo participar?"

    if c2.button("💳 Bancos", key="dlg_c2"):
        opcion_rapida = "cuentas de banco"

    if c3.button("🔎 Mis boletos", key="dlg_c3"):
        opcion_rapida = "verificar mis boletos"

    if c4.button("📅 Sorteos", key="dlg_c4"):
        opcion_rapida = "fecha del sorteo"

    for msg in st.session_state["mensajes_chat"]:

        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Escribe tu duda...")

    prompt = user_input or opcion_rapida

    if prompt:

        if user_input:

            st.session_state["mensajes_chat"].append(
                {
                    "role": "user",
                    "content": prompt
                }
            )

        txt = prompt.lower()

        mostrar_wa = False

        if any(
            palabra in txt
            for palabra in [
                "jugar",
                "participar",
                "funciona",
                "pasos",
                "comprar",
                "instrucciones",
            ]
        ):

            resp = (
                "**Pasos para participar:**\n\n"
                "1. Selecciona una rifa.\n"
                "2. Completa tu nombre, teléfono y cantidad de boletos.\n"
                "3. Selecciona el banco.\n"
                "4. Realiza el pago.\n"
                "5. Sube el comprobante.\n"
                "6. Guarda tus números."
            )

        elif any(
            palabra in txt
            for palabra in [
                "pago",
                "banco",
                "transferencia",
                "banreservas",
                "popular",
                "cuenta",
            ]
        ):

            resp = (
                "**Métodos de pago:**\n\n"
                "Los bancos aparecen solamente después de "
                "seleccionar una rifa y completar tus datos.\n\n"
                "Podrás seleccionar **Banreservas** o "
                "**Banco Popular**."
            )

        elif any(
            palabra in txt
            for palabra in [
                "verificar",
                "consultar",
                "mi boleto",
                "numeros",
                "números",
            ]
        ):

            resp = (
                "Ingresa a la sección "
                "**🔎 Verificador de boletos** e introduce "
                "el número telefónico utilizado durante la compra."
            )

        elif any(
            palabra in txt
            for palabra in [
                "ganador",
                "sorteo",
                "fecha",
                "cuando",
                "cuándo",
            ]
        ):

            resp = (
                "La fecha del sorteo aparece en la ficha "
                "correspondiente de cada rifa."
            )

        elif any(
            palabra in txt
            for palabra in [
                "precio",
                "costo",
                "minimo",
                "mínimo",
            ]
        ):

            resp = (
                "• **PlayStation 5 Pro:** RD$ 5.00 por boleto "
                "(mínimo 15 boletos).\n\n"
                "• **5 iPhone 17 Pro Max:** RD$ 15.00 por boleto "
                "(mínimo 10 boletos)."
            )

        else:

            resp = (
                "¿Necesitas ayuda personalizada? "
                "Puedes hablar con un asesor por WhatsApp."
            )

            mostrar_wa = True

        st.session_state["mensajes_chat"].append(
            {
                "role": "assistant",
                "content": resp
            }
        )

        if mostrar_wa:

            st.markdown(
                f"""
                [💬 Hablar con soporte en WhatsApp]
                (https://wa.me/{WHATSAPP_NUMERO})
                """
            )

        st.rerun()


# =========================================================
# VENTANA DE CONFIRMACIÓN
# =========================================================

@st.dialog("🎟️ ¡Tus boletos fueron registrados!")
def mostrar_ventana_boletos():

    numeros = st.session_state.get(
        "boletos_confirmados_ventana",
        []
    )

    numeros_texto = ", ".join(numeros)

    st.success(
        "🎉 ¡Pago y comprobante recibidos correctamente!"
    )

    st.markdown("### Tus números de boletos")

    st.code(
        numeros_texto,
        language="text"
    )

    st.markdown(
        f"""
        <button
            onclick="navigator.clipboard.writeText({numeros_texto!r})"
            style="
                width:100%;
                padding:12px;
                border-radius:10px;
                border:0;
                font-weight:700;
                cursor:pointer;
            "
        >
            📋 COPIAR BOLETOS
        </button>
        """,
        unsafe_allow_html=True,
    )

    st.warning(
        "⏳ Tus boletos quedan reservados temporalmente "
        "mientras se valida el comprobante."
    )

    st.caption(
        "Guarda tus números. Puedes consultar su estado "
        "posteriormente en el Verificador de Boletos."
    )

    st.info(
        "Al cerrar esta ventana volverás al catálogo."
    )

    if st.button(
        "✅ ENTIENDO",
        use_container_width=True
    ):

        limpiar_compra()

        st.session_state.pop(
            "comprobante_file",
            None
        )

        st.rerun()


if st.session_state.get(
    "mostrar_confirmacion_boletos"
):

    mostrar_ventana_boletos()


# =========================================================
# SIDEBAR
# =========================================================

seccion = st.sidebar.radio(
    "Navegación",
    [
        "🏠 Inicio & Catálogo",
        "🔎 Verificador de boletos",
        "❓ Cómo jugar",
        "🤖 Soporte IA",
        "🏆 Ganadores",
        "⚙️ Administración",
    ],
)

st.sidebar.markdown("---")

if st.sidebar.button(
    "🤖 Abrir Chat de Soporte IA",
    use_container_width=True
):

    abrir_soporte_ia()


# =========================================================
# INICIO Y CATÁLOGO
# =========================================================

if seccion == "🏠 Inicio & Catálogo":

    # -----------------------------------------------------
    # ENCABEZADO
    # -----------------------------------------------------

    col_logo, col_titulo = st.columns([1, 2])

    with col_logo:

        logo = ruta_archivo("logo.png")

        if os.path.exists(logo):
            st.image(
                logo,
                width=220
            )

    with col_titulo:

        st.markdown(
            """
            <p style="
                color:#F5C518;
                font-weight:bold;
                margin-bottom:0;
            ">
                Plataforma Exclusiva de Rifas
            </p>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <h1 style="
                color:#FFFFFF;
                font-size:2.2rem;
                margin-top:0;
            ">
                Premios Exclusivos
            </h1>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # -----------------------------------------------------
    # COMO PARTICIPAR
    # -----------------------------------------------------

    with st.expander(
        "📺 ¿CÓMO PARTICIPAR? — 5 pasos simples"
    ):

        st.write(
            """
            1. Selecciona un premio del catálogo.
            2. Registra tu nombre, teléfono y cantidad de boletos.
            3. Selecciona Banreservas o Banco Popular.
            4. Realiza el pago y sube el comprobante.
            5. Consulta tus números en el Verificador de Boletos.
            """
        )

    st.markdown("---")

    st.subheader("🛍️ CATÁLOGO DE RIFAS")

    # -----------------------------------------------------
    # FILTRO
    # -----------------------------------------------------

    cat_filtro = st.radio(
        "Categoría:",
        [
            "TODOS",
            "Juego",
            "TELÉFONO",
            "DINERO",
            "VEHÍCULOS",
        ],
        horizontal=True,
    )

    conn = conectar_db()
    c = conn.cursor()

    if cat_filtro == "TODOS":

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
            (cat_filtro,),
        )

    rifas = c.fetchall()

    conn.close()

    # -----------------------------------------------------
    # CATÁLOGO
    # -----------------------------------------------------

    cols = st.columns(2)

    for idx, rifa in enumerate(rifas):

        (
            rifa_id,
            rifa_nombre,
            rifa_categoria,
            rifa_precio,
            rifa_minimo,
            rifa_total,
            rifa_imagen,
            rifa_fecha,
        ) = rifa

        conn = conectar_db()
        c = conn.cursor()

        c.execute(
            """
            SELECT COUNT(*)
            FROM boletos
            WHERE
                rifa_id = ?
                AND estado IN ('reservado', 'confirmado')
            """,
            (rifa_id,),
        )

        vendidos = c.fetchone()[0]

        conn.close()

        progreso = (
            int((vendidos / rifa_total) * 100)
            if rifa_total > 0
            else 0
        )

        with cols[idx % 2]:

            st.markdown(
                f"### 🏷️ {rifa_nombre}"
            )

            st.caption(
                f"Categoría: **{rifa_categoria}**"
            )

            imagen_rifa = ruta_archivo(
                rifa_imagen
            )

            if os.path.exists(imagen_rifa):

                st.image(
                    imagen_rifa,
                    use_container_width=True
                )

            st.write(
                f"📅 **Fecha:** {rifa_fecha}"
            )

            st.write(
                f"📊 **PROGRESO: {progreso}%**"
            )

            st.progress(
                progreso / 100
            )

            st.markdown(
                f"### **RD$ {rifa_precio:.2f}**"
            )

            st.caption(
                f"Mínimo {rifa_minimo} boletos"
            )

            if "PlayStation" in rifa_nombre:

                texto_boton = (
                    f"🎮 JUGAR POR "
                    f"{rifa_nombre.upper()}"
                )

            else:

                texto_boton = (
                    f"📱 PARTICIPAR POR "
                    f"{rifa_nombre.upper()}"
                )

            st.button(
                texto_boton,
                key=f"jugar_{rifa_id}",
                on_click=seleccionar_rifa,
                args=(
                    rifa_id,
                    rifa_nombre,
                    rifa_precio,
                    rifa_minimo,
                ),
                use_container_width=True,
            )


    # =====================================================
    # FLUJO DE COMPRA
    # =====================================================

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

        # -------------------------------------------------
        # ENCABEZADO DE RIFA SELECCIONADA
        # -------------------------------------------------

        st.markdown(
            f"""
            <div class="paso-card">

                <span style="
                    background-color:#F5C518;
                    color:#000;
                    font-weight:800;
                    padding:5px 14px;
                    border-radius:20px;
                ">
                    RIFA SELECCIONADA
                </span>

                <h2 style="
                    color:#FFFFFF;
                    margin:12px 0;
                ">
                    🎉 {nombre} 🎉
                </h2>

                <p style="
                    color:#E0E0E0;
                    margin:0;
                ">
                    Precio por boleto:
                    <strong style="color:#F5C518;">
                        RD$ {precio:.2f}
                    </strong>
                </p>

            </div>
            """,
            unsafe_allow_html=True,
        )


        # =================================================
        # PASO 1
        # =================================================

        if paso == 1:

            st.subheader(
                "📝 1. Completa tus datos"
            )

            st.markdown(
                "### 🎟️ Elige tu cantidad de boletos"
            )

            st.caption(
                f"Cantidad mínima: {minimo} boletos. "
                "Puedes seleccionar un combo o escribir "
                "una cantidad manual."
            )

            # -------------------------------------------------
            # COMBOS
            # -------------------------------------------------

            cantidades = [
                (
                    "🟢 NORMAL",
                    minimo,
                ),
                (
                    "🔵 DOBLE",
                    minimo * 2,
                ),
                (
                    "🟣 INTERMEDIO",
                    minimo * 3,
                ),
                (
                    "🟠 PROFESIONAL",
                    minimo * 5,
                ),
                (
                    "🔴 PRO",
                    minimo * 10,
                ),
            ]

            # Máximo permitido
            cantidades = [
                (
                    nombre_combo,
                    min(100, cantidad)
                )
                for nombre_combo, cantidad
                in cantidades
            ]

            # -------------------------------------------------
            # INICIALIZAR CANTIDAD
            # -------------------------------------------------

            if "cant_boletos" not in st.session_state:

                st.session_state[
                    "cant_boletos"
                ] = minimo

                st.session_state[
                    "nivel_boletos"
                ] = "🟢 NORMAL"


            cantidad_actual = int(
                st.session_state[
                    "cant_boletos"
                ]
            )

            nivel_actual = st.session_state.get(
                "nivel_boletos",
                "🟢 NORMAL"
            )

            # -------------------------------------------------
            # BOTONES DE COMBOS
            # -------------------------------------------------

            combo_cols = st.columns(5)

            for i, (
                nombre_combo,
                cantidad_combo
            ) in enumerate(cantidades):

                seleccionado = (
                    cantidad_actual == cantidad_combo
                    and nivel_actual == nombre_combo
                )

                texto_combo = (
                    f"✅ {nombre_combo}\n"
                    f"{cantidad_combo} BOLETOS"
                    if seleccionado
                    else
                    f"{nombre_combo}\n"
                    f"{cantidad_combo} BOLETOS"
                )

                with combo_cols[i]:

                    st.button(
                        texto_combo,
                        key=(
                            f"combo_"
                            f"{st.session_state['rifa_seleccionada']}_"
                            f"{i}"
                        ),
                        on_click=seleccionar_cantidad,
                        args=(
                            cantidad_combo,
                            nombre_combo,
                        ),
                        use_container_width=True,
                    )

            # -------------------------------------------------
            # INDICADOR DE SELECCIÓN
            # -------------------------------------------------

            st.markdown(
                f"""
                <div style="
                    background:rgba(245,197,24,0.12);
                    border:1px solid rgba(245,197,24,0.45);
                    border-radius:12px;
                    padding:12px;
                    margin:15px 0;
                    text-align:center;
                ">
                    🎟️ Cantidad seleccionada:
                    <strong>
                        {cantidad_actual} boletos
                    </strong>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # -------------------------------------------------
            # FORMULARIO
            # -------------------------------------------------

            with st.form(
                "form_datos_cliente",
                clear_on_submit=False
            ):

                nombre_cliente = st.text_input(
                    "👤 Nombre Completo",
                    value=st.session_state.get(
                        "nombre_cliente",
                        ""
                    ),
                )

                telefono_cliente = st.text_input(
                    "📱 Teléfono / WhatsApp",
                    value=st.session_state.get(
                        "telefono_cliente",
                        ""
                    ),
                    placeholder="Ej: 8091234567",
                )

                # -------------------------------------------------
                # CANTIDAD MANUAL
                # -------------------------------------------------

                cantidad_manual = st.number_input(
                    "✏️ O escribe la cantidad manualmente",
                    min_value=minimo,
                    max_value=100,
                    value=cantidad_actual,
                    step=1,
                )

                total_pagar = (
                    int(cantidad_manual)
                    * precio
                )

                st.markdown(
                    f"""
                    ### 💰 Total a pagar

                    **{int(cantidad_manual)} boletos**
                    × RD$ {precio:.2f}
                    = **RD$ {total_pagar:.2f}**
                    """
                )

                continuar_datos = st.form_submit_button(
                    "➡️ CONTINUAR AL PAGO",
                    use_container_width=True,
                )

            # -------------------------------------------------
            # CONTINUAR
            # -------------------------------------------------

            if continuar_datos:

                if not nombre_cliente.strip():

                    st.error(
                        "Por favor escribe tu nombre completo."
                    )

                elif not telefono_cliente.strip():

                    st.error(
                        "Por favor escribe tu teléfono/WhatsApp."
                    )

                else:

                    st.session_state[
                        "nombre_cliente"
                    ] = nombre_cliente.strip()

                    st.session_state[
                        "telefono_cliente"
                    ] = telefono_cliente.strip()

                    st.session_state[
                        "cant_boletos"
                    ] = int(cantidad_manual)

                    # Si cambió manualmente, indicarlo.
                    if int(cantidad_manual) != cantidad_actual:

                        st.session_state[
                            "nivel_boletos"
                        ] = "✏️ MANUAL"

                    st.session_state[
                        "paso_compra"
                    ] = 2

                    # Muy importante:
                    # no mostrar ningún banco antes de llegar
                    # al paso 2.
                    st.session_state.pop(
                        "banco_pago",
                        None
                    )

                    st.rerun()


        # =================================================
        # PASO 2 — BANCOS
        # =================================================

        elif paso == 2:

            st.subheader(
                "💳 2. Selecciona el banco"
            )

            st.caption(
                "Los datos de las cuentas solamente "
                "aparecerán después de seleccionar un banco."
            )

            # -------------------------------------------------
            # BANCOS
            # -------------------------------------------------

            bancos = {

                "Banreservas": {
                    "logo": "barreserva.png",
                    "titular": "ARGENIS MARTINEZ C.",
                    "cuenta": "9606561652",
                },

                "Banco Popular": {
                    "logo": "popular.png",
                    "titular": "ARGENIS MARTINEZ",
                    "cuenta": "821794971",
                },

            }

            banco_actual = st.session_state.get(
                "banco_pago"
            )

            # -------------------------------------------------
            # LOGOS
            # -------------------------------------------------

            banco_cols = st.columns(2)

            for i, (
                nombre_banco,
                datos_banco
            ) in enumerate(bancos.items()):

                with banco_cols[i]:

                    logo_path = ruta_archivo(
                        datos_banco["logo"]
                    )

                    # -------------------------------------------------
                    # MOSTRAR LOGO
                    # -------------------------------------------------

                    if os.path.exists(logo_path):

                        st.image(
                            logo_path,
                            use_container_width=True
                        )

                    else:

                        st.error(
                            f"No se encontró: "
                            f"{datos_banco['logo']}"
                        )

                    # -------------------------------------------------
                    # BOTÓN
                    # -------------------------------------------------

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
                        key=f"banco_btn_{i}",
                        on_click=seleccionar_banco,
                        args=(nombre_banco,),
                        use_container_width=True,
                    )


            # -------------------------------------------------
            # SI NO HAY BANCO
            # -------------------------------------------------

            if not banco_actual:

                st.info(
                    "👆 Selecciona uno de los dos bancos "
                    "para mostrar los datos de transferencia."
                )

                if st.button(
                    "⬅️ VOLVER A MIS DATOS",
                    key="volver_datos_sin_banco",
                    use_container_width=True,
                ):

                    st.session_state[
                        "paso_compra"
                    ] = 1

                    st.rerun()


            # -------------------------------------------------
            # SI YA SELECCIONÓ BANCO
            # -------------------------------------------------

            else:

                datos_banco = bancos[
                    banco_actual
                ]

                logo_path = ruta_archivo(
                    datos_banco["logo"]
                )

                # -------------------------------------------------
                # LOGO GRANDE
                # -------------------------------------------------

                if os.path.exists(logo_path):

                    st.image(
                        logo_path,
                        width=220
                    )

                # -------------------------------------------------
                # INFORMACIÓN DE LA CUENTA
                # -------------------------------------------------

                st.markdown(
                    f"""
                    <div class="banco-card">

                        <h3>
                            🏦 {banco_actual}
                        </h3>

                        <p>
                            Tipo de cuenta:
                            <strong>
                                Ahorros
                            </strong>
                        </p>

                        <p>
                            Titular:
                            <strong>
                                {datos_banco["titular"]}
                            </strong>
                        </p>

                        <p>
                            Número de cuenta:
                        </p>

                        <div style="
                            font-size:1.6rem;
                            font-weight:800;
                            letter-spacing:2px;
                        ">
                            {datos_banco["cuenta"]}
                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # -------------------------------------------------
                # COPIAR CUENTA
                # -------------------------------------------------

                cuenta = datos_banco[
                    "cuenta"
                ]

                st.markdown(
                    f"""
                    <button
                        onclick="
                        navigator.clipboard
                        .writeText('{cuenta}')
                        .then(
                            () => this.innerText =
                            '✅ CUENTA COPIADA'
                        )
                        "
                        style="
                            width:100%;
                            padding:12px;
                            margin-top:10px;
                            border:0;
                            border-radius:8px;
                            background:#F5C518;
                            color:#000;
                            font-weight:800;
                            cursor:pointer;
                        "
                    >
                        📋 COPIAR NÚMERO DE CUENTA
                    </button>
                    """,
                    unsafe_allow_html=True,
                )

                total_pagar = (
                    st.session_state[
                        "cant_boletos"
                    ]
                    * precio
                )

                st.markdown(
                    f"""
                    ### 💰 Total a pagar:
                    **RD$ {total_pagar:.2f}**
                    """
                )

                st.info(
                    "Realiza el depósito y luego "
                    "continúa para subir el comprobante."
                )

                col1, col2 = st.columns(2)

                with col1:

                    if st.button(
                        "⬅️ VOLVER A MIS DATOS",
                        key="volver_datos",
                        use_container_width=True,
                    ):

                        st.session_state[
                            "paso_compra"
                        ] = 1

                        st.rerun()

                with col2:

                    if st.button(
                        "➡️ CONTINUAR Y SUBIR COMPROBANTE",
                        key="continuar_comprobante",
                        use_container_width=True,
                    ):

                        st.session_state[
                            "paso_compra"
                        ] = 3

                        st.rerun()


        # =================================================
        # PASO 3 — COMPROBANTE
        # =================================================

        elif paso == 3:

            st.subheader(
                "📤 3. Sube el comprobante"
            )

            banco_seleccionado = st.session_state.get(
                "banco_pago",
                ""
            )

            cantidad = int(
                st.session_state[
                    "cant_boletos"
                ]
            )

            total = cantidad * precio

            st.info(
                f"""
                Banco seleccionado:
                **{banco_seleccionado}**

                Total a pagar:
                **RD$ {total:.2f}**
                """
            )

            comprobante_file = st.file_uploader(
                "📸 Selecciona la imagen del volante/comprobante",
                type=[
                    "png",
                    "jpg",
                    "jpeg",
                ],
                key="comprobante_file",
            )

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    "⬅️ VOLVER AL BANCO",
                    key="volver_banco",
                    use_container_width=True,
                ):

                    st.session_state[
                        "paso_compra"
                    ] = 2

                    st.rerun()

            with col2:

                reservar = st.button(
                    "✅ RESERVAR MIS BOLETOS",
                    key="reservar_final",
                    use_container_width=True,
                )

            # -------------------------------------------------
            # RESERVAR
            # -------------------------------------------------

            if reservar:

                if not comprobante_file:

                    st.error(
                        "Debes subir la imagen del "
                        "volante/comprobante."
                    )

                else:

                    conn = conectar_db()
                    c = conn.cursor()

                    c.execute(
                        """
                        SELECT id, numero
                        FROM boletos
                        WHERE
                            rifa_id = ?
                            AND estado = 'disponible'
                        """,
                        (
                            st.session_state[
                                "rifa_seleccionada"
                            ],
                        ),
                    )

                    disponibles = c.fetchall()

                    if len(disponibles) < cantidad:

                        st.error(
                            "No hay suficientes boletos disponibles."
                        )

                        conn.close()

                    else:

                        # -------------------------------------------------
                        # SELECCIONAR NÚMEROS ALEATORIOS
                        # -------------------------------------------------

                        asignados = random.sample(
                            disponibles,
                            cantidad
                        )

                        # -------------------------------------------------
                        # CARPETA DE COMPROBANTES
                        # -------------------------------------------------

                        carpeta_comprobantes = ruta_archivo(
                            "comprobantes"
                        )

                        os.makedirs(
                            carpeta_comprobantes,
                            exist_ok=True
                        )

                        extension = os.path.splitext(
                            comprobante_file.name
                        )[1].lower()

                        if extension not in [
                            ".png",
                            ".jpg",
                            ".jpeg",
                        ]:

                            extension = ".png"

                        telefono = st.session_state[
                            "telefono_cliente"
                        ]

                        timestamp = (
                            datetime.datetime.now()
                            .strftime("%Y%m%d_%H%M%S_%f")
                        )

                        nombre_archivo = (
                            f"{telefono}_"
                            f"{timestamp}"
                            f"{extension}"
                        )

                        path_comp = os.path.join(
                            carpeta_comprobantes,
                            nombre_archivo
                        )

                        # -------------------------------------------------
                        # GUARDAR IMAGEN
                        # -------------------------------------------------

                        imagen_comprobante = Image.open(
                            comprobante_file
                        )

                        if imagen_comprobante.mode in [
                            "RGBA",
                            "LA",
                            "P",
                        ]:

                            imagen_comprobante = (
                                imagen_comprobante
                                .convert("RGB")
                            )

                        imagen_comprobante.save(
                            path_comp
                        )

                        ahora = datetime.datetime.now()

                        numeros_asignados = []

                        # -------------------------------------------------
                        # ACTUALIZAR BOLETOS
                        # -------------------------------------------------

                        for (
                            boleto_id,
                            boleto_numero
                        ) in asignados:

                            numeros_asignados.append(
                                boleto_numero
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
                                    telefono,
                                    banco_seleccionado,
                                    path_comp,
                                    ahora,
                                    boleto_id,
                                ),
                            )

                        conn.commit()
                        conn.close()

                        # -------------------------------------------------
                        # GUARDAR PARA VENTANA
                        # -------------------------------------------------

                        st.session_state[
                            "boletos_confirmados_ventana"
                        ] = numeros_asignados

                        st.session_state[
                            "mostrar_confirmacion_boletos"
                        ] = True

                        st.session_state[
                            "compra_completada"
                        ] = True

                        st.rerun()


# =========================================================
# VERIFICADOR
# =========================================================

elif seccion == "🔎 Verificador de boletos":

    st.header(
        "🔎 Verificador de Boletos"
    )

    tel_buscar = st.text_input(
        "Ingresa tu número de WhatsApp registrado:"
    )

    if st.button(
        "🔎 Buscar Mis Boletos",
        use_container_width=True
    ):

        if not tel_buscar.strip():

            st.warning(
                "Escribe tu número de teléfono."
            )

        else:

            conn = conectar_db()
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
                WHERE
                    b.usuario_telefono = ?
                ORDER BY b.numero
                """,
                (
                    tel_buscar.strip(),
                ),
            )

            mis_boletos = c.fetchall()

            conn.close()

            if mis_boletos:

                st.success(
                    f"Se encontraron "
                    f"{len(mis_boletos)} boletos."
                )

                for (
                    numero,
                    estado,
                    rifa_nombre
                ) in mis_boletos:

                    c1, c2, c3 = st.columns(3)

                    c1.write(
                        f"🎟️ **Boleto:** `{numero}`"
                    )

                    c2.write(
                        f"🏆 **Rifa:** {rifa_nombre}"
                    )

                    if estado == "reservado":

                        c3.markdown(
                            "📌 **Estado:** "
                            "⏳ PENDIENTE"
                        )

                    elif estado == "confirmado":

                        c3.markdown(
                            "📌 **Estado:** "
                            "✅ CONFIRMADO Y VÁLIDO"
                        )

                    else:

                        c3.markdown(
                            f"📌 **Estado:** "
                            f"`{estado.upper()}`"
                        )

                    st.markdown("---")

            else:

                st.info(
                    "No se encontraron registros "
                    "con este número."
                )


# =========================================================
# CÓMO JUGAR
# =========================================================

elif seccion == "❓ Cómo jugar":

    st.header(
        "❓ Cómo Participar"
    )

    st.markdown(
        """
        ### Pasos

        **1.** Selecciona tu premio.

        **2.** Completa tu nombre y teléfono.

        **3.** Selecciona la cantidad de boletos.

        **4.** Continúa al pago.

        **5.** Selecciona Banreservas o Banco Popular.

        **6.** Realiza el pago.

        **7.** Sube el comprobante.

        **8.** Guarda tus números.

        **9.** Consulta tus boletos en el verificador.
        """
    )


# =========================================================
# SOPORTE IA
# =========================================================

elif seccion == "🤖 Soporte IA":

    abrir_soporte_ia()


# =========================================================
# GANADORES
# =========================================================

elif seccion == "🏆 Ganadores":

    st.header(
        "🏆 Ganadores Anteriores"
    )

    st.info(
        "Próximamente publicaremos aquí "
        "los ganadores oficiales."
    )


# =========================================================
# ADMINISTRACIÓN
# =========================================================

elif seccion == "⚙️ Administración":

    st.header(
        "⚙️ Administración"
    )

    pass_admin = st.text_input(
        "Contraseña",
        type="password"
    )

    if pass_admin == "admin123":

        conn = conectar_db()
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
            WHERE
                b.estado = 'reservado'
            ORDER BY b.fecha_reserva ASC
            """
        )

        pendientes = c.fetchall()

        if not pendientes:

            st.info(
                "No hay pagos pendientes por confirmar."
            )

        else:

            for boleto in pendientes:

                (
                    boleto_id,
                    numero,
                    nombre,
                    telefono,
                    metodo_pago,
                    comprobante,
                    fecha,
                    rifa_nombre,
                ) = boleto

                st.markdown(
                    f"""
                    #### 🎟️ Boleto `{numero}`

                    **Rifa:** {rifa_nombre}
                    """
                )

                st.write(
                    f"👤 {nombre}  |  "
                    f"📱 {telefono}  |  "
                    f"💳 {metodo_pago}"
                )

                if (
                    comprobante
                    and os.path.exists(comprobante)
                ):

                    st.image(
                        comprobante,
                        width=300
                    )

                c1, c2 = st.columns(2)

                # -------------------------------------------------
                # ACEPTAR
                # -------------------------------------------------

                with c1:

                    if st.button(
                        f"✅ Aceptar {numero}",
                        key=f"aceptar_{boleto_id}",
                        use_container_width=True,
                    ):

                        c.execute(
                            """
                            UPDATE boletos
                            SET estado = 'confirmado'
                            WHERE id = ?
                            """,
                            (boleto_id,),
                        )

                        conn.commit()

                        st.success(
                            f"Boleto {numero} confirmado."
                        )

                        st.rerun()

                # -------------------------------------------------
                # RECHAZAR
                # -------------------------------------------------

                with c2:

                    if st.button(
                        f"❌ Rechazar {numero}",
                        key=f"rechazar_{boleto_id}",
                        use_container_width=True,
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
                            (boleto_id,),
                        )

                        conn.commit()

                        st.warning(
                            f"Boleto {numero} liberado."
                        )

                        st.rerun()

                st.markdown("---")

        conn.close()

    elif pass_admin != "":

        st.error(
            "Contraseña incorrecta."
        )
```

## Cambio importante en los bancos

En este código he puesto exactamente:

```python
"Banreservas": {
    "logo": "barreserva.png",
```

y:

```python
"Banco Popular": {
    "logo": "popular.png",
```

Por lo tanto, el archivo debe llamarse exactamente:

```text
barreserva.png
popular.png
```

Si tu archivo realmente se llama `barreserva.PNG` con mayúsculas, en Windows normalmente no tendrás problema, pero recomiendo dejarlo exactamente como `barreserva.png`.

### El flujo ahora queda así

**Inicio**

→ aparece únicamente el catálogo.

**Presionas "JUGAR"**

→ aparece:

> Rifa seleccionada
> Cantidad de boletos
> 🟢 NORMAL
> 🔵 DOBLE
> 🟣 INTERMEDIO
> 🟠 PROFESIONAL
> 🔴 PRO
> Nombre
> Teléfono
> Cantidad manual
> Total
> **CONTINUAR AL PAGO**

**Todavía aquí NO aparece ningún banco.**

Después de presionar **CONTINUAR AL PAGO**:

→ aparecen los dos logos:

> 🏦 Banreservas
> 🏦 Banco Popular

**Todavía no aparecen los números de cuenta.**

Después de seleccionar uno:

→ aparece su logo + titular + tipo de cuenta + número de cuenta + botón para copiar.

Finalmente:

→ **CONTINUAR Y SUBIR COMPROBANTE**

→ comprobante

→ reservar boletos.

### Sobre los combos

También cambié la lógica para que la cantidad seleccionada quede directamente guardada en `st.session_state` mediante `on_click`. Por ejemplo, si el mínimo de una rifa es **15**:

* 🟢 NORMAL → 15
* 🔵 DOBLE → 30
* 🟣 INTERMEDIO → 45
* 🟠 PROFESIONAL → 75
* 🔴 PRO → 100

Y el máximo continúa siendo **100 boletos**.

**Una cosa muy importante:** si ya tienes un `rifas_v4.db` creado de una versión anterior, este código conserva esa base de datos. Si estás probando desde cero y quieres que se creen nuevamente todos los boletos de las rifas, puedes hacer una copia de seguridad y eliminar `rifas_v4.db` antes de ejecutar esta versión.
