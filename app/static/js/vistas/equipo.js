// Vista "Equipo" (propietario de un negocio): empleados y contador con permisos limitados.
import { api } from "../api.js";
import { avisarCambio } from "../estado.js";
import { icono } from "../iconos.js";
import { cabecera, cupoDelPlan, estadoVacio } from "../componentes.js";
import { escapar, formatoFecha } from "../formato.js";
import { limite } from "../sesion.js";
import { abrirDialogo, notificar } from "../ui.js";

const ROLES = {
  EMPLEADO: {
    nombre: "Empleado",
    icono: "persona",
    resumen: "Registra ventas y gastos del día",
    puede: ["Registrar ingresos y gastos", "Ver la lista de movimientos", "Adjuntar comprobantes"],
    noPuede: ["Ver saldos, reportes ni presupuestos", "Editar o eliminar movimientos"],
  },
  CONTADOR: {
    nombre: "Contador",
    icono: "documento",
    resumen: "Consulta todo y exporta reportes",
    puede: ["Ver panel, reportes y presupuestos", "Exportar a CSV o Excel", "Ver cajas y cuentas por cobrar/pagar"],
    noPuede: ["Crear, editar o eliminar nada"],
  },
};

export async function renderizar(contenedor) {
  const miembros = await api.equipo.listar();

  contenedor.innerHTML = `
    ${cabecera({
      titulo: "Equipo",
      subtitulo: "Da acceso a tu equipo sin compartir tu contraseña. Cada persona ve solo lo que necesita.",
      acciones: `<button type="button" class="boton boton--primario" data-accion="agregar">${icono("mas")}<span>Agregar miembro</span></button>`,
    })}
    ${cupoDelPlan(miembros.length, limite("miembros"), "miembros")}

    <div class="roles">
      <article class="tarjeta rol rol--propietario">
        <span class="rol-icono">${icono("escudo")}</span>
        <h3>Propietario <span class="texto-tenue">(tú)</span></h3>
        <p>Control total: datos, configuración, equipo y plan.</p>
      </article>
      ${Object.values(ROLES)
        .map(
          (r) => `
        <article class="tarjeta rol">
          <span class="rol-icono">${icono(r.icono)}</span>
          <h3>${r.nombre}</h3>
          <p>${r.resumen}</p>
          <ul>
            ${r.puede.map((x) => `<li class="si">${icono("check")}${x}</li>`).join("")}
            ${r.noPuede.map((x) => `<li class="no">${icono("x")}${x}</li>`).join("")}
          </ul>
        </article>`
        )
        .join("")}
    </div>

    <section class="tarjeta tarjeta--tabla">
      ${
        miembros.length
          ? `<div class="tabla-contenedor"><table class="tabla tabla--usuarios">
               <thead><tr><th>Miembro</th><th>Rol</th><th>Estado</th><th>Desde</th><th class="acciones"><span class="sr-only">Acciones</span></th></tr></thead>
               <tbody>${miembros.map(fila).join("")}</tbody>
             </table></div>`
          : estadoVacio({
              icono: "usuarios",
              titulo: "Aún no tienes miembros en tu equipo",
              texto: "Agrega a tu cajero para que registre las ventas, o a tu contador para que descargue los reportes.",
            })
      }
    </section>`;

  contenedor.querySelector("[data-accion='agregar']").addEventListener("click", agregar);
  const buscar = (id) => miembros.find((m) => m.id === Number(id));
  contenedor.querySelectorAll("[data-cambio]").forEach((b) =>
    b.addEventListener("click", () => cambiar(buscar(b.dataset.id), b.dataset.cambio))
  );
}

const iniciales = (nombre) => nombre.split(/\s+/).filter(Boolean).slice(0, 2).map((p) => p[0].toUpperCase()).join("");

