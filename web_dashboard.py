"""
나노센터 예산 분석 웹 대시보드
Flask + SSE + Chart.js 단일 파일 대시보드
"""

import sys
import json
import time
from flask import Flask, Response, jsonify

sys.stdout.reconfigure(encoding='utf-8')

app = Flask(__name__)

# ─── 예산 데이터 ────────────────────────────────────────────────────────────────

budget_summary = {
    "수입": {"사업수익": 1_340_000_000, "자본적수입": 4_000_000_000, "총계": 5_340_000_000, "전년도": 5_295_574_000},
    "지출": {"대행사업비": 4_265_000_000, "일반관리비": 463_280_000, "장비원가": 47_900_000, "임대원가": 21_340_000, "총계": 4_797_520_000, "전년도": 5_492_303_000},
    "차인": {"총계": 542_480_000},
}

income_items = [
    {"항목": "수입 총계",           "예산액": 5_340_000_000, "전년도": 5_295_574_000},
    {"항목": "600 사업수익",         "예산액": 1_340_000_000, "전년도": 1_885_574_000},
    {"항목": "  622 관리사업수익",   "예산액":   940_000_000, "전년도": 1_050_000_000},
    {"항목": "    기타장비활용수익", "예산액":   350_000_000, "전년도":             0},
    {"항목": "    임대료수익",        "예산액":   540_000_000, "전년도":             0},
    {"항목": "    기술료 수익",       "예산액":    50_000_000, "전년도":             0},
    {"항목": "  623 대행사업수익",   "예산액":   300_000_000, "전년도":   735_574_000},
    {"항목": "    직접관리비수익",   "예산액":   265_000_000, "전년도":   569_938_000},
    {"항목": "    기타대행수익",     "예산액":    35_000_000, "전년도":   165_636_000},
    {"항목": "  648 출연금수익",     "예산액":   100_000_000, "전년도":   100_000_000},
    {"항목": "100 자본적 수입",      "예산액": 4_000_000_000, "전년도": 3_410_000_000},
    {"항목": "  176 수탁자산보조금", "예산액": 4_000_000_000, "전년도": 3_410_000_000},
]

expense_nature = [
    # 사업별 대분류
    {"항목": "대행사업비용(A)",               "예산액": 4_265_000_000, "전년도": 5_033_143_000, "구성비": 88.90},
    {"항목": "  초임계원료의약품생산플랫폼(4차)","예산액": 4_000_000_000, "전년도": 3_000_000_000, "구성비": 83.38},
    {"항목": "  2025 디딤돌과제(디아노잔틴)",  "예산액":    45_000_000, "전년도":             0, "구성비":  0.94},
    {"항목": "  2025 광주연구개발특구(유니콘1)","예산액":   175_000_000, "전년도":             0, "구성비":  3.65},
    {"항목": "  국제공동기술개발(귀뚜라미)3차", "예산액":    45_000_000, "전년도":    90_000_000, "구성비":  0.94},
    {"항목": "일반관리비용(C)",               "예산액":   463_280_000, "전년도":   381_160_000, "구성비":  9.66},
    {"항목": "  201 일반운영비",              "예산액":    92_040_000, "전년도":    88_560_000, "구성비":  1.92},
    {"항목": "  202 여비",                   "예산액":    23_040_000, "전년도":    28_800_000, "구성비":  0.48},
    {"항목": "  207 연구개발비",              "예산액":     2_000_000, "전년도":     3_000_000, "구성비":  0.04},
    {"항목": "  213 교육훈련비",              "예산액":     2_800_000, "전년도":     3_400_000, "구성비":  0.06},
    {"항목": "  214 수선유지교체비",           "예산액":    42_800_000, "전년도":    10_000_000, "구성비":  0.89},
    {"항목": "  215 동력비",                  "예산액":   246_000_000, "전년도":   206_000_000, "구성비":  5.13},
    {"항목": "  220 위탁관리비",              "예산액":    41_400_000, "전년도":    41_400_000, "구성비":  0.86},
    {"항목": "  405 자산취득비",              "예산액":     6_000_000, "전년도":             0, "구성비":  0.13},
    {"항목": "  406 기타자본이전(산업재산권)", "예산액":     7_200_000, "전년도":             0, "구성비":  0.15},
    {"항목": "장비사업원가(D)",               "예산액":    47_900_000, "전년도":    62_000_000, "구성비":  1.00},
    {"항목": "  201 일반운영비",              "예산액":     6_100_000, "전년도":     7_200_000, "구성비":  0.13},
    {"항목": "  206 재료비",                  "예산액":    24_000_000, "전년도":    24_000_000, "구성비":  0.50},
    {"항목": "  213 교육훈련비",              "예산액":     2_800_000, "전년도":       800_000, "구성비":  0.06},
    {"항목": "  214 수선유지교체비",           "예산액":    15_000_000, "전년도":    30_000_000, "구성비":  0.31},
    {"항목": "임대사업원가(F)",               "예산액":    21_340_000, "전년도":    16_000_000, "구성비":  0.45},
    {"항목": "  201 일반운영비",              "예산액":     6_500_000, "전년도":     6_500_000, "구성비":  0.14},
    {"항목": "  202 여비",                   "예산액":     3_840_000, "전년도":             0, "구성비":  0.08},
    {"항목": "  213 교육훈련비",              "예산액":     4_000_000, "전년도":     2_500_000, "구성비":  0.08},
    {"항목": "  기타",                        "예산액":     7_000_000, "전년도":     7_000_000, "구성비":  0.15},
]

