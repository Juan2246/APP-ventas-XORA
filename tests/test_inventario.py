"""Pruebas del inventario: consulta, alta, edición y reposición."""

from app.extensions import db
from app.models import Producto, Variante


class TestConsulta:
    def test_sin_termino_devuelve_el_inventario_completo(self, client, catalogo):
        assert len(client.get("/api/search").get_json()) == 2

    def test_filtra_por_nombre_de_producto(self, client, catalogo):
        resultados = client.get("/api/search?q=lucky").get_json()
        assert len(resultados) == 1
        assert resultados[0]["nombre"] == "Lucky"

    def test_la_tabla_de_existencias_expone_stock_real_y_visual(self, client, catalogo):
        fila = client.get("/api/inventory").get_json()[0]
        assert {"stock", "stock_real", "precio_costo"} <= set(fila)


class TestAlta:
    def test_da_de_alta_mercaderia_nueva(self, client, catalogo):
        respuesta = client.post(
            "/api/product",
            json={
                "nombre": "Gorra",
                "categoria": "Ropa",
                "tipo": "general",
                "origen": "China",
                "diseno": "Lisa",
                "stock": 10,
                "costo_total": 50.0,
                "precio_sugerido": 15.0,
            },
        )

        assert respuesta.get_json()["success"] is True
        variante = Variante.query.filter_by(diseno="Lisa").one()
        assert variante.stock == 10
        assert variante.precio_costo == 5.0  # 50 de coste entre 10 unidades

    def test_el_alta_de_cigarreria_convierte_las_cajas_a_cajetillas(
        self, client, catalogo
    ):
        client.post(
            "/api/product",
            json={
                "nombre": "Marlboro",
                "categoria": "Cigarros",
                "tipo": "cigarreria",
                "planchas_por_caja": 5,
                "cajetillas_por_plancha": 10,
                "origen": "Perú",
                "unit_type": "caja",
                "stock": 2,
                "precio_sugerido": 5.0,
            },
        )

        producto = Producto.query.filter_by(nombre="Marlboro").one()
        variante = Variante.query.filter_by(producto_id=producto.id).one()
        assert variante.stock == 100  # 2 cajas x 50 cajetillas

    def test_reusa_el_producto_si_el_nombre_ya_existe(self, client, catalogo):
        client.post(
            "/api/product",
            json={
                "nombre": "Polo básico",
                "categoria": "Ropa",
                "tipo": "general",
                "origen": "Perú",
                "diseno": "Rayas",
                "stock": 5,
            },
        )
        assert Producto.query.filter_by(nombre="Polo básico").count() == 1


class TestReposicion:
    def test_repone_convirtiendo_la_unidad_de_compra(self, client, catalogo):
        client.post(
            "/api/product",
            json={
                "variant_id": catalogo["variante_cigarro"],
                "action_type": "restock",
                "unit_type": "plancha",
                "stock": 2,
            },
        )

        variante = db.session.get(Variante, catalogo["variante_cigarro"])
        assert variante.stock == 520  # 500 + (2 planchas x 10 cajetillas)

    def test_el_coste_del_lote_se_reparte_entre_las_unidades_ingresadas(
        self, client, catalogo
    ):
        client.post(
            "/api/product",
            json={
                "variant_id": catalogo["variante_cigarro"],
                "action_type": "restock",
                "unit_type": "plancha",
                "stock": 2,
                "costo_total": 20.0,
            },
        )

        variante = db.session.get(Variante, catalogo["variante_cigarro"])
        assert variante.precio_costo == 1.0  # 20 entre 20 cajetillas


class TestEdicion:
    def test_edita_los_datos_sin_tocar_el_stock(self, client, catalogo):
        client.post(
            "/api/product",
            json={
                "variant_id": catalogo["variante_polo"],
                "action_type": "edit",
                "nombre": "Polo premium",
                "categoria": "Ropa",
                "tipo": "general",
                "origen": "China",
                "diseno": "Mariposa",
                "precio_sugerido": 20.0,
                "precio_costo": 6.0,
            },
        )

        variante = db.session.get(Variante, catalogo["variante_polo"])
        assert variante.precio_sugerido == 20.0
        assert variante.stock == 40
        assert variante.producto.nombre == "Polo premium"

    def test_pasar_a_general_reinicia_el_empaquetado_y_sus_precios(
        self, client, catalogo
    ):
        client.post(
            "/api/product",
            json={
                "variant_id": catalogo["variante_cigarro"],
                "action_type": "edit",
                "nombre": "Lucky",
                "categoria": "Cigarros",
                "tipo": "general",
                "origen": "Perú",
                "precio_sugerido": 4.0,
            },
        )

        variante = db.session.get(Variante, catalogo["variante_cigarro"])
        assert variante.producto.planchas_por_caja == 1
        assert variante.producto.cajetillas_por_plancha == 1
        assert variante.precio_sugerido_caja == 0

    def test_una_variante_inexistente_responde_404(self, client, catalogo):
        respuesta = client.post(
            "/api/product", json={"variant_id": 99999, "action_type": "edit"}
        )
        assert respuesta.status_code == 404
