# Cookbook: Observed Attack Techniques Pipeline API

## System Requirements

- Python 3.9 or later


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

3. Modify the settings in `oat_pipeline_api.py` to match your environment.
```python
V1_TOKEN = os.environ.get('TMV1_TOKEN', '')
V1_URL = os.environ.get('TMV1_URL', 'https://api.xdr.trendmicro.com')
V1_UA = os.environ.get('TMV1_UA', f'Trend Vision One API Cookbook({os.path.basename(__file__)})')
```
## Sample Script
1. The script provides a command-line interface for interacting with the Observed Attack Techniques Pipeline API.

```bash
$ python oat_pipeline_api.py -u <API_ENDPOINT_URL> -f <JWT_TOKEN_FILE> <COMMAND> [OPTIONS]
```

2. Example commands:
The following examples demonstrate all available operations with the Observed Attack Techniques Pipeline API.
```bash
# 1. Register a data pipeline
python oat_pipeline_api.py register '["medium", "high", "critical"]' -d "My OAT pipeline"

# 2. List all data pipelines
python oat_pipeline_api.py list

# 3. Get specific pipeline information
python oat_pipeline_api.py get <PIPELINE_ID>

# 4. Update pipeline settings
python oat_pipeline_api.py update <PIPELINE_ID> '["low", "medium", "high"]' "Updated description" <ETAG_VALUE>

# 5. Delete pipeline(s)
python oat_pipeline_api.py delete <PIPELINE_ID1> <PIPELINE_ID2>

# 6. List available packages from a pipeline
python oat_pipeline_api.py list-packages <PIPELINE_ID> -s 2023-10-01T00:00:00Z -e 2023-10-01T23:59:59Z -t 500

# 7. Get specific package content
python oat_pipeline_api.py get-package <PIPELINE_ID> <PACKAGE_ID> <OUTPUT_FILE_PATH>

# 8. Continuous package retrieval (runs until Ctrl+C)
python oat_pipeline_api.py continuous-get-packages <PIPELINE_ID> <OUTPUT_DIR> -v 180 -t 500 -b 100
```

## Expected Results

The script performs operations based on the command and outputs results to stdout. Additionally, it logs all operations to a log file.

```text
# For get command:
{
  "riskLevels": [
    "medium",
    "low"
  ],
  "hasDetail": false,
  "registeredDateTime": "2023-10-17T08:18:49Z",
  "description": "test"
}
```
```text

# For delete command:
{
  "Responses": [
    {
      "status": 204
    },
  ]
}
```
```text
# For list-packages command:
{
  "items": [
    {
      "id": "2022092911-91664a49-5284-400c-8e81-f2e8a8ed4322",
      "createdDateTime": "2023-10-12T02:15:23Z"
    },
    ...
  ],
  "totalCount": 274,
  "count": 50,
  "requestedDateTime": "2023-10-17T09:11:57Z",
  "nextLink": "https://api.xdr.trendmicro.com/beta/xdr/oat/dataPipelines/2ba69db9-5111-40f6-9a39-653e1031ec56/packages?startDateTime=2023-10-12T02:00:00Z&endDateTime=2023-10-17T02:59:59Z&top=50&pageToken=1697185272.500556",
  "latestPackageCreatedDateTime": "2023-10-13T08:21:12Z"
}
```
```text
# For continuous-get-packages command:
start capturing..., next request is around:  2022-09-29T18:55:00Z
  - next request is around:  2022-09-29T18:58:00Z
  - next request is around:  2022-09-29T19:01:00Z
  - next request is around:  2022-09-29T19:04:00Z
^Cstop capturing
```

The script also includes retry logic for certain HTTP status codes (429, 502, 504) and will raise exceptions for other HTTP errors.