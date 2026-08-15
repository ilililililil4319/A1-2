# 국내 여행지 추천 프로그램

날짜를 입력하면 AI(OpenAI)가 국내 여행지를 추천하고, Kakao Local API로 해당 지역의 맛집을 검색한 뒤, 두 정보를 종합해 최종 여행 리포트(Markdown)를 생성하는 CLI 프로그램입니다.

모든 기능과 에러 처리 로직은 실제 성공/실패 케이스를 직접 발생시켜 검증을 완료했습니다. (검증 내역은 "8. 테스트 검증 내역" 참고). 기본 요구사항 완료 후 **복수 지역 추천**과 **결과 캐싱** 두 가지 보너스 기능도 실제로 구현해 검증했습니다. (구현 결과는 "13. 보너스 과제 구현 결과" 참고)

---

## 0. 미션 개요

**과제명**: Python 응용 — API 활용 국내 여행지 추천 프로그램 개발

단일 API 호출이 아니라, 서로 다른 API들을 엮어 하나의 인사이트를 만드는 흐름을 구현하는 것이 이 과제의 핵심입니다. 사용자가 여행 날짜를 입력하면:

1. **LLM API**(OpenAI)가 해당 시기에 여행하기 좋은 지역을 추천하고 (보너스: `--count`로 여러 지역 동시 추천 가능)
2. **지도/장소 API**(Kakao Local)가 그 지역의 맛집을 검색하고
3. 다시 **LLM API**가 위 두 결과를 종합해 사람이 읽을 수 있는 최종 여행 리포트를 작성합니다
4. 동일한 날짜로 재실행하면 API를 다시 호출하지 않고 저장된 결과를 재사용합니다 (보너스: 결과 캐싱, `--refresh`로 강제 재조회 가능)

### 과제 목표 (학습자가 스스로 설명할 수 있어야 하는 것)

- REST API의 요청/응답 구조와 HTTP 메서드(GET/POST)의 차이 → 이 프로그램은 OpenAI(POST, JSON body)와 Kakao Local(GET, query parameter) 두 가지 호출 방식을 모두 사용합니다.
- LLM 출력 결과를 구조화(JSON)하여 다음 단계(지도/장소 검색)의 입력으로 활용하는 흐름 → `get_recommendations()`의 반환값(지역 배열)이 그대로 `search_restaurants()`의 입력 파라미터로 지역마다 전달됩니다.
- 외부 API 호출에서 발생하는 대표 오류(인증/쿼터/네트워크/파싱)와 대응 원칙 → 아래 "7. 에러 처리 정책" 표에 정리했고, 실제 상황을 재현해 검증했습니다.
- API 키를 코드에 직접 작성하지 않고 `.env`/환경변수로 관리하는 이유 → 협업/공유 시 실수로 키가 공개되는 것을 방지, 키 교체 시 코드 수정 불필요, 과금/쿼터 사고 예방.

### 항목 선택/결정 내용

| 항목 | 선택/결정 내용 |
|---|---|
| LLM API | OpenAI 계열 API (gpt-4o-mini) 사용 |
| 지도/장소 API | Kakao Local API (키워드 기반 장소 검색) 사용 |
| 개발 환경 | Windows 공용PC, PowerShell·VS Code, Python 3.10 이상 |
| 보안 원칙 | 공용PC이므로 API 키를 파일에 영구 저장하지 않고, PowerShell 세션 임시 환경변수($env:)를 기본으로 사용 |

---

## 1. 기능 목록

| 구분 | 내용 |
|---|---|
| CLI 인터페이스 | `argparse` 기반, `--date "YYYY-MM-DD"` 필수 옵션, 날짜 형식 검증, `--count`(추천 지역 수), `--refresh`(캐시 무시) 옵션 |
| 1차 LLM 추천 | OpenAI가 날짜 기반으로 도시를 `--count`개(기본 1곳, 최대 5곳) JSON 배열(`recommended_city`, `weather`, `events`, `reason`)로 추천 |
| 장소 검색 | Kakao Local API로 추천된 지역마다 맛집 최대 5곳 검색(`name`, `address`, `category`, `url`, `x`, `y`) |
| 2차 LLM 리포트 생성 | 지역별로 추천 이유·날씨·행사·맛집·1일 일정을 종합해 Markdown 리포트 작성, 지역이 여러 곳이면 지역별 섹션으로 구분 |
| 결과 캐싱 | 동일한 `--date`로 재실행하면 API를 다시 호출하지 않고 `results/{date}_data.json`을 재사용, `--refresh`로 강제 재조회 가능 |
| 에러 처리 | 키 미설정 즉시 종료, LLM JSON 파싱 실패 1회 재시도, 장소 검색 0건 최대 2회 재시도, 지도 API 인증 실패 시 "데이터 없음" 처리 후 계속 진행 |
| 결과 저장 | `results/` 폴더에 원본 데이터 JSON과 최종 리포트 Markdown을 날짜별로 저장 |

