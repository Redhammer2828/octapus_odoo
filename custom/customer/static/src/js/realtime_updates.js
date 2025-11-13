/** @odoo-module **/

import { browser } from "@web/core/browser/browser";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";

export const pageRefreshService = {
    dependencies: ["bus_service", "notification"],

    start(env, { bus_service, notification }) {
        const currentUser = env.services.user.userId;
        let lastNotified = null;
        let timer = null;

        bus_service.subscribe("page_refresh", (payload = {}) => {
            const { record_id, uid } = payload;
            if (!record_id) return;

            // Skip if this user triggered the change
            if (uid && uid === currentUser) return;

            // Parse current URL once
            const hash = browser.location.hash.startsWith("#")
                ? browser.location.hash.slice(1)
                : browser.location.hash;
            const url = new URLSearchParams(hash);

            // Only trigger if on aaa.service form view of same record
            if (
                url.get("model") !== "aaa.service" ||
                url.get("view_type") !== "form" ||
                url.get("id") !== record_id.toString()
            ) {
                return;
            }

            // Prevent duplicate notifications
            if (lastNotified === record_id) return;
            lastNotified = record_id;

            notification.add(
                _t("This record was modified by another user. Please refresh to see the latest changes."),
                {
                    title: _t("Record Updated"),
                    type: "warning",
                    sticky: true,
                }
            );

            clearTimeout(timer);
            timer = setTimeout(() => {
                lastNotified = null;
            }, 5000);
        });

        return {
            destroy() {
                clearTimeout(timer);
                lastNotified = null;
            },
        };
    },
};

registry.category("services").add("pageRefresh", pageRefreshService);
