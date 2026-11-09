# TableSummary

A summary record for a source table in list/get responses: identifiers, database, column and approved-column counts, review status, and enrichment source.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**table_id** | **str** | Unique table identifier (database.table format). | 
**name** | **str** | Table name. | 
**database** | **str** | Database the table belongs to. | 
**column_count** | **float** | Number of columns in the table. | [optional] 
**columns_approved** | **float** | Number of columns with reviewStatus&#x3D;APPROVED. Allows the UI to show approval progress (columnsApproved / columnCount) without fetching per-column detail. | [optional] 
**columns_pending_deletion** | **float** | Number of columns the re-scan found removed from the source (retained, pending deletion on approval). Lets the list surface column-level removals in the Review status column. | [optional] 
**pending_relationships** | **float** | Number of inferred foreign keys on this table with &#x60;&#x60;reviewStatus&#x3D;PENDING_REVIEW&#x60;&#x60; — relationships that a cross-source inference pass has proposed and a steward has not yet decided on. Non-zero on tables whose parent source is already &#x60;&#x60;APPROVED&#x60;&#x60; signals that the source&#39;s Approve button has already been clicked but a later cross-source pass has since found new relationships to review; the steward can drill in per-table and use per-relationship review (&#x60;&#x60;PATCH /keys&#x60;&#x60;) or per-table Approve to settle them. Absent when zero to keep response bodies small. | [optional] 
**review_status** | [**ReviewStatus**](ReviewStatus.md) |  | 
**enrichment_source** | **str** | Origin of the table&#39;s business metadata. | [optional] 
**pending_deletion** | **bool** | True when a re-scan found this table removed from the source; it is deleted on approve unless the steward keeps it. Absent/false otherwise. | [optional] 
**added** | **bool** | True when this table was created by the re-scan under review (net-new since the last approved scan). Derived from the re-scan backup; not persisted; absent outside RESCAN_REVIEW. | [optional] 

## Example

```python
from coa_control_plane_server.models.table_summary import TableSummary

# TODO update the JSON string below
json = "{}"
# create an instance of TableSummary from a JSON string
table_summary_instance = TableSummary.from_json(json)
# print the JSON string representation of the object
print(TableSummary.to_json())

# convert the object into a dict
table_summary_dict = table_summary_instance.to_dict()
# create an instance of TableSummary from a dict
table_summary_from_dict = TableSummary.from_dict(table_summary_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


