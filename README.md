# Mis Finanzas · Control de Gastos

Aplicación web de finanzas para **personas y negocios**. Al registrarse cada
usuario elige el tipo de cuenta: según eso se le piden distintos datos y se
activan distintas funciones. Los negocios pueden invitar a su equipo con
permisos limitados, y hay un modelo de suscripción **Gratis / Pro**.
Proyecto académico de Construcción de Software.

**Stack:** Python 3.11+, FastAPI, SQLAlchemy, Alembic, PostgreSQL, pytest, JWT, openpyxl.
Interfaz en HTML, CSS y JavaScript sin librerías ni pasos de compilación.

## Tipos de cuenta y funciones

| Función | Personal | Negocio |
|---|:---:|:---:|
| Movimientos, categorías, panel con gráficos | ✓ | ✓ |
| Presupuesto mensual y **por categoría**, con alertas | ✓ | ✓ |
| **Movimientos recurrentes** (se registran solos cada mes) | ✓ | ✓ |
| **Exportar** a CSV, Excel (Pro) o PDF (imprimir) | ✓ | ✓ |
| Deudas y préstamos / **cuentas por cobrar y pagar** | ✓ | ✓ |
| **Metas de ahorro** con sugerencia de ahorro mensual | ✓ | — |
| **Cajas** (efectivo, banco, Nequi) y transferencias | — | ✓ |
| **Equipo**: empleado y contador | — | ✓ |
| **Comprobantes** adjuntos (foto o PDF) | — | ✓ (Pro) |

Al registrarse:
- **Personal:** nombre y objetivo principal (ahorrar, salir de deudas…).
- **Negocio:** nombre del negocio, sector, NIT y persona responsable.
- En ambos casos se aceptan los términos y la política de tratamiento de
  datos (Ley 1581 de 2012) y se pueden crear categorías sugeridas según el tipo.

## Roles y permisos

Hay dos ejes independientes, definidos en [`app/permisos.py`](app/permisos.py)
(la única fuente de verdad: el backend los hace cumplir y la interfaz los
recibe en `/auth/yo` para mostrar u ocultar opciones):

| Rol dentro del negocio | Ver movimientos | Registrar | Ver reportes | Exportar | Editar / configurar | Gestionar equipo |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Propietario (o cuenta personal) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ (negocio) |
| Empleado | ✓ | ✓ | — | — | — | — |
| Contador | ✓ | — | ✓ | ✓ | — | — |

El **administrador de la plataforma** es otro rol, con su propia **consola de
administración** (barra lateral azul marino y etiqueta ADMIN):

- **Resumen:** ingreso mensual estimado, cuentas de clientes, conversión a Pro,
  cuentas nuevas y uso por mes, distribución por tipo y plan, últimos registros.
- **Usuarios:** búsqueda y filtros (personales, negocios, equipos, Pro,
  desactivadas); activar o desactivar cuentas y cambiar plan o rol.
- **Solicitudes Pro:** bandeja para activar el plan o descartar la solicitud.
- **Mi cuenta:** nombre y contraseña.

Un administrador **no lleva finanzas propias**: no tiene permisos ni funciones
financieras y la API le responde 403 si lo intenta. Tampoco ve nunca montos
ni movimientos de los usuarios, solo cantidades.

## Planes

Definidos en [`app/planes.py`](app/planes.py). Los límites son reglas de
negocio de la capa de servicios; al superarlos la API responde **HTTP 402**.

| | Gratis | Pro |
|---|---|---|
| Precio (referencia) | $0 | $9.900/mes personal · $39.900/mes negocio |
| Recurrentes | 3 | 50 |
| Metas de ahorro | 2 | 20 |
| Cajas | 2 | 20 |
| Miembros del equipo | 1 | 10 |
| Exportar | CSV | CSV y Excel |
| Comprobantes | — | ✓ |

Todavía no hay pasarela de pago: el usuario **solicita** el plan Pro y un
administrador lo activa desde la sección Usuarios.

## Arquitectura por capas

