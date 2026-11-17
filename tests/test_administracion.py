from tests.conftest import (
    CONTRASENA,
    convertir_en_admin,
    crear_categoria,
    crear_movimiento,
    encabezado,
    registrar,
)


def preparar(cliente_anonimo):
    """Un administrador y un usuario normal con un movimiento."""
    admin_sesion = registrar(cliente_anonimo, "admin@correo.com", "Admin")
    convertir_en_admin("admin@correo.com")
    usuario_sesion = registrar(cliente_anonimo, "ana@correo.com", "Ana")
    usuario = encabezado(usuario_sesion)
    categoria = crear_categoria(cliente_anonimo, "Comida", headers=usuario)
    crear_movimiento(cliente_anonimo, categoria, monto=777, descripcion="Secreto", headers=usuario)
    return encabezado(admin_sesion), usuario, usuario_sesion["usuario"]["id"]


def test_un_usuario_normal_no_entra_a_administracion(cliente):
    respuesta = cliente.get("/admin/usuarios")

    assert respuesta.status_code == 403
    assert "administradores" in respuesta.json()["detalle"]


def test_admin_lista_usuarios_sin_ver_sus_finanzas(cliente_anonimo):
    admin, _, _ = preparar(cliente_anonimo)

    respuesta = cliente_anonimo.get("/admin/usuarios", headers=admin)

    assert respuesta.status_code == 200
    ana = next(u for u in respuesta.json() if u["email"] == "ana@correo.com")
    assert ana["movimientos_registrados"] == 1
    assert "777" not in respuesta.text and "Secreto" not in respuesta.text


def test_admin_ve_estadisticas(cliente_anonimo):
    admin, _, _ = preparar(cliente_anonimo)

    datos = cliente_anonimo.get("/admin/estadisticas", headers=admin).json()

    assert datos["total_usuarios"] == 2
    assert datos["usuarios_activos"] == 2
    assert datos["administradores"] == 1
    assert datos["movimientos_registrados"] == 1
    assert datos["cuentas_personales"] == 2
    assert datos["cuentas_pro"] == 0


def test_cuenta_desactivada_pierde_el_acceso(cliente_anonimo):
    admin, usuario, usuario_id = preparar(cliente_anonimo)

    cambio = cliente_anonimo.patch(f"/admin/usuarios/{usuario_id}", json={"activo": False}, headers=admin)
    peticion_con_sesion_vieja = cliente_anonimo.get("/movimientos", headers=usuario)
    nuevo_login = cliente_anonimo.post(
        "/auth/login", data={"username": "ana@correo.com", "password": CONTRASENA}
    )

    assert cambio.status_code == 200
    assert peticion_con_sesion_vieja.status_code == 401
    assert nuevo_login.status_code == 403
    assert "desactivada" in nuevo_login.json()["detalle"]


def test_admin_puede_dar_rol_de_administrador(cliente_anonimo):
    admin, usuario, usuario_id = preparar(cliente_anonimo)

    cliente_anonimo.patch(f"/admin/usuarios/{usuario_id}", json={"rol": "ADMIN"}, headers=admin)

    assert cliente_anonimo.get("/admin/usuarios", headers=usuario).status_code == 200


def test_admin_no_puede_desactivarse_a_si_mismo(cliente_anonimo):
    admin, _, _ = preparar(cliente_anonimo)
    mi_id = cliente_anonimo.get("/auth/yo", headers=admin).json()["id"]

    respuesta = cliente_anonimo.patch(f"/admin/usuarios/{mi_id}", json={"activo": False}, headers=admin)

    assert respuesta.status_code == 400


def test_actualizar_usuario_inexistente(cliente_anonimo):
    admin, _, _ = preparar(cliente_anonimo)

    respuesta = cliente_anonimo.patch("/admin/usuarios/999", json={"activo": False}, headers=admin)

    assert respuesta.status_code == 404
