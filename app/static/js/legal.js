// Términos y política de tratamiento de datos (Ley 1581 de 2012, Colombia).
// PLANTILLA: debe revisarla un abogado y completarse con los datos reales
// del responsable antes de publicar la aplicación.
import { abrirDialogo } from "./ui.js";

const POLITICA = `
  <div class="texto-legal">
    <p class="aviso-plantilla">Plantilla de ejemplo: debe revisarla un abogado antes de publicar la aplicación.</p>
    <h3>1. Responsable del tratamiento</h3>
    <p>Mis Finanzas (razón social, NIT, dirección y correo de contacto por completar).</p>
    <h3>2. Datos que recolectamos</h3>
    <p>Nombre, correo electrónico y, en cuentas de negocio, sector, NIT y persona responsable.
       También los ingresos, gastos, presupuestos y demás registros que tú mismo ingresas.</p>
    <h3>3. Finalidad</h3>
    <p>Prestar el servicio de control de finanzas: guardar tus registros, calcular reportes y
       enviarte alertas dentro de la aplicación. No vendemos ni compartimos tus datos con terceros
       para publicidad.</p>
    <h3>4. Tus derechos</h3>
    <p>Puedes conocer, actualizar, rectificar y solicitar la eliminación de tus datos, y revocar
       esta autorización, escribiendo al correo de contacto. Responderemos en los plazos de la ley.</p>
    <h3>5. Seguridad</h3>
    <p>Tu contraseña se guarda cifrada y nadie, ni siquiera el administrador de la plataforma,
       puede ver tus movimientos o montos.</p>
    <h3>6. Términos de uso</h3>
    <p>La aplicación es una herramienta de registro y no constituye asesoría financiera, contable
       ni tributaria. El plan Gratis puede usarse sin costo; el plan Pro tiene el precio publicado
       en la sección de planes.</p>
  </div>`;

export function mostrarPolitica() {
  abrirDialogo({
    titulo: "Términos y política de tratamiento de datos",
    descripcion: "Ley 1581 de 2012 (protección de datos personales en Colombia)",
    contenido: POLITICA,
    textoConfirmar: "Entendido",
    sinCancelar: true,
    ancho: true,
  });
}
