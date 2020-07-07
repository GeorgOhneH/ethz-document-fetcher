import copy
import logging
from typing import Iterator

from settings.config_objs import ConfigString

logger = logging.getLogger(__name__)


def init_wrapper(func, config_objs):
    def wrapper(self, *args, **kwargs):
        if hasattr(self, "_config_objs"):
            self._config_objs.update(config_objs)
        else:
            self._config_objs = config_objs
        return func(self, *args, **kwargs)

    return wrapper


class ConfigBase(type):
    def __new__(mcs, name, bases, attrs, **kwargs):
        config_objs = {}
        new_attrs = {}
        for key, value in attrs.items():
            if isinstance(value, ConfigString):
                config_obj = value
                config_obj.name = key
                config_objs[key] = config_obj

                new_attrs[key] = property(lambda self, v_k=key: self._config_objs[v_k].get(),
                                          lambda self, value, v_k=key: self._config_objs[v_k].set(value))
            else:
                new_attrs[key] = value

        cls = super().__new__(mcs, name, bases, new_attrs)
        cls.__init__ = init_wrapper(cls.__init__, config_objs)
        return cls


class Configs(metaclass=ConfigBase):
    def __init__(self):
        self.__dict__ = copy.deepcopy(self.__dict__)
        for config_obj in self:
            config_obj.instance = self
        for config_obj in self:
            config_obj.instance_created()
        for config_obj in self:
            if config_obj.default is not None:
                config_obj.set(config_obj.default)

    def get_config_obj(self, name: str) -> ConfigString:
        return self._config_objs[name]

    def __getitem__(self, key):
        return self.get_config_obj(key)

    def __iter__(self) -> Iterator[ConfigString]:
        return iter(self._config_objs.values())

    def __len__(self):
        return len(self._config_objs)

    def to_dict(self):
        return {config_obj.name: config_obj.get() for config_obj in self}

    def check_if_valid(self):
        for config_obj in self:
            if not config_obj.is_valid():
                logger.warning(f"Config object was not valid. Error Msg: {config_obj.msg}")
                return False
        return True
