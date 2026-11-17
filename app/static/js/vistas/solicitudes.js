// Consola de administración · Solicitudes de plan Pro (y cuentas que ya son Pro).
import { api } from "../api.js";
import { avisarCambio } from "../estado.js";
import { icono } from "../iconos.js";
import { cabecera, estadoVacio } from "../componentes.js";
import { escapar, formatoFecha } from "../formato.js";
import { abrirDialogo, notificar } from "../ui.js";

const PRECIOS = { PERSONAL: "$9.900/mes", NEGOCIO: "$39.900/mes" };

export async function renderizar(contenedor) {
  const usuarios = await api.admin.usuarios();
  const pendientes = usuarios
    .filter((u) => u.solicito_pro_en && u.plan === "GRATIS")
    .sort((a, b) => a.solicito_pro_en.localeCompare(b.solicito_pro_en));
  const pro = usuarios.filter((u) => u.plan === "PRO" && !u.negocio_id);

  contenedor.innerHTML = `
    ${cabecera({
      titulo: "Solicitudes de plan Pro",
      subtitulo: "Activa el plan cuando se confirme el pago, o descarta la solicitud. Las más antiguas aparecen primero.",
    })}

    <section class="seccion">
      ${
        pendientes.length
          ? `<div class="bandeja">${pendientes.map(tarjetaSolicitud).join("")}</div>`
          : `<section class="tarjeta">${estadoVacio({ icono: "check-circle", titulo: "No hay solicitudes pendientes", texto: "Cuando un usuario pida el plan Pro aparecerá aquí." })}</section>`
      }
    </section>

    <section class="seccion">
      <header class="seccion-cabecera"><div>
        <h2>Cuentas con plan Pro</h2>
        <p>${pro.length} ${pro.length === 1 ? "cuenta activa" : "cuentas activas"} en el plan de pago</p>
      </div></header>
      <section class="tarjeta tarjeta--tabla">
        ${
          pro.length
            ? `<div class="tabla-contenedor"><table class="tabla tabla--usuarios">
                 <thead><tr><th>Cuenta</th><th>Tipo</th><th>Precio</th><th class="acciones"><span class="sr-only">Acciones</span></th></tr></thead>
                 <tbody>${pro
                   .map(
                     (u) => `<tr>
                       <td><span class="celda-usuario"><span class="avatar avatar--sm">${iniciales(u.nombre)}</span>
                         <span><strong>${escapar(u.nombre)}</strong><small>${escapar(u.email)}</small></span></span></td>
                       <td>${tipo(u)}</td>
                       <td>${PRECIOS[u.tipo_cuenta]}</td>
                       <td class="acciones"><div class="acciones-grupo">
                         <button type="button" class="boton boton--fantasma-peligro boton--sm" data-bajar="${u.id}">Pasar a Gratis</button>
                       </div></td>
                     </tr>`
                   )
                   .join("")}</tbody></table></div>`
            : estadoVacio({ icono: "estrella", titulo: "Aún no hay cuentas Pro" })
        }
      </section>
    </section>`;

  const buscar = (id) => usuarios.find((u) => u.id === Number(id));
  contenedor.querySelectorAll("[data-activar]").forEach((b) => b.addEventListener("click", () => activar(buscar(b.dataset.activar))));
  contenedor.querySelectorAll("[data-descartar]").forEach((b) => b.addEventListener("click", () => descartar(buscar(b.dataset.descartar))));
  contenedor.querySelectorAll("[data-bajar]").forEach((b) => b.addEventListener("click", () => bajar(buscar(b.dataset.bajar))));
}

const iniciales = (nombre) =>
  escapar(nombre.split(/\s+/).filter(Boolean).slice(0, 2).map((p) => p[0].toUpperCase()).join(""));

const tipo = (u) =>
  `<span class="insignia-rol">${icono(u.tipo_cuenta === "NEGOCIO" ? "tienda" : "persona")}${u.tipo_cuenta === "NEGOCIO" ? "Negocio" : "Personal"}</span>`;

function diasDesde(fechaIso) {
  const dias = Math.floor((Date.now() - new Date(fechaIso).getTime()) / 86_400_000);
  return dias <= 0 ? "hoy" : dias === 1 ? "hace 1 día" : `hace ${dias} días`;
}

function tarjetaSolicitud(u) {
  return `
    <article class="tarjeta solicitud">
      <span class="avatar">${iniciales(u.nombre)}</span>
      <div class="solicitud-datos">
        <strong>${escapar(u.nombre)}</strong>
        <span>${escapar(u.email)}</span>
        <span class="solicitud-meta">${tipo(u)} <span>Solicitó ${diasDesde(u.solicito_pro_en)} · ${formatoFecha(u.solicito_pro_en.slice(0, 10))}</span></span>
      </div>
      <div class="solicitud-precio"><span>Pagaría</span><b>${PRECIOS[u.tipo_cuenta]}</b></div>
      <div class="acciones-grupo">
        <button type="button" class="boton boton--secundario boton--sm" data-descartar="${u.id}">Descartar</button>
        <button type="button" class="boton boton--primario boton--sm" data-activar="${u.id}">${icono("check")}Activar Pro</button>
      </div>
    </article>`;
}

function confirmarCambio({ titulo, descripcion, textoConfirmar, peligro = false, cambios, exito }) {
  abrirDialogo({
    titulo,
    descripcion,
    textoConfirmar,
    peligro,
    alEnviar: async () => {
      await api.admin.actualizarUsuario(cambios.id, cambios.datos);
      notificar(exito);
      avisarCambio();
    },
  });
}

const activar = (u) =>
  confirmarCambio({
    titulo: "¿Activar el plan Pro?",
    descripcion: `<b>${escapar(u.nombre)}</b> tendrá los beneficios Pro de inmediato. Hazlo cuando se haya confirmado el pago de ${PRECIOS[u.tipo_cuenta]}.`,
    textoConfirmar: "Activar Pro",
    cambios: { id: u.id, datos: { plan: "PRO" } },
    exito: `Plan Pro activado para ${u.nombre}`,
  });

const descartar = (u) =>
  confirmarCambio({
    titulo: "¿Descartar la solicitud?",
    descripcion: `<b>${escapar(u.nombre)}</b> seguirá en el plan Gratis y podrá volver a solicitar el Pro.`,
    textoConfirmar: "Descartar",
    peligro: true,
    cambios: { id: u.id, datos: { descartar_solicitud: true } },
    exito: "Solicitud descartada",
  });

const bajar = (u) =>
  confirmarCambio({
    titulo: "¿Pasar a plan Gratis?",
    descripcion: `<b>${escapar(u.nombre)}</b> perderá los beneficios Pro (sus datos se conservan, pero no podrá crear más de lo que permite el plan Gratis).`,
    textoConfirmar: "Pasar a Gratis",
    peligro: true,
    cambios: { id: u.id, datos: { plan: "GRATIS" } },
    exito: "La cuenta pasó al plan Gratis",
  });
