from settings import settings

SSO_URL = "https://aai-logon.ethz.ch/idp/profile/SAML2/Redirect/SSO"
SSO_DATA = {
    ":formid": "_content_main_de_jcr_content_par_start",
    ":formstart": "/content/main/de/jcr:content/par/start",
    "_charset_": "UTF-8",
    "form_flavour": "eth_form",
    "j_username": settings.username,
    "j_password": settings.password,
    "_eventId_proceed": "",
}

MOODLE_URL = "https://moodle-app2.let.ethz.ch/Shibboleth.sso/SAML2/POST"
ILIAS_URL = "https://ilias-app2.let.ethz.ch/Shibboleth.sso/SAML2/POST"
