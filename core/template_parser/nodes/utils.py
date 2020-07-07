import hashlib
from core.storage import cache


def get_kwargs_hash(kwargs: dict):
    kwarg_string = get_kwargs_string(kwargs)
    return hashlib.md5(kwarg_string.encode('utf-8')).hexdigest()


def get_kwargs_string(kwargs):
    result = ""
    for key in sorted(kwargs.keys()):
        value = kwargs[key]
        if value is None:
            continue

        if isinstance(value, dict):
            result += get_kwargs_string(value)
        else:
            result += f"{key}:{value}"

    return result


def get_folder_name_from_hash(kwargs_hash):
    folder_name_cache = cache.get_json("folder_name")
    folder_name = folder_name_cache.get(kwargs_hash, None)
    return folder_name


def get_folder_name_from_kwargs(kwargs):
    kwargs_hash = get_kwargs_hash(kwargs)
    return get_folder_name_from_hash(kwargs_hash)