nanocenter_expense = [
    {"항목": "대행사업비용(A)", "예산액": 4_265_000_000, "전년도": 5_033_143_000},
    {"항목": "목적사업비용(B)", "예산액":             0, "전년도":             0},
    {"항목": "일반관리비용(C)", "예산액":   463_280_000, "전년도":   381_160_000},
    {"항목": "장비사업원가(D)", "예산액":    47_900_000, "전년도":    62_000_000},
    {"항목": "분석사업원가(E)", "예산액":             0, "전년도":             0},
    {"항목": "임대사업원가(F)", "예산액":    21_340_000, "전년도":    16_000_000},
]

findings = [
    {"수준": "긍정", "제목": "수입 > 지출: 나노센터 예산 흑자", "내용": "수입 총계 53.4억원 vs 지출 48.0억원 → 차인 +5.4억원 흑자. 자체 운영 예산 범위 내 재정 균형이 유지되고 있습니다."},
    {"수준": "경고", "제목": "대행사업비 집중도 88.9%", "내용": "지출의 88.9%(42.7억)가 대행사업비(수탁과제)에 집중. 초임계플랫폼(40억) 단일 사업 의존도 83.4%로 사업 차질 시 전체 예산에 심각한 영향이 예상됩니다."},
    {"수준": "경고", "제목": "대행사업비 -15.3% 감소", "내용": "대행사업비용 42.7억원 (전년 50.3억원). 신규 과제(디딤돌·광주특구·귀뚜라미)가 추가되었으나 총액은 전년 대비 7.7억원 감소하였습니다."},
    {"수준": "주의", "제목": "관리비 내 동력비 비중 53.2%", "내용": "일반관리비(4.6억) 중 동력비가 2.46억(53.2%)으로 압도적 1위. 에너지 비용 관리가 운영 효율화의 핵심 과제입니다."},
    {"수준": "주의", "제목": "수선유지교체비 4.3배 급증", "내용": "일반관리비 내 수선유지비 4,280만원 (전년 1,000만원, +328%). 장비 노후화에 따른 유지보수 비용 증가 추세가 확인됩니다."},
    {"수준": "긍정", "제목": "일반관리비용 +21.5% 증가", "내용": "일반관리비용 4.6억원 (전년 3.8억원). 센터 자체 운영역량 강화 신호. 동력비 증가(+4,000만)는 시설 가동률 향상을 의미합니다."},
    {"수준": "긍정", "제목": "임대사업원가 +33.4% 증가", "내용": "임대사업원가 2,134만원 (전년 1,600만원). 임대 사업 확대 추세. 임대료 수익(5.4억)과 연계한 수익성 개선 가능성이 있습니다."},
]

recommendations = [
    {"우선순위": "즉시 조치", "제목": "초임계플랫폼 사업 리스크 헷지 계획 수립", "내용": "지출의 83.4%(40억)가 단일 사업에 집중. 2026년 이후 사업 종료 시 대체 수탁과제 확보 전략을 즉시 수립하고 신규 과제 파이프라인을 점검하세요."},
    {"우선순위": "즉시 조치", "제목": "수탁과제 수주 확대 (대행사업비 -15.3% 대응)", "내용": "대행사업비 전년 대비 7.7억원 감소. 정부 R&D, 지자체 위탁, 기업 기술개발 지원 등 신규 과제 수주를 상반기 내 집중 추진하세요."},
    {"우선순위": "단기 계획", "제목": "동력비 에너지 효율화 투자 검토", "내용": "동력비 2.46억원이 관리비의 53% 차지. ESG 연계 에너지 효율화 설비 또는 스마트에너지관리 시스템 도입으로 중기(3년) 10-15% 절감 목표를 수립하세요."},
    {"우선순위": "단기 계획", "제목": "자체 수입 다변화", "내용": "관리사업수익(9.4억)이 전년(10.5억) 대비 -1.1억 감소. 기타장비활용수익(3.5억), 임대료수익(5.4억) 등 신규 수익원 확대 및 수탁과제 영업을 강화하세요."},
    {"우선순위": "단기 계획", "제목": "장비 노후화 선제 대응", "내용": "수선유지비가 전년 1,000만원 → 4,280만원으로 4.3배 급증. 장비 이력 관리 대장을 정비하고 중기 자본지출(장비교체) 계획을 수립하세요."},
    {"우선순위": "중장기 전략", "제목": "나노센터 독립 수익모델 구축", "내용": "현재 수입의 74.9%가 수탁자산보조금(자본적 수입). 기술이전·분석서비스·임대수익 확대를 통해 2030년까지 자체 사업수익 20억원 목표를 설정하세요."},
    {"우선순위": "중장기 전략", "제목": "과제 포트폴리오 다각화", "내용": "현재 수탁과제가 4건에 집중. 바이오·나노·환경 분야 다부처 과제를 발굴하여 5년 내 과제 수 2배, 수익 1.5배 달성을 목표로 설정하세요."},
]

