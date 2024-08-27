from __future__ import annotations

from qtpy.QtCore import QRegularExpression


class QHighlightRule(object):
    def __init__(self, p: QRegularExpression | None = None, f: str | None = None):
        self.pattern: QRegularExpression = p or QRegularExpression()
        self.formatName: str = f or ""
