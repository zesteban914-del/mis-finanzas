// Gráficos hechos con HTML y CSS (sin librerías externas), con tooltip al pasar el mouse.
import { conTooltip } from "./ui.js";
import { escapar, formatoCompacto, formatoMoneda } from "./formato.js";

const filaTooltip = (nombre, colorVar, valor, formato = formatoMoneda) =>
  `<div class="tooltip-fila"><span><i style="background:var(${colorVar})"></i>${nombre}</span><b>${formato(valor)}</b></div>`;

/**
 * Barras horizontales ordenadas de mayor a menor.
 * datos: [{ etiqueta, valor }]
 */
export function barrasHorizontales(contenedor, datos, { colorVar = "--serie-gasto", nombreSerie = "Gastado" } = {}) {
  const ordenados = [...datos].sort((a, b) => b.valor - a.valor);
  const maximo = Math.max(...ordenados.map((d) => d.valor), 1);
  const total = ordenados.reduce((suma, d) => suma + d.valor, 0);

  contenedor.innerHTML = `<div class="barras-h" role="list">${ordenados
    .map(
      (d, i) => `
      <div class="barra-h" role="listitem" tabindex="0" aria-label="${escapar(d.etiqueta)}: ${formatoMoneda(d.valor)}">
        <span class="barra-h-etiqueta">${escapar(d.etiqueta)}</span>
        <span class="barra-h-pista"><span class="barra-h-relleno" style="width:${(d.valor / maximo) * 100}%;background:var(${colorVar});animation-delay:${i * 40}ms"></span></span>
        <span class="barra-h-valor">${formatoMoneda(d.valor)}</span>
      </div>`
    )
    .join("")}</div>`;

  contenedor.querySelectorAll(".barra-h").forEach((fila, i) => {
    const d = ordenados[i];
    const porcentaje = total ? Math.round((d.valor / total) * 100) : 0;
    conTooltip(
      fila,
      `<strong>${escapar(d.etiqueta)}</strong>${filaTooltip(nombreSerie, colorVar, d.valor)}<div class="tooltip-nota">${porcentaje} % del total del mes</div>`
    );
  });
}

/** Escala "redonda" para el eje Y: 0, 1 M, 2 M, 3 M... en lugar de 0, 873.211... */
function escalaRedonda(maximo, divisiones = 4) {
  const bruto = maximo / divisiones;
  const magnitud = 10 ** Math.floor(Math.log10(bruto));
  const razon = bruto / magnitud;
  const factor = razon <= 1 ? 1 : razon <= 2 ? 2 : razon <= 2.5 ? 2.5 : razon <= 5 ? 5 : 10;
  const paso = factor * magnitud;
  return { paso, tope: Math.ceil(maximo / paso) * paso };
}

const balance = (g) => `Balance: ${formatoMoneda(g.valores[0] - g.valores[1])}`;

/**
 * Columnas agrupadas (una columna por serie dentro de cada grupo).
 * grupos: [{ etiqueta, titulo, valores: [n, n], actual? }]
 * series: [{ nombre, colorVar }]
 * opciones: por defecto muestra pesos; para cantidades usar
 *   { formatoValor: (n) => n, formatoEje: (n) => n, enteros: true, nota: null }
 */
export function columnasAgrupadas(contenedor, grupos, series, opciones = {}) {
  const {
    formatoValor = formatoMoneda,
    formatoEje = formatoCompacto,
    enteros = false,
    nota = balance,
    descripcion = "Comparación de ingresos y gastos por mes",
  } = opciones;
  const maximo = Math.max(0, ...grupos.flatMap((g) => g.valores));
  const escala = escalaRedonda(maximo || (enteros ? 4 : 1000));
  // Con cantidades (cuentas, movimientos) el eje no debe mostrar 0,5 o 2,5.
  const paso = enteros ? Math.max(1, Math.ceil(escala.paso)) : escala.paso;
  const tope = enteros ? Math.max(paso, Math.ceil(maximo / paso) * paso) : escala.tope;
  const marcas = [];
  for (let valor = 0; valor <= tope + paso / 2; valor += paso) marcas.push(valor);
  const altura = (valor) => `${(valor / tope) * 100}%`;

  contenedor.innerHTML = `
    <div class="columnas" style="--grupos:${grupos.length}" role="img" aria-label="${escapar(descripcion)}. Usa la vista de tabla para ver los valores.">
      <div class="columnas-y" aria-hidden="true">
        ${marcas.map((v) => `<span style="bottom:${altura(v)}">${formatoEje(v)}</span>`).join("")}
      </div>
      <div class="columnas-trazado">
        ${marcas.map((v) => `<span class="columnas-linea" style="bottom:${altura(v)}"></span>`).join("")}
        <div class="columnas-grupos">
          ${grupos
            .map(
              (g, i) => `
            <div class="columnas-grupo" tabindex="0" aria-label="${escapar(g.titulo)}">
              ${g.valores
                .map(
                  (v, s) =>
                    `<span class="columna" style="height:${altura(v)};background:var(${series[s].colorVar});animation-delay:${i * 50}ms"></span>`
                )
                .join("")}
            </div>`
            )
            .join("")}
        </div>
      </div>
      <span></span>
      <div class="columnas-x" aria-hidden="true">
        ${grupos.map((g) => `<span class="${g.actual ? "actual" : ""}">${escapar(g.etiqueta)}</span>`).join("")}
      </div>
    </div>`;

  contenedor.querySelectorAll(".columnas-grupo").forEach((columna, i) => {
    const g = grupos[i];
    conTooltip(
      columna,
      `<strong>${escapar(g.titulo)}</strong>
       ${g.valores.map((v, s) => filaTooltip(series[s].nombre, series[s].colorVar, v, formatoValor)).join("")}
       ${nota ? `<div class="tooltip-nota">${nota(g)}</div>` : ""}`
    );
  });
}
