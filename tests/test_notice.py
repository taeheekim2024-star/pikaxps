"""parse_notice(): the JSON contract shared by the desktop app and the website."""
from datetime import date

import pytest

pytest.importorskip("PySide6")

from xpsfit.ui.notice import parse_notice  # noqa: E402


def test_empty_object_means_nothing():
    assert parse_notice("{}") is None
    assert parse_notice("") is None
    assert parse_notice("not json") is None
    assert parse_notice("[1, 2]") is None


def test_basic_notice_and_language():
    raw = '{"id": "rel-0.2", "text": "PikaXPS 0.2 is out", "text_ko": "PikaXPS 0.2 출시", ' \
          '"url": "https://taeheekim2024-star.github.io/pikaxps/download/", "label": "Download", "label_ko": "내려받기"}'
    en = parse_notice(raw, lang="en")
    ko = parse_notice(raw, lang="ko")
    assert en["text"] == "PikaXPS 0.2 is out" and en["label"] == "Download"
    assert ko["text"] == "PikaXPS 0.2 출시" and ko["label"] == "내려받기"
    assert en["id"] == ko["id"] == "rel-0.2"
    assert en["url"].startswith("https://")


def test_non_https_links_are_dropped_and_kind_normalised():
    n = parse_notice('{"text": "x", "url": "http://evil.example", "kind": "weird"}')
    assert n["url"] is None
    assert n["kind"] == "info"


def test_expired_notice_is_hidden():
    raw = '{"text": "old", "until": "2026-01-31"}'
    assert parse_notice(raw, today=date(2026, 2, 1)) is None
    assert parse_notice(raw, today=date(2026, 1, 31)) is not None


def test_text_is_trimmed_to_300_chars():
    n = parse_notice('{"text": "' + "a" * 500 + '"}')
    assert len(n["text"]) == 300
