"""Equipo de un negocio (propietario, empleado, contador) y planes de suscripción."""

from datetime import date

from tests.conftest import (
    CONTRASENA,
    activar_pro,
    convertir_en_admin,
    crear_categoria,
    crear_movimiento,
    encabezado,
    registrar,
)

HOY = date.today().isoformat()


def negocio_con_equipo(cliente, pro=True):
    """Propietario (plan Pro) con un empleado y un contador."""
    duena = encabezado(registrar(cliente, "duena@tienda.com", "Tienda Ana", tipo="NEGOCIO"))
    if pro:
        activar_pro("duena@tienda.com")
    categoria = crear_categoria(cliente, "Ventas", headers=duena)
    for email, rol in (("empleado@tienda.com", "EMPLEADO"), ("contador@tienda.com", "CONTADOR")):
        respuesta = cliente.post(
            "/equipo",
            json={"nombre": rol.title(), "email": email, "contrasena": CONTRASENA, "rol_negocio": rol},
            headers=duena,
        )
        assert respuesta.status_code == 201, respuesta.text
    entrar = lambda email: {"Authorization": "Bearer " + cliente.post(  # noqa: E731
        "/auth/login", data={"username": email, "password": CONTRASENA}
    ).json()["access_token"]}
    return duena, entrar("empleado@tienda.com"), entrar("contador@tienda.com"), categoria


def test_el_empleado_registra_ventas_en_la_cuenta_del_negocio(cliente_anonimo):
    duena, empleado, _, categoria = negocio_con_equipo(cliente_anonimo)

    respuesta = crear_movimiento(cliente_anonimo, categoria, tipo="INGRESO", monto=5000, fecha=HOY, headers=empleado)
    vistos_por_la_duena = cliente_anonimo.get("/movimientos", headers=duena).json()

    assert respuesta.status_code == 201
    assert vistos_por_la_duena[0]["registrado_por_nombre"] == "Empleado"


def test_el_empleado_no_edita_ni_ve_reportes(cliente_anonimo):
    duena, empleado, _, categoria = negocio_con_equipo(cliente_anonimo)
    movimiento = crear_movimiento(cliente_anonimo, categoria, fecha=HOY, headers=duena).json()["movimiento"]

    assert cliente_anonimo.delete(f"/movimientos/{movimiento['id']}", headers=empleado).status_code == 403
    assert cliente_anonimo.put(f"/movimientos/{movimiento['id']}", json={"monto": 1}, headers=empleado).status_code == 403
    assert cliente_anonimo.get("/reportes/saldo", headers=empleado).status_code == 403
    assert cliente_anonimo.post("/categorias", json={"nombre": "X"}, headers=empleado).status_code == 403
    assert cliente_anonimo.get("/equipo", headers=empleado).status_code == 403


def test_el_contador_solo_lee_y_exporta(cliente_anonimo):
    _, _, contador, categoria = negocio_con_equipo(cliente_anonimo)

    assert cliente_anonimo.get("/reportes/saldo", headers=contador).status_code == 200
    mes = HOY[:7]
    assert cliente_anonimo.get(f"/reportes/exportar?mes={mes}&formato=csv", headers=contador).status_code == 200
    assert crear_movimiento(cliente_anonimo, categoria, fecha=HOY, headers=contador).status_code == 403


def test_el_plan_gratis_permite_un_solo_miembro(cliente_anonimo):
    duena = encabezado(registrar(cliente_anonimo, "duena@tienda.com", tipo="NEGOCIO"))
    datos = {"nombre": "E", "contrasena": CONTRASENA, "rol_negocio": "EMPLEADO"}

    primero = cliente_anonimo.post("/equipo", json={**datos, "email": "e1@tienda.com"}, headers=duena)
    segundo = cliente_anonimo.post("/equipo", json={**datos, "email": "e2@tienda.com"}, headers=duena)

    assert primero.status_code == 201
    assert segundo.status_code == 402
    assert "Mejora a Pro" in segundo.json()["detalle"]


