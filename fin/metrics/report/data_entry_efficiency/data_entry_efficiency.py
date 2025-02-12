import frappe
from datetime import timedelta

def execute(filters=None):
    if not filters:
        filters = {}

    # Filters
    doctype = filters.get("select_doctype")
    from_date = filters.get("from_date") or frappe.utils.add_days(frappe.utils.nowdate(), -30)
    to_date = filters.get("to_date") or frappe.utils.nowdate()

    if not doctype:
        frappe.throw("Please select a DocType.")

    # Fetch all documents created within the date range
    documents = frappe.get_all(
        doctype,
        filters={
            "creation": ["between", [from_date, to_date]],
            "owner": ["!=", ""]
        },
        fields=["name", "owner", "creation", "modified", "docstatus"],
        order_by="creation asc"
    )

    # Check if the DocType is submittable
    is_submittable = frappe.get_meta(doctype).is_submittable

    # Process data
    user_data = {}
    for doc in documents:
        user = doc["owner"]

        # Determine the end time based on whether the DocType is submittable
        if is_submittable and doc["docstatus"] == 1:
            # Find the submission timestamp from the Version Log
            submission_time = get_submission_time(doc["name"], doctype)
            if not submission_time:
                continue  # Skip if no submission time is found
            end_time = submission_time
        elif not is_submittable:
            # Use the modified timestamp for non-submittable DocTypes
            end_time = doc["modified"]
        else:
            continue  # Skip unsubmitted documents for submittable DocTypes

        # Calculate time taken to create the document
        time_taken = frappe.utils.time_diff_in_seconds(end_time, doc["creation"])

        # Update user data
        if user not in user_data:
            user_data[user] = {
                "total_documents": 0,
                "total_time_taken": 0,
                "documents": []
            }

        user_data[user]["total_documents"] += 1
        user_data[user]["total_time_taken"] += time_taken
        user_data[user]["documents"].append({
            "name": doc["name"],
            "time_taken": time_taken
        })

    # Prepare final result
    result = []
    for user, data in user_data.items():
        if data["total_documents"] > 0:
            avg_time_taken = data["total_time_taken"] / data["total_documents"]
            avg_time_minutes = round(avg_time_taken / 60, 2)  # Convert seconds to minutes
            result.append([user, data["total_documents"], avg_time_minutes])

    # Sort by average time taken (ascending)
    result.sort(key=lambda x: x[2])

    # Columns
    columns = [
        {"label": "User Name", "fieldname": "user_name", "fieldtype": "Data", "width": 200},
        {"label": "Total Documents Created", "fieldname": "total_documents", "fieldtype": "Int", "width": 150},
        {"label": "Average Time Taken per Document (minutes)", "fieldname": "avg_time", "fieldtype": "Float", "width": 200}
    ]

    # Handle no data case
    if not result:
        return columns, []

    return columns, result


def get_submission_time(doc_name, doctype):
    """
    Get the timestamp when the document was submitted (docstatus changed from 0 to 1).
    :param doc_name: Name of the document
    :param doctype: DocType of the document
    :return: Submission timestamp or None if not found
    """
    version_data = frappe.get_all(
        "Version",
        filters={
            "ref_doctype": doctype,
            "docname": doc_name,
            "data": ["like", '%docstatus%']  # Filter versions where docstatus was changed
        },
        fields=["creation", "data"],
        order_by="creation asc"
    )

    for version in version_data:
        try:
            # Parse the 'data' field to extract the old and new values of docstatus
            data = frappe.parse_json(version.data)
            if data.get("changed"):
                for field, old_value, new_value in data["changed"]:
                    if field == "docstatus" and old_value == "0" and new_value == "1":
                        return version.creation
        except Exception:
            continue

    return None