---

## 2. 프로그램 흐름도

```
사용자 입력(--date, [--count], [--refresh])
      │
      ▼
캐시 확인 (--refresh 없고 results/{date}_data.json 있으면) ──있음──▶ 캐시된 regions 재사용
      │ 없음                                                            │
      ▼                                                                 │
[1/3] LLM 1차 추천 (get_recommendations) — 지역 N곳                      │
      │  recommendations: [{recommended_city, weather, events, reason}, ...]
      ▼                                                                 │
[2/3] Kakao 맛집 검색 (search_restaurants) — 지역마다 반복                │
      │  맛집 최대 5곳씩 (0건이어도 계속 진행)                            │
      ▼                                                                 │
      regions: [{recommendation, restaurants}, ...] ◀────────────────────
      │
      ▼
[3/3] LLM 최종 리포트 생성 (generate_report) — 지역별 섹션
      │  Markdown 문자열
      ▼
results/{date}_data.json + results/{date}_travel_plan.md 저장
```

---

## 3. 설치 방법

```bash
# 프로젝트 폴더로 이동 후
pip install requests python-dotenv openai
```

`requirements.txt`로 한 번에 설치할 수도 있습니다.

```bash
pip install -r requirements.txt
```

`requirements.txt` 내용:

```
openai>=1.0.0
requests>=2.31.0
python-dotenv>=1.0.0
```

---

## 4. API 키 설정

이 프로그램은 **OpenAI API 키**와 **Kakao REST API 키** 두 가지가 필요합니다. 키는 코드에 직접 작성하지 않고 아래 두 방식 중 하나로 관리합니다.

### 방식 A — 세션 환경변수 (공용PC 권장)

```powershell
# PowerShell
$env:OPENAI_API_KEY="본인 키"
$env:KAKAO_API_KEY="본인 키"
```

터미널 창을 닫으면 값이 자동으로 사라지므로, 개인 PC가 아닌 공용PC에서 작업할 때 안전합니다.

### 방식 B — `.env` 파일 (개인 PC 권장)

`.env.example`을 복사해 `.env`로 이름을 바꾸고 실제 키 값을 채워 넣습니다.

```
OPENAI_API_KEY=여기에_본인의_OpenAI_키
KAKAO_API_KEY=여기에_본인의_Kakao_REST_API_키
```

`.env` 파일은 `.gitignore`에 등록되어 있어 Git에 커밋되지 않습니다.

### 키 값 확인 시 주의사항

화면을 캡처해 공유할 때도 키 전체를 출력하지 말고 일부만 확인하는 습관을 들입니다.

```powershell
$env:OPENAI_API_KEY.Substring(0,7)   # 앞 7글자만 확인
$env:KAKAO_API_KEY.Length            # 길이만 확인
```

---

## 5. 실행 방법

```bash
# 기본: 지역 1곳 추천
python travel_planner.py --date "2025-03-15"

# 여러 지역을 한 번에 추천 (예: 2곳)
python travel_planner.py --date "2025-03-15" --count 2

# 캐시를 무시하고 강제로 새로 조회
python travel_planner.py --date "2025-03-15" --count 2 --refresh
```

### 출력 예시

```
[1/3] 1차 추천 생성 중(LLM)... (날짜: 2025-03-15)
  - recommended_city: "제주도"
[2/3] 맛집 검색 중(Kakao Local API)...
  - 맛집 5곳 검색 완료
[3/3] 최종 리포트 생성 중(LLM)...
  - 리포트 생성 완료

완료! 아래 결과 파일을 확인하세요.
  - 원본 데이터: C:\Users\user\Desktop\travel_project\results\2025-03-15_data.json
  - 여행 리포트: C:\Users\user\Desktop\travel_project\results\2025-03-15_travel_plan.md
```

복수 지역 추천과 결과 캐싱의 실제 실행 화면은 "13. 보너스 과제 구현 결과"에서 확인할 수 있습니다.

---

## 6. 결과물 형식

### `results/{date}_data.json`

```json
{
  "date": "2025-10-01",
  "regions": [
    {
      "recommendation": {
        "recommended_city": "부산",
        "weather": "...",
        "events": ["...", "..."],
        "reason": "..."
      },
      "restaurants": [
        {"name": "...", "address": "...", "category": "...", "url": "...", "x": "...", "y": "..."}
      ]
    }
  ],
  "errors": []
}
```

### `results/{date}_travel_plan.md`

지역이 1곳이면 `## 추천 지역` 단일 섹션, 여러 곳이면 `## 추천 지역 1 — 부산`, `## 추천 지역 2 — 경주`처럼 지역별 섹션으로 구성됩니다. 각 지역 섹션에는 추천 이유·날씨 요약·행사/축제·맛집 추천·1일 일정 제안이 포함되고, 문서 맨 끝에는 오류 요약(errors) 섹션이 항상 붙습니다.

