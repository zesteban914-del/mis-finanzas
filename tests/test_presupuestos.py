from tests.conftest import crear_categoria, crear_movimiento


def crear_presupuesto(cliente, mes="2026-11", limite=1000):
    return cliente.post("/presupuestos", json={"mes": mes, "limite": limite})


def test_crear_presupuesto(cliente):
    respuesta = crear_presupuesto(cliente)

    assert respuesta.status_code == 201
    assert respuesta.json()["mes"] == "2026-11"


def test_rechaza_mes_con_formato_invalido(cliente):
    respuesta = crear_presupuesto(cliente, mes="noviembre")

    assert respuesta.status_code == 400
    assert "AAAA-MM" in respuesta.json()["detalle"]


def test_rechaza_limite_menor_o_igual_a_cero(cliente):
    respuesta = crear_presupuesto(cliente, limite=0)

    assert respuesta.status_code == 400


def test_no_permite_dos_presupuestos_para_el_mismo_mes(cliente):
    crear_presupuesto(cliente)

    respuesta = crear_presupuesto(cliente)

    assert respuesta.status_code == 409


def test_estado_sin_exceder_el_limite(cliente):
    crear_presupuesto(cliente, mes="2026-11", limite=1000)
    categoria_id = crear_categoria(cliente)
    crear_movimiento(cliente, categoria_id, monto=400, fecha="2026-11-05")

    respuesta = cliente.get("/presupuestos/2026-11/estado")

    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["excedido"] is False
    assert float(datos["total_gastado"]) == 400
    assert float(datos["disponible"]) == 600


def test_detecta_presupuesto_superado(cliente):
    crear_presupuesto(cliente, mes="2026-11", limite=1000)
    categoria_id = crear_categoria(cliente)
    crear_movimiento(cliente, categoria_id, monto=700, fecha="2026-11-05")
    crear_movimiento(cliente, categoria_id, monto=500, fecha="2026-11-10")

    respuesta = cliente.get("/presupuestos/2026-11/estado")

    datos = respuesta.json()
    assert datos["excedido"] is True
    assert float(datos["total_gastado"]) == 1200


def test_alerta_al_crear_gasto_que_supera_el_presupuesto(cliente):
    crear_presupuesto(cliente, mes="2026-11", limite=500)
    categoria_id = crear_categoria(cliente)

    sin_alerta = crear_movimiento(cliente, categoria_id, monto=300, fecha="2026-11-05")
    con_alerta = crear_movimiento(cliente, categoria_id, monto=300, fecha="2026-11-10")

    assert sin_alerta.json()["alerta_presupuesto"] is None
    alerta = con_alerta.json()["alerta_presupuesto"]
    assert alerta is not None
    assert "superado" in alerta


def test_los_ingresos_no_generan_alerta(cliente):
    crear_presupuesto(cliente, mes="2026-11", limite=100)
    categoria_id = crear_categoria(cliente)

    respuesta = crear_movimiento(
        cliente, categoria_id, tipo="INGRESO", monto=99999, fecha="2026-11-05"
    )

    assert respuesta.json()["alerta_presupuesto"] is None


def test_estado_de_mes_sin_presupuesto_devuelve_404(cliente):
    respuesta = cliente.get("/presupuestos/2026-01/estado")

    assert respuesta.status_code == 404


def test_actualizar_y_eliminar_presupuesto(cliente):
    presupuesto_id = crear_presupuesto(cliente).json()["id"]

    actualizado = cliente.put(
        f"/presupuestos/{presupuesto_id}", json={"mes": "2026-12", "limite": 2000}
    )
    assert actualizado.status_code == 200
    assert actualizado.json()["mes"] == "2026-12"

    eliminado = cliente.delete(f"/presupuestos/{presupuesto_id}")
    assert eliminado.status_code == 204
