# Cookbook: Datalake Pipeline API 
This sample demonstrates how to use the Trend Vision One API to manage Data Pipelines, retrieve data packages, and continuously capture data events.

## Requirements

- Python 3.9 or higher

## Installation

1. Clone this repository or download the script.
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

The script provides a command-line interface for interacting with the Data Pipeline API.

### Basic Command Format

```bash
python datalake_pipeline.py -u <API_ENDPOINT_URL> -f <JWT_TOKEN_FILE> <COMMAND> [OPTIONS]
```

### Authentication

- `-u, --url`: The base URL for the API endpoint
- `-f, --token-path`: Path to a file containing your JWT token

### Available Commands

#### Bind a data type to a pipeline

```bash
python datalake_pipeline.py -u <URL> -f <TOKEN_FILE> register -t <TYPE> -d <DESCRIPTION> [-s <SUB_TYPE> ...]
```

Options:
- `-t, --type`: Type of data for the pipeline (telemetry or detection)
- `-d, --description`: Optional description for the data pipeline
- `-s, --sub-type`: Subtypes for telemetry data (can specify multiple)

#### Get bound data pipelines

```bash
python datalake_pipeline.py -u <URL> -f <TOKEN_FILE> list
```

#### Get pipeline information

```bash
python datalake_pipeline.py -u <URL> -f <TOKEN_FILE> get -p <PIPELINE_ID>
```

Options:
- `-p, --pipeline-id`: ID of the pipeline to retrieve

#### Update Pipeline Settings

```bash
python datalake_pipeline.py -u <URL> -f <TOKEN_FILE> update -p <PIPELINE_ID> [-t <TYPE>] [-s <SUB_TYPE> ...] [-d <DESCRIPTION>]
```

Options:
- `-p, --pipeline-id`: ID of the pipeline to update
- `-t, --type`: Updated data type (telemetry or detection)
- `-s, --sub-type`: Updated subtypes (can specify multiple)
- `-d, --description`: Updated description

#### Unbind Data Type from Pipeline

```bash
python datalake_pipeline.py -u <URL> -f <TOKEN_FILE> delete -p <PIPELINE_ID> [-p <PIPELINE_ID> ...]
```

Options:
- `-p, --pipeline-id`: ID(s) of the pipeline(s) to delete (can specify multiple)

#### List Available Packages

```bash
python datalake_pipeline.py -u <URL> -f <TOKEN_FILE> list-packages -p <PIPELINE_ID> -s <START_DATETIME> -e <END_DATETIME> [-t <TOP>] [-l <NEXT_LINK>]
```

Options:
- `-p, --pipeline-id`: ID of the pipeline
- `-s, --start-datetime`: Start time for filtering (format: `2022-09-15T14:10:00Z`)
- `-e, --end-datetime`: End time for filtering (format: `2022-09-15T14:30:00Z`)
- `-t, --top`: Maximum number of records to return (default: 500)
- `-l, --next-link`: Next link from previous response for pagination

#### Get Package

```bash
python datalake_pipeline.py -u <URL> -f <TOKEN_FILE> get-package -p <PIPELINE_ID> -k <PACKAGE_ID> -o <OUTPUT_PATH>
```

Options:
- `-p, --pipeline-id`: ID of the pipeline
- `-k, --package-id`: ID of the package to retrieve
- `-o, --output`: Path to save the package

#### Continuous Package Retrieval

```bash
python datalake_pipeline.py -u <URL> -f <TOKEN_FILE> continuous-get-packages -p <PIPELINE_ID> [-v <INTERVAL>] [-t <TOP>] -o <OUTPUT_DIR>
```

Options:
- `-p, --pipeline-id`: ID of the pipeline
- `-v, --interval`: Time interval in seconds (default: 180)
- `-t, --top`: Maximum number of records per request (default: 500)
- `-o, --output-dir`: Directory to save packages

## Logging

The script logs all operations to a log file named after the script. The log includes timestamps, log levels, function names, line numbers, and messages.

## Error Handling

The script includes retry logic for certain HTTP status codes (429, 502, 504) and will attempt to retry GET requests up to 5 times with exponential backoff.