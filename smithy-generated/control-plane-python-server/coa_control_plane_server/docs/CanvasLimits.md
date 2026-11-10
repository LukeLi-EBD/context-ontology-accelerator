# CanvasLimits


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**max_nodes** | **float** | Maximum nodes returned by one canvas subgraph page. | 
**max_edges** | **float** | Maximum edges returned alongside those nodes. | 
**max_page_size** | **float** | Maximum page size accepted by &#x60;&#x60;maxResults&#x60;&#x60;. | 

## Example

```python
from coa_control_plane_server.models.canvas_limits import CanvasLimits

# TODO update the JSON string below
json = "{}"
# create an instance of CanvasLimits from a JSON string
canvas_limits_instance = CanvasLimits.from_json(json)
# print the JSON string representation of the object
print(CanvasLimits.to_json())

# convert the object into a dict
canvas_limits_dict = canvas_limits_instance.to_dict()
# create an instance of CanvasLimits from a dict
canvas_limits_from_dict = CanvasLimits.from_dict(canvas_limits_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


