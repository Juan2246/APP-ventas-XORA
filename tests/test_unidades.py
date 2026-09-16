"""Pruebas de la conversión entre unidades de venta."""

from types import SimpleNamespace

from app.servicios.unidades import (
    CAJA,
    CAJETILLA,
    PLANCHA,
    multiplicador,
    normalizar_unidad,
    separar_referencia,
)


def producto(tipo="cigarreria", planchas=5, cajetillas=10):
    """Producto mínimo para probar la conversión sin tocar la base de datos."""
    return SimpleNamespace(
        tipo=tipo, planchas_por_caja=planchas, cajetillas_por_plancha=cajetillas
    )


class TestSepararReferencia:
    def test_separa_el_id_y_la_unidad_de_una_referencia_compuesta(self):
        assert separar_referencia("12_caja") == (12, CAJA)

    def test_una_referencia_sin_unidad_se_interpreta_como_unidad_base(self):
        assert separar_referencia("12") == (12, CAJETILLA)

    def test_acepta_un_entero_ademas_de_una_cadena(self):
        assert separar_referencia(7) == (7, CAJETILLA)


class TestMultiplicador:
    def test_una_caja_equivale_a_planchas_por_cajetillas(self):
        assert multiplicador(producto(), CAJA) == 50

    def test_una_plancha_equivale_a_sus_cajetillas(self):
        assert multiplicador(producto(), PLANCHA) == 10

    def test_la_cajetilla_es_la_unidad_base(self):
        assert multiplicador(producto(), CAJETILLA) == 1

    def test_un_empaquetado_sin_definir_no_anula_el_calculo(self):
        # Las filas antiguas pueden tener los factores a NULL: valen 1, no 0.
        assert multiplicador(producto(planchas=None, cajetillas=None), CAJA) == 1


class TestNormalizarUnidad:
    def test_un_producto_general_siempre_se_mueve_en_unidad_base(self):
        assert normalizar_unidad(producto(tipo="general"), CAJA) == CAJETILLA

    def test_un_producto_de_cigarreria_conserva_la_unidad_pedida(self):
        assert normalizar_unidad(producto(), CAJA) == CAJA
