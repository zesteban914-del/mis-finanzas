// Pantallas de inicio de sesión y de registro (registro en dos pasos según el tipo de cuenta).
import { api } from "../api.js";
import { escapar } from "../formato.js";
import { icono } from "../iconos.js";
import { mostrarPolitica } from "../legal.js";
import { guardarSesion } from "../sesion.js";

const BENEFICIOS = [
  ["tendencia", "Panel con tu saldo, gastos por categoría y tendencia de 6 meses"],
  ["objetivo", "Presupuestos con alertas cuando te pasas del límite"],
  ["tienda", "Para tu hogar o tu negocio: cajas, equipo y reportes para el contador"],
  ["candado", "Tus datos son privados: solo tú ves tus movimientos"],
];

const TIPOS = {
  PERSONAL: {
    icono: "persona",
    titulo: "Uso personal",
    texto: "Controla tus gastos, ahorra para tus metas y sal de deudas.",
    incluye: ["Presupuestos y alertas", "Metas de ahorro", "Deudas y préstamos", "Pagos recurrentes"],
  },
  NEGOCIO: {
    icono: "tienda",
    titulo: "Negocio",
    texto: "Para tiendas, emprendimientos y profesionales independientes.",
    incluye: ["Cajas: efectivo, banco, Nequi", "Equipo con empleado y contador", "Cuentas por cobrar y pagar", "Comprobantes y Excel"],
  },
};

let opcionesRegistro = null;

/**
 * modo: "ingresar" | "registro". `alEntrar` se llama cuando la sesión queda iniciada.
 * `aviso`: mensaje opcional (por ejemplo, "tu sesión expiró").
 */
export async function renderizarAutenticacion(contenedor, { modo, alEntrar, aviso = "" }) {
  const esRegistro = modo === "registro";
  document.title = `${esRegistro ? "Crear cuenta" : "Iniciar sesión"} · Mis Finanzas`;
  contenedor.innerHTML = `
    ${panelDeMarca()}
    <section class="autenticacion-panel"><div class="autenticacion-contenido"></div></section>`;
  const zona = contenedor.querySelector(".autenticacion-contenido");

  if (!esRegistro) {
    pintarIngreso(zona, alEntrar, aviso);
    return;
  }
  if (!opcionesRegistro) opcionesRegistro = await api.auth.opciones().catch(() => ({ objetivos: {}, sectores: {} }));
  pintarEleccionDeTipo(zona, (tipo) => pintarRegistro(zona, tipo, alEntrar));
}

function panelDeMarca() {
  return `
    <section class="autenticacion-marca" aria-hidden="true">
      <div class="marca">
        <span class="marca-logo">${icono("tendencia")}</span>
        <strong>Mis Finanzas</strong>
      </div>
      <div class="autenticacion-mensaje">
        <h2>Toma el control de tu dinero, mes a mes.</h2>
        <p>Para personas y negocios: registra ingresos y gastos en segundos y descubre a dónde se va tu plata.</p>
        <ul>${BENEFICIOS.map(([i, texto]) => `<li><span>${icono(i)}</span>${texto}</li>`).join("")}</ul>
      </div>
      <div class="autenticacion-muestra">
        <span>Saldo del mes</span>
        <strong>$ 3.060.000</strong>
        <div class="autenticacion-barras">${[38, 52, 44, 70, 58, 82].map((h) => `<i style="height:${h}%"></i>`).join("")}</div>
      </div>
    </section>`;
}

const marcaMovil = `
  <div class="marca autenticacion-marca-movil">
    <span class="marca-logo">${icono("tendencia")}</span>
    <strong>Mis Finanzas</strong>
  </div>`;

