"""Cada usuario solo puede ver y modificar sus propios datos."""

from tests.conftest import crear_categoria, crear_movimiento, encabezado, registrar


def dos_usuarios(cliente_anonimo):
    ana = encabezado(registrar(cliente_anonimo, "ana@correo.com", "Ana"))
    beto = encabezado(registrar(cliente_anonimo, "beto@correo.com", "Beto"))
    return ana, beto


def test_un_usuario_no_ve_los_movimientos_de_otro(cliente_anonimo):
    ana, beto = dos_usuarios(cliente_anonimo)
    categoria = crear_categoria(cliente_anonimo, "Comida", headers=ana)
    crear_movimiento(cliente_anonimo, categoria, monto=500, headers=ana)

    movimientos_de_beto = cliente_anonimo.get("/movimientos", headers=beto).json()
    categorias_de_beto = cliente_anonimo.get("/categorias", headers=beto).json()

    assert movimientos_de_beto == []
    assert categorias_de_beto == []


def test_no_puede_leer_ni_borrar_un_movimiento_ajeno(cliente_anonimo):
    ana, beto = dos_usuarios(cliente_anonimo)
    categoria = crear_categoria(cliente_anonimo, "Comida", headers=ana)
    movimiento_id = crear_movimiento(cliente_anonimo, categoria, headers=ana).json()[
        "movimiento"
    ]["id"]

    assert cliente_anonimo.get(f"/movimientos/{movimiento_id}", headers=beto).status_code == 404
    assert cliente_anonimo.delete(f"/movimientos/{movimiento_id}", headers=beto).status_code == 404
    assert cliente_anonimo.get(f"/movimientos/{movimiento_id}", headers=ana).status_code == 200


def test_no_puede_usar_la_categoria_de_otro(cliente_anonimo):
    ana, beto = dos_usuarios(cliente_anonimo)
    categoria_de_ana = crear_categoria(cliente_anonimo, "Comida", headers=ana)

    respuesta = crear_movimiento(cliente_anonimo, categoria_de_ana, headers=beto)

    assert respuesta.status_code == 404


def test_dos_usuarios_pueden_tener_categorias_con_el_mismo_nombre(cliente_anonimo):
    ana, beto = dos_usuarios(cliente_anonimo)

    crear_categoria(cliente_anonimo, "Comida", headers=ana)
    respuesta = cliente_anonimo.post("/categorias", json={"nombre": "Comida"}, headers=beto)

    assert respuesta.status_code == 201


def test_el_saldo_y_el_presupuesto_son_independientes(cliente_anonimo):
    ana, beto = dos_usuarios(cliente_anonimo)
    categoria_ana = crear_categoria(cliente_anonimo, "General", headers=ana)
    categoria_beto = crear_categoria(cliente_anonimo, "General", headers=beto)
    crear_movimiento(cliente_anonimo, categoria_ana, tipo="INGRESO", monto=1000, headers=ana)
    crear_movimiento(cliente_anonimo, categoria_beto, tipo="GASTO", monto=300, headers=beto)
    cliente_anonimo.post("/presupuestos", json={"mes": "2026-11", "limite": 100}, headers=beto)

    saldo_ana = cliente_anonimo.get("/reportes/saldo", headers=ana).json()
    saldo_beto = cliente_anonimo.get("/reportes/saldo", headers=beto).json()
    ana_puede_crear_su_presupuesto = cliente_anonimo.post(
        "/presupuestos", json={"mes": "2026-11", "limite": 999}, headers=ana
    )

    assert float(saldo_ana["saldo"]) == 1000
    assert float(saldo_beto["saldo"]) == -300
    assert ana_puede_crear_su_presupuesto.status_code == 201
