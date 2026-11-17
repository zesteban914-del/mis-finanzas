// Diálogo para exportar el reporte de un mes: CSV, Excel (Pro) o PDF (imprimir).
import { api } from "../api.js";
import { insigniaPro } from "../componentes.js";
import { nombreMes } from "../formato.js";
import { icono } from "../iconos.js";
import { puede } from "../sesion.js";
import { abrirDialogo, guardarArchivo, notificar } from "../ui.js";

const FORMATOS = [
  ["csv", "documento", "CSV", "Para abrir en Excel o Google Sheets. Disponible en todos los planes."],
  ["xlsx", "tabla", `Excel ${insigniaPro()}`, "Libro con hoja de resumen y de movimientos, con formato de pesos."],
  ["pdf", "imprimir", "PDF / imprimir", "Imprime el panel o guárdalo como PDF desde el navegador."],
];

export const botonExportar = () =>
  puede("EXPORTAR")
    ? `<button type="button" class="boton boton--secundario" data-accion="exportar">${icono("descargar")}<span>Exportar</span></button>`
    : "";

export function abrirExportacion(mes) {
  abrirDialogo({
    titulo: "Exportar reporte",
    descripcion: `Movimientos y resumen de ${nombreMes(mes)}.`,
    textoConfirmar: "Descargar",
    contenido: `
      <fieldset class="opciones-lista">
        <legend class="sr-only">Formato</legend>
        ${FORMATOS.map(
          ([valor, nombreIcono, titulo, texto], i) => `
          <label class="opcion">
            <input type="radio" name="formato" value="${valor}" ${i === 0 ? "checked" : ""}>
            <span class="opcion-icono">${icono(nombreIcono)}</span>
            <span class="opcion-texto"><strong>${titulo}</strong><span>${texto}</span></span>
          </label>`
        ).join("")}
      </fieldset>`,
    alEnviar: async (datos) => {
      const formato = datos.get("formato");
      if (formato === "pdf") {
        setTimeout(() => window.print(), 300); // después de cerrar el diálogo
        return;
      }
      guardarArchivo(await api.reportes.exportar(mes, formato));
      notificar("Reporte descargado");
    },
  });
}
