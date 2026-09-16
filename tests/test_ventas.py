"""Pruebas del punto de venta: búsqueda de artículos y registro de la venta."""

from app.extensions import db
from app.models import Sale, SaleDetail, Variante


class TestBusquedaDeArticulos:
    def test_sin_termino_no_devuelve_nada(self, client, catalogo):
        respuesta = client.get("/api/search_variants?q=")
        assert respuesta.status_code == 200
        assert respuesta.get_json() == []

    def test_un_producto_general_se_ofrece_como_una_sola_opcion(self, client, catalogo):
        articulos = client.get("/api/search_variants?q=polo").get_json()
        assert len(articulos) == 1
        assert articulos[0]["multiplicador"] == 1
        assert articulos[0]["stock"] == 40

    def test_un_producto_de_cigarreria_se_ofrece_en_sus_tres_niveles(
        self, client, catalogo
    ):
        articulos = client.get("/api/search_variants?q=lucky").get_json()
        niveles = {a["nombre_completo"].rsplit(" - ", 1)[-1][:7] for a in articulos}
        assert len(articulos) == 3
        assert {a["multiplicador"] for a in articulos} == {50, 10, 1}
        assert "CAJA x5" in niveles or any("CAJA" in a["nombre_completo"] for a in articulos)

    def test_el_stock_se_expresa_en_la_unidad_de_cada_nivel(self, client, catalogo):
        articulos = client.get("/api/search_variants?q=lucky").get_json()
        por_multiplicador = {a["multiplicador"]: a["stock"] for a in articulos}
        # 500 cajetillas son 10 cajas o 50 planchas
        assert por_multiplicador[50] == 10
        assert por_multiplicador[10] == 50
        assert por_multiplicador[1] == 500

    def test_encuentra_por_origen_ademas_de_por_nombre(self, client, catalogo):
        assert client.get("/api/search_variants?q=China").get_json()


class TestRegistroDeVenta:
    def test_vender_una_caja_descuenta_sus_cajetillas_del_stock(self, client, catalogo):
        respuesta = client.post(
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

        assert respuesta.status_code == 200
        assert respuesta.get_json()["success"] is True
        variante = db.session.get(Variante, catalogo["variante_cigarro"])
        assert variante.stock == 450  # 500 - (1 caja x 50 cajetillas)

    def test_el_coste_se_escala_a_la_unidad_vendida(self, client, catalogo):
        client.post(
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

        linea = SaleDetail.query.one()
        # La cajetilla cuesta 1.0, así que la caja de 50 cuesta 50.0
        assert linea.costo_unitario == 50.0

    def test_sin_stock_suficiente_se_rechaza_la_venta(self, client, catalogo):
        respuesta = client.post(
            "/process_sale",
            json={
                "total": 99999.0,
                "metodo_pago": "efectivo",
                "items": [
                    {
                        "id": f"{catalogo['variante_cigarro']}_caja",
                        "cantidad": 999,
                        "precio": 180.0,
                    }
                ],
            },
        )

        assert respuesta.status_code == 400
        assert "Stock insuficiente" in respuesta.get_json()["message"]

    def test_una_venta_rechazada_no_descuenta_nada(self, client, catalogo):
        """Una línea sin stock revierte la venta completa, no solo esa línea."""
        client.post(
            "/process_sale",
            json={
                "total": 99999.0,
                "metodo_pago": "efectivo",
                "items": [
                    {"id": str(catalogo["variante_polo"]), "cantidad": 1, "precio": 12.0},
                    {
                        "id": f"{catalogo['variante_cigarro']}_caja",
                        "cantidad": 999,
                        "precio": 180.0,
                    },
                ],
            },
        )

        assert db.session.get(Variante, catalogo["variante_polo"]).stock == 40
        assert Sale.query.count() == 0

    def test_una_referencia_inexistente_se_rechaza(self, client, catalogo):
        respuesta = client.post(
            "/process_sale",
            json={
                "total": 1.0,
                "metodo_pago": "efectivo",
                "items": [{"id": "99999", "cantidad": 1, "precio": 1.0}],
            },
        )
        assert respuesta.status_code == 400
