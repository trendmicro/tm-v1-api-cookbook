# Modify alert status after checking alert details
This task retrieves data about incident-related Workbench alerts and then modifies the status of these alerts after investigation is completed.
```mermaid
graph LR;
s[Start] --> a1[Retrieve<br>Workbench alerts];
a1 --> a2[Parse<br>alert details];
a2 --> a3[Update<br>alert status];
a3 --> a4[List<br>alert details];
a4 --> e[End];
```

## Related APIs
- [Get alert history with details](https://automation.trendmicro.com/xdr/api-v2#tag/Alerts/paths/~1v2.0~1xdr~1workbench~1workbenchHistories/get)
- [Edit alert status](https://automation.trendmicro.com/xdr/api-v2#tag/Alerts/paths/~1v2.0~1xdr~1workbench~1workbenches~1{workbenchId}/put)

## Required products
- At least one Trend Micro product that connects to Trend Vision One

## Sample code
- [Python](python/)
