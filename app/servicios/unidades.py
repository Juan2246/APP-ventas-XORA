"""Conversión entre unidades de venta.

Los productos de cigarrería se venden en tres niveles anidados:

    1 caja = N planchas · 1 plancha = M cajetillas

El stock, en cambio, se almacena siempre en cajetillas (la *unidad base*).
Este módulo concentra la conversión entre niveles, que antes estaba repetida
—con pequeñas divergencias— en cada endpoint que tocaba el inventario.
"""

CAJETILLA = "cajetilla"
PLANCHA = "plancha"
CAJA = "caja"

TIPO_CIGARRERIA = "cigarreria"
TIPO_GENERAL = "general"


def separar_referencia(referencia):
    """Descompone la referencia que envía el front en variante y unidad.

    El carrito identifica cada línea como ``"<id>_<unidad>"`` (por ejemplo
    ``"12_caja"``). Las referencias antiguas viajaban como un id pelado, y
    para ésas la unidad es la base.

    >>> separar_referencia("12_caja")
    (12, 'caja')
    >>> separar_referencia("12")
    (12, 'cajetilla')
    """
    texto = str(referencia)
    if "_" in texto:
        id_variante, unidad = texto.split("_", 1)
        return int(id_variante), unidad
    return int(texto), CAJETILLA


def cajetillas_por_plancha(producto):
    """Cajetillas que entran en una plancha (nunca cero)."""
    return producto.cajetillas_por_plancha or 1


def planchas_por_caja(producto):
    """Planchas que entran en una caja (nunca cero)."""
    return producto.planchas_por_caja or 1


def cajetillas_por_caja(producto):
    """Cajetillas que entran en una caja."""
    return cajetillas_por_plancha(producto) * planchas_por_caja(producto)


def multiplicador(producto, unidad):
    """Cuántas unidades base representa una unidad de venta.

    Depende solo del empaquetado declarado en el producto. Los productos
    generales lo tienen fijado a 1 en ambos niveles, de modo que su
    multiplicador es 1 sea cual sea la unidad que se pida.
    """
    if unidad == CAJA:
        return cajetillas_por_caja(producto)
    if unidad == PLANCHA:
        return cajetillas_por_plancha(producto)
    return 1


def normalizar_unidad(producto, unidad):
    """Fuerza la unidad base en los productos sin empaquetado anidado."""
    if producto.tipo != TIPO_CIGARRERIA:
        return CAJETILLA
    return unidad
