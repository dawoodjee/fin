// Copyright (c) 2023, Adam Dawoodjee and contributors
// For license information, please see license.txt

frappe.query_reports["Data Entry Efficiency"] = {
    "filters": [
        {
            "fieldname": "select_doctype",
            "label": __("Select DocType"),
            "fieldtype": "Link",
            "options": "DocType",
            "reqd": 1, // This field is mandatory
            "description": __("Choose the DocType for which you want to generate the report."),
            "get_query": function() {
                // Fetch only submittable or non-submittable DocTypes that are relevant for data entry
                return {
                    filters: {
                        "issingle": 0, // Exclude single DocTypes
                        "istable": 0   // Exclude child table DocTypes
                    }
                };
            }
        },
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_days(frappe.datetime.get_today(), -30), // Default: 30 days ago
            "reqd": 1 // This field is mandatory
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(), // Default: Today
            "reqd": 1 // This field is mandatory
        }
    ],

    // Optional: Add an "onload" event to set default values or customize the UI
    onload: function(report) {
        // Example: Set focus on the "Select DocType" filter when the report loads
        report.filter_area.find(`[data-fieldname="select_doctype"]`).focus();
    }
};