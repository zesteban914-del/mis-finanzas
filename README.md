# Mis Finanzas · Control de Gastos

Aplicación web multiusuario para registrar ingresos y gastos, administrar
categorías, consultar el saldo, ver un resumen mensual por categoría y
controlar un presupuesto mensual. Cada persona o negocio tiene su propia
cuenta y solo ve sus datos; un administrador gestiona las cuentas.
Proyecto académico de Construcción de Software.

**Stack:** Python 3.11+, FastAPI, SQLAlchemy, PostgreSQL, pytest, JWT.
Interfaz en HTML, CSS y JavaScript sin librerías ni pasos de compilación.

## Arquitectura por capas

```
app/
├── main.py           # Crea la app, registra routers, traduce errores a HTTP y sirve la interfaz
├── config.py         # Configuración por variables de entorno (clave secreta, expiración...)
├── seguridad.py      # Cifrado de contraseñas (PBKDF2) y tokens de sesión (JWT)
├── database.py       # Conexión a la BD y sesión por petición
├── models/           # Entidades: Usuario, Categoria, Movimiento, Presupuesto
├── schemas/          # Validación de entrada y forma de salida (Pydantic)
├── repositories/     # Acceso a datos (patrón Repository), siempre filtrado por usuario
├── services/         # Reglas de negocio y cálculos (no conocen HTTP)
├── controllers/      # Endpoints; dependencias.py identifica al usuario por su token
└── static/           # Interfaz web (capa de presentación)
    ├── index.html
    ├── css/estilos.css      # Diseño: colores claro/oscuro, componentes, responsive
    └── js/
        ├── app.js           # Sesión, navegación entre vistas, tema y atajos
        ├── api.js           # Único módulo que llama a la API (agrega el token)
        ├── sesion.js        # Guarda el token y los datos del usuario
        ├── formato.js       # Dinero (COP) y fechas en español
        ├── componentes.js   # Piezas de HTML reutilizables (KPIs, medidor, etc.)
        ├── graficos.js      # Gráficos de barras y columnas hechos con CSS
        ├── ui.js            # Notificaciones, diálogo modal y tooltip
        └── vistas/          # Ingreso/registro, Panel, Movimientos, Categorías,
                             # Presupuestos, Usuarios (admin) y formularios
tests/                # Pruebas unitarias y de integración con pytest
seed.py               # Cuentas y datos de demostración
docker-compose.yml    # PostgreSQL del proyecto
```

Flujo de una petición: **interfaz → controlador → servicio → repositorio → base de datos**.
Cada capa solo conoce a la de abajo. La interfaz no tiene reglas de negocio:
envía los datos a la API y muestra sus mensajes de error tal como llegan
(por ejemplo "El monto debe ser mayor que 0").

## Usuarios, roles y seguridad

| Rol | Qué puede hacer |
|-----|-----------------|
| **Usuario** | Registrarse, iniciar sesión y gestionar **solo sus propias** categorías, movimientos y presupuestos. |
| **Administrador** | Lo mismo que un usuario con sus propios datos, más la sección **Usuarios**: ver las cuentas, cuántos movimientos tiene cada una, activar o desactivar cuentas y dar o quitar el rol de administrador. |

- **Privacidad:** el administrador **no** puede ver montos, descripciones ni
  movimientos de otras personas; solo datos de la cuenta y cantidades.
- **Aislamiento:** cada categoría, movimiento y presupuesto tiene un
  `usuario_id`. Los repositorios se crean para un usuario y todas sus consultas
  filtran por él. Si alguien pide un registro ajeno recibe 404, como si no
  existiera (así no se revela que existe).
- **Contraseñas:** nunca se guardan; se guarda un hash PBKDF2-SHA256 con sal
  aleatoria y 600.000 iteraciones (recomendación OWASP). Deben tener mínimo 8
  caracteres con letras y números.
- **Sesión:** al iniciar sesión la API entrega un token JWT firmado que vence en
  8 horas. La interfaz lo envía en cada petición (`Authorization: Bearer ...`).
  En cada petición se verifica que la cuenta siga activa: si el administrador
  la desactiva, el acceso se corta de inmediato.
- **Inicio de sesión:** el mensaje de error es el mismo si el correo no existe
  o si la contraseña es incorrecta, y el tiempo de respuesta también, para no
  revelar qué correos están registrados.
- **Protecciones de la cuenta admin:** un administrador no puede desactivarse
  ni quitarse el rol a sí mismo (evita quedarse sin administradores).

### Cuentas de demostración

`python seed.py` crea estas cuentas. Son **solo para la demostración**; cambia
o elimina estas contraseñas antes de usar la app con personas reales.

