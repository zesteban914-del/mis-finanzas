// Fragmentos de HTML que se repiten en varias vistas.
import { icono } from "./iconos.js";
import { escapar, formatoFechaCorta, formatoMoneda, formatoMontoConSigno } from "./formato.js";
import { esPro, puede } from "./sesion.js";

/** Barra de progreso; `clase` = bien | aviso | critico | acento. */
export const barraProgreso = (fraccion, clase = "acento", etiqueta = "Progreso") => `
  <div class="medidor" role="meter" aria-label="${etiqueta}" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${Math.round(fraccion * 100)}">
    <span class="medidor-relleno medidor-relleno--${clase}" style="width:${Math.min(Math.max(fraccion, 0), 1) * 100}%"></span>
  </div>`;

/** Botones de editar y eliminar, solo si el usuario puede gestionar. */
export function botonesEdicion(id, nombre = "registro", { editar = true, eliminar = true } = {}) {
  if (!puede("GESTIONAR")) return "";
  return `
    <div class="categoria-acciones">
      ${editar ? `<button type="button" class="boton-icono" data-editar="${id}" aria-label="Editar ${escapar(nombre)}" title="Editar">${icono("lapiz")}</button>` : ""}
      ${eliminar ? `<button type="button" class="boton-icono boton-icono--peligro" data-eliminar="${id}" aria-label="Eliminar ${escapar(nombre)}" title="Eliminar">${icono("papelera")}</button>` : ""}
    </div>`;
}

/** "2 de 3 en el plan Gratis" con enlace a los planes; nada si es Pro. */
export function cupoDelPlan(usados, limite, nombre) {
  if (esPro()) return "";
  const lleno = usados >= limite;
  return `
    <p class="cupo-plan ${lleno ? "cupo-plan--lleno" : ""}">
      ${icono("estrella")}
      <span>Usas <b>${usados} de ${limite}</b> ${nombre} del plan Gratis.</span>
      <a class="enlace" href="#/cuenta">${lleno ? "Mejorar a Pro" : "Ver planes"}</a>
    </p>`;
}

export const insigniaPro = () => '<span class="insignia-pro">PRO</span>';

/** Enlaza los botones [data-editar] y [data-eliminar] de un contenedor con sus acciones. */
export function enlazarEdicion(contenedor, lista, { alEditar, alEliminar }) {
  const buscar = (id) => lista.find((x) => x.id === Number(id));
  contenedor.querySelectorAll("[data-editar]").forEach((b) => b.addEventListener("click", () => alEditar(buscar(b.dataset.editar))));
  contenedor.querySelectorAll("[data-eliminar]").forEach((b) => b.addEventListener("click", () => alEliminar(buscar(b.dataset.eliminar))));
}

export const SERIES = [
  { nombre: "Ingresos", colorVar: "--serie-ingreso" },
  { nombre: "Gastos", colorVar: "--serie-gasto" },
];

export function cabecera({ titulo, subtitulo = "", acciones = "" }) {
  return `
    <header class="cabecera">
      <div>
        <h1>${titulo}</h1>
        ${subtitulo ? `<p>${subtitulo}</p>` : ""}
      </div>
      <div class="cabecera-acciones">${acciones}</div>
    </header>`;
}

export const botonNuevoMovimiento = (clase = "boton--primario") =>
  puede("REGISTRAR_MOVIMIENTOS")
    ? `<button type="button" class="boton ${clase}" data-accion="nuevo-movimiento">${icono("mas")}<span>Nuevo movimiento</span><kbd>N</kbd></button>`
    : "";

/** Botón principal de una vista ("Nuevo …"), solo si el usuario puede gestionar. */
export const botonPrincipal = (accion, texto, clase = "boton--primario") =>
  puede("GESTIONAR")
    ? `<button type="button" class="boton ${clase}" data-accion="${accion}">${icono("mas")}<span>${texto}</span></button>`
    : "";

export function estadoVacio({ icono: nombreIcono = "bandeja", titulo, texto = "", accion = "" }) {
  return `
    <div class="vacio">
      <span class="vacio-icono">${icono(nombreIcono)}</span>
      <p class="vacio-titulo">${titulo}</p>
      ${texto ? `<p class="vacio-texto">${texto}</p>` : ""}
      ${accion}
    </div>`;
}

export function estadoError(mensaje) {
  return `
    <section class="tarjeta">
      ${estadoVacio({
        icono: "x-circle",
        titulo: "No se pudieron cargar los datos",
        texto: escapar(mensaje),
        accion: `<button type="button" class="boton boton--secundario" onclick="location.reload()">Reintentar</button>`,
      })}
    </section>`;
}

export function esqueleto() {
  return `
    <div class="esqueleto-vista" aria-busy="true" aria-label="Cargando">
      <div class="esq esq-titulo"></div>
      <div class="kpis">${'<div class="esq esq-kpi"></div>'.repeat(4)}</div>
      <div class="panel-rejilla">
        <div class="esq esq-bloque col-5"></div>
        <div class="esq esq-bloque col-7"></div>
      </div>
    </div>`;
}

