"""Fetch today's and total visitors of the site from Google Analytics 4 and write visitors.json.

Env: GA_SA_KEY (service-account JSON), GA_PROPERTY_ID (numeric GA4 property ID),
     GA_START_DATE (first day counted in the total, YYYY-MM-DD), OUT (output path).
"""
import json
import os
from datetime import datetime, timedelta, timezone

from google.auth.transport.requests import AuthorizedSession
from google.oauth2 import service_account

creds = service_account.Credentials.from_service_account_info(
    json.loads(os.environ['GA_SA_KEY']),
    scopes=['https://www.googleapis.com/auth/analytics.readonly'])
session = AuthorizedSession(creds)
url = f"https://analyticsdata.googleapis.com/v1beta/properties/{os.environ['GA_PROPERTY_ID']}:runReport"


def active_users(start, end):
    r = session.post(url, json={'dateRanges': [{'startDate': start, 'endDate': end}],
                                'metrics': [{'name': 'activeUsers'}]})
    r.raise_for_status()
    rows = r.json().get('rows', [])
    return int(rows[0]['metricValues'][0]['value']) if rows else 0


# "today" is interpreted in the property's time zone
data = {
    'today': active_users('today', 'today'),
    'total': active_users(os.environ['GA_START_DATE'], 'today'),
    'updated': datetime.now(timezone(timedelta(hours=9))).strftime('%Y-%m-%d %H:%M KST'),
}
os.makedirs(os.path.dirname(os.environ['OUT']) or '.', exist_ok=True)
with open(os.environ['OUT'], 'w') as fh:
    json.dump(data, fh)
print(data)
