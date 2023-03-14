# Send Workbench alerts, audit logs, and other detection data to Elasticsearch
This task retrieves Workbench alerts, Observed Attack Technique events, detections and audit logs to Elasticsearch.
```mermaid
graph LR;
s[Start] --> wb[Retrieve<br>Workbench alerts];
wb --> oat[Retrieve<br>Observed Attack Techniques<br>events];
oat --> opt{Do you need<br>other detection data?};
opt -- Yes --> d[Retrieve file and web<br>detection data];
d --> opt2{Do you need<br>audit logs?};
opt -- No --> opt2;
opt2 -- Yes --> audit[Retrieve audit logs];
audit --> cd[Convert data to format<br>required for indexing];
opt2 -- No --> cd;
cd --> ie[Index the data<br>in Elasticsearch];
ie --> e[End];
```

## Related APIs
- [Get alerts list](https://automation.trendmicro.com/xdr/api-v3#tag/Workbench/paths/~1v3.0~1workbench~1alerts/get)
- [Get Observed Attack Techniques events](https://automation.trendmicro.com/xdr/api-v3#tag/Observed-Attack-Techniques/paths/~1v3.0~1oat~1detections/get)
- [Get detection data](https://automation.trendmicro.com/xdr/api-v3#tag/Search/paths/~1v3.0~1search~1detections/get)
- [Get entries from audit logs](https://automation.trendmicro.com/xdr/api-v3#tag/Audit-Logs/paths/~1v3.0~1audit~1logs/get)

## Required products
- At least one Trend Micro product that connects to Trend Vision One

## Sample code
- [Python](python/)
