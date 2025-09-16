/** @odoo-module **/

import { registry } from "@web/core/registry";
import { CharField } from "@web/views/fields/char/char_field";
import { useService } from "@web/core/utils/hooks";
import { debounce } from "@web/core/utils/timing";
import { useState, useRef, onWillStart } from "@odoo/owl";

/**
 * Location Search Widget
 */
export class LocationSearchWidget extends CharField {
    static template = "customer.LocationSearchInput";

    setup() {
        super.setup();

        this.state = useState({
            inputValue: this.props.value || "",
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
            if (this.props.value) {
                this.state.inputValue = this.props.value;
            }
        });
    }



    getDebugTitle() {
        this.state.inputValue = this.props.record.data[this.props.name]
        console.log('Props:', this.props);
        console.log('Props.value:', this.props.value);
        console.log('State.inputValue:', this.state.inputValue);
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

            if (fieldName === "location_from_external") {
                query = `${countryFromName} ${value}`.trim();
                console.log(countryFromName)
            } else if (fieldName === "location_to_external") {
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

    selectLocation(location /*, index*/) {
        this.state.selectedLocation = location;
        this.state.inputValue = location.name || "";
        this.state.showDropdown = false;

        if (this.props.update) {
            this.props.update(this.state.inputValue);
        }

        const fieldName = this.props.name;
        const updates = {};
        if (fieldName === "location_from_external") {
            updates["location_from_external"] = location.name || "";
            updates["location_from_id"] = location.id || "";
            updates["location_from_latitude"] = location.latitude || 0.0;
            updates["location_from_longitude"] = location.longitude || 0.0;
            updates["from_location_emirate"] = location.emirate || "";
        } else if (fieldName === "location_to_external") {
            updates["location_to_external"] = location.name || "";
            updates["location_to_id"] = location.id || "";
            updates["location_to_latitude"] = location.latitude || 0.0;
            updates["location_to_longitude"] = location.longitude || 0.0;
            updates["to_location_emirate"] = location.emirate || "";
        }
        if (Object.keys(updates).length > 0 && this.props.record?.update) {
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
        if (fieldName === "location_from_external") {
            updates["location_from_external"] = "";
            updates["location_from_id"] = false;
            updates["location_from_latitude"] = 0.0;
            updates["location_from_longitude"] = 0.0;
            updates["from_location_emirate"] = "";
        } else if (fieldName === "location_to_external") {
            updates["location_to_external"] = "";
            updates["location_to_id"] = false;
            updates["location_to_latitude"] = 0.0;
            updates["location_to_longitude"] = 0.0;
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
    supportedTypes: ["char"],
});




// inherited char field widget but throws error

// /** @odoo-module **/

// import { registry } from "@web/core/registry";
// import { CharField } from "@web/views/fields/char/char_field";
// import { useService } from "@web/core/utils/hooks";
// import { debounce } from "@web/core/utils/timing";
// import { useState, useRef, onWillStart } from "@odoo/owl";

// /**
//  * Location Search Widget
//  */
// export class LocationSearchWidget extends CharField {
//     static template = "customer.LocationSearchInput";

//     setup() {
//         // Call CharField.setup() first → gives you input ref, useInputField, dynamic placeholder
//         super.setup();

//         // Add your own state
//         this.state = useState({
//             inputValue: this.props.value || "",
//             suggestions: [],
//             isLoading: false,
//             selectedLocation: null,
//             showDropdown: false,
//         });

//         this.inputRef = useRef("input");
//         this.rpc = useService("rpc");
//         this.notification = useService("notification");

//         this.debouncedSearch = debounce(this.searchLocations.bind(this), 300);

//         onWillStart(() => {
//             if (this.props.value) {
//                 this.state.inputValue = this.props.value;
//             }
//         });
//     }

//     // Your custom logic for searching locations
//     onInput(ev) {
//         const value = ev.target.value;
//         this.state.inputValue = value;
//         this.state.showDropdown = true;

//         if (value.length >= 3) {
//             this.state.isLoading = true;
//             this.debouncedSearch(value);
//         } else {
//             this.state.suggestions = [];
//             this.state.showDropdown = false;
//         }
//     }

//     async searchLocations(query) {
//         if (!query || query.length < 3) {
//             this.state.isLoading = false;
//             return;
//         }
//         try {
//             const results = await this.rpc("/api/location/search", { query });
//             this.state.suggestions = results || [];
//             this.state.isLoading = false;
//         } catch (error) {
//             this.state.isLoading = false;
//             this.state.suggestions = [];
//             this.notification.add("Error searching locations. Please try again.", { type: "danger" });
//         }
//     }

//     selectLocation(location) {
//         this.state.selectedLocation = location;
//         this.state.inputValue = location.name || "";
//         this.state.showDropdown = false;

//         if (this.props.update) {
//             this.props.update(this.state.inputValue);
//         }

//         // Update related fields
//         const fieldName = this.props.name;
//         const updates = {};
//         if (fieldName === "location_from_external") {
//             updates["location_from_id"] = location.id || "";
//             updates["location_from_latitude"] = location.latitude || 0.0;
//             updates["location_from_longitude"] = location.longitude || 0.0;
//             updates["emirate_from_location"] = location.emirate || "";
//         } else if (fieldName === "location_to_external") {
//             updates["location_to_id"] = location.id || "";
//             updates["location_to_latitude"] = location.latitude || 0.0;
//             updates["location_to_longitude"] = location.longitude || 0.0;
//             updates["emirate_to_location"] = location.emirate || "";
//         }
//         if (Object.keys(updates).length > 0 && this.props.record?.update) {
//             this.props.record.update(updates);
//         }
//     }

//     clearInput() {
//         this.state.inputValue = "";
//         this.state.selectedLocation = null;
//         this.state.suggestions = [];
//         this.state.showDropdown = false;

//         if (this.props.update) {
//             this.props.update("");
//         }

//         const fieldName = this.props.name;
//         const updates = {};
//         if (fieldName === "location_from_external") {
//             updates["location_from_external"] = "";
//             updates["location_from_id"] = false;
//             updates["location_from_latitude"] = 0.0;
//             updates["location_from_longitude"] = 0.0;
//             updates["emirate_from_location"] = "";
//         } else if (fieldName === "location_to_external") {
//             updates["location_to_external"] = "";
//             updates["location_to_id"] = false;
//             updates["location_to_latitude"] = 0.0;
//             updates["location_to_longitude"] = 0.0;
//             updates["emirate_to_location"] = "";
//         }
//         if (Object.keys(updates).length > 0 && this.props.record?.update) {
//             this.props.record.update(updates);
//         }
//     }
// }

// // Register the widget
// registry.category("fields").add("location_search", {
//     component: LocationSearchWidget,
//     supportedTypes: ["char"],
// });






// old code without inheriting char field widget

// /** @odoo-module **/
// import { registry } from "@web/core/registry";
// import { CharField } from "@web/views/fields/char/char_field";
// import { Component, onWillStart, useRef, useState } from "@odoo/owl";
// import { _t } from "@web/core/l10n/translation";
// import { standardFieldProps } from "@web/views/fields/standard_field_props";
// import { useService } from "@web/core/utils/hooks";
// import { debounce } from "@web/core/utils/timing";

// /**
//  * Location Search Widget
//  */
// export class LocationSearchWidget extends Component {
//     static template = "customer.LocationSearchInput";
//     static props = {
//         ...standardFieldProps,
//     };

//     setup() {
//         this.state = useState({
//             inputValue: this.props.value || "",
//             suggestions: [],
//             isLoading: false,
//             selectedLocation: null,
//             showDropdown: false,
//         });

//         this.inputRef = useRef("input");
//         this.rpc = useService("rpc");
//         this.notification = useService("notification");

//         // Set up debounced search function (300ms delay)
//         this.debouncedSearch = debounce(this.searchLocations.bind(this), 300);

//         onWillStart(() => {
//             if (this.props.value) {
//                 this.state.inputValue = this.props.value;
//             }
//         });
//     }

//     /**
//      * Handle input changes and trigger debounced search
//      */
//     onInput(ev) {
//         const value = ev.target.value;
//         this.state.inputValue = value;
//         this.state.showDropdown = true;
        
//         if (value.length >= 3) {
//             this.state.isLoading = true;
//             this.debouncedSearch(value);
//         } else {
//             this.state.suggestions = [];
//             this.state.showDropdown = false;
//         }
//     }

//     /**
//      * Clear the input field and reset related data
//      */
//     clearInput() {
//         this.state.inputValue = "";
//         this.state.selectedLocation = null;
//         this.state.suggestions = [];
//         this.state.showDropdown = false;
//         this.state.isLoading = false;

//         // Update the main field value
//         if (this.props.update) {
//             this.props.update("");
//         }

//         // Clear related fields
//         const fieldName = this.props.name;
//         const updates = {};

//         if (fieldName === "location_from_external") {
//             updates["location_from_id"] = "";
//             updates["location_from_latitude"] = 0.0;
//             updates["location_from_longitude"] = 0.0;
//             updates["emirate_from_location"] = "";
//         } else if (fieldName === "location_to_external") {
//             updates["location_to_id"] = "";
//             updates["location_to_latitude"] = 0.0;
//             updates["location_to_longitude"] = 0.0;
//             updates["emirate_to_location"] = "";
//         }

//         // Apply updates to the current record
//         if (Object.keys(updates).length > 0 && this.props.record?.update) {
//             this.props.record.update(updates);
//         }

//         // Focus back to the input after clearing
//         if (this.inputRef.el) {
//             this.inputRef.el.focus();
//         }
//     }

//     /**
//      * Perform the API call to search locations
//      */
//     async searchLocations(query) {
//         if (!query || query.length < 3) {
//             this.state.isLoading = false;
//             return;
//         }

//         try {
//             // Call backend method to handle the actual API request
//             const results = await this.rpc("/api/location/search", {
//                 query: query,
//             });
//             console.log(results)

//             this.state.suggestions = results || [];
//             this.state.isLoading = false;
//         } catch (error) {
//             this.state.isLoading = false;
//             this.state.suggestions = [];
//             this.notification.add(_t("Error searching locations. Please try again."), {
//                 type: "danger",
//             });
//             console.error("Location search failed:", error);
//         }
//     }

//     /**
//      * Select a location from suggestions
//      */
//     selectLocation(location) {
//         this.state.selectedLocation = location;
//         this.state.inputValue = location.name || "";
//         this.state.showDropdown = false;

//         // Update the main field value (e.g., location_from or location_to)
//         if (this.props.update) {
//             this.props.update(this.state.inputValue);
//         }

//         // Determine which related fields to update
//         const fieldName = this.props.name;
//         const updates = {};

//         if (fieldName === "location_from_external") {
//             updates["location_from_external"] = location.name || "";
//             updates["location_from_id"] = location.id || "";
//             updates["location_from_latitude"] = location.latitude || 0.0;
//             updates["location_from_longitude"] = location.longitude || 0.0;
//             updates["emirate_from_location"] = location.emirate || "";
//         } else if (fieldName === "location_to_external") {
//             updates["location_from_external"] = location.name || "";
//             updates["location_to_id"] = location.id || "";
//             updates["location_to_latitude"] = location.latitude || 0.0;
//             updates["location_to_longitude"] = location.longitude || 0.0;
//             updates["emirate_to_location"] = location.emirate || "";
//         }

//         // Apply updates to the current record
//         if (Object.keys(updates).length > 0 && this.props.record?.update) {
//             this.props.record.update(updates);
//         }
//     }

//     /**
//      * Show tooltip on hover for long location names
//      */
//     onSuggestionMouseEnter(ev) {
//         const tooltip = ev.currentTarget.querySelector('.o_location_tooltip');
//         const suggestionText = ev.currentTarget.querySelector('.fw-normal').textContent;
        
//         // Only show tooltip if text is truncated (longer than visible area)
//         const textElement = ev.currentTarget.querySelector('.fw-normal');
//         if (textElement.scrollWidth > textElement.clientWidth || suggestionText.length > 50) {
//             if (tooltip) {
//                 tooltip.classList.remove('d-none');
//             }
//         }
//     }

//     /**
//      * Hide tooltip on mouse leave
//      */
//     onSuggestionMouseLeave(ev) {
//         const tooltip = ev.currentTarget.querySelector('.o_location_tooltip');
//         if (tooltip) {
//             tooltip.classList.add('d-none');
//         }
//     }

//     /**
//      * Close the dropdown when clicking outside
//      */
//     onWindowClick(ev) {
//         if (this.inputRef.el && !this.inputRef.el.contains(ev.target)) {
//             this.state.showDropdown = false;
//         }
//     }
// }

// // Register the widget
// registry.category("fields").add("location_search", {
//     component: LocationSearchWidget,
//     supportedTypes: ["char"],
// });



