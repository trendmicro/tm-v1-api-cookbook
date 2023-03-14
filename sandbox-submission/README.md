# Submit object to Sandbox Analysis
This task submits files or URLs to the sandbox and retrieves the analysis results if there are submissions available in the daily reserve. If the risk level of the submitted objects is is equal or higher to 'low', this task also downloads an analysis report.
```mermaid
graph LR;
s(Start)-->check_available_count{Are there submissions available<br> in the daily reserve?};
check_available_count--Yes-->check_submission_type{Submission<br>type};
check_available_count--No-->e(End);
check_submission_type--File-->action_submit_file[Submit file];
check_submission_type--URL-->action_submit_url[Submit URL];
action_submit_file-->action_wait_complete[Wait for<br>analysis completion];
action_submit_url-->action_wait_complete;
action_wait_complete-->check_task_status{Task<br>status};
check_task_status--Successful-->action_fetch_result[Get<br>analysis result];
check_task_status--Unsuccessful-->check_error_code{Error<br>code};
check_error_code--Unsupported-->e;
check_error_code--Internal<br>Server Error-->check_submission_type;
action_fetch_result-->check_risk_level{Risk<br>level};
check_risk_level--High / Medium / Low-->action_download_report[Download<br>analysis report];
check_risk_level--No risk-->e;
action_download_report-->e;
```

## Related APIs
- [Get daily reserve](https://automation.trendmicro.com/xdr/api-v3#tag/Sandbox-Analysis/paths/~1v3.0~1sandbox~1submissionUsage/get)
- [Submit file to sandbox](https://automation.trendmicro.com/xdr/api-v3#tag/Sandbox-Analysis/paths/~1v3.0~1sandbox~1files~1analyze/post)
- [Submit URLs to sandbox](https://automation.trendmicro.com/xdr/api-v3#tag/Sandbox-Analysis/paths/~1v3.0~1sandbox~1urls~1analyze/post)
- [Get submission status](https://automation.trendmicro.com/xdr/api-v3#tag/Sandbox-Analysis/paths/~1v3.0~1sandbox~1tasks~1{id}/get)
- [Get analysis results](https://automation.trendmicro.com/xdr/api-v3#tag/Sandbox-Analysis/paths/~1v3.0~1sandbox~1analysisResults~1{id}/get)
- [Download analysis results](https://automation.trendmicro.com/xdr/api-v3#tag/Sandbox-Analysis/paths/~1v3.0~1sandbox~1analysisResults~1{id}~1report/get)
- [Download Investigation Package](https://automation.trendmicro.com/xdr/api-v3#tag/Sandbox-Analysis/paths/~1v3.0~1sandbox~1analysisResults~1{id}~1investigationPackage/get)

## Required products
- None required

## Sample code
- [Python](python/)
