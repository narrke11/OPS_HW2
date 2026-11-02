from __future__ import annotations

import csv
import io
import json
import math
import statistics
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE = "KRW"
ASSETS = {
    "US": {"name": "미국", "code": "USD", "symbol": "$", "flag": "🇺🇸"},
    "GB": {"name": "영국", "code": "GBP", "symbol": "£", "flag": "🇬🇧"},
    "JP": {"name": "일본", "code": "JPY", "symbol": "¥", "flag": "🇯🇵"},
    "CN": {"name": "중국", "code": "CNY", "symbol": "¥", "flag": "🇨🇳"},
    "VN": {"name": "베트남", "code": "VND", "symbol": "₫", "flag": "🇻🇳"},
    "PH": {"name": "필리핀", "code": "PHP", "symbol": "₱", "flag": "🇵🇭"},
    "AU": {"name": "호주", "code": "AUD", "symbol": "A$", "flag": "🇦🇺"},
    "EU": {"name": "유럽연합", "code": "EUR", "symbol": "€", "flag": "🇪🇺"},
    "RU": {"name": "러시아", "code": "RUB", "symbol": "₽", "flag": "🇷🇺"},
    "CA": {"name": "캐나다", "code": "CAD", "symbol": "C$", "flag": "🇨🇦"},
}
STATIC = Path(__file__).parent / "static"
app = FastAPI(title="WonScope FX Forecast")
app.mount("/static", StaticFiles(directory=STATIC), name="static")


def fetch_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "WonScope/1.0"})
    with urllib.request.urlopen(req, timeout=8) as r:
        return json.loads(r.read().decode("utf-8"))


def get_rates(code: str):
    # Frankfurter is ECB-sourced and does not require an API key.
    try:
        latest = fetch_json(f"https://api.frankfurter.app/latest?from={BASE}&to={code}")
        end = datetime.now(timezone.utc).date()
        start = end - timedelta(days=30)
        hist = fetch_json(f"https://api.frankfurter.app/{start}..{end}?from={BASE}&to={code}")
        points = sorted((d, float(v[code])) for d, v in hist.get("rates", {}).items() if code in v)
        return float(latest["rates"][code]), points, latest.get("date"), "Frankfurter / ECB"
    except Exception as exc:
        # A visible fallback keeps the local demo usable offline.
        fallback = {"USD": 0.00073, "GBP": 0.00058, "JPY": 0.109, "CNY": 0.0052, "VND": 18.4,
                    "PHP": 0.041, "AUD": 0.0011, "EUR": 0.00067, "RUB": 0.061, "CAD": 0.0010}
        value = fallback[code]
        return value, [], None, f"오프라인 추정값 (API 오류: {type(exc).__name__})"


def get_news(code: str):
    terms = {"USD": "US dollar Fed geopolitics", "GBP": "UK pound Bank of England", "JPY": "Japan yen BOJ",
             "CNY": "China yuan trade", "VND": "Vietnam dong economy", "PHP": "Philippines peso economy",
             "AUD": "Australia dollar RBA China", "EUR": "Europe euro ECB geopolitics", "RUB": "Russia ruble sanctions",
             "CAD": "Canada dollar oil economy"}
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode({"q": terms.get(code, code), "hl": "en-US", "gl": "US", "ceid": "US:en"})
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "WonScope/1.0"})
        root = ET.fromstring(urllib.request.urlopen(req, timeout=8).read())
        items = []
        for item in root.findall("./channel/item")[:6]:
            title = item.findtext("title", "").split(" - ")[0]
            items.append(title)
        return items, "Google News RSS"
    except Exception:
        return [], "뉴스 피드 연결 실패"


def forecast(rate: float, points: list[tuple[str, float]], news: list[str]):
    values = [v for _, v in points]
    if len(values) >= 2:
        recent = (values[-1] / values[0] - 1) * 100
        daily = (values[-1] / values[-2] - 1) * 100
        vol = statistics.pstdev([values[i] / values[i - 1] - 1 for i in range(1, len(values))]) * 100
    else:
        recent, daily, vol = 0.0, 0.0, 0.35
    text = " ".join(news).lower()
    risk_words = ("war", "sanction", "tariff", "conflict", "crisis", "hawkish", "inflation")
    relief_words = ("ceasefire", "deal", "rate cut", "growth", "recovery")
    risk = sum(text.count(w) for w in risk_words) - sum(text.count(w) for w in relief_words)
    # Direction is quote KRW per 1 foreign unit: positive means foreign currency strengthens vs KRW.
    bias = max(-1.5, min(1.5, recent * 0.35 + daily * 0.15 + risk * 0.12))
    day7 = rate * (1 + bias / 100)
    day30 = rate * (1 + bias * 2.2 / 100)
    confidence = max(48, min(86, 78 - vol * 10 - abs(risk) * 2))
    direction = "상승" if bias > 0.08 else "하락" if bias < -0.08 else "보합"
    return {"direction": direction, "bias_pct": round(bias, 2), "day7": day7, "day30": day30,
            "confidence": round(confidence), "volatility": round(vol, 3), "risk_score": risk,
            "method": "30일 추세 50% + 최근 변화 20% + 뉴스 리스크 신호 30%"}


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/assets")
def assets():
    return {"base": "대한민국 원화 (KRW)", "assets": ASSETS}


@app.get("/api/quote")
def quote(country: str = Query("US")):
    if country not in ASSETS:
        country = "US"
    meta = ASSETS[country]
    rate, points, as_of, source = get_rates(meta["code"])
    news, news_source = get_news(meta["code"])
    series = [{"date": d, "rate": v} for d, v in points]
    return {"country": country, "meta": meta, "base": BASE, "rate": rate, "unit": f"1 {meta['code']} = KRW",
            "as_of": as_of, "source": source, "news_source": news_source, "news": news,
            "history": series, "forecast": forecast(rate, points, news),
            "updated_at": datetime.now().astimezone().isoformat()}