/* Inicio de sesión ------------------------------------------------------------ */
function pintarIngreso(zona, alEntrar, aviso) {
  zona.innerHTML = `
    <form class="autenticacion-formulario" novalidate>
      ${marcaMovil}
      <header>
        <h1>Bienvenido de nuevo</h1>
        <p>Ingresa para ver tus finanzas.</p>
      </header>
      ${aviso ? `<p class="alerta alerta--aviso" role="status">${icono("alerta")}<span>${escapar(aviso)}</span></p>` : ""}
      <p class="dialogo-error autenticacion-error" role="alert" hidden></p>
      ${campoEmail()}
      ${campoContrasena("current-password", "Tu contraseña")}
      <button type="submit" class="boton boton--primario boton--ancho">Iniciar sesión</button>
      <p class="autenticacion-cambio">¿No tienes cuenta? <a class="enlace" href="#/registro">Créala gratis</a></p>
    </form>`;

  manejarFormulario(zona, async (datos) => {
    const email = datos.get("email").trim();
    const contrasena = datos.get("contrasena");
    if (!email || !contrasena) throw new Error("Escribe tu correo y tu contraseña");
    const sesion = await api.auth.iniciarSesion(email, contrasena);
    guardarSesion(sesion.access_token, sesion.usuario);
    alEntrar(sesion.usuario, false);
  });
}

/* Registro, paso 1: tipo de cuenta -------------------------------------------- */
function pintarEleccionDeTipo(zona, alElegir) {
  zona.innerHTML = `
    <div class="autenticacion-formulario">
      ${marcaMovil}
      <header>
        <span class="paso">Paso 1 de 2</span>
        <h1>¿Para qué usarás Mis Finanzas?</h1>
        <p>Así te pedimos solo los datos necesarios y activamos las funciones que te sirven.</p>
      </header>
      <div class="tipos-cuenta">
        ${Object.entries(TIPOS)
          .map(
            ([tipo, t]) => `
          <button type="button" class="tipo-cuenta" data-tipo="${tipo}">
            <span class="tipo-cuenta-icono">${icono(t.icono)}</span>
            <span class="tipo-cuenta-texto">
              <strong>${t.titulo}</strong>
              <span>${t.texto}</span>
              <span class="tipo-cuenta-incluye">${t.incluye.map((x) => `<span>${icono("check")}${x}</span>`).join("")}</span>
            </span>
            ${icono("derecha", "tipo-cuenta-flecha")}
          </button>`
          )
          .join("")}
      </div>
      <p class="autenticacion-cambio">¿Ya tienes cuenta? <a class="enlace" href="#/ingresar">Inicia sesión</a></p>
    </div>`;
  zona.querySelectorAll("[data-tipo]").forEach((boton) =>
    boton.addEventListener("click", () => alElegir(boton.dataset.tipo))
  );
  zona.querySelector("[data-tipo]").focus();
}

