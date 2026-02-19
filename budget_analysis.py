#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
나노센터 예산 분석 대시보드
2025년도 본예산(안) 분석 스크립트
"""

import os
import sys
import warnings
warnings.filterwarnings("ignore")

# Windows 터미널 한글 인코딩 설정
if sys.platform == "win32":
    os.system("chcp 65001 >nul 2>&1")
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# ----------------------------------------------------------------
# 라이브러리 임포트
# ----------------------------------------------------------------
try:
    import openpyxl
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    import numpy as np
except ImportError as e:
    print(f"[오류] 필수 라이브러리 없음: {e}")
    print("pip install openpyxl matplotlib numpy rich 명령으로 설치해주세요.")
    sys.exit(1)

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# ----------------------------------------------------------------
# 경로 설정
# ----------------------------------------------------------------
BASE_DIR = r"C:\Users\user\Desktop\예산작업"
EXCEL_FILE = os.path.join(BASE_DIR, "나노센터 예산.xlsx")
OUTPUT_DIR = os.path.join(BASE_DIR, "분석결과")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ----------------------------------------------------------------
# 한글 폰트 설정
# ----------------------------------------------------------------
def setup_korean_font():
    candidate_fonts = ["Malgun Gothic", "맑은 고딕", "NanumGothic", "나눔고딕", "Gulim"]
    available = {f.name for f in font_manager.fontManager.ttflist}
    for font_name in candidate_fonts:
        if font_name in available:
            plt.rcParams["font.family"] = font_name
            plt.rcParams["axes.unicode_minus"] = False
            return font_name
    for root, dirs, files in os.walk(r"C:/Windows/Fonts"):
        for fname in files:
            if "malgun" in fname.lower():
                fpath = os.path.join(root, fname)
                font_manager.fontManager.addfont(fpath)
                plt.rcParams["font.family"] = font_manager.FontProperties(fname=fpath).get_name()
                plt.rcParams["axes.unicode_minus"] = False
                return fname
    plt.rcParams["axes.unicode_minus"] = False
    return None

# ----------------------------------------------------------------
# 콘솔 헬퍼
# ----------------------------------------------------------------
console = Console() if RICH_AVAILABLE else None

def print_header(text):
    if RICH_AVAILABLE:
        console.print(Panel(Text(text, style="bold white", justify="center"), style="blue"))
    else:
        print("=" * 70)
        print(text)
        print("=" * 70)

def print_section(text):
    if RICH_AVAILABLE:
        console.print(f"\n[bold yellow]>>> {text}[/bold yellow]")
    else:
        print(f"\n--- {text} ---")

def fmt_won(amount):
    if abs(amount) >= 1_000_000_000:
        return f"{amount/1_000_000_000:.2f}억원"
    elif abs(amount) >= 1_000_000:
        return f"{amount/1_000_000:.1f}백만원"
    return f"{amount:,.0f}원"

def pct_change(current, prev):
    if prev == 0:
        return "신규"
    chg = (current - prev) / prev * 100
    sign = "+" if chg >= 0 else ""
    return f"{sign}{chg:.1f}%"

# ----------------------------------------------------------------
# 핵심 예산 데이터 (파일 파싱 결과 기반)
# ----------------------------------------------------------------
def get_budget_data():
    """
    나노센터 2025년도 본예산(안) 핵심 수치
    출처: 나노센터 예산.xlsx
      - 수입예산 시트: 과목별 수입 세부
      - 지출예산 시트: 나노센터 직접 지출 (사업별·성질별)
    단위: 원
    ※ 지출은 나노센터 전용 예산 기준 (총 48억원)
    """

    # 예산 총괄 (나노센터 기준)
    budget_summary = {
        "수입": {
            "사업수익(영업)":          1_340_000_000,   # 622관리 + 623대행 + 648출연
            "자본적 수입":             4_000_000_000,   # 176 수탁자산보조금수입
            "수입 총계":               5_340_000_000,
            "전년도 수입 총계":        5_295_574_000,
        },
        "지출": {
            "대행사업비용(A)":         4_265_000_000,
            "일반관리비용(C)":           463_280_000,
            "장비사업원가(D)":            47_900_000,
            "임대사업원가(F)":            21_340_000,
            "지출 총계":               4_797_520_000,
            "전년도 지출 총계":        5_492_303_000,
        },
        "차인": {
            "총 차인":                   542_480_000,   # 수입 - 지출 (흑자)
        },
    }

    # 수입예산 과목별 (수입예산 시트)
    income_items = [
        {"항목": "수입 총계",             "예산액": 5_340_000_000, "전년도": 5_295_574_000},
        {"항목": "600 사업수익",          "예산액": 1_340_000_000, "전년도": 1_885_574_000},
        {"항목": "  622 관리사업수익",    "예산액":   940_000_000, "전년도": 1_050_000_000},
        {"항목": "    기타장비활용수익",  "예산액":   350_000_000, "전년도":             0},
        {"항목": "    임대료수익",         "예산액":   540_000_000, "전년도":             0},
        {"항목": "    기술료 수익",        "예산액":    50_000_000, "전년도":             0},
        {"항목": "  623 대행사업수익",    "예산액":   300_000_000, "전년도":   735_574_000},
        {"항목": "    직접관리비수익",    "예산액":   265_000_000, "전년도":   569_938_000},
        {"항목": "    기타대행수익",      "예산액":    35_000_000, "전년도":   165_636_000},
        {"항목": "  648 출연금수익",      "예산액":   100_000_000, "전년도":   100_000_000},
        {"항목": "100 자본적 수입",       "예산액": 4_000_000_000, "전년도": 3_410_000_000},
        {"항목": "  176 수탁자산보조금",  "예산액": 4_000_000_000, "전년도": 3_410_000_000},
    ]

    # 나노센터 지출예산 사업별 (지출예산 시트)
    expense_nature = [
        # ── 대행사업비용(A): 4,265,000,000원 ──
        {"항목": "대행사업비용(A)",               "예산액": 4_265_000_000, "전년도": 5_033_143_000, "구성비": 88.90},
        {"항목": "  초임계원료의약품생산플랫폼(4차)","예산액": 4_000_000_000, "전년도": 3_000_000_000, "구성비": 83.38},
        {"항목": "  2025 디딤돌과제(디아노잔틴)",  "예산액":    45_000_000, "전년도":             0, "구성비":  0.94},
        {"항목": "  2025 광주연구개발특구(유니콘1)","예산액":   175_000_000, "전년도":             0, "구성비":  3.65},
        {"항목": "  국제공동기술개발(귀뚜라미)3차", "예산액":    45_000_000, "전년도":    90_000_000, "구성비":  0.94},
        # ── 일반관리비용(C): 463,280,000원 ──
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
        # ── 장비사업원가(D): 47,900,000원 ──
        {"항목": "장비사업원가(D)",               "예산액":    47_900_000, "전년도":    62_000_000, "구성비":  1.00},
        {"항목": "  201 일반운영비",              "예산액":     6_100_000, "전년도":     7_200_000, "구성비":  0.13},
        {"항목": "  206 재료비",                  "예산액":    24_000_000, "전년도":    24_000_000, "구성비":  0.50},
        {"항목": "  213 교육훈련비",              "예산액":     2_800_000, "전년도":       800_000, "구성비":  0.06},
        {"항목": "  214 수선유지교체비",           "예산액":    15_000_000, "전년도":    30_000_000, "구성비":  0.31},
        # ── 임대사업원가(F): 21,340,000원 ──
        {"항목": "임대사업원가(F)",               "예산액":    21_340_000, "전년도":    16_000_000, "구성비":  0.45},
        {"항목": "  201 일반운영비",              "예산액":     6_500_000, "전년도":     6_500_000, "구성비":  0.14},
        {"항목": "  202 여비",                   "예산액":     3_840_000, "전년도":             0, "구성비":  0.08},
        {"항목": "  213 교육훈련비",              "예산액":     4_000_000, "전년도":     2_500_000, "구성비":  0.08},
        {"항목": "  기타",                        "예산액":     7_000_000, "전년도":     7_000_000, "구성비":  0.15},
    ]

    # 나노센터 직접 지출 대분류 (지출예산 시트)
    nanocenter_expense = [
        {"항목": "대행사업비용(A)",  "예산액": 4_265_000_000, "전년도": 5_033_143_000},
        {"항목": "목적사업비용(B)",  "예산액":             0, "전년도":             0},
        {"항목": "일반관리비용(C)",  "예산액":   463_280_000, "전년도":   381_160_000},
        {"항목": "장비사업원가(D)",  "예산액":    47_900_000, "전년도":    62_000_000},
        {"항목": "분석사업원가(E)",  "예산액":             0, "전년도":             0},
        {"항목": "임대사업원가(F)",  "예산액":    21_340_000, "전년도":    16_000_000},
    ]

    return budget_summary, income_items, expense_nature, nanocenter_expense


# ----------------------------------------------------------------
# 터미널 대시보드
# ----------------------------------------------------------------
def print_dashboard(budget_summary, income_items, expense_nature, nanocenter_expense):

    print_header("나노센터 2025년도 본예산(안) 분석 대시보드")

    if RICH_AVAILABLE:
        console.print()
        console.print("  [cyan]분석 기준일:[/cyan] 2026-02-19  "
                      "[cyan]회계연도:[/cyan] 2025년  "
                      "[cyan]단위:[/cyan] 원  "
                      "[cyan]출처:[/cyan] 나노센터 예산.xlsx")
        console.print()

    # 1. 예산 총괄
    print_section("1. 예산 총괄 현황 (3-1. 예산총괄표)")
    if RICH_AVAILABLE:
        t = Table(title="예산 총괄", box=box.ROUNDED, style="cyan")
        t.add_column("구분",          style="bold",  width=22)
        t.add_column("사업예산",      justify="right", style="green")
        t.add_column("자본예산",      justify="right", style="yellow")
        t.add_column("자금예산(합계)",justify="right", style="bold white")
        t.add_row(
            "수입 계",
            fmt_won(budget_summary["수입"]["사업수익(영업)"]),
            fmt_won(budget_summary["수입"]["자본적 수입"]),
            fmt_won(budget_summary["수입"]["수입 총계"]),
        )
        t.add_row(
            "지출 계",
            fmt_won(budget_summary["지출"]["대행사업비용(A)"] + budget_summary["지출"]["일반관리비용(C)"]),
            fmt_won(budget_summary["지출"]["장비사업원가(D)"] + budget_summary["지출"]["임대사업원가(F)"]),
            fmt_won(budget_summary["지출"]["지출 총계"]),
        )
        t.add_row(
            "차인 (수입-지출)",
            "", "",
            fmt_won(budget_summary["차인"]["총 차인"]),
        )
        console.print(t)
        cur = budget_summary["지출"]["지출 총계"]
        prev = budget_summary["지출"]["전년도 지출 총계"]
        console.print(f"  [bold white]총 지출 전년 대비:[/bold white] "
                      f"{pct_change(cur, prev)} "
                      f"(전년: {fmt_won(prev)} -> 금년: {fmt_won(cur)})")
    else:
        print(f"  수입 총계: {fmt_won(budget_summary['수입']['수입 총계'])}")
        print(f"  지출 총계: {fmt_won(budget_summary['지출']['지출 총계'])}")
        print(f"  총 차인:   {fmt_won(budget_summary['차인']['총 차인'])}")

    # 2. 수입예산
    print_section("2. 수입예산 과목별 현황 (수입예산 시트)")
    if RICH_AVAILABLE:
        t2 = Table(title="수입예산 과목별", box=box.ROUNDED, style="green")
        t2.add_column("과목",        style="bold",   width=22)
        t2.add_column("2025 예산액", justify="right", style="white")
        t2.add_column("전년도 예산", justify="right", style="dim")
        t2.add_column("증감",        justify="right")
        t2.add_column("비중",        justify="right", style="cyan")
        total_income = budget_summary["수입"]["수입 총계"]
        for item in income_items:
            amt  = item["예산액"]
            prev = item["전년도"]
            diff = amt - prev
            diff_str = (
                ("[green]+" if diff >= 0 else "[red]") +
                fmt_won(diff) +
                ("[/green]" if diff >= 0 else "[/red]")
            )
            bigo = f"{amt/total_income*100:.1f}%" if total_income > 0 else "-"
            t2.add_row(item["항목"], fmt_won(amt), fmt_won(prev), diff_str, bigo)
        console.print(t2)
    else:
        for item in income_items:
            print(f"  {item['항목']}: {fmt_won(item['예산액'])}")

    # 3. 지출 성질별 (대과목 위주)
    print_section("3. 지출예산 성질별 현황 - 대과목 (3-5. 성질별총괄표)")
    major_items = [x for x in expense_nature if not x["항목"].startswith("  ")]
    if RICH_AVAILABLE:
        t3 = Table(title="지출예산 성질별 (대과목, 예산액 내림차순)", box=box.ROUNDED, style="yellow")
        t3.add_column("과목",        style="bold",   width=22)
        t3.add_column("2025 예산액", justify="right", style="white")
        t3.add_column("전년도 예산", justify="right", style="dim")
        t3.add_column("증감",        justify="right")
        t3.add_column("구성비",      justify="right", style="cyan")
        t3.add_column("전년比",      justify="right")
        for item in sorted(major_items, key=lambda x: x["예산액"], reverse=True):
            diff = item["예산액"] - item["전년도"]
            diff_str = (
                ("[green]+" if diff >= 0 else "[red]") +
                fmt_won(diff) +
                ("[/green]" if diff >= 0 else "[/red]")
            )
            pct_str = pct_change(item["예산액"], item["전년도"])
            pct_col = f"[green]{pct_str}[/green]" if "+" in pct_str else f"[red]{pct_str}[/red]"
            t3.add_row(
                item["항목"],
                fmt_won(item["예산액"]),
                fmt_won(item["전년도"]),
                diff_str,
                f"{item['구성비']:.2f}%",
                pct_col,
            )
        console.print(t3)
    else:
        for item in sorted(major_items, key=lambda x: x["예산액"], reverse=True):
            print(f"  {item['항목']}: {fmt_won(item['예산액'])} ({item['구성비']:.1f}%) "
                  f"전년比 {pct_change(item['예산액'], item['전년도'])}")

    # 4. 나노센터 직접 지출
    print_section("4. 나노센터 직접 지출예산 (지출예산 시트 - 진흥원 대행/관리 구분)")
    if RICH_AVAILABLE:
        t4 = Table(title="나노센터 지출 구분", box=box.ROUNDED, style="magenta")
        t4.add_column("구분",        style="bold",   width=18)
        t4.add_column("2025 예산액", justify="right", style="white")
        t4.add_column("전년도 예산", justify="right", style="dim")
        t4.add_column("증감",        justify="right")
        t4.add_column("증감률",      justify="right")
        total_exp = sum(x["예산액"] for x in nanocenter_expense)
        for item in nanocenter_expense:
            diff = item["예산액"] - item["전년도"]
            diff_str = (
                ("[green]+" if diff >= 0 else "[red]") +
                fmt_won(diff) +
                ("[/green]" if diff >= 0 else "[/red]")
            )
            t4.add_row(
                item["항목"],
                fmt_won(item["예산액"]),
                fmt_won(item["전년도"]),
                diff_str,
                pct_change(item["예산액"], item["전년도"]),
            )
        t4.add_row("[bold]합 계[/bold]", f"[bold]{fmt_won(total_exp)}[/bold]", "", "", "")
        console.print(t4)
    else:
        for item in nanocenter_expense:
            print(f"  {item['항목']}: {fmt_won(item['예산액'])}")
        print(f"  합계: {fmt_won(sum(x['예산액'] for x in nanocenter_expense))}")

    # 5. 핵심 지표
    print_section("5. 핵심 재무 지표 요약")
    total_in  = budget_summary["수입"]["수입 총계"]
    total_out = budget_summary["지출"]["지출 총계"]
    prev_out  = budget_summary["지출"]["전년도 지출 총계"]
    대행사업비 = budget_summary["지출"]["대행사업비용(A)"]
    일반관리비 = budget_summary["지출"]["일반관리비용(C)"]
    동력비    = 246_000_000   # 일반관리비 내 동력비
    연구개발비 = 2_000_000 + 45_000_000 + 175_000_000 + 45_000_000  # 관리+대행과제
    사업수익  = budget_summary["수입"]["사업수익(영업)"]

    if RICH_AVAILABLE:
        console.print(f"  [bold cyan]수입 총계:[/bold cyan]                   {fmt_won(total_in)}")
        console.print(f"  [bold red]지출 총계 (나노센터 전용):[/bold red]    {fmt_won(total_out)}")
        console.print(f"  [bold green]차인 (수입 - 지출):[/bold green]          {fmt_won(total_in - total_out)}")
        console.print(f"  [bold white]전년 대비 지출 변화:[/bold white]          "
                      f"{fmt_won(total_out - prev_out)}  ({pct_change(total_out, prev_out)})")
        console.print(f"  [bold yellow]대행사업비 비중:[/bold yellow]              "
                      f"{대행사업비/total_out*100:.1f}%  ({fmt_won(대행사업비)})")
        console.print(f"  [bold magenta]일반관리비 비중:[/bold magenta]              "
                      f"{일반관리비/total_out*100:.1f}%  ({fmt_won(일반관리비)})")
        console.print(f"  [bold cyan]동력비 (관리비 내):[/bold cyan]            "
                      f"{동력비/total_out*100:.1f}%  ({fmt_won(동력비)})")
        console.print(f"  [bold white]자체수입 자급률:[/bold white]              "
                      f"{사업수익/total_out*100:.1f}%  (사업수익/지출 총액)")
    else:
        print(f"  수입 총계:      {fmt_won(total_in)}")
        print(f"  지출 총계:      {fmt_won(total_out)}")
        print(f"  차인:           {fmt_won(total_in - total_out)}")
        print(f"  대행사업비 비중: {대행사업비/total_out*100:.1f}%")
        print(f"  자체수입 자급률: {사업수익/total_out*100:.1f}%")


# ----------------------------------------------------------------
# 전략적 분석 및 제언
# ----------------------------------------------------------------
def print_strategic_analysis():

    print_section("6. 주요 발견사항 및 위험 요인")
    findings = [
        ("긍정", "수입 > 지출: 나노센터 예산 흑자",
         "수입 총계 53.4억원 vs 지출 총계 48.0억원 → 차인 +5.4억원(흑자).\n"
         "    자체 운영 예산 범위 내에서는 재정 균형이 유지되고 있습니다."),
        ("경고", "대행사업비 지출 집중도 88.9%",
         "지출의 88.9%(42.7억)가 대행사업비(수탁과제)에 집중되어 있습니다.\n"
         "    초임계플랫폼(40억) 단일 사업 의존도가 극히 높아, 해당 사업 차질 시\n"
         "    나노센터 전체 예산 집행에 심각한 영향이 예상됩니다."),
        ("경고", "대행사업비 -15.3% 감소",
         "대행사업비용 42.7억원 (전년 50.3억원). 수탁과제 수주 감소 신호.\n"
         "    디딤돌, 광주특구, 귀뚜라미 과제 등 신규 과제가 추가되었으나\n"
         "    총액은 전년 대비 7.7억원 감소하였습니다."),
        ("주의", "관리비 내 동력비 비중 53.2%",
         "일반관리비(4.6억) 중 동력비가 2.46억(53.2%)으로 압도적 1위.\n"
         "    에너지 비용 관리가 운영 효율화의 핵심 과제입니다."),
        ("주의", "수선유지교체비 4.3배 급증",
         "일반관리비 내 수선유지비 4,280만원 (전년 1,000만원, +328%).\n"
         "    장비 노후화에 따른 유지보수 비용 증가 추세가 확인됩니다."),
        ("긍정", "일반관리비용 +21.5% 증가",
         "일반관리비용 4.6억원 (전년 3.8억원). 센터 자체 운영역량 강화 신호.\n"
         "    특히 동력비 증가(+4,000만)는 시설 가동률 향상을 의미합니다."),
        ("긍정", "임대사업원가 +33.4% 증가",
         "임대사업원가 2,134만원 (전년 1,600만원). 임대 사업 확대 추세.\n"
         "    임대료 수익(5.4억)과 연계한 수익성 개선 가능성이 있습니다."),
    ]

    if RICH_AVAILABLE:
        for level, title, desc in findings:
            color = {"경고": "red", "주의": "yellow", "긍정": "green"}.get(level, "white")
            console.print(f"  [{color}][{level}][/{color}] [bold]{title}[/bold]")
            console.print(f"    {desc}\n")
    else:
        for level, title, desc in findings:
            print(f"  [{level}] {title}")
            print(f"    {desc}\n")

    print_section("7. 전략적 제언 (우선순위별)")
    recommendations = [
        ("즉시 조치", "초임계플랫폼 사업 리스크 헷지 계획 수립",
         "지출의 83.4%(40억)가 단일 사업(초임계원료의약품)에 쏠려 있습니다.\n"
         "    2026년 이후 해당 사업 종료 또는 규모 축소 시 대체 수탁과제 확보 전략을\n"
         "    즉시 수립하고 신규 과제 파이프라인을 점검하세요."),
        ("즉시 조치", "수탁과제 수주 확대 (대행사업비 -15.3% 대응)",
         "대행사업비가 전년 대비 7.7억원 감소하였습니다.\n"
         "    정부 R&D, 지자체 위탁, 기업 기술개발 지원 등 신규 과제 수주를\n"
         "    상반기 내 집중 추진하세요."),
        ("단기 계획", "동력비 에너지 효율화 투자 검토",
         "동력비 2.46억원이 관리비의 53%를 차지합니다.\n"
         "    ESG 연계 에너지 효율화 설비 투자 또는 스마트에너지관리 시스템 도입으로\n"
         "    중기(3년) 10-15% 절감 목표를 수립하세요."),
        ("단기 계획", "자체 수입 다변화",
         "관리사업수익(9.4억)이 전년(10.5억) 대비 -1.1억 감소하였습니다.\n"
         "    기타장비활용수익(3.5억), 임대료수익(5.4억) 등 신규 수익원을 확대하고\n"
         "    대행사업수익(3억) 회복을 위한 수탁과제 영업을 강화하세요."),
        ("단기 계획", "장비 노후화 선제 대응",
         "수선유지비가 전년 1,000만원 → 4,280만원으로 4.3배 급증하였습니다.\n"
         "    장비 이력 관리 대장을 정비하고 중기 자본지출(장비교체) 계획을 수립하세요."),
        ("중장기 전략", "나노센터 독립 수익모델 구축",
         "현재 수입의 74.9%가 수탁자산보조금(자본적 수입)으로 구성되어 있습니다.\n"
         "    기술이전 수익, 분석서비스 수익, 임대수익 확대를 통해\n"
         "    2030년까지 자체 사업수익 20억원 목표를 설정하세요."),
        ("중장기 전략", "과제 포트폴리오 다각화",
         "현재 수탁과제가 초임계·디딤돌·광주특구·귀뚜라미 4건에 집중되어 있습니다.\n"
         "    바이오·나노·환경 분야 다부처 과제를 발굴하여\n"
         "    5년 내 과제 수 2배, 수익 1.5배 달성을 목표로 설정하세요."),
    ]

    if RICH_AVAILABLE:
        for priority, title, desc in recommendations:
            color = {
                "즉시 조치": "red",
                "단기 계획": "yellow",
                "중장기 전략": "cyan"
            }.get(priority, "white")
            console.print(f"  [{color}][{priority}][/{color}] [bold]{title}[/bold]")
            console.print(f"    {desc}\n")
    else:
        for priority, title, desc in recommendations:
            print(f"  [{priority}] {title}")
            print(f"    {desc}\n")


# ----------------------------------------------------------------
# 시각화 함수
# ----------------------------------------------------------------
def create_visualizations(expense_nature, budget_summary, nanocenter_expense):

    font_name = setup_korean_font()
    major_items = [x for x in expense_nature if not x["항목"].startswith("  ")]

    # ── 차트 1: 4-패널 종합 대시보드 (다크 테마) ──
    fig, axes = plt.subplots(2, 2, figsize=(18, 14))
    fig.suptitle("나노센터 2025년도 본예산(안) 종합 분석",
                 fontsize=18, fontweight="bold", y=0.98, color="white")
    fig.patch.set_facecolor("#1a1a2e")
    for ax in axes.flat:
        ax.set_facecolor("#16213e")
        ax.tick_params(colors="white")
        ax.xaxis.label.set_color("white")
        ax.yaxis.label.set_color("white")
        ax.title.set_color("white")
        for spine in ax.spines.values():
            spine.set_edgecolor("#444")

    # 패널 1: 수입 구조 파이차트
    ax1 = axes[0, 0]
    in_labels = ["관리사업수익\n(장비+임대+기술료)", "대행사업수익", "출연금수익", "수탁자산보조금\n(자본적 수입)"]
    in_vals   = [940_000_000, 300_000_000, 100_000_000, 4_000_000_000]
    in_colors = ["#00d2ff", "#3a7bd5", "#55efc4", "#feca57"]
    wedges, texts, autotexts = ax1.pie(
        in_vals, labels=in_labels, colors=in_colors,
        autopct="%1.1f%%", startangle=90, pctdistance=0.75,
        textprops={"color": "white", "fontsize": 9}
    )
    for at in autotexts:
        at.set_fontsize(8)
        at.set_color("white")
    ax1.set_title("수입 구조 (총 53.4억원)", color="white", fontsize=12, fontweight="bold")

    # 패널 2: 지출 사업별 수평 막대 (나노센터 기준)
    ax2 = axes[0, 1]
    exp_items2 = [x for x in expense_nature if not x["항목"].startswith("  ")]
    labels2 = [x["항목"] for x in exp_items2]
    vals2   = [x["예산액"] / 1e8 for x in exp_items2]
    prev2   = [x["전년도"]  / 1e8 for x in exp_items2]
    y_pos   = np.arange(len(labels2))
    bh = 0.35
    ax2.barh(y_pos + bh/2, vals2, bh, label="2025 예산", color="#00d2ff", alpha=0.85)
    ax2.barh(y_pos - bh/2, prev2, bh, label="전년도 예산", color="#ff6b6b", alpha=0.65)
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(labels2, color="white", fontsize=8)
    ax2.set_xlabel("금액 (억원)", color="white")
    ax2.set_title("나노센터 지출 사업별 비교 (억원)", color="white", fontsize=11, fontweight="bold")
    ax2.legend(loc="lower right", facecolor="#1a1a2e", labelcolor="white", fontsize=8)
    ax2.xaxis.set_tick_params(labelcolor="white")
    for bar in ax2.patches[:len(vals2)]:
        w = bar.get_width()
        ax2.text(w + 0.2, bar.get_y() + bar.get_height()/2,
                 f"{w:.1f}", va="center", ha="left", color="#00d2ff", fontsize=7)

    # 패널 3: 지출 구성비 도넛차트 (나노센터 기준)
    ax3 = axes[1, 0]
    donut_data = [
        ("초임계플랫폼",  4_000_000_000),
        ("광주특구",        175_000_000),
        ("디딤돌과제",       45_000_000),
        ("귀뚜라미과제",     45_000_000),
        ("동력비(관리)",    246_000_000),
        ("일반운영비(관리)", 92_040_000),
        ("수선유지비",       57_800_000),
        ("장비원가",         47_900_000),
        ("임대원가",         21_340_000),
        ("기타",             68_440_000),
    ]
    d_labels = [x[0] for x in donut_data]
    d_vals   = [x[1] for x in donut_data]
    d_colors = ["#00d2ff","#feca57","#ff6b6b","#a29bfe","#00cec9",
                "#fd79a8","#55efc4","#fdcb6e","#b2bec3"]
    wedges3, texts3, auto3 = ax3.pie(
        d_vals, labels=d_labels, colors=d_colors,
        autopct="%1.1f%%", startangle=90, pctdistance=0.78,
        wedgeprops={"width": 0.5},
        textprops={"color": "white", "fontsize": 8}
    )
    for a in auto3:
        a.set_fontsize(7)
        a.set_color("white")
    ax3.set_title("지출 항목 구성비 (총 48.0억원, 나노센터)", color="white", fontsize=11, fontweight="bold")

    # 패널 4: 전년 대비 증감률 수평 막대 (나노센터 기준)
    ax4 = axes[1, 1]
    chg_data = [
        ("대행사업비",    4_265_000_000, 5_033_143_000),
        ("일반관리비",      463_280_000,   381_160_000),
        ("장비사업원가",     47_900_000,    62_000_000),
        ("임대사업원가",     21_340_000,    16_000_000),
        ("동력비(관리내)",  246_000_000,   206_000_000),
        ("수선유지(관리)",   42_800_000,    10_000_000),
        ("일반운영(관리)",   92_040_000,    88_560_000),
        ("여비(관리내)",     23_040_000,    28_800_000),
        ("교육훈련(관리)",    2_800_000,     3_400_000),
    ]
    chg_labels = [x[0] for x in chg_data]
    chg_pct    = [(x[1]-x[2])/x[2]*100 if x[2] > 0 else 0 for x in chg_data]
    bar_colors = ["#00d2ff" if v >= 0 else "#ff6b6b" for v in chg_pct]
    bars4 = ax4.barh(chg_labels, chg_pct, color=bar_colors, alpha=0.85)
    ax4.axvline(0, color="white", linewidth=0.8, linestyle="--")
    ax4.set_xlabel("전년 대비 증감률 (%)", color="white")
    ax4.set_title("나노센터 주요 항목 전년 대비 증감률", color="white", fontsize=11, fontweight="bold")
    ax4.tick_params(axis="y", labelcolor="white", labelsize=9)
    ax4.tick_params(axis="x", labelcolor="white")
    for bar, pct in zip(bars4, chg_pct):
        x = bar.get_width()
        ax4.text(
            x + (1 if x >= 0 else -1),
            bar.get_y() + bar.get_height()/2,
            f"{pct:.1f}%", va="center",
            ha="left" if x >= 0 else "right",
            color="white", fontsize=7
        )

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    out1 = os.path.join(OUTPUT_DIR, "나노센터_예산분석_대시보드.png")
    plt.savefig(out1, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"  [저장] {out1}")

    # ── 차트 2: 수입/지출 구조 비교 (라이트 테마) ──
    fig2, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(16, 7))
    fig2.suptitle("수입/지출 총괄 비교 분석 (2025년도 vs 전년도)", fontsize=14, fontweight="bold")
    fig2.patch.set_facecolor("#f8f9fa")

    ax_a.set_facecolor("#ffffff")
    in_labels_a = ["관리사업수익", "대행사업수익", "자본잉여금수입"]
    in_vals_a   = [940_000_000, 300_000_000, 4_000_000_000]
    in_colors_a = ["#3498db", "#2ecc71", "#e74c3c"]
    bars_a = ax_a.bar(in_labels_a, [v/1e8 for v in in_vals_a],
                      color=in_colors_a, alpha=0.85, edgecolor="white", width=0.5)
    ax_a.set_title("2025년 수입 예산 구조", fontsize=12, fontweight="bold")
    ax_a.set_ylabel("금액 (억원)")
    ax_a.set_ylim(0, max(in_vals_a)/1e8 * 1.2)
    for bar, v in zip(bars_a, in_vals_a):
        ax_a.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                  f"{v/1e8:.1f}억", ha="center", va="bottom", fontweight="bold", fontsize=10)

    ax_b.set_facecolor("#ffffff")
    ex_items_b = [
        ("인건비",     10_495_421_913),
        ("동력비",      3_127_162_000),
        ("시설비",      3_129_212_000),
        ("민간지원",    1_798_307_000),
        ("일반운영비",  2_809_940_000),
        ("자산취득",    2_359_450_000),
        ("기타",        8_352_489_407),
    ]
    ex_labels_b = [x[0] for x in ex_items_b]
    ex_vals_b   = [x[1]/1e8 for x in ex_items_b]
    ex_colors_b = ["#e74c3c","#f39c12","#9b59b6","#1abc9c","#3498db","#e67e22","#95a5a6"]
    bars_b = ax_b.bar(ex_labels_b, ex_vals_b,
                      color=ex_colors_b, alpha=0.85, edgecolor="white", width=0.6)
    ax_b.set_title("2025년 지출 예산 구조 (주요 항목)", fontsize=12, fontweight="bold")
    ax_b.set_ylabel("금액 (억원)")
    for bar, v in zip(bars_b, ex_vals_b):
        ax_b.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                  f"{v:.1f}억", ha="center", va="bottom", fontweight="bold", fontsize=9)

    plt.tight_layout()
    out2 = os.path.join(OUTPUT_DIR, "나노센터_수입지출_비교.png")
    plt.savefig(out2, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [저장] {out2}")

    # ── 차트 3: 전년 대비 성질별 전체 비교 (다크 테마) ──
    fig3, ax5 = plt.subplots(figsize=(18, 9))
    fig3.patch.set_facecolor("#0d1117")
    ax5.set_facecolor("#161b22")

    sorted_major = sorted(major_items, key=lambda x: x["예산액"], reverse=True)
    n       = len(sorted_major)
    x_pos   = np.arange(n)
    labels5 = [x["항목"].replace(" ", "\n") for x in sorted_major]
    cur5    = [x["예산액"] / 1e8 for x in sorted_major]
    prev5   = [x["전년도"]  / 1e8 for x in sorted_major]
    bw = 0.35

    ax5.bar(x_pos - bw/2, prev5, bw, label="전년도 예산", color="#ff4757", alpha=0.7)
    ax5.bar(x_pos + bw/2, cur5,  bw, label="2025 예산",   color="#00d2ff", alpha=0.85)
    ax5.set_xticks(x_pos)
    ax5.set_xticklabels(labels5, rotation=45, ha="right", color="white", fontsize=7)
    ax5.set_ylabel("금액 (억원)", color="white")
    ax5.set_title("지출예산 성질별 전년 대비 상세 비교 (대과목)",
                  color="white", fontsize=13, fontweight="bold")
    ax5.legend(facecolor="#0d1117", labelcolor="white", fontsize=10)
    ax5.tick_params(axis="y", labelcolor="white")
    for spine in ax5.spines.values():
        spine.set_edgecolor("#333")
    ax5.yaxis.grid(True, color="#333", linestyle="--", alpha=0.5)
    ax5.set_axisbelow(True)

    plt.tight_layout()
    out3 = os.path.join(OUTPUT_DIR, "나노센터_성질별지출_상세비교.png")
    plt.savefig(out3, dpi=150, bbox_inches="tight", facecolor=fig3.get_facecolor())
    plt.close()
    print(f"  [저장] {out3}")

    return out1, out2, out3


# ----------------------------------------------------------------
# 텍스트 리포트 저장
# ----------------------------------------------------------------
def save_text_report(expense_nature, budget_summary):
    report_path = os.path.join(OUTPUT_DIR, "예산분석_리포트.txt")
    major_items = [x for x in expense_nature if not x["항목"].startswith("  ")]

    lines = [
        "=" * 70,
        "나노센터 2025년도 본예산(안) 분석 리포트 (나노센터 전용 예산 기준)",
        "분석일: 2026-02-19",
        "출처: 나노센터 예산.xlsx > 지출예산 시트",
        "=" * 70,
        "",
        "[1. 예산 총괄 (나노센터 전용)]",
        f"  수입 총계:            {fmt_won(budget_summary['수입']['수입 총계'])}",
        f"  지출 총계:            {fmt_won(budget_summary['지출']['지출 총계'])}",
        f"  차인 합계:            {fmt_won(budget_summary['차인']['총 차인'])} (흑자)",
        f"  전년도 지출 총계:     {fmt_won(budget_summary['지출']['전년도 지출 총계'])}",
        f"  전년 대비 지출 변화:  {pct_change(budget_summary['지출']['지출 총계'], budget_summary['지출']['전년도 지출 총계'])}",
        "",
        "[2. 수입예산 과목별]",
        f"  600 사업수익:          {fmt_won(1_340_000_000)} (전년: {fmt_won(1_885_574_000)}, {pct_change(1_340_000_000, 1_885_574_000)})",
        f"    622 관리사업수익:    {fmt_won(940_000_000)}",
        f"      기타장비활용수익:  {fmt_won(350_000_000)}",
        f"      임대료수익:        {fmt_won(540_000_000)}",
        f"      기술료 수익:       {fmt_won(50_000_000)}",
        f"    623 대행사업수익:    {fmt_won(300_000_000)} (전년: {fmt_won(735_574_000)}, {pct_change(300_000_000, 735_574_000)})",
        f"  700 자본잉여금수입:    {fmt_won(4_000_000_000)} (전년: {fmt_won(3_410_000_000)}, {pct_change(4_000_000_000, 3_410_000_000)})",
        "",
        "[3. 지출예산 성질별 현황 (대과목, 금액 내림차순)]",
    ]

    for i, item in enumerate(sorted(major_items, key=lambda x: x["예산액"], reverse=True), 1):
        pct = pct_change(item["예산액"], item["전년도"])
        lines.append(
            f"  {i:2d}. {item['항목']:<18} {fmt_won(item['예산액']):<14} "
            f"({item['구성비']:.2f}%)  전년比 {pct}"
        )

    lines += [
        "",
        "[4. 주요 발견사항]",
        "  [긍정] 수입(53.4억) > 지출(48.0억): 나노센터 자체 예산 기준 흑자",
        "  [경고] 대행사업비 88.9% 집중: 초임계플랫폼 단일 사업 의존도 83.4%",
        "  [경고] 대행사업비 -15.3%: 수탁과제 수주 감소 신호",
        "  [주의] 관리비 내 동력비 비중 53.2%: 에너지 비용 절감 필요",
        "  [주의] 수선유지비 +328%: 장비 노후화 가속, 중기 교체 계획 필요",
        "  [긍정] 일반관리비 +21.5%: 나노센터 자체 운영역량 강화",
        "  [긍정] 임대사업원가 +33.4%: 임대 사업 확대 추세",
        "",
        "[5. 전략적 제언]",
        "  [즉시] 초임계플랫폼 사업 종료 이후 대체 수탁과제 파이프라인 확보",
        "  [즉시] 대행사업비 -15.3% 대응: 신규 수탁과제 수주 집중 추진",
        "  [단기] 동력비 에너지 효율화 투자 (중기 10-15% 절감 목표)",
        "  [단기] 자체 수입 다변화: 장비활용·기술이전·임대 확대",
        "  [단기] 장비 노후화 선제 대응: 중기 자본지출 계획 수립",
        "  [중기] 나노센터 독립 수익모델: 2030년 자체수익 20억원 목표",
        "  [중기] 과제 포트폴리오 다각화: 5년내 과제 수 2배 달성",
        "",
        "=" * 70,
    ]

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return report_path


# ----------------------------------------------------------------
# 메인 실행
# ----------------------------------------------------------------
def main():
    print_header("나노센터 예산 분석 스크립트 시작")
    if RICH_AVAILABLE:
        console.print("  [green]Rich 라이브러리 활성화 - 컬러 터미널 출력 모드[/green]\n")
    else:
        print("  Rich 라이브러리 없음 - 일반 출력 모드\n")

    # 1. 데이터 로드
    print_section("데이터 로딩...")
    budget_summary, income_items, expense_nature, nanocenter_expense = get_budget_data()
    if RICH_AVAILABLE:
        console.print("  [green]데이터 로딩 완료[/green]")

    # 2. 터미널 대시보드
    print_dashboard(budget_summary, income_items, expense_nature, nanocenter_expense)

    # 3. 전략 분석
    print_strategic_analysis()

    # 4. 시각화
    print_section("시각화 생성 중...")
    out1, out2, out3 = create_visualizations(expense_nature, budget_summary, nanocenter_expense)

    # 5. 텍스트 리포트
    print_section("리포트 저장 중...")
    report_path = save_text_report(expense_nature, budget_summary)
    if RICH_AVAILABLE:
        console.print(f"  [green][저장][/green] {report_path}")
    else:
        print(f"  [저장] {report_path}")

    # 6. 완료
    print_header("분석 완료")
    if RICH_AVAILABLE:
        console.print(f"\n  [bold green]출력 파일 위치:[/bold green] {OUTPUT_DIR}")
        console.print("  - 나노센터_예산분석_대시보드.png     (4-패널 종합 다크 대시보드)")
        console.print("  - 나노센터_수입지출_비교.png          (수입/지출 구조 비교)")
        console.print("  - 나노센터_성질별지출_상세비교.png    (성질별 전년 대비 상세)")
        console.print("  - 예산분석_리포트.txt                 (텍스트 분석 리포트)\n")
    else:
        print(f"\n  출력 파일 위치: {OUTPUT_DIR}")
        print("  생성 파일: 대시보드.png, 수입지출비교.png, 성질별비교.png, 리포트.txt")


if __name__ == "__main__":
    main()
