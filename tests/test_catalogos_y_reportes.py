"""Pruebas de los catálogos auxiliares, el historial y el panel de reportes."""


class TestPaginas:
    def test_todas_las_pantallas_responden(self, client, catalogo):
        for ruta in ["/", "/billing", "/inventario", "/historial", "/reportes"]:
            assert client.get(ruta).status_code == 200, ruta


class TestCatalogos:
    def test_expone_las_opciones_de_los_formularios(self, client, catalogo):
        opciones = client.get("/api/options").get_json()
        assert "Ropa" in opciones["categorias"]
        assert "China" in opciones["origenes"]

    def test_da_de_alta_una_categoria(self, client, catalogo):
        assert client.post("/api/category", json={"nombre": "Juguetes"}).get_json()[
            "success"
        ]

    def test_dar_de_alta_una_categoria_existente_no_la_duplica(self, client, catalogo):
        client.post("/api/category", json={"nombre": "Juguetes"})
        respuesta = client.post("/api/category", json={"nombre": "Juguetes"})
        assert respuesta.get_json()["message"] == "Ya existe"
        assert client.get("/api/options").get_json()["categorias"].count("Juguetes") == 1

    def test_una_categoria_sin_uso_se_puede_borrar(self, client, catalogo):
        client.post("/api/category", json={"nombre": "Juguetes"})
        assert client.delete("/api/category/Juguetes").status_code == 200

    def test_una_categoria_en_uso_no_se_puede_borrar(self, client, catalogo):
        """Borrarla dejaría productos apuntando a una categoría inexistente."""
        respuesta = client.delete("/api/category/Ropa")
        assert respuesta.status_code == 400
        assert "No se puede eliminar" in respuesta.get_json()["message"]

    def test_un_origen_en_uso_no_se_puede_borrar(self, client, catalogo):
        assert client.delete("/api/origin/China").status_code == 400

    def test_una_categoria_sin_nombre_se_rechaza(self, client, catalogo):
        assert client.post("/api/category", json={"nombre": ""}).status_code == 400


def vender_una_caja(client, catalogo):
    return client.post(
        "/process_sale",
        json={
            "total": 180.0,
            "metodo_pago": "efectivo",
            "items": [
                {
                    "id": f"{catalogo['variante_cigarro']}_caja",
                    "cantidad": 1,
                    "precio": 180.0,
                }
            ],
        },
    )


class TestHistorial:
    def test_sin_ventas_el_historial_esta_vacio(self, client, catalogo):
        assert client.get("/api/history").get_json() == []

    def test_una_venta_aparece_con_su_ganancia(self, client, catalogo):
        vender_una_caja(client, catalogo)
        historial = client.get("/api/history").get_json()

        assert len(historial) == 1
        # Se vendió a 180 una caja que costó 50
        assert historial[0]["ganancia"] == 130.0
        assert historial[0]["total_venta"] == 180.0

    def test_se_puede_filtrar_por_nombre_de_producto(self, client, catalogo):
        vender_una_caja(client, catalogo)
        assert len(client.get("/api/history?search=lucky").get_json()) == 1
        assert client.get("/api/history?search=inexistente").get_json() == []


class TestReportes:
    def test_devuelve_la_estructura_que_espera_el_panel(self, client, catalogo):
        datos = client.get("/api/reports").get_json()
        assert {"cards", "charts", "alerts"} == set(datos)
        assert {"income", "profit", "avg_ticket"} == set(datos["cards"])
        assert {"comparison", "trend", "categories", "top5"} == set(datos["charts"])

    def test_la_venta_del_dia_se_refleja_en_las_tarjetas(self, client, catalogo):
        vender_una_caja(client, catalogo)
        tarjetas = client.get("/api/reports").get_json()["cards"]

        assert tarjetas["income"] == 180.0
        assert tarjetas["profit"] == 130.0
        assert tarjetas["avg_ticket"] == 180.0

    def test_avisa_del_stock_por_debajo_del_umbral(self, client, catalogo):
        # Deja el polo en 3 unidades, bajo el umbral de 15
        client.post(
            "/process_sale",
            json={
                "total": 444.0,
                "metodo_pago": "efectivo",
                "items": [
                    {"id": str(catalogo["variante_polo"]), "cantidad": 37, "precio": 12.0}
                ],
            },
        )

        alertas = client.get("/api/reports").get_json()["alerts"]
        assert any(a["producto"] == "Polo básico" and a["stock"] == 3 for a in alertas)

    def test_sin_stock_critico_no_hay_alertas(self, client, catalogo):
        # El polo arranca con 40 y el cigarro con 500: ambos por encima de 15
        assert client.get("/api/reports").get_json()["alerts"] == []
