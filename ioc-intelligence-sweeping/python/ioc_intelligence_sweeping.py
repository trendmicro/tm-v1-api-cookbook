import os
import sys
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
#   default: "Trend Micro Vision One API Cookbook ({script_name})"
V1_UA = os.environ.get('TMV1_UA', 'Trend Micro Vision One API Cookbook '
                       f'({os.path.basename(__file__)})')
V1_WAIT_TASK_INTERVAL = int(os.environ.get('TMV1_WAIT_TASK_INTERVAL', 10))
V1_WAIT_TASK_RETRY = int(os.environ.get('TMV1_WAIT_TASK_RETRY', 12))


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
    intelligence_report_content_types = {
        'stix': 'application/stix+json',
        'csv': 'text/csv'
    }

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

    def import_intelligence_report(self, file_obj, file_name, content_type,
                                   report_name=None):
        if content_type == 'stix':
            report_name = report_name or ''
        elif not report_name:
            raise ValueError('report_name must be specified for '
                             f'{content_type}')
        data = {'reportName': report_name}
        if content_type not in self.intelligence_report_content_types:
            raise ValueError('content_type must be'
                             f' {self.intelligence_report_content_types}.')
        t = self.intelligence_report_content_types[content_type]
        if not file_name:
            file_name = file_bytes.name
        files = {'file': (file_name, file_obj, t)}
        return self.post_multiple('/v3.0/threatintel/intelligenceReports',
                                  data=data, files=files)

    def sweep_by_intelligence_reports(self, report_id):
        request = get_multiple_request('id', report_id)
        for r in request:
            r['sweepType'] = 'manual'
        return self.post_multiple(
            '/v3.0/threatintel/intelligenceReports/sweep', json=request
        )

    def get_threatintel_tasks(self, ids=None):
        params = {}
        if ids is not None:
            params['filter'] = get_filter_arg('id', ids)
        return self.get_items('/v3.0/threatintel/tasks', params=params)


def wait_threatintel_tasks(v1, tasks):
    count = 0
    while True:
        running_task_indexes = [
            i for i, t in enumerate(tasks)
            if t and (t['status'] in ['notstarted', 'running'])
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
        response = v1.get_threatintel_tasks([tasks[i]['id']
                                            for i in running_task_indexes])
        for i, r in enumerate(response):
            tasks[running_task_indexes[i]].update(r)
    finished = not running_task_indexes
    return finished


def import_and_sweep(v1, infile, name, content_type, report_name):
    # Import custom intelligence report
    import_response = v1.import_intelligence_report(
        infile, name, content_type, report_name
    )
    reports = v1.get_from_post_multiple_response(import_response)

    # Sweep by imported custom intelligence report
    imported_report_indexes = [i for i, r in enumerate(reports)
                               if r is not None]
    sweep_response = v1.sweep_by_intelligence_reports(
        [reports[i]['id'] for i in imported_report_indexes]
    )
    tasks = v1.get_from_post_multiple_response(sweep_response)
    wait_threatintel_tasks(v1, tasks)

    # Download when speeping is hit
    hit_task_indexes = [i for i, t in enumerate(tasks)
                        if ((t is not None) and
                            ('succeeded' == t['status']) and
                            (t['isHit'] is True))
                        ]
    file_names = []
    for i in hit_task_indexes:
        task = tasks[i]
        report_id = task['reportId']
        file_name = f'intelligence_report_sweep_{report_id}.json'
        response = v1.get(task['resourceLocation'], use_token=False)
        with open(file_name, 'wb') as f:
            f.write(response)
        file_names.append(file_name)

    r = []
    for i, ((_, import_res), report) in enumerate(zip(import_response,
                                                      reports)):
        if i not in imported_report_indexes:
            r.append((import_res, report, None, None, None))
            continue
        j = imported_report_indexes.index(i)
        (_, sweep_res) = sweep_response[j]
        task = tasks[j]
        if task is None:
            r.append((import_res, report, sweep_res, None, None))
            continue
        if j not in hit_task_indexes:
            r.append((import_res, report, sweep_res, task, None))
            continue
        k = hit_task_indexes.index(j)
        r.append((import_res, report, sweep_res, task, file_names[k]))
    return r


def main(v1_token, v1_url, content_type, infile, name, report_name):
    if infile.isatty():
        raise ValueError('sys.stdin has no input')
    if not name:
        if sys.stdin.name == infile.name:
            raise ValueError(f'file_name must be specified for {infile.name}')
        name = os.path.basename(infile.name)

    v1 = TmV1Client(v1_token, v1_url)
    results = import_and_sweep(v1, infile, name, content_type, report_name)

    print('')
    for (import_res, report, sweep_res, task, file_name) in results:
        if report is None:
            error = import_res.get('body', {}).get('error', '')
            print(f'Unable to import report. Error code: {error}')
            continue
        if task is None:
            error = sweep_res.get('body', {}).get('error', '')
            print('Unable to start sweeping task based on custom '
                  f'intelligence report "{report["id"]}". Error code: {error}')
            continue
        status = task['status']
        if not ('succeeded' == status):
            if status in ['notstarted', 'running']:
                print('The status of the sweeping task based on custom '
                      f'intelligence report "{report["id"]}" is '
                      f'"{status}". Task ID: {task["id"]}')
            elif 'failed' == status:
                error = task.get('error', {})
                error_code = error.get('code', '')
                print('The status of the sweeping task based on custom '
                      f'intelligence report "{report["id"]}" is '
                      f'"{status}". Error code: {error}')
            continue
        if not file_name:
            print('The sweeping task based on custom intelligence report '
                  f'"{report["id"]}" does not have any matched indicators. '
                  f'Task status: {status}')
            continue
        print('The sweeping task based on custom intelligence report '
              f'"{report["id"]}" has matched indicators. Results saved in '
              f'"{file_name}". Task status: {status}.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=('Import IoCs from STIX or CSV file into a custom'
                     ' intelligence report, start a sweeping task, and'
                     ' download a file ("intelligence_report_sweep_'
                     '<report_id>.json") with the matched indicators.'),
        epilog=(f'Example: python {os.path.basename(__file__)} '
                '-f report-a stix < "stix.json"'))
    parser.add_argument(
        '-t', '--v1-token', default=V1_TOKEN,
        help=('Authentication token of your Trend Micro Vision One'
              ' user account'))
    parser.add_argument(
        '-u', '--v1-url', default=TmV1Client.base_url_default,
        help=('URL of the Trend Micro Vision One server for your region.'
              f' The default value is "{TmV1Client.base_url_default}"'))
    parser.add_argument(
        'content_type',
        choices=TmV1Client.intelligence_report_content_types,
        help=('File type of the file to be imported into a custom'
              ' intelligence report.'))
    parser.add_argument(
        'infile', nargs='?',
        type=argparse.FileType('rb'), default=sys.stdin.buffer,
        help=('File to be imported into a custom intelligence report.'
              ' The default value is stdin.'))
    parser.add_argument(
        '-n', '--name',
        help=('Name of the file to be imported. If no value is specified,'
              " the last element of the file path path passed to 'infile' is"
              " used. When the value of 'infile' is stdin, you must specify"
              ' a name.'))
    parser.add_argument(
        '-r', '--report-name',
        help='Name of the imported intelligence report.')
    main(**vars(parser.parse_args()))
