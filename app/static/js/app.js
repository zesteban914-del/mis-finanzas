// Punto de entrada de la interfaz: sesión, navegación entre vistas, tema y atajos.
import { api } from "./api.js";
import { bus, estado } from "./estado.js";
import { mesActual } from "./formato.js";
import { icono } from "./iconos.js";
import { esqueleto, estadoError } from "./componentes.js";
import { actualizarUsuario, cerrarSesion, esAdministrador, obtenerToken, usuarioActual } from "./sesion.js";
import { iniciarDialogo, notificar, ocultarTooltip } from "./ui.js";
import * as panel from "./vistas/panel.js";
import * as movimientos from "./vistas/movimientos.js";
import * as categorias from "./vistas/categorias.js";
import * as presupuestos from "./vistas/presupuestos.js";
import * as administracion from "./vistas/administracion.js";
import { renderizarAutenticacion } from "./vistas/autenticacion.js";
import { abrirFormularioMovimiento } from "./vistas/formulario-movimiento.js";

const VISTAS = { panel, movimientos, categorias, presupuestos, administracion };
const TITULOS = {
  panel: "Panel",
  movimientos: "Movimientos",
  categorias: "Categorías",
  presupuestos: "Presupuestos",
  administracion: "Usuarios",
};
const RUTAS_PUBLICAS = ["ingresar", "registro"];

const contenido = document.getElementById("contenido");
const pantallaApp = document.querySelector(".app");
const pantallaAutenticacion = document.getElementById("autenticacion");

const rutaActual = () => location.hash.replace(/^#\/?/, "");

function vistaActual() {
  const nombre = rutaActual();
  if (nombre === "administracion" && !esAdministrador()) return "panel";
  return VISTAS[nombre] ? nombre : "panel";
}

/* Decide qué mostrar: pantalla de ingreso o la aplicación --------------------- */
let avisoPendiente = "";

function enrutar() {
  if (!obtenerToken()) {
    mostrarAutenticacion();
  } else if (RUTAS_PUBLICAS.includes(rutaActual())) {
    location.hash = "#/panel"; // con sesión iniciada no tiene sentido ver el login
  } else if (rutaActual() === "administracion" && !esAdministrador()) {
    location.hash = "#/panel"; // la API igual respondería 403
  } else {
    mostrarAplicacion();
  }
}

function mostrarAutenticacion() {
  ocultarTooltip();
  pantallaApp.hidden = true;
  pantallaAutenticacion.hidden = false;
  renderizarAutenticacion(pantallaAutenticacion, {
    modo: rutaActual() === "registro" ? "registro" : "ingresar",
    aviso: avisoPendiente,
    alEntrar: (usuario, esNuevo) => {
      avisoPendiente = "";
      notificar(esNuevo ? `¡Bienvenido, ${usuario.nombre}! Tu cuenta está lista.` : `Hola de nuevo, ${usuario.nombre}`);
      if (location.hash === "#/panel") enrutar();
      else location.hash = "#/panel";
    },
  });
  avisoPendiente = "";
}

function mostrarAplicacion() {
  pantallaAutenticacion.hidden = true;
  pantallaAutenticacion.replaceChildren();
  pantallaApp.hidden = false;
  pintarUsuario();
  mostrarVista();
}

function pintarUsuario() {
  const usuario = usuarioActual();
  if (!usuario) return;
  const iniciales = usuario.nombre.split(/\s+/).filter(Boolean).slice(0, 2).map((p) => p[0].toUpperCase()).join("");
  document.getElementById("usuario-avatar").textContent = iniciales;
  document.getElementById("usuario-nombre").textContent = usuario.nombre;
  document.getElementById("usuario-email").textContent = usuario.email;
  document.querySelectorAll(".solo-admin").forEach((elemento) => (elemento.hidden = !esAdministrador()));
}

/* Vistas internas (#/panel, #/movimientos, ...) -------------------------------- */
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
    if (!obtenerToken()) return; // la sesión se cerró mientras cargaba
    destino.innerHTML = estadoError(error.message);
  }
  if (carga !== ultimaCarga) return; // el usuario ya navegó a otra vista
  contenido.replaceChildren(destino);
  if (conEsqueleto) window.scrollTo({ top: 0 });
}

window.addEventListener("hashchange", enrutar);
bus.addEventListener("refrescar", () => {
  if (obtenerToken()) mostrarVista({ conEsqueleto: false });
});

/* Cierre de sesión (por botón o porque el servidor la rechazó) ----------------- */
bus.addEventListener("sesion-cerrada", (evento) => {
  avisoPendiente = evento.detail.motivo;
  estado.mes = mesActual();
  movimientos.establecerFiltros({});
  document.getElementById("dialogo").close();
  if (location.hash === "#/ingresar") enrutar();
  else location.hash = "#/ingresar";
});

document.querySelectorAll(".js-salir").forEach((boton) =>
  boton.addEventListener("click", () => {
    cerrarSesion();
    notificar("Sesión cerrada");
  })
);

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
  if (pantallaApp.hidden || document.getElementById("dialogo").open) return;
  evento.preventDefault();
  abrirFormularioMovimiento();
});

/* Inicio --------------------------------------------------------------------- */
document.querySelectorAll("[data-icono]").forEach((elemento) =>
  elemento.insertAdjacentHTML("afterbegin", icono(elemento.dataset.icono))
);
pintarBotonesTema();
iniciarDialogo();
enrutar();

// Refresca los datos de la cuenta (por si cambió el rol). Si el token ya no
// sirve, api.js cierra la sesión y se muestra la pantalla de ingreso.
if (obtenerToken()) {
  api.auth.miCuenta().then((usuario) => {
    actualizarUsuario(usuario);
    pintarUsuario();
    if (rutaActual() === "administracion" && !esAdministrador()) location.hash = "#/panel";
  }).catch(() => {});
}
