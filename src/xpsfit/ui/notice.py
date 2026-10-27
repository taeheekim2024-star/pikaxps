"""Project notice bar.

At startup the app fetches ONE small static JSON file from the project site and, if it says
something, shows a dismissible bar above the controls. It is how the project can tell users
about a new release, a paper to cite, a sponsor, or an announcement — without any account,
cookie, tracking, or identifier. An empty object ``{}`` means "nothing to show".

    https://taeheekim2024-star.github.io/pikaxps/notice.json

Fields (all optional except ``text``):
    id        unique string; a dismissed id is not shown again
    text      English text (plain text, ≤ 300 chars)   text_ko   Korean text
    url       https:// link opened by the button        label / label_ko   button caption
    kind      "info" (default) | "update" | "sponsor"   until     "YYYY-MM-DD" — hide after this date

Users can turn the whole thing off from Help ▸ "Show notices from the project".
Network failures are ignored silently (4-second timeout, no retry).
"""
from __future__ import annotations

import json
from datetime import date

from PySide6.QtCore import QSettings, Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget

from .. import APP_NAME, __version__
from .i18n import current_language, t

NOTICE_URL = "https://taeheekim2024-star.github.io/pikaxps/notice.json"
SETTING_ENABLED = "notice/enabled"
SETTING_DISMISSED = "notice/dismissed_id"
KINDS = ("info", "update", "sponsor")


def _settings() -> QSettings:
    return QSettings("xpsfit", "PikaXPS")


def notices_enabled() -> bool:
    value = _settings().value(SETTING_ENABLED, True)
    return str(value).lower() not in ("false", "0", "no")


def set_notices_enabled(on: bool) -> None:
    _settings().setValue(SETTING_ENABLED, bool(on))


def parse_notice(raw: bytes | str, *, lang: str = "en", today: date | None = None) -> dict | None:
    """Turn the JSON file into {id, text, url, label, kind}, or None when there is nothing to show."""
    try:
        data = json.loads(raw if isinstance(raw, str) else raw.decode("utf-8"))
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    text = data.get("text_ko") if lang == "ko" else None
    if not isinstance(text, str) or not text.strip():
        text = data.get("text")
    if not isinstance(text, str) or not text.strip():
        return None
    until = data.get("until")
    if until:
        try:
            if (today or date.today()) > date.fromisoformat(str(until)):
                return None
        except ValueError:
            pass
    url = data.get("url")
    if not (isinstance(url, str) and url.startswith("https://")):
        url = None
    label = data.get("label_ko") if lang == "ko" else None
    if not isinstance(label, str) or not label.strip():
        label = data.get("label") if isinstance(data.get("label"), str) else ""
    kind = str(data.get("kind", "info"))
    if kind not in KINDS:
        kind = "info"
    return {
        "id": str(data.get("id") or text)[:120],
        "text": text.strip()[:300],
        "url": url,
        "label": label.strip()[:40],
        "kind": kind,
    }


class NoticeBar(QFrame):
    """A thin, dismissible bar. Hidden until a notice arrives."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("noticeBar")
        self.setVisible(False)
        self._nam: QNetworkAccessManager | None = None
        self._notice: dict | None = None

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 6, 6, 6)
        lay.setSpacing(10)
        self.label = QLabel()
        self.label.setWordWrap(True)
        self.label.setTextFormat(Qt.TextFormat.PlainText)
        lay.addWidget(self.label, 1)
        self.link_btn = QPushButton()
        self.link_btn.setFlat(True)
        self.link_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.link_btn.clicked.connect(self._open_link)
        lay.addWidget(self.link_btn)
        self.close_btn = QPushButton("✕")
        self.close_btn.setFlat(True)
        self.close_btn.setFixedWidth(28)
        self.close_btn.setToolTip(t("Dismiss this notice", "이 공지 닫기"))
        self.close_btn.clicked.connect(self._dismiss)
        lay.addWidget(self.close_btn)
        self.setStyleSheet(
            "#noticeBar { background: #eef3fd; border: 1px solid #c9d8f5; border-radius: 6px; }"
            "#noticeBar QLabel { color: #1e2a3a; }"
            "#noticeBar QPushButton { color: #1d4ed8; font-weight: 600; border: none; padding: 2px 6px; }"
            "#noticeBar QPushButton:hover { text-decoration: underline; }"
        )

    # -- fetching -------------------------------------------------------------------------
    def start(self) -> None:
        """Begin the (single) background request. Safe to call when disabled or offline."""
        if not notices_enabled():
            return
        try:
            self._nam = QNetworkAccessManager(self)
            req = QNetworkRequest(QUrl(NOTICE_URL))
            req.setHeader(QNetworkRequest.KnownHeaders.UserAgentHeader, f"{APP_NAME}/{__version__}")
            req.setTransferTimeout(4000)
            reply = self._nam.get(req)
            reply.finished.connect(lambda r=reply: self._on_reply(r))
        except Exception:
            pass

    def _on_reply(self, reply: QNetworkReply) -> None:
        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                return
            notice = parse_notice(bytes(reply.readAll().data()), lang=current_language())
            if not notice or _settings().value(SETTING_DISMISSED, "") == notice["id"]:
                return
            self.show_notice(notice)
        except Exception:
            pass
        finally:
            reply.deleteLater()

    # -- display --------------------------------------------------------------------------
    def show_notice(self, notice: dict) -> None:
        self._notice = notice
        prefix = {"update": "🆕 ", "sponsor": "❤️ "}.get(notice.get("kind", "info"), "ℹ️ ")
        self.label.setText(prefix + notice["text"])
        has_link = bool(notice.get("url"))
        self.link_btn.setVisible(has_link)
        if has_link:
            self.link_btn.setText(notice.get("label") or t("Open", "열기"))
        self.setVisible(True)

    def _open_link(self) -> None:
        if self._notice and self._notice.get("url"):
            QDesktopServices.openUrl(QUrl(self._notice["url"]))

    def _dismiss(self) -> None:
        if self._notice:
            _settings().setValue(SETTING_DISMISSED, self._notice["id"])
        self.setVisible(False)
