// Vista de deudas: "Deudas y préstamos" (personal) o "Cuentas por cobrar y pagar" (negocio).
// Es la misma entidad en el backend; solo cambian los textos según el tipo de cuenta.
import { api } from "../api.js";
import { avisarCambio } from "../estado.js";
import { icono } from "../iconos.js";
import { barraProgreso, botonPrincipal, botonesEdicion, cabecera, enlazarEdicion, estadoVacio, kpi } from "../componentes.js";
import { escapar, formatoFecha, formatoMoneda } from "../formato.js";
import { esNegocio, puede } from "../sesion.js";
import { abrirDialogo, notificar } from "../ui.js";

const TEXTOS = {
  PERSONAL: {
    titulo: "Deudas y préstamos",
    subtitulo: "Lo que debes y lo que te deben, con abonos y fechas de pago",
    POR_PAGAR: "Debo", POR_COBRAR: "Me deben",
    contraparte: "Persona o entidad", ejemplo: "Ej. Banco, tarjeta de crédito, Juan",
    totalCobrar: "Te deben", totalPagar: "Debes",
  },
  NEGOCIO: {
    titulo: "Cuentas por cobrar y pagar",
    subtitulo: "Ventas a crédito de tus clientes y compras a crédito a tus proveedores",
    POR_PAGAR: "Por pagar", POR_COBRAR: "Por cobrar",
    contraparte: "Cliente o proveedor", ejemplo: "Ej. Distribuidora Harinas S.A.S.",
    totalCobrar: "Por cobrar a clientes", totalPagar: "Por pagar a proveedores",
  },
};
const ESTADOS = {
  PENDIENTE: ["neutro", "calendario", "Pendiente"],
  VENCIDA: ["critico", "alerta", "Vencida"],
  PAGADA: ["bien", "check-circle", "Saldada"],
};

let filtro = "";

const textos = () => TEXTOS[esNegocio() ? "NEGOCIO" : "PERSONAL"];

export async function renderizar(contenedor) {
  const t = textos();
  const deudas = await api.deudas.listar();
  const pendiente = (tipo) => deudas.filter((d) => d.tipo === tipo).reduce((s, d) => s + Number(d.pendiente), 0);
  const vencidas = deudas.filter((d) => d.estado === "VENCIDA").length;
  const visibles = filtro ? deudas.filter((d) => d.tipo === filtro) : deudas;

  contenedor.innerHTML = `
    ${cabecera({ titulo: t.titulo, subtitulo: t.subtitulo, acciones: botonPrincipal("nueva-deuda", "Nuevo registro") })}
    <section class="kpis kpis--3">
      ${kpi({ etiqueta: t.totalCobrar, valor: formatoMoneda(pendiente("POR_COBRAR")), colorVar: "--serie-ingreso", pie: "Saldo pendiente" })}
      ${kpi({ etiqueta: t.totalPagar, valor: formatoMoneda(pendiente("POR_PAGAR")), colorVar: "--serie-gasto", pie: "Saldo pendiente" })}
      ${kpi({ etiqueta: "Vencidas", valor: vencidas, icono: "alerta", pie: vencidas ? "Revisa las fechas de pago" : "Todo al día" })}
    </section>
    <section class="tarjeta tarjeta--tabla">
      <div class="pestanas" role="tablist">
        ${[["", "Todas"], ["POR_COBRAR", t.POR_COBRAR], ["POR_PAGAR", t.POR_PAGAR]]
          .map(([valor, texto]) => `<button type="button" role="tab" aria-selected="${filtro === valor}" class="${filtro === valor ? "activa" : ""}" data-filtro="${valor}">${texto}</button>`)
          .join("")}
      </div>
      ${
        visibles.length
          ? tabla(visibles, t)
          : estadoVacio({
              icono: "documento",
              titulo: "No hay registros",
              texto: esNegocio()
                ? "Registra las ventas a crédito y las facturas de proveedores para saber cuánto entra y sale."
                : "Registra préstamos, tarjetas o dinero que prestaste y lleva el control de los abonos.",
              accion: botonPrincipal("nueva-deuda", "Nuevo registro", "boton--secundario"),
            })
      }
    </section>`;

  contenedor.querySelectorAll("[data-filtro]").forEach((b) =>
    b.addEventListener("click", () => {
      filtro = b.dataset.filtro;
      renderizar(contenedor);
    })
  );
  contenedor.querySelectorAll("[data-accion='nueva-deuda']").forEach((b) => b.addEventListener("click", () => formulario()));
  enlazarEdicion(contenedor, deudas, { alEditar: (d) => formulario(d), alEliminar: (d) => eliminar(d) });
  contenedor.querySelectorAll("[data-abonar]").forEach((b) =>
    b.addEventListener("click", () => abonar(deudas.find((d) => d.id === Number(b.dataset.abonar))))
  );
}

