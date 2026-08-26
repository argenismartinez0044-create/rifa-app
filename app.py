<!-- ARCHIVO COMPLETO: MODAL Y LÓGICA DE JUGADA DE BOLETOS -->

<!-- ESTILOS CSS -->
<style>
/* ==========================================================================
   1. ESTRUCTURA BASE Y OVERLAY DEL MODAL
   ========================================================================== */
.modal-overlay {
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background-color: rgba(5, 9, 20, 0.94);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 9999;
    padding: 15px;
    box-sizing: border-box;
}

.modal-content {
    background-color: #0b1120;
    border: 1px solid #1e293b;
    border-radius: 16px;
    padding: 30px 25px;
    max-width: 950px;
    width: 100%;
    color: #ffffff;
    box-shadow: 0 0 35px rgba(0, 0, 0, 0.9);
    position: relative;
    font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    box-sizing: border-box;
}

.close-btn {
    position: absolute;
    top: 15px; right: 20px;
    font-size: 28px;
    color: #94a3b8;
    cursor: pointer;
    transition: color 0.2s;
}
.close-btn:hover { color: #ffffff; }

/* ==========================================================================
   2. TEXTOS E INSTRUCCIONES
   ========================================================================== */
.modal-title {
    color: #38bdf8;
    font-family: monospace;
    font-size: 1.3rem;
    margin: 0 0 5px 0;
}

.modal-subtitle {
    color: #64748b;
    font-size: 0.85rem;
    margin: 0 0 25px 0;
}

.instruction-box {
    text-align: center;
    margin-bottom: 25px;
}

.main-instruction {
    font-size: 1.05rem;
    color: #f8fafc;
    margin: 0 0 5px 0;
    font-weight: 500;
}

.sub-instruction {
    font-size: 0.85rem;
    color: #64748b;
    margin: 0;
}

/* ==========================================================================
   3. GRILLA Y TARJETAS DE COMBOS (ESTILO NEÓN)
   ========================================================================== */
.combos-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 15px;
    margin-bottom: 25px;
}

.combo-card {
    background: #0f172a;
    border-radius: 12px;
    padding: 22px 10px 18px 10px;
    text-align: center;
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: space-between;
    outline: none;
    width: 100%;
    box-sizing: border-box;
}

.combo-card:hover {
    transform: translateY(-5px);
}