export function kpi({ etiqueta, valor, pie = "", icono: nombreIcono = "", colorVar = "", destacado = false }) {
  const marca = colorVar
    ? `<span class="kpi-muestra" style="background:var(${colorVar})"></span>`
    : nombreIcono ? icono(nombreIcono) : "";
  return `
    <article class="kpi ${destacado ? "kpi--destacado" : ""}">
      <span class="kpi-etiqueta">${marca}${etiqueta}</span>
      <span class="kpi-valor">${valor}</span>
      ${pie ? `<span class="kpi-pie">${pie}</span>` : ""}
    </article>`;
}

export function insigniaTipo(tipo) {
  const esIngreso = tipo === "INGRESO";
  return `<span class="insignia" style="--punto:var(${esIngreso ? "--serie-ingreso" : "--serie-gasto"})">${esIngreso ? "Ingreso" : "Gasto"}</span>`;
}

export const montoMovimiento = (m) =>
  `<span class="monto monto--${m.tipo.toLowerCase()}">${formatoMontoConSigno(m.monto, m.tipo)}</span>`;

export function itemReciente(m, nombreCategoria = "") {
  const esIngreso = m.tipo === "INGRESO";
  return `
    <li class="reciente">
      <span class="reciente-icono" style="--color:var(${esIngreso ? "--serie-ingreso" : "--serie-gasto"})">${icono(esIngreso ? "flecha-ingreso" : "flecha-gasto")}</span>
      <span class="reciente-texto">
        <span class="reciente-titulo">${escapar(m.descripcion || nombreCategoria)}</span>
        <span class="reciente-meta">${escapar(nombreCategoria)} · ${formatoFechaCorta(m.fecha)}</span>
      </span>
      ${montoMovimiento(m)}
    </li>`;
}

/** Clasifica el uso del presupuesto: el color siempre va con icono y texto. */
export function clasificarPresupuesto(estadoPresupuesto) {
  const limite = Number(estadoPresupuesto.limite);
  const fraccion = limite > 0 ? Number(estadoPresupuesto.total_gastado) / limite : 0;
  if (estadoPresupuesto.excedido) return { fraccion, clase: "critico", icono: "x-circle", etiqueta: "Presupuesto superado" };
  if (fraccion >= 0.8) return { fraccion, clase: "aviso", icono: "alerta", etiqueta: "Cerca del límite" };
  return { fraccion, clase: "bien", icono: "check-circle", etiqueta: "Dentro del presupuesto" };
}

export function medidorPresupuesto(estadoPresupuesto, { conDetalle = false } = {}) {
  const c = clasificarPresupuesto(estadoPresupuesto);
  const disponible = Number(estadoPresupuesto.disponible);
  const porcentaje = Math.round(c.fraccion * 100);
  return `
    <div class="presupuesto">
      <div class="presupuesto-cifras">
        <div>
          <span class="presupuesto-gastado">${formatoMoneda(estadoPresupuesto.total_gastado)}</span>
          <span class="presupuesto-limite">gastados de ${formatoMoneda(estadoPresupuesto.limite)}</span>
        </div>
        <span class="estado estado--${c.clase}">${icono(c.icono)}${c.etiqueta}</span>
      </div>
      <div class="medidor" role="meter" aria-label="Presupuesto usado" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${porcentaje}">
        <span class="medidor-relleno medidor-relleno--${c.clase}" style="width:${Math.min(c.fraccion, 1) * 100}%"></span>
      </div>
      <div class="presupuesto-pie">
        <span><b>${porcentaje} %</b> usado</span>
        <span>${disponible >= 0 ? `Disponible: <b>${formatoMoneda(disponible)}</b>` : `Excedido por <b>${formatoMoneda(-disponible)}</b>`}</span>
      </div>
      ${
        conDetalle
          ? `<div class="medidor-detalle">
              <div><span>Límite</span><b>${formatoMoneda(estadoPresupuesto.limite)}</b></div>
              <div><span>Gastado</span><b>${formatoMoneda(estadoPresupuesto.total_gastado)}</b></div>
              <div><span>${disponible >= 0 ? "Disponible" : "Excedido"}</span><b>${formatoMoneda(Math.abs(disponible))}</b></div>
            </div>`
          : ""
      }
    </div>`;
}

/** Tarjeta con un gráfico y su versión en tabla (botones para alternar entre ambos). */
export function tarjetaGrafico({ id, titulo, subtitulo = "", extra = "", tabla, clase = "" }) {
  return `
    <section class="tarjeta ${clase}" data-grafico>
      <header class="tarjeta-cabecera">
        <div>
          <h2 class="tarjeta-titulo">${titulo}</h2>
          ${subtitulo ? `<p class="tarjeta-subtitulo">${subtitulo}</p>` : ""}
        </div>
        <div class="tarjeta-acciones">
          ${extra}
          <div class="alternador" role="group" aria-label="Cambiar vista del gráfico">
            <button type="button" class="activo" data-alternar="grafico" aria-pressed="true" title="Ver gráfico">${icono("grafico")}</button>
            <button type="button" data-alternar="tabla" aria-pressed="false" title="Ver tabla">${icono("tabla")}</button>
          </div>
        </div>
      </header>
      <div data-panel="grafico" id="${id}"></div>
      <div data-panel="tabla" hidden>${tabla}</div>
    </section>`;
}

export const leyenda = (series = SERIES) =>
  `<div class="leyenda">${series.map((s) => `<span><i style="background:var(${s.colorVar})"></i>${s.nombre}</span>`).join("")}</div>`;
