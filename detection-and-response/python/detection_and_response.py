import os
import uuid
import ipaddress
import datetime
import time
import argparse

import requests

# default settings
V1_TOKEN = os.environ.get('TMV1_TOKEN', '')
V1_URL = os.environ.get('TMV1_URL', 'https://api.xdr.trendmicro.com')
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


def is_uuid(v):
    try:
        if not isinstance(v, str):
            return False
        uuid.UUID(hex=v)
    except ValueError:
        return False
    return True


def is_ipaddress(v):
    try:
        ipaddress.ip_address(v)
    except ValueError:
        return False
    return True


def is_aware_datetime(d):
    return (d.tzinfo is not None) and (d.tzinfo.utcoffset(d) is not None)


def get_datetime_arg(d):
    if not is_aware_datetime(d):
        d = d.astimezone()
    d = d.astimezone(datetime.timezone.utc)
    d = d.isoformat(timespec='seconds').replace('+00:00', 'Z')
    return d


def get_filter_arg(name, value, enclose="'", equal='eq'):
    if not is_container(value):
        value = [value]
    param = ' or '.join(f'{name} {equal} {enclose}{x}{enclose}' for x in value)
    if 1 < len(value):
        param = '('+param+')'
    return param


def get_search_query_arg(name, values):
    return get_filter_arg(name, values, enclose='"', equal=':')


def get_multiple_request(name, args):
    r = []
    if is_container(args):
        r.extend({name: v} for v in args)
    elif isinstance(args, str):
        r.append({name: args})
    return r


def kwargs_from_args(t):
    """
    This function returns dict of list for the values of duplicated key.
    """
    d = {}
    if not t:
        return d
    for arg in t:
        d.setdefault(arg[0], []).append(arg[1])
    return d


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

    def patch(self, path, **kwargs):
        kwargs.setdefault('headers', {}).update(self.make_headers())
        r = requests.patch(self.base_url + path, **kwargs)
        if 204 == r.status_code:
            return
        raise RuntimeError(f'Request unsuccessful (PATCH {path}):'
                           f' {r.status_code} {r.text}')

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

    def get_workbench_alerts(self, start=None, end=None,
                             investigation_status=None):
        params = {}
        if start is not None:
            params['startDateTime'] = get_datetime_arg(start)
        if end is not None:
            params['endDateTime'] = get_datetime_arg(end)
        filters = []
        if investigation_status is not None:
            filters.append(get_filter_arg('investigationStatus',
                                          investigation_status))
        headers = {}
        if filters:
            headers['TMV1-Filter'] = ' and '.join(filters)
        return self.get_items('/v3.0/workbench/alerts', params=params,
                              headers=headers)

    def update_workbench_alert(self, alert_id, status):
        return self.patch(f'/v3.0/workbench/alerts/{alert_id}', json={
            'investigationStatus': status})

    def add_workbench_note(self, alert_id, note):
        return self.post(
            f'/v3.0/workbench/alerts/{alert_id}/notes',
            json={'content': note})

    def search_endpoints(self, agent_guid=None, ip=None, endpoint_name=None):
        filters = []
        if agent_guid is not None:
            filters.append(get_filter_arg('agentGuid', agent_guid))
        if ip is not None:
            filters.append(get_filter_arg('ip', ip))
        if endpoint_name is not None:
            filters.append(get_filter_arg('endpointName', endpoint_name))
        headers = {}
        if filters:
            headers['TMV1-Query'] = ' and '.join(filters)
        return self.get_items('/v3.0/eiqs/endpoints', headers=headers)

    def search_email_activities(self, start=None, end=None, to_address=None,
                                url=None):
        params = {}
        if start is not None:
            params['startDateTime'] = get_datetime_arg(start)
        if end is not None:
            params['endDateTime'] = get_datetime_arg(end)
        query = []
        if to_address is not None:
            query.append(get_search_query_arg('mailToAddresses', to_address))
        if url is not None:
            query.append(get_search_query_arg('mailUrlsRealLink', url))
        headers = {'TMV1-Query': 'mailDirection:1'}
        if query:
            headers['TMV1-Query'] = ' and '.join(query)
        return self.get_items('/v3.0/search/emailActivities', params=params,
                              headers=headers)

    def add_suspicious_objects(self, url=None, domain=None, file_sha1=None,
                               mail_address=None, ip=None):
        request = (get_multiple_request('url', url) +
                   get_multiple_request('domain', domain) +
                   get_multiple_request('fileSha1', file_sha1) +
                   get_multiple_request('senderMailAddress', mail_address) +
                   get_multiple_request('ip', ip))
        return self.post_multiple('/v3.0/response/suspiciousObjects',
                                  json=request)

    def isolate_endpoints(self, agent_guid=None, endpoint_name=None):
        request = (get_multiple_request('agentGuid', agent_guid) +
                   get_multiple_request('endpointName', endpoint_name))
        return self.post_multiple('/v3.0/response/endpoints/isolate',
                                  json=request)

    def quarantine_message(self, message_id=None, mailbox=None,
                           unique_id=None):
        request = []
        message_id = get_multiple_request('messageId', message_id)
        if mailbox is not None:
            mailbox = get_multiple_request('mailBox', mailbox)
            if len(message_id) != len(mailbox):
                raise ValueError('message_id and mailbox do not have the same'
                                 ' length')
            for mid, mbox in zip(message_id, mailbox):
                mid.update(mbox)
        request.extend(message_id)
        request.extend(get_multiple_request('uniqueId', unique_id))
        return self.post_multiple('/v3.0/response/emails/quarantine',
                                  json=request)

    def get_response_tasks(self, ids=None):
        params = {}
        if ids is not None:
            params['filter'] = get_filter_arg('id', ids)
        return self.get_items('/v3.0/response/tasks', params=params)


