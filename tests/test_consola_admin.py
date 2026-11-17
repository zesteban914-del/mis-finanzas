"""El administrador de la plataforma tiene una consola propia, sin funciones financieras."""

from datetime import date

from tests.conftest import convertir_en_admin, encabezado, registrar

MES = date.today().strftime("%Y-%m")


def admin_y_usuario(cliente):
    admin = encabezado(registrar(cliente, "admin@app.com", "Admin"))
    convertir_en_admin("admin@app.com")
    usuario = registrar(cliente, "ana@correo.com", "Ana")
    registrar(cliente, "tienda@correo.com", "Tienda", tipo="NEGOCIO")
    return admin, usuario


def test_el_admin_no_tiene_funciones_financieras(cliente_anonimo):
    admin, _ = admin_y_usuario(cliente_anonimo)

    yo = cliente_anonimo.get("/auth/yo", headers=admin).json()
    movimientos = cliente_anonimo.get("/movimientos", headers=admin)

    assert yo["rol"] == "ADMIN"
    assert yo["permisos"] == [] and yo["funciones"] == []
    assert movimientos.status_code == 403
    assert "administrador" in movimientos.json()["detalle"]
    for ruta in ["/reportes/saldo", "/categorias", "/metas", "/cajas", "/deudas", "/recurrentes"]:
        assert cliente_anonimo.get(ruta, headers=admin).status_code == 403, ruta


def test_el_admin_no_solicita_planes(cliente_anonimo):
    admin, _ = admin_y_usuario(cliente_anonimo)

    assert cliente_anonimo.post("/planes/solicitar-pro", headers=admin).status_code == 403


def test_actividad_por_mes_cuenta_registros_por_tipo(cliente_anonimo):
    admin, _ = admin_y_usuario(cliente_anonimo)

    actividad = cliente_anonimo.get("/admin/estadisticas", headers=admin).json()["actividad_por_mes"]
    este_mes = actividad[-1]

    assert len(actividad) == 6
    assert este_mes["mes"] == MES
    assert este_mes["cuentas_personales"] == 1  # el administrador no cuenta como cliente
    assert este_mes["cuentas_negocio"] == 1


def test_descartar_solicitud_de_pro(cliente_anonimo):
    admin, usuario = admin_y_usuario(cliente_anonimo)
    cliente_anonimo.post("/planes/solicitar-pro", headers=encabezado(usuario))

    cliente_anonimo.patch(
        f"/admin/usuarios/{usuario['usuario']['id']}", json={"descartar_solicitud": True}, headers=admin
    )
    datos = cliente_anonimo.get("/auth/yo", headers=encabezado(usuario)).json()

    assert datos["solicito_pro_en"] is None
    assert datos["plan"] == "GRATIS"
