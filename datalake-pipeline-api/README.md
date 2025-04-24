# Datalake Pipeline API cookbook

```mermaid
flowchart TD
    A[Start] --> C{Command Type}
    
    C -->|register| D[Register Data Pipeline]
    C -->|list| E[List Data Pipelines]
    C -->|get| F[Get Pipeline Details]
    C -->|update| G[Update Pipeline]
    C -->|delete| H[Delete Pipeline]
    C -->|list-packages| I[List Pipeline Packages]
    C -->|get-package| J[Get Single Package]
    C -->|continuous-get-packages| K[Start Continuous Capture]
    
    D --> V
    E --> V
    F --> V
    G --> V
    H --> V
    I --> V
    J --> V
    
    K --> Q[Initialize Capture Parameters]
    Q --> R[Wait for Interval]
    R --> S[Fetch Packages]
    S --> T[Save Packages to Bundle]
    T --> U{Continue Capturing?}
    U -->|Yes| R
    U -->|No| V[End]
```

## Related API
- [Data Pipeline Management API](https://automation.trendmicro.com/xdr/api-v3/#tag/Datalake-Pipeline)

## Required Products
- At least one Trend Micro product that connects to Trend Vision One

## Sample code
- [Python](python/)