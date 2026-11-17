// Formato de dinero y fechas en español de Colombia, y utilidades de meses.

const moneda = new Intl.NumberFormat("es-CO", {
  style: "currency",
  currency: "COP",
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
});

export const formatoMoneda = (valor) => moneda.format(Number(valor) || 0);

export function formatoMontoConSigno(valor, tipo) {
  const signo = tipo === "INGRESO" ? "+" : "−";
  return `${signo}${formatoMoneda(Math.abs(Number(valor)))}`;
}

export function formatoCompacto(valor) {
  const numero = Number(valor) || 0;
  const absoluto = Math.abs(numero);
  if (absoluto >= 1e6) return `$${(numero / 1e6).toLocaleString("es-CO", { maximumFractionDigits: 1 })} M`;
  if (absoluto >= 1e3) return `$${Math.round(numero / 1e3).toLocaleString("es-CO")} mil`;
  return `$${numero.toLocaleString("es-CO")}`;
}

const capitalizar = (texto) => texto.charAt(0).toUpperCase() + texto.slice(1);
const dosDigitos = (numero) => String(numero).padStart(2, "0");

function aFecha(iso) {
  const [anio, mes, dia] = iso.split("-").map(Number);
  return new Date(anio, mes - 1, dia || 1);
}

export const fechaIso = (fecha) =>
  `${fecha.getFullYear()}-${dosDigitos(fecha.getMonth() + 1)}-${dosDigitos(fecha.getDate())}`;
export const hoyIso = () => fechaIso(new Date());
export const mesActual = () => hoyIso().slice(0, 7);

export const formatoFecha = (iso) =>
  aFecha(iso).toLocaleDateString("es-CO", { day: "numeric", month: "short", year: "numeric" }).replace(".", "");
export const formatoFechaCorta = (iso) =>
  aFecha(iso).toLocaleDateString("es-CO", { day: "numeric", month: "short" }).replace(".", "");

/** "2026-11" → "Noviembre 2026" */
export const nombreMes = (mes) =>
  capitalizar(aFecha(mes).toLocaleDateString("es-CO", { month: "long" })) + ` ${mes.slice(0, 4)}`;
/** "2026-11" → "noviembre" */
export const nombreMesSolo = (mes) => aFecha(mes).toLocaleDateString("es-CO", { month: "long" });
/** "2026-11" → "Nov" */
export const nombreMesCorto = (mes) =>
  capitalizar(aFecha(mes).toLocaleDateString("es-CO", { month: "short" }).replace(".", ""));

export function desplazarMes(mes, cantidad) {
  const fecha = aFecha(mes);
  fecha.setMonth(fecha.getMonth() + cantidad);
  return fechaIso(fecha).slice(0, 7);
}

/** Los `cantidad` meses que terminan en `mes`, del más antiguo al más reciente. */
export const mesesHasta = (mes, cantidad) =>
  Array.from({ length: cantidad }, (_, i) => desplazarMes(mes, i - cantidad + 1));

export function rangoDelMes(mes) {
  const inicio = aFecha(mes);
  const fin = new Date(inicio.getFullYear(), inicio.getMonth() + 1, 0);
  return { inicio: fechaIso(inicio), fin: fechaIso(fin) };
}

const ENTIDADES = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
/** Evita que un texto escrito por el usuario se interprete como HTML. */
export const escapar = (texto) => String(texto ?? "").replace(/[&<>"']/g, (c) => ENTIDADES[c]);
