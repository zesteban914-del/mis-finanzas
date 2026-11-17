# Control de Gastos Personales

Aplicación web para registrar ingresos y gastos, administrar categorías,
consultar el saldo, ver un resumen mensual por categoría y controlar un
presupuesto mensual. Tiene una API REST y una interfaz web que la consume.
Proyecto académico de Construcción de Software.

**Stack:** Python 3.11+, FastAPI, SQLAlchemy, PostgreSQL, pytest.
Interfaz en HTML, CSS y JavaScript sin librerías ni pasos de compilación.

## Arquitectura por capas

```
app/
├── main.py           # Crea la app, registra routers, traduce errores a HTTP y sirve la interfaz
├── database.py       # Conexión a la BD y sesión por petición
├── models/           # Entidades (tablas): Categoria, Movimiento, Presupuesto
├── schemas/          # Validación de entrada y forma de salida (Pydantic)
├── repositories/     # Acceso a datos (patrón Repository): solo consultas
├── services/         # Reglas de negocio y cálculos (no conocen HTTP)
├── controllers/      # Endpoints: reciben la petición y llaman al servicio
└── static/           # Interfaz web (capa de presentación)
    ├── index.html
    ├── css/estilos.css      # Diseño: colores claro/oscuro, componentes, responsive
    └── js/
        ├── app.js           # Navegación entre vistas, tema y atajos de teclado
        ├── api.js           # Único módulo que llama a la API REST
        ├── formato.js       # Dinero (COP) y fechas en español
        ├── componentes.js   # Piezas de HTML reutilizables (KPIs, medidor, etc.)
        ├── graficos.js      # Gráficos de barras y columnas hechos con CSS
        ├── ui.js            # Notificaciones, diálogo modal y tooltip
        └── vistas/          # Panel, Movimientos, Categorías, Presupuestos y formularios
tests/                # Pruebas unitarias y de integración con pytest
seed.py               # Datos de ejemplo (6 meses de movimientos)
docker-compose.yml    # PostgreSQL del proyecto
```

Flujo de una petición: **interfaz → controlador → servicio → repositorio → base de datos**.
Cada capa solo conoce a la de abajo. La interfaz no tiene reglas de negocio:
envía los datos a la API y muestra sus mensajes de error tal como llegan
(por ejemplo "El monto debe ser mayor que 0").

## Interfaz web

Al abrir <http://localhost:8000> se ve:

- **Panel:** saldo actual, ingresos, gastos y balance del mes (con la variación
  frente al mes anterior), estado del presupuesto, gastos por categoría,
  ingresos vs. gastos de los últimos 6 meses y movimientos recientes. Con las
  flechas se cambia de mes.
- **Movimientos:** tabla con filtros por rango de fechas, categoría y tipo;
  crear, editar y eliminar.
- **Categorías:** crear, renombrar y eliminar (si tiene movimientos, la API lo
  impide y la interfaz muestra el motivo).
- **Presupuestos:** un límite por mes con su barra de uso y estado.

Detalles de diseño: modo claro y oscuro, versión para celular, colores fijos
(azul = ingresos, naranja = gastos), estados del presupuesto con icono y texto
(no solo color), cada gráfico tiene también vista de tabla, y la tecla **N**
abre el formulario de nuevo movimiento.

### Principios SOLID aplicados
- **S (Responsabilidad única):** cada capa y cada clase tiene una sola tarea
  (p. ej. `RepositorioMovimientos` solo consulta, `ServicioMovimientos` solo
  aplica reglas).
- **O (Abierto/cerrado):** se agregan recursos nuevos con nuevos routers,
  servicios y repositorios sin modificar los existentes.
- **L (Sustitución de Liskov):** las excepciones `ErrorDeValidacion`,
  `RecursoNoEncontrado` y `ConflictoDeDatos` heredan de `ErrorDeAplicacion`
  y pueden usarse donde se espera la clase base.
- **I (Segregación de interfaces):** cada repositorio expone solo los métodos
  que su entidad necesita.
- **D (Inversión de dependencias):** los servicios no dependen de FastAPI; la
  sesión de BD se inyecta con `Depends(obtener_db)`, lo que permite usar
  SQLite en memoria en las pruebas.

### Manejo de errores
Los servicios lanzan excepciones de negocio y `main.py` las convierte en
respuestas JSON `{"detalle": "..."}`:

| Excepción             | HTTP | Ejemplo                                   |
|-----------------------|------|-------------------------------------------|
| `ErrorDeValidacion`   | 400  | Monto ≤ 0, fecha futura, mes mal escrito  |
| `RecursoNoEncontrado` | 404  | Categoría o movimiento inexistente        |
| `ConflictoDeDatos`    | 409  | Nombre duplicado, categoría con movimientos |

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
3. Configurar la conexión (opcional; este es el valor por defecto):
   ```powershell
   $env:DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5434/control_gastos"
   ```
   Si la app no logra conectarse, al arrancar muestra el motivo (servidor
   apagado, contraseña incorrecta, etc.) y se detiene.

## Ejecutar la aplicación

```bash
python seed.py                  # carga datos de ejemplo (opcional)
uvicorn app.main:app --reload
```

- Interfaz web: <http://localhost:8000>
- Documentación interactiva de la API: <http://localhost:8000/docs>

## Correr las pruebas

Las pruebas usan SQLite en memoria, así que **no necesitan PostgreSQL**.

```bash
pytest --cov=app --cov-report=term-missing
```

## Endpoints

| Método | Ruta                               | Descripción                                  |
|--------|------------------------------------|----------------------------------------------|
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

### Ejemplo

```bash
curl -X POST http://localhost:8000/movimientos -H "Content-Type: application/json" \
  -d '{"tipo":"GASTO","monto":50000,"fecha":"2026-11-10","descripcion":"Mercado","categoria_id":2}'
```

```json
{
  "movimiento": {"id": 7, "tipo": "GASTO", "monto": "50000.00", "fecha": "2026-11-10",
                 "descripcion": "Mercado", "categoria_id": 2},
  "alerta_presupuesto": null
}
```

## Reglas de negocio
- El monto debe ser mayor que 0.
- Todo movimiento debe tener una categoría existente.
- No se permiten fechas futuras.
- No se puede eliminar una categoría con movimientos asociados.
- Saldo = suma de ingresos − suma de gastos.
- Al registrar un gasto que hace superar el presupuesto del mes, la respuesta
  incluye `alerta_presupuesto`.
