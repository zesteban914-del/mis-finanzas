// Vista "Presupuestos": límite total por mes y límites mensuales por categoría.
import { api } from "../api.js";
import { avisarCambio } from "../estado.js";
import { icono } from "../iconos.js";
import {
  barraProgreso, botonPrincipal, botonesEdicion, cabecera, enlazarEdicion, estadoVacio, medidorPresupuesto,
} from "../componentes.js";
import { escapar, formatoMoneda, mesActual, nombreMes, nombreMesSolo } from "../formato.js";
import { abrirDialogo, notificar } from "../ui.js";
import { abrirFormularioPresupuesto } from "./formulario-presupuesto.js";

export async function renderizar(contenedor) {
  const [presupuestos, porCategoria, categorias] = await Promise.all([
    api.presupuestos.listar(),
    api.presupuestos.porCategoria(mesActual()),
    api.categorias.listar(),
  ]);
  const estados = await Promise.all(presupuestos.map((p) => api.presupuestos.estado(p.mes)));
  const lista = presupuestos
    .map((p, i) => ({ ...p, estado: estados[i] }))
    .sort((a, b) => b.mes.localeCompare(a.mes));
  const superados = lista.filter((p) => p.estado.excedido).length;
  const mes = nombreMesSolo(mesActual());

  contenedor.innerHTML = `
    ${cabecera({
      titulo: "Presupuestos",
      subtitulo: "Define cuánto gastar como máximo y recibe alertas cuando te pases",
      acciones: botonPrincipal("nuevo-presupuesto", "Presupuesto mensual"),
    })}

    <section class="seccion">
      <header class="seccion-cabecera">
        <div>
          <h2>Límites por categoría</h2>
          <p>Aplican todos los meses. Mostrando el gasto de ${mes}.</p>
        </div>
        ${botonPrincipal("nuevo-limite", "Límite por categoría", "boton--secundario")}
      </header>
      ${
        porCategoria.length
          ? `<div class="rejilla-tarjetas">${porCategoria.map(tarjetaLimite).join("")}</div>`
          : `<section class="tarjeta">${estadoVacio({
              icono: "etiqueta",
              titulo: "Sin límites por categoría",
              texto: "Ejemplo: máximo $600.000 al mes en Comida. Te avisamos al registrar un gasto que lo supere.",
            })}</section>`
      }
    </section>

    <section class="seccion">
      <header class="seccion-cabecera">
        <div>
          <h2>Presupuesto total del mes</h2>
          <p>${lista.length ? `${lista.length} ${lista.length === 1 ? "mes" : "meses"} con presupuesto · ${superados} ${superados === 1 ? "superado" : "superados"}` : "Un límite para todos los gastos de un mes"}</p>
        </div>
      </header>
      ${
        lista.length
          ? `<div class="rejilla-tarjetas">${lista.map(tarjetaPresupuesto).join("")}</div>`
          : `<section class="tarjeta">${estadoVacio({
              icono: "objetivo",
              titulo: "Aún no tienes presupuestos mensuales",
              texto: "Crea uno para el mes actual y te avisaremos cuando tus gastos lo superen.",
            })}</section>`
      }
    </section>`;

  contenedor.querySelector("[data-accion='nuevo-presupuesto']")?.addEventListener("click", () => abrirFormularioPresupuesto());
  contenedor.querySelector("[data-accion='nuevo-limite']")?.addEventListener("click", () => formularioLimite(categorias, porCategoria));

  const seccionLimites = contenedor.querySelectorAll(".seccion")[0];
  enlazarEdicion(seccionLimites, porCategoria.map((e) => ({ ...e, id: e.categoria_id })), {
    alEditar: (estado) => formularioLimite(categorias, porCategoria, estado),
    alEliminar: (estado) => quitarLimite(estado),
  });
  const seccionMensual = contenedor.querySelectorAll(".seccion")[1];
  enlazarEdicion(seccionMensual, lista, {
    alEditar: (p) => abrirFormularioPresupuesto(p),
    alEliminar: (p) => eliminar(p),
  });
}

