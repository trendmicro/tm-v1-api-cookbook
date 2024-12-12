# Cookbook: "Create custom reports in XLSX or PPTX format using data from the Security Posture API"

## System Requirements

- Python 3.9 or later

## Environment Setup

1. Install `pipenv`.
    ```text
    $ pip install pipenv
    ```
2. Create a virtual environment for installing packages and managing dependencies.
    ```text
    $ pipenv install
    ```
3. Modify the settings in `documentation-security-posture.py` to match your environment.
    ```python
    V1_TOKEN = os.environ.get('TMV1_TOKEN', '')
    V1_URL = os.environ.get('TMV1_URL', 'https://api.xdr.trendmicro.com')
    V1_UA = os.environ.get('TMV1_UA', f'Trend Vision One API Cookbook ({os.path.basename(__file__)})')
    V1_XLSX_FILENAME = os.environ.get('TMV1_XLSX_FILENAME', 'security_posture.xlsx')
    V1_PPTX_FILENAME = os.environ.get('TMV1_PPTX_FILENAME', 'security_posture.pptx')
    V1_YAML_FILENAME = os.environ.get('TMV1_YAML_FILENAME', 'security_posture.yaml')
    ```
    Alternatively, you can set these as environment variables or script command parameters.


## Sample Script

1. Activate the virtual environment associated with your project.
    ```text
    $ pipenv shell
    ```
2. Run the sample script using any of the available parameters.
    - Get information about your current security posture and create XLSX file with the information.
    ```text
    (python) $ python documentation_security_posture.py export -s <path_to_file>
    ```
    - Generate a report in PPTX format based on the information from the generated XLSX report.
    ```text
    (python) $ python documentation_security_posture.py report -s <path_to_Excel_file> -p <path_to_PowerPoint_file>
    ```

## Expected Results
### Custom report file in XLSX format
The sample script generates an XLSX file (`security_posture.xlsx`) that includes various security metrics, such as:

- General
- Risk Index
- Risk Category Level
- High Impact Risk Events Threat Detection
- High Impact Risk Events Security Configuration
- High Impact Risk Events System Configuration
- High Impact Risk Events Vulnerability Detection
- High Impact Risk Events Anomaly Detection
- High Impact Risk Events Account Compromise
- High Impact Risk Events Cloud App Activity
- High Impact Risk Events XDR Detection
- Vulnerability Assessment Coverage Rate
- CVE Management Metrics Count
- CVE Management Metrics Average Unpatched Days
- CVE Management Metrics Density
- CVE Management Metrics Vulnerable Endpoint Rate
- CVE Management Metrics Legacy OS Endpoint Count
- CVE Management Metrics Mttp Days
- Exposure Status Cloud Asset Misconfiguration
- Exposure Status Unexpected Internet Facing Interface
- Exposure Status Insecure Host Connection
- Exposure Status Domain Account Misconfiguration
- Exposure Status
- Security Configuration Status Endpoint Agent
- Security Configuration Status Endpoint Agent Version
- Security Configuration Status Endpoint Agent Feature Apex One Adoption Rate
- Security Configuration Status Endpoint Agent Feature Apex One Saas Adoption Rate
- Security Configuration Status Endpoint Agent Feature Apex One On Premises Adoption Rate
- Security Configuration Status Endpoint Agent Feature Cloud One Adoption Rate
- Security Configuration Status Endpoint Agent Feature Standard Protection Adoption Rate
- Security Configuration Status Endpoint Agent Feature Deep Software Adoption Rate
- Security Configuration Status Endpoint Agent Feature Workload Adoption Rate
- Security Configuration Status Endpoint Agent Feature Server Workload Protection Adoption Rate
- Security Configuration Status Virtual Patching
- Security Configuration Status Email Sensor Exchange
- Security Configuration Status Email Sensor Gmail
- Security Configuration Status Cloud Apps



Each security metric, except for general, is stored in a separate worksheet inside XLSX workbooks. Every worksheet contains a row with the `createdDateTime` field of the response.

