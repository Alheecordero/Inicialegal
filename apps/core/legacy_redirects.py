"""URLs del sitio anterior que Google sigue mostrando. 301 a la página vigente."""

from django.urls import path
from django.views.generic import RedirectView

# Origen sin barra inicial, con barra final. Destino absoluto.
LEGACY_PATHS = {
    "inicio/": "/",
    "privacy-policy/": "/p/privacidad/",
    "landing-page-tributario/": "/areas/derecho-tributario/",
    "2025/09/15/sociedades-de-profesionales-lo-que-debes-saber-tras-la-nueva-resolucion-del-sii/": (
        "/blog/sociedades-de-profesionales-lo-que-debes-saber-tras-la-nueva-resolucion-del-sii/"
    ),
    "2025/09/15/spa-la-sociedad-preferida-por-los-emprendedores-en-chile/": (
        "/blog/spa-la-sociedad-preferida-por-los-emprendedores-en-chile-y-cuando-no-conviene-usarla/"
    ),
    "2025/09/15/spa-la-sociedad-preferida-por-los-emprendedores-en-chile-y-cuando-no-conviene-usarla/": (
        "/blog/spa-la-sociedad-preferida-por-los-emprendedores-en-chile-y-cuando-no-conviene-usarla/"
    ),
    "2025/09/15/registro-de-marcas-ante-el-inapi/": "/blog/registro-de-marcas-en-inapi/",
    "2025/09/15/registro-de-marcas-en-inapi/": "/blog/registro-de-marcas-en-inapi/",
    "2025/09/15/estas-recopilando-datos-de-clientes-sin-saberlo/": (
        "/blog/estas-recopilando-datos-de-clientes-sin-saberlo-como-evitar-multas-con-la-nueva-ley-de-proteccion-de-datos-personales/"
    ),
    "2025/09/15/estas-recopilando-datos-de-clientes-sin-saberlo-como-evitar-multas-con-la-nueva-ley-de-proteccion-de-datos-personales/": (
        "/blog/estas-recopilando-datos-de-clientes-sin-saberlo-como-evitar-multas-con-la-nueva-ley-de-proteccion-de-datos-personales/"
    ),
    "2025/09/15/errores-comunes-al-emprender-en-chile-y-como-evitarlos/": (
        "/blog/errores-comunes-al-emprender-en-chile-y-como-evitarlos/"
    ),
    "2025/09/15/terminos-y-condiciones-el-arma-secreta/": (
        "/blog/terminos-y-condiciones-el-arma-secreta-que-puede-hacer-crecer-o-hundir-tu-negocio-online/"
    ),
    "2025/09/15/terminos-y-condiciones-el-arma-secreta-que-puede-hacer-crecer-o-hundir-tu-negocio-online/": (
        "/blog/terminos-y-condiciones-el-arma-secreta-que-puede-hacer-crecer-o-hundir-tu-negocio-online/"
    ),
}


def legacy_redirect_patterns():
    return [
        path(
            source,
            RedirectView.as_view(url=target, permanent=True, query_string=True),
        )
        for source, target in LEGACY_PATHS.items()
    ]
