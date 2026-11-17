// Formulario modal para registrar o editar un movimiento.
// Las reglas (monto > 0, sin fechas futuras, categoría existente) las valida el
// backend; aquí solo se muestran sus mensajes de error.
import { api } from "../api.js";
import { insigniaPro } from "../componentes.js";
import { avisarCambio } from "../estado.js";
import { escapar, hoyIso } from "../formato.js";
import { icono } from "../iconos.js";
import { esPro, puede, tieneFuncion } from "../sesion.js";
import { abrirDialogo, notificar } from "../ui.js";

export async function abrirFormularioMovimiento(movimiento = null) {
  const conCajas = tieneFuncion("CAJAS");
  const [categorias, cajas] = await Promise.all([
    api.categorias.listar(),
    conCajas ? api.cajas.listar() : Promise.resolve([]),
  ]);
  if (!categorias.length) {
    notificar(
      puede("GESTIONAR")
        ? "Primero crea al menos una categoría para tus movimientos"
        : "Aún no hay categorías: pide al propietario que las cree",
      "advertencia"
    );
    if (puede("GESTIONAR")) location.hash = "#/categorias";
    return;
  }

  const tipo = movimiento?.tipo ?? "GASTO";
  const opciones = (lista, actual) =>
    lista.map((x) => `<option value="${x.id}" ${x.id === actual ? "selected" : ""}>${escapar(x.nombre)}</option>`).join("");
  const conComprobante = !movimiento && tieneFuncion("COMPROBANTES") && esPro();

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
          <select class="entrada" name="categoria_id">${opciones(categorias, movimiento?.categoria_id)}</select>
        </label>
      </div>
      ${
        conCajas && cajas.length
          ? `<label class="campo">
               <span class="campo-etiqueta">Caja <span class="texto-tenue">(de dónde sale o a dónde entra)</span></span>
               <select class="entrada" name="caja_id">
                 <option value="">Sin caja</option>
                 ${opciones(cajas, movimiento?.caja_id)}
               </select>
             </label>`
          : ""
      }
      <label class="campo">
        <span class="campo-etiqueta">Descripción <span class="texto-tenue">(opcional)</span></span>
        <input class="entrada" name="descripcion" maxlength="255" placeholder="Ej. Mercado de la semana" value="${escapar(movimiento?.descripcion ?? "")}">
      </label>
      ${
        conComprobante
          ? `<label class="campo">
               <span class="campo-etiqueta">Comprobante ${insigniaPro()} <span class="texto-tenue">(opcional: foto o PDF, máx. 2 MB)</span></span>
               <input class="entrada entrada-archivo" type="file" name="archivo" accept="image/jpeg,image/png,image/webp,application/pdf">
             </label>`
          : ""
      }`,
    alEnviar: async (datos) => {
      const cuerpo = {
        tipo: datos.get("tipo"),
        monto: Number(datos.get("monto")),
        fecha: datos.get("fecha"),
        categoria_id: Number(datos.get("categoria_id")),
        descripcion: datos.get("descripcion").trim(),
      };
      if (conCajas && datos.has("caja_id")) cuerpo.caja_id = datos.get("caja_id") ? Number(datos.get("caja_id")) : null;

      if (movimiento) {
        await api.movimientos.actualizar(movimiento.id, cuerpo);
        notificar("Movimiento actualizado");
      } else {
        const respuesta = await api.movimientos.crear(cuerpo);
        const archivo = datos.get("archivo");
        if (archivo && archivo.size) {
          try {
            await api.movimientos.subirComprobante(respuesta.movimiento.id, archivo);
          } catch (error) {
            notificar(`El movimiento se guardó, pero no el comprobante: ${error.message}`, "advertencia");
          }
        }
        notificar(cuerpo.tipo === "INGRESO" ? "Ingreso registrado" : "Gasto registrado");
        respuesta.alertas.forEach((alerta) => notificar(alerta, "advertencia"));
      }
      avisarCambio();
    },
  });
}