```
app/
├── main.py           # Crea la app, registra routers, traduce errores a HTTP y sirve la interfaz
├── config.py         # Configuración por variables de entorno
├── permisos.py       # Qué puede hacer cada rol y qué funciones tiene cada tipo de cuenta
├── planes.py         # Límites y precios de los planes
├── catalogos.py      # Objetivos, sectores y categorías sugeridas
├── seguridad.py      # Cifrado de contraseñas (PBKDF2) y tokens de sesión (JWT)
├── migraciones.py    # Aplica las migraciones de Alembic al arrancar
├── database.py       # Conexión a la BD y sesión por petición
├── models/           # Entidades: Usuario, Categoria, Movimiento, Presupuesto,
│                     #   PresupuestoCategoria, Recurrente, Meta, Deuda, Caja,
│                     #   Transferencia, Comprobante
├── schemas/          # Validación de entrada y forma de salida (Pydantic)
├── repositories/     # Acceso a datos; base.py filtra SIEMPRE por el dueño de los datos
├── services/         # Reglas de negocio (no conocen HTTP); autorizacion.py aplica permisos y planes
├── controllers/      # Endpoints; dependencias.py identifica al usuario y arma cada servicio
└── static/           # Interfaz web (capa de presentación)
    ├── css/estilos.css
    └── js/           # app.js (navegación por permisos), api.js, sesion.js, vistas/...
migraciones/          # Migraciones de Alembic (historial de cambios de la base)
tests/                # Pruebas unitarias y de integración con pytest
seed.py               # Cuentas y datos de demostración
docker-compose.yml    # PostgreSQL del proyecto
```

Flujo de una petición: **interfaz → controlador → servicio → repositorio → base de datos**.

- **Aislamiento de datos:** cada registro tiene un `usuario_id` (su dueño).
  Los repositorios heredan de `RepositorioDelTitular`, que filtra todas las
  consultas por el dueño. Los miembros de un equipo trabajan sobre los datos
  del negocio (`titular_id`). Pedir un registro ajeno responde 404.
- **Inyección de dependencias:** cada endpoint declara el servicio y el
  permiso que necesita, por ejemplo
  `Depends(servicio(ServicioCajas, Permiso.GESTIONAR, Funcion.CAJAS))`;
  FastAPI verifica sesión, permiso y función antes de ejecutarlo.
- **La interfaz no tiene reglas de negocio:** envía los datos a la API y
  muestra sus mensajes de error tal como llegan.

### Principios SOLID aplicados
- **S:** cada capa y clase tiene una tarea (`seguridad.py` solo cifra y firma,
  `autorizacion.py` solo decide si se permite algo, cada servicio una entidad).
- **O:** las funciones nuevas (cajas, metas, equipo…) se agregaron con
  nuevos modelos, repositorios, servicios y routers, sin cambiar las reglas
  existentes; los permisos se amplían editando una tabla, no los endpoints.
- **L:** todos los repositorios de datos heredan de `RepositorioDelTitular` y
  pueden usarse donde se espera la base; todas las excepciones heredan de
  `ErrorDeAplicacion`.
- **I:** cada repositorio expone solo los métodos que su entidad necesita.
- **D:** los servicios reciben la sesión y el usuario por inyección; no
  dependen de FastAPI, por eso se prueban también sin HTTP.

### Manejo de errores

| Excepción             | HTTP | Ejemplo                                   |
|-----------------------|------|-------------------------------------------|
| `ErrorDeValidacion`   | 400  | Monto ≤ 0, fecha futura, abono mayor que la deuda |
| `NoAutenticado`       | 401  | Sin sesión, token vencido, clave incorrecta |
| `LimiteDelPlan`       | 402  | Cuarto recurrente o Excel en el plan Gratis |
| `SinPermiso`          | 403  | Empleado intentando eliminar, cuenta personal entrando a Cajas |
| `RecursoNoEncontrado` | 404  | Registro inexistente (o de otra cuenta)   |
| `ConflictoDeDatos`    | 409  | Correo o nombre duplicado, categoría o caja en uso |

Los errores de tipo (p. ej. texto en `monto`) los responde FastAPI con 422.

## Seguridad
- Contraseñas con hash PBKDF2-SHA256, sal aleatoria y 600.000 iteraciones (OWASP).
- Sesión con JWT firmado que vence en 8 horas; en cada petición se verifica
  que la cuenta (y la del negocio, si es un miembro) siga activa.
- El inicio de sesión responde igual (mensaje y tiempo) si el correo no existe
  o si la clave es incorrecta.
- Comprobantes: solo JPG, PNG, WEBP o PDF de hasta 2 MB.
- Todo texto del usuario se escapa antes de mostrarse en la interfaz.

