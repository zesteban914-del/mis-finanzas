// Vista "Metas de ahorro" (cuentas personales).
import { api } from "../api.js";
import { avisarCambio } from "../estado.js";
import { icono } from "../iconos.js";
import {
  barraProgreso, botonPrincipal, botonesEdicion, cabecera, cupoDelPlan, enlazarEdicion, estadoVacio,
} from "../componentes.js";
import { escapar, formatoFecha, formatoMoneda, hoyIso } from "../formato.js";
import { limite, puede } from "../sesion.js";
import { abrirDialogo, notificar } from "../ui.js";

export async function renderizar(contenedor) {
  const metas = await api.metas.listar();
  const ahorrado = metas.reduce((s, m) => s + Number(m.monto_ahorrado), 0);
  const objetivo = metas.reduce((s, m) => s + Number(m.monto_objetivo), 0);

  contenedor.innerHTML = `
    ${cabecera({
      titulo: "Metas de ahorro",
      subtitulo: metas.length
        ? `Llevas ${formatoMoneda(ahorrado)} de ${formatoMoneda(objetivo)} entre todas tus metas`
        : "Ponle nombre y fecha a lo que quieres lograr",
      acciones: botonPrincipal("nueva-meta", "Nueva meta"),
    })}
    ${puede("GESTIONAR") ? cupoDelPlan(metas.length, limite("metas"), "metas") : ""}
    ${
      metas.length
        ? `<div class="rejilla-tarjetas rejilla-tarjetas--ancha">${metas.map(tarjeta).join("")}</div>`
        : `<section class="tarjeta">${estadoVacio({
            icono: "alcancia",
            titulo: "Aún no tienes metas",
            texto: "Ejemplo: «Viaje a Cartagena», $2.000.000 para junio. Te mostramos cuánto ahorrar cada mes.",
            accion: botonPrincipal("nueva-meta", "Crear mi primera meta", "boton--secundario"),
          })}</section>`
    }`;

  contenedor.querySelectorAll("[data-accion='nueva-meta']").forEach((b) => b.addEventListener("click", () => formulario()));
  enlazarEdicion(contenedor, metas, { alEditar: (m) => formulario(m), alEliminar: (m) => eliminar(m) });
  contenedor.querySelectorAll("[data-aportar]").forEach((b) =>
    b.addEventListener("click", () => aportar(metas.find((m) => m.id === Number(b.dataset.aportar))))
  );
}

/** Cuánto ahorrar por mes para llegar a tiempo. */
function sugerenciaMensual(meta) {
  if (!meta.fecha_limite || meta.completada) return "";
  const hoy = new Date();
  const [a, m] = meta.fecha_limite.split("-").map(Number);
  const meses = Math.max(1, (a - hoy.getFullYear()) * 12 + (m - 1 - hoy.getMonth()));
  return `Ahorra <b>${formatoMoneda(Number(meta.faltante) / meses)}</b> al mes para lograrlo`;
}

function tarjeta(meta) {
  return `
    <article class="tarjeta tarjeta-meta ${meta.completada ? "es-completada" : ""}">
      <header class="tarjeta-cabecera" style="margin-bottom:0">
        <div class="meta-titulo">
          <span class="meta-icono">${icono(meta.completada ? "check" : "alcancia")}</span>
          <div>
            <h3 class="tarjeta-titulo">${escapar(meta.nombre)}</h3>
            <p class="tarjeta-subtitulo">${meta.fecha_limite ? `Para el ${formatoFecha(meta.fecha_limite)}` : "Sin fecha límite"}</p>
          </div>
        </div>
        ${botonesEdicion(meta.id, meta.nombre)}
      </header>
      <div class="limite-cifras">
        <b>${formatoMoneda(meta.monto_ahorrado)}</b>
        <span class="texto-tenue">de ${formatoMoneda(meta.monto_objetivo)}</span>
      </div>
      ${barraProgreso(meta.porcentaje / 100, meta.completada ? "bien" : "acento", `Progreso de ${escapar(meta.nombre)}`)}
      <div class="meta-pie">
        <span>${meta.completada ? "<b>¡Meta cumplida!</b>" : `<b>${meta.porcentaje} %</b> · faltan ${formatoMoneda(meta.faltante)}`}</span>
        ${!meta.completada && puede("GESTIONAR") ? `<button type="button" class="boton boton--secundario boton--sm" data-aportar="${meta.id}">${icono("mas")}Aportar</button>` : ""}
      </div>
      ${sugerenciaMensual(meta) ? `<p class="ayuda">${sugerenciaMensual(meta)}</p>` : ""}
    </article>`;
}

function formulario(actual = null) {
  abrirDialogo({
    titulo: actual ? "Editar meta" : "Nueva meta de ahorro",
    textoConfirmar: actual ? "Guardar cambios" : "Crear meta",
    contenido: `
      <label class="campo">
        <span class="campo-etiqueta">¿Para qué ahorras?</span>
        <input class="entrada" name="nombre" maxlength="80" placeholder="Ej. Viaje, fondo de emergencia, portátil" value="${escapar(actual?.nombre ?? "")}">
      </label>
      <div class="campos-fila">
        <label class="campo">
          <span class="campo-etiqueta">Monto objetivo</span>
          <span class="entrada-prefijo"><span>$</span>
            <input name="monto_objetivo" type="number" inputmode="decimal" step="any" placeholder="0" value="${actual ? Number(actual.monto_objetivo) : ""}">
          </span>
        </label>
        <label class="campo">
          <span class="campo-etiqueta">Fecha límite <span class="texto-tenue">(opcional)</span></span>
          <input class="entrada" name="fecha_limite" type="date" min="${hoyIso()}" value="${actual?.fecha_limite ?? ""}">
        </label>
      </div>`,
    alEnviar: async (datos) => {
      const cuerpo = {
        nombre: datos.get("nombre").trim(),
        monto_objetivo: Number(datos.get("monto_objetivo")),
        fecha_limite: datos.get("fecha_limite") || null,
      };
      if (actual) await api.metas.actualizar(actual.id, cuerpo);
      else await api.metas.crear(cuerpo);
      notificar(actual ? "Meta actualizada" : "Meta creada");
      avisarCambio();
    },
  });
}

function aportar(meta) {
  abrirDialogo({
    titulo: `Aportar a «${escapar(meta.nombre)}»`,
    descripcion: `Te faltan ${formatoMoneda(meta.faltante)} para cumplirla.`,
    textoConfirmar: "Aportar",
    contenido: `
      <label class="campo">
        <span class="campo-etiqueta">Monto del aporte</span>
        <span class="entrada-prefijo"><span>$</span><input name="monto" type="number" inputmode="decimal" step="any" placeholder="0"></span>
      </label>`,
    alEnviar: async (datos) => {
      const resultado = await api.metas.aportar(meta.id, Number(datos.get("monto")));
      notificar(resultado.completada ? `¡Cumpliste tu meta «${meta.nombre}»!` : "Aporte registrado");
      avisarCambio();
    },
  });
}

function eliminar(meta) {
  abrirDialogo({
    titulo: "¿Eliminar meta?",
    descripcion: `Se eliminará <b>${escapar(meta.nombre)}</b> y su progreso.`,
    textoConfirmar: "Eliminar",
    peligro: true,
    alEnviar: async () => {
      await api.metas.eliminar(meta.id);
      notificar("Meta eliminada");
      avisarCambio();
    },
  });
}