function fila(m) {
  const otroRol = m.rol_negocio === "EMPLEADO" ? "CONTADOR" : "EMPLEADO";
  return `
    <tr class="${m.activo ? "" : "fila-inactiva"}">
      <td>
        <span class="celda-usuario">
          <span class="avatar avatar--sm">${escapar(iniciales(m.nombre))}</span>
          <span><strong>${escapar(m.nombre)}</strong><small>${escapar(m.email)}</small></span>
        </span>
      </td>
      <td><span class="insignia-rol">${icono(ROLES[m.rol_negocio].icono)}${ROLES[m.rol_negocio].nombre}</span></td>
      <td>${m.activo ? `<span class="estado estado--bien">${icono("check-circle")}Activo</span>` : `<span class="estado estado--neutro">${icono("x-circle")}Sin acceso</span>`}</td>
      <td class="celda-fecha">${formatoFecha(m.creado_en.slice(0, 10))}</td>
      <td class="acciones">
        <div class="acciones-grupo">
          <button type="button" class="boton boton--secundario boton--sm" data-id="${m.id}" data-cambio="rol">Cambiar a ${ROLES[otroRol].nombre.toLowerCase()}</button>
          <button type="button" class="boton boton--secundario boton--sm" data-id="${m.id}" data-cambio="estado">${m.activo ? "Quitar acceso" : "Dar acceso"}</button>
          <button type="button" class="boton-icono boton-icono--peligro" data-id="${m.id}" data-cambio="eliminar" aria-label="Eliminar a ${escapar(m.nombre)}" title="Eliminar">${icono("papelera")}</button>
        </div>
      </td>
    </tr>`;
}

function agregar() {
  abrirDialogo({
    titulo: "Agregar miembro al equipo",
    descripcion: "Creamos su cuenta con una contraseña inicial. Compártela en persona; podrá cambiarla en «Mi cuenta».",
    textoConfirmar: "Agregar",
    contenido: `
      <fieldset class="opciones-lista opciones-lista--fila">
        <legend class="campo-etiqueta">Rol</legend>
        ${Object.entries(ROLES)
          .map(
            ([valor, r], i) => `
          <label class="opcion">
            <input type="radio" name="rol_negocio" value="${valor}" ${i === 0 ? "checked" : ""}>
            <span class="opcion-icono">${icono(r.icono)}</span>
            <span class="opcion-texto"><strong>${r.nombre}</strong><span>${r.resumen}</span></span>
          </label>`
          )
          .join("")}
      </fieldset>
      <label class="campo"><span class="campo-etiqueta">Nombre</span><input class="entrada" name="nombre" maxlength="80" autocomplete="off" placeholder="Ej. Laura Gómez"></label>
      <div class="campos-fila">
        <label class="campo"><span class="campo-etiqueta">Correo</span><input class="entrada" name="email" type="email" maxlength="120" autocomplete="off" placeholder="laura@correo.com"></label>
        <label class="campo"><span class="campo-etiqueta">Contraseña inicial</span><input class="entrada" name="contrasena" type="text" maxlength="128" autocomplete="new-password" placeholder="Mín. 8, letras y números"></label>
      </div>`,
    alEnviar: async (datos) => {
      await api.equipo.crear({
        nombre: datos.get("nombre").trim(),
        email: datos.get("email").trim(),
        contrasena: datos.get("contrasena"),
        rol_negocio: datos.get("rol_negocio"),
      });
      notificar("Miembro agregado: ya puede iniciar sesión");
      avisarCambio();
    },
  });
}

function cambiar(miembro, cambio) {
  const nombre = `<b>${escapar(miembro.nombre)}</b>`;
  const otroRol = miembro.rol_negocio === "EMPLEADO" ? "CONTADOR" : "EMPLEADO";
  const opciones = {
    rol: {
      titulo: `¿Cambiar a ${ROLES[otroRol].nombre.toLowerCase()}?`,
      descripcion: `${nombre} pasará a tener los permisos de ${ROLES[otroRol].nombre.toLowerCase()}: ${ROLES[otroRol].resumen.toLowerCase()}.`,
      textoConfirmar: "Cambiar rol",
      accion: () => api.equipo.actualizar(miembro.id, { rol_negocio: otroRol }),
    },
    estado: miembro.activo
      ? {
          titulo: "¿Quitar acceso?",
          descripcion: `${nombre} no podrá iniciar sesión. Lo que registró se conserva.`,
          textoConfirmar: "Quitar acceso",
          peligro: true,
          accion: () => api.equipo.actualizar(miembro.id, { activo: false }),
        }
      : {
          titulo: "¿Dar acceso?",
          descripcion: `${nombre} podrá volver a iniciar sesión.`,
          textoConfirmar: "Dar acceso",
          accion: () => api.equipo.actualizar(miembro.id, { activo: true }),
        },
    eliminar: {
      titulo: "¿Eliminar del equipo?",
      descripcion: `Se eliminará la cuenta de ${nombre}. Los movimientos que registró se conservan, pero sin autor.`,
      textoConfirmar: "Eliminar",
      peligro: true,
      accion: () => api.equipo.eliminar(miembro.id),
    },
  }[cambio];
  abrirDialogo({
    ...opciones,
    alEnviar: async () => {
      await opciones.accion();
      notificar("Equipo actualizado");
      avisarCambio();
    },
  });
}