# ─── SSE 스트림 메시지 ───────────────────────────────────────────────────────────

SSE_STEPS = [
    (1,  "엑셀 파일 로딩 중..."),
    (2,  "예산 총괄표 분석 중..."),
    (3,  "수입예산 과목별 파싱 중..."),
    (4,  "지출예산 성질별 데이터 처리 중..."),
    (5,  "나노센터 직접 지출 분석 중..."),
    (6,  "핵심 재무 지표 계산 중..."),
    (7,  "전년 대비 증감률 산출 중..."),
    (8,  "위험 요인 분석 중..."),
    (9,  "전략적 제언 생성 중..."),
    (10, "대시보드 렌더링 완료!"),
]

# ─── HTML 템플릿 ────────────────────────────────────────────────────────────────

DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>나노센터 예산 분석 대시보드 2026</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg:        #0f0f1a;
    --card:      #1a1a2e;
    --card2:     #16213e;
    --accent:    #00d2ff;
    --danger:    #ff6b6b;
    --warning:   #feca57;
    --positive:  #00cec9;
    --text:      #e0e0e0;
    --text-dim:  #8888aa;
    --border:    #2a2a4a;
    --radius:    12px;
  }

  html { scroll-behavior: smooth; }

  body {
    font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    line-height: 1.6;
  }

  /* ── Header ── */
  .header {
    background: linear-gradient(135deg, #0d1b2a 0%, #1a1a2e 50%, #0d2137 100%);
    border-bottom: 1px solid var(--border);
    padding: 28px 32px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 16px;
  }
  .header-left h1 {
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--accent);
    letter-spacing: -0.5px;
  }
  .header-left p {
    font-size: 0.85rem;
    color: var(--text-dim);
    margin-top: 4px;
  }
  .header-badges {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
  }
  .badge {
    padding: 5px 14px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
    border: 1px solid;
  }
  .badge-blue  { color: var(--accent);   border-color: var(--accent);   background: rgba(0,210,255,0.08); }
  .badge-red   { color: var(--danger);   border-color: var(--danger);   background: rgba(255,107,107,0.08); }
  .badge-green { color: var(--positive); border-color: var(--positive); background: rgba(0,206,201,0.08); }

  /* ── Loading Panel ── */
  #loading-panel {
    max-width: 720px;
    margin: 40px auto;
    padding: 0 24px;
  }
  .loading-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 32px;
  }
  .loading-title {
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--accent);
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .spinner {
    width: 18px; height: 18px;
    border: 2px solid rgba(0,210,255,0.2);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    flex-shrink: 0;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  .progress-wrap {
    background: rgba(255,255,255,0.06);
    border-radius: 8px;
    height: 10px;
    overflow: hidden;
    margin-bottom: 20px;
  }
  .progress-bar {
    height: 100%;
    background: linear-gradient(90deg, #0072ff, #00d2ff);
    border-radius: 8px;
    transition: width 0.4s ease;
    width: 0%;
  }
  .progress-label {
    font-size: 0.8rem;
    color: var(--text-dim);
    text-align: right;
    margin-top: -14px;
    margin-bottom: 16px;
  }
  .log-box {
    background: rgba(0,0,0,0.3);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px;
    max-height: 220px;
    overflow-y: auto;
    font-family: 'Courier New', monospace;
    font-size: 0.82rem;
  }
  .log-line {
    padding: 3px 0;
    color: var(--text-dim);
    display: flex;
    gap: 10px;
    align-items: flex-start;
  }
  .log-line.active { color: var(--accent); }
  .log-line.done   { color: var(--positive); }
  .log-step { color: #4a4a6a; flex-shrink: 0; }

  /* ── Main Dashboard ── */
  #dashboard {
    display: none;
    padding: 28px 32px 48px;
    max-width: 1400px;
    margin: 0 auto;
  }

  /* ── KPI Grid ── */
  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 24px;
  }
  @media (max-width: 900px) { .kpi-grid { grid-template-columns: repeat(2, 1fr); } }
  @media (max-width: 520px) { .kpi-grid { grid-template-columns: 1fr; } }

  .kpi-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 22px 20px;
    position: relative;
    overflow: hidden;
    transition: transform 0.2s, box-shadow 0.2s;
  }
  .kpi-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 30px rgba(0,0,0,0.3);
  }
  .kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
  }
  .kpi-blue::before   { background: var(--accent); }
  .kpi-red::before    { background: var(--danger); }
  .kpi-orange::before { background: #ff9f43; }
  .kpi-yellow::before { background: var(--warning); }

  .kpi-label {
    font-size: 0.78rem;
    color: var(--text-dim);
    font-weight: 500;
    margin-bottom: 10px;
    letter-spacing: 0.3px;
  }
  .kpi-value {
    font-size: 1.85rem;
    font-weight: 700;
    line-height: 1.1;
    margin-bottom: 6px;
  }
  .kpi-blue   .kpi-value { color: var(--accent); }
  .kpi-red    .kpi-value { color: var(--danger); }
  .kpi-orange .kpi-value { color: #ff9f43; }
  .kpi-yellow .kpi-value { color: var(--warning); }
  .kpi-sub {
    font-size: 0.75rem;
    color: var(--text-dim);
  }
  .kpi-icon {
    position: absolute;
    top: 18px; right: 18px;
    font-size: 1.8rem;
    opacity: 0.15;
  }

  /* ── Section Title ── */
  .section-title {
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--text);
    margin-bottom: 16px;
    padding-bottom: 10px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .section-title span.dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: var(--accent);
    display: inline-block;
  }

  /* ── Chart Grid ── */
  .chart-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-bottom: 24px;
  }
  @media (max-width: 800px) { .chart-grid { grid-template-columns: 1fr; } }

  .chart-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 22px;
  }
  .chart-card .chart-title {
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--text-dim);
    margin-bottom: 18px;
    letter-spacing: 0.2px;
  }
  .chart-wrap {
    position: relative;
    width: 100%;
  }
  .chart-wrap.pie-wrap  { height: 280px; }
  .chart-wrap.bar-wrap  { height: 320px; }
  .chart-wrap.bar-wrap2 { height: 380px; }

  /* ── Table ── */
  .table-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 22px;
    margin-bottom: 24px;
    overflow-x: auto;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.83rem;
  }
  thead th {
    text-align: right;
    padding: 10px 12px;
    font-weight: 600;
    color: var(--text-dim);
    border-bottom: 1px solid var(--border);
    white-space: nowrap;
  }
  thead th:first-child { text-align: left; }
  tbody tr {
    border-bottom: 1px solid rgba(255,255,255,0.04);
    transition: background 0.15s;
  }
  tbody tr:hover { background: rgba(0,210,255,0.04); }
  tbody td {
    padding: 9px 12px;
    text-align: right;
    white-space: nowrap;
  }
  tbody td:first-child { text-align: left; color: var(--text); }
  .num-pos { color: #4cd137; }
  .num-neg { color: var(--danger); }
  .num-neutral { color: var(--text-dim); }
  .indent1 { padding-left: 20px !important; }
  .indent2 { padding-left: 36px !important; }
  .row-total { font-weight: 700; background: rgba(0,210,255,0.05); }

  /* ── Findings ── */
  .findings-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 14px;
    margin-bottom: 24px;
  }
  .finding-card {
    background: var(--card);
    border-radius: var(--radius);
    padding: 18px 20px;
    border-left: 4px solid;
    transition: transform 0.2s;
  }
  .finding-card:hover { transform: translateY(-2px); }
  .finding-card.danger   { border-color: var(--danger);   background: linear-gradient(135deg, #1a1a2e, #2a1a1a); }
  .finding-card.warning  { border-color: var(--warning);  background: linear-gradient(135deg, #1a1a2e, #2a2210); }
  .finding-card.positive { border-color: var(--positive); background: linear-gradient(135deg, #1a1a2e, #0e2a2a); }
  .finding-level {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 1px;
    padding: 2px 10px;
    border-radius: 20px;
    display: inline-block;
    margin-bottom: 10px;
  }
  .finding-card.danger   .finding-level { background: rgba(255,107,107,0.2); color: var(--danger); }
  .finding-card.warning  .finding-level { background: rgba(254,202,87,0.2);  color: var(--warning); }
  .finding-card.positive .finding-level { background: rgba(0,206,201,0.2);   color: var(--positive); }
  .finding-title {
    font-size: 0.92rem;
    font-weight: 600;
    color: var(--text);
    margin-bottom: 8px;
  }
  .finding-body {
    font-size: 0.82rem;
    color: var(--text-dim);
    line-height: 1.7;
  }

  /* ── Recommendations ── */
  .rec-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
    gap: 14px;
    margin-bottom: 24px;
  }
  .rec-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 18px 20px;
    transition: transform 0.2s, border-color 0.2s;
  }
  .rec-card:hover {
    transform: translateY(-2px);
    border-color: rgba(0,210,255,0.3);
  }
  .rec-badge {
    font-size: 0.7rem;
    font-weight: 700;
    padding: 3px 12px;
    border-radius: 20px;
    display: inline-block;
    margin-bottom: 10px;
    letter-spacing: 0.5px;
  }
  .badge-immediate { background: rgba(255,107,107,0.2); color: var(--danger); border: 1px solid rgba(255,107,107,0.4); }
  .badge-short     { background: rgba(254,202,87,0.2);  color: var(--warning); border: 1px solid rgba(254,202,87,0.4); }
  .badge-long      { background: rgba(0,210,255,0.15);  color: var(--accent);  border: 1px solid rgba(0,210,255,0.3); }
  .rec-title {
    font-size: 0.92rem;
    font-weight: 600;
    color: var(--text);
    margin-bottom: 8px;
  }
  .rec-body {
    font-size: 0.82rem;
    color: var(--text-dim);
    line-height: 1.7;
  }

  /* ── Footer ── */
  .footer {
    text-align: center;
    padding: 24px;
    color: var(--text-dim);
    font-size: 0.78rem;
    border-top: 1px solid var(--border);
    margin-top: 16px;
  }

  /* ── Scrollbar ── */
  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: var(--bg); }
  ::-webkit-scrollbar-thumb { background: #2a2a4a; border-radius: 3px; }
  ::-webkit-scrollbar-thumb:hover { background: #3a3a6a; }
</style>
</head>
<body>

<!-- ════════════════════════════════════════════════
     HEADER
════════════════════════════════════════════════ -->
<header class="header">
  <div class="header-left">
    <h1>나노센터 예산 분석 대시보드</h1>
    <p>2026년도 예산 vs 전년도 비교 분석 &nbsp;|&nbsp; 생성일: 2026-02-19</p>
  </div>
  <div class="header-badges">
    <span class="badge badge-blue">2026 예산 (나노센터 전용)</span>
    <span class="badge badge-green">흑자 +5.4억</span>
    <span class="badge badge-green">실시간 분석</span>
  </div>
</header>

<!-- ════════════════════════════════════════════════
     LOADING PANEL
════════════════════════════════════════════════ -->
<div id="loading-panel">
  <div class="loading-card">
    <div class="loading-title">
      <div class="spinner" id="spin"></div>
      <span>예산 데이터 분석 중...</span>
    </div>
    <div class="progress-wrap">
      <div class="progress-bar" id="prog-bar"></div>
    </div>
    <div class="progress-label" id="prog-label">0 / 10</div>
    <div class="log-box" id="log-box"></div>
  </div>
</div>

<!-- ════════════════════════════════════════════════
     MAIN DASHBOARD (hidden until stream completes)
════════════════════════════════════════════════ -->
<div id="dashboard">

  <!-- KPI Cards -->
  <div class="kpi-grid">
    <div class="kpi-card kpi-blue">
      <div class="kpi-label">총 수입</div>
      <div class="kpi-value">53.4억</div>
      <div class="kpi-sub">전년도 52.9억 대비 +0.8%</div>
      <div class="kpi-icon">&#128200;</div>
    </div>
    <div class="kpi-card kpi-red">
      <div class="kpi-label">총 지출 (나노센터 전용)</div>
      <div class="kpi-value">48.0억</div>
      <div class="kpi-sub">전년도 54.9억 대비 -12.7%</div>
      <div class="kpi-icon">&#128201;</div>
    </div>
    <div class="kpi-card kpi-orange">
      <div class="kpi-label">차인 (수입 - 지출)</div>
      <div class="kpi-value">+5.4억</div>
      <div class="kpi-sub">나노센터 기준 흑자 구조</div>
      <div class="kpi-icon">&#10003;</div>
    </div>
    <div class="kpi-card kpi-yellow">
      <div class="kpi-label">자급률 (사업수익/지출)</div>
      <div class="kpi-value">27.9%</div>
      <div class="kpi-sub">대행사업비 집중도 88.9%</div>
      <div class="kpi-icon">&#128268;</div>
    </div>
  </div>

  <!-- Chart Row 1 -->
  <div class="chart-grid">
    <div class="chart-card">
      <div class="chart-title">수입 구조 파이차트 (억원)</div>
      <div class="chart-wrap pie-wrap">
        <canvas id="chart-income"></canvas>
      </div>
    </div>
    <div class="chart-card">
      <div class="chart-title">나노센터 지출 사업별 비교 (억원)</div>
      <div class="chart-wrap bar-wrap">
        <canvas id="chart-expense-top10"></canvas>
      </div>
    </div>
  </div>

  <!-- Chart Row 2 -->
  <div class="chart-grid">
    <div class="chart-card">
      <div class="chart-title">지출 구성비 도넛차트 (나노센터 48억 기준)</div>
      <div class="chart-wrap pie-wrap">
        <canvas id="chart-composition"></canvas>
      </div>
    </div>
    <div class="chart-card">
      <div class="chart-title">전년 대비 증감률 (주요 항목)</div>
      <div class="chart-wrap bar-wrap">
        <canvas id="chart-yoy"></canvas>
      </div>
    </div>
  </div>

  <!-- Income Table -->
  <div class="table-card">
    <div class="section-title"><span class="dot"></span>수입예산 상세</div>
    <table id="tbl-income">
      <thead>
        <tr>
          <th>과목명</th>
          <th>2025 예산</th>
          <th>전년도</th>
          <th>증감</th>
          <th>비중</th>
        </tr>
      </thead>
      <tbody id="tbl-income-body"></tbody>
    </table>
  </div>

  <!-- Expense Table -->
  <div class="table-card">
    <div class="section-title"><span class="dot"></span>나노센터 지출 사업별·성질별 상세</div>
    <table id="tbl-expense">
      <thead>
        <tr>
          <th>과목명</th>
          <th>2025예산 (억)</th>
          <th>전년도 (억)</th>
          <th>증감 (억)</th>
          <th>구성비 %</th>
          <th>전년比 %</th>
        </tr>
      </thead>
      <tbody id="tbl-expense-body"></tbody>
    </table>
  </div>

  <!-- Findings -->
  <div class="section-title" style="margin-bottom:16px;"><span class="dot" style="background:var(--danger)"></span>위험 요인 분석</div>
  <div class="findings-grid" id="findings-grid"></div>

  <!-- Recommendations -->
  <div class="section-title" style="margin-bottom:16px;"><span class="dot" style="background:var(--positive)"></span>전략적 제언</div>
  <div class="rec-grid" id="rec-grid"></div>

</div><!-- /#dashboard -->

<footer class="footer">
  나노센터 예산 분석 시스템 &nbsp;|&nbsp; 2026년도 예산 기준 &nbsp;|&nbsp; Flask + Chart.js
</footer>

<!-- ════════════════════════════════════════════════
     JAVASCRIPT
════════════════════════════════════════════════ -->
<script>
/* ── Utility ── */
const fmt = (v, unit='원') => {
  if (v === 0) return '-';
  const abs = Math.abs(v);
  const sign = v < 0 ? '-' : '';
  if (abs >= 1e8) return sign + (abs / 1e8).toFixed(1) + '억' + unit;
  if (abs >= 1e4) return sign + (abs / 1e4).toFixed(0) + '만' + unit;
  return sign + abs.toLocaleString() + unit;
};
const fmtB = v => v === 0 ? '-' : (v / 1e8).toFixed(2);   // 억 단위 소수 2자리
const pct  = (cur, prev) => prev === 0 ? null : ((cur - prev) / prev * 100);
const pctStr = (cur, prev) => {
  if (prev === 0) return '<span class="num-pos">신규</span>';
  const p = pct(cur, prev);
  const s = p >= 0 ? '+' : '';
  const cls = p >= 0 ? 'num-pos' : 'num-neg';
  return `<span class="${cls}">${s}${p.toFixed(1)}%</span>`;
};
const diffStr = (cur, prev) => {
  const d = cur - prev;
  if (d === 0) return '<span class="num-neutral">-</span>';
  const cls = d > 0 ? 'num-pos' : 'num-neg';
  return `<span class="${cls}">${fmtB(d)}</span>`;
};

/* ── Data (embedded from Python) ── */
const DATA = __BUDGET_DATA__;

/* ── SSE Stream ── */
const progBar   = document.getElementById('prog-bar');
const progLabel = document.getElementById('prog-label');
const logBox    = document.getElementById('log-box');
const spinner   = document.getElementById('spin');

function addLog(step, total, msg, isDone) {
  // mark previous active as done
  document.querySelectorAll('.log-line.active').forEach(el => {
    el.classList.remove('active');
    el.classList.add('done');
    el.querySelector('.log-ico').textContent = '✔';
  });

  const line = document.createElement('div');
  line.className = 'log-line' + (isDone ? ' done' : ' active');
  line.innerHTML = `<span class="log-step">[${String(step).padStart(2,' ')}/${total}]</span>
                    <span class="log-ico">${isDone ? '✔' : '▶'}</span>
                    <span>${msg}</span>`;
  logBox.appendChild(line);
  logBox.scrollTop = logBox.scrollHeight;
}

const STEPS = [
  "엑셀 파일 로딩 중...",
  "예산 총괄표 분석 중...",
  "수입예산 과목별 파싱 중...",
  "지출예산 성질별 데이터 처리 중...",
  "나노센터 직접 지출 분석 중...",
  "핵심 재무 지표 계산 중...",
  "전년 대비 증감률 산출 중...",
  "위험 요인 분석 중...",
  "전략적 제언 생성 중...",
  "대시보드 렌더링 완료!",
];
let currentStep = 0;
const timer = setInterval(() => {
  currentStep++;
  const pct = (currentStep / STEPS.length * 100).toFixed(0);
  progBar.style.width = pct + '%';
  progLabel.textContent = `${currentStep} / ${STEPS.length}`;
  addLog(currentStep, STEPS.length, STEPS[currentStep - 1], currentStep === STEPS.length);

  if (currentStep >= STEPS.length) {
    clearInterval(timer);
    spinner.style.display = 'none';
    setTimeout(() => {
      document.getElementById('loading-panel').style.display = 'none';
      const dash = document.getElementById('dashboard');
      dash.style.display = 'block';
      dash.style.opacity = '0';
      dash.style.transition = 'opacity 0.6s ease';
      requestAnimationFrame(() => { dash.style.opacity = '1'; });
      initDashboard();
    }, 600);
  }
}, 350);

/* ── Dashboard Init ── */
function initDashboard() {
  buildIncomeTbl();
  buildExpenseTbl();
  buildFindings();
  buildRecs();
  buildCharts();
}

/* ── Income Table ── */
function buildIncomeTbl() {
  const totalBudget = DATA.income.reduce((s,r) => r['항목']==='수입 총계' ? r['예산액'] : s, 0);
  const tbody = document.getElementById('tbl-income-body');
  DATA.income.forEach(row => {
    const name = row['항목'];
    const cur  = row['예산액'];
    const prev = row['전년도'];
    const diff = cur - prev;
    const ratio = totalBudget > 0 ? (cur / totalBudget * 100).toFixed(1) + '%' : '-';

    let indent = '';
    if (name.startsWith('    ')) indent = 'indent2';
    else if (name.startsWith('  ')) indent = 'indent1';
    const isTotal = name === '수입 총계';

    const tr = document.createElement('tr');
    if (isTotal) tr.classList.add('row-total');
    tr.innerHTML = `
      <td class="${indent}">${name.trim()}</td>
      <td>${fmt(cur)}</td>
      <td class="num-neutral">${prev === 0 ? '-' : fmt(prev)}</td>
      <td>${prev === 0 ? '<span class="num-pos">신규</span>' : diffStr(cur, prev)}</td>
      <td class="num-neutral">${isTotal ? '100%' : ratio}</td>`;
    tbody.appendChild(tr);
  });
}

/* ── Expense Table ── */
function buildExpenseTbl() {
  const tbody = document.getElementById('tbl-expense-body');
  DATA.expense.forEach(row => {
    const name = row['항목'];
    const cur  = row['예산액'];
    const prev = row['전년도'];
    const comp = row['구성비'];

    let indentClass = '';
    if (name.startsWith('  ')) indentClass = 'indent1';
    const isParent = !name.startsWith('  ');

    const tr = document.createElement('tr');
    if (isParent) tr.style.background = 'rgba(0,210,255,0.04)';
    tr.innerHTML = `
      <td class="${indentClass}" style="${isParent ? 'font-weight:600;color:var(--text)' : ''}">${name.trim()}</td>
      <td>${fmtB(cur)}</td>
      <td class="num-neutral">${prev === 0 ? '-' : fmtB(prev)}</td>
      <td>${prev === 0 ? '<span class="num-pos">신규</span>' : diffStr(cur, prev)}</td>
      <td class="num-neutral">${comp.toFixed(2)}%</td>
      <td>${prev === 0 ? '<span class="num-pos">신규</span>' : pctStr(cur, prev)}</td>`;
    tbody.appendChild(tr);
  });
}

/* ── Findings ── */
function buildFindings() {
  const grid = document.getElementById('findings-grid');
  const classMap = { '경고': 'danger', '주의': 'warning', '긍정': 'positive' };
  DATA.findings.forEach(f => {
    const cls = classMap[f['수준']] || 'warning';
    const div = document.createElement('div');
    div.className = `finding-card ${cls}`;
    div.innerHTML = `
      <span class="finding-level">${f['수준']}</span>
      <div class="finding-title">${f['제목']}</div>
      <div class="finding-body">${f['내용']}</div>`;
    grid.appendChild(div);
  });
}

/* ── Recommendations ── */
function buildRecs() {
  const grid = document.getElementById('rec-grid');
  const badgeMap = { '즉시 조치': 'badge-immediate', '단기 계획': 'badge-short', '중장기 전략': 'badge-long' };
  DATA.recommendations.forEach(r => {
    const bc = badgeMap[r['우선순위']] || 'badge-long';
    const div = document.createElement('div');
    div.className = 'rec-card';
    div.innerHTML = `
      <span class="rec-badge ${bc}">${r['우선순위']}</span>
      <div class="rec-title">${r['제목']}</div>
      <div class="rec-body">${r['내용']}</div>`;
    grid.appendChild(div);
  });
}

/* ── Chart.js global defaults ── */
Chart.defaults.color = '#8888aa';
Chart.defaults.borderColor = 'rgba(255,255,255,0.06)';
Chart.defaults.font.family = "'Noto Sans KR', 'Malgun Gothic', sans-serif";
Chart.defaults.font.size = 11;

function buildCharts() {
  buildIncomeChart();
  buildTop10Chart();
  buildCompositionChart();
  buildYoYChart();
}

/* Chart 1: 수입 구조 도넛 */
function buildIncomeChart() {
  const ctx = document.getElementById('chart-income').getContext('2d');
  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['관리사업수익', '대행사업수익', '출연금수익', '수탁자산보조금(자본)'],
      datasets: [{
        data: [940, 300, 100, 4000],
        backgroundColor: ['rgba(0,210,255,0.8)', 'rgba(0,206,201,0.8)', 'rgba(85,239,196,0.8)', 'rgba(116,185,255,0.8)'],
        borderColor: '#1a1a2e',
        borderWidth: 3,
        hoverOffset: 12,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '62%',
      plugins: {
        legend: { position: 'bottom', labels: { padding: 16, color: '#c0c0d8', boxWidth: 14 } },
        tooltip: {
          callbacks: {
            label: (ctx) => ` ${ctx.label}: ${ctx.parsed.toLocaleString()}백만원`
          }
        }
      }
    }
  });
}

/* Chart 2: 나노센터 지출 사업별 비교 수평막대 */
function buildTop10Chart() {
  // 대분류 항목만 (들여쓰기 없는 항목)
  const topItems = DATA.expense.filter(r => !r['항목'].startsWith('  '));
  const top10 = topItems.slice().sort((a,b) => b['예산액'] - a['예산액']).slice(0,10);
  const labels = top10.map(r => r['항목']);
  const cur25  = top10.map(r => +(r['예산액'] / 1e8).toFixed(2));
  const prev   = top10.map(r => +(r['전년도'] / 1e8).toFixed(2));

  const ctx = document.getElementById('chart-expense-top10').getContext('2d');
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        { label: '2025예산', data: cur25, backgroundColor: 'rgba(0,210,255,0.7)', borderRadius: 4, borderSkipped: false },
        { label: '전년도',   data: prev,  backgroundColor: 'rgba(255,107,107,0.5)', borderRadius: 4, borderSkipped: false },
      ]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom', labels: { color: '#c0c0d8', boxWidth: 14, padding: 14 } },
        tooltip: { callbacks: { label: (c) => ` ${c.dataset.label}: ${c.parsed.x}억원` } }
      },
      scales: {
        x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { callback: v => v + '억' } },
        y: { grid: { display: false }, ticks: { color: '#c0c0d8' } }
      }
    }
  });
}

