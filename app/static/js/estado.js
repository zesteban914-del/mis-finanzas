// Estado compartido entre vistas y un canal para avisar que hay que volver a pintar.
import { mesActual } from "./formato.js";

export const estado = {
  mes: mesActual(), // mes que muestra el panel (AAAA-MM)
};

export const bus = new EventTarget();

/** Se llama después de crear, editar o eliminar algo para refrescar la vista actual. */
export const avisarCambio = () => bus.dispatchEvent(new Event("refrescar"));
