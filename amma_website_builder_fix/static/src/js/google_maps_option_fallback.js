import { Plugin } from "@html_editor/plugin";
import { WebsiteBuilder } from "@website/builder/website_builder";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";

/**
 * El editor de la web declara una dependencia obligatoria hacia el plugin
 * "googleMapsOption" (website/static/src/builder/plugins/options/google_maps_option):
 * la acción "configureApiKey" de la pestaña Tema lo pide en su lista de
 * dependencias. Si ese plugin no se ha registrado en el navegador (por ejemplo
 * porque su módulo JS no llegó al bundle de assets), el editor entero no
 * arranca y muestra "Missing dependency: googleMapsOption".
 *
 * Este plugin sustituto expone los mismos métodos compartidos sin hacer nada,
 * de modo que el editor pueda abrirse. Sólo se añade cuando el plugin original
 * no está presente.
 */
export class GoogleMapsOptionFallbackPlugin extends Plugin {
    static id = "googleMapsOption";
    static shared = [
        "configureGMapsAPI",
        "initializeGoogleMaps",
        "failedToInitializeGoogleMaps",
        "shouldRefetchApiKey",
        "shouldNotRefetchApiKey",
        "commitPlace",
        "getPlace",
        "getMapsAPI",
        "notifyGMapsError",
    ];

    notifyUnavailable() {
        this.services.notification.add(
            _t(
                "The Google Maps options are not available on this website. Contact your administrator."
            ),
            { type: "warning" }
        );
    }

    async configureGMapsAPI() {
        this.notifyUnavailable();
        return false;
    }

    async initializeGoogleMaps() {
        return false;
    }

    failedToInitializeGoogleMaps() {}

    shouldRefetchApiKey() {
        return false;
    }

    shouldNotRefetchApiKey() {}

    commitPlace() {}

    async getPlace() {
        return undefined;
    }

    getMapsAPI() {
        return undefined;
    }

    notifyGMapsError() {
        this.notifyUnavailable();
    }
}

patch(WebsiteBuilder.prototype, {
    get builderProps() {
        const builderProps = super.builderProps;
        const plugins = builderProps.Plugins || [];
        if (!plugins.some((P) => P.id === GoogleMapsOptionFallbackPlugin.id)) {
            console.warn(
                "The 'googleMapsOption' plugin is missing: a no-op fallback is used so that the website builder can start."
            );
            builderProps.Plugins = [...plugins, GoogleMapsOptionFallbackPlugin];
        }
        return builderProps;
    },
});