/* Colores y resplandores específicos de cada paquete */
.combo-card.popular { border: 1.5px solid #eab308; box-shadow: inset 0 0 10px rgba(234,179,8,0.1), 0 0 15px rgba(234,179,8,0.25); }
.combo-card.elite { border: 1.5px solid #06b6d4; box-shadow: inset 0 0 10px rgba(6,182,212,0.1), 0 0 15px rgba(6,182,212,0.25); }
.combo-card.campeon { border: 1.5px solid #3b82f6; box-shadow: inset 0 0 10px rgba(59,130,246,0.1), 0 0 15px rgba(59,130,246,0.25); }
.combo-card.leyenda { border: 1.5px solid #eab308; box-shadow: inset 0 0 10px rgba(234,179,8,0.1), 0 0 15px rgba(234,179,8,0.25); }
.combo-card.mitico { border: 1.5px solid #ef4444; box-shadow: inset 0 0 10px rgba(239,68,68,0.1), 0 0 15px rgba(239,68,68,0.25); }

/* Etiquetas superiores (Badges) */
.badge {
    position: absolute;
    top: -12px;
    font-size: 0.65rem;
    font-weight: bold;
    padding: 3px 8px;
    border-radius: 10px;
    letter-spacing: 0.5px;
}
.badge.yellow { background-color: #eab308; color: #000000; }
.badge.red { background-color: #ef4444; color: #ffffff; }

.card-icon { font-size: 1.8rem; margin-bottom: 5px; }
.card-title { font-size: 0.85rem; color: #94a3b8; margin: 0; letter-spacing: 1px; font-weight: 600; }

.card-number { font-size: 2.2rem; font-weight: 800; line-height: 1; margin: 6px 0; }
.combo-card.popular .card-number, .combo-card.leyenda .card-number { color: #facc15; }
.combo-card.elite .card-number { color: #22d3ee; }
.combo-card.campeon .card-number { color: #60a5fa; }
.combo-card.mitico .card-number { color: #f87171; }

.card-unit { font-size: 0.65rem; color: #64748b; letter-spacing: 1px; }
.card-price { font-size: 0.95rem; font-weight: bold; color: #ffffff; margin-top: 10px; }

/* Botón de Cantidad Personalizada */
.btn-custom-qty {
    width: 100%;
    background: transparent;
    border: 1px dashed #22c55e;
    color: #22c55e;
    padding: 14px;
    border-radius: 8px;
    font-weight: bold;
    font-size: 0.9rem;
    cursor: pointer;
    transition: background 0.2s;
    letter-spacing: 0.5px;
}
.btn-custom-qty:hover { background: rgba(34, 197, 94, 0.08); }
.min-qty-text { text-align: center; color: #475569; font-size: 0.75rem; margin-top: 6px; }

/* ==========================================================================
   4. FORMULARIO Y MÉTODOS DE PAGO (PASO 2)
   ========================================================================== */
.btn-back {
    background: none; border: none;
    color: #38bdf8; cursor: pointer;
    padding: 0; margin-bottom: 15px; font-size: 0.9rem;
}

.step-title { margin-top: 0; color: #f8fafc; font-size: 1.3rem; }

.form-group { margin-bottom: 15px; text-align: left; }
.form-group label { display: block; margin-bottom: 6px; color: #94a3b8; font-size: 0.85rem; }

.form-group input[type="text"],
.form-group input[type="tel"],
.form-group input[type="number"] {
    width: 100%;
    padding: 12px;
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 6px;
    color: #ffffff;
    box-sizing: border-box;
    font-size: 0.95rem;
}
.form-group input:focus {
    outline: none;
    border-color: #38bdf8;
}

.total-box {
    background: #1e293b;
    padding: 12px 15px;
    border-radius: 6px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
}
.total-box span { color: #cbd5e1; font-size: 0.9rem; }
.total-box strong { color: #22c55e; font-size: 1.25rem; }

/* Grilla de Métodos de Pago */
.payment-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
    gap: 10px;
}

.payment-btn {
    background: #0f172a;
    border: 1px solid #334155;
    color: #94a3b8;
    padding: 12px 8px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.85rem;
    font-weight: 500;
    transition: all 0.2s;
}

.payment-btn.active {
    border-color: #38bdf8;
    color: #ffffff;
    background: rgba(56, 189, 248, 0.15);
    box-shadow: 0 0 10px rgba(56, 189, 248, 0.2);
}

.btn-submit-final {
    width: 100%;
    background: #22c55e;
    color: #000000;
    border: none;
    padding: 14px;
    border-radius: 8px;
    font-weight: bold;
    font-size: 1rem;
    cursor: pointer;
    margin-top: 15px;
    transition: background 0.2s;
}
.btn-submit-final:hover { background: #16a34a; }
</style>


<!-- ESTRUCTURA HTML DEL MODAL -->
<div id="modalJugar" class="modal-overlay" style="display: none;">
    <div class="modal-content">
        <!-- Botón para cerrar -->
        <span class="close-btn" onclick="cerrarModal()">&times;</span>

        <!-- ==================== PASO 1: SELECCIÓN DE COMBOS ==================== -->
        <div id="paso1-combos" class="modal-step">
            <h2 class="modal-title">S 17 PRO MAX POR 15 PESITOS FLASH#25</h2>
            <p class="modal-subtitle">Elige tu paquete de números</p>

            <div class="instruction-box">
                <p class="main-instruction">Selecciona un paquete o elige cantidad personalizada</p>
                <p class="sub-instruction">A mayor cantidad, más oportunidades de ganar</p>
            </div>

            <!-- TARJETAS DE PAQUETES DE COMBOS -->
            <div class="combos-container">
                <!-- 1. PRO (POPULAR) -->
                <button type="button" class="combo-card popular" onclick="seleccionarCombo(10)">
                    <span class="badge yellow">★ POPULAR</span>
                    <div class="card-icon">🚀</div>
                    <h3 class="card-title">PRO</h3>
                    <div class="card-number">10</div>
                    <span class="card-unit">NÚMEROS</span>
                    <div class="card-price">RD$ 150</div>
                </button>

                <!-- 2. ELITE -->
                <button type="button" class="combo-card elite" onclick="seleccionarCombo(15)">
                    <div class="card-icon">🏆</div>
                    <h3 class="card-title">ELITE</h3>
                    <div class="card-number">15</div>
                    <span class="card-unit">NÚMEROS</span>
                    <div class="card-price">RD$ 225</div>
                </button>

                <!-- 3. CAMPEÓN -->
                <button type="button" class="combo-card campeon" onclick="seleccionarCombo(25)">
                    <div class="card-icon">👑</div>
                    <h3 class="card-title">CAMPEÓN</h3>
                    <div class="card-number">25</div>
                    <span class="card-unit">NÚMEROS</span>
                    <div class="card-price">RD$ 375</div>
                </button>

                <!-- 4. LEYENDA (VIP) -->
                <button type="button" class="combo-card leyenda" onclick="seleccionarCombo(50)">
                    <span class="badge yellow">★ VIP</span>
                    <div class="card-icon">⚡</div>
                    <h3 class="card-title">LEYENDA</h3>
                    <div class="card-number">50</div>
                    <span class="card-unit">NÚMEROS</span>
                    <div class="card-price">RD$ 750</div>
                </button>

                <!-- 5. MÍTICO (MÁXIMO) -->
                <button type="button" class="combo-card mitico" onclick="seleccionarCombo(100)">
                    <span class="badge red">🔥 MÁXIMO</span>
                    <div class="card-icon">🦅</div>
                    <h3 class="card-title">MÍTICO</h3>
                    <div class="card-number">100</div>
                    <span class="card-unit">NÚMEROS</span>
                    <div class="card-price">RD$ 1,500</div>
                </button>
            </div>

            <!-- BOTÓN CANTIDAD PERSONALIZADA -->
            <div class="custom-qty-container">
                <button type="button" class="btn-custom-qty" onclick="irACantidadPersonalizada()">
                    ⚙ ELEGIR CANTIDAD PERSONALIZADA
                </button>
                <p class="min-qty-text">Mínimo 10 números</p>
            </div>
        </div>

        <!-- ==================== PASO 2: FORMULARIO Y CANTIDAD ==================== -->
        <div id="paso2-formulario" class="modal-step" style="display: none;">
            <button type="button" class="btn-back" onclick="volverAPaso1()">← Cambiar paquete</button>

            <h2 class="step-title">Finaliza tu Jugada</h2>

            <form id="formJugada" method="POST" action="/procesar-jugada/" onsubmit="procesarFormulario(event)">
                <!-- En Django se incluye {% csrf_token %} en esta línea si aplica -->

                <div class="form-group">
                    <label for="inputCantidad">Cantidad de Números / Boletos:</label>
                    <input type="number" id="inputCantidad" name="cantidad" min="10" value="10" oninput="actualizarPrecioTotal()" required>
                </div>

                <div class="total-box">
                    <span>Total a pagar:</span>
                    <strong id="displayTotal">RD$ 150</strong>
                </div>

                <div class="form-group">
                    <label for="nombre">Nombre Completo:</label>
                    <input type="text" id="nombre" name="nombre" placeholder="Tu nombre" required>
                </div>

                <div class="form-group">
                    <label for="telefono">Teléfono / WhatsApp:</label>
                    <input type="tel" id="telefono" name="telefono" placeholder="809-000-0000" required>
                </div>

                <!-- MÉTODOS DE PAGO DISPONIBLES (BHD y Santa Cruz retirados) -->
                <div class="form-group">
                    <label>Selecciona Método de Pago:</label>
                    <input type="hidden" id="metodoPagoSeleccionado" name="metodo_pago" value="banreservas">
                    
                    <div class="payment-grid">
                        <button type="button" class="payment-btn active" onclick="seleccionarMetodo(event, 'banreservas')">
                            Banreservas
                        </button>
                        <button type="button" class="payment-btn" onclick="seleccionarMetodo(event, 'popular')">
                            Banco Popular
                        </button>
                        <button type="button" class="payment-btn" onclick="seleccionarMetodo(event, 'caribe_express')">
                            Caribe Express / Paga Todo
                        </button>
                    </div>
                </div>

                <button type="submit" class="btn-submit-final">CONFIRMAR Y COMPLETAR JUGADA</button>
            </form>
        </div>
    </div>
</div>


<!-- LÓGICA JAVASCRIPT -->
<script>
// Precio unitario por cada boleto
const PRECIO_UNITARIO = 15; // RD$15 por número

// Función para abrir el modal al presionar "Jugar"
function abrirModalJugar() {
    document.getElementById('modalJugar').style.display = 'flex';
    document.getElementById('paso1-combos').style.display = 'block';
    document.getElementById('paso2-formulario').style.display = 'none';
}

// Función para cerrar el modal
function cerrarModal() {
    document.getElementById('modalJugar').style.display = 'none';
}

// Cuando se selecciona una tarjeta de combo en el Paso 1
function seleccionarCombo(cantidad) {
    const inputCantidad = document.getElementById('inputCantidad');
    inputCantidad.value = cantidad;
    actualizarPrecioTotal();
    mostrarPaso2();
}

// Cuando se presiona "Elegir cantidad personalizada"
function irACantidadPersonalizada() {
    const inputCantidad = document.getElementById('inputCantidad');
    inputCantidad.value = 10; // Valor por defecto
    actualizarPrecioTotal();
    mostrarPaso2();
}

// Cambio de pantalla al Paso 2
function mostrarPaso2() {
    document.getElementById('paso1-combos').style.display = 'none';
    document.getElementById('paso2-formulario').style.display = 'block';
}

// Regresar al Paso 1
function volverAPaso1() {
    document.getElementById('paso2-formulario').style.display = 'none';
    document.getElementById('paso1-combos').style.display = 'block';
}

// Actualización automática del precio (Boletos x RD$15)
function actualizarPrecioTotal() {
    const inputCantidad = document.getElementById('inputCantidad');
    let cantidad = parseInt(inputCantidad.value) || 0;
    
    // Garantizar que la cantidad mínima sea 10
    if (cantidad < 10 && cantidad !== 0) {
        cantidad = 10;
    }
    
    const total = cantidad * PRECIO_UNITARIO;
    document.getElementById('displayTotal').innerText = `RD$ ${total.toLocaleString()}`;
}

// Selección de método de pago (resuelve el error de cierre inesperado)
function seleccionarMetodo(event, metodo) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }

    // Guardar el valor en el campo oculto del formulario
    document.getElementById('metodoPagoSeleccionado').value = metodo;

    // Cambiar visualmente el estado activo del botón
    const botones = document.querySelectorAll('.payment-btn');
    botones.forEach(btn => btn.classList.remove('active'));
    
    event.currentTarget.classList.add('active');
}

// Validación antes del envío final
function procesarFormulario(event) {
    const cantidad = parseInt(document.getElementById('inputCantidad').value);
    if (cantidad < 10) {
        event.preventDefault();
        alert("La cantidad mínima para jugar es de 10 boletos.");
        return false;
    }
    // El formulario se enviará normalmente a Python a la ruta /procesar-jugada/
}
</script>
