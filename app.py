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
# BASE DE DATOS (NO BORRA LOS DATOS EXISTENTES)
# =========================================================

def conectar():
    return sqlite3.connect(DB_FILE, check_same_thread=False)


def agregar_columna_si_no_existe(conn, tabla, columna, definicion):
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({tabla})")
    columnas = [x[1] for x in cur.fetchall()]

    if columna not in columnas:
        cur.execute(
            f"ALTER TABLE {tabla} ADD COLUMN {columna} {definicion}"
        )


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

    agregar_columna_si_no_existe(
        conn,
        "rifas",
        "activa",
        "INTEGER DEFAULT 1"
    )

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
            (
                "Banreservas",
                "ARGENIS MARTINEZ C.",
                "Ahorros",
                "9606561652",
                "banreservas.png"
            ),
            (
                "Banco Popular",
                "ARGENIS MARTINEZ",
                "Ahorros",
                "821794971",
                "popular.png"
            ),
        ])

    # Solo crea las 2 rifas originales si la base está vacía.
    c.execute("SELECT COUNT(*) FROM rifas")

    if c.fetchone()[0] == 0:

        iniciales = [
            (
                "PlayStation 5 Pro",
                "Juego",
                5.0,
                15,
                100000,
                "play.jpg",
                "Fecha pendiente"
            ),
            (
                "5 iPhone 17 Pro Max",
                "TELÉFONO",
                15.0,
                10,
                100000,
                "iphone.jpg",
                "Al vender el 80%"
            ),
        ]

        for rifa in iniciales:
            c.execute("""
                INSERT INTO rifas
                (
                    nombre,
                    categoria,
                    precio_boleto,
                    min_boletos,
                    total_boletos,
                    imagen,
                    fecha,
                    activa
                )
                VALUES (?,?,?,?,?,?,?,1)
            """, rifa)

        for rifa_id in (1, 2):

            numeros = [
                (rifa_id, f"{i:05d}")
                for i in range(1, 100001)
            ]

            c.executemany(
                "INSERT INTO boletos (rifa_id,numero) VALUES (?,?)",
                numeros
            )

    conn.commit()
    conn.close()


def liberar_expirados():

    conn = conectar()

    conn.execute("""
        UPDATE boletos
        SET
            estado='disponible',
            usuario_nombre=NULL,
            usuario_telefono=NULL,
            metodo_pago=NULL,
            comprobante=NULL,
            fecha_reserva=NULL
        WHERE
            estado='reservado'
            AND fecha_reserva < ?
    """, (
        datetime.datetime.now()
        - datetime.timedelta(minutes=15),
    ))

    conn.commit()
    conn.close()


init_db()
liberar_expirados()


# =========================================================
# CONFIGURACIÓN DEL TEMA
# =========================================================

if "tema_claro" not in st.session_state:
    st.session_state["tema_claro"] = False

if "vista_actual" not in st.session_state:
    st.session_state["vista_actual"] = "rifas"

# Estado del verificador
if "verificador_paso" not in st.session_state:
    st.session_state["verificador_paso"] = 1

if "verificador_rifa" not in st.session_state:
    st.session_state["verificador_rifa"] = None

if "telefono_verificador" not in st.session_state:
    st.session_state["telefono_verificador"] = ""

if "resultados_verificador" not in st.session_state:
    st.session_state["resultados_verificador"] = None

# Estado del soporte IA
if "mostrar_soporte_ia" not in st.session_state:
    st.session_state["mostrar_soporte_ia"] = False


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

    limpio = "".join(
        ch if ch.isalnum() else "_"
        for ch in base
    )

    ruta = os.path.join(
        carpeta,
        f"{limpio}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}{ext}"
    )

    with open(ruta, "wb") as f:
        f.write(uploaded.getbuffer())

    return ruta


def guardar_comprobante(uploaded):

    base = st.session_state.get(
        "telefono_cliente",
        "cliente"
    )

    return guardar_imagen(
        uploaded,
        "comprobantes",
        base
    )


