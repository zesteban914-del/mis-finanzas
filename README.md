# Control de Gastos Personales

API REST para registrar ingresos y gastos, administrar categorías, consultar
el saldo, obtener un resumen mensual por categoría y controlar un presupuesto
mensual. Proyecto académico de Construcción de Software.

**Stack:** Python 3.11+, FastAPI, SQLAlchemy, PostgreSQL, pytest.

## Arquitectura por capas

```
app/
├── main.py           # Crea la app, registra routers y traduce errores a HTTP
├── database.py       # Conexión a la BD y sesión por petición
├── models/           # Entidades (tablas): Categoria, Movimiento, Presupuesto
├── schemas/          # Validación de entrada y forma de salida (Pydantic)
├── repositories/     # Acceso a datos (patrón Repository): solo consultas
├── services/         # Reglas de negocio y cálculos (no conocen HTTP)
└── controllers/      # Endpoints: reciben la petición y llaman al servicio
tests/                # Pruebas de integración de la API con pytest
seed.py               # Datos de ejemplo
```

Flujo de una petición: **controlador → servicio → repositorio → base de datos**.
Cada capa solo conoce a la de abajo.

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

1. Crear la base de datos en PostgreSQL:
   ```sql
   CREATE DATABASE control_gastos;
   ```
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
   $env:DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/control_gastos"
   ```

## Ejecutar la aplicación

```bash
python seed.py                  # carga datos de ejemplo (opcional)
uvicorn app.main:app --reload
```

Documentación interactiva: <http://localhost:8000/docs>

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
