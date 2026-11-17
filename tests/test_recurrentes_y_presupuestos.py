"""Movimientos recurrentes, presupuesto por categoría y exportación."""

import io
from datetime import date

from openpyxl import load_workbook

from app.database import SesionLocal
from app.models import Usuario
from app.schemas import CategoriaCrear, RecurrenteCrear
from app.services import ServicioCategorias, ServicioRecurrentes
from tests.conftest import activar_pro, crear_categoria, crear_movimiento, registrar

HOY = date.today()
MES = HOY.strftime("%Y-%m")


def mes_atras(meses: int) -> str:
    total = HOY.year * 12 + HOY.month - 1 - meses
    return f"{total // 12:04d}-{total % 12 + 1:02d}"


def recurrente(cliente, categoria_id, **extra):
    datos = {"tipo": "GASTO", "monto": 950000, "descripcion": "Arriendo", "dia_del_mes": 1,
             "categoria_id": categoria_id, **extra}
    return cliente.post("/recurrentes", json=datos)


# Recurrentes ---------------------------------------------------------------
def test_genera_los_meses_pendientes_una_sola_vez(cliente):
    categoria = crear_categoria(cliente, "Vivienda")
    recurrente(cliente, categoria, mes_inicio=mes_atras(2))

    primera = cliente.post("/recurrentes/generar").json()["movimientos_creados"]
    segunda = cliente.post("/recurrentes/generar").json()["movimientos_creados"]
    movimientos = cliente.get("/movimientos").json()

    assert primera == 3  # hace dos meses, el mes pasado y este (día 1 ya pasó)
    assert segunda == 0
    assert len(movimientos) == 3
    assert all(m["recurrente_id"] is not None for m in movimientos)


def test_no_genera_fechas_futuras(cliente_anonimo):
    registrar(cliente_anonimo, "ana@correo.com")
    db = SesionLocal()
    try:
        usuario = db.query(Usuario).filter(Usuario.email == "ana@correo.com").one()
        categoria = ServicioCategorias(db, usuario).crear(CategoriaCrear(nombre="Salario"))
        servicio = ServicioRecurrentes(db, usuario)
        servicio.crear(RecurrenteCrear(tipo="INGRESO", monto=100, dia_del_mes=20,
                                       categoria_id=categoria.id, mes_inicio="2026-01"))

        creados = servicio.generar_pendientes(hoy=date(2026, 3, 10))
    finally:
        db.close()

    assert creados == 2  # 20 de enero y 20 de febrero; el 20 de marzo aún no llega


def test_recurrente_inactivo_no_genera(cliente):
    categoria = crear_categoria(cliente, "Vivienda")
    creado = recurrente(cliente, categoria).json()
    cliente.patch(f"/recurrentes/{creado['id']}", json={"activo": False})

    assert cliente.post("/recurrentes/generar").json()["movimientos_creados"] == 0


def test_valida_dia_y_monto(cliente):
    categoria = crear_categoria(cliente, "Vivienda")

    assert recurrente(cliente, categoria, dia_del_mes=31).status_code == 400
    assert recurrente(cliente, categoria, monto=0).status_code == 400
    assert recurrente(cliente, 999).status_code == 404


def test_plan_gratis_permite_tres_recurrentes(cliente):
    categoria = crear_categoria(cliente, "Vivienda")
    for _ in range(3):
        assert recurrente(cliente, categoria).status_code == 201

    cuarto = recurrente(cliente, categoria)

    assert cuarto.status_code == 402


def test_no_se_elimina_categoria_usada_por_un_recurrente(cliente):
    categoria = crear_categoria(cliente, "Vivienda")
    recurrente(cliente, categoria)

    assert cliente.delete(f"/categorias/{categoria}").status_code == 409


# Presupuesto por categoría ------------------------------------------------
def test_alerta_al_superar_el_limite_de_una_categoria(cliente):
    comida = crear_categoria(cliente, "Comida")
    cliente.put(f"/presupuestos/categorias/{comida}", json={"limite": 500})

    dentro = crear_movimiento(cliente, comida, monto=300, fecha=HOY.isoformat()).json()
    fuera = crear_movimiento(cliente, comida, monto=300, fecha=HOY.isoformat()).json()
    estado = cliente.get("/presupuestos/categorias").json()[0]

    assert dentro["alertas"] == []
    assert any("Comida" in a for a in fuera["alertas"])
    assert estado["excedido"] is True and estado["porcentaje"] == 120


def test_presupuesto_categoria_validaciones(cliente):
    comida = crear_categoria(cliente, "Comida")

    assert cliente.put(f"/presupuestos/categorias/{comida}", json={"limite": 0}).status_code == 400
    assert cliente.put("/presupuestos/categorias/999", json={"limite": 100}).status_code == 404
    assert cliente.delete(f"/presupuestos/categorias/{comida}").status_code == 404


def test_actualizar_y_quitar_presupuesto_categoria(cliente):
    comida = crear_categoria(cliente, "Comida")
    cliente.put(f"/presupuestos/categorias/{comida}", json={"limite": 500})

    actualizado = cliente.put(f"/presupuestos/categorias/{comida}", json={"limite": 800}).json()
    quitado = cliente.delete(f"/presupuestos/categorias/{comida}")

    assert float(actualizado["limite"]) == 800
    assert quitado.status_code == 204
    assert cliente.get("/presupuestos/categorias").json() == []


# Exportación ---------------------------------------------------------------
def test_exportar_csv(cliente):
    comida = crear_categoria(cliente, "Comida")
    crear_movimiento(cliente, comida, monto=1234.5, descripcion="Mercado", fecha=HOY.isoformat())

    respuesta = cliente.get(f"/reportes/exportar?mes={MES}&formato=csv")
    texto = respuesta.content.decode("utf-8-sig")

    assert respuesta.status_code == 200
    assert f"reporte-{MES}.csv" in respuesta.headers["content-disposition"]
    assert texto.startswith("Fecha;Tipo;Categoría")
    assert "Mercado;1234,50" in texto


def test_excel_requiere_plan_pro(cliente):
    gratis = cliente.get(f"/reportes/exportar?mes={MES}&formato=xlsx")
    activar_pro("ana@correo.com")
    comida = crear_categoria(cliente, "Comida")
    crear_movimiento(cliente, comida, monto=500, fecha=HOY.isoformat())
    pro = cliente.get(f"/reportes/exportar?mes={MES}&formato=xlsx")

    libro = load_workbook(io.BytesIO(pro.content))

    assert gratis.status_code == 402
    assert pro.status_code == 200
    assert libro.sheetnames == ["Resumen", "Movimientos"]
    assert libro["Movimientos"]["C2"].value == "Comida"


def test_exportar_formato_invalido(cliente):
    assert cliente.get(f"/reportes/exportar?mes={MES}&formato=pdf").status_code == 400
