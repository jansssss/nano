"""
정적 HTML 파일 생성 스크립트
web_dashboard.py의 데이터와 템플릿을 사용해 docs/index.html 생성
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from web_dashboard import (
    DASHBOARD_HTML,
    budget_summary,
    income_items,
    expense_nature,
    nanocenter_expense,
    findings,
    recommendations,
)

budget_data = {
    "summary": budget_summary,
    "income": income_items,
    "expense": expense_nature,
    "nanocenter": nanocenter_expense,
    "findings": findings,
    "recommendations": recommendations,
}

data_json = json.dumps(budget_data, ensure_ascii=False)
html = DASHBOARD_HTML.replace('__BUDGET_DATA__', data_json)

os.makedirs('docs', exist_ok=True)
with open('docs/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("docs/index.html 생성 완료!")
