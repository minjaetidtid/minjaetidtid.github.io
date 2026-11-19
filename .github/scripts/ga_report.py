"""Detailed visitor report from Google Analytics 4 (who visited: when, where, device, source).

Env: GA_SA_KEY, GA_PROPERTY_ID, GA_START_DATE, OUT. Run only through the manual workflow;
the output is encrypted before it is uploaded.
"""
import json
import os

from google.auth.transport.requests import AuthorizedSession
from google.oauth2 import service_account

creds = service_account.Credentials.from_service_account_info(
    json.loads(os.environ['GA_SA_KEY']),
    scopes=['https://www.googleapis.com/auth/analytics.readonly'])
session = AuthorizedSession(creds)
base = f"https://analyticsdata.googleapis.com/v1beta/properties/{os.environ['GA_PROPERTY_ID']}"
dates = [{'startDate': os.environ['GA_START_DATE'], 'endDate': 'today'}]


def report(kind, dims, mets, **extra):
    body = {'dimensions': [{'name': d} for d in dims], 'metrics': [{'name': m} for m in mets],
            'limit': 1000, **extra}
    r = session.post(f'{base}:{kind}', json=body)
    if not r.ok:
        return {'error': r.text}
    out = [dict(zip(dims + mets, [v['value'] for v in row.get('dimensionValues', [])] +
                    [v['value'] for v in row['metricValues']])) for row in r.json().get('rows', [])]
    return out


data = {
    'visits': report('runReport',
                     ['dateHour', 'country', 'city', 'deviceCategory', 'operatingSystem', 'browser',
                      'sessionSource', 'sessionMedium', 'newVsReturning'],
                     ['activeUsers', 'sessions', 'screenPageViews', 'userEngagementDuration'],
                     dateRanges=dates),
    'devices': report('runReport',
                      ['dateHour', 'city', 'mobileDeviceBranding', 'mobileDeviceMarketingName',
                       'mobileDeviceModel', 'operatingSystemWithVersion', 'browser', 'screenResolution',
                       'language'],
                      ['activeUsers', 'screenPageViews', 'userEngagementDuration'], dateRanges=dates),
    'pages': report('runReport', ['pagePath'], ['screenPageViews', 'activeUsers'], dateRanges=dates),
    'realtime_30min': report('runRealtimeReport', ['country', 'city', 'deviceCategory', 'minutesAgo'],
                             ['activeUsers']),
}
os.makedirs(os.path.dirname(os.environ['OUT']) or '.', exist_ok=True)
with open(os.environ['OUT'], 'w') as fh:
    json.dump(data, fh, ensure_ascii=False, indent=1)
print({k: len(v) if isinstance(v, list) else v for k, v in data.items()})
