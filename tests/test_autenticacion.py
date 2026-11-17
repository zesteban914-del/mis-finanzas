from app.seguridad import cifrar_contrasena, leer_token, verificar_contrasena
from tests.conftest import CONTRASENA, encabezado, registrar


def iniciar_sesion(cliente, email, contrasena=CONTRASENA):
    return cliente.post("/auth/login", data={"username": email, "password": contrasena})


def test_registro_crea_cuenta_y_devuelve_sesion(cliente_anonimo):
    sesion = registrar(cliente_anonimo, "Ana@Correo.com ", "Ana")

    assert sesion["token_type"] == "bearer"
    assert sesion["usuario"]["email"] == "ana@correo.com"  # se normaliza
    assert sesion["usuario"]["rol"] == "USUARIO"
    assert "contrasena" not in str(sesion["usuario"])


def test_registro_puede_crear_categorias_sugeridas(cliente_anonimo):
    sesion = registrar(cliente_anonimo, "ana@correo.com", categorias_iniciales=True)

    categorias = cliente_anonimo.get("/categorias", headers=encabezado(sesion)).json()

    assert {"Salario", "Comida", "Transporte"} <= {c["nombre"] for c in categorias}


def test_no_permite_correo_duplicado(cliente_anonimo):
    registrar(cliente_anonimo, "ana@correo.com")

    respuesta = cliente_anonimo.post(
        "/auth/registro",
        json={"nombre": "Otra", "email": "ANA@correo.com", "contrasena": CONTRASENA},
    )

    assert respuesta.status_code == 409


def test_rechaza_contrasena_debil(cliente_anonimo):
    respuesta = cliente_anonimo.post(
        "/auth/registro",
        json={"nombre": "Ana", "email": "ana@correo.com", "contrasena": "12345678"},
    )

    assert respuesta.status_code == 400
    assert "letras y números" in respuesta.json()["detalle"]


def test_rechaza_correo_invalido(cliente_anonimo):
    respuesta = cliente_anonimo.post(
        "/auth/registro",
        json={"nombre": "Ana", "email": "no-es-un-correo", "contrasena": CONTRASENA},
    )

    assert respuesta.status_code == 400


def test_login_correcto(cliente_anonimo):
    registrar(cliente_anonimo, "ana@correo.com")

    respuesta = iniciar_sesion(cliente_anonimo, "ana@correo.com")

    assert respuesta.status_code == 200
    assert respuesta.json()["access_token"]


def test_login_con_contrasena_incorrecta(cliente_anonimo):
    registrar(cliente_anonimo, "ana@correo.com")

    respuesta = iniciar_sesion(cliente_anonimo, "ana@correo.com", "Incorrecta123")

    assert respuesta.status_code == 401
    assert respuesta.json()["detalle"] == "Correo o contraseña incorrectos"


def test_login_con_correo_inexistente_da_el_mismo_mensaje(cliente_anonimo):
    respuesta = iniciar_sesion(cliente_anonimo, "nadie@correo.com")

    assert respuesta.status_code == 401
    assert respuesta.json()["detalle"] == "Correo o contraseña incorrectos"


def test_endpoints_protegidos_exigen_sesion(cliente_anonimo):
    for ruta in ["/categorias", "/movimientos", "/presupuestos", "/reportes/saldo"]:
        respuesta = cliente_anonimo.get(ruta)
        assert respuesta.status_code == 401, ruta
        assert respuesta.headers["www-authenticate"] == "Bearer"


def test_token_invalido_es_rechazado(cliente_anonimo):
    respuesta = cliente_anonimo.get(
        "/categorias", headers={"Authorization": "Bearer token-falso"}
    )

    assert respuesta.status_code == 401


def test_mi_cuenta(cliente):
    respuesta = cliente.get("/auth/yo")

    assert respuesta.status_code == 200
    assert respuesta.json()["email"] == "ana@correo.com"


def test_contrasena_se_guarda_cifrada():
    guardada = cifrar_contrasena("MiClave2026")

    assert "MiClave2026" not in guardada
    assert verificar_contrasena("MiClave2026", guardada)
    assert not verificar_contrasena("otra", guardada)
    assert not verificar_contrasena("MiClave2026", "formato-invalido")


def test_leer_token_invalido_devuelve_none():
    assert leer_token("abc.def.ghi") is None
