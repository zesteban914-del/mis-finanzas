from app.services.presupuesto_servicio import formato_pesos


def test_la_raiz_sirve_la_interfaz_web(cliente):
    respuesta = cliente.get("/")

    assert respuesta.status_code == 200
    assert "text/html" in respuesta.headers["content-type"]
    assert "Mis Finanzas" in respuesta.text


def test_los_archivos_de_la_interfaz_se_sirven(cliente):
    assert cliente.get("/static/js/app.js").status_code == 200
    assert cliente.get("/static/css/estilos.css").status_code == 200


def test_la_interfaz_se_revalida_siempre(cliente):
    for ruta in ["/", "/static/js/app.js", "/static/css/estilos.css"]:
        assert cliente.get(ruta).headers["cache-control"] == "no-cache", ruta


def test_sin_middlewares_para_que_vercel_use_su_cdn():
    from app.main import app

    assert app.user_middleware == []


def test_formato_pesos_usa_punto_de_miles():
    assert formato_pesos(2149000) == "$2.149.000"
