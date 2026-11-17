// Vista "Recurrentes": pagos e ingresos que se repiten cada mes y se registran solos.
import { api } from "../api.js";
import { avisarCambio } from "../estado.js";
import { icono } from "../iconos.js";
import {
  botonPrincipal, botonesEdicion, cabecera, cupoDelPlan, enlazarEdicion, estadoVacio, insigniaTipo, montoMovimiento,
} from "../componentes.js";
import { desplazarMes, escapar, formatoFecha, formatoMoneda, mesActual, nombreMes } from "../formato.js";
import { limite, puede, tieneFuncion } from "../sesion.js";
import { abrirDialogo, notificar } from "../ui.js";

const DIAS = Array.from({ length: 28 }, (_, i) => i + 1);

export async function renderizar(contenedor) {
  const conCajas = tieneFuncion("CAJAS");
  const [recurrentes, categorias, cajas] = await Promise.all([
    api.recurrentes.listar(),
    api.categorias.listar(),
    conCajas ? api.cajas.listar() : Promise.resolve([]),
  ]);
  const nombres = new Map(categorias.map((c) => [c.id, c.nombre]));
  const activos = recurrentes.filter((r) => r.activo);
  const total = (tipo) => activos.filter((r) => r.tipo === tipo).reduce((s, r) => s + Number(r.monto), 0);

  contenedor.innerHTML = `
    ${cabecera({
      titulo: "Recurrentes",
      subtitulo: "Arriendo, salario, suscripciones… se registran solos cada mes al abrir la aplicación",
      acciones: botonPrincipal("nuevo-recurrente", "Nuevo recurrente"),
    })}
    ${puede("GESTIONAR") ? cupoDelPlan(recurrentes.length, limite("recurrentes"), "recurrentes") : ""}
    <section class="tarjeta tarjeta--tabla">
      <div class="resumen-filtro">
        <span><b>${activos.length}</b> activos</span>
        <span><i style="background:var(--serie-ingreso)"></i>Ingresos fijos al mes <b>${formatoMoneda(total("INGRESO"))}</b></span>
        <span><i style="background:var(--serie-gasto)"></i>Gastos fijos al mes <b>${formatoMoneda(total("GASTO"))}</b></span>
      </div>
      ${
        recurrentes.length
          ? tabla(recurrentes, nombres)
          : estadoVacio({
              icono: "repetir",
              titulo: "Aún no tienes recurrentes",
              texto: "Agrega tus pagos fijos (arriendo, servicios, nómina) y deja de registrarlos a mano cada mes.",
              accion: botonPrincipal("nuevo-recurrente", "Nuevo recurrente", "boton--secundario"),
            })
      }
    </section>`;

  contenedor.querySelectorAll("[data-accion='nuevo-recurrente']").forEach((b) =>
    b.addEventListener("click", () => formulario(categorias, cajas))
  );
  enlazarEdicion(contenedor, recurrentes, {
    alEditar: (r) => formulario(categorias, cajas, r),
    alEliminar: (r) => eliminar(r),
  });
  contenedor.querySelectorAll("[data-activar]").forEach((interruptor) =>
    interruptor.addEventListener("change", async () => {
      try {
        await api.recurrentes.actualizar(Number(interruptor.dataset.activar), { activo: interruptor.checked });
        notificar(interruptor.checked ? "Recurrente activado" : "Recurrente pausado");
        avisarCambio();
      } catch (error) {
        interruptor.checked = !interruptor.checked;
        notificar(error.message, "error");
      }
    })
  );
}

/** Fecha en que se registrará la próxima vez. */
function proximaFecha(r) {
  const mes = r.ultimo_mes_generado ? desplazarMes(r.ultimo_mes_generado, 1) : r.mes_inicio;
  return `${mes}-${String(r.dia_del_mes).padStart(2, "0")}`;
}

function tabla(recurrentes, nombres) {
  const editable = puede("GESTIONAR");
  const filas = recurrentes
    .map(
      (r) => `
      <tr class="${r.activo ? "" : "fila-inactiva"}">
        <td class="celda-descripcion">
          ${escapar(r.descripcion || nombres.get(r.categoria_id) || "Recurrente")}
          <small class="celda-autor">${escapar(nombres.get(r.categoria_id) ?? "")}</small>
        </td>
        <td class="celda-tipo">${insigniaTipo(r.tipo)}</td>
        <td>Día ${r.dia_del_mes} de cada mes</td>
        <td class="celda-fecha">${r.activo ? formatoFecha(proximaFecha(r)) : '<span class="texto-tenue">En pausa</span>'}</td>
        <td class="num">${montoMovimiento(r)}</td>
        <td>
          ${
            editable
              ? `<label class="interruptor" title="${r.activo ? "Pausar" : "Activar"}">
                   <input type="checkbox" data-activar="${r.id}" ${r.activo ? "checked" : ""}>
                   <span></span><span class="sr-only">Activo</span>
                 </label>`
              : r.activo ? "Activo" : "En pausa"
          }
        </td>
        <td class="acciones">${botonesEdicion(r.id, r.descripcion || "recurrente")}</td>
      </tr>`
    )
    .join("");
  return `
    <div class="tabla-contenedor">
      <table class="tabla tabla--recurrentes">
        <thead><tr><th>Concepto</th><th>Tipo</th><th>Frecuencia</th><th>Próximo registro</th><th class="num">Monto</th><th>Activo</th><th class="acciones"><span class="sr-only">Acciones</span></th></tr></thead>
        <tbody>${filas}</tbody>
      </table>
    </div>`;
}

