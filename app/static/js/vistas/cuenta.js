// Vista "Mi cuenta y plan": perfil según el tipo de cuenta, contraseña y suscripción.
import { api } from "../api.js";
import { bus } from "../estado.js";
import { icono } from "../iconos.js";
import { cabecera } from "../componentes.js";
import { escapar, formatoFecha, formatoMoneda } from "../formato.js";
import { mostrarPolitica } from "../legal.js";
import { actualizarUsuario, esNegocio, usuarioActual } from "../sesion.js";
import { notificar } from "../ui.js";

const ROLES = { PROPIETARIO: "Propietario", EMPLEADO: "Empleado", CONTADOR: "Contador" };

export async function renderizar(contenedor) {
  const usuario = usuarioActual();
  const esMiembro = Boolean(usuario.negocio_id);
  const [planes, opciones] = await Promise.all([api.planes.catalogo(), api.auth.opciones()]);
  const opcionesDe = (mapa, actual) =>
    `<option value="">Sin especificar</option>` +
    Object.entries(mapa).map(([v, t]) => `<option value="${v}" ${v === actual ? "selected" : ""}>${escapar(t)}</option>`).join("");

  contenedor.innerHTML = `
    ${cabecera({ titulo: "Mi cuenta y plan", subtitulo: escapar(usuario.email) })}

    <section class="seccion">
      <header class="seccion-cabecera"><div><h2>Plan</h2>
        <p>${esMiembro ? `Tu equipo usa el plan de ${escapar(usuario.nombre_negocio)}.` : "Empieza gratis y mejora cuando lo necesites."}</p></div>
      </header>
      <div class="planes">${planes.map((p) => tarjetaPlan(p, usuario, esMiembro)).join("")}</div>
      ${
        !esMiembro
          ? `<p class="ayuda">${icono("candado")} El pago en línea (Wompi, PayU o Mercado Pago) se integrará próximamente. Por ahora, al solicitar el plan Pro un administrador lo activa.</p>`
          : ""
      }
    </section>

    <div class="rejilla-dos">
      <form class="tarjeta formulario-tarjeta" data-formulario="perfil" novalidate>
        <header class="tarjeta-cabecera">
          <div>
            <h2 class="tarjeta-titulo">Perfil</h2>
            <p class="tarjeta-subtitulo">
              ${esMiembro
                ? `${ROLES[usuario.rol_negocio]} en <b>${escapar(usuario.nombre_negocio)}</b>`
                : `Cuenta ${esNegocio() ? "de negocio" : "personal"} · desde ${formatoFecha(usuario.creado_en.slice(0, 10))}`}
            </p>
          </div>
          <span class="insignia-rol">${icono(esNegocio() ? "tienda" : "persona")}${esNegocio() ? "Negocio" : "Personal"}</span>
        </header>
        <label class="campo">
          <span class="campo-etiqueta">${esNegocio() && !esMiembro ? "Nombre del negocio" : "Nombre"}</span>
          <input class="entrada" name="nombre" maxlength="80" value="${escapar(usuario.nombre)}">
        </label>
        ${
          esMiembro
            ? ""
            : esNegocio()
              ? `<div class="campos-fila">
                   <label class="campo"><span class="campo-etiqueta">Sector</span><select class="entrada" name="sector">${opcionesDe(opciones.sectores, usuario.sector)}</select></label>
                   <label class="campo"><span class="campo-etiqueta">NIT</span><input class="entrada" name="nit" maxlength="20" value="${escapar(usuario.nit ?? "")}" placeholder="900123456-7"></label>
                 </div>
                 <label class="campo"><span class="campo-etiqueta">Persona responsable</span><input class="entrada" name="responsable" maxlength="80" value="${escapar(usuario.responsable ?? "")}"></label>`
              : `<label class="campo"><span class="campo-etiqueta">Objetivo principal</span><select class="entrada" name="objetivo">${opcionesDe(opciones.objetivos, usuario.objetivo)}</select></label>`
        }
        <p class="dialogo-error" role="alert" hidden></p>
        <div class="formulario-pie"><button type="submit" class="boton boton--primario">Guardar perfil</button></div>
      </form>

      <form class="tarjeta formulario-tarjeta" data-formulario="contrasena" novalidate>
        <header class="tarjeta-cabecera"><div><h2 class="tarjeta-titulo">Contraseña</h2>
          <p class="tarjeta-subtitulo">Mínimo 8 caracteres, con letras y números</p></div></header>
        <label class="campo"><span class="campo-etiqueta">Contraseña actual</span><input class="entrada" name="actual" type="password" autocomplete="current-password"></label>
        <div class="campos-fila">
          <label class="campo"><span class="campo-etiqueta">Nueva contraseña</span><input class="entrada" name="nueva" type="password" autocomplete="new-password"></label>
          <label class="campo"><span class="campo-etiqueta">Repítela</span><input class="entrada" name="confirmacion" type="password" autocomplete="new-password"></label>
        </div>
        <p class="dialogo-error" role="alert" hidden></p>
        <div class="formulario-pie"><button type="submit" class="boton boton--secundario">Cambiar contraseña</button></div>
      </form>
    </div>

    <p class="ayuda ayuda--centrada">
      <button type="button" class="enlace" data-accion="politica">${icono("documento")}Términos y política de tratamiento de datos</button>
    </p>`;

  enviarFormulario(contenedor, "perfil", async (datos) => {
    const cambios = { nombre: datos.get("nombre").trim() };
    for (const campo of ["objetivo", "sector", "nit", "responsable"]) {
      if (datos.has(campo)) cambios[campo] = datos.get(campo);
    }
    usuarioActualizado(await api.auth.actualizarPerfil(cambios));
    notificar("Perfil actualizado");
  });
  enviarFormulario(contenedor, "contrasena", async (datos, formulario) => {
    if (datos.get("nueva") !== datos.get("confirmacion")) throw new Error("Las contraseñas nuevas no coinciden");
    await api.auth.cambiarContrasena({ actual: datos.get("actual"), nueva: datos.get("nueva") });
    formulario.reset();
    notificar("Contraseña actualizada");
  });
  contenedor.querySelector("[data-accion='solicitar-pro']")?.addEventListener("click", async (evento) => {
    evento.currentTarget.disabled = true;
    try {
      usuarioActualizado(await api.planes.solicitarPro());
      notificar("Solicitud enviada: un administrador activará tu plan Pro");
    } catch (error) {
      notificar(error.message, "error");
    }
  });
  contenedor.querySelector("[data-accion='politica']").addEventListener("click", mostrarPolitica);
}

