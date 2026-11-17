// Cliente de la API REST. Es el único módulo que hace peticiones HTTP.
import { cerrarSesion, obtenerToken } from "./sesion.js";

export class ErrorApi extends Error {
  constructor(mensaje, estado) {
    super(mensaje);
    this.estado = estado;
  }
}

const NOMBRES_CAMPOS = {
  monto: "monto",
  fecha: "fecha",
  tipo: "tipo",
  categoria_id: "categoría",
  descripcion: "descripción",
  nombre: "nombre",
  email: "correo",
  contrasena: "contraseña",
  username: "correo",
  password: "contraseña",
  mes: "mes",
  limite: "límite",
};

function mensajeDeError(cuerpo, estado) {
  // Errores de negocio del backend: { "detalle": "..." } (400, 404, 409)
  if (cuerpo && typeof cuerpo.detalle === "string") return cuerpo.detalle;
  // Errores de tipo que valida FastAPI/Pydantic: { "detail": [...] } (422)
  if (cuerpo && Array.isArray(cuerpo.detail) && cuerpo.detail.length) {
    const campo = cuerpo.detail[0].loc?.at(-1);
    return `Revisa el campo «${NOMBRES_CAMPOS[campo] ?? campo}»: falta o no tiene un valor válido`;
  }
  if (estado >= 500) return "Error interno del servidor. Revisa que la base de datos esté encendida.";
  return "No se pudo completar la operación";
}

async function solicitar(metodo, ruta, datos, { formulario = false } = {}) {
  const encabezados = {};
  const token = obtenerToken();
  if (token) encabezados.Authorization = `Bearer ${token}`;
  let cuerpoPeticion;
  if (formulario) {
    cuerpoPeticion = new URLSearchParams(datos);
  } else if (datos) {
    encabezados["Content-Type"] = "application/json";
    cuerpoPeticion = JSON.stringify(datos);
  }

  let respuesta;
  try {
    respuesta = await fetch(ruta, { method: metodo, headers: encabezados, body: cuerpoPeticion });
  } catch {
    throw new ErrorApi("No hay conexión con el servidor. ¿Está corriendo la API?", 0);
  }
  if (respuesta.status === 204) return null;
  const cuerpo = await respuesta.json().catch(() => null);
  if (!respuesta.ok) {
    const mensaje = mensajeDeError(cuerpo, respuesta.status);
    // Sesión vencida o cuenta desactivada: se vuelve a la pantalla de ingreso.
    if (respuesta.status === 401 && token) cerrarSesion(mensaje);
    throw new ErrorApi(mensaje, respuesta.status);
  }
  return cuerpo;
}

function consulta(parametros) {
  const busqueda = new URLSearchParams();
  for (const [clave, valor] of Object.entries(parametros)) {
    if (valor !== "" && valor !== null && valor !== undefined) busqueda.set(clave, valor);
  }
  const texto = busqueda.toString();
  return texto ? `?${texto}` : "";
}

export const api = {
  auth: {
    // Formato OAuth2 estándar: el correo va en "username".
    iniciarSesion: (email, contrasena) =>
      solicitar("POST", "/auth/login", { username: email, password: contrasena }, { formulario: true }),
    registrarse: (datos) => solicitar("POST", "/auth/registro", datos),
    miCuenta: () => solicitar("GET", "/auth/yo"),
  },
  admin: {
    usuarios: () => solicitar("GET", "/admin/usuarios"),
    estadisticas: () => solicitar("GET", "/admin/estadisticas"),
    actualizarUsuario: (id, cambios) => solicitar("PATCH", `/admin/usuarios/${id}`, cambios),
  },
  categorias: {
    listar: () => solicitar("GET", "/categorias"),
    crear: (datos) => solicitar("POST", "/categorias", datos),
    actualizar: (id, datos) => solicitar("PUT", `/categorias/${id}`, datos),
    eliminar: (id) => solicitar("DELETE", `/categorias/${id}`),
  },
  movimientos: {
    listar: (filtros = {}) => solicitar("GET", `/movimientos${consulta(filtros)}`),
    crear: (datos) => solicitar("POST", "/movimientos", datos),
    actualizar: (id, datos) => solicitar("PUT", `/movimientos/${id}`, datos),
    eliminar: (id) => solicitar("DELETE", `/movimientos/${id}`),
  },
  presupuestos: {
    listar: () => solicitar("GET", "/presupuestos"),
    crear: (datos) => solicitar("POST", "/presupuestos", datos),
    actualizar: (id, datos) => solicitar("PUT", `/presupuestos/${id}`, datos),
    eliminar: (id) => solicitar("DELETE", `/presupuestos/${id}`),
    estado: (mes) => solicitar("GET", `/presupuestos/${mes}/estado`),
  },
  reportes: {
    saldo: () => solicitar("GET", "/reportes/saldo"),
    resumenMensual: (mes) => solicitar("GET", `/reportes/resumen-mensual${consulta({ mes })}`),
  },
};
