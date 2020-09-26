import asyncio
import logging
import time

from core.exceptions import LoginError

logger = logging.getLogger(__name__)

locks = {}


async def safe_login_module(session, site_settings, login_function):
    if not callable(login_function):
        logger.warning("login function was not callable")
        return

    func_name = login_function.__module__ + "." + login_function.__name__
    lock_name = func_name + str(id(session))

    if lock_name in locks:
        lock = locks[lock_name]
    else:
        lock = asyncio.Lock()
        locks[lock_name] = lock

    async with lock:
        if not hasattr(login_function, "errors"):
            login_function.errors = {}
        if id(session) not in login_function.errors:
            logger.debug(f"Logging into {func_name}")
            start_time = time.time()
            try:
                await login_function(session=session, site_settings=site_settings)
                logger.debug(f"Logged into {func_name}, time: {(time.time() - start_time):.2f}")
                login_function.errors[id(session)] = False
            except LoginError as e:
                login_function.errors[id(session)] = True
                raise e
        if login_function.errors[id(session)]:
            raise LoginError("Previous login was not successful")


def get_module_function(name):
    mf_name = ("custom." + name).split(".")
    module_name = ".".join(mf_name[:-1])
    function_name = mf_name[-1]
    return module_name, function_name


def check_if_null(p_kwargs):
    for key, value in p_kwargs.items():
        if value is None:
            return True
    return False


def dict_to_string(d):
    result = ""
    for key, value in d.items():
        result += str(key) + "=" + str(value) + " "
    if d:
        result = result[:-1]
    return result


def ignore_if_signal_is_none(function):
    def wrapper(self, *args, **kwargs):
        if self.signals is None:
            return
        result = function(self, *args, **kwargs)
        return result

    return wrapper