function usuarioActualizado(usuario) {
  actualizarUsuario(usuario);
  bus.dispatchEvent(new Event("usuario-actualizado"));
}

function tarjetaPlan(plan, usuario, esMiembro) {
  const esPro = plan.plan === "PRO";
  let accion = "";
  if (plan.actual) {
    accion = `<span class="plan-actual">${icono("check-circle")}Tu plan actual</span>`;
  } else if (esPro && !esMiembro) {
    accion = usuario.solicito_pro_en
      ? `<span class="plan-actual plan-actual--pendiente">${icono("calendario")}Solicitud enviada el ${formatoFecha(usuario.solicito_pro_en.slice(0, 10))}</span>`
      : `<button type="button" class="boton boton--primario boton--ancho" data-accion="solicitar-pro">${icono("estrella")}Solicitar plan Pro</button>`;
  }
  return `
    <article class="tarjeta plan ${esPro ? "plan--pro" : ""} ${plan.actual ? "plan--actual" : ""}">
      <header>
        <h3>${esPro ? `Pro ${icono("estrella")}` : "Gratis"}</h3>
        <p class="plan-precio">${plan.precio_mensual ? `${formatoMoneda(plan.precio_mensual)}<span>/mes</span>` : "$0<span>/siempre</span>"}</p>
      </header>
      <ul>${plan.beneficios.map((b) => `<li>${icono("check")}${escapar(b)}</li>`).join("")}</ul>
      ${accion}
    </article>`;
}

function enviarFormulario(contenedor, nombre, alEnviar) {
  const formulario = contenedor.querySelector(`[data-formulario="${nombre}"]`);
  const cajaError = formulario.querySelector(".dialogo-error");
  const boton = formulario.querySelector("[type=submit]");
  formulario.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    cajaError.hidden = true;
    boton.disabled = true;
    try {
      await alEnviar(new FormData(formulario), formulario);
    } catch (error) {
      cajaError.innerHTML = `${icono("alerta")}<span>${escapar(error.message)}</span>`;
      cajaError.hidden = false;
    } finally {
      boton.disabled = false;
    }
  });
}
