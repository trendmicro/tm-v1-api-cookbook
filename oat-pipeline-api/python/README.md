# Cookbook: OAT Pipeline API
This sample demonstrates how to use the Trend Vision One API to manage Observed Attack Technique (OAT) Data Pipelines, retrieve packages of OAT data, and continuously capture OAT events.

## Requirements

- Python 3.9 or higher


## Installation

1. Clone this repository or download the script.
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

The script provides a command-line interface for interacting with the OAT Data Pipeline API.

### Basic Command Format

```bash
python oat_pipeline.py -u <API_ENDPOINT_URL> -f <JWT_TOKEN_FILE> <COMMAND> [OPTIONS]
```

### Authentication

- `-u, --url`: The base URL for the API endpoint
- `-f, --token-path`: Path to a file containing your JWT token

### Available Commands

#### Register a Data Pipeline

```bash
python oat_pipeline.py -u <URL> -f <TOKEN_FILE> register -r <RISK_LEVELS> -d <DESCRIPTION>
```

Options:
- `-r, --risk-levels`: Risk levels to register (e.g., `'["critical", "high"]'`)
- `-d, --description`: Optional description for the data pipeline

#### Get Active Data Pipelines

```bash
python oat_pipeline.py -u <URL> -f <TOKEN_FILE> list
```

#### Modify Data Pipeline Settings

```bash
python oat_pipeline.py -u <URL> -f <TOKEN_FILE> modify -p <PIPELINE_ID> -r <RISK_LEVELS> -d <DESCRIPTION> -i <IF_MATCH> [--has-detail]
```

Options:
- `-p, --pipeline-id`: ID of the pipeline to modify
- `-r, --risk-levels`: Updated risk levels
- `-d, --description`: Updated description
- `-i, --if-match`: ETag for concurrency control
- `--has-detail`: Whether to include details (flag)


#### Get Data Pipeline Settings

```bash
python oat_pipeline.py -u <URL> -f <TOKEN_FILE> get -p <PIPELINE_ID>
```

Options:
- `-p, --pipeline-id`: ID of the pipeline to retrieve

Result:
```json
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


#### Unregister From Data Pipeline

```bash
python oat_pipeline.py -u <URL> -f <TOKEN_FILE> delete -p <PIPELINE_ID> -p <PIPELINE_ID> ...
```

Options:
- `-p, --pipeline-id`: ID(s) of the pipeline(s) to delete (can be specified multiple times)

Result
```json
{
  "Responses": [
    {
      "status": 204
    },
  ]
}
```

#### List Data Pipeline Packages

```bash
python oat_pipeline.py -u <URL> -f <TOKEN_FILE> list-packages -p <PIPELINE_ID> -s <START_DATETIME> -e <END_DATETIME>] -t <TOP> -l <NEXT_LINK>
```

Options:
- `-p, --pipeline-id`: ID of the pipeline
- `-s, --start-datetime`: Start time for filtering (format: `2022-09-15T14:10:00Z`)
- `-e, --end-datetime`: End time for filtering (format: `2022-09-15T14:30:00Z`)
- `-t, --top`: Maximum number of records to return (default: 500)
- `-l, --next-link`: Next link from previous response for pagination

Result:
```json
{
  "items": [
    {
      "id": "2022092911-91664a49-5284-400c-8e81-f2e8a8ed4322",
      "createdDateTime": "2023-10-12T02:15:23Z"
    },
  ...(truncated)
    {
      "id": "2022092914-0d0d24c0-f1b6-47a6-9f7c-18c2122d5152",
      "createdDateTime": "2023-10-13T08:21:12Z"
    }
  ],
  "totalCount": 274,
  "count": 50,
  "requestedDateTime": "2023-10-17T09:11:57Z",
  "nextLink": "https://https://api.xdr.trendmicro.com/beta/xdr/oat/dataPipelines/2ba69db9-5111-40f6-9a39-653e1031ec56/packages?startDateTime=2023-10-12T02:00:00Z&endDateTime=2023-10-17T02:59:59Z&top=50&pageToken=1697185272.500556",
  "latestPackageCreatedDateTime": "2023-10-13T08:21:12Z"
}

```


#### Get Observed Attack Techniques Event Package

```bash
python oat_pipeline.py -u <URL> -f <TOKEN_FILE> get-package -p <PIPELINE_ID> -k <PACKAGE_ID> -o <OUTPUT_PATH>
```

Options:
- `-p, --pipeline-id`: ID of the pipeline
- `-k, --package-id`: ID of the package to retrieve
- `-o, --output`: Path to save the package

#### Get Observed Attack Techniques Event Package
```bash
python [URL] -u <URL> -f <TOKEN_FILE> get-package -p <PIPELINE_ID> -k <PACKAGE_ID> -o <OUTPUT_PATH>
```
Options:
- `-p, --pipeline-id`: ID of the pipeline
- `-k, --package-id`: ID of the package to retrieve
- `-o, --output`: Path to save the package
- Provide a link to a guidance

#### Continuous Package Retrieval

```bash
python oat_pipeline.py -u <URL> -f <TOKEN_FILE> continuous-get-packages -p <PIPELINE_ID> [-v <INTERVAL>] [-t <TOP>] -o <OUTPUT_DIR>
```

Options:
- `-p, --pipeline-id`: ID of the pipeline
- `-v, --interval`: Time interval in seconds (default: 180)
- `-t, --top`: Maximum number of records per request (default: 500)
- `-o, --output-dir`: Directory to save packages

Result:
```bash
start capturing..., next request is around:  2022-09-29T18:55:00Z
  - next request is around:  2022-09-29T18:58:00Z
  - next request is around:  2022-09-29T19:01:00Z
  - next request is around:  2022-09-29T19:04:00Z
^Cstop capturing

```

## Logging

The script logs all operations to a log file named after the script. The log includes timestamps, log levels, function names, line numbers, and messages.

## Error Handling

The script includes retry logic for certain HTTP status codes (429, 502, 504) and will raise exceptions for other HTTP errors.