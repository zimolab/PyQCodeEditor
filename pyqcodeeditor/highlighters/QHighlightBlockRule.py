from __future__ import annotations

from qtpy.QtCore import QRegularExpression


class QHighlightBlockRule(object):
    def __init__(
        self,
        start: QRegularExpression | None = None,
        end: QRegularExpression | None = None,
        f: str | None = None,
    ):
        self.startPattern = start or QRegularExpression()
        self.endPattern = end or QRegularExpression()
        self.formatName = f or ""
