# Cookbook: "Submit object to Sandbox Analysis"

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
3. Modify the settings in `sandbox-submission.py` to match your environment.
    ```python
    V1_TOKEN = os.environ.get('TMV1_TOKEN', '')
    V1_URL = os.environ.get('TMV1_URL', 'https://api.xdr.trendmicro.com')
    V1_UA = os.environ.get('TMV1_UA', f'Trend Micro Vision One API Cookbook ({os.path.basename(__file__)})')
    V1_WAIT_TASK_INTERVAL = int(os.environ.get('TMV1_WAIT_TASK_INTERVAL', 10))
    V1_WAIT_TASK_RETRY = int(os.environ.get('TMV1_WAIT_TASK_RETRY', 12))
    V1_ANALYZE_INTERVAL = int(os.environ.get('TMV1_ANALYZE_INTERVAL', 300))
    V1_ANALYZE_RETRY = int(os.environ.get('TMV1_ANALYZE_RETRY', 3))
    ```
    Alternatively, you can set these as environment variables or script command parameters.

## Sample Script

1. Activate the virtual environment associated with your project.
    ```text
    $ pipenv shell
    ```
2. Run a sample script with parameters.  
    The following script submits a password-protected file and the file's password to Sandbox Analysis.
    ```text
    (python) $ sandbox-submission.py file -n <name> -p <archive_password> < <path_to_file>
    (python) $ sandbox-submission.py file -p <archive_password> <path_to_file>
    ```
    The following script submits two URLs to Sandbox Analysis.
    ```text
    (python) $ sandbox-submission.py url <URL1> <URL2>
    ```

## Expected Results

The following sample code writes the submissions available in the daily reserve, how many objects are being sent to Sandbox Analysis, and the analysis results to `stdout`. 

```text
Submissions available: <remaining_submission_count>
Submitting 1 file.../Submitting <url_count> url(s)...
Tasks running: <running_tasks_count>; Waiting interval (seconds): <interval_seconds>; Number of intervals: <retry_count>.

Analyzing: "<file_name>"; Task status: succeeded; Risk level: <risk_level>; Analysis report saved to: "sandbox_analysis_file_<analysis_result_id>.pdf".
Analyzing: "<URL1>"; Task status: succeeded; Risk level: <risk_level>; Analysis report saved to: "sandbox_analysis_url_<analysis_result_id>.pdf".
Analyzing: "<URL2>"; Task status: succeeded; Risk level: <risk_level>.
```
The sample code also downloads an analysis report to "sandbox\_analysis\_<file\/url\>_\<analysis\_result\_id\>.json" if the risk level of the submitted objects is is equal or higher to 'low'.