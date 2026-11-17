// Punto de entrada de la interfaz: sesión, navegación según permisos, tema y atajos.
import { api } from "./api.js";
import { bus, estado } from "./estado.js";
import { escapar, mesActual } from "./formato.js";
import { icono } from "./iconos.js";
import { esqueleto, estadoError } from "./componentes.js";
import {
  actualizarUsuario, cerrarSesion, esAdministrador, esNegocio, obtenerToken, puede, tieneFuncion, usuarioActual,
} from "./sesion.js";
import { iniciarDialogo, notificar, ocultarTooltip } from "./ui.js";
import * as panel from "./vistas/panel.js";
import * as movimientos from "./vistas/movimientos.js";
import * as categorias from "./vistas/categorias.js";
import * as presupuestos from "./vistas/presupuestos.js";
import * as recurrentes from "./vistas/recurrentes.js";
import * as metas from "./vistas/metas.js";
import * as deudas from "./vistas/deudas.js";
import * as cajas from "./vistas/cajas.js";
import * as equipo from "./vistas/equipo.js";
import * as cuenta from "./vistas/cuenta.js";
import * as administracion from "./vistas/administracion.js";
import * as resumenAdmin from "./vistas/resumen-admin.js";
import * as solicitudes from "./vistas/solicitudes.js";
import { renderizarAutenticacion } from "./vistas/autenticacion.js";
import { abrirFormularioMovimiento } from "./vistas/formulario-movimiento.js";

const VISTAS = {
  panel, movimientos, presupuestos, recurrentes, metas, categorias, cajas, deudas, equipo, cuenta,
  "resumen-admin": resumenAdmin, administracion, solicitudes,
};
const RUTAS_PUBLICAS = ["ingresar", "registro"];
const ORDEN_INICIO = ["panel", "movimientos", "cuenta"];

const contenido = document.getElementById("contenido");
const pantallaApp = document.querySelector(".app");
const pantallaAutenticacion = document.getElementById("autenticacion");
const enlaceDe = (vista) => document.querySelector(`.navegacion [data-vista="${vista}"]`);

const rutaActual = () => location.hash.replace(/^#\/?/, "");

/** Cada enlace del menú declara lo que necesita (data-permiso, data-funcion, data-admin). */
function vistaPermitida(nombre) {
  const enlace = enlaceDe(nombre);
  if (!VISTAS[nombre] || !enlace) return false;
  const { permiso, funcion } = enlace.dataset;
  if ("admin" in enlace.dataset && !esAdministrador()) return false;
  if (permiso && !puede(permiso)) return false;
  if (funcion && !tieneFuncion(funcion)) return false;
  return true;
}

// Un administrador de la plataforma empieza en su panel; el resto, en el primero que pueda ver.
const vistaInicial = () => (esAdministrador() ? "resumen-admin" : ORDEN_INICIO.find(vistaPermitida));

/* Decide qué mostrar: pantalla de ingreso o la aplicación --------------------- */
let avisoPendiente = "";

function enrutar() {
  const ruta = rutaActual();
  if (!obtenerToken()) {
    mostrarAutenticacion();
  } else if (RUTAS_PUBLICAS.includes(ruta) || !vistaPermitida(ruta)) {
    location.replace(`#/${vistaInicial()}`); // la API igual respondería 403
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
      recurrentesGenerados = false;
      const destino = `#/${vistaInicial()}`;
      if (location.hash === destino) enrutar();
      else location.hash = destino; // el evento hashchange llama a enrutar()
    },
  });
  avisoPendiente = "";
}

let recurrentesGenerados = false;

async function mostrarAplicacion() {
  pantallaAutenticacion.hidden = true;
  pantallaAutenticacion.replaceChildren();
  pantallaApp.hidden = false;
  pintarUsuario();
  actualizarContadorSolicitudes();
  if (!recurrentesGenerados) {
    recurrentesGenerados = true;
    await generarRecurrentes();
  }
  mostrarVista();
}

/** Registra los pagos/ingresos recurrentes que vencieron desde la última visita. */
async function generarRecurrentes() {
  if (!puede("VER_MOVIMIENTOS")) return;
  try {
    const { movimientos_creados: creados } = await api.recurrentes.generar();
    if (creados > 0) {
      notificar(`Se registraron ${creados} ${creados === 1 ? "movimiento recurrente" : "movimientos recurrentes"} pendientes`);
    }
  } catch {
    /* no es crítico: se intentará en la próxima visita */
  }
}

const ROLES_NEGOCIO = { PROPIETARIO: "Propietario", EMPLEADO: "Empleado", CONTADOR: "Contador" };

