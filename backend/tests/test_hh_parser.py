import json

import pytest

from app.tools.hh_parser import parse_hh_vacancy


@pytest.mark.asyncio
async def test_hh_parser_invalid_url():
    data = await parse_hh_vacancy("https://example.com/vacancy/123")
    assert "error" in data


@pytest.mark.asyncio
async def test_hh_parser_valid_url_api_ok(monkeypatch):
    async def fake_fetch(vacancy_id: str):
        return {
            "name": "Data Engineer",
            "employer": {"name": "Company"},
            "description": "<b>Hello</b>",
            "key_skills": [{"name": "Python"}, {"name": "SQL"}],
            "experience": {"name": "1–3 года"},
            "area": {"name": "Алматы"},
            "salary": {"from": 100, "to": 200, "currency": "KZT"},
        }

    monkeypatch.setattr("app.tools.hh_parser._fetch_via_api", fake_fetch)
    data = await parse_hh_vacancy("https://hh.ru/vacancy/123456")
    assert data["title"] == "Data Engineer"
    assert data["company"] == "Company"
    assert "Python" in data["skills"]


@pytest.mark.asyncio
async def test_hh_parser_api_error_fallback_html_error(monkeypatch):
    async def fake_fetch(vacancy_id: str):
        raise RuntimeError("api down")

    async def fake_html(url: str):
        raise RuntimeError("blocked")

    monkeypatch.setattr("app.tools.hh_parser._fetch_via_api", fake_fetch)
    monkeypatch.setattr("app.tools.hh_parser._fetch_via_html", fake_html)
    data = await parse_hh_vacancy("https://hh.ru/vacancy/123456")
    assert data.get("error")

