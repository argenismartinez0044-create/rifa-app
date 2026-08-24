import streamlit as st
import sqlite3
import os
from datetime import datetime, timedelta
import random

# ==========================================
# CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(
    page_title="Sistema de Rifas",
    page_icon="🎟️",
    layout="wide"
)

DB_FILE = "rifas.db"

# ==========================================
# BASE DE DATOS E INICIALIZACIÓN
# ==========================================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Tabla de rifas
    c.execute("""
        CREATE TABLE IF NOT EXISTS rifas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            categoria TEXT,
            precio REAL NOT NULL,
            min_boletos INTEGER NOT NULL,
            total_boletos INTEGER NOT NULL,
            fecha_sorteo TEXT NOT NULL,
            imagen TEXT,
            activa INTEGER DEFAULT 1
        )
    """)
    
    # Tabla de boletos
    c.execute("""
        CREATE TABLE IF NOT EXISTS boletos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rifa_id INTEGER NOT NULL,
            numero INTEGER NOT NULL,
            estado TEXT DEFAULT 'disponible',
            usuario_nombre TEXT,
            usuario_telefono TEXT,
            comprobante TEXT,
            fecha_reserva TEXT,
            FOREIGN KEY (rifa_id) REFERENCES rifas (id)
        )
    """)
    
    # Tabla de administradores
    c.execute("""
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    
    # Admin por defecto si no existe ninguno
    c.execute("SELECT * FROM admin")
    if not c.fetchall():
        c.execute("INSERT INTO admin (usuario, password) VALUES (?, ?)", ("admin", "admin123"))
        
    conn.commit()
    conn.close()

def liberar_expirados():
    """Libera boletos reservados si han pasado más de 24 horas sin confirmación."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    hace_24h = (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
    
    c.execute(
        """
        UPDATE boletos 
        SET estado = 'disponible', usuario_nombre = NULL, usuario_telefono = NULL, comprobante = NULL, fecha_reserva = NULL 
        WHERE estado = 'reservado' AND fecha_reserva < ?
        """,
        (hace_24h,)
    )
    conn.commit()
    conn.close()

# Inicializar BD y limpiar boletos expirados al cargar
init_db()
liberar_expirados()

# ==========================================
# MENÚ NAVEGACIÓN LATERAL
# ==========================================
st.sidebar.title("🎟️ Menú Principal")
seccion = st.sidebar.radio(
    "Ir a:",
    ["🏠 Catálogo de Rifas", "🔎 Verificador de boletos", "🔒 Administración"]
)

# ==========================================
# SECCIÓN 1: CATÁLOGO DE RIFAS Y COMPRA
# ==========================================
if seccion == "🏠 Catálogo de Rifas":
    st.title("🎟️ Rifas Disponibles")
    st.write("Selecciona una rifa para participar y adquirir tus números.")
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM rifas WHERE activa = 1")
    rifas = c.fetchall()
    conn.close()
    
    if not rifas:
        st.info("No hay rifas activas en este momento. ¡Vuelve pronto!")
    else:
        cols = st.columns(2)
        for idx, r in enumerate(rifas):
            r_id, r_nombre, r_cat, r_precio, r_min, r_total, r_fecha, r_img, r_activa = r
            
            # Calcular progreso de boletos vendidos/reservados
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM boletos WHERE rifa_id = ? AND estado != 'disponible'", (r_id,))
            ocupados = c.fetchone()[0]
            conn.close()
            
            progreso = int((ocupados / r_total) * 100) if r_total > 0 else 0
            
            with cols[idx % 2]:
                st.markdown(f"### 🏷️ {r_nombre}")
                st.caption(f"Categoría: **{r_cat}**")
                
                if r_img and os.path.exists(r_img):
                    st.image(r_img, use_container_width=True)
                
                st.write(f"🗓️ **Fecha:** {r_fecha}")
                st.write(f"📊 **PROGRESO: {progreso}%**")
                st.progress(progreso / 100)
                
                st.markdown(f"#### **RD$ {r_precio:.2f}**")
                st.caption(f"Mínimo {r_min} boletos")
                
                label_btn = f"🎮 JUGAR POR {r_nombre.upper()}"
                if st.button(label_btn, key=f"btn_rifa_{r_id}"):
                    st.session_state["rifa_seleccionada"] = r_id
                    st.session_state["rifa_nombre"] = r_nombre
                    st.session_state["rifa_precio"] = r_precio
                    st.session_state["rifa_min"] = r_min
                    st.session_state["rifa_total"] = r_total

    # Formulario de compra si seleccionó una rifa
    if "rifa_seleccionada" in st.session_state:
        st.markdown("---")
        st.header(f"🎟️ Comprar Boletos - {st.session_state['rifa_nombre']}")
        
        cant_boletos = st.number_input(
            "Cantidad de boletos a comprar:",
            min_value=int(st.session_state["rifa_min"]),
            max_value=int(st.session_state["rifa_total"]),
            value=int(st.session_state["rifa_min"]),
            step=1
        )
        
        total_pagar = cant_boletos * st.session_state["rifa_precio"]
        st.write(f"💰 **Total a pagar:** RD$ {total_pagar:.2f}")
        
        st.subheader("📝 Datos del Comprador")
        nombre_cliente = st.text_input("Nombre Completo:")
        telefono_cliente = st.text_input("Número de Teléfono (WhatsApp):")
        comprobante_file = st.file_uploader("Sube tu comprobante de pago (Imagen/PDF):", type=["png", "jpg", "jpeg", "pdf"])
        
        btn_confirmar = st.button("✅ RESERVAR MIS BOLETOS")
        
        if btn_confirmar:
            if not nombre_cliente or not telefono_cliente or not comprobante_file:
                st.error("Por favor completa todos los campos.")
            else:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute(
                    "SELECT id, numero FROM boletos WHERE rifa_id = ? AND estado = 'disponible'",
                    (st.session_state["rifa_seleccionada"],)
                )
                disp = c.fetchall()
                
                if len(disp) < cant_boletos:
                    st.error("No hay suficientes boletos disponibles.")
                    conn.close()
                else:
                    asignados = random.sample(disp, cant_boletos)
                    os.makedirs("comprobantes", exist_ok=True)
                    
                    file_ext = comprobante_file.name.split(".")[-1]
                    filename = f"comprobantes/comp_{telefono_cliente}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file_ext}"
                    with open(filename, "wb") as f:
                        f.write(comprobante_file.getbuffer())
                        
                    num_asignados = []
                    fecha_ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    for b_id, b_num in asignados:
                        num_asignados.append(b_num)
                        c.execute(
                            """
                            UPDATE boletos 
                            SET estado = 'reservado', usuario_nombre = ?, usuario_telefono = ?, comprobante = ?, fecha_reserva = ?
                            WHERE id = ?
                            """,
                            (nombre_cliente, telefono_cliente, filename, fecha_ahora, b_id)
                        )
                    conn.commit()
                    conn.close()
                    
                    st.success("🎉 ¡Boletos asignados temporalmente!")
                    st.info(
                        "⏳ **Estado:** PENDIENTE DE CONFIRMACIÓN\n\n"
                        "Tus números ya están apartados a tu nombre. Nuestro equipo validará el comprobante de pago en un plazo máximo de **24 horas** para cambiar su estado a **CONFIRMADO**."
                    )

                    st.subheader("🎟️ Tus Números Asignados (Pendientes de Validación):")
                    cols_num = st.columns(min(len(num_asignados), 5))
                    for i, n in enumerate(num_asignados):
                        cols_num[i % 5].metric("Boleto", n, delta="Pendiente", delta_color="off")

# ==========================================
# SECCIÓN 2: VERIFICADOR DE BOLETOS
# ==========================================
elif seccion == "🔎 Verificador de boletos":
    st.header("🔎 Verificador de Boletos")
    tel_buscar = st.text_input("Ingresa tu número de teléfono para consultar tus números:")
    
    if st.button("Buscar mis boletos"):
        if tel_buscar:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute(
                """
                SELECT b.numero, b.estado, r.nombre 
                FROM boletos b 
                JOIN rifas r ON b.rifa_id = r.id 
                WHERE b.usuario_telefono = ?
                """, 
                (tel_buscar,)
            )
            mis_boletos = c.fetchall()
            conn.close()
            
            if mis_boletos:
                st.success(f"Se encontraron {len(mis_boletos)} boletos asociados a tu número:")
                for num, est, rifa_nom in mis_boletos:
                    c1, c2, c3 = st.columns(3)
                    c1.write(f"🎟️ **Boleto:** `{num}`")
                    c2.write(f"🏆 **Rifa:** {rifa_nom}")
                    
                    if est == "reservado":
                        c3.markdown("📌 **Estado:** ⏳ *PENDIENTE (En revisión max 24h)*")
                    elif est == "confirmado":
                        c3.markdown("📌 **Estado:** ✅ *CONFIRMADO Y VÁLIDO*")
                    else:
                        c3.markdown(f"📌 **Estado:** `{est.upper()}`")
                        
                    st.markdown("---")
            else:
                st.warning("No se encontraron boletos registrados con este número de teléfono.")
        else:
            st.error("Por favor ingresa un número de teléfono válido.")

# ==========================================
# SECCIÓN 3: PANEL DE ADMINISTRACIÓN
# ==========================================
elif seccion == "🔒 Administración":
    st.title("🔒 Panel Administrativo")
    
    if "admin_logged" not in st.session_state:
        st.session_state["admin_logged"] = False
        
    if not st.session_state["admin_logged"]:
        st.subheader("Iniciar Sesión")
        user_input = st.text_input("Usuario:")
        pass_input = st.text_input("Contraseña:", type="password")
        
        if st.button("Entrar"):
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT * FROM admin WHERE usuario = ? AND password = ?", (user_input, pass_input))
            res = c.fetchone()
            conn.close()
            
            if res:
                st.session_state["admin_logged"] = True
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")
    else:
        st.sidebar.button("Cerrar Sesión", on_click=lambda: st.session_state.update({"admin_logged": False}))
        
        tab1, tab2, tab3 = st.tabs(["➕ Crear Rifa", "📌 Revisar Reservas", "📊 Estadísticas"])
        
        # TAB 1: CREAR RIFA
        with tab1:
            st.subheader("Crear Nueva Rifa")
            with st.form("form_nueva_rifa"):
                nombre = st.text_input("Nombre de la Rifa:")
                categoria = st.selectbox("Categoría:", ["Tecnología", "Vehículos", "Dinero en Efectivo", "Electrodomésticos", "Otros"])
                precio = st.number_input("Precio por boleto (RD$):", min_value=1.0, value=100.0)
                min_boletos = st.number_input("Mínimo de boletos por compra:", min_value=1, value=1)
                total_boletos = st.number_input("Total de boletos de la rifa:", min_value=10, value=100)
                fecha_sorteo = st.date_input("Fecha del Sorteo:")
                imagen_file = st.file_uploader("Subir imagen promocional:", type=["png", "jpg", "jpeg"])
                
                submitted = st.form_submit_button("Crear Rifa")
                
                if submitted:
                    if nombre:
                        img_path = ""
                        if imagen_file:
                            os.makedirs("imagenes_rifas", exist_ok=True)
                            img_path = f"imagenes_rifas/{datetime.now().strftime('%Y%m%d%H%M%S')}_{imagen_file.name}"
                            with open(img_path, "wb") as f:
                                f.write(imagen_file.getbuffer())
                                
                        conn = sqlite3.connect(DB_FILE)
                        c = conn.cursor()
                        c.execute(
                            """
                            INSERT INTO rifas (nombre, categoria, precio, min_boletos, total_boletos, fecha_sorteo, imagen)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                            (nombre, categoria, precio, min_boletos, total_boletos, str(fecha_sorteo), img_path)
                        )
                        rifa_id = c.lastrowid
                        
                        # Crear los boletos individualmente
                        boletos_data = [(rifa_id, i+1) for i in range(total_boletos)]
                        c.executemany("INSERT INTO boletos (rifa_id, numero) VALUES (?, ?)", boletos_data)
                        
                        conn.commit()
                        conn.close()
                        
                        st.success(f"¡Rifa '{nombre}' creada con éxito con {total_boletos} boletos!")
                    else:
                        st.error("Ingresa el nombre de la rifa.")
                        
        # TAB 2: REVISAR RESERVAS
        with tab2:
            st.subheader("Aprobar o Rechazar Reservas")
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute(
                """
                SELECT b.id, b.numero, b.usuario_nombre, b.usuario_telefono, b.comprobante, b.fecha_reserva, r.nombre
                FROM boletos b
                JOIN rifas r ON b.rifa_id = r.id
                WHERE b.estado = 'reservado'
                """
            )
            reservas = c.fetchall()
            conn.close()
            
            if not reservas:
                st.info("No hay reservas pendientes de revisión.")
            else:
                for b_id, num, u_nom, u_tel, comp, f_res, r_nom in reservas:
                    with st.expander(f"🎟️ Boleto #{num} - {r_nom} ({u_nom})"):
                        st.write(f"👤 **Cliente:** {u_nom}")
                        st.write(f"📞 **Teléfono:** {u_tel}")
                        st.write(f"🕒 **Fecha de reserva:** {f_res}")
                        
                        if comp and os.path.exists(comp):
                            if comp.endswith(".pdf"):
                                st.write("📄 Comprobante PDF guardado.")
                            else:
                                st.image(comp, width=300)
                        
                        col_ap, col_re = st.columns(2)
                        if col_ap.button("✅ Aceptar Pago", key=f"ap_{b_id}"):
                            conn = sqlite3.connect(DB_FILE)
                            c = conn.cursor()
                            c.execute("UPDATE boletos SET estado = 'confirmado' WHERE id = ?", (b_id,))
                            conn.commit()
                            conn.close()
                            st.success(f"Boleto #{num} confirmado.")
                            st.rerun()
                            
                        if col_re.button("❌ Rechazar / Liberar", key=f"re_{b_id}"):
                            conn = sqlite3.connect(DB_FILE)
                            c = conn.cursor()
                            c.execute(
                                """
                                UPDATE boletos 
                                SET estado = 'disponible', usuario_nombre = NULL, usuario_telefono = NULL, comprobante = NULL, fecha_reserva = NULL
                                WHERE id = ?
                                """,
                                (b_id,)
                            )
                            conn.commit()
                            conn.close()
                            st.warning(f"Boleto #{num} liberado nuevamente.")
                            st.rerun()

        # TAB 3: ESTADÍSTICAS
        with tab3:
            st.subheader("Resumen de Ventas")
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            
            c.execute("SELECT COUNT(*) FROM boletos WHERE estado = 'confirmado'")
            total_confirmados = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM boletos WHERE estado = 'reservado'")
            total_reservados = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM boletos WHERE estado = 'disponible'")
            total_disponibles = c.fetchone()[0]
            
            c.execute(
                """
                SELECT SUM(r.precio) 
                FROM boletos b 
                JOIN rifas r ON b.rifa_id = r.id 
                WHERE b.estado = 'confirmado'
                """
            )
            recaudado = c.fetchone()[0] or 0.0
            
            conn.close()
            
            col_a, col_b, col_c, col_d = st.columns(4)
            col_a.metric("Confirmados", total_confirmados)
            col_b.metric("Reservados", total_reservados)
            col_c.metric("Disponibles", total_disponibles)
            col_d.metric("Total Recaudado", f"RD$ {recaudado:.2f}")
