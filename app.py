import os
import sqlite3
import datetime
import hashlib
import streamlit as st

# Configuración de carpetas necesarias
os.makedirs("comprobantes", exist_ok=True)
os.makedirs("imagenes_rifas", exist_ok=True)

# -----------------------------------------------------------------------------
# FUNCIONES AUXILIARES DE BASE DE DATOS Y ADMINISTRACIÓN
# -----------------------------------------------------------------------------

def inicializar_db_administracion():
    """Asegura que la tabla de rifas tenga los campos requeridos para gestión dinámica."""
    conn = sqlite3.connect("rifas.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS rifas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            precio_boleto REAL NOT NULL,
            total_boletos INTEGER NOT NULL,
            imagen_url TEXT,
            estado TEXT DEFAULT 'activa'
        )
    """)
    conn.commit()
    conn.close()

def guardar_imagen_subida(archivo_imagen):
    """Guarda la imagen subida en disco y retorna la ruta."""
    if archivo_imagen is not None:
        path_img = f"imagenes_rifas/{int(datetime.datetime.now().timestamp())}_{archivo_imagen.name}"
        with open(path_img, "wb") as f:
            f.write(archivo_imagen.getbuffer())
        return path_img
    return None

def panel_administrador():
    """Panel de control para el dueño del sistema: Gestión de Rifas y Validaciones."""
    st.title("⚙️ Panel de Administración")
    
    tab_rifas, tab_validaciones = st.tabs(["🎟️ Gestión de Rifas (Opciones 2 y 3)", "💳 Validación de Pagos"])
    
    # -------------------------------------------------------------------------
    # TAB 1: OPCIONES 2 Y 3 (CREAR Y GESTIONAR RIFAS / SUBIR FOTOS)
    # -------------------------------------------------------------------------
    with tab_rifas:
        st.subheader("➕ Crear Nueva Rifa")
        
        with st.form("form_nueva_rifa", clear_on_submit=True):
            nombre_rifa = st.text_input("Nombre / Título de la Rifa")
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                precio_boleto = st.number_input("Precio por Boleto (RD$)", min_value=1.0, value=100.0, step=10.0)
            with col_p2:
                total_boletos = st.number_input("Cantidad Total de Boletos", min_value=1, value=100, step=10)
            
            imagen_rifa = st.file_uploader("Foto del Premio / Rifa", type=["jpg", "jpeg", "png", "webp"])
            
            btn_crear = st.form_submit_button("🚀 Publicar Nueva Rifa", use_container_width=True)
            
            if btn_crear:
                if not nombre_rifa.strip():
                    st.error("⚠️ El nombre de la rifa no puede estar vacío.")
                else:
                    ruta_img = guardar_imagen_subida(imagen_rifa) if imagen_rifa else ""
                    conn = sqlite3.connect("rifas.db")
                    c = conn.cursor()
                    c.execute(
                        "INSERT INTO rifas (nombre, precio_boleto, total_boletos, imagen_url, estado) VALUES (?, ?, ?, ?, 'activa')",
                        (nombre_rifa.strip(), precio_boleto, total_boletos, ruta_img)
                    )
                    rifa_id = c.lastrowid
                    
                    # Generar los boletos para esta nueva rifa
                    for num in range(1, total_boletos + 1):
                        c.execute(
                            "INSERT INTO boletos (rifa_id, numero, estado) VALUES (?, ?, 'disponible')",
                            (rifa_id, num)
                        )
                    conn.commit()
                    conn.close()
                    st.success(f"✅ ¡Rifa '{nombre_rifa}' creada exitosamente con {total_boletos} boletos!")
                    st.rerun()

        st.markdown("<hr>", unsafe_allow_html=True)
        st.subheader("📋 Rifas Registradas")
        
        conn = sqlite3.connect("rifas.db")
        c = conn.cursor()
        c.execute("SELECT id, nombre, precio_boleto, total_boletos, imagen_url, estado FROM rifas ORDER BY id DESC")
        listado_rifas = c.fetchall()
        conn.close()
        
        if not listado_rifas:
            st.info("No hay rifas creadas en el sistema.")
        else:
            for r_id, r_nom, r_precio, r_tot, r_img, r_est in listado_rifas:
                with st.expander(f"📌 {r_nom.upper()} — Estado: {r_est.upper()}"):
                    col_det1, col_det2 = st.columns([1, 2])
                    with col_det1:
                        if r_img and os.path.exists(r_img):
                            st.image(r_img, use_column_width=True)
                        else:
                            st.caption("🖼️ Sin imagen asignada")
                    
                    with col_det2:
                        st.write(f"**Precio por boleto:** RD$ {r_precio:,.2f}")
                        st.write(f"**Total boletos:** {r_tot}")
                        
                        nuevo_estado = st.selectbox(
                            "Estado de la rifa",
                            ["activa", "pausada", "finalizada"],
                            index=["activa", "pausada", "finalizada"].index(r_est),
                            key=f"estado_{r_id}"
                        )
                        
                        nueva_foto = st.file_uploader("Actualizar foto", type=["jpg", "jpeg", "png", "webp"], key=f"foto_{r_id}")
                        
                        if st.button("💾 Guardar Cambios", key=f"btn_save_{r_id}"):
                            conn = sqlite3.connect("rifas.db")
                            c = conn.cursor()
                            if nueva_foto:
                                ruta_nueva = guardar_imagen_subida(nueva_foto)
                                c.execute("UPDATE rifas SET estado = ?, imagen_url = ? WHERE id = ?", (nuevo_estado, ruta_nueva, r_id))
                            else:
                                c.execute("UPDATE rifas SET estado = ? WHERE id = ?", (nuevo_estado, r_id))
                            conn.commit()
                            conn.close()
                            st.success("✅ Rifa actualizada correctamente.")
                            st.rerun()

    # -------------------------------------------------------------------------
    # TAB 2: VALIDACIÓN Y APROBACIÓN DE PAGOS
    # -------------------------------------------------------------------------
    with tab_validaciones:
        st.subheader("🔍 Comprobantes por Aprobar")
        
        conn = sqlite3.connect("rifas.db")
        c = conn.cursor()
        c.execute("""
            SELECT b.rifa_id, r.nombre, b.usuario_nombre, b.usuario_telefono, b.metodo_pago, b.comprobante, COUNT(b.id)
            FROM boletos b
            JOIN rifas r ON b.rifa_id = r.id
            WHERE b.estado = 'reservado'
            GROUP BY b.rifa_id, b.usuario_nombre, b.usuario_telefono, b.comprobante
        """)
        reservas_pendientes = c.fetchall()
        conn.close()

        if not reservas_pendientes:
            st.success("🎉 No hay pagos pendientes de aprobación.")
        else:
            for r_id, r_nombre, u_nom, u_tel, m_pago, comp_path, cant_boletos in reservas_pendientes:
                with st.container():
                    st.markdown(f"### Cliente: {u_nom} ({u_tel})")
                    st.write(f"**Rifa:** {r_nombre} | **Boletos a confirmar:** {cant_boletos} | **Método:** {m_pago}")
                    
                    if comp_path and os.path.exists(comp_path):
                        st.image(comp_path, width=300)
                    else:
                        st.warning("No se encontró el archivo del comprobante.")

                    col_ap1, col_ap2 = st.columns(2)
                    with col_ap1:
                        if st.button("✅ Aprobar Pago", key=f"ap_{u_tel}_{comp_path}"):
                            conn = sqlite3.connect("rifas.db")
                            c = conn.cursor()
                            c.execute("""
                                UPDATE boletos
                                SET estado = 'pagado'
                                WHERE usuario_telefono = ? AND comprobante = ? AND estado = 'reservado'
                            """, (u_tel, comp_path))
                            conn.commit()
                            conn.close()
                            st.success("Pago APROBADO correctamente.")
                            st.rerun()

                    with col_ap2:
                        if st.button("❌ Rechazar / Liberar", key=f"rec_{u_tel}_{comp_path}"):
                            conn = sqlite3.connect("rifas.db")
                            c = conn.cursor()
                            c.execute("""
                                UPDATE boletos
                                SET estado = 'disponible', usuario_nombre = NULL, usuario_telefono = NULL,
                                    metodo_pago = NULL, comprobante = NULL, comprobante_hash = NULL, fecha_reserva = NULL
                                WHERE usuario_telefono = ? AND comprobante = ? AND estado = 'reservado'
                            """, (u_tel, comp_path))
                            conn.commit()
                            conn.close()
                            st.warning("Reserva rechazada y boletos liberados.")
                            st.rerun()
                    st.markdown("<hr>", unsafe_allow_html=True)


# Inicializar la tabla de administración al arrancar
inicializar_db_administracion()

# -----------------------------------------------------------------------------
# FLUJO DE COMPRA DEL CLIENTE (MANTENIDO INTACTO)
# -----------------------------------------------------------------------------

# Renderizado según la etapa del paso de compra
paso = st.session_state.get("paso_compra", 1)

if paso == 2:
    # Lógica previa de procesamiento e inserción
    path_comp = f"comprobantes/{comp_hash[:10]}_{comprobante_file.name}"
    with open(path_comp, "wb") as f:
        f.write(bytes_comprobante)

    ahora = datetime.datetime.now()
    numeros_asignados = []

    for b_id, b_num in asignados:
        c.execute(
            """
            UPDATE boletos
            SET estado = 'reservado',
                usuario_nombre = ?,
                usuario_telefono = ?,
                metodo_pago = ?,
                comprobante = ?,
                comprobante_hash = ?,
                fecha_reserva = ?
            WHERE id = ?
            """,
            (
                nombre_cliente.strip(),
                telefono_cliente.strip(),
                st.session_state["banco_pago"],
                path_comp,
                comp_hash,
                ahora,
                b_id,
            ),
        )
        numeros_asignados.append(b_num)

    conn.commit()
    conn.close()

    # Guardar datos en session_state para pantalla final
    st.session_state["resumen_compra"] = {
        "nombre": nombre_cliente.strip(),
        "telefono": telefono_cliente.strip(),
        "rifa": nombre,
        "boletos": numeros_asignados,
        "monto": monto_total,
        "banco": st.session_state["banco_pago"],
    }
    st.session_state["paso_compra"] = 3
    st.rerun()
else:
    conn.close()
    st.error(
        f"❌ No hay suficientes boletos disponibles. Solo quedan {len(disp)}."
    )

elif paso == 3:
    resumen = st.session_state.get("resumen_compra", {})
    st.balloons()

    st.markdown(
        f"""
        <div style="background: #090d16; border: 2px solid #22c55e; border-radius: 16px; padding: 25px; text-align: center; max-width: 650px; margin: 0 auto;">
            <h2 style="color: #22c55e; margin-top: 0;">🎉 ¡RESERVA REGISTRADA CON ÉXITO!</h2>
            <p style="color: #cbd5e1; font-size: 1rem;">Gracias <strong>{resumen.get('nombre', '')}</strong>, tu comprobante ha sido subido correctamente.</p>
            <hr style="border-color: #1e293b; margin: 15px 0;">
            <p style="color: #94a3b8; font-size: 0.9rem; margin-bottom: 5px;">TU SELECCIÓN PARA <strong>{resumen.get('rifa', '').upper()}</strong></p>
            <div style="background: #0f172a; border-radius: 10px; padding: 15px; margin: 10px 0;">
                <span style="color: #38bdf8; font-size: 1.4rem; font-weight: bold;">{len(resumen.get('boletos', []))} BOLETOS RESERVADOS</span>
                <div style="color: #f59e0b; font-weight: bold; margin-top: 5px;">Monto: RD$ {resumen.get('monto', 0):,.2f} ({resumen.get('banco', '')})</div>
            </div>
            <div style="margin: 15px 0;">
                <span style="color: #94a3b8; font-size: 0.85rem;">ESTADO DE TUS BOLETOS:</span><br>
                <div class="badge-pending" style="margin-top: 5px; font-size: 0.85rem; padding: 6px 14px;">PENDIENTE A CONFIRMAR</div>
            </div>
            <p style="color: #64748b; font-size: 0.8rem;">Nuestro equipo verificará tu transferencia. Puedes consultar el estado en cualquier momento con tu teléfono en el <strong>Verificador de Boletos</strong>.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        # Botón para notificar vía WhatsApp
        msg_wa = (
            f"¡Hola! Acabo de realizar una reserva en Sirio Rifas RD.%0A"
            f"👤 *Nombre:* {resumen.get('nombre', '')}%0A"
            f"📱 *Teléfono:* {resumen.get('telefono', '')}%0A"
            f"🎟️ *Rifa:* {resumen.get('rifa', '')}%0A"
            f"🔢 *Cantidad de boletos:* {len(resumen.get('boletos', []))}%0A"
            f"💳 *Monto:* RD$ {resumen.get('monto', 0):,.2f} ({resumen.get('banco', '')})"
        )
        st.markdown(
            f"""
            <a href="https://wa.me/1{WHATSAPP_NUMERO}?text={msg_wa}" target="_blank" style="text-decoration: none;">
                <div style="background: #22c55e; color: white; text-align: center; padding: 12px; border-radius: 8px; font-weight: bold;">
                    📲 NOTIFICAR POR WHATSAPP
                </div>
            </a>
            """,
            unsafe_allow_html=True,
        )

    with col_b2:
        if st.button("🔄 VOLVER AL INICIO", use_container_width=True):
            st.session_state["paso_compra"] = 0
            st.session_state["vista_actual"] = "rifas"
            st.rerun()
