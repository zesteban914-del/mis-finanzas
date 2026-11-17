// Vista "Usuarios" (solo administradores de la plataforma).
// Por privacidad no muestra montos ni movimientos, solo cuántos tiene cada cuenta.
import { api } from "../api.js";
import { avisarCambio } from "../estado.js";
import { icono } from "../iconos.js";
import { cabecera, estadoVacio, insigniaPro, kpi } from "../componentes.js";
import { escapar, formatoFecha, formatoMoneda } from "../formato.js";
import { usuarioActual } from "../sesion.js";
import { abrirDialogo, notificar } from "../ui.js";

let busqueda = "";
let soloSolicitudes = false;

export async function renderizar(contenedor) {
  const [usuarios, e] = await Promise.all([api.admin.usuarios(), api.admin.estadisticas()]);
  const yo = usuarioActual();

  contenedor.innerHTML = `
    ${cabecera({
      titulo: "Usuarios",
      subtitulo: "Gestiona las cuentas de la plataforma. Por privacidad, aquí no se ven los datos financieros de nadie.",
    })}

    <section class="kpis" aria-label="Estadísticas">
      ${kpi({ etiqueta: "Ingreso mensual estimado", valor: formatoMoneda(e.ingreso_mensual_estimado), icono: "tendencia", destacado: true, pie: `${e.cuentas_pro} ${e.cuentas_pro === 1 ? "cuenta" : "cuentas"} en plan Pro` })}
      ${kpi({ etiqueta: "Cuentas", valor: e.cuentas_personales + e.cuentas_negocio, icono: "usuarios", pie: `${e.cuentas_personales} personales · ${e.cuentas_negocio} de negocio` })}
      ${kpi({ etiqueta: "Solicitudes de Pro", valor: e.solicitudes_pro, icono: "estrella", pie: e.solicitudes_pro ? "Pendientes por activar" : "Ninguna pendiente" })}
      ${kpi({ etiqueta: "Movimientos registrados", valor: e.movimientos_registrados.toLocaleString("es-CO"), icono: "movimientos", pie: `${e.usuarios_activos} de ${e.total_usuarios} usuarios activos` })}
    </section>

    <section class="tarjeta tarjeta--tabla">
      <div class="barra-busqueda">
        <span class="entrada-icono">${icono("buscar")}
          <input class="entrada" type="search" placeholder="Buscar por nombre o correo" value="${escapar(busqueda)}" aria-label="Buscar usuarios">
        </span>
        <label class="casilla"><input type="checkbox" data-solo-solicitudes ${soloSolicitudes ? "checked" : ""}><span>Solo solicitudes de Pro</span></label>
      </div>
      <div id="lista-usuarios"></div>
    </section>`;

  const lista = contenedor.querySelector("#lista-usuarios");
  const pintar = () => {
    const termino = busqueda.trim().toLowerCase();
    const visibles = usuarios.filter(
      (u) =>
        (!termino || u.nombre.toLowerCase().includes(termino) || u.email.includes(termino)) &&
        (!soloSolicitudes || (u.solicito_pro_en && u.plan === "GRATIS"))
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
  contenedor.querySelector("[data-solo-solicitudes]").addEventListener("change", (evento) => {
    soloSolicitudes = evento.target.checked;
    pintar();
  });
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
      ${interruptor("admin", "Administrador de la plataforma", "Puede ver y gestionar todas las cuentas (no sus finanzas)", usuario.rol === "ADMIN")}
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
