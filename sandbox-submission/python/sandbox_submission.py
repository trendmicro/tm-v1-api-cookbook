import os
import sys
import base64
import time
import argparse

import requests

# Setting variables
V1_TOKEN = os.environ.get('TMV1_TOKEN', '')
# Specify the correct domain name for your region in V1_URL
#   ref: https://automation.trendmicro.com/xdr/Guides/Regional-Domains
V1_URL = os.environ.get('TMV1_URL', 'https://api.xdr.trendmicro.com')
# This value is used for User-Agent header in API requests. So you can
# customize this value to describe your company name, integration tool name,
# and so on as you like.
#   default: "Trend Vision One API Cookbook ({script_name})"
V1_UA = os.environ.get('TMV1_UA', 'Trend Vision One API Cookbook '
                       f'({os.path.basename(__file__)})')
V1_WAIT_TASK_INTERVAL = int(os.environ.get('TMV1_WAIT_TASK_INTERVAL', 10))
V1_WAIT_TASK_RETRY = int(os.environ.get('TMV1_WAIT_TASK_RETRY', 12))
V1_ANALYZE_INTERVAL = int(os.environ.get('TMV1_ANALYZE_INTERVAL', 300))
V1_ANALYZE_RETRY = int(os.environ.get('TMV1_ANALYZE_RETRY', 3))


def is_container(v):
    try:
        if isinstance(v, (str, bytes)):
            return False
        iter(v)
    except TypeError:
        return False
    return True


def get_multiple_request(name, args):
    r = []
    if is_container(args):
        r.extend({name: v} for v in args)
    elif isinstance(args, str):
        r.append({name: args})
    return r


def get_filter_arg(name, value, enclose="'", equal='eq'):
    if not is_container(value):
        value = [value]
    param = ' or '.join(f'{name} {equal} {enclose}{x}{enclose}' for x in value)
    if 1 < len(value):
        param = '('+param+')'
    return param


class TmV1Client:
    base_url_default = V1_URL
    WB_STATUS_NEW = 'New'
    WB_STATUS_IN_PROGRESS = 'In Progress'

    def __init__(self, token, base_url=None):
        if not token:
            raise ValueError('Authentication token missing')
        self.token = token
        self.base_url = base_url or TmV1Client.base_url_default

    def make_headers(self, **kwargs):
        headers = {}
        use_token = kwargs.pop('use_token', True)
        if use_token:
            headers['Authorization'] = 'Bearer ' + self.token
        if 'files' not in kwargs:
            headers['Content-Type'] = 'application/json;charset=utf-8'
        headers['User-Agent'] = V1_UA
        return headers

    def get(self, url_or_path, use_token=True, **kwargs):
        kwargs.setdefault('headers', {}).update(
            self.make_headers(use_token=use_token)
        )
        url = (self.base_url + url_or_path if url_or_path.startswith('/') else
               url_or_path)
        r = requests.get(url, **kwargs)
        if 200 == r.status_code:
            if 'application/json' in r.headers.get('Content-Type', ''):
                return r.json()
            return r.content
        raise RuntimeError(f'Request unsuccessful (GET {url_or_path}):'
                           f' {r.status_code} {r.text}')

    def post(self, path, **kwargs):
        kwargs.setdefault('headers', {}).update(self.make_headers(**kwargs))
        r = requests.post(self.base_url + path, **kwargs)
        if ((r.status_code in [200, 201, 202, 207]) and
                ('application/json' in r.headers.get('Content-Type', ''))):
            return r.status_code, r.headers, r.json()
        elif r.status_code in [201, 202]:
            return r.status_code, r.headers, r.content
        raise RuntimeError(f'Request unsuccessful (POST {path}):'
                           f' {r.status_code} {r.headers} {r.text}')

    def get_items(self, path, **kwargs):
        items = []
        next_link = None
        while True:
            if next_link is None:
                r = self.get(path, **kwargs)
            else:
                r = self.get(next_link,
                             **{'headers': kwargs.get('headers', {})})
            items.extend(r['items'])
            if 'nextLink' not in r:
                break
            next_link = r['nextLink']
        return items

    def get_from_post_response(self, status_code, headers, body):
        if (201 == status_code) and ('Location' in headers):
            return self.get(headers['Location'])
        if (202 == status_code) and ('Operation-Location' in headers):
            return self.get(headers['Operation-Location'])
        # response APIs return 'Operation-Location' for duplicated tasks
        if (400 == status_code) and ('Operation-Location' in headers):
            if isinstance(body, dict):
                error = body.get('error', {})
                code = error.get('code', '')
                message = error.get('message', '')
                if ('TaskError' == code) and ('Task duplication.' == message):
                    return self.get(headers['Operation-Location'])

    def post_multiple(self, path, **kwargs):
        json_ = kwargs.get('json')
        if (json_ is not None) and (not isinstance(json_, list)):
            raise ValueError('json is not list.')
        (_, _, r) = self.post(path, **kwargs)
        if json_ is None:
            json_ = [None] * len(r)
        if len(json_) == len(r):
            return [*zip(json_, r)]
        raise ValueError('The request and the response do not have the same '
                         'length')

    def get_from_post_multiple_response(self, response):
        items = [None] * len(response)
        for i, (_, r) in enumerate(response):
            headers = dict((h['name'], h['value'])
                           for h in r.get('headers', []))
            body = r.get('body')
            items[i] = self.get_from_post_response(r['status'], headers, body)
        return items

    def get_sandbox_sumbission_usage(self):
        return self.get('/v3.0/sandbox/submissionUsage')

    def analyze_file(self, file_obj, file_name, archive_password=None,
                     document_password=None):
        data = {}
        if archive_password is not None:
            data['archivePassword'] = base64.b64encode(
                archive_password.encode()
            ).decode()
        if document_password is not None:
            data['documentPassword'] = base64.b64encode(
                document_password.encode()
            ).decode()
        if not file_name:
            file_name = file_obj.name
        files = {'file': (file_name, file_obj, 'application/octet-stream')}
        return self.post('/v3.0/sandbox/files/analyze', data=data, files=files)

    def analyze_url(self, url):
        request = get_multiple_request('url', url)
        return self.post_multiple('/v3.0/sandbox/urls/analyze', json=request)

    def get_sandbox_tasks(self, ids=None):
        params = {}
        if ids is not None:
            params['filter'] = get_filter_arg('id', ids)
        return self.get_items('/v3.0/sandbox/tasks', params=params)

    def get_sandbox_analysis_result(self, analysis_result_id):
        return self.get(f'/v3.0/sandbox/analysisResults/{analysis_result_id}')

    def get_sandbox_analysis_report(self, analysis_result_id):
        return self.get(
            f'/v3.0/sandbox/analysisResults/{analysis_result_id}/report'
        )


