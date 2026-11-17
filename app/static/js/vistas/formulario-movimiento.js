// Formulario modal para registrar o editar un movimiento.
// Las reglas (monto > 0, sin fechas futuras, categoría existente) las valida el
// backend; aquí solo se muestran sus mensajes de error.
import { api } from "../api.js";
import { avisarCambio } from "../estado.js";
import { escapar, hoyIso } from "../formato.js";
import { icono } from "../iconos.js";
import { abrirDialogo, notificar } from "../ui.js";

export async function abrirFormularioMovimiento(movimiento = null) {
  const categorias = await api.categorias.listar();
  if (!categorias.length) {
    notificar("Primero crea al menos una categoría para tus movimientos", "advertencia");
    location.hash = "#/categorias";
    return;
  }

  const tipo = movimiento?.tipo ?? "GASTO";
  const opciones = categorias
    .map((c) => `<option value="${c.id}" ${c.id === movimiento?.categoria_id ? "selected" : ""}>${escapar(c.nombre)}</option>`)
    .join("");

  abrirDialogo({
    titulo: movimiento ? "Editar movimiento" : "Nuevo movimiento",
    descripcion: movimiento ? "Corrige los datos y guarda los cambios." : "Registra un ingreso o un gasto.",
    textoConfirmar: movimiento ? "Guardar cambios" : "Registrar",
    contenido: `
      <fieldset class="campo">
        <legend class="campo-etiqueta sr-only">Tipo de movimiento</legend>
        <div class="segmentado">
          <label class="segmento segmento--gasto">
            <input type="radio" name="tipo" value="GASTO" ${tipo === "GASTO" ? "checked" : ""}>
            <span>${icono("flecha-gasto")}Gasto</span>
          </label>
          <label class="segmento segmento--ingreso">
            <input type="radio" name="tipo" value="INGRESO" ${tipo === "INGRESO" ? "checked" : ""}>
            <span>${icono("flecha-ingreso")}Ingreso</span>
          </label>
        </div>
      </fieldset>
      <label class="campo">
        <span class="campo-etiqueta">Monto</span>
        <span class="entrada-prefijo">
          <span>$</span>
          <input name="monto" type="number" inputmode="decimal" step="any" placeholder="0" value="${movimiento ? Number(movimiento.monto) : ""}">
        </span>
      </label>
      <div class="campos-fila">
        <label class="campo">
          <span class="campo-etiqueta">Fecha</span>
          <input class="entrada" name="fecha" type="date" max="${hoyIso()}" value="${movimiento?.fecha ?? hoyIso()}">
        </label>
        <label class="campo">
          <span class="campo-etiqueta">Categoría</span>
          <select class="entrada" name="categoria_id">${opciones}</select>
        </label>
      </div>
      <label class="campo">
        <span class="campo-etiqueta">Descripción <span class="texto-tenue">(opcional)</span></span>
        <input class="entrada" name="descripcion" maxlength="255" placeholder="Ej. Mercado de la semana" value="${escapar(movimiento?.descripcion ?? "")}">
      </label>`,
    alEnviar: async (datos) => {
      const cuerpo = {
        tipo: datos.get("tipo"),
        monto: Number(datos.get("monto")),
        fecha: datos.get("fecha"),
        categoria_id: Number(datos.get("categoria_id")),
        descripcion: datos.get("descripcion").trim(),
      };
      if (movimiento) {
        await api.movimientos.actualizar(movimiento.id, cuerpo);
        notificar("Movimiento actualizado");
      } else {
        const respuesta = await api.movimientos.crear(cuerpo);
        notificar(cuerpo.tipo === "INGRESO" ? "Ingreso registrado" : "Gasto registrado");
        if (respuesta.alerta_presupuesto) notificar(respuesta.alerta_presupuesto, "advertencia");
      }
      avisarCambio();
    },
  });
}
