// Vista "Cajas" (negocios): efectivo, bancos y billeteras digitales, con transferencias.
import { api } from "../api.js";
import { avisarCambio } from "../estado.js";
import { icono } from "../iconos.js";
import { botonPrincipal, botonesEdicion, cabecera, cupoDelPlan, enlazarEdicion, estadoVacio } from "../componentes.js";
import { escapar, formatoFecha, formatoMoneda, hoyIso } from "../formato.js";
import { limite, puede } from "../sesion.js";
import { abrirDialogo, notificar } from "../ui.js";
import { establecerFiltros } from "./movimientos.js";

const TIPOS = {
  EFECTIVO: ["efectivo", "Efectivo", "Caja registradora, caja menor"],
  BANCO: ["banco", "Cuenta bancaria", "Bancolombia, Davivienda…"],
  BILLETERA: ["celular", "Billetera digital", "Nequi, Daviplata…"],
};

export async function renderizar(contenedor) {
  const [cajas, transferencias] = await Promise.all([api.cajas.listar(), api.cajas.transferencias()]);
  const total = cajas.reduce((s, c) => s + Number(c.saldo_actual), 0);
  const nombres = new Map(cajas.map((c) => [c.id, c.nombre]));
  const puedeTransferir = puede("GESTIONAR") && cajas.length >= 2;

  contenedor.innerHTML = `
    ${cabecera({
      titulo: "Cajas",
      subtitulo: cajas.length ? `Tienes <b>${formatoMoneda(total)}</b> entre todas tus cajas` : "Dónde está el dinero de tu negocio",
      acciones: `${puedeTransferir ? `<button type="button" class="boton boton--secundario" data-accion="transferir">${icono("movimientos")}<span>Transferir</span></button>` : ""}${botonPrincipal("nueva-caja", "Nueva caja")}`,
    })}
    ${puede("GESTIONAR") ? cupoDelPlan(cajas.length, limite("cajas"), "cajas") : ""}
    ${
      cajas.length
        ? `<div class="rejilla-tarjetas">${cajas.map(tarjeta).join("")}</div>`
        : `<section class="tarjeta">${estadoVacio({
            icono: "billetera",
            titulo: "Aún no tienes cajas",
            texto: "Crea una caja por cada lugar donde guardas dinero: la caja registradora, tu cuenta bancaria o Nequi.",
            accion: botonPrincipal("nueva-caja", "Crear mi primera caja", "boton--secundario"),
          })}</section>`
    }
    <section class="tarjeta tarjeta--tabla">
      <header class="tarjeta-cabecera tarjeta-cabecera--tabla">
        <div><h2 class="tarjeta-titulo">Transferencias entre cajas</h2>
        <p class="tarjeta-subtitulo">Mover dinero no es ingreso ni gasto: no cambia tu saldo total</p></div>
      </header>
      ${
        transferencias.length
          ? `<div class="tabla-contenedor"><table class="tabla">
               <thead><tr><th>Fecha</th><th>Desde</th><th>Hacia</th><th>Detalle</th><th class="num">Monto</th></tr></thead>
               <tbody>${transferencias
                 .map(
                   (t) => `<tr>
                     <td class="celda-fecha">${formatoFecha(t.fecha)}</td>
                     <td>${escapar(nombres.get(t.origen_id) ?? "—")}</td>
                     <td>${escapar(nombres.get(t.destino_id) ?? "—")}</td>
                     <td>${t.descripcion ? escapar(t.descripcion) : '<span class="texto-tenue">—</span>'}</td>
                     <td class="num"><span class="monto">${formatoMoneda(t.monto)}</span></td>
                   </tr>`
                 )
                 .join("")}</tbody></table></div>`
          : estadoVacio({ icono: "movimientos", titulo: "Sin transferencias", texto: "Ejemplo: consignar el efectivo del día en el banco." })
      }
    </section>`;

  contenedor.querySelectorAll("[data-accion='nueva-caja']").forEach((b) => b.addEventListener("click", () => formulario()));
  contenedor.querySelector("[data-accion='transferir']")?.addEventListener("click", () => transferir(cajas));
  enlazarEdicion(contenedor, cajas, { alEditar: (c) => formulario(c), alEliminar: (c) => eliminar(c) });
  contenedor.querySelectorAll("[data-ver-movimientos]").forEach((b) =>
    b.addEventListener("click", () => {
      establecerFiltros({ caja_id: b.dataset.verMovimientos });
      location.hash = "#/movimientos";
    })
  );
}

