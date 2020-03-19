import requests
import re
import settings


def get_technishce_mechanik():
    session = requests.Session()

    response = session.get("https://ilias-app2.let.ethz.ch/login.php")
    response = session.get("https://ilias-app2.let.ethz.ch/shib_login.php?target=")
    response = session.get(response.url)

    data = {
        "user_idp": "https://aai-logon.ethz.ch/idp/shibboleth",
        "Select": "Auswählen",
    }

    r = session.post(response.url, data=data)

    match = re.search("jsessionid=.*=e1s1", r.text)

    data = {
        ":formid": "_content_main_de_jcr_content_par_start",
        ":formstart": "/content/main/de/jcr:content/par/start",
        "_charset_": "UTF-8",
        "form_flavour": "eth_form",
        "j_username": settings.username,
        "j_password": settings.password,
        "_eventId_proceed": "",
    }

    r = session.post("https://aai-logon.ethz.ch/idp/profile/SAML2/Redirect/SSO;{}".format(match.group()), data=data)

    match = re.search("""name="RelayState" value="(.*)"/>""", r.text)
    ssm = match.group(1)

    match = re.search("""name="SAMLResponse" value="(.*)"/>""", r.text)
    sam = match.group(1)
    ssm = ssm[17:]
    data = {
        "RelayState": "ss:mem:{}".format(ssm),
        "SAMLResponse": sam,
    }

    r = session.post("https://ilias-app2.let.ethz.ch/Shibboleth.sso/SAML2/POST", data=data)
    r = session.get(
        "https://ilias-app2.let.ethz.ch/ilias.php?ref_id=175238&cmd=view&cmdClass=ilrepositorygui&cmdNode=7z&baseClass=ilRepositoryGUI")

    match = re.findall(
        """<h4 class="il_ContainerItemTitle"><a href="(.*)" class="il_ContainerItemTitle"  >(Serie [0-9]+)</a></h4>""",
        r.text)
    resu = {}
    for serie, i in match:
        rr = {}
        serie = serie.replace('amp;', "")
        r = session.get("https://ilias-app2.let.ethz.ch/{}".format(serie))
        match = re.findall(
            """<h4 class="il_ContainerItemTitle"><a href="(.*)" class="il_ContainerItemTitle".*>(.*)</a></h4>""",
            r.text)
        for url, name in match:
            if name != "Lösungen":
                rr[name] = url
            else:
                url = url.replace('amp;', "")
                r = session.get("https://ilias-app2.let.ethz.ch/{}".format(url))
                match = re.findall(
                    """<h4 class="il_ContainerItemTitle"><a href="(.*)" class="il_ContainerItemTitle".*>(.*)</a></h4>""",
                    r.text)
                for url2, name2 in match:
                    rr[name2] = url2
        resu[i] = rr
    return {"uebungen": resu, }, session


if __name__ == "__main__":
    print(get_technishce_mechanik())
