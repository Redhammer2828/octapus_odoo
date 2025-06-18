/** @odoo-module **/
import { browser } from "@web/core/browser/browser";
import { registry } from "@web/core/registry";

// Define service
export const pageRefreshService = {
    dependencies: ["bus_service"],
    start(env, { bus_service }) {
        console.log("Registering bus service for page refresh");

        bus_service.subscribe("page_refresh", ({ model_name }) => {
            console.log("Received page refresh notification");

            if (browser.location.href.includes(`model=${model_name}`)) {
                maybeReloadView();
            } else {
                console.log("Not on the target model page, skipping reload");
            }
        });

        function maybeReloadView() {
            const actionService = env.services.action;

            const hash = window.location.hash.slice(1);
            const urlParams = new URLSearchParams(hash);

            const viewType = urlParams.get('view_type');
            const recordId = urlParams.get('id');

            // If user is in form view and editing/creating, do not reload
            if (viewType === 'form') {
                if (!recordId) {
                    // In create mode → skip reload
                    console.log("In form view create mode → skipping reload");
                    return;
                } else {
                    // In form view with existing record → also skip reload to prevent breaking user flow
                    console.log("In form view with saved record → skipping reload");
                    return;
                }
            }

            // Otherwise (tree, kanban, etc.) → reload
            console.log("Executing soft reload in non-form view");
            actionService.doAction({
                type: "ir.actions.client",
                tag: "soft_reload",
            });
        }
    },
};

registry.category("services").add("pageRefresh", pageRefreshService);