function formulario(categorias, cajas, actual = null) {
  if (!categorias.length) {
    notificar("Primero crea al menos una categoría", "advertencia");
    return;
  }
  const tipo = actual?.tipo ?? "GASTO";
  const opciones = (lista, valor) =>
    lista.map((x) => `<option value="${x.id}" ${x.id === valor ? "selected" : ""}>${escapar(x.nombre)}</option>`).join("");
  abrirDialogo({
    titulo: actual ? "Editar recurrente" : "Nuevo movimiento recurrente",
    descripcion: actual ? "Los cambios aplican a los próximos meses." : "Se registrará automáticamente el día que elijas de cada mes.",
    textoConfirmar: actual ? "Guardar cambios" : "Crear recurrente",
    contenido: `
      ${
        actual
          ? ""
          : `<div class="segmentado">
               <label class="segmento segmento--gasto"><input type="radio" name="tipo" value="GASTO" ${tipo === "GASTO" ? "checked" : ""}><span>${icono("flecha-gasto")}Gasto</span></label>
               <label class="segmento segmento--ingreso"><input type="radio" name="tipo" value="INGRESO" ${tipo === "INGRESO" ? "checked" : ""}><span>${icono("flecha-ingreso")}Ingreso</span></label>
             </div>`
      }
      <label class="campo">
        <span class="campo-etiqueta">Monto</span>
        <span class="entrada-prefijo"><span>$</span>
          <input name="monto" type="number" inputmode="decimal" step="any" placeholder="0" value="${actual ? Number(actual.monto) : ""}">
        </span>
      </label>
      <label class="campo">
        <span class="campo-etiqueta">Concepto</span>
        <input class="entrada" name="descripcion" maxlength="255" placeholder="Ej. Arriendo, Netflix, Nómina" value="${escapar(actual?.descripcion ?? "")}">
      </label>
      <div class="campos-fila">
        <label class="campo">
          <span class="campo-etiqueta">Día de cada mes</span>
          <select class="entrada" name="dia_del_mes">${DIAS.map((d) => `<option value="${d}" ${d === (actual?.dia_del_mes ?? 1) ? "selected" : ""}>Día ${d}</option>`).join("")}</select>
        </label>
        <label class="campo">
          <span class="campo-etiqueta">Categoría</span>
          <select class="entrada" name="categoria_id">${opciones(categorias, actual?.categoria_id)}</select>
        </label>
      </div>
      ${
        actual
          ? ""
          : `<div class="campos-fila">
               ${
                 cajas.length
                   ? `<label class="campo"><span class="campo-etiqueta">Caja</span>
                        <select class="entrada" name="caja_id"><option value="">Sin caja</option>${opciones(cajas)}</select></label>`
                   : ""
               }
               <label class="campo">
                 <span class="campo-etiqueta">Empieza en</span>
                 <select class="entrada" name="mes_inicio">
                   ${[0, 1, 2, 3, 4, 5].map((n) => desplazarMes(mesActual(), -n)).map((m) => `<option value="${m}">${nombreMes(m)}</option>`).join("")}
                 </select>
               </label>
             </div>
             <p class="ayuda">Si eliges un mes anterior, se registran también los meses que ya pasaron.</p>`
      }`,
    alEnviar: async (datos) => {
      const cuerpo = {
        monto: Number(datos.get("monto")),
        descripcion: datos.get("descripcion").trim(),
        dia_del_mes: Number(datos.get("dia_del_mes")),
        categoria_id: Number(datos.get("categoria_id")),
      };
      if (actual) {
        await api.recurrentes.actualizar(actual.id, cuerpo);
        notificar("Recurrente actualizado");
      } else {
        await api.recurrentes.crear({
          ...cuerpo,
          tipo: datos.get("tipo"),
          caja_id: datos.get("caja_id") ? Number(datos.get("caja_id")) : null,
          mes_inicio: datos.get("mes_inicio"),
        });
        const { movimientos_creados: creados } = await api.recurrentes.generar();
        notificar(creados ? `Recurrente creado: se registraron ${creados} movimientos pendientes` : "Recurrente creado");
      }
      avisarCambio();
    },
  });
}

function eliminar(recurrente) {
  abrirDialogo({
    titulo: "¿Eliminar recurrente?",
    descripcion: `<b>${escapar(recurrente.descripcion || "Este recurrente")}</b> dejará de registrarse. Los movimientos que ya se registraron se conservan.`,
    textoConfirmar: "Eliminar",
    peligro: true,
    alEnviar: async () => {
      await api.recurrentes.eliminar(recurrente.id);
      notificar("Recurrente eliminado");
      avisarCambio();
    },
  });
}