def test_no_se_puede_crear_otro_propietario(cliente_anonimo):
    duena = encabezado(registrar(cliente_anonimo, "duena@tienda.com", tipo="NEGOCIO"))

    respuesta = cliente_anonimo.post(
        "/equipo",
        json={"nombre": "X", "email": "x@tienda.com", "contrasena": CONTRASENA, "rol_negocio": "PROPIETARIO"},
        headers=duena,
    )

    assert respuesta.status_code == 400


def test_si_se_desactiva_el_negocio_su_equipo_pierde_acceso(cliente_anonimo):
    _, empleado, _, _ = negocio_con_equipo(cliente_anonimo)
    admin = encabezado(registrar(cliente_anonimo, "admin@app.com"))
    convertir_en_admin("admin@app.com")
    id_negocio = next(
        u["id"] for u in cliente_anonimo.get("/admin/usuarios", headers=admin).json()
        if u["email"] == "duena@tienda.com"
    )

    cliente_anonimo.patch(f"/admin/usuarios/{id_negocio}", json={"activo": False}, headers=admin)

    assert cliente_anonimo.get("/movimientos", headers=empleado).status_code == 401


def test_eliminar_miembro_conserva_sus_movimientos(cliente_anonimo):
    duena, empleado, _, categoria = negocio_con_equipo(cliente_anonimo)
    crear_movimiento(cliente_anonimo, categoria, fecha=HOY, headers=empleado)
    miembro_id = next(
        m["id"] for m in cliente_anonimo.get("/equipo", headers=duena).json() if m["rol_negocio"] == "EMPLEADO"
    )

    eliminado = cliente_anonimo.delete(f"/equipo/{miembro_id}", headers=duena)
    movimientos = cliente_anonimo.get("/movimientos", headers=duena).json()

    assert eliminado.status_code == 204
    assert len(movimientos) == 1 and movimientos[0]["registrado_por_nombre"] is None


def test_catalogo_de_planes_segun_tipo(cliente_anonimo):
    personal = encabezado(registrar(cliente_anonimo, "ana@correo.com"))
    negocio = encabezado(registrar(cliente_anonimo, "tienda@correo.com", tipo="NEGOCIO"))

    precio_pro = lambda h: next(p for p in cliente_anonimo.get("/planes", headers=h).json() if p["plan"] == "PRO")["precio_mensual"]  # noqa: E731

    assert precio_pro(personal) == 9900
    assert precio_pro(negocio) == 39900


def test_solicitar_pro_y_activacion_por_el_admin(cliente_anonimo):
    usuario = registrar(cliente_anonimo, "ana@correo.com")
    ana = encabezado(usuario)
    admin = encabezado(registrar(cliente_anonimo, "admin@app.com"))
    convertir_en_admin("admin@app.com")

    solicitud = cliente_anonimo.post("/planes/solicitar-pro", headers=ana)
    pendientes = cliente_anonimo.get("/admin/estadisticas", headers=admin).json()["solicitudes_pro"]
    cliente_anonimo.patch(f"/admin/usuarios/{usuario['usuario']['id']}", json={"plan": "PRO"}, headers=admin)
    yo = cliente_anonimo.get("/auth/yo", headers=ana).json()
    estadisticas = cliente_anonimo.get("/admin/estadisticas", headers=admin).json()

    assert solicitud.json()["solicito_pro_en"] is not None
    assert pendientes == 1
    assert yo["plan"] == "PRO" and yo["solicito_pro_en"] is None
    assert estadisticas["ingreso_mensual_estimado"] == 9900
    assert cliente_anonimo.post("/planes/solicitar-pro", headers=ana).status_code == 400


def test_el_equipo_usa_el_plan_del_negocio(cliente_anonimo):
    _, empleado, _, _ = negocio_con_equipo(cliente_anonimo, pro=True)

    yo = cliente_anonimo.get("/auth/yo", headers=empleado).json()

    assert yo["plan"] == "PRO"
    assert yo["nombre_negocio"] == "Tienda Ana"
    assert cliente_anonimo.post("/planes/solicitar-pro", headers=empleado).status_code == 403
