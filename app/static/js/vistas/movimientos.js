// Vista "Movimientos": tabla con filtros. En negocios suma caja, autor y comprobante.
import { api } from "../api.js";
import { avisarCambio } from "../estado.js";
import { icono } from "../iconos.js";
import { botonNuevoMovimiento, cabecera, estadoVacio, insigniaTipo, montoMovimiento } from "../componentes.js";
import { escapar, formatoFecha, formatoMoneda, formatoMontoConSigno, hoyIso } from "../formato.js";
import { esPro, puede, tieneFuncion } from "../sesion.js";
import { abrirArchivo, abrirDialogo, notificar } from "../ui.js";
import { abrirFormularioMovimiento } from "./formulario-movimiento.js";

const FILTROS_VACIOS = { fecha_inicio: "", fecha_fin: "", categoria_id: "", caja_id: "", tipo: "" };
const filtros = { ...FILTROS_VACIOS };

export function establecerFiltros(nuevos) {
  Object.assign(filtros, FILTROS_VACIOS, nuevos);
}

export async function renderizar(contenedor) {
  const conCajas = tieneFuncion("CAJAS");
  const conComprobantes = tieneFuncion("COMPROBANTES");
  const [categorias, cajas] = await Promise.all([
    api.categorias.listar(),
    conCajas ? api.cajas.listar() : Promise.resolve([]),
  ]);
  let movimientos = [];
  let errorFiltro = "";
  try {
    // Fechas, categoría y caja se filtran en el servidor; el tipo, en el navegador.
    const { tipo, ...filtrosServidor } = filtros;
    movimientos = await api.movimientos.listar(filtrosServidor);
  } catch (error) {
    if (error.estado !== 400) throw error;
    errorFiltro = error.message;
  }

  const nombres = new Map(categorias.map((c) => [c.id, c.nombre]));
  const nombresCaja = new Map(cajas.map((c) => [c.id, c.nombre]));
  const visibles = filtros.tipo ? movimientos.filter((m) => m.tipo === filtros.tipo) : movimientos;
  const sumar = (tipo) => visibles.filter((m) => m.tipo === tipo).reduce((suma, m) => suma + Number(m.monto), 0);
  const ingresos = sumar("INGRESO");
  const gastos = sumar("GASTO");
  const hayFiltros = Object.values(filtros).some(Boolean);
  const seleccionado = (a, b) => (String(a) === String(b) ? "selected" : "");
  const opcionesTabla = { nombres, nombresCaja, conCajas, conComprobantes };

  contenedor.innerHTML = `
    ${cabecera({
      titulo: "Movimientos",
      subtitulo: puede("GESTIONAR") ? "Todos los ingresos y gastos registrados" : "Ingresos y gastos registrados en la cuenta",
      acciones: botonNuevoMovimiento(),
    })}

    <section class="tarjeta tarjeta--tabla">
      <form class="filtros ${conCajas ? "filtros--con-caja" : ""}" aria-label="Filtros de movimientos">
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
        ${
          conCajas
            ? `<label class="campo">
                 <span class="campo-etiqueta">Caja</span>
                 <select class="entrada" name="caja_id">
                   <option value="">Todas las cajas</option>
                   ${cajas.map((c) => `<option value="${c.id}" ${seleccionado(c.id, filtros.caja_id)}>${escapar(c.nombre)}</option>`).join("")}
                 </select>
               </label>`
            : ""
        }
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
          ? tabla(visibles, opcionesTabla)
          : estadoVacio({
              titulo: hayFiltros ? "Ningún movimiento coincide con los filtros" : "Aún no hay movimientos",
              texto: hayFiltros ? "Prueba con otro rango de fechas, categoría o caja." : "Registra el primer ingreso o gasto para empezar.",
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
  contenedor.querySelectorAll("[data-comprobante]").forEach((boton) =>
    boton.addEventListener("click", () => gestionarComprobante(buscar(boton.dataset.comprobante)))
  );
}

function tabla(movimientos, { nombres, nombresCaja, conCajas, conComprobantes }) {
  const editar = puede("GESTIONAR");
  const filas = movimientos
    .map((m) => {
      const autor = m.registrado_por_nombre || (m.recurrente_id ? "Automático (recurrente)" : "");
      return `
      <tr>
        <td class="celda-fecha">${formatoFecha(m.fecha)}</td>
        <td class="celda-descripcion">
          ${m.descripcion ? escapar(m.descripcion) : '<span class="texto-tenue">Sin descripción</span>'}
          ${m.recurrente_id ? `<span class="marca-recurrente" title="Movimiento recurrente">${icono("repetir")}</span>` : ""}
          ${conCajas && autor ? `<small class="celda-autor">${escapar(autor)}</small>` : ""}
        </td>
        <td class="celda-categoria"><span class="chip">${escapar(nombres.get(m.categoria_id) ?? "—")}</span></td>
        ${conCajas ? `<td class="celda-caja">${m.caja_id ? escapar(nombresCaja.get(m.caja_id) ?? "—") : '<span class="texto-tenue">—</span>'}</td>` : ""}
        <td class="celda-tipo">${insigniaTipo(m.tipo)}</td>
        <td class="num">${montoMovimiento(m)}</td>
        <td class="acciones">
          ${botonComprobante(m, conComprobantes)}
          ${
            editar
              ? `<button type="button" class="boton-icono" data-editar="${m.id}" aria-label="Editar movimiento" title="Editar">${icono("lapiz")}</button>
                 <button type="button" class="boton-icono boton-icono--peligro" data-eliminar="${m.id}" aria-label="Eliminar movimiento" title="Eliminar">${icono("papelera")}</button>`
              : ""
          }
        </td>
      </tr>`;
    })
    .join("");
  return `
    <div class="tabla-contenedor">
      <table class="tabla tabla--movimientos">
        <thead>
          <tr>
            <th>Fecha</th><th>Descripción</th><th>Categoría</th>${conCajas ? "<th>Caja</th>" : ""}<th>Tipo</th>
            <th class="num">Monto</th><th class="acciones"><span class="sr-only">Acciones</span></th>
          </tr>
        </thead>
        <tbody>${filas}</tbody>
      </table>
    </div>`;
}

function botonComprobante(movimiento, conComprobantes) {
  if (!conComprobantes) return "";
  if (movimiento.tiene_comprobante) {
    return `<button type="button" class="boton-icono boton-icono--activo" data-comprobante="${movimiento.id}" aria-label="Ver comprobante" title="Ver comprobante">${icono("clip")}</button>`;
  }
  if (!puede("REGISTRAR_MOVIMIENTOS")) return "";
  return `<button type="button" class="boton-icono" data-comprobante="${movimiento.id}" aria-label="Adjuntar comprobante" title="Adjuntar comprobante">${icono("clip")}</button>`;
}

function gestionarComprobante(movimiento) {
  if (movimiento.tiene_comprobante) {
    abrirDialogo({
      titulo: "Comprobante adjunto",
      descripcion: `${escapar(movimiento.descripcion || "Movimiento")} · ${formatoMontoConSigno(movimiento.monto, movimiento.tipo)}`,
      contenido: puede("GESTIONAR")
        ? '<label class="casilla"><input type="checkbox" name="eliminar"><span>Eliminar el comprobante</span></label>'
        : "",
      textoConfirmar: "Abrir archivo",
      alEnviar: async (datos) => {
        if (datos.get("eliminar") === "on") {
          await api.movimientos.eliminarComprobante(movimiento.id);
          notificar("Comprobante eliminado");
          avisarCambio();
          return;
        }
        abrirArchivo(await api.movimientos.descargarComprobante(movimiento.id));
      },
    });
    return;
  }
  abrirDialogo({
    titulo: "Adjuntar comprobante",
    descripcion: esPro()
      ? "Foto o PDF de la factura o recibo (máximo 2 MB)."
      : "Los comprobantes son una función del plan Pro.",
    contenido: `<input class="entrada entrada-archivo" type="file" name="archivo" accept="image/jpeg,image/png,image/webp,application/pdf">`,
    textoConfirmar: "Subir",
    alEnviar: async (datos) => {
      const archivo = datos.get("archivo");
      if (!archivo || !archivo.size) throw new Error("Elige un archivo");
      await api.movimientos.subirComprobante(movimiento.id, archivo);
      notificar("Comprobante adjuntado");
      avisarCambio();
    },
  });
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
