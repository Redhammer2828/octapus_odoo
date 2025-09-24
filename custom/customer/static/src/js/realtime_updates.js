/** @odoo-module **/
import { browser } from "@web/core/browser/browser";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";

export const pageRefreshService = {
    dependencies: ["bus_service", "notification"],

    start(env, { bus_service, notification }) {
        console.log("Registering bus service for page refresh");

        // 🔹 Keep track of last shown notification to avoid duplicates
        let lastNotifiedKey = null;
        let notifyTimeout = null;

        bus_service.subscribe("page_refresh", ({ model_name, record_id, is_create_mode = false, uid = null }) => {
            const actionService = env.services.action;
            const currentUser = env.services.user.userId;

            const hash = window.location.hash.startsWith("#")
                ? window.location.hash.slice(1)
                : window.location.hash;
            const urlParams = new URLSearchParams(hash);

            const modelNameFromUrl = urlParams.get("model");

            if (modelNameFromUrl == "afl.dashboard") {
                actionService.doAction({ type: "ir.actions.client", tag: "soft_reload" });
                return;
            }

            if (uid && uid === currentUser) {
                console.log("🙅 Skipping notification for triggering user:", currentUser);
                return;
            }

            if (!browser.location.href.includes(`model=${model_name}`)) {
                return;
            }

            maybeReloadView(model_name, record_id, is_create_mode, notification, actionService);
        });

        function maybeReloadView(modelName, record_id, is_create_mode = false, notification, actionService) {
            const hash = window.location.hash.startsWith("#")
                ? window.location.hash.slice(1)
                : window.location.hash;
            const urlParams = new URLSearchParams(hash);

            const viewType = urlParams.get("view_type");
            const currentRecordId = urlParams.get("id");

            // ---------- FORM VIEW ----------
            if (viewType === "form" && is_create_mode === false) {
                if (currentRecordId && currentRecordId === record_id.toString()) {
                    const key = `${modelName}_${record_id}`;

                    // ✅ Deduplicate notifications
                    if (lastNotifiedKey !== key) {
                        lastNotifiedKey = key;
                        notification.add(
                            _t("Some changes have been made. Please reload the page to view changes."),
                            {
                                title: _t("Data Updated"),
                                type: "danger",
                                sticky: true,
                            }
                        );
                        console.log("✅ Notification shown once for:", key);

                        // Reset key after 5s (so future updates can still notify)
                        clearTimeout(notifyTimeout);
                        notifyTimeout = setTimeout(() => {
                            lastNotifiedKey = null;
                        }, 5000);
                    }
                }
                return;
            }

            if (viewType === "form" && is_create_mode === true) {
                return;
            }

            if (viewType === "list" || viewType === "kanban") {
                console.log("Soft reloading list/kanban view");
                actionService.doAction({ type: "ir.actions.client", tag: "soft_reload" });
                return;
            }
        }
    },
};

registry.category("services").add("pageRefresh", pageRefreshService);


