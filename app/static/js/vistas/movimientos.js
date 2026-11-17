// Vista "Movimientos": tabla con filtros por fecha, categoría y tipo.
import { api } from "../api.js";
import { avisarCambio } from "../estado.js";
import { icono } from "../iconos.js";
import { botonNuevoMovimiento, cabecera, estadoVacio, insigniaTipo, montoMovimiento } from "../componentes.js";
import { escapar, formatoFecha, formatoMoneda, formatoMontoConSigno, hoyIso } from "../formato.js";
import { abrirDialogo, notificar } from "../ui.js";
import { abrirFormularioMovimiento } from "./formulario-movimiento.js";

const FILTROS_VACIOS = { fecha_inicio: "", fecha_fin: "", categoria_id: "", tipo: "" };
const filtros = { ...FILTROS_VACIOS };

export function establecerFiltros(nuevos) {
  Object.assign(filtros, FILTROS_VACIOS, nuevos);
}

export async function renderizar(contenedor) {
  const categorias = await api.categorias.listar();
  let movimientos = [];
  let errorFiltro = "";
  try {
    // Fechas y categoría se filtran en el servidor; el tipo, en el navegador.
    const { tipo, ...filtrosServidor } = filtros;
    movimientos = await api.movimientos.listar(filtrosServidor);
  } catch (error) {
    if (error.estado !== 400) throw error;
    errorFiltro = error.message;
  }

  const nombres = new Map(categorias.map((c) => [c.id, c.nombre]));
  const visibles = filtros.tipo ? movimientos.filter((m) => m.tipo === filtros.tipo) : movimientos;
  const sumar = (tipo) => visibles.filter((m) => m.tipo === tipo).reduce((suma, m) => suma + Number(m.monto), 0);
  const ingresos = sumar("INGRESO");
  const gastos = sumar("GASTO");
  const hayFiltros = Object.values(filtros).some(Boolean);
  const seleccionado = (a, b) => (String(a) === String(b) ? "selected" : "");

  contenedor.innerHTML = `
    ${cabecera({ titulo: "Movimientos", subtitulo: "Todos tus ingresos y gastos registrados", acciones: botonNuevoMovimiento() })}

    <section class="tarjeta tarjeta--tabla">
      <form class="filtros" aria-label="Filtros de movimientos">
        <label class="campo">
          <span class="campo-etiqueta">Desde</span>
          <input class="entrada" type="date" name="fecha_inicio" value="${filtros.fecha_inicio}" max="${hoyIso()}">
        </label>
        <label class="campo">
          <span class="campo-etiqueta">Hasta</span>
          <input class="entrada" type="date" name="fecha_fin" value="${filtros.fecha_fin}" max="${hoyIso()}">
        </label>
        <label class="campo">
          <span class="campo-etiqueta">Categoría</span>
          <select class="entrada" name="categoria_id">
            <option value="">Todas las categorías</option>
            ${categorias.map((c) => `<option value="${c.id}" ${seleccionado(c.id, filtros.categoria_id)}>${escapar(c.nombre)}</option>`).join("")}
          </select>
        </label>
        <label class="campo">
          <span class="campo-etiqueta">Tipo</span>
          <select class="entrada" name="tipo">
            <option value="">Ingresos y gastos</option>
            <option value="INGRESO" ${seleccionado("INGRESO", filtros.tipo)}>Solo ingresos</option>
            <option value="GASTO" ${seleccionado("GASTO", filtros.tipo)}>Solo gastos</option>
          </select>
        </label>
        <button type="button" class="boton boton--fantasma" data-accion="limpiar" ${hayFiltros ? "" : "disabled"}>${icono("x")}Limpiar</button>
      </form>

      ${errorFiltro ? `<p class="aviso-filtro" role="alert">${icono("alerta")}${escapar(errorFiltro)}</p>` : ""}

      <div class="resumen-filtro">
        <span><b>${visibles.length}</b> ${visibles.length === 1 ? "movimiento" : "movimientos"}</span>
        <span><i style="background:var(--serie-ingreso)"></i>Ingresos <b>${formatoMoneda(ingresos)}</b></span>
        <span><i style="background:var(--serie-gasto)"></i>Gastos <b>${formatoMoneda(gastos)}</b></span>
        <span>Balance <b>${formatoMoneda(ingresos - gastos)}</b></span>
      </div>

      ${
        visibles.length
          ? tabla(visibles, nombres)
          : estadoVacio({
              titulo: hayFiltros ? "Ningún movimiento coincide con los filtros" : "Aún no tienes movimientos",
              texto: hayFiltros ? "Prueba con otro rango de fechas o con otra categoría." : "Registra tu primer ingreso o gasto para empezar.",
              accion: hayFiltros ? "" : botonNuevoMovimiento("boton--secundario"),
            })
      }
    </section>`;

  contenedor.querySelector(".filtros").addEventListener("change", (evento) => {
    filtros[evento.target.name] = evento.target.value;
    renderizar(contenedor);
  });
  contenedor.querySelector("[data-accion='limpiar']").addEventListener("click", () => {
    establecerFiltros({});
    renderizar(contenedor);
  });

  const buscar = (id) => visibles.find((m) => m.id === Number(id));
  contenedor.querySelectorAll("[data-editar]").forEach((boton) =>
    boton.addEventListener("click", () => abrirFormularioMovimiento(buscar(boton.dataset.editar)))
  );
  contenedor.querySelectorAll("[data-eliminar]").forEach((boton) =>
    boton.addEventListener("click", () => confirmarEliminacion(buscar(boton.dataset.eliminar), nombres))
  );
}

function tabla(movimientos, nombres) {
  const filas = movimientos
    .map(
      (m) => `
      <tr>
        <td class="celda-fecha">${formatoFecha(m.fecha)}</td>
        <td class="celda-descripcion">${m.descripcion ? escapar(m.descripcion) : '<span class="texto-tenue">Sin descripción</span>'}</td>
        <td class="celda-categoria"><span class="chip">${escapar(nombres.get(m.categoria_id) ?? "—")}</span></td>
        <td class="celda-tipo">${insigniaTipo(m.tipo)}</td>
        <td class="num">${montoMovimiento(m)}</td>
        <td class="acciones">
          <button type="button" class="boton-icono" data-editar="${m.id}" aria-label="Editar movimiento" title="Editar">${icono("lapiz")}</button>
          <button type="button" class="boton-icono boton-icono--peligro" data-eliminar="${m.id}" aria-label="Eliminar movimiento" title="Eliminar">${icono("papelera")}</button>
        </td>
      </tr>`
    )
    .join("");
  return `
    <div class="tabla-contenedor">
      <table class="tabla tabla--movimientos">
        <thead>
          <tr><th>Fecha</th><th>Descripción</th><th>Categoría</th><th>Tipo</th><th class="num">Monto</th><th class="acciones"><span class="sr-only">Acciones</span></th></tr>
        </thead>
        <tbody>${filas}</tbody>
      </table>
    </div>`;
}

function confirmarEliminacion(movimiento, nombres) {
  const nombre = escapar(movimiento.descripcion || nombres.get(movimiento.categoria_id) || "este movimiento");
  abrirDialogo({
    titulo: "¿Eliminar movimiento?",
    descripcion: `Se eliminará <b>${nombre}</b> (${formatoMontoConSigno(movimiento.monto, movimiento.tipo)}). Esta acción no se puede deshacer.`,
    textoConfirmar: "Eliminar",
    peligro: true,
    alEnviar: async () => {
      await api.movimientos.eliminar(movimiento.id);
      notificar("Movimiento eliminado");
      avisarCambio();
    },
  });
}
