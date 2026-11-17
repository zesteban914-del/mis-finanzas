from tests.conftest import crear_categoria, crear_movimiento


def test_saldo_sin_movimientos_es_cero(cliente):
    respuesta = cliente.get("/reportes/saldo")

    assert respuesta.status_code == 200
    assert float(respuesta.json()["saldo"]) == 0


def test_calcula_saldo_correctamente(cliente):
    categoria_id = crear_categoria(cliente)
    crear_movimiento(cliente, categoria_id, tipo="INGRESO", monto=2000)
    crear_movimiento(cliente, categoria_id, tipo="GASTO", monto=500)
    crear_movimiento(cliente, categoria_id, tipo="GASTO", monto=300.5)

    respuesta = cliente.get("/reportes/saldo")

    datos = respuesta.json()
    assert float(datos["total_ingresos"]) == 2000
    assert float(datos["total_gastos"]) == 800.5
    assert float(datos["saldo"]) == 1199.5


def test_resumen_mensual_por_categoria(cliente):
    comida_id = crear_categoria(cliente, "Comida")
    salario_id = crear_categoria(cliente, "Salario")
    crear_movimiento(
        cliente, salario_id, tipo="INGRESO", monto=3000, fecha="2026-05-01"
    )
    crear_movimiento(cliente, comida_id, tipo="GASTO", monto=200, fecha="2026-05-10")
    crear_movimiento(cliente, comida_id, tipo="GASTO", monto=150, fecha="2026-05-20")
    # Este movimiento es de otro mes y NO debe aparecer en el resumen:
    crear_movimiento(cliente, comida_id, tipo="GASTO", monto=999, fecha="2026-06-01")

    respuesta = cliente.get("/reportes/resumen-mensual", params={"mes": "2026-05"})

    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["mes"] == "2026-05"
    assert float(datos["total_ingresos"]) == 3000
    assert float(datos["total_gastos"]) == 350
    assert float(datos["balance"]) == 2650

    por_nombre = {c["categoria"]: c for c in datos["categorias"]}
    assert float(por_nombre["Comida"]["total_gastos"]) == 350
    assert float(por_nombre["Salario"]["total_ingresos"]) == 3000


def test_resumen_con_mes_invalido_falla(cliente):
    respuesta = cliente.get("/reportes/resumen-mensual", params={"mes": "2026-13"})

    assert respuesta.status_code == 400
    assert "AAAA-MM" in respuesta.json()["detalle"]
