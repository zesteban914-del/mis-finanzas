// Vista "Presupuestos": un límite de gasto por mes y su estado actual.
import { api } from "../api.js";
import { avisarCambio } from "../estado.js";
import { icono } from "../iconos.js";
import { cabecera, estadoVacio, medidorPresupuesto } from "../componentes.js";
import { formatoMoneda, mesActual, nombreMes } from "../formato.js";
import { abrirDialogo, notificar } from "../ui.js";
import { abrirFormularioPresupuesto } from "./formulario-presupuesto.js";

export async function renderizar(contenedor) {
  const presupuestos = await api.presupuestos.listar();
  const estados = await Promise.all(presupuestos.map((p) => api.presupuestos.estado(p.mes)));
  const lista = presupuestos
    .map((p, i) => ({ ...p, estado: estados[i] }))
    .sort((a, b) => b.mes.localeCompare(a.mes));
  const superados = lista.filter((p) => p.estado.excedido).length;

  const botonNuevo = `<button type="button" class="boton boton--primario" data-accion="nuevo-presupuesto">${icono("mas")}Nuevo presupuesto</button>`;

  contenedor.innerHTML = `
    ${cabecera({
      titulo: "Presupuestos",
      subtitulo: lista.length
        ? `${lista.length} ${lista.length === 1 ? "mes" : "meses"} con presupuesto · ${superados} ${superados === 1 ? "superado" : "superados"}`
        : "Define cuánto quieres gastar como máximo cada mes",
      acciones: botonNuevo,
    })}
    ${
      lista.length
        ? `<div class="rejilla-tarjetas">${lista.map(tarjetaPresupuesto).join("")}</div>`
        : `<section class="tarjeta">${estadoVacio({
            icono: "objetivo",
            titulo: "Aún no tienes presupuestos",
            texto: "Crea uno para el mes actual y te avisaremos cuando tus gastos lo superen.",
            accion: botonNuevo.replace("boton--primario", "boton--secundario"),
          })}</section>`
    }`;

  contenedor.querySelectorAll("[data-accion='nuevo-presupuesto']").forEach((boton) =>
    boton.addEventListener("click", () => abrirFormularioPresupuesto())
  );
  const buscar = (id) => lista.find((p) => p.id === Number(id));
  contenedor.querySelectorAll("[data-editar]").forEach((boton) =>
    boton.addEventListener("click", () => abrirFormularioPresupuesto(buscar(boton.dataset.editar)))
  );
  contenedor.querySelectorAll("[data-eliminar]").forEach((boton) =>
    boton.addEventListener("click", () => eliminar(buscar(boton.dataset.eliminar)))
  );
}

function tarjetaPresupuesto(p) {
  const esActual = p.mes === mesActual();
  return `
    <article class="tarjeta tarjeta-presupuesto ${esActual ? "es-actual" : ""}">
      <header class="tarjeta-cabecera" style="margin-bottom:0">
        <div>
          <h2 class="tarjeta-titulo">${nombreMes(p.mes)}</h2>
          <p class="tarjeta-subtitulo">Límite de ${formatoMoneda(p.limite)}${esActual ? '<span class="etiqueta-actual">Mes actual</span>' : ""}</p>
        </div>
        <div class="categoria-acciones">
          <button type="button" class="boton-icono" data-editar="${p.id}" aria-label="Editar presupuesto de ${nombreMes(p.mes)}" title="Editar">${icono("lapiz")}</button>
          <button type="button" class="boton-icono boton-icono--peligro" data-eliminar="${p.id}" aria-label="Eliminar presupuesto de ${nombreMes(p.mes)}" title="Eliminar">${icono("papelera")}</button>
        </div>
      </header>
      ${medidorPresupuesto(p.estado)}
    </article>`;
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
