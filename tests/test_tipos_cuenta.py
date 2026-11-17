"""Registro por tipo de cuenta, perfil y funciones disponibles según el tipo."""

from tests.conftest import CONTRASENA, encabezado, registrar


def registro(cliente, **datos):
    base = {"nombre": "Ana", "email": "ana@correo.com", "contrasena": CONTRASENA, "acepta_terminos": True}
    return cliente.post("/auth/registro", json={**base, **datos})


def test_registro_de_negocio_guarda_sus_datos(cliente_anonimo):
    sesion = registrar(
        cliente_anonimo, "espiga@correo.com", "Panadería La Espiga", tipo="NEGOCIO",
        sector="ALIMENTOS", nit="900.123.456-7", responsable="Carlos Pérez",
    )

    usuario = sesion["usuario"]
    assert usuario["tipo_cuenta"] == "NEGOCIO"
    assert usuario["rol_negocio"] == "PROPIETARIO"
    assert usuario["nit"] == "900123456-7"
    assert usuario["nombre_negocio"] == "Panadería La Espiga"
    assert set(usuario["funciones"]) == {"CAJAS", "EQUIPO", "COMPROBANTES"}
    assert "GESTIONAR_EQUIPO" in usuario["permisos"]


def test_registro_personal_tiene_metas_y_no_equipo(cliente_anonimo):
    usuario = registrar(cliente_anonimo, "ana@correo.com", objetivo="AHORRAR")["usuario"]

    assert usuario["tipo_cuenta"] == "PERSONAL"
    assert usuario["objetivo"] == "AHORRAR"
    assert usuario["funciones"] == ["METAS"]
    assert "GESTIONAR_EQUIPO" not in usuario["permisos"]
    assert usuario["plan"] == "GRATIS"
    assert usuario["limites"]["recurrentes"] == 3 and usuario["limites"]["exportar_excel"] is False


def test_exige_aceptar_los_terminos(cliente_anonimo):
    respuesta = registro(cliente_anonimo, acepta_terminos=False)

    assert respuesta.status_code == 400
    assert "política de tratamiento de datos" in respuesta.json()["detalle"]


def test_rechaza_nit_y_sector_invalidos(cliente_anonimo):
    assert registro(cliente_anonimo, tipo_cuenta="NEGOCIO", nit="ABC").status_code == 400
    assert registro(cliente_anonimo, tipo_cuenta="NEGOCIO", sector="PIRATERIA").status_code == 400


def test_categorias_sugeridas_dependen_del_tipo(cliente_anonimo):
    personal = registrar(cliente_anonimo, "ana@correo.com", categorias_iniciales=True)
    negocio = registrar(cliente_anonimo, "tienda@correo.com", tipo="NEGOCIO", categorias_iniciales=True)

    nombres = lambda s: {c["nombre"] for c in cliente_anonimo.get("/categorias", headers=encabezado(s)).json()}  # noqa: E731

    assert "Educación" in nombres(personal) and "Nómina" not in nombres(personal)
    assert {"Ventas", "Nómina", "Impuestos"} <= nombres(negocio)


def test_opciones_de_registro(cliente_anonimo):
    datos = cliente_anonimo.get("/auth/opciones-registro").json()

    assert "AHORRAR" in datos["objetivos"]
    assert "ALIMENTOS" in datos["sectores"]


def test_actualizar_perfil(cliente):
    respuesta = cliente.patch("/auth/yo", json={"nombre": "Ana María", "objetivo": "SALIR_DE_DEUDAS"})

    assert respuesta.status_code == 200
    assert respuesta.json()["nombre"] == "Ana María"
    assert respuesta.json()["objetivo"] == "SALIR_DE_DEUDAS"


def test_cambiar_contrasena(cliente):
    incorrecta = cliente.put("/auth/yo/contrasena", json={"actual": "Otra12345", "nueva": "Nueva12345"})
    correcta = cliente.put("/auth/yo/contrasena", json={"actual": CONTRASENA, "nueva": "Nueva12345"})
    login = cliente.post("/auth/login", data={"username": "ana@correo.com", "password": "Nueva12345"})

    assert incorrecta.status_code == 400
    assert correcta.status_code == 204
    assert login.status_code == 200


def test_funciones_restringidas_por_tipo(cliente_anonimo):
    personal = encabezado(registrar(cliente_anonimo, "ana@correo.com"))
    negocio = encabezado(registrar(cliente_anonimo, "tienda@correo.com", tipo="NEGOCIO"))

    assert cliente_anonimo.get("/cajas", headers=personal).status_code == 403
    assert cliente_anonimo.get("/equipo", headers=personal).status_code == 403
    assert cliente_anonimo.get("/metas", headers=negocio).status_code == 403
    assert cliente_anonimo.get("/deudas", headers=personal).status_code == 200
    assert cliente_anonimo.get("/deudas", headers=negocio).status_code == 200
