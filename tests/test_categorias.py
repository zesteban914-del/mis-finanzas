from tests.conftest import crear_categoria, crear_movimiento


def test_crear_y_listar_categorias(cliente):
    crear_categoria(cliente, "Transporte")
    crear_categoria(cliente, "Comida")

    respuesta = cliente.get("/categorias")

    assert respuesta.status_code == 200
    nombres = [c["nombre"] for c in respuesta.json()]
    assert nombres == ["Comida", "Transporte"]  # ordenadas alfabéticamente


def test_no_permite_nombre_duplicado(cliente):
    crear_categoria(cliente, "Comida")

    respuesta = cliente.post("/categorias", json={"nombre": "Comida"})

    assert respuesta.status_code == 409
    assert "Ya existe" in respuesta.json()["detalle"]


def test_actualizar_categoria(cliente):
    categoria_id = crear_categoria(cliente, "Comda")

    respuesta = cliente.put(f"/categorias/{categoria_id}", json={"nombre": "Comida"})

    assert respuesta.status_code == 200
    assert respuesta.json()["nombre"] == "Comida"


def test_actualizar_a_nombre_duplicado_falla(cliente):
    crear_categoria(cliente, "Comida")
    otra_id = crear_categoria(cliente, "Transporte")

    respuesta = cliente.put(f"/categorias/{otra_id}", json={"nombre": "Comida"})

    assert respuesta.status_code == 409


def test_obtener_categoria_inexistente_devuelve_404(cliente):
    respuesta = cliente.get("/categorias/999")

    assert respuesta.status_code == 404


def test_eliminar_categoria_sin_movimientos(cliente):
    categoria_id = crear_categoria(cliente)

    respuesta = cliente.delete(f"/categorias/{categoria_id}")

    assert respuesta.status_code == 204
    assert cliente.get(f"/categorias/{categoria_id}").status_code == 404


def test_no_permite_eliminar_categoria_con_movimientos(cliente):
    categoria_id = crear_categoria(cliente)
    crear_movimiento(cliente, categoria_id)

    respuesta = cliente.delete(f"/categorias/{categoria_id}")

    assert respuesta.status_code == 409
    assert "movimiento" in respuesta.json()["detalle"]
