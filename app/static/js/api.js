// Cliente de la API REST. Es el único módulo que hace peticiones HTTP.
import { cerrarSesion, obtenerToken } from "./sesion.js";

export class ErrorApi extends Error {
  constructor(mensaje, estado) {
    super(mensaje);
    this.estado = estado; // 402 = la acción requiere el plan Pro
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
  dia_del_mes: "día del mes",
  monto_objetivo: "monto objetivo",
  monto_total: "monto",
  contraparte: "persona o empresa",
  rol_negocio: "rol",
  origen_id: "caja de origen",
  destino_id: "caja de destino",
  archivo: "archivo",
};

function mensajeDeError(cuerpo, estado) {
  // Errores de negocio del backend: { "detalle": "..." } (400, 401, 402, 403, 404, 409)
  if (cuerpo && typeof cuerpo.detalle === "string") return cuerpo.detalle;
  // Errores de tipo que valida FastAPI/Pydantic: { "detail": [...] } (422)
  if (cuerpo && Array.isArray(cuerpo.detail) && cuerpo.detail.length) {
    const campo = cuerpo.detail[0].loc?.at(-1);
    return `Revisa el campo «${NOMBRES_CAMPOS[campo] ?? campo}»: falta o no tiene un valor válido`;
  }
  if (estado >= 500) return "Error interno del servidor. Revisa que la base de datos esté encendida.";
  return "No se pudo completar la operación";
}

function nombreDeArchivo(encabezado, porDefecto) {
  const utf8 = /filename\*=UTF-8''([^;]+)/i.exec(encabezado || "");
  if (utf8) return decodeURIComponent(utf8[1]);
  const simple = /filename="?([^";]+)"?/i.exec(encabezado || "");
  return simple ? simple[1] : porDefecto;
}

/**
 * opciones.formulario: envía los datos como formulario (inicio de sesión OAuth2).
 * opciones.archivo: un FormData con un archivo adjunto.
 * opciones.descargar: devuelve { blob, nombre } en vez de JSON.
 */
async function solicitar(metodo, ruta, datos, { formulario = false, archivo = null, descargar = false } = {}) {
  const encabezados = {};
  const token = obtenerToken();
  if (token) encabezados.Authorization = `Bearer ${token}`;
  let cuerpoPeticion;
  if (archivo) {
    cuerpoPeticion = archivo;
  } else if (formulario) {
    cuerpoPeticion = new URLSearchParams(datos);
  } else if (datos !== undefined) {
    encabezados["Content-Type"] = "application/json";
    cuerpoPeticion = JSON.stringify(datos);
  }

  let respuesta;
  try {
    respuesta = await fetch(ruta, { method: metodo, headers: encabezados, body: cuerpoPeticion });
  } catch {
    throw new ErrorApi("No hay conexión con el servidor. ¿Está corriendo la API?", 0);
  }
  if (!respuesta.ok) {
    const cuerpo = await respuesta.json().catch(() => null);
    const mensaje = mensajeDeError(cuerpo, respuesta.status);
    // Sesión vencida o cuenta desactivada: se vuelve a la pantalla de ingreso.
    if (respuesta.status === 401 && token) cerrarSesion(mensaje);
    throw new ErrorApi(mensaje, respuesta.status);
  }
  if (descargar) {
    const nombre = nombreDeArchivo(respuesta.headers.get("Content-Disposition"), "archivo");
    return { blob: await respuesta.blob(), nombre };
  }
  if (respuesta.status === 204) return null;
  return respuesta.json();
}

function consulta(parametros) {
  const busqueda = new URLSearchParams();
  for (const [clave, valor] of Object.entries(parametros)) {
    if (valor !== "" && valor !== null && valor !== undefined) busqueda.set(clave, valor);
  }
  const texto = busqueda.toString();
  return texto ? `?${texto}` : "";
}

/** CRUD estándar de un recurso: listar, crear, actualizar (PATCH o PUT) y eliminar. */
const recurso = (base, metodoActualizar = "PATCH") => ({
  listar: (filtros = {}) => solicitar("GET", `${base}${consulta(filtros)}`),
  crear: (datos) => solicitar("POST", base, datos),
  actualizar: (id, datos) => solicitar(metodoActualizar, `${base}/${id}`, datos),
  eliminar: (id) => solicitar("DELETE", `${base}/${id}`),
});

export const api = {
  auth: {
    // Formato OAuth2 estándar: el correo va en "username".
    iniciarSesion: (email, contrasena) =>
      solicitar("POST", "/auth/login", { username: email, password: contrasena }, { formulario: true }),
    registrarse: (datos) => solicitar("POST", "/auth/registro", datos),
    opciones: () => solicitar("GET", "/auth/opciones-registro"),
    miCuenta: () => solicitar("GET", "/auth/yo"),
    actualizarPerfil: (datos) => solicitar("PATCH", "/auth/yo", datos),
    cambiarContrasena: (datos) => solicitar("PUT", "/auth/yo/contrasena", datos),
  },
  planes: {
    catalogo: () => solicitar("GET", "/planes"),
    solicitarPro: () => solicitar("POST", "/planes/solicitar-pro"),
  },
  admin: {
    usuarios: () => solicitar("GET", "/admin/usuarios"),
    estadisticas: () => solicitar("GET", "/admin/estadisticas"),
    actualizarUsuario: (id, cambios) => solicitar("PATCH", `/admin/usuarios/${id}`, cambios),
  },
  categorias: recurso("/categorias", "PUT"),
  movimientos: {
    ...recurso("/movimientos", "PUT"),
    subirComprobante: (id, archivoElegido) => {
      const datos = new FormData();
      datos.append("archivo", archivoElegido);
      return solicitar("POST", `/movimientos/${id}/comprobante`, null, { archivo: datos });
    },
    descargarComprobante: (id) => solicitar("GET", `/movimientos/${id}/comprobante`, undefined, { descargar: true }),
    eliminarComprobante: (id) => solicitar("DELETE", `/movimientos/${id}/comprobante`),
  },
  presupuestos: {
    ...recurso("/presupuestos", "PUT"),
    estado: (mes) => solicitar("GET", `/presupuestos/${mes}/estado`),
    porCategoria: (mes) => solicitar("GET", `/presupuestos/categorias${consulta({ mes })}`),
    definirCategoria: (categoriaId, limite) => solicitar("PUT", `/presupuestos/categorias/${categoriaId}`, { limite }),
    quitarCategoria: (categoriaId) => solicitar("DELETE", `/presupuestos/categorias/${categoriaId}`),
  },
  reportes: {
    saldo: () => solicitar("GET", "/reportes/saldo"),
    resumenMensual: (mes) => solicitar("GET", `/reportes/resumen-mensual${consulta({ mes })}`),
    exportar: (mes, formato) =>
      solicitar("GET", `/reportes/exportar${consulta({ mes, formato })}`, undefined, { descargar: true }),
  },
  recurrentes: {
    ...recurso("/recurrentes"),
    generar: () => solicitar("POST", "/recurrentes/generar"),
  },
  metas: {
    ...recurso("/metas"),
    aportar: (id, monto) => solicitar("POST", `/metas/${id}/aportes`, { monto }),
  },
  deudas: {
    ...recurso("/deudas"),
    abonar: (id, monto) => solicitar("POST", `/deudas/${id}/abonos`, { monto }),
  },
  cajas: {
    ...recurso("/cajas"),
    transferencias: () => solicitar("GET", "/cajas/transferencias"),
    transferir: (datos) => solicitar("POST", "/cajas/transferencias", datos),
  },
  equipo: recurso("/equipo"),
};