---

## 7. 에러 처리 정책

| 상황 | 담당 함수 | 동작 |
|---|---|---|
| API 키 미설정 | `load_api_keys()` | 즉시 종료 + 어떤 키가 없는지와 설정 방법 안내 |
| OpenAI 인증 실패(401/403) | `get_recommendations()` | 핵심 기능이므로 즉시 종료 |
| OpenAI JSON 파싱 실패 | `get_recommendations()` | 프롬프트를 보강해 최대 1회 재시도, 이후 "정보없음" 기본값으로 계속 진행 |
| Kakao 인증 실패(401/403) | `search_restaurants()` | 맛집을 "데이터 없음"으로 처리, 리포트 생성은 중단 없이 계속 |
| Kakao 검색 결과 0건 | `search_restaurants()` | 검색어를 "맛집→음식점→도시명" 순으로 바꿔 최대 2회 재시도 |
| 네트워크 오류 | `search_restaurants()` | 맛집을 "데이터 없음"으로 처리하고 계속 진행 |
| 리포트 생성 중 오류 | `generate_report()` | Python으로 조립한 기본 템플릿으로 대체 |
| 캐시 파일 손상 | `load_cache_if_exists()` | 캐시를 무시하고 API를 새로 호출 |

추가로, LLM이 최종 리포트를 코드블록(` ``` `)으로 감싸거나 제목(H1)을 중복으로 넣는 경우가 실제로 발생해, `strip_code_fence()` 함수와 중복 제목 제거 로직으로 후처리하도록 보강했습니다.

---

## 8. 테스트 검증 내역

아래 상황을 실제로 발생시켜 정상 동작을 검증했습니다.

| 테스트 항목 | 재현 방법 | 결과 |
|---|---|---|
| CLI 옵션 누락 / 날짜 형식 오류 | `--date` 없이 실행, `--date "2026-13-99"` | 사용법 안내 후 종료 |
| API 키 미설정 | `$env:OPENAI_API_KEY=""` 후 실행 | `[AUTH_ERROR]` 즉시 종료 + 설정 안내 |
| OpenAI 인증 실패 | 잘못된 형식의 키로 실행 | `[AUTH_ERROR]` 즉시 종료 |
| Kakao 인증 실패(401) | `$env:KAKAO_API_KEY="invalid_test_key_1234"` | 맛집 "데이터 없음" 처리 후 `[3/3]`까지 정상 완주 |
| 맛집 검색 0건 | 존재하지 않는 지명으로 `search_restaurants()` 직접 호출 | 검색어 3종 순차 재시도 후 "데이터 없음" 표기 |
| 정상 실행(2회 이상) | 서로 다른 날짜(2025-03-15, 2025-09-15)로 반복 실행 | 매번 다른 지역·맛집·리포트가 정상 생성 |
| 복수 지역 추천 | `--count 2`로 실행 | 지역 2곳이 한 번에 추천되고 지역별 섹션으로 리포트 생성 |
| 결과 캐싱 | 동일 `--date`로 재실행 / `--refresh` 추가 재실행 | 캐시 재사용 시 API 미호출, `--refresh` 시 실제 재호출(다른 지역 추천으로 증명) |

---

## 9. 공용PC 보안 주의사항

- 실제 작업은 개인 소유가 아닌 공용PC에서 진행했으므로, API 키는 `.env` 파일이 아닌 **PowerShell 세션 임시 환경변수**로 관리했습니다. 터미널 창을 닫으면 자동 소멸되어 파일로 남지 않습니다.
- 작업 종료 후에는 프로젝트 폴더 삭제 → 클립보드 비우기 → 휴지통 비우기 → 브라우저 캐시/기록 삭제 → 재부팅 순으로 정리했습니다.
- 화면 캡처를 공유할 때는 키 값을 `.Substring()`이나 `.Length`로만 확인해 전체 키가 노출되지 않도록 했습니다.
- 제출용으로는 `.env.example`(실제 키 없이 형식만) 파일을 별도로 남겼습니다.

---

## 10. 트러블슈팅 Q&A

**Q. `can't open file 'C:\...\파일명.py'` 오류가 뜹니다.**
A. 터미널의 현재 작업 폴더와 파일이 저장된 위치가 다르거나, 명령어의 "파일명" 자리에 실제 파일명을 입력하지 않고 그대로 입력한 경우입니다. `cd`로 파일이 있는 폴더로 이동한 뒤 정확한 파일명으로 실행하세요.

**Q. 한글이 깨져서 나옵니다.**
A. 파일 저장 인코딩이 UTF-8이 아닌 경우 발생합니다. 편집기의 인코딩을 UTF-8로 지정해 저장하고, 코드 내 모든 파일 입출력에 `encoding="utf-8"`을 명시하세요.

**Q. `usage: ... error: the following arguments are required: --date` 가 뜹니다.**
A. `--date "YYYY-MM-DD"` 옵션 없이 실행한 경우입니다. 정상 동작이며, 안내된 형식대로 옵션을 추가해 다시 실행하세요.

**Q. `__pycache__` 폴더는 지워도 되나요?**
A. 네. 실행 시 자동으로 재생성되는 컴파일 캐시이므로 삭제해도 프로그램 동작에는 영향이 없습니다. `.gitignore`에도 `__pycache__/`, `*.pyc`가 등록되어 있어 Git에는 추적되지 않습니다.

**Q. 맛집 검색 결과가 "데이터 없음"으로 나옵니다.**
A. Kakao API 인증 실패이거나, 검색어 3종(맛집/음식점/도시명)으로 재시도해도 결과가 0건인 경우입니다. 프로그램은 중단되지 않고 리포트 생성까지 계속 진행합니다.

**Q. `--count`를 크게 줘도 되나요?**
A. 최대 5까지 지원합니다(`MAX_REGION_COUNT`). 그 이상 입력하면 자동으로 5로 조정되고 안내 메시지가 출력됩니다. 지역 수가 많아질수록 API 호출 횟수도 늘어나니 참고하세요.

**Q. 캐시가 있는데도 최신 결과를 보고 싶으면요?**
A. `--refresh` 옵션을 붙이면 저장된 캐시를 무시하고 API를 처음부터 다시 호출합니다.

---

## 11. 프로젝트 구조

```
travel_project/
├── travel_planner.py       ← 메인 프로그램 (보너스 기능 포함, 19KB)
├── requirements.txt        ← 필요 패키지 목록 (openai, requests, python-dotenv)
├── README.md                ← 이 문서
├── .gitignore                ← .env, __pycache__/, *.pyc 등 Git 제외 목록
├── .env.example                ← API 키 입력 템플릿 (실제 키 없음)
└── results/                    ← 실행 결과 저장 폴더 (자동 생성)
    ├── 2025-03-15_data.json / 2025-03-15_travel_plan.md
    ├── 2025-09-15_data.json / 2025-09-15_travel_plan.md
    └── 2025-10-01_data.json / 2025-10-01_travel_plan.md   ← 보너스 기능 검증용(복수 지역 2곳)
```

---

## 12. 전체 소스 코드 (travel_planner.py)

기본 요구사항 완료 후 두 보너스 과제(복수 지역 추천, 결과 캐싱)를 실제로 반영한 최종 버전이다. `--count`(추천받을 지역 수)와 `--refresh`(캐시 무시) 옵션이 추가되었다. 전체 코드(약 457줄)를 그대로 수록한다.

```python
"""
Python 응용: API 활용 국내 여행지 추천 프로그램 (보너스 과제 반영판)
- LLM(OpenAI)으로 날짜 기반 1차 여행지 추천(JSON) — 복수 지역 지원
- Kakao Local API로 추천 도시별 맛집 검색
- LLM(OpenAI)으로 최종 여행 리포트(Markdown) 생성 — 지역별 섹션 포함
- 결과를 results/ 폴더에 JSON + Markdown으로 저장
- [보너스 1] --count 옵션으로 여러 지역을 한 번에 추천
- [보너스 2] 동일한 날짜로 재실행 시 API 재호출 없이 저장된 결과를 재사용(캐싱)

실행 예시:
    python travel_planner_with_bonus.py --date "2025-03-15"
    python travel_planner_with_bonus.py --date "2025-03-15" --count 3
    python travel_planner_with_bonus.py --date "2025-03-15" --refresh
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime

import requests

try:
    from dotenv import load_dotenv
    load_dotenv()  # .env 파일이 있으면 읽어서 환경변수로 등록 (없어도 에러 아님)
except ImportError:
    pass  # python-dotenv 미설치 시에도 세션 환경변수($env:)만으로 동작 가능

from openai import OpenAI
from openai import AuthenticationError, APIError


# =========================================================
# 0. 설정값
# =========================================================
OPENAI_MODEL = "gpt-4o-mini"
KAKAO_SEARCH_COUNT = 5          # 맛집 검색 권장 개수
LLM_JSON_RETRY_LIMIT = 1        # LLM JSON 파싱 실패 시 재시도 횟수 (요구사항: 최대 1회)
PLACE_EMPTY_RETRY_LIMIT = 2     # 맛집 검색 0건 시 파라미터를 바꿔 재시도할 횟수 (최대 2회)
DEFAULT_REGION_COUNT = 1        # [보너스 1] --count 미지정 시 기본 추천 지역 수
MAX_REGION_COUNT = 5            # [보너스 1] --count 상한 (과도한 API 호출 방지)


# =========================================================
# 유틸: LLM 응답에서 코드펜스(```markdown ... ``` 등) 제거
# =========================================================
def strip_code_fence(text: str) -> str:
    """LLM 응답이 ```json ... ``` 또는 ```markdown ... ``` 로 감싸져 오는 경우 제거"""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


# =========================================================
# 1. API 키 로드 및 검증 (제약사항: 키 미설정 시 즉시 종료)
# =========================================================
def load_api_keys():
    openai_key = os.getenv("OPENAI_API_KEY")
    kakao_key = os.getenv("KAKAO_API_KEY")

    missing = []
    if not openai_key:
        missing.append("OPENAI_API_KEY")
    if not kakao_key:
        missing.append("KAKAO_API_KEY")

    if missing:
        print(f"[AUTH_ERROR] 다음 환경변수가 설정되지 않았습니다: {', '.join(missing)}")
        print('→ PowerShell 예시: $env:OPENAI_API_KEY="본인 키"')
        print("→ .env 파일을 쓰는 경우: OPENAI_API_KEY=본인 키 형식으로 저장했는지 확인하세요.")
        sys.exit(1)

    return openai_key, kakao_key


# =========================================================
# 2. CLI 인자 처리 + 날짜 검증
#    [보너스 1] --count 추가
#    [보너스 2] --refresh 추가
# =========================================================
def parse_args():
    parser = argparse.ArgumentParser(
        description="국내 여행지 추천 프로그램 (복수 지역 + 결과 캐싱 지원)",
        usage='python travel_planner_with_bonus.py --date "YYYY-MM-DD" [--count N] [--refresh]'
    )
    parser.add_argument("--date", required=True, help="여행 날짜 (형식: YYYY-MM-DD)")
    parser.add_argument(
        "--count", type=int, default=DEFAULT_REGION_COUNT,
        help=f"추천받을 지역 수 (기본 {DEFAULT_REGION_COUNT}, 최대 {MAX_REGION_COUNT})"
    )
    parser.add_argument(
        "--refresh", action="store_true",
        help="이미 저장된 결과가 있어도 캐시를 무시하고 API를 다시 호출"
    )
    args = parser.parse_args()

    try:
        datetime.strptime(args.date, "%Y-%m-%d")
    except ValueError:
        parser.print_usage()
        print('날짜 형식이 올바르지 않습니다. 예: --date "2025-03-15"')
        sys.exit(1)

    if args.count < 1:
        print("--count는 1 이상이어야 합니다. 1로 조정합니다.")
        args.count = 1
    if args.count > MAX_REGION_COUNT:
        print(f"--count는 최대 {MAX_REGION_COUNT}까지 지원합니다. {MAX_REGION_COUNT}로 조정합니다.")
        args.count = MAX_REGION_COUNT

    return args


# =========================================================
# [보너스 2] 결과 캐싱 — 동일 날짜 재실행 시 저장된 데이터 재사용
# =========================================================
def load_cache_if_exists(date: str):
    """results/{date}_data.json이 있으면 읽어서 반환, 없으면 None"""
    path = os.path.join(os.getcwd(), "results", f"{date}_data.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        # 캐시 파일이 손상된 경우 캐시를 무시하고 새로 조회
        return None


# =========================================================
# 3. LLM 1차 추천 (JSON) — [보너스 1] 여러 지역을 한 번에 추천
#    파싱 실패 시 최대 1회 재시도
# =========================================================
def get_recommendations(client: OpenAI, date: str, count: int, errors: list):
    base_prompt = f"""
{date}에 여행하기 좋은 국내 도시를 서로 겹치지 않게 {count}곳 추천해줘.
각 도시는 우선순위(추천도) 순서로 나열해줘.
반드시 아래 JSON 형식으로만 답하고, 다른 설명은 절대 붙이지 마.

{{
  "recommendations": [
    {{
      "recommended_city": "도시명",
      "weather": "해당 시기 일반적 날씨 요약",
      "events": ["행사/축제 후보1", "행사/축제 후보2"],
      "reason": "추천 근거 2~4문장"
    }}
  ]
}}

recommendations 배열의 길이는 반드시 {count}여야 해.
""".strip()

    prompt = base_prompt
    for attempt in range(1, LLM_JSON_RETRY_LIMIT + 2):
        try:
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
            content = strip_code_fence(response.choices[0].message.content)
            if content.lower().startswith("json"):
                content = content[4:].strip()

            data = json.loads(content)
            recs = data.get("recommendations")

            if not isinstance(recs, list) or not recs:
                raise ValueError("recommendations 배열이 비어있거나 없음")

            required_keys = ["recommended_city", "weather", "events", "reason"]
            for rec in recs:
                if not all(k in rec for k in required_keys):
                    raise ValueError("필수 키 누락")

            # 요청한 개수보다 적게 왔으면 있는 만큼만 사용 (많이 왔으면 앞에서부터 count개만 사용)
            return recs[:count]

        except (json.JSONDecodeError, ValueError) as e:
            print(f"[LLM_PARSE_ERROR] {attempt}번째 시도 JSON 파싱 실패: {e}")
            errors.append({
                "step": "recommendation",
                "type": "LLM_PARSE_ERROR",
                "message": f"attempt {attempt}: {str(e)}"
            })
            if attempt <= LLM_JSON_RETRY_LIMIT:
                prompt = base_prompt + "\n\n반드시 JSON 객체만 출력해. 앞뒤에 어떤 텍스트도 붙이지 마."
                time.sleep(1)
                continue
            # 재시도 소진 → 기본값 1건으로 진행 (프로그램은 계속)
            return [{
                "recommended_city": "정보없음",
                "weather": "정보없음",
                "events": [],
                "reason": "LLM 응답 파싱에 실패하여 추천 정보를 가져오지 못했습니다."
            }]

        except AuthenticationError:
            print("[AUTH_ERROR] OpenAI 인증에 실패했습니다 (401/403). API 키를 다시 확인하세요.")
            errors.append({"step": "recommendation", "type": "AUTH_ERROR", "message": "OpenAI 401/403"})
            sys.exit(1)

        except APIError as e:
            print(f"[API_ERROR] OpenAI 호출 중 오류: {e}")
            errors.append({"step": "recommendation", "type": "API_ERROR", "message": str(e)})
            if attempt <= LLM_JSON_RETRY_LIMIT:
                time.sleep(1)
                continue
            return [{
                "recommended_city": "정보없음",
                "weather": "정보없음",
                "events": [],
                "reason": "API 오류로 추천 정보를 가져오지 못했습니다."
            }]


# =========================================================
# 4. Kakao Local API 맛집 검색 (지역별로 동일하게 반복 호출)
# =========================================================
def search_restaurants(kakao_key: str, city: str, errors: list):
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {kakao_key}"}
    queries = [f"{city} 맛집", f"{city} 음식점", city]

    for attempt, query in enumerate(queries[:PLACE_EMPTY_RETRY_LIMIT + 1], start=1):
        try:
            res = requests.get(
                url, headers=headers,
                params={"query": query, "size": KAKAO_SEARCH_COUNT},
                timeout=10
            )

            if res.status_code in (401, 403):
                print(f"[AUTH_ERROR] Kakao 인증 실패({res.status_code}). 키 설정을 확인하세요.")
                print(f"→ '{city}' 맛집 섹션은 '데이터 없음'으로 처리하고 계속 진행합니다.")
                errors.append({
                    "step": "place_search",
                    "type": "AUTH_ERROR",
                    "message": f"HTTP {res.status_code} (city={city})"
                })
                return []

            res.raise_for_status()
            documents = res.json().get("documents", [])

            if documents:
                return [{
                    "name": d.get("place_name", ""),
                    "address": d.get("address_name", ""),
                    "category": d.get("category_name", ""),
                    "url": d.get("place_url", ""),
                    "x": d.get("x", ""),
                    "y": d.get("y", ""),
                } for d in documents]

            print(f"[EMPTY_RESULT] '{query}' 검색 결과 0건 ({attempt}/{PLACE_EMPTY_RETRY_LIMIT + 1}차 시도)")
            errors.append({
                "step": "place_search",
                "type": "EMPTY_RESULT",
                "message": f"0 results for query='{query}'"
            })
            time.sleep(0.5)
            continue

        except requests.exceptions.RequestException as e:
            print(f"[NETWORK_ERROR] Kakao API 호출 실패: {e}")
            errors.append({"step": "place_search", "type": "NETWORK_ERROR", "message": str(e)})
            return []

    print(f"[EMPTY_RESULT] '{city}' 재시도 후에도 맛집 검색 결과가 없습니다. '데이터 없음'으로 표기합니다.")
    return []


# =========================================================
# 5. LLM 최종 리포트 생성 (Markdown) — [보너스 1] 지역별 섹션 구성
# =========================================================
def generate_region_section(client: OpenAI, region_no: int, recommendation: dict,
                             restaurants: list, errors: list) -> str:
    """지역 1곳에 대한 리포트 섹션(##으로 시작)을 생성"""
    city = recommendation.get("recommended_city", "정보없음")
    weather = recommendation.get("weather", "정보없음")
    events = recommendation.get("events", [])
    reason = recommendation.get("reason", "")

    if restaurants:
        restaurant_text = "\n".join(f"- {r['name']} ({r['address']})" for r in restaurants)
    else:
        restaurant_text = "데이터 없음 (장소 검색 결과 0건 또는 API 오류)"

    prompt = f"""
아래 정보를 바탕으로 국내 여행 추천 리포트의 한 지역 섹션을 Markdown으로 작성해줘.

[출력 형식 규칙 - 반드시 지켜]
1. 코드블록(```)으로 감싸지 마. 순수 Markdown 텍스트만 출력해.
2. # 으로 시작하는 제목(H1)은 절대 넣지 마.
3. 출력의 맨 첫 줄은 반드시 "### 추천 이유" 여야 해. 지역명 제목은 이미 별도로 붙일 것이므로 넣지 마.

