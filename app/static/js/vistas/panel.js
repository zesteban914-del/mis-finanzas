// Vista "Panel": resumen del mes con KPIs, presupuesto, gráficos y últimos movimientos.
import { api } from "../api.js";
import { avisarCambio, estado } from "../estado.js";
import { barrasHorizontales, columnasAgrupadas } from "../graficos.js";
import { icono } from "../iconos.js";
import {
  SERIES, botonNuevoMovimiento, cabecera, clasificarPresupuesto, estadoVacio,
  itemReciente, kpi, leyenda, medidorPresupuesto, tarjetaGrafico,
} from "../componentes.js";
import {
  desplazarMes, escapar, formatoMoneda, mesActual, mesesHasta,
  nombreMes, nombreMesCorto, nombreMesSolo, rangoDelMes,
} from "../formato.js";
import { abrirFormularioPresupuesto } from "./formulario-presupuesto.js";
import { establecerFiltros } from "./movimientos.js";

const sinPresupuesto = (error) => {
  if (error.estado === 404) return null;
  throw error;
};

export async function renderizar(contenedor) {
  const mes = estado.mes;
  const meses = mesesHasta(mes, 6);
  const { inicio, fin } = rangoDelMes(mes);

  const [saldo, resumenes, movimientosMes, categorias, presupuesto] = await Promise.all([
    api.reportes.saldo(),
    Promise.all(meses.map((m) => api.reportes.resumenMensual(m))),
    api.movimientos.listar({ fecha_inicio: inicio, fecha_fin: fin }),
    api.categorias.listar(),
    api.presupuestos.estado(mes).catch(sinPresupuesto),
  ]);

  const resumen = resumenes.at(-1);
  const anterior = resumenes.at(-2);
  const nombres = new Map(categorias.map((c) => [c.id, c.nombre]));
  const ingresos = Number(resumen.total_ingresos);
  const gastos = Number(resumen.total_gastos);
  const balance = Number(resumen.balance);
  const mesTexto = nombreMesSolo(mes);

  const gastosPorCategoria = resumen.categorias
    .filter((c) => Number(c.total_gastos) > 0)
    .map((c) => ({ etiqueta: c.categoria, valor: Number(c.total_gastos) }));
  const tendencia = resumenes.map((r) => ({
    etiqueta: nombreMesCorto(r.mes),
    titulo: nombreMes(r.mes),
    valores: [Number(r.total_ingresos), Number(r.total_gastos)],
    actual: r.mes === mes,
  }));

  contenedor.innerHTML = `
    ${cabecera({
      titulo: "Panel",
      subtitulo: `Así van tus finanzas en ${mesTexto}`,
      acciones: `${selectorMes(mes)}${botonNuevoMovimiento()}`,
    })}

    ${alertaPresupuesto(presupuesto, mesTexto)}

    <section class="kpis" aria-label="Indicadores">
      ${kpi({ etiqueta: "Saldo actual", valor: formatoMoneda(saldo.saldo), pie: "Todos tus ingresos menos tus gastos", icono: "billetera", destacado: true })}
      ${kpi({ etiqueta: `Ingresos de ${mesTexto}`, valor: formatoMoneda(ingresos), pie: variacion(ingresos, Number(anterior.total_ingresos), anterior.mes), colorVar: "--serie-ingreso" })}
      ${kpi({ etiqueta: `Gastos de ${mesTexto}`, valor: formatoMoneda(gastos), pie: variacion(gastos, Number(anterior.total_gastos), anterior.mes), colorVar: "--serie-gasto" })}
      ${kpi({ etiqueta: "Balance del mes", valor: formatoMoneda(balance), pie: textoAhorro(ingresos, balance), icono: "balanza" })}
    </section>

    <div class="panel-rejilla">
      <section class="tarjeta col-5">
        <header class="tarjeta-cabecera">
          <div>
            <h2 class="tarjeta-titulo">Presupuesto de ${mesTexto}</h2>
            <p class="tarjeta-subtitulo">Tus gastos del mes frente al límite</p>
          </div>
          ${presupuesto ? `<button type="button" class="boton-icono" data-accion="editar-presupuesto" aria-label="Editar presupuesto" title="Editar presupuesto">${icono("lapiz")}</button>` : ""}
        </header>
        ${
          presupuesto
            ? medidorPresupuesto(presupuesto, { conDetalle: true })
            : estadoVacio({
                icono: "objetivo",
                titulo: "Sin presupuesto para este mes",
                texto: "Define un límite de gasto y te avisaremos cuando lo superes.",
                accion: `<button type="button" class="boton boton--secundario" data-accion="crear-presupuesto">${icono("mas")}Definir presupuesto</button>`,
              })
        }
      </section>

      ${
        gastosPorCategoria.length
          ? tarjetaGrafico({
              id: "grafico-categorias",
              titulo: "Gastos por categoría",
              subtitulo: `En qué se fue tu dinero en ${mesTexto}`,
              tabla: tablaCategorias(gastosPorCategoria),
              clase: "col-7",
            })
          : `<section class="tarjeta col-7">
              <header class="tarjeta-cabecera"><div><h2 class="tarjeta-titulo">Gastos por categoría</h2></div></header>
              ${estadoVacio({ icono: "grafico", titulo: "Sin gastos este mes", texto: "Cuando registres gastos verás aquí en qué se va tu dinero." })}
            </section>`
      }

      ${tarjetaGrafico({
        id: "grafico-tendencia",
        titulo: "Ingresos vs. gastos",
        subtitulo: "Últimos 6 meses",
        extra: leyenda(),
        tabla: tablaTendencia(tendencia),
        clase: "col-7",
      })}

      <section class="tarjeta col-5">
        <header class="tarjeta-cabecera">
          <div>
            <h2 class="tarjeta-titulo">Movimientos recientes</h2>
            <p class="tarjeta-subtitulo">${movimientosMes.length} ${movimientosMes.length === 1 ? "registro" : "registros"} en ${mesTexto}</p>
          </div>
          ${movimientosMes.length ? `<a class="enlace" href="#/movimientos" data-accion="ver-mes">Ver todos${icono("derecha")}</a>` : ""}
        </header>
        ${
          movimientosMes.length
            ? `<ul class="recientes">${movimientosMes.slice(0, 6).map((m) => itemReciente(m, nombres.get(m.categoria_id))).join("")}</ul>`
            : estadoVacio({ titulo: "Sin movimientos este mes", texto: "Registra tu primer ingreso o gasto.", accion: botonNuevoMovimiento("boton--secundario") })
        }
      </section>
    </div>`;

  const contenedorCategorias = contenedor.querySelector("#grafico-categorias");
  if (contenedorCategorias) barrasHorizontales(contenedorCategorias, gastosPorCategoria);
  columnasAgrupadas(contenedor.querySelector("#grafico-tendencia"), tendencia, SERIES);

  contenedor.querySelectorAll("[data-mes]").forEach((boton) =>
    boton.addEventListener("click", () => {
      estado.mes = desplazarMes(mes, Number(boton.dataset.mes));
      avisarCambio();
    })
  );
  contenedor.querySelector("[data-accion='crear-presupuesto']")?.addEventListener("click", () => abrirFormularioPresupuesto(null, mes));
  contenedor.querySelector("[data-accion='editar-presupuesto']")?.addEventListener("click", async () => {
    const lista = await api.presupuestos.listar();
    abrirFormularioPresupuesto(lista.find((p) => p.mes === mes));
  });
  contenedor.querySelector("[data-accion='ver-mes']")?.addEventListener("click", () => establecerFiltros({ fecha_inicio: inicio, fecha_fin: fin }));
}

