# Perform IoC Sweeping from a CSV or STIX (2.x) file
This task imports IoCs from STIX (2.x) or CSV files into a custom intelligence report, starts a sweeping task, and then checks for matched indicators.
![flowchart](../.resources/perform_ioc_sweeping_from_a_csv_or_stix_(2.x)_file.png)  

## Related APIs
- [Import STIX and CSV files as custom intelligence reports](https://automation.trendmicro.com/xdr/api-v3#tag/Intelligence-Reports/paths/~1v3.0~1threatintel~1intelligenceReports/post)
- [Trigger sweeping task](https://automation.trendmicro.com/xdr/api-v3#tag/Intelligence-Reports/paths/~1v3.0~1threatintel~1intelligenceReports~1sweep/post)
- [Get task results](https://automation.trendmicro.com/xdr/api-v3#tag/Intelligence-Reports/paths/~1v3.0~1threatintel~1tasks~1{id}/get)

## Required products
- At least one of the following: Deep Security, Trend Micro Cloud One - Workload Security, Trend Micro Apex One, Trend Micro Apex One (Mac), XDR Endpoint Sensor

## Sample code
- [Python](python/)