반드시 아래 섹션을 모두 포함해:
### 추천 이유
### 날씨 요약
### 행사/축제
### 맛집 추천
### 1일 일정 제안 (오전/오후/저녁)

[입력 정보]
- 추천 지역: {city}
- 날씨: {weather}
- 행사/축제 후보: {', '.join(events) if events else '없음'}
- 추천 이유: {reason}
- 맛집 목록:
{restaurant_text}

맛집 목록이 "데이터 없음"이면 맛집 추천 섹션에도 "데이터 없음"이라고 그대로 표기해.
""".strip()

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
        )
        body = strip_code_fence(response.choices[0].message.content)

        lines = body.split("\n")
        i = 0
        while i < len(lines) and lines[i].strip() == "":
            i += 1
        if i < len(lines) and lines[i].strip().startswith("#") and not lines[i].strip().startswith("###"):
            lines = lines[i + 1:]
        body = "\n".join(lines).strip()

    except (AuthenticationError, APIError) as e:
        print(f"[REPORT_ERROR] '{city}' 리포트 생성 중 오류: {e}. 기본 템플릿으로 대체합니다.")
        errors.append({"step": "report_generation", "type": "API_ERROR", "message": f"{city}: {str(e)}"})
        body = f"""### 추천 이유
{reason}