def fetch_new_workbench_alerts(v1, start, end):
    return v1.get_workbench_alerts(
        start, end,
        investigation_status=TmV1Client.WB_STATUS_NEW
    )


def make_added_suspicious_objects_arg(indicator):
    t = indicator['type']
    v = indicator['value']
    if v:
        if 'url' == t:
            return ('url', v)
        if 'domain' == t:
            return ('domain', v)
        if 'file_sha1' == t:
            return ('file_sha1', v)
        if 'email_sender' == t:
            return ('mail_address', v)
        if 'ip' == t:
            return ('ip', v)


def make_searched_endpoints_args(entity):
    id_ = entity['entityId']
    v = entity['entityValue']
    if (is_uuid(id_) and v['guid'] == id_):
        return (('agent_guid', id_),)
    elif (isinstance(id_, list) and
            all(is_ipaddress(ip) for ip in id_) and
            v['ips'] == id_):
        return tuple(('ip', ip) for ip in id_)
    elif v['name'] == id_:
        return (('endpoint_name', id_),)
    return


def make_searched_emails_args(entity, indicators):
    urls = set(indicator['value'] for indicator in indicators
               if ((indicator['id'] in entity['relatedIndicatorIds']) and
                   ('url' == indicator['type'])))
    return tuple([('to_address', entity['entityValue'])] +
                 [('url', url) for url in urls])


def make_isolated_endpoint_arg(endpoint):
    if (endpoint['productCode'] in ['sao', 'sds', 'xes']):
        if endpoint['agentGuid']:
            return ('agent_guid', endpoint['agentGuid'])
        elif endpoint['endpointName']:
            return ('endpoint_name', endpoint['endpointName'])
    return


def make_quarantined_email_arg(activity):
    if activity['mailMsgId']:
        return ('message_id', activity['mailMsgId'])
    elif activity['msgUuid']:
        return ('unique_id', activity['msgUuid'])
    return