def seleccionar_rifa(
    rifa_id,
    nombre,
    precio,
    minimo
):

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
        SELECT
            COUNT(*),
            SUM(
                CASE
                    WHEN estado='disponible'
                    THEN 1 ELSE 0
                END
            ),
            SUM(
                CASE
                    WHEN estado='reservado'
                    THEN 1 ELSE 0
                END
            ),
            SUM(
                CASE
                    WHEN estado='confirmado'
                    THEN 1 ELSE 0
                END
            )
        FROM boletos
        WHERE rifa_id=?
    """, (rifa_id,)).fetchone()

    conn.close()

    return tuple(
        x or 0
        for x in fila
    )


def crear_boletos(
    conn,
    rifa_id,
    cantidad
):

    conn.executemany(
        """
        INSERT INTO boletos
        (rifa_id,numero,estado)
        VALUES (?,?,'disponible')
        """,
        [
            (
                rifa_id,
                f"{i:05d}"
            )
            for i in range(1, cantidad + 1)
        ]
    )


def obtener_metodos_pago(
    activos_solo=True
):

    conn = conectar()

    if activos_solo:

        filas = conn.execute("""
            SELECT
                id,
                nombre,
                titular,
                tipo_cuenta,
                numero_cuenta,
                imagen,
                activo
            FROM metodos_pago
            WHERE COALESCE(activo,1)=1
            ORDER BY id
        """).fetchall()

    else:

        filas = conn.execute("""
            SELECT
                id,
                nombre,
                titular,
                tipo_cuenta,
                numero_cuenta,
                imagen,
                activo
            FROM metodos_pago
            ORDER BY id
        """).fetchall()

    conn.close()

    return filas


def limpiar_compra():

    for k in (
        "rifa_seleccionada",
        "nombre_rifa",
        "precio_rifa",
        "min_rifa",
        "cant_boletos",
        "paso_compra",
        "nombre_cliente",
        "telefono_cliente",
        "banco_pago",
        "compra_completada"
    ):
        st.session_state.pop(k, None)


# =========================================================
# NAVEGACIÓN PÚBLICA
# =========================================================

def abrir_verificador():

    st.session_state["vista_actual"] = "verificador"
    st.session_state["verificador_paso"] = 1
    st.session_state["verificador_rifa"] = None
    st.session_state["telefono_verificador"] = ""
    st.session_state["resultados_verificador"] = None


def volver_rifas():

    st.session_state["vista_actual"] = "rifas"
    st.session_state["verificador_paso"] = 1
    st.session_state["verificador_rifa"] = None
    st.session_state["telefono_verificador"] = ""
    st.session_state["resultados_verificador"] = None


def abrir_como_jugar():

    st.session_state["vista_actual"] = "como_jugar"


def normalizar_telefono(telefono):

    return (
        telefono
        .replace(" ", "")
        .replace("-", "")
        .replace("(", "")
        .replace(")", "")
        .replace("+", "")
        .strip()
    )


# =========================================================
# SOPORTE IA
# =========================================================

@st.dialog("🤖 Asistente Virtual - Rifas Sirio RD")
def abrir_soporte_ia():

    st.caption(
        "Respuestas instantáneas las 24 horas."
    )

    if "mensajes_chat" not in st.session_state:

        st.session_state["mensajes_chat"] = [{
            "role": "assistant",
            "content": (
                "¡Hola! Soy tu asistente de **Rifas Sirio RD** 🎲.\n\n"
                "¿En qué te puedo ayudar?"
            )
        }]

    # =====================================================
    # RESPUESTAS RÁPIDAS
    # =====================================================

    c1, c2, c3, c4, c5 = st.columns(5)

    opcion = None

    if c1.button(
        "🎲 ¿Cómo jugar?",
        key="dlg_c1",
        use_container_width=True
    ):
        opcion = "¿Cómo participar?"

    if c2.button(
        "💳 Bancos",
        key="dlg_c2",
        use_container_width=True
    ):
        opcion = "cuentas de banco"

    if c3.button(
        "🔎 Mis boletos",
        key="dlg_c3",
        use_container_width=True
    ):
        opcion = "verificar mis boletos"

    if c4.button(
        "📅 Sorteos",
        key="dlg_c4",
        use_container_width=True
    ):
        opcion = "fecha del sorteo"

    if c5.button(
        "👤 Soporte humano",
        key="dlg_soporte",
        use_container_width=True
    ):
        st.session_state["mostrar_soporte_ia"] = True

    # =====================================================
    # MENSAJES
    # =====================================================

    for msg in st.session_state["mensajes_chat"]:

        with st.chat_message(msg["role"]):

            st.markdown(
                msg["content"]
            )

    entrada = st.chat_input(
        "Escribe tu duda..."
    )

    prompt = entrada or opcion

    if prompt:

        if entrada:

            st.session_state[
                "mensajes_chat"
            ].append({
                "role": "user",
                "content": prompt
            })

        txt = prompt.lower()

        # -----------------------------------------------
        # CÓMO JUGAR
        # -----------------------------------------------

        if any(
            w in txt
            for w in [
                "jugar",
                "participar",
                "funciona",
                "pasos",
                "comprar",
                "instrucciones"
            ]
        ):

            resp = (
                "1. Selecciona una rifa.\n"
                "2. Elige la cantidad de boletos o un combo.\n"
                "3. Realiza la transferencia bancaria.\n"
                "4. Sube el comprobante.\n"
                "5. Espera la validación de tu pago.\n"
                "6. Puedes verificar tus boletos con tu número de WhatsApp."
            )

        # -----------------------------------------------
        # BANCOS
        # -----------------------------------------------

        elif any(
            w in txt
            for w in [
                "pago",
                "banco",
                "transferencia",
                "banreservas",
                "popular",
                "cuenta"
            ]
        ):

            resp = (
                "Los métodos de pago disponibles aparecen después "
                "de completar los datos de la rifa.\n\n"
                "El administrador puede agregar o actualizar bancos "
                "desde **⚙️ Administración → 🏦 Métodos de pago**."
            )

        # -----------------------------------------------
        # VERIFICADOR
        # -----------------------------------------------

        elif any(
            w in txt
            for w in [
                "verificar",
                "consultar",
                "mi boleto",
                "mis boletos",
                "numeros",
                "números"
            ]
        ):

            resp = (
                "Puedes utilizar el botón **🔎 Verificar boleto** "
                "que aparece en la parte superior de la página.\n\n"
                "Primero selecciona la rifa y luego introduce el "
                "número de WhatsApp utilizado para registrar tus boletos."
            )

        # -----------------------------------------------
        # SORTEOS
        # -----------------------------------------------

        elif any(
            w in txt
            for w in [
                "ganador",
                "sorteo",
                "fecha",
                "cuando",
                "cuándo"
            ]
        ):

            resp = (
                "La condición o fecha del sorteo aparece "
                "en la ficha correspondiente de cada rifa."
            )

        # -----------------------------------------------
        # PRECIOS
        # -----------------------------------------------

        elif any(
            w in txt
            for w in [
                "precio",
                "costo",
                "minimo",
                "mínimo",
                "combo",
                "boletos"
            ]
        ):

            resp = (
                "Los precios y cantidades mínimas dependen de cada rifa. "
                "Puedes consultar el precio directamente en la ficha "
                "del premio que deseas jugar."
            )

        # -----------------------------------------------
        # SOPORTE
        # -----------------------------------------------

        elif any(
            w in txt
            for w in [
                "soporte",
                "humano",
                "persona",
                "administrador",
                "ayuda"
            ]
        ):

            resp = (
                "Claro. Si necesitas ayuda de una persona, puedes "
                "contactar directamente con nuestro soporte humano "
                "por WhatsApp."
            )

            st.session_state[
                "mostrar_soporte_ia"
            ] = True

        # -----------------------------------------------
        # PREGUNTA NO RECONOCIDA
        # -----------------------------------------------

        else:

            resp = (
                "No estoy seguro de poder responder esa pregunta "
                "correctamente. 🤔\n\n"
                "Para recibir ayuda personalizada puedes hablar "
                "directamente con una persona de nuestro equipo."
            )

            st.session_state[
                "mostrar_soporte_ia"
            ] = True

        st.session_state[
            "mensajes_chat"
        ].append({
            "role": "assistant",
            "content": resp
        })

        st.rerun()

    # =====================================================
    # SOPORTE HUMANO
    # =====================================================

    if st.session_state.get(
        "mostrar_soporte_ia",
        False
    ):

        st.markdown("---")

        st.markdown(
            "### 👤 ¿Necesitas hablar con una persona?"
        )

        st.write(
            "Nuestro soporte humano puede ayudarte directamente "
            "por WhatsApp."
        )

        st.link_button(
            "💬 HABLAR CON SOPORTE HUMANO",
            f"https://wa.me/{WHATSAPP_NUMERO}",
            use_container_width=True
        )

        st.caption(
            f"WhatsApp de soporte: {WHATSAPP_NUMERO}"
        )


# =========================================================
# ESTILO Y NAVEGACIÓN
# =========================================================

query_params = st.query_params

es_admin_url = (
    query_params.get(
        "admin",
        ""
    ).lower()
    in ["true", "1"]
)


# =========================================================
# ESTILO PÚBLICO
# =========================================================

if not es_admin_url:

    if st.session_state["tema_claro"]:

        st.markdown("""
        <style>

        .stApp {
            background:
                linear-gradient(
                    135deg,
                    #f8f9fc 0%,
                    #eef1f7 50%,
                    #ffffff 100%
                ) !important;

            color: #111111;
        }

        .barra-superior {
            width: 100%;
            padding: 5px 0 12px 0;
        }

        div.stButton > button {
            border-radius: 14px;
            min-height: 45px;
            font-weight: 700;
            background: rgba(255,255,255,0.85);
        }

        .verificador-card {
            background:
                linear-gradient(
                    135deg,
                    #ffffff,
                    #eef1f7
                );

            border: 1px solid #d7dbe5;
            border-radius: 18px;
            padding: 25px;
            margin: 25px 0;
        }

        </style>
        """, unsafe_allow_html=True)

    else:

        st.markdown("""
        <style>

        .stApp {
            background:
                linear-gradient(
                    135deg,
                    #0b0d17 0%,
                    #171b2e 50%,
                    #080910 100%
                ) !important;

            color: #ffffff;
        }

        .barra-superior {
            width: 100%;
            padding: 5px 0 12px 0;
        }

        div.stButton > button {
            border-radius: 14px;
            min-height: 45px;
            font-weight: 700;
            transition: 0.2s;
        }

        div.stButton > button:hover {
            border-color: #F5C518 !important;
            color: #F5C518 !important;
        }

        .verificador-card {
            background:
                linear-gradient(
                    135deg,
                    #101522,
                    #1c2638
                );

            border: 1px solid rgba(245,197,24,0.35);
            border-radius: 18px;
            padding: 25px;
            margin: 25px 0;
        }

        </style>
        """, unsafe_allow_html=True)


# =========================================================
# BARRA SUPERIOR PÚBLICA
# =========================================================

if not es_admin_url:

    st.markdown(
        '<div class="barra-superior"></div>',
        unsafe_allow_html=True
    )

    nav1, nav2, nav3, nav4 = st.columns(
        [1.1, 1.3, 0.7, 1.5]
    )

    # -----------------------------------------------
    # RIFAS
    # -----------------------------------------------

    with nav1:

        if st.button(
            "🎟️ Rifas",
            key="nav_rifas",
            use_container_width=True
        ):

            volver_rifas()
            st.rerun()

    # -----------------------------------------------
    # CÓMO JUGAR
    # -----------------------------------------------

    with nav2:

        if st.button(
            "❓ Cómo jugar",
            key="nav_como_jugar",
            use_container_width=True
        ):

            abrir_como_jugar()
            st.rerun()

    # -----------------------------------------------
    # TEMA
    # -----------------------------------------------

    with nav3:

        tema_icono = (
            "☀️"
            if not st.session_state["tema_claro"]
            else "🌙"
        )

        if st.button(
            tema_icono,
            key="nav_tema",
            use_container_width=True
        ):

            st.session_state["tema_claro"] = (
                not st.session_state["tema_claro"]
            )

            st.rerun()

    # -----------------------------------------------
    # VERIFICAR BOLETO
    # -----------------------------------------------

    with nav4:

        if st.button(
            "🔎 Verificar boleto",
            key="nav_verificar",
            use_container_width=True
        ):

            abrir_verificador()
            st.rerun()


# =========================================================
# MENÚ LATERAL
# =========================================================

opciones_menu = [
    "🏠 Inicio & Catálogo",
    "❓ Cómo jugar",
    "🤖 Soporte IA",
    "🏆 Ganadores"
]

# Administración solamente mediante ?admin=true

if es_admin_url:

    opciones_menu.append(
        "⚙️ Administración"
    )

index_defecto = (
    len(opciones_menu) - 1
    if es_admin_url
    else 0
)

seccion = st.sidebar.radio(
    "Navegación",
    opciones_menu,
    index=index_defecto
)

st.sidebar.markdown("---")

if st.sidebar.button(
    "🤖 Abrir Chat de Soporte IA",
    use_container_width=True
):

    abrir_soporte_ia()


# =========================================================
# VISTA PÚBLICA: VERIFICADOR
# =========================================================

if (
    not es_admin_url
    and st.session_state.get("vista_actual")
    == "verificador"
):

    st.markdown("""
    <div class="verificador-card">
        <h2 style="color:#F5C518;">
            🔎 Verificar mis boletos
        </h2>

        <p>
            Consulta los boletos registrados a tu número
            de WhatsApp para una rifa específica.
        </p>
    </div>
    """, unsafe_allow_html=True)

    paso = st.session_state.get(
        "verificador_paso",
        1
    )

    # =====================================================
    # PASO 1
    # =====================================================

    if paso == 1:

        st.markdown(
            "### 🟡 PASO 1 — Selecciona la rifa"
        )

        conn = conectar()

        rifas_verificador = conn.execute("""
            SELECT
                id,
                nombre,
                categoria,
                imagen
            FROM rifas
            WHERE COALESCE(activa,1)=1
            ORDER BY id
        """).fetchall()

        conn.close()

        if not rifas_verificador:

            st.info(
                "No hay rifas activas disponibles."
            )

        else:

            opciones_rifas = {
                f"{nombre} — {categoria}": rid
                for rid, nombre, categoria, imagen
                in rifas_verificador
            }

            rifa_elegida = st.selectbox(
                "Selecciona la rifa que deseas consultar:",
                list(opciones_rifas.keys()),
                key="selector_rifa_verificador"
            )

            rid_verificador = opciones_rifas[
                rifa_elegida
            ]

            datos_rifa = next(
                r
                for r in rifas_verificador
                if r[0] == rid_verificador
            )

            rid, nombre_rifa_ver, categoria_ver, imagen_ver = datos_rifa

            if imagen_ver and archivo_existe(imagen_ver):

                c1, c2 = st.columns(
                    [1, 2]
                )

                with c1:

                    st.image(
                        imagen_ver,
                        use_container_width=True
                    )

                with c2:

                    st.markdown(
                        f"## 🎟️ {nombre_rifa_ver}"
                    )

                    st.caption(
                        f"Categoría: {categoria_ver}"
                    )

            st.markdown("")

            if st.button(
                "➡️ CONTINUAR",
                key="continuar_verificador",
                use_container_width=True
            ):

                st.session_state[
                    "verificador_rifa"
                ] = rid_verificador

                st.session_state[
                    "verificador_paso"
                ] = 2

                st.session_state[
                    "resultados_verificador"
                ] = None

                st.rerun()


    # =====================================================
    # PASO 2
    # =====================================================

    elif paso == 2:

        st.markdown(
            "### 🟡 PASO 2 — Introduce tu teléfono"
        )

        rid_verificador = st.session_state.get(
            "verificador_rifa"
        )

        if not rid_verificador:

            st.warning(
                "Primero debes seleccionar una rifa."
            )

            if st.button(
                "⬅️ Volver al paso 1",
                key="volver_paso1_error",
                use_container_width=True
            ):

                st.session_state[
                    "verificador_paso"
                ] = 1

                st.rerun()

        else:

            conn = conectar()

            rifa_info = conn.execute("""
                SELECT
                    nombre,
                    categoria
                FROM rifas
                WHERE id=?
            """, (
                rid_verificador,
            )).fetchone()

            conn.close()

            if rifa_info:

                nombre_rifa_ver, categoria_ver = (
                    rifa_info
                )

                st.success(
                    f"🎟️ Rifa seleccionada: "
                    f"**{nombre_rifa_ver}**"
                )

            telefono_ver = st.text_input(
                "📱 Número de WhatsApp registrado",
                value=st.session_state.get(
                    "telefono_verificador",
                    ""
                ),
                placeholder="Ejemplo: 8294835217",
                key="input_telefono_verificador"
            )

            c1, c2 = st.columns(2)

            with c1:

                if st.button(
                    "⬅️ CAMBIAR RIFA",
                    key="cambiar_rifa_verificador",
                    use_container_width=True
                ):

                    st.session_state[
                        "verificador_paso"
                    ] = 1

                    st.session_state[
                        "verificador_rifa"
                    ] = None

                    st.session_state[
                        "telefono_verificador"
                    ] = ""

                    st.session_state[
                        "resultados_verificador"
                    ] = None

                    st.rerun()

            with c2:

                buscar = st.button(
                    "🔎 BUSCAR MIS BOLETOS",
                    key="buscar_boletos_verificador",
                    use_container_width=True
                )

            if buscar:

                telefono_limpio = normalizar_telefono(
                    telefono_ver
                )

                if not telefono_limpio:

                    st.error(
                        "Introduce tu número de teléfono."
                    )

                else:

                    st.session_state[
                        "telefono_verificador"
                    ] = telefono_limpio

                    conn = conectar()

                    boletos_ver = conn.execute("""
                        SELECT
                            b.numero,
                            b.estado,
                            b.usuario_nombre,
                            b.usuario_telefono,
                            r.nombre
                        FROM boletos b
                        INNER JOIN rifas r
                            ON b.rifa_id = r.id
                        WHERE
                            b.rifa_id=?
                            AND b.usuario_telefono=?
                            AND b.estado IN (
                                'reservado',
                                'confirmado'
                            )
                        ORDER BY b.numero
                    """, (
                        rid_verificador,
                        telefono_limpio
                    )).fetchall()

                    conn.close()

                    st.session_state[
                        "resultados_verificador"
                    ] = boletos_ver


            # =================================================
            # RESULTADOS
            # =================================================

            resultados = st.session_state.get(
                "resultados_verificador"
            )

            if resultados is not None:

                st.markdown("---")

                if not resultados:

                    st.warning(
                        "No encontramos boletos registrados "
                        "con ese número para la rifa seleccionada."
                    )

                else:

                    st.success(
                        f"🎉 Se encontraron "
                        f"**{len(resultados)} boletos** "
                        f"para esta rifa."
                    )

                    nombre_cliente_resultado = (
                        resultados[0][2]
                    )

                    if nombre_cliente_resultado:

                        st.markdown(
                            f"### 👤 "
                            f"{nombre_cliente_resultado}"
                        )

                    st.markdown(
                        "### 🎟️ Tus boletos"
                    )

                    for (
                        numero,
                        estado,
                        cliente,
                        telefono,
                        rifa
                    ) in resultados:

                        c1, c2, c3 = st.columns(
                            [1, 2, 2]
                        )

                        with c1:

                            st.markdown(
                                f"### `{numero}`"
                            )

                        with c2:

                            if estado == "confirmado":

                                st.success(
                                    "✅ CONFIRMADO"
                                )

                            elif estado == "reservado":

                                st.warning(
                                    "⏳ PENDIENTE DE VALIDACIÓN"
                                )

                            else:

                                st.info(
                                    estado.upper()
                                )

                        with c3:

                            st.write(
                                f"🎟️ {rifa}"
                            )

                        st.markdown("---")

                    st.caption(
                        "Los boletos pendientes aún deben "
                        "ser validados por la administración."
                    )

    st.markdown("---")

    if st.button(
        "🏠 VOLVER A LAS RIFAS",
        key="volver_rifas_verificador",
        use_container_width=True
    ):

        volver_rifas()
        st.rerun()


# =========================================================
# CATÁLOGO + COMPRA
# =========================================================

elif seccion == "🏠 Inicio & Catálogo":

    # Si el usuario está en "Cómo jugar" no mostramos catálogo.
    if st.session_state.get("vista_actual") == "como_jugar":

        st.header(
            "❓ Cómo Participar"
        )

        st.markdown("""
        ### 🎟️ ¿Cómo jugar?

        **1. Selecciona tu premio**

        Elige la rifa en la que deseas participar.

        **2. Selecciona tus boletos**

        Puedes seleccionar uno de los combos disponibles
        o indicar manualmente la cantidad de boletos.

        **3. Realiza el pago**

        Selecciona el método de pago disponible y realiza
        la transferencia por el monto correspondiente.

        **4. Sube el comprobante**

        Toma una foto clara del comprobante y súbela
        al sistema.

        **5. Espera la validación**

        La administración revisará tu comprobante.

        **6. Verifica tus boletos**

        Utiliza el botón **🔎 Verificar boleto** para
        consultar tus números utilizando el mismo
        número de WhatsApp registrado.
        """)

        st.markdown("---")

        if st.button(
            "🎟️ VER LAS RIFAS",
            use_container_width=True
        ):

            volver_rifas()
            st.rerun()

    else:

        # =================================================
        # ENCABEZADO
        # =================================================

        a, b = st.columns(
            [1, 2]
        )

        with a:

            if archivo_existe(
                "logo.png"
            ):

                st.image(
                    "logo.png",
                    width=220
                )

        with b:

            st.markdown(
                "<p style='color:#F5C518;font-weight:bold;'>"
                "Plataforma Exclusiva de Rifas"
                "</p>",
                unsafe_allow_html=True
            )

            st.markdown(
                "<h1 style='color:#FFF;'>"
                "Premios Exclusivos Garantizados"
                "</h1>",
                unsafe_allow_html=True
            )

        # =================================================
        # CARGAR RIFAS
        # =================================================

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
            ORDER BY id
        """).fetchall()

        conn.close()

        # =================================================
        # CATÁLOGO
        # =================================================

        for (
            rid,
            nombre,
            categoria,
            precio,
            minimo,
            total,
            imagen,
            fecha
        ) in rifas:

            (
                total_db,
                disponibles,
                reservados,
                confirmados
            ) = contar_estados(rid)

            progreso = (
                (
                    reservados
                    + confirmados
                )
                / total_db
                * 100
            ) if total_db else 0

            with st.container(
                border=True
            ):

                c1, c2 = st.columns(
                    [1, 2]
                )

                with c1:

                    if archivo_existe(imagen):

                        st.image(
                            imagen,
                            use_container_width=True
                        )

                    else:

                        st.info(
                            "Imagen no disponible"
                        )

                with c2:

                    st.markdown(
                        f"### {nombre}"
                    )

                    st.caption(
                        f"Categoría: {categoria}"
                    )

                    st.markdown(
                        f"### RD$ {precio:.2f}"
                    )

                    st.caption(
                        f"Mínimo {minimo} boletos"
                    )

                    st.write(
                        f"📅 **Fecha:** {fecha}"
                    )

                    st.write(
                        f"📊 **Progreso:** "
                        f"{progreso:.2f}%"
                    )

                    st.progress(
                        min(
                            1,
                            progreso / 100
                        )
                    )

                    st.button(
                        f"🎟️ PARTICIPAR POR "
                        f"{nombre.upper()}",
                        key=f"jugar_{rid}",
                        on_click=seleccionar_rifa,
                        args=(
                            rid,
                            nombre,
                            precio,
                            minimo
                        ),
                        use_container_width=True
                    )

        # =================================================
        # COMPRA
        # =================================================

        if "rifa_seleccionada" in st.session_state:

            st.markdown("---")

            nombre = st.session_state[
                "nombre_rifa"
            ]

            precio = st.session_state[
                "precio_rifa"
            ]

            minimo = int(
                st.session_state[
                    "min_rifa"
                ]
            )

            paso = st.session_state.get(
                "paso_compra",
                1
            )

            st.markdown(f"""
            <div style="
                background:
                linear-gradient(
                    135deg,
                    #0f2027,
                    #203a43,
                    #2c5364
                );
                border-radius:16px;
                padding:20px;
                text-align:center;
            ">

                <span style="
                    background:#F5C518;
                    color:#000;
                    font-weight:800;
                    padding:4px 12px;
                    border-radius:20px;
                ">
                    Rifa seleccionada
                </span>

                <h2 style="color:#fff;">
                    🎉 {nombre} 🎉
                </h2>

                <p style="color:#eee;">
                    Precio por boleto:
                    <strong style="color:#F5C518;">
                        RD$ {precio:.2f}
                    </strong>
                </p>

            </div>
            """, unsafe_allow_html=True)

            # =================================================
            # PASO 1 COMPRA
            # =================================================

            if paso == 1:

                st.subheader(
                    "📝 1. Completa tus datos "
                    "y selecciona tu combo"
                )

                st.markdown(
                    "### 💥 SELECCIÓN DE COMBOS DE BOLETOS"
                )

                combos = [
                    (
                        "🟢 COMBO BÁSICO",
                        minimo
                    ),
                    (
                        "🔵 COMBO DOBLE",
                        minimo * 2
                    ),
                    (
                        "🟣 COMBO INTERMEDIO",
                        minimo * 3
                    ),
                    (
                        "🟠 COMBO PROFESIONAL",
                        minimo * 5
                    ),
                    (
                        "🔴 COMBO PRO VIP",
                        minimo * 10
                    ),
                ]

                cols = st.columns(5)

                for i, (
                    nom_combo,
                    cantidad
                ) in enumerate(combos):

                    cantidad = min(
                        100,
                        cantidad
                    )

                    with cols[i]:

                        st.markdown(
                            f"""
                            **{nom_combo}**

                            🎟️ {cantidad} boletos

                            RD$ {cantidad * precio:.2f}
                            """
                        )

                        if st.button(
                            "Seleccionar",
                            key=f"combo_{i}",
                            use_container_width=True
                        ):

                            st.session_state[
                                "cant_boletos"
                            ] = cantidad

                            st.rerun()

                with st.form(
                    "datos_cliente"
                ):

                    nombre_cliente = st.text_input(
                        "Nombre Completo",
                        value=st.session_state.get(
                            "nombre_cliente",
                            ""
                        )
                    )

                    telefono = st.text_input(
                        "Teléfono / WhatsApp",
                        value=st.session_state.get(
                            "telefono_cliente",
                            ""
                        )
                    )

                    cantidad = st.number_input(
                        "✏️ Boletos seleccionados:",
                        min_value=minimo,
                        max_value=100,
                        value=int(
                            st.session_state.get(
                                "cant_boletos",
                                minimo
                            )
                        ),
                        step=1
                    )

                    st.markdown(
                        f"### 💰 Total: "
                        f"**RD$ {cantidad * precio:.2f}**"
                    )

                    continuar = st.form_submit_button(
                        "➡️ CONTINUAR AL PAGO",
                        use_container_width=True
                    )

                if continuar:

                    if (
                        not nombre_cliente.strip()
                        or not telefono.strip()
                    ):

                        st.error(
                            "Completa tu nombre "
                            "y teléfono/WhatsApp."
                        )

                    else:

                        st.session_state.update({
                            "nombre_cliente":
                                nombre_cliente.strip(),

                            "telefono_cliente":
                                telefono.strip(),

                            "cant_boletos":
                                int(cantidad),

                            "paso_compra":
                                2
                        })

                        st.rerun()

            # =================================================
            # PASO 2 PAGO
            # =================================================

            elif paso == 2:

                st.subheader(
                    "💳 2. Selecciona el método de pago"
                )

                metodos = obtener_metodos_pago(
                    True
                )

                if not metodos:

                    st.error(
                        "No hay métodos de pago activos. "
                        "El administrador debe agregar uno "
                        "desde ⚙️ Administración."
                    )

                else:

                    nombres_metodos = [
                        fila[1]
                        for fila in metodos
                    ]

                    metodo = st.radio(
                        "¿Dónde deseas realizar el pago?",
                        nombres_metodos,
                        horizontal=True,
                        key="banco_pago"
                    )

                    seleccionado = next(
                        fila
                        for fila in metodos
                        if fila[1] == metodo
                    )

                    (
                        metodo_id,
                        banco,
                        titular,
                        tipo_cuenta,
                        cuenta,
                        imagen_banco,
                        activo
                    ) = seleccionado

                    if (
                        imagen_banco
                        and archivo_existe(
                            imagen_banco
                        )
                    ):

                        st.image(
                            imagen_banco,
                            width=180
                        )

                    elif (
                        banco == "Banreservas"
                        and archivo_existe(
                            "barreserva.png"
                        )
                    ):

                        st.image(
                            "barreserva.png",
                            width=180
                        )

                    else:

                        st.info(
                            "Logo no disponible "
                            "para este método."
                        )

                    st.markdown(
                        f"### 🏦 {banco}"
                    )

                    st.write(
                        f"**Tipo:** {tipo_cuenta}"
                    )

                    st.write(
                        f"**Titular:** {titular}"
                    )

                    st.write(
                        "**Número de cuenta:**"
                    )

                    st.code(
                        str(cuenta),
                        language=None
                    )

                    st.caption(
                        "💡 Usa el icono de copiar que aparece "
                        "en el recuadro para copiar el número."
                    )

                    st.markdown(
                        f"### 💰 Total a pagar: "
                        f"**RD$ "
                        f"{st.session_state['cant_boletos'] * precio:.2f}**"
                    )

                    st.info(
                        "Realiza el depósito y luego sube "
                        "la foto del volante/comprobante."
                    )

                x, y = st.columns(2)

                with x:

                    if st.button(
                        "⬅️ VOLVER A DATOS Y COMBOS",
                        key="volver_datos",
                        use_container_width=True
                    ):

                        st.session_state[
                            "paso_compra"
                        ] = 1

                        st.rerun()

                with y:

                    if st.button(
                        "➡️ CONTINUAR Y SUBIR COMPROBANTE",
                        key="continuar_comprobante",
                        use_container_width=True
                    ):

                        st.session_state[
                            "paso_compra"
                        ] = 3

                        st.rerun()

            # =================================================
            # PASO 3 COMPROBANTE
            # =================================================

            elif paso == 3:

                st.subheader(
                    "📤 3. Sube el volante/comprobante "
                    "del depósito"
                )

                st.info(
                    f"Banco: **"
                    f"{st.session_state['banco_pago']}"
                    f"** · Total: **RD$ "
                    f"{st.session_state['cant_boletos'] * precio:.2f}"
                    f"**"
                )

                comprobante = st.file_uploader(
                    "Selecciona la imagen del "
                    "volante/comprobante",
                    type=[
                        "png",
                        "jpg",
                        "jpeg"
                    ],
                    key="comprobante_file"
                )

                x, y = st.columns(2)

                with x:

                    if st.button(
                        "⬅️ VOLVER AL BANCO",
                        key="volver_banco",
                        use_container_width=True
                    ):

                        st.session_state[
                            "paso_compra"
                        ] = 2

                        st.rerun()

                with y:

                    reservar = st.button(
                        "✅ RESERVAR MIS BOLETOS",
                        key="reservar_final",
                        use_container_width=True
                    )

                if reservar:

                    if not comprobante:

                        st.error(
                            "Debes subir el comprobante."
                        )

                    else:

                        conn = conectar()
                        cur = conn.cursor()

                        cur.execute("""
                            SELECT
                                id,
                                numero
                            FROM boletos
                            WHERE
                                rifa_id=?
                                AND estado='disponible'
                        """, (
                            st.session_state[
                                "rifa_seleccionada"
                            ],
                        ))

                        disponibles = cur.fetchall()

                        cantidad = int(
                            st.session_state[
                                "cant_boletos"
                            ]
                        )

                        if len(disponibles) < cantidad:

                            st.error(
                                "No hay suficientes boletos disponibles."
                            )

                            conn.close()

                        else:

                            asignados = random.sample(
                                disponibles,
                                cantidad
                            )

                            ruta = guardar_comprobante(
                                comprobante
                            )

                            ahora = (
                                datetime.datetime.now()
                            )

                            numeros = []

                            for (
                                bid,
                                numero
                            ) in asignados:

                                numeros.append(
                                    numero
                                )

                                cur.execute("""
                                    UPDATE boletos
                                    SET
                                        estado='reservado',
                                        usuario_nombre=?,
                                        usuario_telefono=?,
                                        metodo_pago=?,
                                        comprobante=?,
                                        fecha_reserva=?
                                    WHERE id=?
                                """, (
                                    st.session_state[
                                        "nombre_cliente"
                                    ],
                                    st.session_state[
                                        "telefono_cliente"
                                    ],
                                    st.session_state[
                                        "banco_pago"
                                    ],
                                    ruta,
                                    ahora,
                                    bid
                                ))

                            conn.commit()
                            conn.close()

                            st.success(
                                "🎉 ¡Boletos asignados temporalmente!"
                            )

                            st.info(
                                "Quedan pendientes de validación "
                                "del comprobante."
                            )

                            st.subheader(
                                "🎟️ Tus números asignados:"
                            )

                            cols = st.columns(
                                min(
                                    5,
                                    len(numeros)
                                )
                            )

                            for i, n in enumerate(
                                numeros
                            ):

                                cols[
                                    i % 5
                                ].metric(
                                    "Boleto",
                                    n,
                                    delta="Pendiente",
                                    delta_color="off"
                                )

                            for k in (
                                "rifa_seleccionada",
                                "nombre_rifa",
                                "precio_rifa",
                                "min_rifa",
                                "paso_compra",
                                "banco_pago"
                            ):

                                st.session_state.pop(
                                    k,
                                    None
                                )