/* Chart 3: 지출 구성비 도넛 (나노센터 48억 기준) */
function buildCompositionChart() {
  const groups = [
    { label: '초임계플랫폼',  value: 83.38 },
    { label: '광주특구',      value:  3.65 },
    { label: '디딤돌과제',    value:  0.94 },
    { label: '귀뚜라미과제',  value:  0.94 },
    { label: '동력비(관리)',  value:  5.13 },
    { label: '일반운영비(관리)', value: 1.92 },
    { label: '수선유지비',    value:  1.20 },
    { label: '장비원가',      value:  1.00 },
    { label: '기타',          value:  1.84 },
  ];
  const palette = [
    'rgba(0,210,255,0.85)', 'rgba(0,206,201,0.85)', 'rgba(116,185,255,0.85)',
    'rgba(162,155,254,0.85)', 'rgba(253,203,110,0.85)', 'rgba(255,107,107,0.85)',
    'rgba(0,184,148,0.85)', 'rgba(255,159,64,0.85)', 'rgba(99,110,114,0.7)',
  ];
  const ctx = document.getElementById('chart-composition').getContext('2d');
  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: groups.map(g => g.label),
      datasets: [{
        data: groups.map(g => g.value),
        backgroundColor: palette,
        borderColor: '#1a1a2e',
        borderWidth: 2,
        hoverOffset: 10,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '55%',
      plugins: {
        legend: { position: 'bottom', labels: { padding: 12, color: '#c0c0d8', boxWidth: 12 } },
        tooltip: { callbacks: { label: (c) => ` ${c.label}: ${c.parsed}%` } }
      }
    }
  });
}

