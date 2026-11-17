// Vista "Categorías": crear, renombrar y eliminar categorías.
import { api } from "../api.js";
import { avisarCambio } from "../estado.js";
import { icono } from "../iconos.js";
import { cabecera, estadoVacio } from "../componentes.js";
import { escapar, formatoMoneda, mesActual, nombreMesSolo } from "../formato.js";
import { abrirDialogo, notificar } from "../ui.js";

export async function renderizar(contenedor) {
  const mes = mesActual();
  const [categorias, movimientos, resumen] = await Promise.all([
    api.categorias.listar(),
    api.movimientos.listar(),
    api.reportes.resumenMensual(mes),
  ]);

  const cantidad = new Map();
  for (const m of movimientos) cantidad.set(m.categoria_id, (cantidad.get(m.categoria_id) ?? 0) + 1);
  const totalesMes = new Map(
    resumen.categorias.map((c) => [c.categoria_id, { ingresos: Number(c.total_ingresos), gastos: Number(c.total_gastos) }])
  );

  contenedor.innerHTML = `
    ${cabecera({ titulo: "Categorías", subtitulo: "Organiza tus movimientos por tipo de ingreso o gasto" })}

    <form class="tarjeta formulario-linea" aria-label="Nueva categoría">
      <label class="campo">
        <span class="sr-only">Nombre de la nueva categoría</span>
        <input class="entrada" name="nombre" maxlength="50" placeholder="Nombre de la nueva categoría, por ejemplo «Mascotas»" autocomplete="off">
      </label>
      <button type="submit" class="boton boton--primario">${icono("mas")}Agregar categoría</button>
    </form>

    ${
      categorias.length
        ? `<div class="rejilla-tarjetas">${categorias
            .map((c) => tarjetaCategoria(c, cantidad.get(c.id) ?? 0, totalesMes.get(c.id), mes))
            .join("")}</div>`
        : `<section class="tarjeta">${estadoVacio({ icono: "etiqueta", titulo: "Aún no hay categorías", texto: "Crea tu primera categoría para empezar a registrar movimientos." })}</section>`
    }`;

  const formulario = contenedor.querySelector(".formulario-linea");
  formulario.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const nombre = new FormData(formulario).get("nombre").trim();
    if (!nombre) {
      notificar("Escribe un nombre para la categoría", "advertencia");
      return;
    }
    try {
      await api.categorias.crear({ nombre });
      notificar(`Categoría «${nombre}» creada`);
      avisarCambio();
    } catch (error) {
      notificar(error.message, "error");
    }
  });

  const buscar = (id) => categorias.find((c) => c.id === Number(id));
  contenedor.querySelectorAll("[data-editar]").forEach((boton) =>
    boton.addEventListener("click", () => renombrar(buscar(boton.dataset.editar)))
  );
  contenedor.querySelectorAll("[data-eliminar]").forEach((boton) =>
    boton.addEventListener("click", () => eliminar(buscar(boton.dataset.eliminar)))
  );
}

function tarjetaCategoria(categoria, cantidadMovimientos, totales = { ingresos: 0, gastos: 0 }, mes) {
  const nombre = escapar(categoria.nombre);
  // Una categoría de ingresos (ej. Salario) muestra lo recibido, no lo gastado.
  const esDeIngresos = totales.ingresos > totales.gastos;
  const sinMovimientos = !totales.ingresos && !totales.gastos;
  const etiquetaPie = sinMovimientos
    ? `Sin movimientos en ${nombreMesSolo(mes)}`
    : `${esDeIngresos ? "Ingresado" : "Gastado"} en ${nombreMesSolo(mes)}`;
  const valorPie = sinMovimientos ? "—" : formatoMoneda(esDeIngresos ? totales.ingresos : totales.gastos);
  return `
    <article class="tarjeta tarjeta-categoria">
      <div class="categoria-cabecera">
        <span class="categoria-avatar" aria-hidden="true">${escapar(categoria.nombre.charAt(0).toUpperCase())}</span>
        <div class="categoria-info">
          <h3 title="${nombre}">${nombre}</h3>
          <p>${cantidadMovimientos} ${cantidadMovimientos === 1 ? "movimiento" : "movimientos"}</p>
        </div>
        <div class="categoria-acciones">
          <button type="button" class="boton-icono" data-editar="${categoria.id}" aria-label="Renombrar ${nombre}" title="Renombrar">${icono("lapiz")}</button>
          <button type="button" class="boton-icono boton-icono--peligro" data-eliminar="${categoria.id}" aria-label="Eliminar ${nombre}" title="Eliminar">${icono("papelera")}</button>
        </div>
      </div>
      <div class="categoria-pie">
        <span>${etiquetaPie}</span>
        <b>${valorPie}</b>
      </div>
    </article>`;
}

function renombrar(categoria) {
  abrirDialogo({
    titulo: "Renombrar categoría",
    textoConfirmar: "Guardar",
    contenido: `
      <label class="campo">
        <span class="campo-etiqueta">Nombre</span>
        <input class="entrada" name="nombre" maxlength="50" value="${escapar(categoria.nombre)}" autocomplete="off">
      </label>`,
    alEnviar: async (datos) => {
      await api.categorias.actualizar(categoria.id, { nombre: datos.get("nombre").trim() });
      notificar("Categoría actualizada");
      avisarCambio();
    },
  });
}

function eliminar(categoria) {
  abrirDialogo({
    titulo: "¿Eliminar categoría?",
    descripcion: `Se eliminará <b>${escapar(categoria.nombre)}</b>. Solo es posible si no tiene movimientos asociados.`,
    textoConfirmar: "Eliminar",
    peligro: true,
    alEnviar: async () => {
      await api.categorias.eliminar(categoria.id);
      notificar("Categoría eliminada");
      avisarCambio();
    },
  });
}