def wait_sandbox_tasks(v1, tasks):
    count = 0
    while True:
        running_task_indexes = [
            i for i, t in enumerate(tasks)
            if t and ('running' == t['status'])
        ]
        if not running_task_indexes:
            break
        if not (count < V1_WAIT_TASK_RETRY):
            break
        count += 1
        print((f'Tasks running: {len(running_task_indexes)}; '
               f'Waiting interval (seconds): {V1_WAIT_TASK_INTERVAL}; '
               f'Number of intervals: {count}.'))
        time.sleep(V1_WAIT_TASK_INTERVAL)
        response = v1.get_sandbox_tasks([tasks[i]['id']
                                         for i in running_task_indexes])
        for i, r in enumerate(response):
            tasks[running_task_indexes[i]].update(r)
    finished = not running_task_indexes
    if not finished:
        print('Tasks not finished')
    return finished


def fetch_analysis_result(v1, task):
    if 'succeeded' == task['status']:
        if 'resourceLocation' in task:
            return v1.get(task['resourceLocation'])


def fetch_analysis_report(v1, result, file_name_prefix):
    id_ = result['id']
    if result['riskLevel'] in ['high', 'medium', 'low']:
        response = v1.get_sandbox_analysis_report(id_)
        dest_name = f'{file_name_prefix}_{id_}.pdf'
        with open(dest_name, 'wb') as f:
            f.write(response)
        return dest_name


def need_retry(task):
    if 'error' in task:
        return 'InternalServerError' == task['error']['code']


def analyze_file(v1, infile, name, archive_password, document_password):
    file_name_prefix = 'sandbox_analysis_file'
    count = 0
    while True:
        status_code, headers, response = v1.analyze_file(
            infile, name, archive_password, document_password
        )
        task = v1.get_from_post_response(status_code, headers, response)
        if task is None:
            return (name, response, None, None, None)
        wait_sandbox_tasks(v1, [task])
        result = fetch_analysis_result(v1, task)
        if result is None:
            if not (need_retry(task) and (count < V1_ANALYZE_RETRY)):
                return (name, response, task, None, None)
            count += 1
            time.sleep(V1_ANALYZE_INTERVAL)
            continue
        file_name = fetch_analysis_report(v1, result, file_name_prefix)
        if file_name is None:
            return (name, response, task, result, None)
        return (name, response, task, result, file_name)