Notes: 
- Due to limitations with Microsoft Excel, worksheet names exceeding 31 characters are automatically shortened. For more information about how the script handles worksheet names, see [Configuration File](#configuration-file).  
- If the new worksheet name exceeds 31 characters, the sample script outputs the following error to `stderr`:
```text
RuntimeError: worksheet name '<worksheet_name>' exceeds the 31 character maximum.
```
- If multiple worksheets have the same name, the script outputs the following error to `stderr`:
```text
RuntimeError: worksheet '<worksheet_name>' already exists.
```
- In cases where the data structure of the response is not supported, the script outputs the following error to `stderr`:
```text
ValueError: Data structure not supported.
```

### Custom report file in PPTX format
The sample code can also generate a custom report in PPTX format (`security_posture.pptx`) based on the information from the generated XLSX report (`security_posture.xlsx`).

The PPTX report presents each of the security metrics from the XLSX report in a line chart format, ordered chronologically by date.

Note: In the `Risk Category Level` data source, the line chart values are replaced as follows:
- low - `0`
- medium - `1`
- high - `2`

## Configuration File
To manage worksheet names longer than 31 characters, the sample code uses a configuration file (`security_posture.yaml`).

The following is an example of a configuration file:

```text
worksheet names:
  High Impact Risk Events Threat Detection: HIREs Threat Detection
  High Impact Risk Events Security Configuration: HIREs Security Configuration
  High Impact Risk Events System Configuration: HIREs System Configuration
  High Impact Risk Events Vulnerability Detection: HIREs Vulnerability Detection
  High Impact Risk Events Anomaly Detection: HIREs Anomaly Detection
  High Impact Risk Events Account Compromise: HIREs Account Compromise
  High Impact Risk Events Cloud App Activity: HIREs Cloud App ACTs
  High Impact Risk Events XDR Detection: HIREs XDR Detection
  Vulnerability Assessment Coverage Rate: VA Coverage Rate
  CVE Management Metrics Average Unpatched Days: CVE MM AVG. Unpatched Days
  CVE Management Metrics Vulnerable Endpoint Rate: CVE MM Vulnerable Endpoint Rate
  CVE Management Metrics Legacy OS Endpoint Count: CVE MM Legacy OS Endpoint Count
  CVE Management Metrics Mttp Days: CVE MM Mttp Days
  Exposure Status Cloud Asset Misconfiguration: ES Cloud Asset Misconfiguration
  Exposure Status Unexpected Internet Facing Interface: ES Unexpected INET Facing IF
  Exposure Status Insecure Host Connection: ES Insecure Host Connection
  Exposure Status Domain Account Misconfiguration: ES Domain Acct. Misconfig
  Security Configuration Status Endpoint Agent: SCS EP Agent
  Security Configuration Status Endpoint Agent Version: SCS EP Agent Version
  Security Configuration Status Endpoint Agent Feature Apex One Adoption Rate: SCS EP Agent A1 Adoption Rate
  Security Configuration Status Endpoint Agent Feature Apex One Saas Adoption Rate: SCS EPA A1 Saas Adoption Rate
  Security Configuration Status Endpoint Agent Feature Apex One On Premises Adoption Rate: SCS EPA A1 OnPre Adoption Rate
  Security Configuration Status Endpoint Agent Feature Cloud One Adoption Rate: SCS EP Agent C1 Adoption Rate
  Security Configuration Status Endpoint Agent Feature Standard Protection Adoption Rate: SCS EP Agent SP Adoption Rate
  Security Configuration Status Endpoint Agent Feature Deep Software Adoption Rate: SCS EP Agent DS Adoption Rate
  Security Configuration Status Endpoint Agent Feature Workload Adoption Rate: SCS EPA Workload Adoption Rate
  Security Configuration Status Endpoint Agent Feature Server Workload Protection Adoption Rate: SCS EP Agent SWP Adoption Rate
  Security Configuration Status Virtual Patching: SCS Virtual Patching
  Security Configuration Status Email Sensor Exchange: SCS Email Sensor Exchange
  Security Configuration Status Email Sensor Gmail: SCS Email Sensor Gmail
  Security Configuration Status Cloud Apps: SCS Cloud Apps
```