## Instalación

1. Encender PostgreSQL con Docker Desktop abierto:
   ```powershell
   docker compose up -d
   ```
   Crea el contenedor `control_gastos_db` (base `control_gastos`, usuario y
   contraseña `postgres`) en el puerto **5434**.
2. Crear el entorno virtual e instalar dependencias (PowerShell):
   ```powershell
   py -3.12 -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements-dev.txt     # incluye pytest; en producción basta requirements.txt
   ```
3. Variables de entorno (opcionales en desarrollo):

   | Variable | Para qué sirve | Por defecto |
   |----------|----------------|-------------|
   | `DATABASE_URL` | Conexión a PostgreSQL | `postgresql+psycopg2://postgres:postgres@localhost:5434/control_gastos` |
   | `CLAVE_SECRETA` | Firma las sesiones. **Obligatoria en producción** | Clave de desarrollo (la app avisa) |
   | `MINUTOS_EXPIRACION_TOKEN` | Duración de la sesión | `480` |

## Ejecutar la aplicación

La forma más simple (Windows, no hace falta activar el entorno virtual):

```powershell
.\iniciar.bat
```

Enciende PostgreSQL con Docker y arranca la app en el puerto 8000 (otro
puerto: `.\iniciar.bat 8080`). Para cargar los datos de demostración, una vez:

```powershell
.venv\Scripts\python.exe seed.py
```

Equivalente manual, con el entorno virtual activado (`.venv\Scripts\activate`):

```bash
python seed.py
uvicorn app.main:app --reload --reload-dir app
```

Si PowerShell dice que `uvicorn` o `python` "no se reconoce", es porque el
entorno virtual no está activado en esa terminal: usa `.\iniciar.bat`.

- Interfaz web: <http://localhost:8000>
- Documentación de la API: <http://localhost:8000/docs> (botón **Authorize**
  con correo y contraseña para probar los endpoints protegidos).

## Migraciones de la base de datos

La estructura de la base se versiona con **Alembic** (`migraciones/versions/`).
Al arrancar, la app aplica sola las migraciones pendientes **sin borrar
datos**. Comandos útiles:

```bash
alembic upgrade head                    # aplicar migraciones pendientes
alembic revision -m "descripcion"       # crear una migración nueva
alembic history                         # ver el historial
```

Las pruebas usan SQLite en memoria y crean las tablas directamente.

### Cuentas de demostración

Las crea `python seed.py`. Son **solo para la demostración**.

| Cuenta | Correo | Contraseña | Qué muestra |
|--------|--------|------------|-------------|
| Administrador | `admin@misfinanzas.test` | `Admin12345` | Sección Usuarios, métricas, solicitudes de Pro |
| Personal (Gratis) | `demo@misfinanzas.test` | `Demo12345` | 6 meses de datos, metas (en el límite del plan), deudas, recurrentes, solicitud de Pro pendiente |
| Negocio (Pro) | `espiga@misfinanzas.test` | `Espiga12345` | Panadería con cajas, transferencias, cuentas por cobrar/pagar, equipo |
| Empleada | `laura@misfinanzas.test` | `Empleado12345` | Solo registra y ve movimientos de la panadería |
| Contador | `contador@misfinanzas.test` | `Contador12345` | Ve y exporta todo, no puede editar |
| Desactivada | `inactiva@misfinanzas.test` | `Inactiva12345` | No puede iniciar sesión |

## Correr las pruebas

```bash
pytest --cov=app --cov-report=term-missing
```

Cubren reglas de negocio, autenticación, aislamiento entre cuentas, tipos de
cuenta, roles del equipo, límites de planes, recurrentes, presupuestos por
categoría, exportación, metas, deudas, cajas, comprobantes y administración.

## Endpoints

Todos, salvo `/auth/registro`, `/auth/login` y `/auth/opciones-registro`,
exigen `Authorization: Bearer <token>`. La lista completa con ejemplos está
en `/docs`.

