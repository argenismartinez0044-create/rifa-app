import datetime
import os
import random
import sqlite3
import streamlit as st
from PIL import Image

# ---------------------------------------------------------
# 1. BASE DE DATOS (Persistencia y control de duplicados)
# ---------------------------------------------------------
DB_FILE = "rifa.db"


def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Tabla de Boletos
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS boletos (
            numero TEXT PRIMARY KEY,
            estado TEXT DEFAULT 'disponible', -- disponible, reservado, confirmado
            nombre TEXT,
            telefono TEXT,
            metodo_pago TEXT,
            comprobante_path TEXT,
            fecha_reserva TIMESTAMP
        )
    """
    )
    # Generar números del 00001 al 99999 si la base está vacía
    c.execute("SELECT COUNT(*) FROM boletos")
    if c.fetchone()[0] == 0:
        numeros = [f"{i:05d}" for i in range(1, 100000)]
        c.executemany("INSERT INTO boletos (numero) VALUES (?)", [(n,) for n in numeros])
        conn.commit()
    conn.close()


def liberar_reservas_expiradas():
    """Libera boletos reservados hace más de 24h sin confirmación."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    limite = datetime.datetime.now() - datetime.timedelta(hours=24)
    c.execute(
        """
        UPDATE boletos 
        SET estado = 'disponible', nombre = NULL, telefono = NULL, 
            metodo_pago = NULL, comprobante_path = NULL, fecha_reserva = NULL
        WHERE estado = 'reservado' AND fecha_reserva < ?
    """,
        (limite,),
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------
# 2. INTERFAZ Y LÓGICA DE APLICACIÓN
# ---------------------------------------------------------
st.set_page_config(page_title="Sistema de Rifas", layout="centered")
init_db()
liberar_reservas_expiradas()

st.title("🎟️ Rifa Oficial - Participa y Gana")

# Menú lateral para navegación
opcion = st.sidebar.radio("Navegación", ["Comprar Boletos", "Administración"])

if opcion == "Comprar Boletos":
    st.header("📸 Premio de la Rifa")

    # Carga opcional de la imagen de la rifa
    if os.path.exists("premio.jpg"):
        st.image("premio.jpg", caption="Premio Principal", use_column_width=True)

    st.markdown("---")
    st.header("💳 Métodos de Pago")
    st.info(
        """
    - **Transferencia Bancaria:** Banco ABC - Cuenta: 123-456789-0
    - **Pago Móvil / Wallet:** +1 800 555 0199
    - **Efectivo / Agente:** Solicitar datos por WhatsApp
    """
    )

    st.markdown("---")
    st.header("📝 Formulario de Registro")

    with st.form("registro_rifa"):
        nombre = st.text_input("Nombre completo")
        telefono = st.text_input("Número de Teléfono / WhatsApp")
        cantidad = st.number_input(
            "Cantidad de boletos a comprar", min_value=1, max_value=10, value=1
        )
        metodo_pago = st.selectbox(
            "Método de pago realizado",
            ["Transferencia Bancaria", "Pago Móvil", "Efectivo"],
        )
        comprobante = st.file_uploader(
            "Sube tu volante/comprobante de pago (JPG, PNG)",
            type=["png", "jpg", "jpeg"],
        )

        submit = st.form_submit_button("Reservar Boletos")

    if submit:
        if not nombre or not telefono or not comprobante:
            st.error(
                "Por favor completa todos los campos y sube el comprobante de pago."
            )
        else:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()

            # Obtener boletos disponibles
            c.execute("SELECT numero FROM boletos WHERE estado = 'disponible'")
            disponibles = [row[0] for row in c.fetchall()]

            if len(disponibles) < cantidad:
                st.error("No hay suficientes boletos disponibles.")
            else:
                # Selección aleatoria sin repetición
                boletos_asignados = random.sample(disponibles, cantidad)

                # Guardar comprobante
                os.makedirs("comprobantes", exist_ok=True)
                comprobante_path = (
                    f"comprobantes/{telefono}_{datetime.datetime.now().timestamp()}.jpg"
                )
                image = Image.open(comprobante)
                image.save(comprobante_path)

                # Actualizar estado a 'reservado'
                ahora = datetime.datetime.now()
                for num in boletos_asignados:
                    c.execute(
                        """
                        UPDATE boletos 
                        SET estado = 'reservado', nombre = ?, telefono = ?, 
                            metodo_pago = ?, comprobante_path = ?, fecha_reserva = ?
                        WHERE numero = ?
                    """,
                        (
                            nombre,
                            telefono,
                            metodo_pago,
                            comprobante_path,
                            ahora,
                            num,
                        ),
                    )

                conn.commit()
                conn.close()

                # Confirmación al usuario
                st.success("🎉 ¡Boletos asignados exitosamente!")
                st.warning(
                    "⚠️ **IMPORTANTE:** Tienes **24 horas** para que tu pago sea verificado por el administrador. "
                    "De lo contrario, los números se liberarán automáticamente."
                )

                st.subheader("🎟️ Tus Números Asignados:")
                cols = st.columns(len(boletos_asignados))
                for idx, num in enumerate(boletos_asignados):
                    cols[idx].metric("Boleto", num)

elif opcion == "Administración":
    st.header("⚙️ Panel de Administración")
    clave = st.text_input("Contraseña de admin", type="password")

    if clave == "admin123":  # Cambiar por una clave segura
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()

        st.subheader("🖼️ Configurar Foto de la Rifa")
        foto_premio = st.file_uploader(
            "Subir nueva foto del premio", type=["jpg", "png", "jpeg"]
        )
        if foto_premio:
            img = Image.open(foto_premio)
            img.save("premio.jpg")
            st.success("Imagen del premio actualizada.")

        st.markdown("---")
        st.subheader("📌 Reservas Pendientes por Confirmar")

        c.execute(
            "SELECT numero, nombre, telefono, metodo_pago, comprobante_path, fecha_reserva FROM boletos WHERE estado = 'reservado'"
        )
        pendientes = c.fetchall()

        if not pendientes:
            st.info("No hay reservas pendientes de aprobación.")
        else:
            for item in pendientes:
                num, nom, tel, met, img_path, fecha = item
                st.write(f"**Boleto:** `{num}` | **Cliente:** {nom} | **Tel:** {tel}")
                st.write(f"**Método:** {met} | **Fecha Reserva:** {fecha}")

                if os.path.exists(img_path):
                    st.image(img_path, width=300, caption=f"Comprobante - {nom}")

                col1, col2 = st.columns(2)
                if col1.button(f"Confirmar {num}", key=f"conf_{num}"):
                    c.execute(
                        "UPDATE boletos SET estado = 'confirmado' WHERE numero = ?",
                        (num,),
                    )
                    conn.commit()
                    st.rerun()

                if col2.button(f"Rechazar/Liberar {num}", key=f"rec_{num}"):
                    c.execute(
                        """
                        UPDATE boletos 
                        SET estado = 'disponible', nombre = NULL, telefono = NULL, 
                            metodo_pago = NULL, comprobante_path = NULL, fecha_reserva = NULL
                        WHERE numero = ?
                    """,
                        (num,),
                    )
                    conn.commit()
                    st.rerun()
                st.markdown("---")

        conn.close()