def wait_response_tasks(v1, tasks):
    count = 0
    while True:
        running_task_indexes = [
            i for i, t in enumerate(tasks)
            if t and (t['status'] in ['queued', 'running'])
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
        response = v1.get_response_tasks([tasks[i]['id']
                                         for i in running_task_indexes])
        for i, r in enumerate(response):
            tasks[running_task_indexes[i]].update(r)
    finished = not running_task_indexes
    if not finished:
        print('Tasks not finished')
    return finished


def fetch_endpoints(v1, *endpoints):
    r = {}
    for args in endpoints:
        r[args] = v1.search_endpoints(**kwargs_from_args(args))
    return r


def fetch_email_activities(v1, start, end, *emails):
    r = {}
    for args in emails:
        r[args] = v1.search_email_activities(start, end,
                                             **kwargs_from_args(args))
    return r


def add_suspicious_objects(v1, suspicious_objects):
    r = {}
    if not suspicious_objects:
        return r
    response = v1.add_suspicious_objects(**kwargs_from_args(
        suspicious_objects
    ))
    tasks = v1.get_from_post_multiple_response(response)
    wait_response_tasks(v1, tasks)
    for (req, res), task in zip(response, tasks):
        if 'url' in req:
            suspicious_object = ('url', req['url'])
        elif 'domain' in req:
            suspicious_object = ('domain', req['domain'])
        elif 'fileSha1' in req:
            suspicious_object = ('file_sha1', req['fileSha1'])
        elif 'senderMailAddress' in req:
            suspicious_object = ('mail_address', req['senderMailAddress'])
        elif 'ip' in req:
            suspicious_object = ('ip', req['ip'])
        if suspicious_object not in suspicious_objects:
            raise RuntimeError(f'Unknown item found ({suspicious_object})')
        r[suspicious_object] = (res, task)
    return r


def isolate_endpoints(v1, endpoints):
    r = {}
    if not endpoints:
        return r
    response = v1.isolate_endpoints(**kwargs_from_args(endpoints))
    tasks = v1.get_from_post_multiple_response(response)
    wait_response_tasks(v1, tasks)
    for (req, res), task in zip(response, tasks):
        if 'agentGuid' in req:
            endpoint = ('agent_guid', req['agentGuid'])
        elif 'endpointName' in req:
            endpoint = ('endpoint_name', req['endpointName'])
        if endpoint not in endpoints:
            raise RuntimeError(f'Unknown item found ({endpoint})')
        r[endpoint] = (res, task)
    return r


def quarantine_emails(v1, emails):
    r = {}
    if not emails:
        return r
    response = v1.quarantine_message(**kwargs_from_args(emails))
    tasks = v1.get_from_post_multiple_response(response)
    wait_response_tasks(v1, tasks)
    for (req, res), task in zip(response, tasks):
        if 'messageId' in req:
            email = ('message_id', req['messageId'])
        elif 'uniqueId' in req:
            email = ('unique_id', req['uniqueId'])
        if email not in emails:
            raise RuntimeError(f'Unknown item found ({email})')
        r[email] = (res, task)
    return r


def get_added_suspicious_object_note(indicator, added_suspicous_objects):
    arg = indicator["add"]
    action = f'adding {arg[0]} "{arg[1]}" to the suspicious object list'
    (res, task) = added_suspicous_objects[indicator['add']]
    if not task:
        error = res.get('body', {}).get('error', '')
        return f'Unable to start {action} task. Error code: {error}'
    status = task['status']
    if 'running' == status:
        return (f'The status of {action} task is "{status}". '
                f'Task ID: {task["id"]}')
    if 'succeeded' != status:
        error = task.get('error', '')
        return (f'The status of {action} task is "{status}". '
                f'Error code: {error}')
    return (f'Object {arg[0]} "{arg[1]}" added to Suspicious Object List'
            'successfully.')


def get_isolated_endpoint_notes(entity, searched_endpoints,
                                isolated_endpoints):
    v = entity["entityValue"]
    name = f'"{v.get("name", v.get("ips", [v.get("guid")])[0])}"'
    if 'search' not in entity:
        return [f'No action taken for endpoint {name}.']
    endpoints = searched_endpoints[entity['search']]
    if not endpoints:
        return [f'Endpoint not found. {name}']

    action = f'isolating endpoint {name}'
    r = []
    for e in endpoints:
        if 'isolate' not in e:
            r.append(f'Unable to isolate endpoint {name}.')
            continue
        (res, task) = isolated_endpoints[e['isolate']]
        if not task:
            error = res.get('body', {}).get('error', '')
            r.append(f'Unable to start {action} task. '
                     f'Error code: {error}')
        status = task['status']
        if 'running' == status:
            r.append(f'The status of the {action} task is "{status}". '
                     f'Task ID: {task["id"]}')
            continue
        r.append(f'Endpoint {name} isolated successfully.')
    return r


def get_quarantined_email_notes(entity, searched_emails, quarantined_emails):
    name = f'"{entity["entityId"]}"'
    if 'search' not in entity:
        note = [f'No action taken for the message for {name}.']
    activities = searched_emails[entity['search']]
    if not activities:
        return [f'Message activity for {name} not found.']

    action = f'quarantining the message for {name}'
    r = []
    for a in activities:
        if 'quarantine' not in a:
            r.append(f'Unable to quarantine the message for {name}.')
            continue
        (res, task) = quarantined_emails[a['quarantine']]
        if not task:
            error = res.get('body', {}).get('error', '')
            r.append(f'Unable to start {action} task. '
                     f'Error code: {error}')
        status = task['status']
        if 'running' == status:
            r.append(f'The status of the {action} task is "{status}". '
                     f'Task ID: {task["id"]}')
            continue
        r.append(f'Message for {name} quarantined successfully.')
    return r


def main(start, end, days, v1_token, v1_url):
    if end is None:
        end = datetime.datetime.now(datetime.timezone.utc)
    else:
        end = datetime.datetime.fromisoformat(end)
    if start is None:
        start = end + datetime.timedelta(days=-days)
    else:
        start = datetime.datetime.fromisoformat(start)
    v1 = TmV1Client(v1_token, v1_url)

    alerts = fetch_new_workbench_alerts(v1, start, end)
    if not alerts:
        print('No Workbench alerts found')
        return
    print(f'Retrieved workbench alerts: {len(alerts)}')

    detections = {}
    added_suspicous_objects = set()
    searched_endpoints = set()
    searched_emails = set()
    for alert in alerts:
        # Update alert status to 'In Progress'
        alert_id = alert['id']
        v1.update_workbench_alert(alert_id, TmV1Client.WB_STATUS_IN_PROGRESS)

        # Collect suspicious objects from indicators
        detections[alert_id] = {}
        for indicator in alert['indicators']:
            arg = make_added_suspicious_objects_arg(indicator)
            if arg is not None:
                added_suspicous_objects.add(arg)
                indicator['add'] = arg
                detections[alert_id].setdefault(
                    'suspicious_objects', []).append(indicator)

        # Collect affected endponts/emails from entities of impactScope
        for entity in alert['impactScope']['entities']:
            if 'host' == entity['entityType']:
                args = make_searched_endpoints_args(entity)
                if args is not None:
                    searched_endpoints.add(args)
                    entity['search'] = args
                detections[alert_id].setdefault('endpoints', []).append(entity)
            elif 'emailAddress' == entity['entityType']:
                args = make_searched_emails_args(entity, alert['indicators'])
                searched_emails.add(args)
                entity['search'] = args
                detections[alert_id].setdefault('emails', []).append(entity)

    # Add suspicous objects
    print(f'Added suspicious objects: {len(added_suspicous_objects)}')
    added_suspicous_objects = add_suspicious_objects(v1,
                                                     added_suspicous_objects)

    # Search Endpoints and Isolate
    searched_endpoints = fetch_endpoints(v1, *searched_endpoints)
    isolated_endpoints = set()
    for endpoints in searched_endpoints.values():
        if endpoints:
            for e in endpoints:
                arg = make_isolated_endpoint_arg(e)
                if arg is not None:
                    isolated_endpoints.add(arg)
                    e['isolate'] = arg
    print(f'Isolated endpoints: {len(isolated_endpoints)}')
    isolated_endpoints = isolate_endpoints(v1, isolated_endpoints)

    # Search Email Activities and Quarantine
    searched_emails = fetch_email_activities(v1, start, end, *searched_emails)
    quarantined_emails = set()
    for activities in searched_emails.values():
        if activities:
            for a in activities:
                arg = make_quarantined_email_arg(a)
                if arg is not None:
                    quarantined_emails.add(arg)
                    a['quarantine'] = arg
    print(f'Quarantined emails: {len(quarantined_emails)}')
    quarantined_emails = quarantine_emails(v1, quarantined_emails)

    # Update Workbench Alert Notes according to isolating/quarantining
    for alert_id, detection in detections.items():
        print('')
        print(f'Alert ID: {alert_id}')
        if not detection:
            note = 'No action taken for workbench alert.'
            v1.add_workbench_note(alert_id, note)
            print(f'{note}')
            continue
        for indicator in detection.get('suspicious_objects', []):
            note = get_added_suspicious_object_note(indicator,
                                                    added_suspicous_objects)
            v1.add_workbench_note(alert_id, note)
            print(f'{note}')

        for entity in detection.get('endpoints', []):
            notes = get_isolated_endpoint_notes(entity, searched_endpoints,
                                                isolated_endpoints)
            for note in notes:
                v1.add_workbench_note(alert_id, note)
                print(f'{note}')

        for entity in detection.get('emails', []):
            notes = get_quarantined_email_notes(entity, searched_emails,
                                                quarantined_emails)
            for note in notes:
                v1.add_workbench_note(alert_id, note)
                print(f'{note}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=('Take a response action on the highlighted object '
                     'in a Workbench alert'),
        epilog=(f'Example: python {os.path.basename(__file__)} '
                '-e 2021-04-12T14:28:00.123456+00:00 -d 5'))
    parser.add_argument(
        '-t', '--v1-token', default=V1_TOKEN,
        help=('Authentication token of your Trend Micro Vision One'
              ' user account'))
    parser.add_argument(
        '-u', '--v1-url', default=TmV1Client.base_url_default,
        help=('URL of the Trend Micro Vision One server for your region.'
              f' The default value is "{TmV1Client.base_url_default}"'))
    parser.add_argument(
        '-s', '--start',
        help=('Timestamp in ISO 8601 format that indicates the start of'
              ' the data retrieval time range'))
    parser.add_argument(
        '-e', '--end',
        help=('Timestamp in ISO 8601 format that indicates the end of the data'
              ' retrieval time range. The default value is the current time.'))
    parser.add_argument(
        '-d', '--days', type=int, default=5,
        help=('Number of days before the end time of the data retrieval'
              ' time range. The default value is 5.'))
    main(**vars(parser.parse_args()))
