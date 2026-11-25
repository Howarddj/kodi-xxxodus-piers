"""
Exports Issues from a specified repository to a CSV file
Uses basic authentication (Github username + password) to retrieve Issues
from a repository that username has access to. Supports Github API v3.
"""
import csv
import sys
import xbmc
import xbmcvfs
import os
import requests
import kodi

# Python 3 / Kodi 20+: xbmc.translatePath is gone, csv wants a text file, and
# str + bytes concatenation fails, so only encode on Python 2.
PY2 = sys.version_info[0] == 2
translatePath = xbmc.translatePath if PY2 else xbmcvfs.translatePath
def _t(s):
    s = s or ''
    return s.encode('utf-8') if PY2 else s

def run(REPO, STATE):
    ISSUES_FOR_REPO_URL = 'http://api.github.com/repos/%s/issues?state=%s' % (REPO, STATE)

    def write_issues(response):
        "output a list of issues to csv"
        if not r.status_code == 200:
            raise Exception(r.status_code)
        for issue in r.json():
            username = issue.get("user", {}).get('login', {})
            if issue['labels']:
                labels = issue['labels']
                for label in labels:
                    #if label['name'] == "Client Requested":
                    csvout.writerow(['\n<item>\n<id>'+str(issue['number'])+'</id>\n<username>'+username+'</username>\n<label>'+label['name']+'</label>\n<title>'+_t(issue['title'])+'</title>\n<body>'+_t(issue['body'])+'</body>\n<created>'+issue['created_at']+'</created>\n</item>\n'])
            else:
                csvout.writerow(['\n<item>\n<id>'+str(issue['number'])+'</id>\n<username>'+username+'</username>\n<label>No Label</label>\n<title>'+_t(issue['title'])+'</title>\n<body>'+_t(issue['body'])+'</body>\n<created>'+issue['created_at']+'</created>\n</item>\n'])

    r = requests.get(ISSUES_FOR_REPO_URL, verify=False)
    csvfile = translatePath(os.path.join(kodi.datafolder, '%s-issues-%s.csv' % (kodi.get_id(),STATE)))
    csvout = csv.writer(open(csvfile, 'wb') if PY2 else open(csvfile, 'w', newline='', encoding='utf-8'))
    write_issues(r)

    #more pages? examine the 'link' header returned
    if 'link' in r.headers:
        pages = dict(
            [(rel[6:-1], url[url.index('<')+1:-1]) for url, rel in
                [link.split(';') for link in
                    r.headers['link'].split(',')]])
        while 'last' in pages and 'next' in pages:
            r = requests.get(pages['next'])
            write_issues(r)
            if pages['next'] == pages['last']:
                break