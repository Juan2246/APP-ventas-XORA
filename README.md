<img src="docs/brand.svg" width="76" height="76" alt="Símbolo de Brío">

# Brío · ventas e inventario

Hice esta aplicación para el negocio de mi familia, donde las ventas y el inventario se llevaban en facturas de papel. El reto estaba en el detalle: un mismo producto se vende por caja, por plancha o por cajetilla, y las existencias tienen que cuadrar en los tres casos.

Brío reúne el punto de venta, las reposiciones y los reportes en una aplicación local. El código conserva el nombre `APP-ventas-XORA`; en versiones y capturas anteriores aparece como XoraMarket.

**Python · Flask · SQLAlchemy · SQLite · Jinja2 · Bootstrap**

[Ver el caso en mi portafolio](https://portafolio-juan-torres-puce.vercel.app/proyectos/xoramarket)

### La decisión principal

Guardo el stock en una sola unidad base. Las cajas y planchas se convierten al registrar cada operación. Esa regla vive en `app/servicios/unidades.py`, compartida por las rutas que usan inventario.

### Estado

Uso local. Todavía no tiene autenticación de usuarios: no debe exponerse directamente a internet. La configuración de servidor incluida es un punto de partida para desarrollo, no una garantía de despliegue seguro.

## Funcionalidades

- Punto de venta con búsqueda de productos y cobro
- Inventario con alta, edición y reposición de mercadería
- **Venta por unidades anidadas:** un mismo artículo se vende por caja, por
  plancha o por cajetilla, cada una con su precio, y el stock se descuenta
  siempre en la unidad base
- Cálculo automático de coste unitario al ingresar un lote
- Historial de ventas con la ganancia de cada línea
- Panel de reportes: ingresos y ganancia del día, ticket promedio, tendencia
  del mes, reparto por categoría, más vendidos y alertas de stock crítico

## Puesta en marcha

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
python run.py
```

En PowerShell, antes de `python run.py`, definir una clave local con
`$env:SECRET_KEY = python -c "import secrets; print(secrets.token_urlsafe(48))"`.
En producción, guardarla de forma persistente en la configuración privada del
servicio. `.env.example` documenta las variables; `python run.py` no carga
archivos `.env` automáticamente.

La aplicación queda en `http://localhost:5000`. El primer arranque crea la base
de datos y siembra las categorías y orígenes iniciales.

```bash
pip install -r requirements-dev.txt
pytest                             # ejecutar las pruebas
flask --app wsgi init-db           # preparar la base de datos sin arrancar el servidor
```

## Estructura del proyecto

La aplicación se construye con el patrón **application factory**: en vez de
crear la aplicación al importar el módulo, la crea una función. Eso permite
levantarla con configuraciones distintas (desarrollo, pruebas, producción) sin
tocar el código, y es lo que hace posible que las pruebas corran contra una base
de datos en memoria.

Cada área funcional vive en su propio **blueprint**, de modo que añadir una
pantalla no implica volver a un archivo compartido por todo el sistema.

```
.
├── app/
│   ├── __init__.py          create_app(): construye y cablea la aplicación
│   ├── config.py            Configuración por entorno (nada de secretos en el código)
│   ├── extensions.py        Instancias de extensiones, sin aplicación asociada
│   ├── models.py            Modelo de datos
│   ├── cli.py               Comandos de `flask` (init-db)
│   ├── servicios/
│   │   └── unidades.py      Conversión entre caja, plancha y cajetilla
│   ├── blueprints/
│   │   ├── paginas.py       Pantallas HTML
│   │   ├── ventas.py        Búsqueda de artículos y registro de la venta
│   │   ├── inventario.py    Consulta, alta, edición y reposición
│   │   ├── catalogos.py     Categorías y orígenes
│   │   ├── historial.py     Historial de ventas
│   │   └── reportes.py      Métricas del panel
│   ├── templates/           Plantillas Jinja: solo estructura HTML
│   └── static/
│       ├── css/             Estilos globales (base.css) y de cada pantalla
│       └── js/              Lógica de cada pantalla (billing, inventory, history, reports)
├── scripts/
│   ├── audit_db.py          Utilidades de mantenimiento de la base
│   ├── clean_db.py
│   └── migraciones/         Migraciones históricas del esquema
├── tests/                   Batería de pruebas (pytest)
├── run.py                   Arranque en desarrollo
├── wsgi.py                  Punto de entrada de producción (gunicorn)
└── requirements.txt
```

### Cómo se lleva el stock

El inventario tiene una sola fuente de verdad: **el stock se guarda siempre en
la unidad base** (la cajetilla, para los productos de cigarrería). Vender una
caja no descuenta "una caja", descuenta sus 50 cajetillas.

```
1 caja = N planchas        (planchas_por_caja)
1 plancha = M cajetillas   (cajetillas_por_plancha)
```

Esa conversión estaba repetida en cada endpoint que tocaba el inventario, con
pequeñas divergencias entre copias. Ahora vive en `app/servicios/unidades.py`
y todos los endpoints la comparten.

## Pruebas

```bash
pytest
```

Las pruebas cubren la conversión de unidades, el descuento de stock, el alta y
reposición de mercadería, los catálogos, el historial y las métricas del panel.
Corren sobre SQLite en memoria: no tocan la base de datos real.

## Configuración de servidor

Antes de un despliegue público hacen falta autenticación y una revisión de seguridad. Estos comandos describen cómo iniciar el proceso, no resuelven ese límite.

En producción se sirve con gunicorn a través de `wsgi.py`:

```bash
gunicorn wsgi:app
```

El `Procfile` ya declara ese comando. En Render, el *Start Command* del servicio
debe apuntar a `gunicorn wsgi:app`.

## Configuración

| Variable | Descripción | Valor por defecto |
|---|---|---|
| `SECRET_KEY` | Clave aleatoria de sesión, mínimo 32 caracteres. Obligatoria fuera de pruebas | ninguno |
| `FLASK_ENV` | `development`, `testing` o `production` | `development` |
| `DATABASE_URL` | Cadena de conexión | `sqlite:///marketflow.db` |

La base de datos vive en `instance/` y **no se versiona**: contiene los datos
reales del negocio. Los archivos `.env` y sus variantes locales también se excluyen; solo se versiona `.env.example` sin valores privados.

## Deuda técnica conocida

- `Sale.fecha` usa `datetime.utcnow()`, que está en desuso. Migrarlo a fechas
  con zona horaria exige convertir los registros ya guardados, así que se deja
  documentado en lugar de cambiarlo a medias.
- El esquema se crea con `db.create_all()`. Un esquema que va a seguir
  evolucionando pide migraciones versionadas (Alembic / Flask-Migrate); las
  migraciones históricas de `scripts/migraciones/` son scripts sueltos.

## Autor

Juan Sebastián Torres Sánchez
