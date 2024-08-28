from __future__ import annotations

import os.path
import warnings
from contextlib import AbstractContextManager
from importlib import resources
from pathlib import Path
from typing import TextIO

from qtpy.QtCore import QRegularExpression
from qtpy.QtGui import QKeyEvent

from .QLanguage import QLanguage

BASE_PATH = os.path.dirname(__file__)
RES_PATH = os.path.join(BASE_PATH, "resource")

# noinspection SpellCheckingInspection
__PKG_NAME = "pyqcodeeditor"
__RES_PATH = "resources"
__LANG_PATH = "languages"


def get_resource_directory(
    get_dir_string: bool = False,
) -> AbstractContextManager[Path] | str:
    if not get_dir_string:
        return resources.path(__PKG_NAME, __RES_PATH)
    with resources.path(__PKG_NAME, __RES_PATH) as path:
        return str(path)


def get_resource_file(path: str) -> str | None:
    with get_resource_directory(False) as res_dir:
        file = os.path.join(res_dir, path)
        if not os.path.isfile(file):
            return None
        return os.path.normpath(file)


def open_resource_text_file(
    path: str, encoding: str = "utf-8", errors: str = "strict"
) -> TextIO | None:
    with get_resource_directory(False) as res_dir:
        file = os.path.join(res_dir, path)
        if not os.path.isfile(file):
            return None
        return open(file, "r", encoding=encoding, errors=errors)


def open_resource_binary_file(path: str):
    with get_resource_directory(False) as res_dir:
        file = os.path.join(res_dir, path)
        if not os.path.isfile(file):
            return None
        return open(file, "rb")


def read_resource_text_file(
    path: str, encoding: str = "utf-8", errors: str = "strict"
) -> str | None:
    with get_resource_directory(False) as res_dir:
        file = os.path.join(res_dir, path)
        if not os.path.isfile(file):
            return None
        with open(file, "r", encoding=encoding, errors=errors) as f:
            return f.read()


def read_resource_binary_file(path: str) -> bytes | None:
    with get_resource_directory(False) as res_dir:
        file = os.path.join(res_dir, path)
        if not os.path.isfile(file):
            return None
        with open(file, "rb") as f:
            return f.read()


def get_language_file(lang_file: str):
    return get_resource_file(os.path.join(__LANG_PATH, lang_file))


def read_language_file(lang_file: str) -> str | None:
    return read_resource_text_file(os.path.join(__LANG_PATH, lang_file))


def index_of(string: str, rx: QRegularExpression, form_: int):
    m = rx.match(string, form_)
    if m.hasMatch():
        return m.capturedStart()
    return -1


def key_pressed(event: QKeyEvent, *keys) -> bool:
    k = event.key()
    return any(k == key for key in keys)


def has_modifier(event: QKeyEvent, *modifiers) -> bool:
    return any(event.modifiers() == modifier for modifier in modifiers)


def is_shortcut(event: QKeyEvent, modifies, keys) -> bool:
    if not isinstance(modifies, (list, tuple, set)):
        modifies = [modifies]
    if not isinstance(keys, (list, tuple, set)):
        keys = [keys]
    return has_modifier(event, *modifies) and key_pressed(event, *keys)


def load_builtin_language(filename: str) -> QLanguage | None:
    lang_file = get_language_file(filename)
    if not lang_file or not os.path.isfile(lang_file):
        warnings.warn(f"Language file not found: {lang_file}")
        return None
    lang = QLanguage(lang_file)
    if lang.isLoaded():
        return lang
    warnings.warn(f"Language file not loaded: {lang_file}")
    return None
