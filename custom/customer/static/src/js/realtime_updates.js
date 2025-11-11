/** @odoo-module **/

import { browser } from "@web/core/browser/browser";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";

export const pageRefreshService = {
    dependencies: ["bus_service", "notification"],

    start(env, { bus_service, notification }) {
        const actionService = env.services.action;
        const currentUser = env.services.user.userId;

        // ═══════════════════════════════════════════════════════════
        // 🔹 Constants & Config
        // ═══════════════════════════════════════════════════════════
        const MSG_SYSTEM_BUSY = _t("High update volume detected. Please refresh manually if needed.");
        const MSG_DATA_UPDATED = _t("Status was updated by another user. Reload the page to see changes.");

        const MAX_EVENTS_PER_WINDOW = 250;
        const EVENT_WINDOW_DURATION = 10000;
        const RELOAD_DEBOUNCE_MS = 5000;
        const NOTIFICATION_RESET_MS = 5000;
        const MODEL_EVENT_DEBOUNCE_MS = 300;

        // ═══════════════════════════════════════════════════════════
        // 🔹 Internal state
        // ═══════════════════════════════════════════════════════════
        let currentViewState = null;
        let viewStateParsed = false;
        let reloadScheduled = false;
        let reloadTimer = null;
        let notificationTimer = null;
        let lastNotifiedKey = null;
        let eventCount = 0;
        let eventWindowStart = Date.now();
        const modelDebounceTimers = new Map();

        // ═══════════════════════════════════════════════════════════
        // 🔹 Navigation tracking (hash + router)
        // ═══════════════════════════════════════════════════════════
        const updateViewState = () => {
            currentViewState = parseUrl();
            viewStateParsed = true;
            lastNotifiedKey = null;
        };

        browser.addEventListener("hashchange", updateViewState);
        if (env.services.router?.on) {
            env.services.router.on("ROUTE_CHANGE", null, updateViewState);
        }

        // ═══════════════════════════════════════════════════════════
        // 🔹 Main bus subscription
        // ═══════════════════════════════════════════════════════════
        bus_service.subscribe("page_refresh", (payload) => handleRefreshEvent(payload));

        // ═══════════════════════════════════════════════════════════
        // 🔹 Handlers
        // ═══════════════════════════════════════════════════════════
        function handleRefreshEvent(payload) {
            const { model_name, uid } = payload;

            // Skip own-user events
            if (uid && uid === currentUser) return;

            // Debounce by model to avoid redundant reloads
            clearTimeout(modelDebounceTimers.get(model_name));
            modelDebounceTimers.set(
                model_name,
                setTimeout(() => processRefreshEvent(payload), MODEL_EVENT_DEBOUNCE_MS)
            );
        }

        function processRefreshEvent(payload) {
            const { model_name, record_id, is_create_mode = false } = payload;

            ensureViewStateParsed();

            // EVENT THROTTLING
            const now = Date.now();
            if (now - eventWindowStart > EVENT_WINDOW_DURATION) {
                eventCount = 0;
                eventWindowStart = now;
            }
            eventCount++;
            if (eventCount > MAX_EVENTS_PER_WINDOW) {
                if (eventCount === MAX_EVENTS_PER_WINDOW + 1) {
                    notification.add(MSG_SYSTEM_BUSY, {
                        title: _t("System Busy"),
                        type: "warning",
                        sticky: false,
                    });
                }
                return;
            }

            // Match active model
            const { model: activeModel } = getCurrentViewState();
            if (activeModel !== model_name) return;

            handleViewRefresh(model_name, record_id, is_create_mode);
        }

        function handleViewRefresh(modelName, recordId, isCreateMode) {
            const { view_type, id: currentRecordId } = getCurrentViewState();

            if (view_type === "form") {
                if (isCreateMode) return;
                if (currentRecordId && currentRecordId === recordId.toString()) {
                    showFormUpdateNotification(modelName, recordId);
                }
                return;
            }

            if (view_type === "list" || view_type === "kanban") {
                scheduleReload();
            }
        }

        // ═══════════════════════════════════════════════════════════
        // 🔹 Notifications
        // ═══════════════════════════════════════════════════════════
        function showFormUpdateNotification(modelName, recordId) {
            const notificationKey = `${modelName}_${recordId}`;

            const formView = document.querySelector(".o_form_view");
            if (!formView) return;
            if (lastNotifiedKey === notificationKey) return;

            lastNotifiedKey = notificationKey;

            notification.add(MSG_DATA_UPDATED, {
                title: _t("Data Updated"),
                type: "warning",
                sticky: true,
            });

            clearTimeout(notificationTimer);
            notificationTimer = setTimeout(() => {
                lastNotifiedKey = null;
            }, NOTIFICATION_RESET_MS);
        }

        // ═══════════════════════════════════════════════════════════
        // 🔹 Soft reload scheduling
        // ═══════════════════════════════════════════════════════════
        function scheduleReload() {
            if (reloadScheduled) return;

            reloadScheduled = true;
            clearTimeout(reloadTimer);

            reloadTimer = setTimeout(() => {
                actionService.doAction({ type: "ir.actions.client", tag: "soft_reload" });

                // Reset internal state so notifications reappear properly
                reloadScheduled = false;
                lastNotifiedKey = null;
                viewStateParsed = false; // Force re-parse after reload
                reloadTimer = null;
            }, RELOAD_DEBOUNCE_MS);
        }

        // ═══════════════════════════════════════════════════════════
        // 🔹 Helpers
        // ═══════════════════════════════════════════════════════════
        function ensureViewStateParsed() {
            if (!viewStateParsed) {
                updateViewState();
            }
        }

        function parseUrl() {
            const hash = browser.location.hash.startsWith("#")
                ? browser.location.hash.slice(1)
                : browser.location.hash;
            const urlParams = new URLSearchParams(hash);
            return {
                model: urlParams.get("model"),
                view_type: urlParams.get("view_type"),
                id: urlParams.get("id"),
            };
        }

        function getCurrentViewState() {
            let model = currentViewState?.model || null;
            let viewType = currentViewState?.view_type || null;

            const viewEl = document.querySelector(".o_form_view, .o_list_view, .o_kanban_view");
            if (viewEl) {
                model = viewEl.dataset.model || model;
                if (viewEl.classList.contains("o_form_view")) viewType = "form";
                else if (viewEl.classList.contains("o_list_view")) viewType = "list";
                else if (viewEl.classList.contains("o_kanban_view")) viewType = "kanban";
            } else if (env.services.action.currentController?.props?.resModel) {
                model = env.services.action.currentController.props.resModel;
            }

            // ✅ Reset notification state when view type changes (e.g. list → form)
            if (viewType !== currentViewState?.view_type) {
                lastNotifiedKey = null;
            }

            return { model, view_type: viewType, id: currentViewState?.id || null };
        }

        // ═══════════════════════════════════════════════════════════
        // 🔹 Cleanup
        // ═══════════════════════════════════════════════════════════
        function resetTimers() {
            clearTimeout(reloadTimer);
            clearTimeout(notificationTimer);
            reloadTimer = null;
            notificationTimer = null;
        }

        return {
            destroy() {
                resetTimers();
                lastNotifiedKey = null;
                reloadScheduled = false;
                viewStateParsed = false;
                modelDebounceTimers.clear();
            },
        };
    },
};

registry.category("services").add("pageRefresh", pageRefreshService);