/* Chart 4: 전년比 증감률 수평막대 (나노센터 대분류 기준) */
function buildYoYChart() {
  const items = DATA.expense
    .filter(r => !r['항목'].startsWith('  ') && r['전년도'] > 0)
    .map(r => ({
      label: r['항목'],
      yoy: +((r['예산액'] - r['전년도']) / r['전년도'] * 100).toFixed(1),
    })).sort((a, b) => a.yoy - b.yoy);

  const labels = items.map(i => i.label);
  const values = items.map(i => i.yoy);
  const colors = values.map(v => v >= 0 ? 'rgba(0,210,255,0.75)' : 'rgba(255,107,107,0.75)');

  const ctx = document.getElementById('chart-yoy').getContext('2d');
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: '전년 대비 증감률 (%)',
        data: values,
        backgroundColor: colors,
        borderRadius: 4,
        borderSkipped: false,
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: (c) => ` ${c.parsed.x >= 0 ? '+' : ''}${c.parsed.x}%` } }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255,255,255,0.05)' },
          ticks: { callback: v => v + '%' },
          afterDataLimits: (axis) => { axis.max = Math.max(axis.max, 20); axis.min = Math.min(axis.min, -20); }
        },
        y: { grid: { display: false }, ticks: { color: '#c0c0d8', font: { size: 10 } } }
      }
    }
  });
}
</script>
</body>
</html>
"""

# ─── Flask 라우트 ────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    """메인 대시보드 HTML 반환 (모든 데이터 인라인 embed)"""
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
    return html, 200, {'Content-Type': 'text/html; charset=utf-8'}


@app.route('/stream')
def stream():
    """SSE 엔드포인트: 분석 단계를 순차 스트리밍"""
    def generate():
        total = len(SSE_STEPS)
        for step, message in SSE_STEPS:
            is_done = (step == total)
            payload = json.dumps({
                "step": step,
                "total": total,
                "message": message,
                "done": is_done,
            }, ensure_ascii=False)
            yield f"data: {payload}\n\n"
            time.sleep(0.35)

    return Response(
        generate(),
        content_type='text/event-stream; charset=utf-8',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive',
        }
    )


@app.route('/api/data')
def api_data():
    """전체 예산 데이터 JSON 반환"""
    return jsonify({
        "summary": budget_summary,
        "income": income_items,
        "expense": expense_nature,
        "nanocenter": nanocenter_expense,
        "findings": findings,
        "recommendations": recommendations,
    })


# ─── 진입점 ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print()
    print("  나노센터 예산 분석 웹 대시보드")
    print("  http://localhost:5000 에서 접근하세요")
    print("  종료: Ctrl+C")
    print()
    app.run(host='0.0.0.0', port=5000, threaded=True, debug=False)
