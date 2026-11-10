# GetCanvasManifestResponseContent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**capabilities** | **List[str]** | Capabilities the canvas may rely on (e.g. &#x60;&#x60;nodeKinds&#x60;&#x60;, &#x60;&#x60;graphFilter&#x60;&#x60;, &#x60;&#x60;cursorPaging&#x60;&#x60;). Clients must ignore values they do not recognise, so a capability can be added without breaking older frontends. | 
**limits** | [**CanvasLimits**](CanvasLimits.md) |  | 

## Example

```python
from coa_control_plane_server.models.get_canvas_manifest_response_content import GetCanvasManifestResponseContent

# TODO update the JSON string below
json = "{}"
# create an instance of GetCanvasManifestResponseContent from a JSON string
get_canvas_manifest_response_content_instance = GetCanvasManifestResponseContent.from_json(json)
# print the JSON string representation of the object
print(GetCanvasManifestResponseContent.to_json())

# convert the object into a dict
get_canvas_manifest_response_content_dict = get_canvas_manifest_response_content_instance.to_dict()
# create an instance of GetCanvasManifestResponseContent from a dict
get_canvas_manifest_response_content_from_dict = GetCanvasManifestResponseContent.from_dict(get_canvas_manifest_response_content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


