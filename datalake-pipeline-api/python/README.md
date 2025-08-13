# Cookbook: "Datalake Pipeline API"
## System Requirements
- Python 3.9 or higher

## Environment Setup

1. Clone this repository or download the script and install dependencies using pipenv:

```bash
# Install pipenv if you don't have it
pip install pipenv
```
2. Create a virtual environment for installing packages and managing dependencies.
```bash
# Install the dependencies from Pipfile
pipenv install

# Activate the virtual environment
pipenv shell    
```
3. Modify the settings in `datalake_pipeline_api.py` to match your environment.
```python
V1_TOKEN = os.environ.get('TMV1_TOKEN', '')
V1_URL = os.environ.get('TMV1_URL', 'https://api.xdr.trendmicro.com')
V1_UA = os.environ.get('TMV1_UA', f'Trend Vision One API Cookbook({os.path.basename(__file__)})')
```
## Sample Script
1. The script provides a command-line interface for interacting with the Datalake Pipeline API.

```bash
python datalake_pipeline_api.py -u <API_ENDPOINT_URL> -f <JWT_TOKEN_FILE> <COMMAND> [OPTIONS]
```
2. Example commands:
The following examples demonstrate all available operations with the Datalake Pipeline API.
```bash
# 1. Register (bind a data type to a pipeline)
python datalake_pipeline_api.py register -t telemetry -d "My telemetry pipeline" -s endpoint -s email

# 2. List all bound data pipelines
python datalake_pipeline_api.py list

# 3. Get specific pipeline information
python datalake_pipeline_api.py get <PIPELINE_ID>

# 4. Update pipeline settings
python datalake_pipeline_api.py update <PIPELINE_ID> -t detection -d "Updated description"

# 5. Delete (unbind) pipeline(s)
python datalake_pipeline_api.py delete <PIPELINE_ID1> <PIPELINE_ID2>

# 6. List available packages from a pipeline
python datalake_pipeline_api.py list-packages <PIPELINE_ID> -s 2023-10-01T00:00:00Z -e 2023-10-01T23:59:59Z

# 7. Get specific package content
python datalake_pipeline_api.py get-package <PIPELINE_ID> <PACKAGE_ID> <OUTPUT_FILE_PATH>

# 8. Continuous package retrieval (runs until Ctrl+C)
python datalake_pipeline_api.py continuous-get-packages <PIPELINE_ID> <OUTPUT_DIR> -v 180 -t 500
```
## Expected Results
The script outputs results for each of the 8 available operations:

### 1. Register Command
```text
request: register, args: type=telemetry, description=My telemetry pipeline
resp=<Response [201]>, trace-id=12345678-1234-1234-1234-123456789abc
https://api.xdr.trendmicro.com/v3.0/datalake/dataPipelines/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

### 2. List Command
```text
request: list
resp=<Response [200]>, trace-id=12345678-1234-1234-1234-123456789abc
{
  "items": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "type": "telemetry",
      "subType": ["endpoint", "email"],
      "description": "My telemetry pipeline",
      "registeredDateTime": "2023-10-17T08:18:49Z"
    }
  ]
}
```

### 3. Get Command
```text
request: get,args: pipeline_id=a1b2c3d4-e5f6-7890-abcd-ef1234567890
resp=<Response [200]>, trace-id=12345678-1234-1234-1234-123456789abc
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "type": "telemetry",
  "subType": ["endpoint", "email"],
  "description": "My telemetry pipeline",
  "registeredDateTime": "2023-10-17T08:18:49Z"
}
```

### 4. Update Command
```text
request: update, args: pipeline_id=a1b2c3d4-e5f6-7890-abcd-ef1234567890, type=detection, sub_type=None, description=Updated description
resp=<Response [200]>, trace-id=12345678-1234-1234-1234-123456789abc
Status Code: 200, Response Text: {"id":"a1b2c3d4-e5f6-7890-abcd-ef1234567890","type":"detection","description":"Updated description"}, trace-id=12345678-1234-1234-1234-123456789abc
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "type": "detection",
  "description": "Updated description",
  "registeredDateTime": "2023-10-17T08:18:49Z"
}
```

### 5. Delete Command
```text
request: delete, args: pipeline_id_list=['a1b2c3d4-e5f6-7890-abcd-ef1234567890']
resp=<Response [200]>, trace-id=12345678-1234-1234-1234-123456789abc
[
  {
    "status": 200,
    "message": "Pipeline(s) successfully deleted"
  }
]
```

### 6. List-packages Command
```text
request: list-packages, args: pipeline_id=a1b2c3d4-e5f6-7890-abcd-ef1234567890, start_datetime=2023-10-01T00:00:00Z, end_datetime=2023-10-01T23:59:59Z, top=500, 
resp=<Response [200]>, trace-id=12345678-1234-1234-1234-123456789abc
{
  "items": [
    {
      "id": "20231001-package-id-123",
      "createdDateTime": "2023-10-01T12:30:45Z"
    },
    {
      "id": "20231001-package-id-456",
      "createdDateTime": "2023-10-01T14:15:30Z"
    }
  ],
  "totalCount": 2,
  "requestedDateTime": "2023-10-17T09:11:57Z"
}
```

### 7. Get-package Command
```text
request: get-package, args: pipeline_id=a1b2c3d4-e5f6-7890-abcd-ef1234567890, package_id=20231001-package-id-123, output=/path/to/output.gz
resp=<Response [200]>, trace-id=12345678-1234-1234-1234-123456789abc
```
*Package content is written to the specified output file*

### 8. Continuous-get-packages Command
```text
start capturing..., next request is around:  2023-10-17T12:03:00Z
resp=<Response [200]>, trace-id=12345678-1234-1234-1234-123456789abc
- saved package: 20231017-package-id-789
- saved package: 20231017-package-id-abc
captured packages until: 2023-10-17T12:03:00Z
  - captured package count: 2
  - bundle path: /output/bundle-2023-10-17T12:00:00Z-2023-10-17T12:03:00Z.gz
  - next request is around:  2023-10-17T12:06:00Z
^Cstop capturing
Stop capturing
```