# Perform IoC Sweeping from a CSV or STIX (2.x) file
This task imports IoCs from STIX (2.x) or CSV files into a custom intelligence report, starts a sweeping task, and then checks for matched indicators.
```mermaid
graph LR;
s(Start)-->action_upload_file[Upload<br> CSV / STIX file];
action_upload_file-->action_trigger_sweeping[Trigger IoC sweeping<br>for uploaded file];
action_trigger_sweeping-->action_wait_sweeping[Wait for<br>sweeping completion];
action_wait_sweeping-->action_fetch_result[Fetch<br>sweeping result];
action_fetch_result-->check_sweeping_hit{Does sweeping<br>have any matched indicators?};
check_sweeping_hit--Yes-->action_download_result[Download<br>sweeping result];
action_download_result-->e(End);
check_sweeping_hit--No-->e;
```

## Related APIs
- [Import STIX and CSV files as custom intelligence reports](https://automation.trendmicro.com/xdr/api-v3#tag/Intelligence-Reports/paths/~1v3.0~1threatintel~1intelligenceReports/post)
- [Trigger sweeping task](https://automation.trendmicro.com/xdr/api-v3#tag/Intelligence-Reports/paths/~1v3.0~1threatintel~1intelligenceReports~1sweep/post)
- [Get task results](https://automation.trendmicro.com/xdr/api-v3#tag/Intelligence-Reports/paths/~1v3.0~1threatintel~1tasks~1{id}/get)

## Required products
- At least one of the following: Deep Security, Trend Cloud One - Workload Security, Trend Micro Apex One, Trend Micro Apex One (Mac), XDR Endpoint Sensor

## Sample code
- [Python](python/)
