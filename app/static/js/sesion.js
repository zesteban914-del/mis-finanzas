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
export const esNegocio = () => sesion?.usuario?.tipo_cuenta === "NEGOCIO";
export const esPro = () => sesion?.usuario?.plan === "PRO";
/** ¿El usuario puede hacer esta acción? (lista que envía el backend en /auth/yo) */
export const puede = (permiso) => sesion?.usuario?.permisos?.includes(permiso) ?? false;
/** Límite numérico del plan actual (recurrentes, metas, cajas, miembros). */
export const limite = (recurso) => sesion?.usuario?.limites?.[recurso] ?? 0;
/** ¿Su tipo de cuenta tiene este módulo? (METAS, CAJAS, EQUIPO, COMPROBANTES) */
export const tieneFuncion = (funcion) => sesion?.usuario?.funciones?.includes(funcion) ?? false;

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
