# Create custom reports in XLSX or PPTX format using data from the Security Posture API
This cookbook queries the Security Posture API once a day and creates custom reports in PPTX or XLSX format with the retrieved data. Each security metric is stored in a separate sheet inside XLSX workbooks or an individual slide in PPTX slides.
```mermaid
graph LR;
s[Start] --> cmd{Execute command};
cmd -- Get security posture information --> sp[Get<br>Security posture<br>information];
sp --> file{Does the<br>XLSX report exist?};
file -- Yes --> a[Append row to the<br>existing XLSX file];
file -- No --> c[Create new XLSX File];
cmd -- Generate PPTX report --> r[Read existing XLSX file];
r --> v[Create a new PPTX file<br>and insert charts];
c --> e[End];
a --> e[End];
v --> e[End];
```

## Related APIs
- [Get security posture data](https://automation.trendmicro.com/xdr/api-beta#tag/Security-Posture/paths/~1beta~1xdr~1riskInsights~1securityPosture/get)

## Required products
- At least one Trend Micro product that connects to Trend Vision One

## Sample code
- [Python](python/)