function pintarUsuario() {
  const usuario = usuarioActual();
  if (!usuario) return;
  const iniciales = usuario.nombre.split(/\s+/).filter(Boolean).slice(0, 2).map((p) => p[0].toUpperCase()).join("");
  document.getElementById("usuario-avatar").textContent = iniciales;
  document.getElementById("usuario-nombre").innerHTML =
    `${escapar(usuario.nombre)}${usuario.plan === "PRO" ? ' <span class="insignia-pro">PRO</span>' : ""}`;
  const admin = esAdministrador();
  document.body.classList.toggle("modo-admin", admin); // otra identidad visual para la consola
  document.getElementById("usuario-detalle").textContent = usuario.negocio_id
    ? `${ROLES_NEGOCIO[usuario.rol_negocio]} · ${usuario.nombre_negocio}`
    : admin ? "Administrador de la plataforma" : usuario.email;
  document.getElementById("marca-subtitulo").textContent = admin
    ? "Consola de administración"
    : esNegocio() ? usuario.nombre_negocio || "Cuenta de negocio" : "Finanzas personales";
  document.getElementById("nav-cuenta").textContent = admin ? "Mi cuenta" : "Mi cuenta y plan";
  document.getElementById("nav-deudas").textContent = esNegocio() ? "Por cobrar y pagar" : "Deudas y préstamos";

  // Menú: cada enlace se muestra solo si el usuario puede usarlo; los grupos vacíos se ocultan.
  document.querySelectorAll(".navegacion [data-vista]").forEach((enlace) => {
    enlace.hidden = !vistaPermitida(enlace.dataset.vista);
  });
  document.querySelectorAll(".grupo-nav").forEach((grupo) => {
    grupo.hidden = !grupo.querySelector("[data-vista]:not([hidden])");
  });
}

/* Vistas internas (#/panel, #/movimientos, ...) -------------------------------- */
let ultimaCarga = 0;

async function mostrarVista({ conEsqueleto = true } = {}) {
  const nombre = rutaActual();
  if (!vistaPermitida(nombre)) return;
  const carga = ++ultimaCarga;
  ocultarTooltip();
  const enlace = enlaceDe(nombre);
  document.title = `${enlace.querySelector("span").textContent.trim()} · Mis Finanzas`;
  document.querySelectorAll(".navegacion [data-vista]").forEach((e) => {
    const activo = e === enlace;
    e.classList.toggle("activo", activo);
    activo ? e.setAttribute("aria-current", "page") : e.removeAttribute("aria-current");
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
  if (!obtenerToken()) return;
  mostrarVista({ conEsqueleto: false });
  actualizarContadorSolicitudes();
});

/** Número de solicitudes de Pro pendientes junto al enlace del menú (solo administradores). */
async function actualizarContadorSolicitudes() {
  const contador = document.getElementById("contador-solicitudes");
  if (!esAdministrador()) {
    contador.hidden = true;
    return;
  }
  try {
    const { solicitudes_pro: pendientes } = await api.admin.estadisticas();
    contador.textContent = pendientes;
    contador.hidden = pendientes === 0;
  } catch {
    contador.hidden = true;
  }
}
bus.addEventListener("usuario-actualizado", () => {
  pintarUsuario();
  enrutar();
});

/* Cierre de sesión (por botón o porque el servidor la rechazó) ----------------- */
bus.addEventListener("sesion-cerrada", (evento) => {
  document.body.classList.remove("modo-admin");
  avisoPendiente = evento.detail.motivo;
  estado.mes = mesActual();
  movimientos.establecerFiltros({});
  recurrentesGenerados = false;
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
  if (pantallaApp.hidden || document.getElementById("dialogo").open || !puede("REGISTRAR_MOVIMIENTOS")) return;
  evento.preventDefault();
  abrirFormularioMovimiento();
});

/* Inicio --------------------------------------------------------------------- */
document.querySelectorAll("[data-icono]").forEach((elemento) =>
  elemento.insertAdjacentHTML("afterbegin", icono(elemento.dataset.icono))
);
pintarBotonesTema();
iniciarDialogo();

// Con sesión guardada, primero se refrescan los datos de la cuenta (rol, plan,
// permisos) para no mostrar un menú desactualizado. Si el token ya no sirve,
// api.js cierra la sesión y se muestra la pantalla de ingreso.
if (obtenerToken()) {
  api.auth
    .miCuenta()
    .then((usuario) => actualizarUsuario(usuario))
    .catch(() => {})
    .finally(enrutar);
} else {
  enrutar();
}
