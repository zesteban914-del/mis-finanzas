// Formulario modal para crear o editar un presupuesto mensual.
import { api } from "../api.js";
import { avisarCambio } from "../estado.js";
import { mesActual, nombreMes } from "../formato.js";
import { abrirDialogo, notificar } from "../ui.js";

export function abrirFormularioPresupuesto(presupuesto = null, mesSugerido = mesActual()) {
  abrirDialogo({
    titulo: presupuesto ? "Editar presupuesto" : "Nuevo presupuesto",
    descripcion: "Define cuánto quieres gastar como máximo en un mes. Te avisaremos si lo superas.",
    textoConfirmar: presupuesto ? "Guardar cambios" : "Crear presupuesto",
    contenido: `
      <label class="campo">
        <span class="campo-etiqueta">Mes</span>
        <input class="entrada" name="mes" type="month" placeholder="AAAA-MM" value="${presupuesto?.mes ?? mesSugerido}">
      </label>
      <label class="campo">
        <span class="campo-etiqueta">Límite de gasto</span>
        <span class="entrada-prefijo">
          <span>$</span>
          <input name="limite" type="number" inputmode="decimal" step="any" placeholder="0" value="${presupuesto ? Number(presupuesto.limite) : ""}">
        </span>
      </label>`,
    alEnviar: async (datos) => {
      const cuerpo = { mes: datos.get("mes").trim(), limite: Number(datos.get("limite")) };
      if (presupuesto) {
        await api.presupuestos.actualizar(presupuesto.id, cuerpo);
        notificar("Presupuesto actualizado");
      } else {
        await api.presupuestos.crear(cuerpo);
        notificar(`Presupuesto de ${nombreMes(cuerpo.mes)} creado`);
      }
      avisarCambio();
    },
  });
}
