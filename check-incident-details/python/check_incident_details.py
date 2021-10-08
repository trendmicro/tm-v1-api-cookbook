import argparse
import datetime
import json
import os

import requests

# default settings
V1_TOKEN = os.environ.get('TMV1_TOKEN', '')
V1_URL = os.environ.get('TMV1_URL', 'https://api.xdr.trendmicro.com')


def check_datetime_aware(d):
    return (d.tzinfo is not None) and (d.tzinfo.utcoffset(d) is not None)


class TmV1Client:
    base_url_default = V1_URL
    WB_STATUS_IN_PROGRESS = 1

    def __init__(self, token, base_url=None):
        if not token:
            raise ValueError('Authentication token missing')
        self.token = token
        self.base_url = base_url or TmV1Client.base_url_default

    def make_headers(self):
        return {
            'Authorization': 'Bearer ' + self.token,
            'Content-Type': 'application/json;charset=utf-8'
        }

    def get(self, path, **kwargs):
        kwargs.setdefault('headers', {}).update(self.make_headers())
        r = requests.get(self.base_url + path, **kwargs)
        if ((200 == r.status_code)
                and ('application/json' in r.headers.get('Content-Type', ''))):
            return r.json()
        raise RuntimeError(f'Request unsuccessful (GET {path}):'
                           f' {r.status_code} {r.text}')

    def put(self, path, **kwargs):
        kwargs.setdefault('headers', {}).update(self.make_headers())
        r = requests.put(self.base_url + path, **kwargs)
        if ((200 == r.status_code)
                and ('application/json' in r.headers.get('Content-Type', ''))):
            return r.json()
        raise RuntimeError(f'Request unsuccessful (PUT {path}):'
                           f' {r.status_code} {r.text}')

    def get_workbench_histories(self, start, end, offset=None, size=None):
        if not check_datetime_aware(start):
            start = start.astimezone()
        if not check_datetime_aware(end):
            end = end.astimezone()
        start = start.astimezone(datetime.timezone.utc)
        end = end.astimezone(datetime.timezone.utc)
        start = start.isoformat(timespec='milliseconds').replace('+00:00', 'Z')
        end = end.isoformat(timespec='milliseconds').replace('+00:00', 'Z')
        # API returns data in the range of [offset, offset+limit)
        return self.get(
            '/v2.0/xdr/workbench/workbenchHistories',
            params=dict([('startTime', start), ('endTime', end),
                        ('sortBy', '-createdTime')]
                        + ([('offset', offset)] if offset is not None else [])
                        + ([('limit', size)] if size is not None else [])
                        ))['data']['workbenchRecords']

    def update_workbench(self, workbench_id, status):
        return self.put(
            f'/v2.0/xdr/workbench/workbenches/{workbench_id}',
            json={'investigationStatus': status})


def fetch_workbench_alerts(v1, start, end):
    """
    This function do the loop to get all workbench alerts by changing
    the parameters of both 'offset' and 'size'.
    """
    offset = 0
    size = 100
    alerts = []
    while True:
        gotten = v1.get_workbench_histories(start, end, offset, size)
        if not gotten:
            break
        print(f'Workbench alerts ({offset} {offset+size}): {len(gotten)}')
        alerts.extend(gotten)
        offset = len(alerts)
    return alerts


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

    wb_records = fetch_workbench_alerts(v1, start, end)
    if wb_records:
        print('')
        print('Target Workbench alerts:')
        print(json.dumps([x['workbenchId'] for x in wb_records], indent=2))
        print('')
        records_list = []
        for record in wb_records:
            wb_id = record['workbenchId']
            records_list.append(record)
            if record['investigationStatus'] == 0:
                v1.update_workbench(wb_id, TmV1Client.WB_STATUS_IN_PROGRESS)
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
    parser.add_argument(
        '-t', '--v1-token', default=V1_TOKEN,
        help=('Authentication token of your Trend Micro Vision One'
              ' user account'))
    parser.add_argument(
        '-r', '--v1-url', default=TmV1Client.base_url_default,
        help=('URL of the Trend Micro Vision One server for your region.'
              f' The default value is "{TmV1Client.base_url_default}"'))
    main(**vars(parser.parse_args()))
