# -*- coding: utf-8 -*-
{
    'name': "Web - Arreglo del editor (Google Maps)",
    'summary': "Evita que el editor de la web falle con "
               "\"Missing dependency: googleMapsOption\".",
    'description': """
Arreglo del editor de la web (Google Maps)
==========================================

El editor de la web (*website builder*) de Odoo 19 no arranca y muestra el error
``Missing dependency: googleMapsOption`` cuando el plugin ``googleMapsOption``
del módulo *website* no llega a registrarse en el navegador (bundle de assets
incompleto o regenerado a medias). La acción "Configurar clave de API" de la
pestaña *Tema* declara ese plugin como dependencia obligatoria, así que al
faltar revienta el editor entero: no se puede editar ninguna página.

Este módulo registra un plugin de reemplazo (sin funcionalidad) con ese mismo
identificador **sólo cuando el original no está cargado**, de forma que el
editor abre con normalidad. Si el plugin original sí está disponible, este
módulo no hace absolutamente nada.

Mientras el reemplazo esté activo, el bloque *Mapa de Google* no ofrece sus
opciones y el botón de configurar la clave de API avisa de que no está
disponible; el resto del editor funciona igual.
""",
    'author': "Rebersa Soluciones",
    'website': "https://www.rebersasoluciones.com",
    'category': 'Website/Website',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'depends': [
        'website',
    ],
    'assets': {
        'website.website_builder_assets': [
            'amma_website_builder_fix/static/src/js/google_maps_option_fallback.js',
        ],
    },
    'application': False,
    'installable': True,
    'auto_install': True,
}
