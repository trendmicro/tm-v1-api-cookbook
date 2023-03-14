# Cookbook: "Perform IoC Sweeping from a CSV or STIX (2.x) file"

## System Requirements

- Python 3.7 or later

## Environment Setup

1. Install `pipenv`.
    ```text
    $ pip install pipenv
    ```
2. Create a virtual environment for installing packages and managing dependencies.
    ```text
    $ pipenv install
    ```
3. Modify the settings in `ioc_intelligence_sweeping.py` to match your environment.
    ```python
    V1_TOKEN = os.environ.get('TMV1_TOKEN', '')
    V1_URL = os.environ.get('TMV1_URL', 'https://api.xdr.trendmicro.com')
    V1_UA = os.environ.get('TMV1_UA', f'Trend Vision One API Cookbook ({os.path.basename(__file__)})')
    V1_WAIT_TASK_INTERVAL = int(os.environ.get('TMV1_WAIT_TASK_INTERVAL', 10))
    V1_WAIT_TASK_RETRY = int(os.environ.get('TMV1_WAIT_TASK_RETRY', 12))
    ```
    Alternatively, you can set these as environment variables or script command parameters.

## Sample Script

1. Activate the virtual environment associated with your project.
    ```text
    $ pipenv shell
    ```
2. Run a sample script with parameters.  
    The following script imports "stix.json" as "stix.json", and sets up "stix.json"'s file type to STIX.
    ```text
    (python) $ python intelligence_sweeping.py -n stix.json stix < stix.json
    (python) $ python intelligence_sweeping.py stix stix.json
    ```
    The following script imports "reports.csv" as "reports.csv", sets up "reports.csv"'s file type to CSV, and creates the report "sample_report".
    ```text
    (python) $ python intelligence_sweeping.py -r sample_report -n reports.csv csv < reports.csv
    (python) $ python intelligence_sweeping.py -r sample_report csv reports.csv
    ```


## Expected Results

The following sample code imports IoCs from STIX or CSV file into a custom intelligence report, starts a sweeping task, downloads any matched indicators to "intelligence\_report\_sweep_\<report\_id\>.json", and writes the information to `stdout`.

```text
Tasks running: {number}; Waiting interval (seconds): {interval}; Number of intervals: {interval_count}.

The sweeping task based on custom intelligence report "<report_id>" has matched indicators. Sweeping result saved in "intelligence_report_sweep_<report_id>.json".
The sweeping task based on custom intelligence report "<report_id>" does not have any matched indicators.
```