| Grupo | Rutas |
|-------|-------|
| Autenticación y cuenta | `POST /auth/registro`, `POST /auth/login`, `GET /auth/opciones-registro`, `GET·PATCH /auth/yo`, `PUT /auth/yo/contrasena` |
| Planes | `GET /planes`, `POST /planes/solicitar-pro` |
| Equipo (negocio) | `GET·POST /equipo`, `PATCH·DELETE /equipo/{id}` |
| Categorías | `GET·POST /categorias`, `GET·PUT·DELETE /categorias/{id}` |
| Movimientos | `GET·POST /movimientos` (filtros `fecha_inicio`, `fecha_fin`, `categoria_id`, `caja_id`), `GET·PUT·DELETE /movimientos/{id}` |
| Comprobantes (negocio) | `POST·GET·DELETE /movimientos/{id}/comprobante` |
| Presupuestos | `GET·POST /presupuestos`, `GET /presupuestos/{mes}/estado`, `PUT·DELETE /presupuestos/{id}` |
| Presupuesto por categoría | `GET /presupuestos/categorias?mes=`, `PUT·DELETE /presupuestos/categorias/{categoria_id}` |
| Recurrentes | `GET·POST /recurrentes`, `POST /recurrentes/generar`, `PATCH·DELETE /recurrentes/{id}` |
| Reportes | `GET /reportes/saldo`, `GET /reportes/resumen-mensual?mes=`, `GET /reportes/exportar?mes=&formato=csv\|xlsx` |
| Metas (personal) | `GET·POST /metas`, `POST /metas/{id}/aportes`, `PATCH·DELETE /metas/{id}` |
| Deudas | `GET·POST /deudas` (filtro `tipo`), `POST /deudas/{id}/abonos`, `PATCH·DELETE /deudas/{id}` |
| Cajas (negocio) | `GET·POST /cajas`, `PATCH·DELETE /cajas/{id}`, `GET·POST /cajas/transferencias` |
| Administración | `GET /admin/usuarios`, `GET /admin/estadisticas`, `PATCH /admin/usuarios/{id}` |

## Reglas de negocio
- El monto debe ser mayor que 0 y no se permiten fechas futuras.
- Todo movimiento debe tener una categoría (y caja, si se indica) de la misma cuenta.
- No se puede eliminar una categoría con movimientos o recurrentes, ni una caja con movimientos o transferencias.
- Saldo = suma de ingresos − suma de gastos; saldo de una caja = saldo inicial + ingresos − gastos + transferencias recibidas − enviadas.
- Una transferencia no puede superar el saldo de la caja de origen ni ir a la misma caja.
- Un abono no puede superar el saldo pendiente de la deuda.
- Los recurrentes se registran el día elegido (1 a 28) de cada mes, una sola vez por mes.
- Al registrar un gasto que supera el presupuesto del mes o el límite de su categoría, la respuesta trae la alerta.
- Los límites de cada plan se verifican al crear recurrentes, metas, cajas y miembros, al exportar a Excel y al adjuntar comprobantes.

## Publicar en Vercel

La app funciona en [Vercel](https://vercel.com) sin cambios de código: Vercel
detecta FastAPI en `app/main.py`, instala `requirements.txt` y sirve la
interfaz. La base de datos es PostgreSQL de **Neon** (plan gratuito).

1. En Vercel: **Add New → Project**, importa el repositorio de GitHub y pulsa
   **Deploy** (el primer despliegue fallará porque aún no hay base ni clave; es normal).
2. En el proyecto: **Storage → Create Database → Neon** y conéctala al
   proyecto. Vercel agrega sola la variable `DATABASE_URL`.
3. En **Settings → Environment Variables** agrega:

   | Variable | Valor |
   |----------|-------|
   | `CLAVE_SECRETA` | Una clave larga y aleatoria. Genérala con `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
   | `CARGAR_DATOS_DEMO` | `1` si quieres las cuentas de demostración (se cargan solo si la base está vacía) |

4. **Deployments → Redeploy**. Al arrancar, la app aplica las migraciones en
   Neon y, si lo pediste, carga la demostración.

Cada `git push` a `main` publica una versión nueva automáticamente.
Sin `CLAVE_SECRETA` la app **no arranca** en Vercel: la clave de desarrollo
está en este repositorio público y con ella cualquiera podría fabricar sesiones.

## Antes de ponerla en producción
- Integrar una pasarela de pago (Wompi, PayU o Mercado Pago) para cobrar el plan Pro.
- Enviar correos: recuperar contraseña, verificar correo y alertas de presupuesto.
- Limitar los intentos de inicio de sesión y ofrecer verificación en dos pasos.
- Revisar con un abogado los términos y la política de datos (el texto actual es una plantilla).
- Copias de seguridad automáticas de la base de datos.
