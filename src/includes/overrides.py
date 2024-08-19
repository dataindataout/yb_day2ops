import requests


def suppress_warnings():
    # os.environ['REQUESTS_CA_BUNDLE'] = "./ca_cert.pem"

    # Suppress only the single warning from urllib3 needed.
    requests.urllib3.disable_warnings()

    # override the methods to set verify=False
    requests.get = lambda url, **kwargs: requests.request(
        method="GET", url=url, verify=False, **kwargs
    )
    requests.post = lambda url, **kwargs: requests.request(
        method="POST", url=url, verify=False, **kwargs
    )
    requests.put = lambda url, **kwargs: requests.request(
        method="PUT", url=url, verify=False, **kwargs
    )
    requests.delete = lambda url, **kwargs: requests.request(
        method="DELETE", url=url, verify=False, **kwargs
    )
