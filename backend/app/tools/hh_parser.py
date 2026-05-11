from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional

import httpx
from bs4 import BeautifulSoup
from langchain_core.tools import tool


HH_VACANCY_ID_RE = re.compile(r"/vacancy/(\d+)")


def _is_hh_url(url: str) -> bool:
    u = (url or "").strip().lower()
    return u.startswith("https://hh.ru/") or u.startswith("http://hh.ru/") or u.startswith("https://www.hh.ru/") or u.startswith("http://www.hh.ru/")


def _extract_vacancy_id(url: str) -> Optional[str]:
    m = HH_VACANCY_ID_RE.search(url or "")
    return m.group(1) if m else None


def _skills_from_api(data: Dict[str, Any]) -> list[str]:
    skills = []
    for item in data.get("key_skills") or []:
        name = item.get("name")
        if name:
            skills.append(name)
    return skills


def _strip_html(s: str) -> str:
    if not s:
        return ""
    soup = BeautifulSoup(s, "html.parser")
    return soup.get_text("\n", strip=True)


async def _fetch_via_api(vacancy_id: str) -> Dict[str, Any]:
    url = f"https://api.hh.ru/vacancies/{vacancy_id}"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, headers={"User-Agent": "ai-interview-coach/1.0"})
        resp.raise_for_status()
        return resp.json()


async def _fetch_via_html(url: str) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (compatible; ai-interview-coach/1.0)"})
        resp.raise_for_status()
        html = resp.text

    soup = BeautifulSoup(html, "html.parser")
    title = (soup.find("h1") or {}).get_text(strip=True) if soup.find("h1") else ""
    company = ""
    company_el = soup.select_one('[data-qa="vacancy-company-name"]')
    if company_el:
        company = company_el.get_text(strip=True)

    desc_el = soup.select_one('[data-qa="vacancy-description"]')
    description = desc_el.get_text("\n", strip=True) if desc_el else ""

    return {
        "title": title or "",
        "company": company or "",
        "requirements": "",
        "responsibilities": description or "",
        "skills": [],
        "experience": "",
        "location": "",
        "salary": "",
    }


async def parse_hh_vacancy(url: str) -> dict:
    """
    Best-effort HH vacancy parser.
    - Validate hh.ru URL
    - Extract vacancy ID
    - Try HH API
    - Fallback to HTML parsing
    """
    if not _is_hh_url(url):
        return {"error": "Некорректная ссылка. Поддерживаются только вакансии с hh.ru."}

    vacancy_id = _extract_vacancy_id(url)
    if not vacancy_id:
        return {"error": "Не удалось извлечь ID вакансии из ссылки. Попросите пользователя вставить текст вакансии вручную."}

    try:
        data = await _fetch_via_api(vacancy_id)
        salary = data.get("salary") or {}
        salary_str = ""
        if isinstance(salary, dict) and salary:
            frm = salary.get("from")
            to = salary.get("to")
            cur = salary.get("currency")
            if frm and to:
                salary_str = f"{frm}-{to} {cur}"
            elif frm:
                salary_str = f"from {frm} {cur}"
            elif to:
                salary_str = f"to {to} {cur}"

        experience = (data.get("experience") or {}).get("name") or ""
        address = data.get("address") or {}
        area = (data.get("area") or {}).get("name") or ""
        location = (address.get("city") if isinstance(address, dict) else None) or area

        description = _strip_html(data.get("description") or "")
        # HH API doesn't always separate requirements/responsibilities; keep description as responsibilities.
        return {
            "title": data.get("name") or "",
            "company": (data.get("employer") or {}).get("name") or "",
            "requirements": "",
            "responsibilities": description,
            "skills": _skills_from_api(data),
            "experience": experience,
            "location": location or "",
            "salary": salary_str,
        }
    except Exception:
        try:
            return await _fetch_via_html(url)
        except Exception:
            return {"error": "Не удалось получить данные вакансии. Попросите пользователя вставить текст вакансии вручную."}


@tool
async def hh_vacancy_parser_tool(url: str) -> str:
    """
    Parses a vacancy from hh.ru and returns structured vacancy data (JSON string).
    """
    data = await parse_hh_vacancy(url)
    return json.dumps(data, ensure_ascii=False)

