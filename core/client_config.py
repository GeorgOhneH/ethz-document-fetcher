import sys

class ClientConfig(object):
    PUBLIC_KEY = 'yIEWDP2+1xuGrk1NBKIBfFMzxpwEo+6jrsOyWMM9rS8'
    APP_NAME = 'ethz-document-fetcher'
    COMPANY_NAME = 'ethz-document-fetcher'
    HTTP_TIMEOUT = 30
    MAX_DOWNLOAD_RETRIES = 3
    UPDATE_URLS = [f'https://ethz-document-fetcher-release.s3.eu-central-1.amazonaws.com/{sys.platform}']
