// Vista "Usuarios" (solo administradores): cuentas registradas y su estado.
// Por privacidad no muestra montos ni movimientos, solo cuántos tiene cada cuenta.
import { api } from "../api.js";
import { avisarCambio } from "../estado.js";
import { icono } from "../iconos.js";
import { cabecera, estadoVacio, kpi } from "../componentes.js";
import { escapar, formatoFecha } from "../formato.js";
import { usuarioActual } from "../sesion.js";
import { abrirDialogo, notificar } from "../ui.js";

let busqueda = "";

export async function renderizar(contenedor) {
  const [usuarios, estadisticas] = await Promise.all([api.admin.usuarios(), api.admin.estadisticas()]);
  const yo = usuarioActual();

  contenedor.innerHTML = `
    ${cabecera({
      titulo: "Usuarios",
      subtitulo: "Gestiona las cuentas de la plataforma. Por privacidad, aquí no se ven los datos financieros de nadie.",
    })}

    <section class="kpis" aria-label="Estadísticas">
      ${kpi({ etiqueta: "Cuentas registradas", valor: estadisticas.total_usuarios, icono: "usuarios" })}
      ${kpi({ etiqueta: "Cuentas activas", valor: estadisticas.usuarios_activos, icono: "check-circle" })}
      ${kpi({ etiqueta: "Administradores", valor: estadisticas.administradores, icono: "escudo" })}
      ${kpi({ etiqueta: "Movimientos registrados", valor: estadisticas.movimientos_registrados.toLocaleString("es-CO"), icono: "movimientos", pie: "Entre todas las cuentas" })}
    </section>

    <section class="tarjeta tarjeta--tabla">
      <div class="barra-busqueda">
        <span class="entrada-icono">${icono("buscar")}
          <input class="entrada" type="search" placeholder="Buscar por nombre o correo" value="${escapar(busqueda)}" aria-label="Buscar usuarios">
        </span>
      </div>
      <div id="lista-usuarios"></div>
    </section>`;

  const lista = contenedor.querySelector("#lista-usuarios");
  const pintar = () => {
    const termino = busqueda.trim().toLowerCase();
    const visibles = usuarios.filter(
      (u) => !termino || u.nombre.toLowerCase().includes(termino) || u.email.includes(termino)
    );
    lista.innerHTML = visibles.length
      ? tablaUsuarios(visibles, yo.id)
      : estadoVacio({ icono: "buscar", titulo: "Ningún usuario coincide con la búsqueda" });
    lista.querySelectorAll("[data-cambio]").forEach((boton) =>
      boton.addEventListener("click", () => confirmarCambio(usuarios.find((u) => u.id === Number(boton.dataset.id)), boton.dataset.cambio))
    );
  };

  contenedor.querySelector('input[type="search"]').addEventListener("input", (evento) => {
    busqueda = evento.target.value;
    pintar();
  });
  pintar();
}

const iniciales = (nombre) =>
  nombre.split(/\s+/).filter(Boolean).slice(0, 2).map((p) => p[0].toUpperCase()).join("");

function tablaUsuarios(usuarios, miId) {
  const filas = usuarios
    .map((u) => {
      const soyYo = u.id === miId;
      const esAdmin = u.rol === "ADMIN";
      return `
      <tr class="${u.activo ? "" : "fila-inactiva"}">
        <td>
          <span class="celda-usuario">
            <span class="avatar avatar--sm">${escapar(iniciales(u.nombre))}</span>
            <span>
              <strong>${escapar(u.nombre)}${soyYo ? ' <span class="etiqueta-actual">Tú</span>' : ""}</strong>
              <small>${escapar(u.email)}</small>
            </span>
          </span>
        </td>
        <td>${esAdmin ? `<span class="insignia-rol insignia-rol--admin">${icono("escudo")}Administrador</span>` : '<span class="insignia-rol">Usuario</span>'}</td>
        <td>${u.activo ? `<span class="estado estado--bien">${icono("check-circle")}Activa</span>` : `<span class="estado estado--neutro">${icono("x-circle")}Desactivada</span>`}</td>
        <td class="celda-fecha">${formatoFecha(u.creado_en.slice(0, 10))}</td>
        <td class="num">${u.movimientos_registrados.toLocaleString("es-CO")}</td>
        <td class="acciones">
          <div class="acciones-grupo">
          ${
            soyYo
              ? '<span class="texto-tenue">—</span>'
              : `<button type="button" class="boton boton--secundario boton--sm" data-id="${u.id}" data-cambio="rol">${esAdmin ? "Quitar admin" : "Hacer admin"}</button>
                 <button type="button" class="boton ${u.activo ? "boton--fantasma-peligro" : "boton--secundario"} boton--sm" data-id="${u.id}" data-cambio="estado">${u.activo ? "Desactivar" : "Activar"}</button>`
          }
          </div>
        </td>
      </tr>`;
    })
    .join("");
  return `
    <div class="tabla-contenedor">
      <table class="tabla tabla--usuarios">
        <thead><tr><th>Usuario</th><th>Rol</th><th>Estado</th><th>Registro</th><th class="num">Movimientos</th><th class="acciones"><span class="sr-only">Acciones</span></th></tr></thead>
        <tbody>${filas}</tbody>
      </table>
    </div>`;
}

function confirmarCambio(usuario, cambio) {
  const nombre = `<b>${escapar(usuario.nombre)}</b>`;
  let opciones;
  if (cambio === "estado") {
    opciones = usuario.activo
      ? {
          titulo: "¿Desactivar cuenta?",
          descripcion: `${nombre} no podrá iniciar sesión y su sesión actual se cerrará. Sus datos se conservan y puedes reactivarla cuando quieras.`,
          textoConfirmar: "Desactivar",
          peligro: true,
          cambios: { activo: false },
          exito: "Cuenta desactivada",
        }
      : { titulo: "¿Activar cuenta?", descripcion: `${nombre} podrá volver a iniciar sesión.`, textoConfirmar: "Activar", cambios: { activo: true }, exito: "Cuenta activada" };
  } else {
    opciones =
      usuario.rol === "ADMIN"
        ? { titulo: "¿Quitar rol de administrador?", descripcion: `${nombre} dejará de ver esta sección.`, textoConfirmar: "Quitar admin", peligro: true, cambios: { rol: "USUARIO" }, exito: "Rol actualizado" }
        : { titulo: "¿Hacer administrador?", descripcion: `${nombre} podrá ver y gestionar todas las cuentas (no sus finanzas).`, textoConfirmar: "Hacer admin", cambios: { rol: "ADMIN" }, exito: "Rol actualizado" };
  }
  abrirDialogo({
    ...opciones,
    alEnviar: async () => {
      await api.admin.actualizarUsuario(usuario.id, opciones.cambios);
      notificar(opciones.exito);
      avisarCambio();
    },
  });
}
