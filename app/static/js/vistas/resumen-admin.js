// Consola de administración · Resumen: indicadores del negocio (sin montos de los usuarios).
import { api } from "../api.js";
import { columnasAgrupadas } from "../graficos.js";
import { icono } from "../iconos.js";
import { barraProgreso, cabecera, estadoVacio, insigniaPro, kpi, leyenda, tarjetaGrafico } from "../componentes.js";
import { escapar, formatoFecha, formatoMoneda, nombreMes, nombreMesCorto } from "../formato.js";

const SERIES_CUENTAS = [
  { nombre: "Personales", colorVar: "--serie-ingreso" },
  { nombre: "Negocios", colorVar: "--serie-3" },
];
const SERIE_ACTIVIDAD = [{ nombre: "Movimientos", colorVar: "--serie-ingreso" }];
const CANTIDADES = { formatoValor: (n) => n.toLocaleString("es-CO"), formatoEje: (n) => n.toLocaleString("es-CO"), enteros: true };

export async function renderizar(contenedor) {
  const [e, usuarios] = await Promise.all([api.admin.estadisticas(), api.admin.usuarios()]);
  const titulares = usuarios.filter((u) => !u.negocio_id && u.rol !== "ADMIN");
  const totalCuentas = titulares.length;
  const personales = titulares.filter((u) => u.tipo_cuenta === "PERSONAL").length;
  const conversion = totalCuentas ? Math.round((e.cuentas_pro / totalCuentas) * 100) : 0;
  const pendientes = usuarios.filter((u) => u.solicito_pro_en && u.plan === "GRATIS");
  const recientes = [...titulares].sort((a, b) => b.creado_en.localeCompare(a.creado_en)).slice(0, 5);
  const ultimoMes = e.actividad_por_mes.at(-1);

  contenedor.innerHTML = `
    ${cabecera({
      titulo: "Resumen de la plataforma",
      subtitulo: "Cómo va el negocio. Por privacidad, aquí no se ven montos ni movimientos de los usuarios.",
    })}

    <section class="kpis" aria-label="Indicadores">
      ${kpi({ etiqueta: "Ingreso mensual estimado", valor: formatoMoneda(e.ingreso_mensual_estimado), icono: "tendencia", destacado: true, pie: `${e.cuentas_pro} ${e.cuentas_pro === 1 ? "cuenta" : "cuentas"} en plan Pro` })}
      ${kpi({ etiqueta: "Cuentas de clientes", valor: totalCuentas, icono: "usuarios", pie: `${personales} personales · ${totalCuentas - personales} negocios` })}
      ${kpi({ etiqueta: "Conversión a Pro", valor: `${conversion} %`, icono: "estrella", pie: `${e.cuentas_pro} de ${totalCuentas} cuentas pagan` })}
      ${kpi({ etiqueta: "Nuevas este mes", valor: ultimoMes.cuentas_personales + ultimoMes.cuentas_negocio, icono: "persona", pie: `${ultimoMes.movimientos.toLocaleString("es-CO")} movimientos registrados en ${nombreMes(ultimoMes.mes).toLowerCase()}` })}
    </section>

    ${
      pendientes.length
        ? `<a class="alerta alerta--aviso alerta--enlace" href="#/solicitudes">${icono("estrella")}
             <span><strong>${pendientes.length} ${pendientes.length === 1 ? "solicitud" : "solicitudes"} de plan Pro</strong> esperan tu revisión.</span>
             <span class="enlace">Revisar${icono("derecha")}</span></a>`
        : ""
    }

    <div class="panel-rejilla">
      ${tarjetaGrafico({
        id: "grafico-cuentas",
        titulo: "Cuentas nuevas por mes",
        subtitulo: "Últimos 6 meses, sin contar miembros de equipos",
        extra: leyenda(SERIES_CUENTAS),
        tabla: tablaActividad(e.actividad_por_mes),
        clase: "col-7",
      })}
      ${tarjetaGrafico({
        id: "grafico-actividad",
        titulo: "Uso de la aplicación",
        subtitulo: "Movimientos registrados por mes (solo la cantidad)",
        tabla: tablaActividad(e.actividad_por_mes),
        clase: "col-5",
      })}

      <section class="tarjeta col-5">
        <header class="tarjeta-cabecera"><div>
          <h2 class="tarjeta-titulo">Distribución de cuentas</h2>
          <p class="tarjeta-subtitulo">Por tipo y plan</p>
        </div></header>
        ${distribucion(titulares)}
      </section>

      <section class="tarjeta col-7">
        <header class="tarjeta-cabecera">
          <div><h2 class="tarjeta-titulo">Últimos registros</h2><p class="tarjeta-subtitulo">Cuentas creadas más recientemente</p></div>
          <a class="enlace" href="#/administracion">Ver todas${icono("derecha")}</a>
        </header>
        ${
          recientes.length
            ? `<ul class="lista-cuentas">${recientes.map(itemCuenta).join("")}</ul>`
            : estadoVacio({ icono: "usuarios", titulo: "Aún no hay cuentas de clientes" })
        }
      </section>
    </div>`;

  const grupos = e.actividad_por_mes.map((a, i, todos) => ({
    etiqueta: nombreMesCorto(a.mes),
    titulo: nombreMes(a.mes),
    actual: i === todos.length - 1,
  }));
  columnasAgrupadas(
    contenedor.querySelector("#grafico-cuentas"),
    grupos.map((g, i) => ({ ...g, valores: [e.actividad_por_mes[i].cuentas_personales, e.actividad_por_mes[i].cuentas_negocio] })),
    SERIES_CUENTAS,
    { ...CANTIDADES, descripcion: "Cuentas nuevas por mes", nota: (g) => `Total: ${g.valores[0] + g.valores[1]} cuentas` }
  );
  columnasAgrupadas(
    contenedor.querySelector("#grafico-actividad"),
    grupos.map((g, i) => ({ ...g, valores: [e.actividad_por_mes[i].movimientos] })),
    SERIE_ACTIVIDAD,
    { ...CANTIDADES, descripcion: "Movimientos registrados por mes", nota: null }
  );
}

