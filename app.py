
st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    f"""
    <div style="text-align:center;margin-bottom:25px;">
        <p style="color:#F5C518;font-weight:bold;letter-spacing:1px;">
            EXPERIENCIA EXCLUSIVA
        </p>
        <h1 style="color:{text_color};font-size:34px;font-weight:800;">
            Premios extraordinarios garantizados
        </h1>
        <p style="color:#888888;font-size:16px;">
            Participa de forma sencilla y segura.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)


with st.expander(
    "❓ ¿CÓMO JUGAR? — 5 pasos simples",
    expanded=False
):
    st.markdown("""
    1. **Elige tu Rifa:** selecciona el premio que deseas.
    2. **Selecciona tus boletos:** elige un paquete o cantidad.
    3. **Completa tus datos:** nombre y WhatsApp.
    4. **Realiza el pago:** selecciona el banco y sube tu comprobante.
    5. **Espera la aprobación:** después de verificar el pago,
       el sistema asignará tus números automáticamente.
    """)


st.divider()


# =========================================================
# CATÁLOGO DE RIFAS ACTIVAS
# =========================================================

st.markdown(
    '<div id="rifas-activas"></div>',
    unsafe_allow_html=True
)

st.markdown(
    f"<h2 style='color:{text_color};'>🔥 Rifas Activas</h2>",
    unsafe_allow_html=True
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
        fecha
    FROM rifas
    WHERE COALESCE(activa,1)=1
""").fetchall()

descripciones = dict(conn.execute(
    "SELECT id, COALESCE(descripcion, '') FROM rifas"
).fetchall())

conn.close()

cols_rifas = st.columns(2)

for idx, r in enumerate(rifas):
    (
        r_id,
        r_nombre,
        r_categoria,
        r_precio,
        r_min,
        r_total,
        r_img,
        r_fecha
    ) = r

    porcentaje = obtener_porcentaje_rifa(r_id, r_total)

    with cols_rifas[idx % 2]:
        with st.container(border=True):

            if r_img and os.path.exists(r_img):
                st.image(r_img, use_container_width=True)

            st.markdown(f"### {r_nombre}")
            st.caption(
                f"Categoría: {r_categoria} | Sorteo: {r_fecha}"
            )
            if descripciones.get(r_id):
                st.write(descripciones[r_id])
            st.caption(f"Compra mínima: {r_min} boletos.")

            st.markdown(
                f"**Precio por boleto:** "
                f"<span style='color:#f5c518;font-size:18px;'>"
                f"RD$ {r_precio:,.2f}</span>",
                unsafe_allow_html=True
            )

            st.markdown(
                f"""
                <div class="progress-text">
                    <span>Progreso de venta</span>
                    <span>{porcentaje:.2f}%</span>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.progress(porcentaje / 100.0)

            if st.button(
                "🎮 JUGAR",
                key=f"btn_jugar_{r_id}",
                use_container_width=True
            ):
                st.session_state["selected_rifa"] = r
                st.session_state["active_dialog"] = "combos"
                st.rerun()
