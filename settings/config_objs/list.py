import logging

from settings.config_objs.string import ConfigString, LineEdit

logger = logging.getLogger(__name__)


class ListLineEdit(LineEdit):
    def get_value(self):
        raw = super(ListLineEdit, self).get_value()
        if raw is None:
            return []
        return [x.strip() for x in raw.split(",") if x.strip()]

    def set_value(self, value):
        if value is None:
            super(ListLineEdit, self).set_value("")
        else:
            super(ListLineEdit, self).set_value(", ".join(value))


class ConfigList(ConfigString):
    def __init__(self, hint_text="", *args, **kwargs):
        super().__init__(hint_text="Separate by comma. " + hint_text, *args, **kwargs)

    def init_widget(self):
        return ListLineEdit(self)

    def _save(self):
        if not self._value:
            return "[]"
        result = "["
        for x in self._value[:-1]:
            result += str(x) + ", "
        result += self._value[-1] + "]"
        return result

    def _load(self, value):
        if not value:
            return []

        if value[0] != "[" or value[-1] != "]":
            logger.warning(f"Could not load value from {self.name}. Using empty list")
            return []

        return [x.strip() for x in value[1:-1].split(",") if x.strip()]

    def _test(self, value, from_widget):
        if not isinstance(value, list):
            raise ValueError("Value must be a list")

    def set_parser(self, parser):
        parser.add_argument(f'--{self.name}', nargs='*')