| Cuenta | Correo | Contraseña | Contenido |
|--------|--------|------------|-----------|
| Administrador | `admin@misfinanzas.test` | `Admin12345` | Acceso a la sección Usuarios |
| Usuario demo | `demo@misfinanzas.test` | `Demo12345` | 6 meses de movimientos y 3 presupuestos |
| Negocio | `espiga@misfinanzas.test` | `Espiga12345` | Una panadería con pocos movimientos |
| Inactiva | `inactiva@misfinanzas.test` | `Inactiva12345` | Cuenta desactivada (no puede entrar) |

## Interfaz web

Al abrir <http://localhost:8000> aparece la pantalla para **iniciar sesión** o
**crear una cuenta** (con la opción de empezar con categorías sugeridas).
Dentro de la aplicación:

- **Panel:** saldo actual, ingresos, gastos y balance del mes (con la variación
  frente al mes anterior), estado del presupuesto, gastos por categoría,
  ingresos vs. gastos de los últimos 6 meses y movimientos recientes. Con las
  flechas se cambia de mes.
- **Movimientos:** tabla con filtros por rango de fechas, categoría y tipo;
  crear, editar y eliminar.
- **Categorías:** crear, renombrar y eliminar (si tiene movimientos, la API lo
  impide y la interfaz muestra el motivo).
- **Presupuestos:** un límite por mes con su barra de uso y estado.
- **Usuarios** (solo administradores): estadísticas generales, búsqueda y
  gestión de cuentas.

Detalles de diseño: modo claro y oscuro, versión para celular, colores fijos
(azul = ingresos, naranja = gastos), estados del presupuesto con icono y texto
(no solo color), cada gráfico tiene también vista de tabla, y la tecla **N**
abre el formulario de nuevo movimiento.

### Principios SOLID aplicados
- **S (Responsabilidad única):** cada capa y cada clase tiene una sola tarea
  (p. ej. `RepositorioMovimientos` solo consulta, `ServicioMovimientos` solo
  aplica reglas, `seguridad.py` solo cifra y firma).
- **O (Abierto/cerrado):** se agregan recursos nuevos con nuevos routers,
  servicios y repositorios sin modificar los existentes (así se agregaron
  autenticación y administración).
- **L (Sustitución de Liskov):** todas las excepciones de negocio heredan de
  `ErrorDeAplicacion` y pueden usarse donde se espera la clase base.
- **I (Segregación de interfaces):** cada repositorio expone solo los métodos
  que su entidad necesita.
- **D (Inversión de dependencias):** los servicios no dependen de FastAPI. La
  sesión de BD, el usuario actual y cada servicio se inyectan con `Depends`
  (ver `controllers/dependencias.py`), lo que permite usar SQLite en memoria
  en las pruebas.

### Manejo de errores
Los servicios lanzan excepciones de negocio y `main.py` las convierte en
respuestas JSON `{"detalle": "..."}`:

| Excepción             | HTTP | Ejemplo                                   |
|-----------------------|------|-------------------------------------------|
| `ErrorDeValidacion`   | 400  | Monto ≤ 0, fecha futura, contraseña débil |
| `NoAutenticado`       | 401  | Sin sesión, token vencido, clave incorrecta |
| `SinPermiso`          | 403  | Usuario normal entrando a administración, cuenta desactivada |
| `RecursoNoEncontrado` | 404  | Categoría o movimiento inexistente (o de otro usuario) |
| `ConflictoDeDatos`    | 409  | Nombre o correo duplicado, categoría con movimientos |

Los errores de tipo (p. ej. enviar texto en `monto`) los responde FastAPI con 422.

## Instalación

1. Encender PostgreSQL. La forma recomendada es con Docker Desktop abierto:
   ```powershell
   docker compose up -d
   ```
   Esto crea un contenedor `control_gastos_db` con la base `control_gastos`
   (usuario y contraseña `postgres`) en el puerto **5434**, para no chocar con
   otro PostgreSQL que ya use el 5432. Para apagarlo: `docker compose down`.

   Si prefieres un PostgreSQL instalado en Windows, crea la base con
   `CREATE DATABASE control_gastos;` y ajusta `DATABASE_URL` (paso 3).
2. Crear el entorno virtual e instalar dependencias (PowerShell en Windows):
   ```powershell
   py -3.12 -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
   En Linux/Mac la activación es `source .venv/bin/activate`. Si PowerShell
   responde que la ejecución de scripts está deshabilitada, ejecuta una vez
   `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
3. Variables de entorno (todas opcionales en desarrollo):

   | Variable | Para qué sirve | Valor por defecto |
   |----------|----------------|-------------------|
   | `DATABASE_URL` | Conexión a PostgreSQL | `postgresql+psycopg2://postgres:postgres@localhost:5434/control_gastos` |
   | `CLAVE_SECRETA` | Firma los tokens de sesión. **Obligatoria en producción**, larga y aleatoria | Una clave de desarrollo (la app avisa al arrancar) |
   | `MINUTOS_EXPIRACION_TOKEN` | Duración de la sesión | `480` (8 horas) |

   En PowerShell: `$env:CLAVE_SECRETA = "..."`. Para generar una clave segura:
   `python -c "import secrets; print(secrets.token_urlsafe(48))"`.

   Si la app no logra conectarse a la base, al arrancar muestra el motivo
   (servidor apagado, contraseña incorrecta, etc.) y se detiene.