function distribucion(titulares) {
  const total = titulares.length || 1;
  const contar = (tipo, plan) => titulares.filter((u) => u.tipo_cuenta === tipo && u.plan === plan).length;
  const filas = [
    ["persona", "Personal", "PERSONAL", "GRATIS"],
    ["persona", "Personal", "PERSONAL", "PRO"],
    ["tienda", "Negocio", "NEGOCIO", "GRATIS"],
    ["tienda", "Negocio", "NEGOCIO", "PRO"],
  ].map(([nombreIcono, tipo, clave, plan]) => ({
    nombreIcono,
    html: `${tipo} · ${plan === "PRO" ? insigniaPro() : "Gratis"}`,
    texto: `${tipo} ${plan === "PRO" ? "Pro" : "Gratis"}`,
    cantidad: contar(clave, plan),
    clase: plan === "PRO" ? "bien" : "acento",
  }));
  const inactivas = titulares.filter((u) => !u.activo).length;
  return `
    <ul class="distribucion">
      ${filas
        .map(
          (f) => `
        <li>
          <span class="distribucion-etiqueta">${icono(f.nombreIcono)}${f.html}</span>
          ${barraProgreso(f.cantidad / total, f.clase, f.texto)}
          <b>${f.cantidad}</b>
        </li>`
        )
        .join("")}
    </ul>
    <p class="ayuda">${inactivas} ${inactivas === 1 ? "cuenta desactivada" : "cuentas desactivadas"} incluidas en el total.</p>`;
}

function itemCuenta(u) {
  const iniciales = u.nombre.split(/\s+/).filter(Boolean).slice(0, 2).map((p) => p[0].toUpperCase()).join("");
  return `
    <li class="reciente">
      <span class="avatar avatar--sm">${escapar(iniciales)}</span>
      <span class="reciente-texto">
        <span class="reciente-titulo">${escapar(u.nombre)}</span>
        <span class="reciente-meta">${escapar(u.email)} · ${formatoFecha(u.creado_en.slice(0, 10))}</span>
      </span>
      <span class="insignia-rol">${icono(u.tipo_cuenta === "NEGOCIO" ? "tienda" : "persona")}${u.tipo_cuenta === "NEGOCIO" ? "Negocio" : "Personal"}</span>
      ${u.plan === "PRO" ? insigniaPro() : '<span class="texto-tenue">Gratis</span>'}
    </li>`;
}

function tablaActividad(actividad) {
  const filas = actividad
    .map((a) => `<tr><td>${nombreMes(a.mes)}</td><td class="num">${a.cuentas_personales}</td><td class="num">${a.cuentas_negocio}</td><td class="num">${a.movimientos.toLocaleString("es-CO")}</td></tr>`)
    .join("");
  return `<div class="tabla-contenedor"><table class="tabla tabla--compacta">
    <thead><tr><th>Mes</th><th class="num">Personales</th><th class="num">Negocios</th><th class="num">Movimientos</th></tr></thead>
    <tbody>${filas}</tbody></table></div>`;
}
