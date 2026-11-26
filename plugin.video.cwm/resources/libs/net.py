# Every request in Cum With Me (and its scrapers, which run in the same interpreter) was made
# without a timeout, so one slow or dead site froze the whole full-screen window. Give all
# requests a default timeout unless the caller sets one.
import requests

DEFAULT_TIMEOUT = 20

if not getattr(requests.Session.request, '_cwm_timeout', False):
    _orig_request = requests.Session.request

    def _request(self, method, url, **kwargs):
        if kwargs.get('timeout') is None:
            kwargs['timeout'] = DEFAULT_TIMEOUT
        return _orig_request(self, method, url, **kwargs)

    _request._cwm_timeout = True
    requests.Session.request = _request