function tabla(deudas, t) {
  const filas = deudas
    .map((d) => {
      const [clase, nombreIcono, texto] = ESTADOS[d.estado];
      const fraccion = Number(d.monto_pagado) / Number(d.monto_total);
      return `
      <tr>
        <td class="celda-descripcion">
          ${escapar(d.contraparte)}
          ${d.descripcion ? `<small class="celda-autor">${escapar(d.descripcion)}</small>` : ""}
        </td>
        <td><span class="insignia" style="--punto:var(${d.tipo === "POR_COBRAR" ? "--serie-ingreso" : "--serie-gasto"})">${t[d.tipo]}</span></td>
        <td class="celda-progreso">
          ${barraProgreso(fraccion, d.estado === "PAGADA" ? "bien" : "acento", "Abonado")}
          <small>${formatoMoneda(d.monto_pagado)} de ${formatoMoneda(d.monto_total)}</small>
        </td>
        <td class="celda-fecha">
          <span class="estado estado--${clase}">${icono(nombreIcono)}${texto}</span>
          ${d.fecha_vencimiento ? `<small class="celda-autor">Vence ${formatoFecha(d.fecha_vencimiento)}</small>` : ""}
        </td>
        <td class="num"><span class="monto">${formatoMoneda(d.pendiente)}</span></td>
        <td class="acciones">
          <div class="acciones-grupo">
            ${d.estado !== "PAGADA" && puede("GESTIONAR") ? `<button type="button" class="boton boton--secundario boton--sm" data-abonar="${d.id}">Abonar</button>` : ""}
            ${botonesEdicion(d.id, d.contraparte)}
          </div>
        </td>
      </tr>`;
    })
    .join("");
  return `
    <div class="tabla-contenedor">
      <table class="tabla tabla--deudas">
        <thead><tr><th>${t.contraparte}</th><th>Tipo</th><th>Abonado</th><th>Estado</th><th class="num">Pendiente</th><th class="acciones"><span class="sr-only">Acciones</span></th></tr></thead>
        <tbody>${filas}</tbody>
      </table>
    </div>`;
}

function formulario(actual = null) {
  const t = textos();
  abrirDialogo({
    titulo: actual ? "Editar registro" : "Nuevo registro",
    textoConfirmar: actual ? "Guardar cambios" : "Crear",
    contenido: `
      ${
        actual
          ? ""
          : `<div class="segmentado">
               <label class="segmento segmento--gasto"><input type="radio" name="tipo" value="POR_PAGAR" checked><span>${icono("flecha-gasto")}${t.POR_PAGAR}</span></label>
               <label class="segmento segmento--ingreso"><input type="radio" name="tipo" value="POR_COBRAR"><span>${icono("flecha-ingreso")}${t.POR_COBRAR}</span></label>
             </div>`
      }
      <label class="campo">
        <span class="campo-etiqueta">${t.contraparte}</span>
        <input class="entrada" name="contraparte" maxlength="80" placeholder="${t.ejemplo}" value="${escapar(actual?.contraparte ?? "")}">
      </label>
      <div class="campos-fila">
        <label class="campo">
          <span class="campo-etiqueta">Monto total</span>
          <span class="entrada-prefijo"><span>$</span>
            <input name="monto_total" type="number" inputmode="decimal" step="any" placeholder="0" value="${actual ? Number(actual.monto_total) : ""}">
          </span>
        </label>
        <label class="campo">
          <span class="campo-etiqueta">Fecha de vencimiento <span class="texto-tenue">(opcional)</span></span>
          <input class="entrada" name="fecha_vencimiento" type="date" value="${actual?.fecha_vencimiento ?? ""}">
        </label>
      </div>
      <label class="campo">
        <span class="campo-etiqueta">Detalle <span class="texto-tenue">(opcional)</span></span>
        <input class="entrada" name="descripcion" maxlength="255" placeholder="Ej. Factura 1023, cuota 3 de 12" value="${escapar(actual?.descripcion ?? "")}">
      </label>`,
    alEnviar: async (datos) => {
      const cuerpo = {
        contraparte: datos.get("contraparte").trim(),
        monto_total: Number(datos.get("monto_total")),
        fecha_vencimiento: datos.get("fecha_vencimiento") || null,
        descripcion: datos.get("descripcion").trim(),
      };
      if (actual) await api.deudas.actualizar(actual.id, cuerpo);
      else await api.deudas.crear({ ...cuerpo, tipo: datos.get("tipo") });
      notificar(actual ? "Registro actualizado" : "Registro creado");
      avisarCambio();
    },
  });
}

function abonar(deuda) {
  abrirDialogo({
    titulo: `Abono · ${escapar(deuda.contraparte)}`,
    descripcion: `Saldo pendiente: ${formatoMoneda(deuda.pendiente)}.`,
    textoConfirmar: "Registrar abono",
    contenido: `
      <label class="campo">
        <span class="campo-etiqueta">Monto del abono</span>
        <span class="entrada-prefijo"><span>$</span><input name="monto" type="number" inputmode="decimal" step="any" value="${Number(deuda.pendiente)}"></span>
      </label>`,
    alEnviar: async (datos) => {
      const resultado = await api.deudas.abonar(deuda.id, Number(datos.get("monto")));
      notificar(resultado.estado === "PAGADA" ? "¡Quedó saldada!" : "Abono registrado");
      avisarCambio();
    },
  });
}

function eliminar(deuda) {
  abrirDialogo({
    titulo: "¿Eliminar registro?",
    descripcion: `Se eliminará el registro de <b>${escapar(deuda.contraparte)}</b> y sus abonos.`,
    textoConfirmar: "Eliminar",
    peligro: true,
    alEnviar: async () => {
      await api.deudas.eliminar(deuda.id);
      notificar("Registro eliminado");
      avisarCambio();
    },
  });
}