### 날씨 요약
{weather}

### 행사/축제
{', '.join(events) if events else '데이터 없음'}

### 맛집 추천
{restaurant_text}

### 1일 일정 제안
리포트 자동 생성에 실패하여 기본 템플릿으로 표시되었습니다."""

    return f"## 추천 지역 {region_no} — {city}\n\n{body}"


def generate_report(client: OpenAI, date: str, regions: list, errors: list) -> str:
    """regions: [{"recommendation": {...}, "restaurants": [...]}, ...]"""
    sections = []
    for idx, region in enumerate(regions, start=1):
        section = generate_region_section(
            client, idx, region["recommendation"], region["restaurants"], errors
        )
        sections.append(section)

    body = "\n\n".join(sections)

    if errors:
        errors_text = "\n".join(f"- [{e['step']}] {e['type']}: {e['message']}" for e in errors)
    else:
        errors_text = "없음"

    header = f"# {date} 국내 여행 추천 리포트 ({len(regions)}개 지역)\n\n"
    footer = f"\n\n## 오류 요약(errors)\n{errors_text}\n"

    return header + body + footer


# =========================================================
# 6. 결과 저장 — [보너스 1] regions 배열로 저장 (복수 지역 지원)
# =========================================================
def save_results(date: str, regions: list, report: str, errors: list):
    results_dir = os.path.join(os.getcwd(), "results")
    os.makedirs(results_dir, exist_ok=True)

    raw_data = {
        "date": date,
        "regions": regions,   # [{"recommendation": {...}, "restaurants": [...]}, ...]
        "errors": errors,
    }

    json_path = os.path.join(results_dir, f"{date}_data.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(raw_data, f, ensure_ascii=False, indent=2)

    md_path = os.path.join(results_dir, f"{date}_travel_plan.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(report)

    return json_path, md_path


# =========================================================
# 7. 메인 실행 흐름 — [보너스 2] 캐시 확인 로직 포함
# =========================================================
def main():
    args = parse_args()
    date = args.date
    openai_key, kakao_key = load_api_keys()
    client = OpenAI(api_key=openai_key)

    errors = []

    # ---- [보너스 2] 캐시 확인 ----
    cached = None if args.refresh else load_cache_if_exists(date)

    if cached:
        print(f"[CACHE] 기존 결과를 재사용합니다 → results/{date}_data.json (API를 호출하지 않습니다)")
        regions = cached.get("regions", [])
        errors = cached.get("errors", [])
        cities = ", ".join(r["recommendation"].get("recommended_city", "?") for r in regions)
        print(f'  - 캐시된 추천 지역({len(regions)}곳): {cities}')
    else:
        print(f'[1/3] 1차 추천 생성 중(LLM)... (날짜: {date}, 지역 수: {args.count})')
        recommendations = get_recommendations(client, date, args.count, errors)
        cities = ", ".join(r.get("recommended_city", "?") for r in recommendations)
        print(f'  - 추천 지역({len(recommendations)}곳): {cities}')

        print("[2/3] 지역별 맛집 검색 중(Kakao Local API)...")
        regions = []
        for rec in recommendations:
            city = rec.get("recommended_city", "정보없음")
            restaurants = search_restaurants(kakao_key, city, errors)
            print(f"  - {city}: 맛집 {len(restaurants)}곳 검색 완료" if restaurants
                  else f"  - {city}: 맛집 검색 결과 없음 (데이터 없음으로 진행)")
            regions.append({"recommendation": rec, "restaurants": restaurants})

    print("[3/3] 최종 리포트 생성 중(LLM)...")
    report = generate_report(client, date, regions, errors)
    print("  - 리포트 생성 완료")

    json_path, md_path = save_results(date, regions, report, errors)

    print(f"\n완료! 아래 결과 파일을 확인하세요.")
    print(f"  - 원본 데이터: {json_path}")
    print(f"  - 여행 리포트: {md_path}")
    if errors:
        print(f"  - 처리 중 {len(errors)}건의 오류/경고가 기록되었습니다 (JSON의 errors 항목 참고).")


if __name__ == "__main__":
    main()
```

---

## 13. 보너스 과제 구현 결과 — 복수 지역 추천 & 결과 캐싱

기본 요구사항 완료 후 두 보너스 기능을 실제로 구현했다. CLI에 `--count`(추천받을 지역 수)와 `--refresh`(캐시 무시하고 강제 재조회) 옵션을 추가했다.

### 실행 방법

```bash
# 여러 지역을 한 번에 추천받기 (예: 2곳)
python travel_planner.py --date "2025-10-01" --count 2

# 같은 날짜로 다시 실행 → API 호출 없이 캐시된 결과 재사용
python travel_planner.py --date "2025-10-01" --count 2

# 캐시를 무시하고 강제로 새로 조회
python travel_planner.py --date "2025-10-01" --count 2 --refresh
```

### 복수 지역 추천 — 실행 결과

![](images/bonus2.png)

*PowerShell — --count 2로 실행한 결과, 부산·경주 2개 지역이 한 번에 추천되고 [1/3]~[3/3] 전 과정이 정상 완료된 화면*

![](images/bonus3.png)

*VS Code — 2025-10-01_travel_plan.md 결과. "추천 지역 1 – 부산", "추천 지역 2 – 경주"로 지역별 섹션이 분리되어 생성됨*

![](images/bonus4.png)

*VS Code — 2025-10-01_data.json 결과. "regions" 배열 안에 지역별 recommendation·restaurants가 구조화되어 저장됨*

![](images/bonus5.png)

*results 폴더 — 기존 2025-03-15·2025-09-15 결과는 그대로 보존된 채 2025-10-01 결과(2개 지역 포함, 5KB)만 새로 추가된 모습*

### 결과 캐싱 — 실행 결과

![](images/bonus6.png)

*PowerShell — --refresh 없이 동일한 --date로 재실행 시 [CACHE] 기존 결과를 재사용합니다 메시지와 함께 [1/3]·[2/3] 단계 없이 바로 [3/3]로 진행되는 화면*

![](images/bonus7.png)

*PowerShell — --refresh를 붙여 같은 날짜로 재실행하면 캐시를 무시하고 [1/3]부터 다시 API를 호출해, 이번에는 경주 대신 전주가 추천됨(실제로 API가 재호출되었음을 증명)*

### 최종 프로젝트 폴더

![](images/bonus1.png)

*최종 travel_project 폴더 — travel_planner.py가 보너스 기능이 반영된 19KB 버전으로 교체된 모습*

---

## 14. 요구사항 자체 점검표

| 항목 | 확인 |
|---|---|
| CLI 기반 Python 프로그램(travel_planner.py) 완성 | ✅ |
| `--date "YYYY-MM-DD"` 옵션으로 실행, 형식 검증 포함 | ✅ |
| 실행 시 진행 로그 + 결과 저장 경로 출력 | ✅ |
| `results/`에 원본 데이터 JSON + 최종 리포트 Markdown 저장 | ✅ |
| API 키를 코드에 직접 작성하지 않음 | ✅ |
| `.env`/환경변수로 키 관리, `.gitignore`에 `.env` 등록 | ✅ |
| 지도 API 실패해도 리포트 생성은 계속 진행 | ✅ |
| 실제 오류 상황(키 미설정/인증 실패/검색 0건/옵션 오류) 재현 검증 | ✅ |
| (보너스) 복수 지역 추천 — `--count` 옵션 | ✅ |
| (보너스) 결과 캐싱 — 재실행/`--refresh` | ✅ |

---

*본 README는 실제 개발·검증 과정을 거쳐 작성되었습니다. 개발 과정의 시행착오와 상세 검증 기록은 별도 작업과정보고서를 참고하세요.*