function selectorMes(mes) {
  return `
    <div class="selector-mes">
      <button type="button" class="boton-icono" data-mes="-1" aria-label="Mes anterior">${icono("izquierda")}</button>
      <span class="selector-mes-etiqueta" aria-live="polite">${nombreMes(mes)}</span>
      <button type="button" class="boton-icono" data-mes="1" aria-label="Mes siguiente" ${mes >= mesActual() ? "disabled" : ""}>${icono("derecha")}</button>
    </div>`;
}

function alertaPresupuesto(presupuesto, mesTexto) {
  if (!presupuesto) return "";
  const { clase } = clasificarPresupuesto(presupuesto);
  if (clase === "critico") {
    return `<div class="alerta alerta--critico" role="alert">${icono("x-circle")}
      <span><strong>Superaste tu presupuesto de ${mesTexto}</strong> por ${formatoMoneda(-Number(presupuesto.disponible))}.</span></div>`;
  }
  if (clase === "aviso") {
    return `<div class="alerta alerta--aviso">${icono("alerta")}
      <span><strong>Estás cerca del límite:</strong> te quedan ${formatoMoneda(presupuesto.disponible)} para ${mesTexto}.</span></div>`;
  }
  return "";
}

function variacion(actual, anterior, mesAnterior) {
  const nombreAnterior = nombreMesSolo(mesAnterior);
  if (!anterior) return `Sin datos de ${nombreAnterior}`;
  const cambio = Math.round(((actual - anterior) / anterior) * 100);
  if (cambio === 0) return `Igual que en ${nombreAnterior}`;
  return `${icono(cambio > 0 ? "sube" : "baja")}${cambio > 0 ? "+" : "−"}${Math.abs(cambio)} % vs. ${nombreAnterior}`;
}

function textoAhorro(ingresos, balance) {
  if (ingresos <= 0) return "Aún no hay ingresos este mes";
  if (balance < 0) return "Gastaste más de lo que ingresó";
  return `Ahorras el ${Math.round((balance / ingresos) * 100)} % de tus ingresos`;
}

function tablaCategorias(datos) {
  const total = datos.reduce((suma, d) => suma + d.valor, 0);
  const filas = [...datos]
    .sort((a, b) => b.valor - a.valor)
    .map((d) => `<tr><td>${escapar(d.etiqueta)}</td><td class="num">${formatoMoneda(d.valor)}</td><td class="num">${Math.round((d.valor / total) * 100)} %</td></tr>`)
    .join("");
  return `<div class="tabla-contenedor"><table class="tabla tabla--compacta">
    <thead><tr><th>Categoría</th><th class="num">Gastado</th><th class="num">Participación</th></tr></thead>
    <tbody>${filas}</tbody></table></div>`;
}

function tablaTendencia(grupos) {
  const filas = grupos
    .map(({ titulo, valores: [ingresos, gastos] }) =>
      `<tr><td>${titulo}</td><td class="num">${formatoMoneda(ingresos)}</td><td class="num">${formatoMoneda(gastos)}</td><td class="num">${formatoMoneda(ingresos - gastos)}</td></tr>`)
    .join("");
  return `<div class="tabla-contenedor"><table class="tabla tabla--compacta">
    <thead><tr><th>Mes</th><th class="num">Ingresos</th><th class="num">Gastos</th><th class="num">Balance</th></tr></thead>
    <tbody>${filas}</tbody></table></div>`;
}
