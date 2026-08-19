# Web – Arreglo del editor (Google Maps)

Módulo pequeño que evita que el **editor de la web** deje de abrirse con el error:

```
OwlError: The following error occurred in onWillStart: "Missing dependency: googleMapsOption"
Caused by: Error: Missing dependency: googleMapsOption
    at Editor.getDependencies
    at Editor.getEditorContext
    at BuilderActionsPlugin.setup
```

## Qué pasa

En Odoo 19 el editor de la web carga sus *plugins* desde el registro
`website-plugins`. Uno de ellos, `ThemeTabPlugin`
(`website/static/src/builder/plugins/theme/theme_tab_plugin.js`), registra la
acción `configureApiKey` (el botón para meter la clave de Google Maps en la
pestaña **Tema**) con esta dependencia obligatoria:

```js
export class ConfigureApiKeyAction extends BuilderAction {
    static id = "configureApiKey";
    static dependencies = ["googleMapsOption"];
```

Ese identificador lo aporta `GoogleMapsOptionPlugin`
(`website/static/src/builder/plugins/options/google_maps_option/google_maps_option_plugin.js`).

Cuando ese plugin **no llega a registrarse en el navegador** (su módulo JS no
está en el bundle `website.website_builder_assets`, el bundle se quedó a medias
al regenerarse, o un `ir.asset` lo excluyó), `BuilderActionsPlugin` pide la
dependencia al arrancar, no la encuentra y **revienta el editor entero**: no se
puede editar ninguna página, aunque no se use el bloque *Mapa de Google*.

## Qué hace este módulo

Comprueba, justo antes de arrancar el editor, si el plugin `googleMapsOption`
está en la lista de plugins. Si **no** está, añade un plugin sustituto con ese
mismo identificador que expone los mismos métodos compartidos sin hacer nada, y
deja un aviso en la consola. El editor abre con normalidad.

Si el plugin original sí está cargado (funcionamiento normal), este módulo no
hace nada.

Mientras el sustituto esté activo:

- el bloque *Mapa de Google* no muestra sus opciones en el editor;
- el botón de configurar la clave de API avisa de que no está disponible;
- el resto del editor funciona igual que siempre.

## Antes de dar el problema por cerrado

Este módulo es una **red de seguridad**: mantiene el editor usable, pero no
recupera las opciones del mapa. Si se quieren de vuelta, hay que arreglar el
origen en el servidor:

1. Regenerar los assets (Ajustes → Técnico → **Regenerar los bundles de
   assets**), o borrar los adjuntos de assets y recargar con `?debug=assets`.
2. Comprobar en la consola del navegador si el cargador de módulos JS avisa de
   módulos que no se han podido cargar (ahí aparecería
   `@website/builder/plugins/options/google_maps_option/...`).
3. Revisar en Ajustes → Técnico → **Assets** si hay algún registro `ir.asset`
   que quite ficheros de `website/static/src/builder/**`.

## Instalación

Depende sólo de `website` y está marcado como `auto_install`, así que se instala
solo en cuanto el módulo *Sitio web* esté instalado. Se puede desinstalar sin
efectos secundarios.
