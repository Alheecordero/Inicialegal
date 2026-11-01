"""URLs del sitio anterior que Google sigue mostrando. 301 a la página vigente."""

from django.http import HttpResponsePermanentRedirect
from django.urls import path, re_path
from django.views.generic import RedirectView

# Origen sin barra inicial, con barra final. Destino absoluto.
LEGACY_PATHS = {
    "inicio/": "/",
    "privacy-policy/": "/p/privacidad/",
    "landing-page-tributario/": "/areas/derecho-tributario/",
    "landing-page-derecho-laboral/": "/areas/derecho-laboral/",
    "serviciospenales/": "/areas/derecho-penal-economico/",
    "2025/09/15/spa-la-sociedad-preferida-por-los-emprendedores-en-cl/": (
        "/blog/spa-la-sociedad-preferida-por-los-emprendedores-en-chile-y-cuando-no-conviene-usarla/"
    ),
    "2025/10/10/consumidor-digital-y-proteccion-de-datos-la-nueva-responsabilidad-de-los-emprendedores-que-inspiran-confianza/": (
        "/areas/tecnologia-y-datos/"
    ),
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


def legacy_dated_post(request, slug):
    """Cualquier otra URL de WordPress con fecha (/AAAA/MM/DD/slug/): al artículo si existe, si no al blog."""
    from apps.blog.models import Post

    post = Post.published.filter(slug=slug).first()
    return HttpResponsePermanentRedirect(post.get_absolute_url() if post else "/blog/")


def legacy_redirect_patterns():
    return [
        *(
            path(source, RedirectView.as_view(url=target, permanent=True, query_string=True))
            for source, target in LEGACY_PATHS.items()
        ),
        re_path(r"^\d{4}/\d{2}/\d{2}/(?P<slug>[-\w]+)/?$", legacy_dated_post),
    ]
