BASE_URL = "https://moodle-app2.let.ethz.ch"
AUTH_URL = "https://moodle-app2.let.ethz.ch/auth/shibboleth/login.php"
IDP_DATA = {"idp": "https://aai-logon.ethz.ch/idp/shibboleth"}

PDF_IMAGE = "https://moodle-app2.let.ethz.ch/theme/image.php/boost_ethz/core/1587709378/f/pdf-24"

MTYPE_FILE = "resource"
MTYPE_EXTERNAL_LINK = "url"
MTYPE_DIRECTORY = "folder"

UPDATE_REQUEST_PAYLOAD = [{
    "index": 0,
    "methodname": "core_course_get_updates_since",
    "args": {
        "courseid": 12228,
        "since": 0,
    }
}]
AJAX_SERVICE_URL = "https://moodle-app2.let.ethz.ch/lib/ajax/service.php"
