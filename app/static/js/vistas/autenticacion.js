// Pantallas de inicio de sesión y de registro.
import { api } from "../api.js";
import { escapar } from "../formato.js";
import { icono } from "../iconos.js";
import { guardarSesion } from "../sesion.js";

const BENEFICIOS = [
  ["tendencia", "Panel con tu saldo, gastos por categoría y tendencia de 6 meses"],
  ["objetivo", "Presupuesto mensual con alertas cuando lo superas"],
  ["candado", "Tus datos son privados: solo tú ves tus movimientos"],
];

/**
 * modo: "ingresar" | "registro". `alEntrar` se llama cuando la sesión queda iniciada.
 * `aviso`: mensaje opcional (por ejemplo, "tu sesión expiró").
 */
export function renderizarAutenticacion(contenedor, { modo, alEntrar, aviso = "" }) {
  const esRegistro = modo === "registro";
  document.title = `${esRegistro ? "Crear cuenta" : "Iniciar sesión"} · Mis Finanzas`;

  contenedor.innerHTML = `
    <section class="autenticacion-marca" aria-hidden="true">
      <div class="marca">
        <span class="marca-logo">${icono("tendencia")}</span>
        <strong>Mis Finanzas</strong>
      </div>
      <div class="autenticacion-mensaje">
        <h2>Toma el control de tu dinero, mes a mes.</h2>
        <p>Registra ingresos y gastos en segundos y descubre a dónde se va tu plata.</p>
        <ul>${BENEFICIOS.map(([i, texto]) => `<li><span>${icono(i)}</span>${texto}</li>`).join("")}</ul>
      </div>
      <div class="autenticacion-muestra">
        <span>Saldo del mes</span>
        <strong>$ 3.060.000</strong>
        <div class="autenticacion-barras">${[38, 52, 44, 70, 58, 82].map((h) => `<i style="height:${h}%"></i>`).join("")}</div>
      </div>
    </section>

    <section class="autenticacion-panel">
      <form class="autenticacion-formulario" novalidate>
        <div class="marca autenticacion-marca-movil">
          <span class="marca-logo">${icono("tendencia")}</span>
          <strong>Mis Finanzas</strong>
        </div>
        <header>
          <h1>${esRegistro ? "Crea tu cuenta" : "Bienvenido de nuevo"}</h1>
          <p>${esRegistro ? "Empieza gratis. Solo toma un minuto." : "Ingresa para ver tus finanzas."}</p>
        </header>

        ${aviso ? `<p class="alerta alerta--aviso" role="status">${icono("alerta")}<span>${escapar(aviso)}</span></p>` : ""}
        <p class="dialogo-error autenticacion-error" role="alert" hidden></p>

        ${
          esRegistro
            ? `<label class="campo">
                 <span class="campo-etiqueta">Nombre</span>
                 <input class="entrada" name="nombre" autocomplete="name" maxlength="80" placeholder="Tu nombre o el de tu negocio">
               </label>`
            : ""
        }
        <label class="campo">
          <span class="campo-etiqueta">Correo electrónico</span>
          <input class="entrada" name="email" type="email" autocomplete="email" maxlength="120" placeholder="tu@correo.com">
        </label>
        <label class="campo">
          <span class="campo-etiqueta">Contraseña</span>
          <span class="entrada-con-boton">
            <input class="entrada" name="contrasena" type="password" maxlength="128"
              autocomplete="${esRegistro ? "new-password" : "current-password"}"
              placeholder="${esRegistro ? "Mínimo 8 caracteres, con letras y números" : "Tu contraseña"}">
            <button type="button" class="boton-icono" data-alternar-contrasena aria-label="Mostrar contraseña" title="Mostrar contraseña">${icono("ojo")}</button>
          </span>
        </label>
        ${
          esRegistro
            ? `<label class="casilla">
                 <input type="checkbox" name="categorias" checked>
                 <span>Crear categorías sugeridas (Salario, Comida, Transporte…)</span>
               </label>`
            : ""
        }

        <button type="submit" class="boton boton--primario boton--ancho">${esRegistro ? "Crear cuenta" : "Iniciar sesión"}</button>

        <p class="autenticacion-cambio">
          ${
            esRegistro
              ? `¿Ya tienes cuenta? <a class="enlace" href="#/ingresar">Inicia sesión</a>`
              : `¿No tienes cuenta? <a class="enlace" href="#/registro">Créala gratis</a>`
          }
        </p>
      </form>
    </section>`;

  const formulario = contenedor.querySelector("form");
  const cajaError = contenedor.querySelector(".autenticacion-error");
  const botonEnviar = formulario.querySelector('[type="submit"]');
  const campoContrasena = formulario.elements.contrasena;

  contenedor.querySelector("[data-alternar-contrasena]").addEventListener("click", (evento) => {
    const visible = campoContrasena.type === "text";
    campoContrasena.type = visible ? "password" : "text";
    evento.currentTarget.setAttribute("aria-label", visible ? "Mostrar contraseña" : "Ocultar contraseña");
  });

  formulario.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const datos = new FormData(formulario);
    const email = datos.get("email").trim();
    const contrasena = datos.get("contrasena");
    cajaError.hidden = true;

    if (!email || !contrasena || (esRegistro && !datos.get("nombre").trim())) {
      mostrarError(cajaError, esRegistro ? "Completa nombre, correo y contraseña" : "Escribe tu correo y tu contraseña");
      return;
    }

    botonEnviar.disabled = true;
    botonEnviar.classList.add("cargando");
    try {
      const sesion = esRegistro
        ? await api.auth.registrarse({
            nombre: datos.get("nombre").trim(),
            email,
            contrasena,
            crear_categorias_iniciales: datos.get("categorias") === "on",
          })
        : await api.auth.iniciarSesion(email, contrasena);
      guardarSesion(sesion.access_token, sesion.usuario);
      alEntrar(sesion.usuario, esRegistro);
    } catch (error) {
      mostrarError(cajaError, error.message);
    } finally {
      botonEnviar.disabled = false;
      botonEnviar.classList.remove("cargando");
    }
  });

  formulario.querySelector("input").focus();
}

function mostrarError(caja, mensaje) {
  caja.innerHTML = `${icono("alerta")}<span>${escapar(mensaje)}</span>`;
  caja.hidden = false;
}
