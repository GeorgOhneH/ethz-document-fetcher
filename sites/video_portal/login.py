from sites.video_portal.constants import BASE_URL


def get_eth_auth(site_settings):
    return {
        "_charset_": "utf-8",
        "j_username": site_settings.username,
        "j_password": site_settings.password,
        "j_validate": "true",
    }


async def login_and_data(session, site_settings, department, year, semester, course_id, meta_video_url,
                         pwd_username=None, pwd_password=None, depth=0):
    course_url = f"{BASE_URL}{department}/{year}/{semester}/{course_id}"

    async with session.get(meta_video_url) as response:
        meta_data = await response.json()

    if meta_data["authorized"]:
        return meta_data

    if depth >= 4:
        raise Exception("could not log in after 4 tries")

    protection = meta_data["protection"]

    if protection == "ETH":
        security_check_url = f"{BASE_URL}{department}/{year}/{semester}/j_security_check"
        async with session.post(security_check_url, data=get_eth_auth(site_settings)) as response:
            await response.text()

    elif protection == "PWD":
        if not pwd_username or not pwd_username:
            raise ValueError("pwd_username and pwd_password must be set")
        pwd_data = {
            "_charset_": "utf-8",
            "username": pwd_username,
            "password": pwd_password,
        }
        series_url = course_url + ".series-login.json"
        async with session.post(series_url, data=pwd_data) as response:
            await response.text()

    return await login_and_data(session, site_settings, department, year, semester, course_id, meta_video_url,
                                pwd_username=pwd_username, pwd_password=pwd_password, depth=depth + 1)