function tarjetaLimite(estado) {
  const fraccion = Number(estado.gastado) / Number(estado.limite);
  const clase = estado.excedido ? "critico" : fraccion >= 0.8 ? "aviso" : "bien";
  const disponible = Number(estado.disponible);
  return `
    <article class="tarjeta tarjeta-limite">
      <header class="tarjeta-cabecera" style="margin-bottom:0">
        <div>
          <h3 class="tarjeta-titulo">${escapar(estado.categoria)}</h3>
          <p class="tarjeta-subtitulo">Límite de ${formatoMoneda(estado.limite)} al mes</p>
        </div>
        ${botonesEdicion(estado.categoria_id, estado.categoria)}
      </header>
      <div class="limite-cifras">
        <b>${formatoMoneda(estado.gastado)}</b>
        <span class="estado estado--${clase}">${estado.excedido ? `${icono("x-circle")}Superado` : clase === "aviso" ? `${icono("alerta")}${estado.porcentaje} %` : `${icono("check-circle")}${estado.porcentaje} %`}</span>
      </div>
      ${barraProgreso(fraccion, clase, `Uso del límite de ${escapar(estado.categoria)}`)}
      <p class="limite-pie">${disponible >= 0 ? `Te quedan <b>${formatoMoneda(disponible)}</b>` : `Te pasaste por <b>${formatoMoneda(-disponible)}</b>`}</p>
    </article>`;
}

function tarjetaPresupuesto(p) {
  const esActual = p.mes === mesActual();
  return `
    <article class="tarjeta tarjeta-presupuesto ${esActual ? "es-actual" : ""}">
      <header class="tarjeta-cabecera" style="margin-bottom:0">
        <div>
          <h3 class="tarjeta-titulo">${nombreMes(p.mes)}</h3>
          <p class="tarjeta-subtitulo">Límite de ${formatoMoneda(p.limite)}${esActual ? '<span class="etiqueta-actual">Mes actual</span>' : ""}</p>
        </div>
        ${botonesEdicion(p.id, `presupuesto de ${nombreMes(p.mes)}`)}
      </header>
      ${medidorPresupuesto(p.estado)}
    </article>`;
}

function formularioLimite(categorias, existentes, actual = null) {
  const conLimite = new Set(existentes.map((e) => e.categoria_id));
  const disponibles = actual ? categorias.filter((c) => c.id === actual.categoria_id) : categorias.filter((c) => !conLimite.has(c.id));
  if (!disponibles.length) {
    notificar("Todas tus categorías ya tienen límite", "advertencia");
    return;
  }
  abrirDialogo({
    titulo: actual ? `Límite de ${escapar(actual.categoria)}` : "Nuevo límite por categoría",
    descripcion: "Máximo que quieres gastar cada mes en esta categoría.",
    textoConfirmar: "Guardar límite",
    contenido: `
      <label class="campo">
        <span class="campo-etiqueta">Categoría</span>
        <select class="entrada" name="categoria_id" ${actual ? "disabled" : ""}>
          ${disponibles.map((c) => `<option value="${c.id}">${escapar(c.nombre)}</option>`).join("")}
        </select>
      </label>
      <label class="campo">
        <span class="campo-etiqueta">Límite mensual</span>
        <span class="entrada-prefijo"><span>$</span>
          <input name="limite" type="number" inputmode="decimal" step="any" placeholder="0" value="${actual ? Number(actual.limite) : ""}">
        </span>
      </label>`,
    alEnviar: async (datos) => {
      const categoriaId = actual ? actual.categoria_id : Number(datos.get("categoria_id"));
      await api.presupuestos.definirCategoria(categoriaId, Number(datos.get("limite")));
      notificar("Límite guardado");
      avisarCambio();
    },
  });
}

function quitarLimite(estado) {
  abrirDialogo({
    titulo: "¿Quitar límite?",
    descripcion: `La categoría <b>${escapar(estado.categoria)}</b> quedará sin límite mensual. Tus movimientos no cambian.`,
    textoConfirmar: "Quitar límite",
    peligro: true,
    alEnviar: async () => {
      await api.presupuestos.quitarCategoria(estado.categoria_id);
      notificar("Límite eliminado");
      avisarCambio();
    },
  });
}

function eliminar(presupuesto) {
  abrirDialogo({
    titulo: "¿Eliminar presupuesto?",
    descripcion: `Se eliminará el presupuesto de <b>${nombreMes(presupuesto.mes)}</b>. Tus movimientos no se borran.`,
    textoConfirmar: "Eliminar",
    peligro: true,
    alEnviar: async () => {
      await api.presupuestos.eliminar(presupuesto.id);
      notificar("Presupuesto eliminado");
      avisarCambio();
    },
  });
}