function tarjeta(caja) {
  const [nombreIcono, tipo] = TIPOS[caja.tipo];
  const saldo = Number(caja.saldo_actual);
  return `
    <article class="tarjeta tarjeta-caja">
      <header class="categoria-cabecera">
        <span class="caja-icono caja-icono--${caja.tipo.toLowerCase()}">${icono(nombreIcono)}</span>
        <div class="categoria-info">
          <h3>${escapar(caja.nombre)}</h3>
          <p>${tipo}</p>
        </div>
        ${botonesEdicion(caja.id, caja.nombre)}
      </header>
      <div>
        <span class="texto-tenue caja-etiqueta">Saldo actual</span>
        <strong class="caja-saldo ${saldo < 0 ? "caja-saldo--negativo" : ""}">${formatoMoneda(saldo)}</strong>
      </div>
      <div class="categoria-pie">
        <span>Saldo inicial ${formatoMoneda(caja.saldo_inicial)}</span>
        <button type="button" class="enlace" data-ver-movimientos="${caja.id}">Ver movimientos${icono("derecha")}</button>
      </div>
    </article>`;
}

function formulario(actual = null) {
  abrirDialogo({
    titulo: actual ? "Editar caja" : "Nueva caja",
    textoConfirmar: actual ? "Guardar cambios" : "Crear caja",
    contenido: `
      <fieldset class="opciones-lista opciones-lista--fila">
        <legend class="campo-etiqueta">Tipo</legend>
        ${Object.entries(TIPOS)
          .map(
            ([valor, [nombreIcono, titulo, ejemplo]]) => `
          <label class="opcion">
            <input type="radio" name="tipo" value="${valor}" ${(actual?.tipo ?? "EFECTIVO") === valor ? "checked" : ""}>
            <span class="opcion-icono">${icono(nombreIcono)}</span>
            <span class="opcion-texto"><strong>${titulo}</strong><span>${ejemplo}</span></span>
          </label>`
          )
          .join("")}
      </fieldset>
      <div class="campos-fila">
        <label class="campo">
          <span class="campo-etiqueta">Nombre</span>
          <input class="entrada" name="nombre" maxlength="60" placeholder="Ej. Caja principal" value="${escapar(actual?.nombre ?? "")}">
        </label>
        <label class="campo">
          <span class="campo-etiqueta">Saldo inicial</span>
          <span class="entrada-prefijo"><span>$</span>
            <input name="saldo_inicial" type="number" inputmode="decimal" step="any" value="${actual ? Number(actual.saldo_inicial) : 0}">
          </span>
        </label>
      </div>`,
    alEnviar: async (datos) => {
      const cuerpo = {
        nombre: datos.get("nombre").trim(),
        tipo: datos.get("tipo"),
        saldo_inicial: Number(datos.get("saldo_inicial") || 0),
      };
      if (actual) await api.cajas.actualizar(actual.id, cuerpo);
      else await api.cajas.crear(cuerpo);
      notificar(actual ? "Caja actualizada" : "Caja creada");
      avisarCambio();
    },
  });
}

function transferir(cajas) {
  const opciones = (seleccion) =>
    cajas.map((c, i) => `<option value="${c.id}" ${i === seleccion ? "selected" : ""}>${escapar(c.nombre)} · ${formatoMoneda(c.saldo_actual)}</option>`).join("");
  abrirDialogo({
    titulo: "Transferir entre cajas",
    descripcion: "Por ejemplo, consignar el efectivo del día en el banco.",
    textoConfirmar: "Transferir",
    contenido: `
      <div class="campos-fila">
        <label class="campo"><span class="campo-etiqueta">Desde</span><select class="entrada" name="origen_id">${opciones(0)}</select></label>
        <label class="campo"><span class="campo-etiqueta">Hacia</span><select class="entrada" name="destino_id">${opciones(1)}</select></label>
      </div>
      <div class="campos-fila">
        <label class="campo">
          <span class="campo-etiqueta">Monto</span>
          <span class="entrada-prefijo"><span>$</span><input name="monto" type="number" inputmode="decimal" step="any" placeholder="0"></span>
        </label>
        <label class="campo"><span class="campo-etiqueta">Fecha</span><input class="entrada" name="fecha" type="date" max="${hoyIso()}" value="${hoyIso()}"></label>
      </div>
      <label class="campo">
        <span class="campo-etiqueta">Detalle <span class="texto-tenue">(opcional)</span></span>
        <input class="entrada" name="descripcion" maxlength="255" placeholder="Ej. Consignación ventas del día">
      </label>`,
    alEnviar: async (datos) => {
      await api.cajas.transferir({
        origen_id: Number(datos.get("origen_id")),
        destino_id: Number(datos.get("destino_id")),
        monto: Number(datos.get("monto")),
        fecha: datos.get("fecha"),
        descripcion: datos.get("descripcion").trim(),
      });
      notificar("Transferencia registrada");
      avisarCambio();
    },
  });
}

function eliminar(caja) {
  abrirDialogo({
    titulo: "¿Eliminar caja?",
    descripcion: `Se eliminará <b>${escapar(caja.nombre)}</b>. Solo es posible si no tiene movimientos ni transferencias.`,
    textoConfirmar: "Eliminar",
    peligro: true,
    alEnviar: async () => {
      await api.cajas.eliminar(caja.id);
      notificar("Caja eliminada");
      avisarCambio();
    },
  });
}
