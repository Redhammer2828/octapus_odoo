/** @odoo-module **/
import { browser } from "@web/core/browser/browser";
import { registry } from "@web/core/registry";

// Define service
export const pageRefreshService = {
    dependencies: ["bus_service"],
    start(env, { bus_service }) {
        console.log("Registering bus service for page refresh");

        bus_service.subscribe("page_refresh", ({ model_name, is_create_mode = false }) => {
            // React only if current URL targets this model
            if (!browser.location.href.includes(`model=${model_name}`)) {
                return;
            }
            maybeReloadView(model_name, is_create_mode);
        });

        function maybeReloadView(modelName, is_create_mode = false) {
            const actionService = env.services.action;

            // Parse current route
            const hash = window.location.hash.startsWith("#")
                ? window.location.hash.slice(1)
                : window.location.hash;
            const urlParams = new URLSearchParams(hash);

            const viewType = urlParams.get("view_type"); // "form", "list", ...
            const recordId = urlParams.get("id");        // null when creating

            // Special-case: always allow AFL dashboard to refresh (it is a form-like view)
            if (modelName === "afl.dashboard") {
                actionService.doAction({ type: "ir.actions.client", tag: "soft_reload" });
                return;
            }


            if (viewType === "form" && is_create_mode == false) {
                actionService.doAction({ type: "ir.actions.client", tag: "reload" });
            }
            else if (viewType === "form" && is_create_mode == true) {
                return;
            }

            // Non-form views (list/kanban/etc.) → soft reload
            // actionService.doAction({ type: "ir.actions.client", tag: "soft_reload" });
            if (viewType === "list" || viewType === "kanban") {
                actionService.doAction({ type: "ir.actions.client", tag: "soft_reload" });
                return;
            }
        }
    },
};

registry.category("services").add("pageRefresh", pageRefreshService);


