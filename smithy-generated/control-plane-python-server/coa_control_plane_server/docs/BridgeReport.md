# BridgeReport

Outcome of a document-to-table bridge run, on a completed bridge job. Name lists are capped; counts are not. Additional diagnostic counters may appear.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**ontology_id** | **str** | Ontology the bridge ran on. | [optional] 
**dry_run** | **bool** | Whether this was a dry run (no proposal created). | [optional] 
**proposal_id** | **str** | The pending proposal holding the planned changes (absent on a dry run or when nothing would change). Accept it to write them. | [optional] 
**tables_considered** | **float** | Table classes considered. | [optional] 
**tables_with_evidence** | **float** | Tables that had any document evidence and were sent to the LLM. | [optional] 
**tables_without_evidence** | **List[str]** | Tables with no document evidence (left unchanged). | [optional] 
**table_definitions** | **float** | Definitions proposed for tables. | [optional] 
**column_definitions** | **float** | Definitions proposed for columns. | [optional] 
**replaced_boilerplate** | **float** | Definitions that replaced a placeholder description (the old text is kept in the description history). | [optional] 
**replaced_by_rule** | **float** | Replacements decided by the word-based placeholder check. | [optional] 
**replaced_by_model** | **float** | Replacements decided only by the model judging the existing description a placeholder: the ones to review before accepting. | [optional] 
**replaced_by_model_subjects** | **List[str]** | Tables and columns whose description the model alone judged a placeholder (capped). | [optional] 
**appended_to_existing** | **float** | Definitions appended after an informative existing description. | [optional] 
**table_links** | **float** | &#x60;skos:closeMatch&#x60; / &#x60;skos:relatedMatch&#x60; links from tables to document classes. | [optional] 
**column_links** | **float** | &#x60;skos:closeMatch&#x60; / &#x60;skos:relatedMatch&#x60; links from columns to document classes. | [optional] 
**defined_tables** | **List[str]** | Names of the tables given a definition (capped). | [optional] 
**defined_columns** | **List[str]** | Names of the columns given a definition (capped). | [optional] 
**links** | **List[str]** | The links proposed, one per entry as \&quot;&lt;table or table.column&gt; &lt;closeMatch|relatedMatch&gt; &lt;document class label&gt;\&quot; (capped). | [optional] 
**llm_calls** | **float** | Definition LLM calls made. | [optional] 
**llm_failures** | **float** | Definition LLM calls that failed after retries. | [optional] 
**first_llm_error** | **str** | First LLM error seen, if any. | [optional] 
**failed_tables** | **List[str]** | Tables whose definition calls all failed. | [optional] 
**notes** | **List[str]** | Run notes (missing evidence sources, search failures). | [optional] 
**elapsed_seconds** | **float** | Wall-clock run time in seconds. | [optional] 

## Example

```python
from coa_control_plane_server.models.bridge_report import BridgeReport

# TODO update the JSON string below
json = "{}"
# create an instance of BridgeReport from a JSON string
bridge_report_instance = BridgeReport.from_json(json)
# print the JSON string representation of the object
print(BridgeReport.to_json())

# convert the object into a dict
bridge_report_dict = bridge_report_instance.to_dict()
# create an instance of BridgeReport from a dict
bridge_report_from_dict = BridgeReport.from_dict(bridge_report_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


