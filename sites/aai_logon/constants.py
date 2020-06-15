from settings import settings

SSO_URL = "https://aai-logon.ethz.ch/idp/profile/SAML2/Redirect/SSO"
BASE_URL = "https://aai-logon.ethz.ch"
SSO_DATA = {
    ":formid": "_content_main_de_jcr_content_par_start",
    ":formstart": "/content/main/de/jcr:content/par/start",
    "_charset_": "UTF-8",
    "form_flavour": "eth_form",
    "j_username": settings.username,
    "j_password": settings.password,
    "_eventId_proceed": "",
}
