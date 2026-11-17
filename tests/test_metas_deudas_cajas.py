"""Metas de ahorro, deudas, cajas con transferencias y comprobantes."""

from datetime import date, timedelta

import pytest

from tests.conftest import activar_pro, crear_categoria, crear_movimiento, registrar

HOY = date.today()
AYER = (HOY - timedelta(days=1)).isoformat()


@pytest.fixture()
def negocio(cliente_anonimo):
    sesion = registrar(cliente_anonimo, "tienda@correo.com", "Tienda", tipo="NEGOCIO")
    cliente_anonimo.headers["Authorization"] = f"Bearer {sesion['access_token']}"
    return cliente_anonimo


# Metas (cuenta personal) ----------------------------------------------------
def test_meta_avanza_con_aportes_hasta_completarse(cliente):
    meta = cliente.post("/metas", json={"nombre": "Viaje", "monto_objetivo": 1000}).json()

    parcial = cliente.post(f"/metas/{meta['id']}/aportes", json={"monto": 400}).json()
    completa = cliente.post(f"/metas/{meta['id']}/aportes", json={"monto": 700}).json()

    assert parcial["porcentaje"] == 40 and float(parcial["faltante"]) == 600
    assert completa["completada"] is True and completa["porcentaje"] == 100


def test_meta_validaciones(cliente):
    assert cliente.post("/metas", json={"nombre": "", "monto_objetivo": 100}).status_code == 400
    assert cliente.post("/metas", json={"nombre": "X", "monto_objetivo": 0}).status_code == 400
    assert cliente.post("/metas", json={"nombre": "X", "monto_objetivo": 10, "fecha_limite": AYER}).status_code == 400
    meta = cliente.post("/metas", json={"nombre": "X", "monto_objetivo": 10}).json()
    assert cliente.post(f"/metas/{meta['id']}/aportes", json={"monto": -5}).status_code == 400


def test_plan_gratis_permite_dos_metas(cliente):
    for nombre in ("A", "B"):
        assert cliente.post("/metas", json={"nombre": nombre, "monto_objetivo": 10}).status_code == 201

    assert cliente.post("/metas", json={"nombre": "C", "monto_objetivo": 10}).status_code == 402


def test_editar_y_eliminar_meta(cliente):
    meta = cliente.post("/metas", json={"nombre": "Viaje", "monto_objetivo": 1000}).json()

    editada = cliente.patch(f"/metas/{meta['id']}", json={"nombre": "Viaje a Cartagena"}).json()

    assert editada["nombre"] == "Viaje a Cartagena"
    assert cliente.delete(f"/metas/{meta['id']}").status_code == 204
    assert cliente.get("/metas").json() == []


# Deudas ----------------------------------------------------------------------
def test_abonos_hasta_saldar_la_deuda(cliente):
    deuda = cliente.post(
        "/deudas", json={"tipo": "POR_PAGAR", "contraparte": "Banco", "monto_total": 1000}
    ).json()

    excesivo = cliente.post(f"/deudas/{deuda['id']}/abonos", json={"monto": 1500})
    abonada = cliente.post(f"/deudas/{deuda['id']}/abonos", json={"monto": 1000}).json()
    otra_vez = cliente.post(f"/deudas/{deuda['id']}/abonos", json={"monto": 1})

    assert excesivo.status_code == 400 and "supera el saldo pendiente" in excesivo.json()["detalle"]
    assert abonada["estado"] == "PAGADA" and float(abonada["pendiente"]) == 0
    assert otra_vez.status_code == 400


def test_deuda_vencida_y_filtro_por_tipo(cliente):
    cliente.post("/deudas", json={"tipo": "POR_COBRAR", "contraparte": "Luis", "monto_total": 50,
                                  "fecha_vencimiento": AYER})
    cliente.post("/deudas", json={"tipo": "POR_PAGAR", "contraparte": "Banco", "monto_total": 70})

    por_cobrar = cliente.get("/deudas?tipo=POR_COBRAR").json()

    assert len(por_cobrar) == 1
    assert por_cobrar[0]["estado"] == "VENCIDA"


def test_deuda_validaciones_y_edicion(cliente):
    assert cliente.post("/deudas", json={"tipo": "POR_PAGAR", "contraparte": " ", "monto_total": 5}).status_code == 400
    deuda = cliente.post("/deudas", json={"tipo": "POR_PAGAR", "contraparte": "Banco", "monto_total": 100}).json()
    cliente.post(f"/deudas/{deuda['id']}/abonos", json={"monto": 60})

    menor_que_abonado = cliente.patch(f"/deudas/{deuda['id']}", json={"monto_total": 50})
    editada = cliente.patch(f"/deudas/{deuda['id']}", json={"contraparte": "Bancolombia"}).json()

    assert menor_que_abonado.status_code == 400
    assert editada["contraparte"] == "Bancolombia"
    assert cliente.delete(f"/deudas/{deuda['id']}").status_code == 204


