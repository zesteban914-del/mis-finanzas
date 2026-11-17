// Sesión del usuario: token JWT y datos de la cuenta, guardados en el navegador.
import { bus } from "./estado.js";

const CLAVE = "mis-finanzas-sesion";

function leerGuardada() {
  try {
    return JSON.parse(localStorage.getItem(CLAVE));
  } catch {
    return null;
  }
}

let sesion = leerGuardada();

export const obtenerToken = () => sesion?.token ?? null;
export const usuarioActual = () => sesion?.usuario ?? null;
export const esAdministrador = () => sesion?.usuario?.rol === "ADMIN";

export function guardarSesion(token, usuario) {
  sesion = { token, usuario };
  try {
    localStorage.setItem(CLAVE, JSON.stringify(sesion));
  } catch {
    /* sin almacenamiento: la sesión dura mientras la pestaña esté abierta */
  }
}

export function actualizarUsuario(usuario) {
  if (sesion) guardarSesion(sesion.token, usuario);
}

/** motivo: texto opcional que se muestra en la pantalla de inicio de sesión. */
export function cerrarSesion(motivo = "") {
  sesion = null;
  try {
    localStorage.removeItem(CLAVE);
  } catch {
    /* nada que borrar */
  }
  bus.dispatchEvent(new CustomEvent("sesion-cerrada", { detail: { motivo } }));
}
