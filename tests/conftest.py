import pytest
import sys
from settings.settings import Settings


def pytest_addoption(parser):
    for action in Settings.parser._actions:
        kwargs = {k: v for k, v in action._get_kwargs() if v}
        name = kwargs.pop("option_strings")
        if "--help" in name:
            continue
        parser.addoption(*name)