/* Registro, paso 2: datos según el tipo ---------------------------------------- */
function pintarRegistro(zona, tipo, alEntrar) {
  const esNegocio = tipo === "NEGOCIO";
  const opciones = (mapa, vacio) =>
    `<option value="">${vacio}</option>` +
    Object.entries(mapa).map(([valor, texto]) => `<option value="${valor}">${escapar(texto)}</option>`).join("");

  zona.innerHTML = `
    <form class="autenticacion-formulario" novalidate>
      ${marcaMovil}
      <header>
        <button type="button" class="enlace enlace--volver" data-volver>${icono("izquierda")}Cambiar tipo de cuenta</button>
        <span class="paso">Paso 2 de 2 · ${TIPOS[tipo].titulo}</span>
        <h1>${esNegocio ? "Datos de tu negocio" : "Crea tu cuenta"}</h1>
      </header>
      <p class="dialogo-error autenticacion-error" role="alert" hidden></p>

      <label class="campo">
        <span class="campo-etiqueta">${esNegocio ? "Nombre del negocio" : "Tu nombre"}</span>
        <input class="entrada" name="nombre" maxlength="80" autocomplete="${esNegocio ? "organization" : "name"}"
          placeholder="${esNegocio ? "Ej. Panadería La Espiga" : "Ej. Ana Martínez"}">
      </label>
      ${
        esNegocio
          ? `<div class="campos-fila">
               <label class="campo">
                 <span class="campo-etiqueta">Sector</span>
                 <select class="entrada" name="sector">${opciones(opcionesRegistro.sectores, "Elige uno")}</select>
               </label>
               <label class="campo">
                 <span class="campo-etiqueta">NIT <span class="texto-tenue">(opcional)</span></span>
                 <input class="entrada" name="nit" maxlength="20" inputmode="numeric" placeholder="900123456-7">
               </label>
             </div>
             <label class="campo">
               <span class="campo-etiqueta">Persona responsable <span class="texto-tenue">(opcional)</span></span>
               <input class="entrada" name="responsable" maxlength="80" autocomplete="name" placeholder="Quién administra la cuenta">
             </label>`
          : `<label class="campo">
               <span class="campo-etiqueta">¿Cuál es tu objetivo principal? <span class="texto-tenue">(opcional)</span></span>
               <select class="entrada" name="objetivo">${opciones(opcionesRegistro.objetivos, "Elige uno")}</select>
             </label>`
      }
      ${campoEmail()}
      ${campoContrasena("new-password", "Mínimo 8 caracteres, con letras y números")}
      <label class="casilla">
        <input type="checkbox" name="categorias" checked>
        <span>Crear categorías sugeridas para ${esNegocio ? "un negocio (Ventas, Insumos, Nómina…)" : "uso personal (Salario, Comida, Transporte…)"}</span>
      </label>
      <label class="casilla">
        <input type="checkbox" name="terminos">
        <span>Acepto los <button type="button" class="enlace enlace--en-linea" data-politica>términos y la política de tratamiento de datos</button></span>
      </label>
      <button type="submit" class="boton boton--primario boton--ancho">Crear cuenta</button>
      <p class="autenticacion-cambio">¿Ya tienes cuenta? <a class="enlace" href="#/ingresar">Inicia sesión</a></p>
    </form>`;

  zona.querySelector("[data-volver]").addEventListener("click", () =>
    pintarEleccionDeTipo(zona, (t) => pintarRegistro(zona, t, alEntrar))
  );
  zona.querySelector("[data-politica]").addEventListener("click", mostrarPolitica);

  manejarFormulario(zona, async (datos) => {
    if (!datos.get("nombre").trim() || !datos.get("email").trim() || !datos.get("contrasena")) {
      throw new Error("Completa nombre, correo y contraseña");
    }
    const cuerpo = {
      tipo_cuenta: tipo,
      nombre: datos.get("nombre").trim(),
      email: datos.get("email").trim(),
      contrasena: datos.get("contrasena"),
      acepta_terminos: datos.get("terminos") === "on",
      crear_categorias_iniciales: datos.get("categorias") === "on",
      ...(esNegocio
        ? { sector: datos.get("sector") || null, nit: datos.get("nit") || null, responsable: datos.get("responsable") || null }
        : { objetivo: datos.get("objetivo") || null }),
    };
    const sesion = await api.auth.registrarse(cuerpo);
    guardarSesion(sesion.access_token, sesion.usuario);
    alEntrar(sesion.usuario, true);
  });
}

/* Piezas compartidas ------------------------------------------------------------ */
const campoEmail = () => `
  <label class="campo">
    <span class="campo-etiqueta">Correo electrónico</span>
    <input class="entrada" name="email" type="email" autocomplete="email" maxlength="120" placeholder="tu@correo.com">
  </label>`;

const campoContrasena = (autocompletar, ayuda) => `
  <label class="campo">
    <span class="campo-etiqueta">Contraseña</span>
    <span class="entrada-con-boton">
      <input class="entrada" name="contrasena" type="password" maxlength="128" autocomplete="${autocompletar}" placeholder="${ayuda}">
      <button type="button" class="boton-icono" data-alternar-contrasena aria-label="Mostrar contraseña" title="Mostrar contraseña">${icono("ojo")}</button>
    </span>
  </label>`;

function manejarFormulario(zona, enviar) {
  const formulario = zona.querySelector("form");
  const cajaError = zona.querySelector(".autenticacion-error");
  const botonEnviar = formulario.querySelector('[type="submit"]');
  const campoClave = formulario.elements.contrasena;

  zona.querySelector("[data-alternar-contrasena]").addEventListener("click", (evento) => {
    const visible = campoClave.type === "text";
    campoClave.type = visible ? "password" : "text";
    evento.currentTarget.setAttribute("aria-label", visible ? "Mostrar contraseña" : "Ocultar contraseña");
  });

  formulario.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    cajaError.hidden = true;
    botonEnviar.disabled = true;
    botonEnviar.classList.add("cargando");
    try {
      await enviar(new FormData(formulario));
    } catch (error) {
      cajaError.innerHTML = `${icono("alerta")}<span>${escapar(error.message)}</span>`;
      cajaError.hidden = false;
    } finally {
      botonEnviar.disabled = false;
      botonEnviar.classList.remove("cargando");
    }
  });
  formulario.querySelector("input, select").focus();
}
