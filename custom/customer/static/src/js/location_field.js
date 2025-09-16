/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Many2OneField } from "@web/views/fields/many2one/many2one_field";
import { useService } from "@web/core/utils/hooks";
import { debounce } from "@web/core/utils/timing";
import { useState, useRef, onWillStart } from "@odoo/owl";

/**
 * Location Search Widget
 */
export class LocationSearchWidget extends Many2OneField {
    static template = "customer.LocationSearchInput";

    setup() {
        super.setup();

        const val = this.props.value;
        this.state = useState({
            inputValue: Array.isArray(val) ? val[1] : (val || ""),
            suggestions: [],
            isLoading: false,
            selectedLocation: null,
            showDropdown: false,
        });

        this.inputRef = useRef("input");
        this.rpc = useService("rpc");
        this.notification = useService("notification");

        this.debouncedSearch = debounce(this.searchLocations.bind(this), 300);

        onWillStart(() => {
            const val = this.props.value;
            if (this.props.value) {
                this.state.inputValue = Array.isArray(val) ? val[1] : (val || "");
            }
        });
    }



    getDebugTitle() {
        const value = this.props.record.data[this.props.name];
        if (Array.isArray(value)) {
            this.state.inputValue = value[1];   // <-- take the display_name
        } else {
            this.state.inputValue = "";
        }

        return this.state.inputValue;
    }



    onInput(ev) {
        const value = ev.target.value;
        this.state.inputValue = value;
        this.state.showDropdown = true;
        const fieldName = this.props.name;
        const countryFromName = this.props.record.data.country_from_id?.[1] || "";
        const countryToName = this.props.record.data.country_to_id?.[1] || "";


        if (value.length >= 3) {
            this.state.isLoading = true;
            let query = ""; 

            if (fieldName === "selected_from_location") {
                query = `${countryFromName} ${value}`.trim();
                console.log(countryFromName)
            } else if (fieldName === "selected_to_location") {
                query = `${countryToName} ${value}`.trim();
                console.log(countryToName)
            }

            this.debouncedSearch(query);
        } else {
            this.state.suggestions = [];
            this.state.showDropdown = false;
        }
    }

    async searchLocations(query) {
        if (!query || query.length < 3) {
            this.state.isLoading = false;
            return;
        }
        try {
            const results = await this.rpc("/api/location/search", { query });
            this.state.suggestions = results || [];
            this.state.isLoading = false;
        } catch (error) {
            this.state.isLoading = false;
            this.state.suggestions = [];
            this.notification.add("Error searching locations. Please try again.", { type: "danger" });
        }
    }

    async createNewLocation(name, latitude, longitude) {
        try {
            const locationIds = await this.env.services.orm.create("location.suggestion", [
                {
                    name: name,
                    latitude: latitude,
                    longitude: longitude,
                },
            ]);
            console.log("Created Location ID:", locationIds[0]); // first created ID
            return locationIds[0];
        } catch (error) {
            console.error("Error creating record:", error);
        }
    }


    async selectLocation(location) {
        this.state.selectedLocation = location;
        this.state.inputValue = location.name || "";
        this.state.showDropdown = false;

        const locationId = await this.createNewLocation(
            location.name,
            location.latitude,
            location.longitude
        );

        // ✅ store ID in DB, show name in UI
        const updates = {};
        if (this.props.name === "selected_from_location") {
            updates.selected_from_location = locationId ? [locationId, location.name] : false;
            updates.from_location_emirate = location.emirate || "";
        } else if (this.props.name === "selected_to_location") {
            updates.selected_to_location = locationId ? [locationId, location.name] : false;
            updates.to_location_emirate = location.emirate || "";
        }

        this.state.recordId = locationId;

        if (this.props.record?.update) {
            this.props.record.update(updates);
        }
    }

    clearInput() {
        this.state.inputValue = "";
        this.state.selectedLocation = null;
        this.state.suggestions = [];
        this.state.showDropdown = false;

        if (this.props.update) {
            this.props.update("");
        }

        const fieldName = this.props.name;
        const updates = {};

        if (fieldName === "selected_from_location") {
            updates["selected_from_location"] = false;
            updates["from_location_emirate"] = "";
        } else if (fieldName === "selected_to_location") {
            updates["selected_to_location"] = false;
            updates["to_location_emirate"] = "";
        }

        if (Object.keys(updates).length > 0 && this.props.record?.update) {
            this.props.record.update(updates);
        }

        if (this.inputRef?.el) {
            this.inputRef.el.focus();
        }
    }

    onWindowClick() {
        this.state.showDropdown = false;
    }

}

registry.category("fields").add("location_search", {
    component: LocationSearchWidget,
    supportedTypes: ["many2one"],
});




