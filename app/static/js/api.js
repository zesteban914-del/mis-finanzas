// Cliente de la API REST. Es el único módulo que hace peticiones HTTP.

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

async function solicitar(metodo, ruta, datos) {
  let respuesta;
  try {
    respuesta = await fetch(ruta, {
      method: metodo,
      headers: datos ? { "Content-Type": "application/json" } : {},
      body: datos ? JSON.stringify(datos) : undefined,
    });
  } catch {
    throw new ErrorApi("No hay conexión con el servidor. ¿Está corriendo la API?", 0);
  }
  if (respuesta.status === 204) return null;
  const cuerpo = await respuesta.json().catch(() => null);
  if (!respuesta.ok) throw new ErrorApi(mensajeDeError(cuerpo, respuesta.status), respuesta.status);
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