# Cajas (negocio) --------------------------------------------------------------
def test_saldo_de_cada_caja_y_transferencias(negocio):
    efectivo = negocio.post("/cajas", json={"nombre": "Caja", "tipo": "EFECTIVO", "saldo_inicial": 100}).json()
    banco = negocio.post("/cajas", json={"nombre": "Banco", "tipo": "BANCO"}).json()
    ventas = crear_categoria(negocio, "Ventas")
    crear_movimiento(negocio, ventas, tipo="INGRESO", monto=500, fecha=HOY.isoformat())
    negocio.post("/movimientos", json={"tipo": "INGRESO", "monto": 400, "fecha": HOY.isoformat(),
                                       "categoria_id": ventas, "caja_id": efectivo["id"]})

    sin_saldo = negocio.post("/cajas/transferencias", json={"origen_id": efectivo["id"], "destino_id": banco["id"],
                                                             "monto": 600, "fecha": HOY.isoformat()})
    misma = negocio.post("/cajas/transferencias", json={"origen_id": banco["id"], "destino_id": banco["id"],
                                                         "monto": 1, "fecha": HOY.isoformat()})
    ok = negocio.post("/cajas/transferencias", json={"origen_id": efectivo["id"], "destino_id": banco["id"],
                                                      "monto": 300, "fecha": HOY.isoformat()})
    saldos = {c["nombre"]: float(c["saldo_actual"]) for c in negocio.get("/cajas").json()}

    assert sin_saldo.status_code == 400 and "Saldo insuficiente" in sin_saldo.json()["detalle"]
    assert misma.status_code == 400
    assert ok.status_code == 201
    assert saldos == {"Caja": 200, "Banco": 300}
    assert len(negocio.get("/cajas/transferencias").json()) == 1
    assert len(negocio.get(f"/movimientos?caja_id={efectivo['id']}").json()) == 1


def test_no_se_elimina_caja_con_movimientos(negocio):
    caja = negocio.post("/cajas", json={"nombre": "Caja", "tipo": "EFECTIVO"}).json()
    vacia = negocio.post("/cajas", json={"nombre": "Nequi", "tipo": "BILLETERA"}).json()
    ventas = crear_categoria(negocio, "Ventas")
    negocio.post("/movimientos", json={"tipo": "INGRESO", "monto": 10, "fecha": HOY.isoformat(),
                                       "categoria_id": ventas, "caja_id": caja["id"]})

    assert negocio.delete(f"/cajas/{caja['id']}").status_code == 409
    assert negocio.delete(f"/cajas/{vacia['id']}").status_code == 204


def test_cajas_validaciones_y_limite(negocio):
    assert negocio.post("/cajas", json={"nombre": "X", "tipo": "BANCO", "saldo_inicial": -1}).status_code == 400
    negocio.post("/cajas", json={"nombre": "A", "tipo": "BANCO"})
    assert negocio.post("/cajas", json={"nombre": "A", "tipo": "BANCO"}).status_code == 409
    negocio.post("/cajas", json={"nombre": "B", "tipo": "BANCO"})
    assert negocio.post("/cajas", json={"nombre": "C", "tipo": "BANCO"}).status_code == 402
    ventas = crear_categoria(negocio, "Ventas")
    caja_inexistente = negocio.post("/movimientos", json={"tipo": "GASTO", "monto": 1, "fecha": HOY.isoformat(),
                                                          "categoria_id": ventas, "caja_id": 999})
    assert caja_inexistente.status_code == 404


def test_renombrar_caja(negocio):
    caja = negocio.post("/cajas", json={"nombre": "Caja", "tipo": "EFECTIVO"}).json()

    renombrada = negocio.patch(f"/cajas/{caja['id']}", json={"nombre": "Caja principal"}).json()

    assert renombrada["nombre"] == "Caja principal"


# Comprobantes (negocio, plan Pro) ---------------------------------------------
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 100


def test_comprobantes_requieren_plan_pro(negocio):
    ventas = crear_categoria(negocio, "Ventas")
    movimiento = crear_movimiento(negocio, ventas, fecha=HOY.isoformat()).json()["movimiento"]

    respuesta = negocio.post(f"/movimientos/{movimiento['id']}/comprobante",
                             files={"archivo": ("factura.png", PNG, "image/png")})

    assert respuesta.status_code == 402


def test_subir_descargar_y_eliminar_comprobante(negocio):
    activar_pro("tienda@correo.com")
    ventas = crear_categoria(negocio, "Ventas")
    movimiento_id = crear_movimiento(negocio, ventas, fecha=HOY.isoformat()).json()["movimiento"]["id"]
    ruta = f"/movimientos/{movimiento_id}/comprobante"

    tipo_invalido = negocio.post(ruta, files={"archivo": ("virus.exe", b"MZ", "application/octet-stream")})
    muy_grande = negocio.post(ruta, files={"archivo": ("big.png", b"0" * (2 * 1024 * 1024 + 1), "image/png")})
    subido = negocio.post(ruta, files={"archivo": ("factura.png", PNG, "image/png")})
    marcado = negocio.get(f"/movimientos/{movimiento_id}").json()["tiene_comprobante"]
    descargado = negocio.get(ruta)
    eliminado = negocio.delete(ruta)

    assert tipo_invalido.status_code == 400
    assert muy_grande.status_code == 400
    assert subido.status_code == 201
    assert marcado is True
    assert descargado.content == PNG and descargado.headers["content-type"] == "image/png"
    assert eliminado.status_code == 204
    assert negocio.get(ruta).status_code == 404
