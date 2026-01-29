import argparse
import datetime
import json
import os

import requests

# Setting variables
V1_TOKEN = os.environ.get('TMV1_TOKEN', '')
# Specify the correct domain name for your region in V1_URL
#   default: https://api.xdr.trendmicro.com (US region)
V1_URL = os.environ.get('TMV1_URL', 'https://api.xdr.trendmicro.com')
# This value is used for User-Agent header in API requests. So you can
# customize this value to describe your company name, integration tool name,
# and so on as you like.
#   default: "Trend Vision One API Cookbook ({script_name})"
V1_UA = os.environ.get('TMV1_UA', 'Trend Vision One API Cookbook '
                       f'({os.path.basename(__file__)})')


def is_aware_datetime(d):
    return (d.tzinfo is not None) and (d.tzinfo.utcoffset(d) is not None)


def get_datetime_param(d):
    if not is_aware_datetime(d):
        d = d.astimezone()
    d = d.astimezone(datetime.timezone.utc)
    d = d.isoformat(timespec='seconds').replace('+00:00', 'Z')
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

    def get_workbench_alerts(self, start=None, end=None):
        params = {}
        if start is not None:
            params['startDateTime'] = get_datetime_param(start)
        if end is not None:
            params['endDateTime'] = get_datetime_param(end)
        return self.get_items('/v3.0/workbench/alerts', params=params)

    def update_workbench_alert(self, alert_id, status):
        return self.patch(f'/v3.0/workbench/alerts/{alert_id}',
                          json={'investigationStatus': status})


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

    wb_records = v1.get_workbench_alerts(start, end)
    if wb_records:
        print('')
        print('Target Workbench alerts:')
        print(json.dumps([x['id'] for x in wb_records], indent=2))
        print('')
        records_list = []
        for record in wb_records:
            wb_id = record['id']
            records_list.append(record)
            if TmV1Client.WB_STATUS_NEW == record['investigationStatus']:
                v1.update_workbench_alert(wb_id,
                                          TmV1Client.WB_STATUS_IN_PROGRESS)
        print('Details of target Workbench alerts:')
        print(json.dumps(records_list, indent=2))
    else:
        print('No Workbench alerts found')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Modify alert status after checking alert details',
        epilog=(f'Example: python {os.path.basename(__file__)} '
                '-e 2021-04-12T14:28:00.123456+00:00 -d 5'))
    parser.add_argument(
        '-t', '--v1-token', default=V1_TOKEN,
        help='Authentication token of your Trend Vision One user account')
    parser.add_argument(
        '-u', '--v1-url', default=TmV1Client.base_url_default,
        help=('URL of the Trend Micro One server for your region.'
              f' The default value is "{TmV1Client.base_url_default}"'))
    parser.add_argument(
        '-s', '--start',
        help=('Timestamp in ISO 8601 format that indicates the start of'
              ' the data retrieval time range'))
    parser.add_argument(
        '-e', '--end',
        help=('Timestamp in ISO 8601 format that indicates the end of the data'
              ' retrieval time range. The default value is the current time'))
    parser.add_argument(
        '-d', '--days', type=int, default=5,
        help=('Number of days before the end time of the data retrieval'
              ' time range. The default value is 5.'))
    main(**vars(parser.parse_args()))