## Ejecutar la aplicación

```bash
python seed.py                  # crea las cuentas y datos de demostración (opcional)
uvicorn app.main:app --reload
```

- Interfaz web: <http://localhost:8000>
- Documentación interactiva de la API: <http://localhost:8000/docs>. Para
  probar endpoints protegidos, pulsa **Authorize** y escribe correo y
  contraseña.

## Correr las pruebas

Las pruebas usan SQLite en memoria, así que **no necesitan PostgreSQL**.

```bash
pytest --cov=app --cov-report=term-missing
```

Cubren las reglas de negocio, la autenticación (registro, inicio de sesión,
tokens inválidos), el aislamiento entre usuarios (nadie ve ni modifica datos
ajenos) y la administración (permisos, privacidad y cuentas desactivadas).

## Endpoints

Todos, salvo los de `/auth/registro` y `/auth/login`, exigen el encabezado
`Authorization: Bearer <token>`.

| Método | Ruta                               | Descripción                                  |
|--------|------------------------------------|----------------------------------------------|
| POST   | `/auth/registro`                   | Crear cuenta (devuelve el token)             |
| POST   | `/auth/login`                      | Iniciar sesión (formulario OAuth2: `username` = correo, `password`) |
| GET    | `/auth/yo`                         | Datos de la cuenta actual                    |
| POST   | `/categorias`                      | Crear categoría                              |
| GET    | `/categorias`                      | Listar categorías                            |
| GET    | `/categorias/{id}`                 | Obtener una categoría                        |
| PUT    | `/categorias/{id}`                 | Editar categoría                             |
| DELETE | `/categorias/{id}`                 | Eliminar categoría (si no tiene movimientos) |
| POST   | `/movimientos`                     | Registrar ingreso o gasto (incluye alerta de presupuesto) |
| GET    | `/movimientos`                     | Listar; filtros `fecha_inicio`, `fecha_fin`, `categoria_id` |
| GET    | `/movimientos/{id}`                | Obtener un movimiento                        |
| PUT    | `/movimientos/{id}`                | Editar movimiento (campos opcionales)        |
| DELETE | `/movimientos/{id}`                | Eliminar movimiento                          |
| POST   | `/presupuestos`                    | Definir presupuesto mensual                  |
| GET    | `/presupuestos`                    | Listar presupuestos                          |
| GET    | `/presupuestos/{mes}/estado`       | Gastado vs. límite y si se superó            |
| PUT    | `/presupuestos/{id}`               | Editar presupuesto                           |
| DELETE | `/presupuestos/{id}`               | Eliminar presupuesto                         |
| GET    | `/reportes/saldo`                  | Saldo = ingresos − gastos                    |
| GET    | `/reportes/resumen-mensual?mes=AAAA-MM` | Totales del mes por categoría           |
| GET    | `/admin/usuarios`                  | *(admin)* Cuentas con su cantidad de movimientos |
| GET    | `/admin/estadisticas`              | *(admin)* Totales de cuentas y movimientos   |
| PATCH  | `/admin/usuarios/{id}`             | *(admin)* Activar/desactivar o cambiar rol   |

### Ejemplo

```bash
# 1. Iniciar sesión y guardar el token
curl -X POST http://localhost:8000/auth/login -d "username=demo@misfinanzas.test&password=Demo12345"

# 2. Registrar un gasto con ese token
curl -X POST http://localhost:8000/movimientos \
  -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
  -d '{"tipo":"GASTO","monto":50000,"fecha":"2026-11-10","descripcion":"Mercado","categoria_id":2}'
```

## Reglas de negocio
- El monto debe ser mayor que 0.
- Todo movimiento debe tener una categoría existente **del mismo usuario**.
- No se permiten fechas futuras.
- No se puede eliminar una categoría con movimientos asociados.
- Saldo = suma de ingresos − suma de gastos (de cada usuario).
- Al registrar un gasto que hace superar el presupuesto del mes, la respuesta
  incluye `alerta_presupuesto`.
- El nombre de categoría y el mes del presupuesto son únicos **por usuario**.
- El correo de cada cuenta es único.

## Antes de ponerla en producción
Para venderla como servicio faltaría, como mínimo: definir `CLAVE_SECRETA`,
servirla con HTTPS, usar migraciones de base de datos (por ejemplo Alembic) en
lugar de `create_all`, limitar los intentos de inicio de sesión, permitir
recuperar la contraseña por correo y hacer copias de seguridad de la base.
