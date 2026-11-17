// Piezas de interfaz reutilizables: notificaciones, diálogo modal y tooltip.
import { icono } from "./iconos.js";
import { escapar } from "./formato.js";

/* Notificaciones ---------------------------------------------------------- */
const ICONO_NOTIFICACION = { exito: "check-circle", error: "x-circle", advertencia: "alerta" };

export function notificar(mensaje, tipo = "exito") {
  const elemento = document.createElement("div");
  elemento.className = `notificacion notificacion--${tipo}`;
  elemento.setAttribute("role", tipo === "error" ? "alert" : "status");
  elemento.innerHTML = `
    <span class="notificacion-icono">${icono(ICONO_NOTIFICACION[tipo])}</span>
    <p>${escapar(mensaje)}</p>
    <button type="button" class="boton-icono boton-icono--sm" aria-label="Cerrar notificación">${icono("x")}</button>`;

  let cerrada = false;
  const cerrar = () => {
    if (cerrada) return;
    cerrada = true;
    elemento.classList.add("saliendo");
    setTimeout(() => elemento.remove(), 200);
  };
  elemento.querySelector("button").addEventListener("click", cerrar);
  document.getElementById("notificaciones").append(elemento);
  setTimeout(cerrar, tipo === "exito" ? 3500 : 7000);
}

/* Diálogo modal ------------------------------------------------------------ */
const dialogo = () => document.getElementById("dialogo");

export function iniciarDialogo() {
  // Clic en el fondo oscuro cierra el diálogo.
  dialogo().addEventListener("click", (evento) => {
    if (evento.target === dialogo()) dialogo().close();
  });
}

/**
 * Abre un formulario modal. `alEnviar` recibe los datos del formulario; si lanza
 * un error, su mensaje se muestra dentro del diálogo y este queda abierto.
 */
/** Descarga un archivo recibido de la API (exportaciones). */
export function guardarArchivo({ blob, nombre }) {
  const url = URL.createObjectURL(blob);
  const enlace = Object.assign(document.createElement("a"), { href: url, download: nombre });
  document.body.append(enlace);
  enlace.click();
  enlace.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/** Abre un archivo recibido de la API en una pestaña nueva (comprobantes). */
export function abrirArchivo({ blob }) {
  const url = URL.createObjectURL(blob);
  window.open(url, "_blank", "noopener");
  setTimeout(() => URL.revokeObjectURL(url), 60_000);
}

/** Mensaje de error; si la acción requiere el plan Pro (402) agrega un enlace a los planes. */
export function htmlDeError(error) {
  const enlacePlanes =
    error.estado === 402 ? ` <a class="enlace" href="#/cuenta" data-cerrar-dialogo>Ver planes</a>` : "";
  return `${icono(error.estado === 402 ? "estrella" : "alerta")}<span>${escapar(error.message)}${enlacePlanes}</span>`;
}

export function abrirDialogo({
  titulo,
  descripcion = "",
  contenido = "",
  textoConfirmar = "Guardar",
  peligro = false,
  sinCancelar = false,
  ancho = false,
  alEnviar = async () => {},
}) {
  const d = dialogo();
  d.classList.toggle("dialogo--ancho", ancho);
  d.innerHTML = `
    <form class="dialogo-form" novalidate>
      <header class="dialogo-cabecera">
        <div>
          <h2>${titulo}</h2>
          ${descripcion ? `<p>${descripcion}</p>` : ""}
        </div>
        <button type="button" class="boton-icono" data-cerrar aria-label="Cerrar">${icono("x")}</button>
      </header>
      <div class="dialogo-cuerpo">${contenido}</div>
      <p class="dialogo-error" role="alert" hidden></p>
      <footer class="dialogo-pie">
        ${sinCancelar ? "" : '<button type="button" class="boton boton--secundario" data-cerrar>Cancelar</button>'}
        <button type="submit" class="boton ${peligro ? "boton--peligro" : "boton--primario"}">${textoConfirmar}</button>
      </footer>
    </form>`;

  const formulario = d.querySelector("form");
  const cajaError = d.querySelector(".dialogo-error");
  const botonEnviar = formulario.querySelector('[type="submit"]');
  d.querySelectorAll("[data-cerrar]").forEach((boton) => boton.addEventListener("click", () => d.close()));

  formulario.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    cajaError.hidden = true;
    botonEnviar.disabled = true;
    botonEnviar.classList.add("cargando");
    try {
      await alEnviar(new FormData(formulario));
      d.close();
    } catch (error) {
      cajaError.innerHTML = htmlDeError(error);
      cajaError.hidden = false;
      cajaError.querySelector("[data-cerrar-dialogo]")?.addEventListener("click", () => d.close());
    } finally {
      botonEnviar.disabled = false;
      botonEnviar.classList.remove("cargando");
    }
  });

  if (!d.open) d.showModal();
  const primerCampo = formulario.querySelector(".dialogo-cuerpo input:not([type=radio]), .dialogo-cuerpo select");
  (primerCampo ?? botonEnviar).focus();
}

/* Tooltip ------------------------------------------------------------------ */
const tooltip = () => document.getElementById("tooltip");

export function ocultarTooltip() {
  tooltip().hidden = true;
}

function posicionar(x, y) {
  const t = tooltip();
  const caja = t.getBoundingClientRect();
  let izquierda = x + 14;
  let arriba = y - caja.height - 12;
  if (izquierda + caja.width > window.innerWidth - 8) izquierda = x - caja.width - 14;
  if (arriba < 8) arriba = y + 18;
  t.style.transform = `translate(${Math.max(8, izquierda)}px, ${arriba}px)`;
}

/** Muestra `contenidoHtml` al pasar el mouse o al enfocar el elemento con el teclado. */
export function conTooltip(elemento, contenidoHtml) {
  const mostrar = (x, y) => {
    tooltip().innerHTML = contenidoHtml;
    tooltip().hidden = false;
    posicionar(x, y);
  };
  elemento.addEventListener("pointerenter", (e) => mostrar(e.clientX, e.clientY));
  elemento.addEventListener("pointermove", (e) => posicionar(e.clientX, e.clientY));
  elemento.addEventListener("pointerleave", ocultarTooltip);
  elemento.addEventListener("focus", () => {
    const caja = elemento.getBoundingClientRect();
    mostrar(caja.left + caja.width / 2, caja.top);
  });
  elemento.addEventListener("blur", ocultarTooltip);
}