def analyze_urls(v1, url):
    r = []
    file_name_prefix = 'sandbox_analysis_url'
    count = 0
    while True:
        response = v1.analyze_url(url)
        tasks = v1.get_from_post_multiple_response(response)
        wait_sandbox_tasks(v1, tasks)

        url = []
        for (req, res), task in zip(response, tasks):
            name = req['url']
            if task is None:
                r.append((name, res, None, None, None))
                continue
            result = fetch_analysis_result(v1, task)
            if result is None:
                if need_retry(task):
                    # set to url to be retried
                    url.append(req['url'])
                else:
                    r.append((name, res, task, None, None))
                continue
            dest_name = fetch_analysis_report(v1, result, file_name_prefix)
            if dest_name is None:
                r.append((name, res, task, result, None))
                continue
            r.append((name, res, task, result, dest_name))
        if not url:
            break
        if not (count < V1_ANALYZE_RETRY):
            break
        count += 1
        time.sleep(V1_ANALYZE_INTERVAL)
    return r


def main(v1_token, v1_url, infile=None, name=None, archive_password=None,
         document_password=None, url=None):
    v1 = TmV1Client(v1_token, v1_url)

    r = v1.get_sandbox_sumbission_usage()
    remaining_count = r['submissionRemainingCount']
    if not (0 < remaining_count):
        raise RuntimeError('No submissions available in the daily reserve')
    print(f'Submissions available: {remaining_count}')

    results = []
    if infile is not None:
        if infile.isatty():
            raise ValueError('sys.stdin has no input')
        if not name:
            if sys.stdin.name == infile.name:
                raise ValueError('file_name must be specified for '
                                 f'{infile.name}')
            name = os.path.basename(infile.name)
        print(f'Submitting 1 file...')
        r = analyze_file(v1, infile, name, archive_password,
                         document_password)
        results.append(r)
    elif url is not None:
        if not url:
            raise ValueError('No URL specified')
        url_count = len(url)
        print(f'Submitting {url_count} URLs...')
        r = analyze_urls(v1, url)
        results.extend(r)

    print('')
    for (name, res, task, result, file_name) in results:
        if task is None:
            error = res.get('body', {}).get('error', '')
            print(f'Unable to start analyzing "{name}" task. '
                  f'Error code: {error}')
            continue
        status = task['status']
        if not result:
            if 'running' == status:
                print(f'The status of the analyzing "{name}" task is '
                      f'"{status}". Task ID: {task["id"]}')
            elif 'failed' == status:
                error = task.get('error', {})
                error_code = error.get('code', '')
                if 'Unsupported' == error_code:
                    print(f'Unable to analyze "{name}". Object not supported.')
                else:
                    print(f'The status of the analyzing "{name}" task is '
                          f'"{status}". Error code: {error}')
            continue
        risk_level = result['riskLevel']
        if not file_name:
            print(f'Analyzing: "{name}"; Task status: {status}; '
                  f'Risk level: {risk_level}.')
            continue
        print(f'Analyzing: "{name}"; Task status: {status}; Risk level: '
              f'{risk_level}; Analysis report saved to: {file_name}.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=('Submit files or URLs to the sandbox and retrieve the'
                     ' analysis results if there are submissions available in'
                     " the daily reserve. When 'Risk level' is equal or"
                     " higher to 'low', a file (\"sandbox_analysis_<file/url>"
                     '_<analysis_result_id>.pdf") with the analysis results'
                     ' is downloaded.'),
        epilog="Refer to examples of the operations 'file' and 'url'.")
    parser.add_argument(
        '-t', '--v1-token', default=V1_TOKEN,
        help='Authentication token of your Trend Vision One user account')
    parser.add_argument(
        '-u', '--v1-url', default=TmV1Client.base_url_default,
        help=('URL of the Trend Vision One server for your region.'
              f' The default value is "{TmV1Client.base_url_default}"'))
    subparsers = parser.add_subparsers(help='')
    file_parser = subparsers.add_parser(
        'file', help='Submit file to the sandbox.',
        epilog=(f'Example: python {os.path.basename(__file__)} file'
                f' /path/to/file')
    )
    file_parser.add_argument(
        'infile', nargs='?',
        type=argparse.FileType('rb'), default=sys.stdin.buffer,
        help='File to be sent to the sandbox. The default value is stdin.')
    file_parser.add_argument(
        '-n', '--name',
        help=('Name of file to be sent to sandbox. If no value is specified,'
              " the last element of the file path path passed to 'infile' is"
              " used. When the value of 'infile' is stdin, you must specify"
              ' a name.'))
    file_parser.add_argument(
        '-p', '--archive-password',
        help='Password used to decrypt the submitted archive.')
    file_parser.add_argument(
        '-d', '--document-password',
        help='Password used to decrypt the submitted file.')
    url_parser = subparsers.add_parser(
        'url', help='Submit URLs to the sandbox.',
        epilog=(f'Example: python {os.path.basename(__file__)} url'
                ' https://www.trendmicro.com')
    )
    url_parser.add_argument(
        'url', nargs='*',
        help=('URL to be submitted. A number of URLs can be specified.'))
    main(**vars(parser.parse_args()))
