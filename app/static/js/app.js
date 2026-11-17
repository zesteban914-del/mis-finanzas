// Punto de entrada de la interfaz: navegación entre vistas, tema claro/oscuro y atajos.
import { bus } from "./estado.js";
import { icono } from "./iconos.js";
import { esqueleto, estadoError } from "./componentes.js";
import { iniciarDialogo, ocultarTooltip } from "./ui.js";
import * as panel from "./vistas/panel.js";
import * as movimientos from "./vistas/movimientos.js";
import * as categorias from "./vistas/categorias.js";
import * as presupuestos from "./vistas/presupuestos.js";
import { abrirFormularioMovimiento } from "./vistas/formulario-movimiento.js";

const VISTAS = { panel, movimientos, categorias, presupuestos };
const TITULOS = { panel: "Panel", movimientos: "Movimientos", categorias: "Categorías", presupuestos: "Presupuestos" };
const contenido = document.getElementById("contenido");

const vistaActual = () => {
  const nombre = location.hash.replace(/^#\/?/, "");
  return VISTAS[nombre] ? nombre : "panel";
};

/* Navegación (las rutas son #/panel, #/movimientos, ...) ------------------- */
let ultimaCarga = 0;

async function mostrarVista({ conEsqueleto = true } = {}) {
  const nombre = vistaActual();
  const carga = ++ultimaCarga;
  ocultarTooltip();
  document.title = `${TITULOS[nombre]} · Mis Finanzas`;
  document.querySelectorAll("[data-vista]").forEach((enlace) => {
    const activo = enlace.dataset.vista === nombre;
    enlace.classList.toggle("activo", activo);
    activo ? enlace.setAttribute("aria-current", "page") : enlace.removeAttribute("aria-current");
  });

  if (conEsqueleto) contenido.innerHTML = esqueleto();
  const destino = document.createElement("div");
  destino.className = "vista";
  try {
    await VISTAS[nombre].renderizar(destino);
  } catch (error) {
    destino.innerHTML = estadoError(error.message);
  }
  if (carga !== ultimaCarga) return; // el usuario ya navegó a otra vista
  contenido.replaceChildren(destino);
  if (conEsqueleto) window.scrollTo({ top: 0 });
}

window.addEventListener("hashchange", () => mostrarVista());
bus.addEventListener("refrescar", () => mostrarVista({ conEsqueleto: false }));

/* Tema claro / oscuro ------------------------------------------------------- */
const temaEfectivo = () =>
  document.documentElement.dataset.theme ??
  (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");

function pintarBotonesTema() {
  const oscuro = temaEfectivo() === "dark";
  document.querySelectorAll(".js-tema").forEach((boton) => {
    const texto = oscuro ? "Modo claro" : "Modo oscuro";
    boton.innerHTML = boton.classList.contains("boton-icono")
      ? icono(oscuro ? "sol" : "luna")
      : `${icono(oscuro ? "sol" : "luna")}<span>${texto}</span>`;
    boton.setAttribute("aria-label", `Cambiar a ${texto.toLowerCase()}`);
  });
}

document.querySelectorAll(".js-tema").forEach((boton) =>
  boton.addEventListener("click", () => {
    const nuevo = temaEfectivo() === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = nuevo;
    try {
      localStorage.setItem("tema", nuevo);
    } catch {
      /* sin almacenamiento disponible: el tema dura solo esta visita */
    }
    pintarBotonesTema();
  })
);
matchMedia("(prefers-color-scheme: dark)").addEventListener("change", pintarBotonesTema);

/* Acciones globales ---------------------------------------------------------- */
document.addEventListener("click", (evento) => {
  if (evento.target.closest("[data-accion='nuevo-movimiento']")) {
    abrirFormularioMovimiento();
    return;
  }
  // Alternar entre gráfico y tabla dentro de una tarjeta.
  const alternar = evento.target.closest("[data-alternar]");
  if (alternar) {
    const tarjeta = alternar.closest("[data-grafico]");
    tarjeta.querySelectorAll("[data-alternar]").forEach((b) => {
      const activo = b === alternar;
      b.classList.toggle("activo", activo);
      b.setAttribute("aria-pressed", String(activo));
    });
    tarjeta.querySelectorAll("[data-panel]").forEach((p) => (p.hidden = p.dataset.panel !== alternar.dataset.alternar));
  }
});

// Atajo de teclado: "N" abre el formulario de nuevo movimiento.
document.addEventListener("keydown", (evento) => {
  const escribiendo = ["INPUT", "SELECT", "TEXTAREA"].includes(document.activeElement?.tagName);
  if (evento.key.toLowerCase() !== "n" || evento.ctrlKey || evento.metaKey || evento.altKey || escribiendo) return;
  if (document.getElementById("dialogo").open) return;
  evento.preventDefault();
  abrirFormularioMovimiento();
});

/* Inicio --------------------------------------------------------------------- */
document.querySelectorAll("[data-icono]").forEach((elemento) =>
  elemento.insertAdjacentHTML("afterbegin", icono(elemento.dataset.icono))
);
pintarBotonesTema();
iniciarDialogo();
mostrarVista();