# =========================================================
# CÓMO JUGAR DESDE MENÚ LATERAL
# =========================================================

elif seccion == "❓ Cómo jugar":

    st.header(
        "❓ Cómo Participar"
    )

    st.markdown("""
    1. Selecciona tu premio.
    2. Compra tus boletos.
    3. Transfiere por banco.
    4. Sube el comprobante.
    5. Espera la validación.
    6. Verifica tus números.
    """)


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

    st.caption(
        "Panel para propietario y administrador."
    )

    admin_password = st.text_input(
        "Contraseña de administrador",
        type="password"
    )

    ADMIN_PASSWORD = st.secrets.get(
        "ADMIN_PASSWORD",
        "admin123"
    )

    OWNER_PASSWORD = st.secrets.get(
        "OWNER_PASSWORD",
        "sirio2026"
    )

    if admin_password in (
        ADMIN_PASSWORD,
        OWNER_PASSWORD
    ):

        rol = (
            "Propietario"
            if admin_password == OWNER_PASSWORD
            else "Administrador"
        )

        st.success(
            f"Acceso autorizado: **{rol}**"
        )

        t1, t2, t3, t4, t5 = st.tabs([
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

            st.subheader(
                "💳 Volantes/comprobantes pendientes"
            )

            conn = conectar()

            pendientes = conn.execute("""
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
                    ON b.rifa_id=r.id
                WHERE b.estado='reservado'
                ORDER BY b.fecha_reserva DESC
            """).fetchall()

            if not pendientes:

                st.info(
                    "No hay pagos pendientes."
                )

            else:

                for (
                    bid,
                    numero,
                    cliente,
                    telefono,
                    metodo,
                    comp,
                    fecha,
                    rifa
                ) in pendientes:

                    st.markdown(
                        f"### 🎟️ Boleto `{numero}` — {rifa}"
                    )

                    st.write(
                        f"👤 {cliente} | "
                        f"📱 {telefono} | "
                        f"💳 {metodo} | "
                        f"🕒 {fecha}"
                    )

                    if (
                        comp
                        and os.path.exists(comp)
                    ):

                        st.image(
                            comp,
                            width=350
                        )

                    else:

                        st.warning(
                            "Comprobante no disponible."
                        )

                    a, b = st.columns(2)

                    if a.button(
                        f"✅ Aprobar {numero}",
                        key=f"aprobar_{bid}",
                        use_container_width=True
                    ):

                        conn.execute(
                            """
                            UPDATE boletos
                            SET estado='confirmado'
                            WHERE id=?
                            """,
                            (bid,)
                        )

                        conn.commit()
                        st.rerun()

                    if b.button(
                        f"❌ Rechazar/Eliminar {numero}",
                        key=f"rechazar_{bid}",
                        use_container_width=True
                    ):

                        conn.execute("""
                            UPDATE boletos
                            SET
                                estado='disponible',
                                usuario_nombre=NULL,
                                usuario_telefono=NULL,
                                metodo_pago=NULL,
                                comprobante=NULL,
                                fecha_reserva=NULL
                            WHERE id=?
                        """, (bid,))

                        conn.commit()
                        st.rerun()

                    st.markdown("---")

            conn.close()


        # -------------------------------------------------
        # BOLETOS
        # -------------------------------------------------

        with t2:

            st.subheader(
                "🎟️ Control de boletos por rifa"
            )

            conn = conectar()

            rifas = conn.execute(
                "SELECT id,nombre FROM rifas ORDER BY id"
            ).fetchall()

            conn.close()

            for rid, nombre in rifas:

                (
                    total,
                    disponibles,
                    reservados,
                    confirmados
                ) = contar_estados(rid)

                with st.expander(
                    f"🎟️ {nombre}"
                ):

                    a, b, c, d = st.columns(4)

                    a.metric(
                        "Total",
                        total
                    )

                    b.metric(
                        "Disponibles",
                        disponibles
                    )

                    c.metric(
                        "Pendientes",
                        reservados
                    )

                    d.metric(
                        "Confirmados",
                        confirmados
                    )

                    if st.button(
                        f"🧹 VACIAR RIFA: {nombre}",
                        key=f"vaciar_{rid}",
                        use_container_width=True
                    ):

                        conn = conectar()

                        conn.execute("""
                            UPDATE boletos
                            SET
                                estado='disponible',
                                usuario_nombre=NULL,
                                usuario_telefono=NULL,
                                metodo_pago=NULL,
                                comprobante=NULL,
                                fecha_reserva=NULL
                            WHERE rifa_id=?
                        """, (rid,))

                        conn.execute(
                            """
                            UPDATE ofertas
                            SET estado='disponible'
                            WHERE rifa_id=?
                            """,
                            (rid,)
                        )

                        conn.commit()
                        conn.close()

                        st.success(
                            "Rifa vaciada."
                        )

                        st.rerun()


        # -------------------------------------------------
        # RIFAS
        # -------------------------------------------------

        with t3:

            st.subheader(
                "🎁 Crear, actualizar y administrar rifas"
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
                    fecha,
                    COALESCE(activa,1)
                FROM rifas
                ORDER BY id
            """).fetchall()

            conn.close()

            for (
                rid,
                nombre,
                categoria,
                precio,
                minimo,
                total,
                imagen,
                fecha,
                activa
            ) in rifas:

                with st.expander(
                    f"✏️ {nombre}"
                ):

                    with st.form(
                        f"editar_{rid}"
                    ):

                        n = st.text_input(
                            "Nombre",
                            value=nombre
                        )

                        cat = st.text_input(
                            "Categoría",
                            value=categoria
                        )

                        p = st.number_input(
                            "Precio por boleto",
                            min_value=0.0,
                            value=float(precio),
                            step=0.50
                        )

                        m = st.number_input(
                            "Mínimo de boletos",
                            min_value=1,
                            value=int(minimo),
                            step=1
                        )

                        f = st.text_input(
                            "Fecha/condición",
                            value=fecha
                        )

                        act = st.checkbox(
                            "Rifa activa",
                            value=bool(activa)
                        )

                        guardar = st.form_submit_button(
                            "💾 GUARDAR CAMBIOS",
                            use_container_width=True
                        )

                    if guardar:

                        conn = conectar()

                        conn.execute("""
                            UPDATE rifas
                            SET
                                nombre=?,
                                categoria=?,
                                precio_boleto=?,
                                min_boletos=?,
                                fecha=?,
                                activa=?
                            WHERE id=?
                        """, (
                            n.strip(),
                            cat.strip(),
                            float(p),
                            int(m),
                            f.strip(),
                            1 if act else 0,
                            rid
                        ))

                        conn.commit()
                        conn.close()

                        st.success(
                            "Rifa actualizada."
                        )

                        st.rerun()

                    if st.button(
                        f"🗑️ Eliminar rifa: {nombre}",
                        key=f"del_rifa_{rid}",
                        use_container_width=True
                    ):

                        conn = conectar()
                        cur = conn.cursor()

                        estados = cur.execute(
                            """
                            SELECT COUNT(*)
                            FROM boletos
                            WHERE
                                rifa_id=?
                                AND estado IN (
                                    'reservado',
                                    'confirmado'
                                )
                            """,
                            (rid,)
                        ).fetchone()[0]

                        if estados:

                            conn.close()

                            st.error(
                                "No se puede eliminar: "
                                "primero vacía la rifa "
                                "y verifica los pagos."
                            )

                        else:

                            cur.execute(
                                "DELETE FROM ofertas WHERE rifa_id=?",
                                (rid,)
                            )

                            cur.execute(
                                "DELETE FROM boletos WHERE rifa_id=?",
                                (rid,)
                            )

                            cur.execute(
                                "DELETE FROM rifas WHERE id=?",
                                (rid,)
                            )

                            conn.commit()
                            conn.close()

                            st.success(
                                "Rifa eliminada."
                            )

                            st.rerun()

            st.markdown("---")

            st.subheader(
                "➕ Subir nueva rifa"
            )

            with st.form(
                "nueva_rifa"
            ):

                nombre_n = st.text_input(
                    "Nombre de la nueva rifa"
                )

                cat_n = st.text_input(
                    "Categoría",
                    value="Premio"
                )

                precio_n = st.number_input(
                    "Precio por boleto (RD$)",
                    min_value=0.0,
                    value=5.0,
                    step=0.50
                )

                minimo_n = st.number_input(
                    "Mínimo de boletos",
                    min_value=1,
                    value=10,
                    step=1
                )

                total_n = st.number_input(
                    "Cantidad total de boletos",
                    min_value=1,
                    max_value=1000000,
                    value=1000,
                    step=100
                )

                fecha_n = st.text_input(
                    "Fecha/condición",
                    value="Fecha pendiente"
                )

                imagen_n = st.file_uploader(
                    "Imagen de la nueva rifa",
                    type=[
                        "png",
                        "jpg",
                        "jpeg"
                    ],
                    key="imagen_nueva"
                )

                crear = st.form_submit_button(
                    "🚀 CREAR NUEVA RIFA",
                    use_container_width=True
                )

            if crear:

                if not nombre_n.strip():

                    st.error(
                        "Escribe el nombre de la rifa."
                    )

                else:

                    ruta_imagen = (
                        guardar_imagen(
                            imagen_n,
                            "rifas",
                            nombre_n
                        )
                        if imagen_n
                        else ""
                    )

                    conn = conectar()
                    cur = conn.cursor()

                    cur.execute("""
                        INSERT INTO rifas
                        (
                            nombre,
                            categoria,
                            precio_boleto,
                            min_boletos,
                            total_boletos,
                            imagen,
                            fecha,
                            activa
                        )
                        VALUES (?,?,?,?,?,?,?,1)
                    """, (
                        nombre_n.strip(),
                        cat_n.strip(),
                        float(precio_n),
                        int(minimo_n),
                        int(total_n),
                        ruta_imagen,
                        fecha_n.strip()
                    ))

                    nuevo_id = cur.lastrowid

                    crear_boletos(
                        conn,
                        nuevo_id,
                        int(total_n)
                    )

                    conn.commit()
                    conn.close()

                    st.success(
                        "🎉 Nueva rifa creada."
                    )

                    st.rerun()


        # -------------------------------------------------
        # OFERTAS
        # -------------------------------------------------

        with t4:

            st.subheader(
                "⭐ Números de oferta y premios"
            )

            conn = conectar()

            lista = conn.execute(
                "SELECT id,nombre FROM rifas ORDER BY id"
            ).fetchall()

            conn.close()

            if lista:

                mapa = {
                    nombre: rid
                    for rid, nombre in lista
                }

                elegido = st.selectbox(
                    "Selecciona la rifa",
                    list(mapa.keys())
                )

                rid = mapa[elegido]

                st.markdown(
                    "#### ➕ Oferta manual"
                )

                with st.form(
                    "oferta_manual"
                ):

                    numero = st.text_input(
                        "Número de boleto, ejemplo 00025"
                    )

                    premio = st.text_input(
                        "Premio",
                        placeholder="RD$ 1,000 en efectivo"
                    )

                    valor = st.number_input(
                        "Valor estimado del premio (RD$)",
                        min_value=0.0,
                        value=0.0,
                        step=100.0
                    )

                    guardar_oferta = st.form_submit_button(
                        "💾 GUARDAR OFERTA MANUAL"
                    )

                if guardar_oferta:

                    if (
                        not numero.strip()
                        or not premio.strip()
                    ):

                        st.error(
                            "Completa el número y el premio."
                        )

                    else:

                        num_fmt = f"{int(numero):05d}"

                        conn = conectar()

                        try:

                            conn.execute("""
                                INSERT INTO ofertas
                                (
                                    rifa_id,
                                    numero,
                                    premio,
                                    valor_premio,
                                    estado
                                )
                                VALUES (
                                    ?, ?, ?, ?, 'disponible'
                                )
                                ON CONFLICT(
                                    rifa_id,
                                    numero
                                )
                                DO UPDATE SET
                                    premio=excluded.premio,
                                    valor_premio=excluded.valor_premio
                            """, (
                                rid,
                                num_fmt,
                                premio.strip(),
                                float(valor)
                            ))

                            conn.commit()

                            st.success(
                                f"Oferta asignada al boleto "
                                f"`{num_fmt}`."
                            )

                            st.rerun()

                        except Exception as e:

                            st.error(
                                f"Error al guardar oferta: {e}"
                            )

                        finally:

                            conn.close()

                st.markdown("---")

                st.markdown(
                    "#### 🎲 Generar ofertas aleatorias"
                )

                with st.form(
                    "ofertas_random"
                ):

                    cant_random = st.number_input(
                        "Cantidad de ofertas a generar",
                        min_value=1,
                        max_value=50,
                        value=5,
                        step=1
                    )

                    premio_base = st.text_input(
                        "Premio base / Descripción",
                        value="Bono Sorpresa RD$ 500"
                    )

                    valor_base = st.number_input(
                        "Valor individual por oferta (RD$)",
                        min_value=0.0,
                        value=500.0,
                        step=50.0
                    )

                    gen_random = st.form_submit_button(
                        "🎲 GENERAR OFERTAS ALEATORIAS"
                    )

                if gen_random:

                    conn = conectar()
                    cur = conn.cursor()

                    disponibles = cur.execute(
                        """
                        SELECT numero
                        FROM boletos
                        WHERE
                            rifa_id=?
                            AND estado='disponible'
                        """,
                        (rid,)
                    ).fetchall()

                    if len(disponibles) < cant_random:

                        st.error(
                            "No hay suficientes boletos disponibles "
                            "para asignar esas ofertas."
                        )

                    else:

                        seleccionados = random.sample(
                            [
                                d[0]
                                for d in disponibles
                            ],
                            int(cant_random)
                        )

                        for num in seleccionados:

                            cur.execute("""
                                INSERT INTO ofertas
                                (
                                    rifa_id,
                                    numero,
                                    premio,
                                    valor_premio,
                                    estado
                                )
                                VALUES (
                                    ?, ?, ?, ?, 'disponible'
                                )
                                ON CONFLICT(
                                    rifa_id,
                                    numero
                                )
                                DO UPDATE SET
                                    premio=excluded.premio,
                                    valor_premio=excluded.valor_premio
                            """, (
                                rid,
                                num,
                                premio_base.strip(),
                                float(valor_base)
                            ))

                        conn.commit()

                        st.success(
                            f"Se generaron "
                            f"{cant_random} ofertas aleatorias "
                            f"con éxito."
                        )

                        st.rerun()

                    conn.close()

                st.markdown("---")

                st.markdown(
                    "#### 📜 Ofertas registradas para esta rifa"
                )

                conn = conectar()

                ofertas = conn.execute("""
                    SELECT
                        id,
                        numero,
                        premio,
                        valor_premio,
                        estado
                    FROM ofertas
                    WHERE rifa_id=?
                    ORDER BY numero
                """, (rid,)).fetchall()

                conn.close()

                if not ofertas:

                    st.info(
                        "No hay ofertas configuradas para esta rifa."
                    )

                else:

                    for (
                        oid,
                        num,
                        prem,
                        val,
                        est
                    ) in ofertas:

                        c1, c2, c3, c4 = st.columns(
                            [1, 3, 2, 1]
                        )

                        c1.write(
                            f"🎟️ `{num}`"
                        )

                        c2.write(
                            f"🎁 {prem}"
                        )

                        c3.write(
                            f"💰 RD$ {val:.2f} ({est})"
                        )

                        if c4.button(
                            "🗑️",
                            key=f"del_oferta_{oid}"
                        ):

                            conn = conectar()

                            conn.execute(
                                "DELETE FROM ofertas WHERE id=?",
                                (oid,)
                            )

                            conn.commit()
                            conn.close()

                            st.rerun()


        # -------------------------------------------------
        # MÉTODOS DE PAGO
        # -------------------------------------------------

        with t5:

            st.subheader(
                "🏦 Administrar Métodos de Pago"
            )

            metodos = obtener_metodos_pago(
                activos_solo=False
            )

            for (
                m_id,
                m_nombre,
                m_titular,
                m_tipo,
                m_cuenta,
                m_img,
                m_activo
            ) in metodos:

                with st.expander(
                    f"🏦 {m_nombre} "
                    f"({'Activo' if m_activo else 'Inactivo'})"
                ):

                    with st.form(
                        f"form_mp_{m_id}"
                    ):

                        nom = st.text_input(
                            "Nombre de la Institución/Banco",
                            value=m_nombre
                        )

                        tit = st.text_input(
                            "Titular de la Cuenta",
                            value=m_titular
                        )

                        tipo = st.selectbox(
                            "Tipo de Cuenta",
                            [
                                "Ahorros",
                                "Corriente"
                            ],
                            index=(
                                0
                                if m_tipo == "Ahorros"
                                else 1
                            )
                        )

                        num = st.text_input(
                            "Número de Cuenta",
                            value=m_cuenta
                        )

                        act = st.checkbox(
                            "Método Activo",
                            value=bool(m_activo)
                        )

                        img_file = st.file_uploader(
                            "Actualizar Logo (opcional)",
                            type=[
                                "png",
                                "jpg",
                                "jpeg"
                            ],
                            key=f"img_mp_{m_id}"
                        )

                        guardar_mp = st.form_submit_button(
                            "💾 GUARDAR CAMBIOS"
                        )

                    if guardar_mp:

                        conn = conectar()

                        ruta_img = m_img

                        if img_file:

                            ruta_img = guardar_imagen(
                                img_file,
                                "bancos",
                                nom
                            )

                        conn.execute("""
                            UPDATE metodos_pago
                            SET
                                nombre=?,
                                titular=?,
                                tipo_cuenta=?,
                                numero_cuenta=?,
                                imagen=?,
                                activo=?
                            WHERE id=?
                        """, (
                            nom.strip(),
                            tit.strip(),
                            tipo,
                            num.strip(),
                            ruta_img,
                            1 if act else 0,
                            m_id
                        ))

                        conn.commit()
                        conn.close()

                        st.success(
                            "Método de pago actualizado."
                        )

                        st.rerun()

                    if st.button(
                        f"🗑️ Eliminar {m_nombre}",
                        key=f"del_mp_{m_id}"
                    ):

                        conn = conectar()

                        conn.execute(
                            "DELETE FROM metodos_pago WHERE id=?",
                            (m_id,)
                        )

                        conn.commit()
                        conn.close()

                        st.success(
                            "Método de pago eliminado."
                        )

                        st.rerun()

            st.markdown("---")

            st.subheader(
                "➕ Agregar Nuevo Método de Pago"
            )

            with st.form(
                "nuevo_metodo_pago"
            ):

                n_nombre = st.text_input(
                    "Nombre del Banco/Plataforma"
                )

                n_titular = st.text_input(
                    "Nombre del Titular"
                )

                n_tipo = st.selectbox(
                    "Tipo de Cuenta",
                    [
                        "Ahorros",
                        "Corriente"
                    ]
                )

                n_cuenta = st.text_input(
                    "Número de Cuenta"
                )

                n_img = st.file_uploader(
                    "Logo/Imagen del Banco",
                    type=[
                        "png",
                        "jpg",
                        "jpeg"
                    ],
                    key="nueva_img_mp"
                )

                crear_mp = st.form_submit_button(
                    "🚀 CREAR MÉTODO DE PAGO"
                )

            if crear_mp:

                if (
                    not n_nombre.strip()
                    or not n_titular.strip()
                    or not n_cuenta.strip()
                ):

                    st.error(
                        "Completa todos los campos obligatorios."
                    )

                else:

                    ruta_img = (
                        guardar_imagen(
                            n_img,
                            "bancos",
                            n_nombre
                        )
                        if n_img
                        else ""
                    )

                    conn = conectar()

                    try:

                        conn.execute("""
                            INSERT INTO metodos_pago
                            (
                                nombre,
                                titular,
                                tipo_cuenta,
                                numero_cuenta,
                                imagen,
                                activo
                            )
                            VALUES (?, ?, ?, ?, ?, 1)
                        """, (
                            n_nombre.strip(),
                            n_titular.strip(),
                            n_tipo,
                            n_cuenta.strip(),
                            ruta_img
                        ))

                        conn.commit()

                        st.success(
                            "Nuevo método de pago "
                            "agregado correctamente."
                        )

                        st.rerun()

                    except sqlite3.IntegrityError:

                        st.error(
                            "Ya existe un método de pago "
                            "con ese nombre."
                        )

                    finally:

                        conn.close()
