PROPFIND_DATA = """<?xml version="1.0"?>
<a:propfind xmlns:a="DAV:">
    <a:prop xmlns:oc="http://owncloud.org/ns">
        <oc:checksums/>
        <a:getcontenttype/>
    </a:prop>
</a:propfind>"""

BASE_URL = "https://polybox.ethz.ch"
WEBDAV_PUBLIC_URL = "https://polybox.ethz.ch/public.php/webdav/"
WEBDAV_REMOTE_URL = "https://polybox.ethz.ch/remote.php/webdav/"
INDEX_URL = "https://polybox.ethz.ch/index.php/"
LOGIN_USER_URL = "https://polybox.ethz.ch/index.php/login"
USER_WEBDAV_URL = "https://polybox.ethz.ch/remote.php/dav/files/"

BASIC_HEADER = {
    "Content-Type": "application/xml; charset=utf-8",
    "Depth": "infinity",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:74.0) Gecko/20100101 Firefox/74.0",
}


