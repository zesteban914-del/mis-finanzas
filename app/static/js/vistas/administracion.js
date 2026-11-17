// Vista "Usuarios" (solo administradores de la plataforma).
// Por privacidad no muestra montos ni movimientos, solo cuántos tiene cada cuenta.
import { api } from "../api.js";
import { avisarCambio } from "../estado.js";
import { icono } from "../iconos.js";
import { cabecera, estadoVacio, insigniaPro } from "../componentes.js";
import { escapar, formatoFecha } from "../formato.js";
import { usuarioActual } from "../sesion.js";
import { abrirDialogo, notificar } from "../ui.js";

const FILTROS = {
  todas: ["Todas", () => true],
  personales: ["Personales", (u) => !u.negocio_id && u.rol !== "ADMIN" && u.tipo_cuenta === "PERSONAL"],
  negocios: ["Negocios", (u) => !u.negocio_id && u.tipo_cuenta === "NEGOCIO"],
  equipos: ["Miembros de equipos", (u) => Boolean(u.negocio_id)],
  pro: ["Plan Pro", (u) => u.plan === "PRO" && !u.negocio_id],
  admins: ["Administradores", (u) => u.rol === "ADMIN"],
  inactivas: ["Desactivadas", (u) => !u.activo],
};

let busqueda = "";
let filtro = "todas";

export async function renderizar(contenedor) {
  const usuarios = await api.admin.usuarios();
  const yo = usuarioActual();

  contenedor.innerHTML = `
    ${cabecera({
      titulo: "Usuarios",
      subtitulo: `${usuarios.length} cuentas en la plataforma. Por privacidad, aquí no se ven los datos financieros de nadie.`,
    })}

    <section class="tarjeta tarjeta--tabla">
      <div class="barra-busqueda">
        <span class="entrada-icono">${icono("buscar")}
          <input class="entrada" type="search" placeholder="Buscar por nombre o correo" value="${escapar(busqueda)}" aria-label="Buscar usuarios">
        </span>
      </div>
      <div class="pestanas" role="tablist">
        ${Object.entries(FILTROS)
          .map(([clave, [texto, condicion]]) => {
            const cantidad = usuarios.filter(condicion).length;
            return `<button type="button" role="tab" aria-selected="${filtro === clave}" class="${filtro === clave ? "activa" : ""}" data-filtro="${clave}">${texto} <span class="texto-tenue">${cantidad}</span></button>`;
          })
          .join("")}
      </div>
      <div id="lista-usuarios"></div>
    </section>`;

  const lista = contenedor.querySelector("#lista-usuarios");
  const pintar = () => {
    const termino = busqueda.trim().toLowerCase();
    const visibles = usuarios.filter(
      (u) =>
        (!termino || u.nombre.toLowerCase().includes(termino) || u.email.includes(termino)) &&
        FILTROS[filtro][1](u)
    );
    lista.innerHTML = visibles.length
      ? tablaUsuarios(visibles, yo.id)
      : estadoVacio({ icono: "buscar", titulo: "Ningún usuario coincide" });
    lista.querySelectorAll("[data-gestionar]").forEach((boton) =>
      boton.addEventListener("click", () => gestionar(usuarios.find((u) => u.id === Number(boton.dataset.gestionar))))
    );
  };

  contenedor.querySelector('input[type="search"]').addEventListener("input", (evento) => {
    busqueda = evento.target.value;
    pintar();
  });
  contenedor.querySelectorAll("[data-filtro]").forEach((boton) =>
    boton.addEventListener("click", () => {
      filtro = boton.dataset.filtro;
      renderizar(contenedor);
    })
  );
  pintar();
}

const iniciales = (nombre) =>
  nombre.split(/\s+/).filter(Boolean).slice(0, 2).map((p) => p[0].toUpperCase()).join("");

const ROLES_NEGOCIO = { EMPLEADO: "Empleado", CONTADOR: "Contador" };

function tipoDeCuenta(u) {
  if (u.negocio_id) return `<span class="insignia-rol">${icono("usuarios")}${ROLES_NEGOCIO[u.rol_negocio]} de ${escapar(u.nombre_negocio)}</span>`;
  return u.tipo_cuenta === "NEGOCIO"
    ? `<span class="insignia-rol">${icono("tienda")}Negocio</span>`
    : `<span class="insignia-rol">${icono("persona")}Personal</span>`;
}

