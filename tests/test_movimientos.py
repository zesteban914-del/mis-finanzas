from tests.conftest import crear_categoria, crear_movimiento


def test_crear_movimiento(cliente):
    categoria_id = crear_categoria(cliente)

    respuesta = crear_movimiento(
        cliente, categoria_id, tipo="INGRESO", monto=2500.5, descripcion="Salario"
    )

    assert respuesta.status_code == 201
    datos = respuesta.json()
    movimiento = datos["movimiento"]
    assert movimiento["tipo"] == "INGRESO"
    assert float(movimiento["monto"]) == 2500.5
    assert movimiento["descripcion"] == "Salario"
    assert datos["alerta_presupuesto"] is None


def test_rechaza_monto_cero(cliente):
    categoria_id = crear_categoria(cliente)

    respuesta = crear_movimiento(cliente, categoria_id, monto=0)

    assert respuesta.status_code == 400
    assert "mayor que 0" in respuesta.json()["detalle"]


def test_rechaza_monto_negativo(cliente):
    categoria_id = crear_categoria(cliente)

    respuesta = crear_movimiento(cliente, categoria_id, monto=-50)

    assert respuesta.status_code == 400


def test_rechaza_fecha_futura(cliente):
    categoria_id = crear_categoria(cliente)

    respuesta = crear_movimiento(cliente, categoria_id, fecha="2099-01-01")

    assert respuesta.status_code == 400
    assert "futura" in respuesta.json()["detalle"]


def test_rechaza_categoria_inexistente(cliente):
    respuesta = crear_movimiento(cliente, categoria_id=999)

    assert respuesta.status_code == 404
    assert "no existe" in respuesta.json()["detalle"]


def test_actualizar_movimiento(cliente):
    categoria_id = crear_categoria(cliente)
    movimiento_id = crear_movimiento(cliente, categoria_id).json()["movimiento"]["id"]

    respuesta = cliente.put(
        f"/movimientos/{movimiento_id}",
        json={"monto": 777, "descripcion": "Corregido"},
    )

    assert respuesta.status_code == 200
    assert float(respuesta.json()["monto"]) == 777
    assert respuesta.json()["descripcion"] == "Corregido"


def test_actualizar_con_monto_invalido_falla(cliente):
    categoria_id = crear_categoria(cliente)
    movimiento_id = crear_movimiento(cliente, categoria_id).json()["movimiento"]["id"]

    respuesta = cliente.put(f"/movimientos/{movimiento_id}", json={"monto": -1})

    assert respuesta.status_code == 400


def test_eliminar_movimiento(cliente):
    categoria_id = crear_categoria(cliente)
    movimiento_id = crear_movimiento(cliente, categoria_id).json()["movimiento"]["id"]

    respuesta = cliente.delete(f"/movimientos/{movimiento_id}")

    assert respuesta.status_code == 204
    assert cliente.get(f"/movimientos/{movimiento_id}").status_code == 404


def test_filtrar_por_rango_de_fechas(cliente):
    categoria_id = crear_categoria(cliente)
    crear_movimiento(cliente, categoria_id, fecha="2026-01-15")
    crear_movimiento(cliente, categoria_id, fecha="2026-02-15")
    crear_movimiento(cliente, categoria_id, fecha="2026-03-15")

    respuesta = cliente.get(
        "/movimientos",
        params={"fecha_inicio": "2026-02-01", "fecha_fin": "2026-02-28"},
    )

    assert respuesta.status_code == 200
    movimientos = respuesta.json()
    assert len(movimientos) == 1
    assert movimientos[0]["fecha"] == "2026-02-15"


def test_filtrar_por_categoria(cliente):
    comida_id = crear_categoria(cliente, "Comida")
    transporte_id = crear_categoria(cliente, "Transporte")
    crear_movimiento(cliente, comida_id)
    crear_movimiento(cliente, transporte_id)
    crear_movimiento(cliente, transporte_id)

    respuesta = cliente.get("/movimientos", params={"categoria_id": transporte_id})

    assert respuesta.status_code == 200
    assert len(respuesta.json()) == 2


def test_rango_de_fechas_invertido_falla(cliente):
    respuesta = cliente.get(
        "/movimientos",
        params={"fecha_inicio": "2026-03-01", "fecha_fin": "2026-01-01"},
    )

    assert respuesta.status_code == 400
