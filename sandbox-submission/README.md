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
- [Get daily reserve](https://portal.xdr.trendmicro.com/index.html#/admin/automation_center?goto=api&from=v3.0&tag=tag%2FSandbox-Analysis%2Fpaths%2F~1v3.0~1sandbox~1submissionUsage%2Fget)
- [Submit file to sandbox](https://portal.xdr.trendmicro.com/index.html#/admin/automation_center?goto=api&from=v3.0&tag=tag%2FSandbox-Analysis%2Fpaths%2F~1v3.0~1sandbox~1files~1analyze%2Fpost)
- [Submit URLs to sandbox](https://portal.xdr.trendmicro.com/index.html#/admin/automation_center?goto=api&from=v3.0&tag=tag%2FSandbox-Analysis%2Fpaths%2F~1v3.0~1sandbox~1urls~1analyze%2Fpost)
- [Get submission status](https://portal.xdr.trendmicro.com/index.html#/admin/automation_center?goto=api&from=v3.0&tag=tag%2FSandbox-Analysis%2Fpaths%2F~1v3.0~1sandbox~1tasks~1%7Bid%7D%2Fget)
- [Get analysis results](https://portal.xdr.trendmicro.com/index.html#/admin/automation_center?goto=api&from=v3.0&tag=tag%2FSandbox-Analysis%2Fpaths%2F~1v3.0~1sandbox~1analysisResults~1%7Bid%7D%2Fget)
- [Download analysis results](https://portal.xdr.trendmicro.com/index.html#/admin/automation_center?goto=api&from=v3.0&tag=tag%2FSandbox-Analysis%2Fpaths%2F~1v3.0~1sandbox~1analysisResults~1%7Bid%7D~1report%2Fget)
- [Download Investigation Package](https://portal.xdr.trendmicro.com/index.html#/admin/automation_center?goto=api&from=v3.0&tag=tag%2FSandbox-Analysis%2Fpaths%2F~1v3.0~1sandbox~1analysisResults~1%7Bid%7D~1investigationPackage%2Fget)

## Required products
- None required

## Sample code
- [Python](python/)