function tablaUsuarios(usuarios, miId) {
  const filas = usuarios
    .map((u) => {
      const soyYo = u.id === miId;
      const solicitud = u.solicito_pro_en && u.plan === "GRATIS";
      return `
      <tr class="${u.activo ? "" : "fila-inactiva"}">
        <td>
          <span class="celda-usuario">
            <span class="avatar avatar--sm">${escapar(iniciales(u.nombre))}</span>
            <span>
              <strong>${escapar(u.nombre)}${soyYo ? ' <span class="etiqueta-actual">Tú</span>' : ""}${u.rol === "ADMIN" ? ` <span class="etiqueta-actual">${icono("escudo")}Admin</span>` : ""}</strong>
              <small>${escapar(u.email)}</small>
            </span>
          </span>
        </td>
        <td>${tipoDeCuenta(u)}</td>
        <td>
          ${u.plan === "PRO" ? insigniaPro() : '<span class="texto-tenue">Gratis</span>'}
          ${solicitud ? `<span class="estado estado--aviso">${icono("estrella")}Solicitó Pro</span>` : ""}
        </td>
        <td>${u.activo ? `<span class="estado estado--bien">${icono("check-circle")}Activa</span>` : `<span class="estado estado--neutro">${icono("x-circle")}Desactivada</span>`}</td>
        <td class="num">${u.movimientos_registrados.toLocaleString("es-CO")}</td>
        <td class="acciones">
          <div class="acciones-grupo">
            ${soyYo ? '<span class="texto-tenue">—</span>' : `<button type="button" class="boton ${solicitud ? "boton--primario" : "boton--secundario"} boton--sm" data-gestionar="${u.id}">Gestionar</button>`}
          </div>
        </td>
      </tr>`;
    })
    .join("");
  return `
    <div class="tabla-contenedor">
      <table class="tabla tabla--usuarios tabla--admin">
        <thead><tr><th>Usuario</th><th>Tipo</th><th>Plan</th><th>Estado</th><th class="num">Movimientos</th><th class="acciones"><span class="sr-only">Acciones</span></th></tr></thead>
        <tbody>${filas}</tbody>
      </table>
    </div>`;
}

function gestionar(usuario) {
  const esMiembro = Boolean(usuario.negocio_id);
  const interruptor = (nombre, titulo, texto, activo, deshabilitado = false) => `
    <label class="ajuste ${deshabilitado ? "ajuste--deshabilitado" : ""}">
      <span class="ajuste-texto"><strong>${titulo}</strong><span>${texto}</span></span>
      <span class="interruptor"><input type="checkbox" name="${nombre}" ${activo ? "checked" : ""} ${deshabilitado ? "disabled" : ""}><span></span></span>
    </label>`;

  abrirDialogo({
    titulo: escapar(usuario.nombre),
    descripcion: `${escapar(usuario.email)} · registrado el ${formatoFecha(usuario.creado_en.slice(0, 10))}`,
    textoConfirmar: "Guardar cambios",
    contenido: `
      ${
        usuario.solicito_pro_en && usuario.plan === "GRATIS"
          ? `<p class="alerta alerta--aviso">${icono("estrella")}<span>Solicitó el plan Pro el ${formatoFecha(usuario.solicito_pro_en.slice(0, 10))}. Actívalo cuando se confirme el pago.</span></p>`
          : ""
      }
      ${interruptor("pro", "Plan Pro", esMiembro ? "Usa el plan de su negocio" : "Desbloquea Excel, comprobantes y límites más altos", usuario.plan === "PRO", esMiembro)}
      ${interruptor("admin", "Administrador de la plataforma", "Usa la consola de administración. Mientras lo sea, la cuenta no usa funciones financieras (sus datos se conservan)", usuario.rol === "ADMIN")}
      ${interruptor("activo", "Cuenta activa", "Si la desactivas, no podrá iniciar sesión (sus datos se conservan)", usuario.activo)}`,
    alEnviar: async (datos) => {
      const cambios = {
        rol: datos.get("admin") === "on" ? "ADMIN" : "USUARIO",
        activo: datos.get("activo") === "on",
      };
      const plan = datos.get("pro") === "on" ? "PRO" : "GRATIS";
      if (!esMiembro && plan !== usuario.plan) cambios.plan = plan;
      await api.admin.actualizarUsuario(usuario.id, cambios);
      notificar("Cuenta actualizada");
      avisarCambio();
    },
  });
}
