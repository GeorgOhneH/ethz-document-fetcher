PROPFIND_DATA = """<?xml version="1.0"?>
<a:propfind xmlns:a="DAV:">
    <a:prop xmlns:oc="http://owncloud.org/ns">
        <oc:checksums/>
        <a:getcontenttype/>
    </a:prop>
</a:propfind>"""

WEBDAV_URL = "https://polybox.ethz.ch/public.php/webdav/"
INDEX_URL = "https://polybox.ethz.ch/index.php/s/"

BASIC_HEADER = {
    "Content-Type": "application/xml; charset=utf-8",
    "Depth": "infinity",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:74.0) Gecko/20100101 Firefox/74.0",
}


