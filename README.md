# 국내 여행지 추천 프로그램

날짜를 입력하면 AI(OpenAI)가 국내 여행지를 1차 추천하고, Kakao Local API로 해당 지역의 맛집을 검색한 뒤, 두 정보를 종합해 최종 여행 리포트(Markdown)를 생성하는 CLI 프로그램입니다.

모든 기능과 에러 처리 로직은 실제 성공/실패 케이스를 직접 발생시켜 검증을 완료했습니다. (검증 내역은 "9. 테스트 검증 내역" 참고)

---

## 0. 미션 개요

**과제명**: Python 응용 — API 활용 국내 여행지 추천 프로그램 개발

단일 API 호출이 아니라, **서로 다른 API들을 엮어 하나의 인사이트를 만드는 흐름**을 구현하는 것이 이 과제의 핵심입니다. 사용자가 여행 날짜를 입력하면:

1. **LLM API**(OpenAI)가 해당 시기에 여행하기 좋은 지역을 추천하고
2. **지도/장소 API**(Kakao Local)가 그 지역의 맛집을 검색하고
3. 다시 **LLM API**가 위 두 결과를 종합해 사람이 읽을 수 있는 최종 여행 리포트를 작성합니다.

### 과제 목표 (학습자가 스스로 설명할 수 있어야 하는 것)

- [x] REST API의 요청/응답 구조와 HTTP 메서드(GET/POST)의 차이
  → 이 프로그램은 OpenAI(POST, JSON body)와 Kakao Local(GET, query parameter) 두 가지 호출 방식을 모두 사용합니다.
- [x] LLM 출력 결과를 구조화(JSON)하여 다음 단계(지도/장소 검색)의 입력으로 활용하는 흐름
  → `get_recommendation()`의 반환값 `recommended_city`가 그대로 `search_restaurants()`의 입력 파라미터로 전달됩니다.
- [x] 외부 API 호출에서 발생하는 대표 오류(인증/쿼터/네트워크/파싱)와 대응 원칙
  → 아래 "7. 에러 처리 정책" 표에 정리했고, 실제로 4가지 오류 상황을 재현해 검증했습니다.
- [x] API 키를 코드에 직접 작성하지 않고 `.env`/환경변수로 관리하는 이유
  → 협업/공유 시 실수로 키가 공개되는 것을 방지, 키 교체 시 코드 수정 불필요, 과금/쿼터 서비스에서의 사고 예방.

---

## 1. 기능 목록

| 구분 | 내용 |
|---|---|
| CLI 인터페이스 | `argparse` 기반, `--date "YYYY-MM-DD"` 필수 옵션, 날짜 형식 검증 |
| 1차 LLM 추천 | OpenAI가 날짜 기반으로 도시 1곳을 JSON(`recommended_city`, `weather`, `events`, `reason`)으로 추천 |
| 장소 검색 | Kakao Local API로 추천 도시의 맛집 최대 5곳 검색 (`name`, `address`, `category`, `url`, `x`, `y`) |
| 2차 LLM 리포트 생성 | 1차 추천 + 맛집 목록을 종합해 Markdown 리포트 작성 (추천지역/이유, 날씨, 행사, 맛집, 1일 일정) |
| 에러 처리 | 키 미설정 즉시 종료, LLM JSON 파싱 실패 1회 재시도, 장소 검색 0건 최대 2회 재시도, 지도 API 인증 실패 시 "데이터 없음" 처리 후 계속 진행 |
| 결과 저장 | `results/{date}_data.json`(원본 데이터+오류기록), `results/{date}_travel_plan.md`(최종 리포트) |
| 보안 | API 키는 `os.getenv()`로만 로드, 코드/README/결과물에 실키 미포함, `.gitignore`로 `.env` 보호 |

---

## 2. 프로그램 흐름

```
날짜 입력 (--date)
   │
   ▼
① OpenAI 1차 여행지 추천 (JSON)
   recommended_city / weather / events / reason
   │
   ▼
② Kakao Local API로 해당 지역 맛집 검색 (최대 5곳)
   │
   ▼
③ OpenAI가 ①+② 정보를 종합해 최종 리포트 작성 (Markdown)
   │
   ▼
results/ 폴더에 저장
   ├── {date}_data.json        (원본 데이터 + 오류 기록)
   └── {date}_travel_plan.md   (최종 여행 리포트)
```

LLM API는 총 2회 호출됩니다. 1차 호출은 구조화된 JSON을, 2차 호출은 사람이 읽을 Markdown 리포트를 생성하는 데 사용됩니다.

---

## 3. 프로젝트 구조

```
travel_project/
├── travel_planner.py     ← 메인 프로그램 (하단 "전체 소스 코드" 참고)
├── requirements.txt      ← 필요 패키지 목록
├── README.md              ← 이 문서
├── .gitignore             ← .env, venv, 캐시 등 Git 제외 목록
├── .env.example           ← API 키 입력 템플릿 (실제 키 없음)
└── results/               ← 실행 결과 저장 폴더 (자동 생성)
    ├── 2025-03-15_data.json
    ├── 2025-03-15_travel_plan.md
    ├── 2025-09-15_data.json
    └── 2025-09-15_travel_plan.md
```

---

## 4. 설치

```
pip install -r requirements.txt
```

`requirements.txt` 내용:
```
openai>=1.0.0
requests>=2.31.0
python-dotenv>=1.0.0
```

---

## 5. API 키 설정

이 프로그램은 **코드에 API 키를 직접 작성하지 않고, 환경변수를 통해서만** 키를 읽습니다 (`os.getenv()` 사용). 두 가지 방식 중 상황에 맞게 선택하세요.

### 방법 1) 세션 환경변수 — 공용PC 권장

PowerShell 창을 닫으면 값이 자동으로 사라져 안전합니다.

```
$env:OPENAI_API_KEY="본인의 OpenAI 키"
$env:KAKAO_API_KEY="본인의 Kakao REST API 키"
```

macOS / Linux:
```
export OPENAI_API_KEY="본인의 OpenAI 키"
export KAKAO_API_KEY="본인의 Kakao REST API 키"
```

**설정이 잘 됐는지 확인** (키 값 전체를 노출하지 않고 형식만 확인):
```
$env:OPENAI_API_KEY.Substring(0,3)   # "sk-" 가 나와야 정상
$env:KAKAO_API_KEY.Length            # 숫자가 나오면 값이 들어있는 것
```

> ⚠️ 주의: PowerShell 창을 새로 열거나 컴퓨터를 재시작하면 세션 환경변수는 초기화됩니다. 매번 실행 전에 다시 설정해야 합니다. 이는 공용PC에서 키가 남지 않도록 **의도적으로 설계된 동작**입니다.

### 방법 2) `.env` 파일 — 개인PC 권장

`.env.example` 파일을 복사해 `.env`로 이름을 바꾸고 실제 키 값을 채워 넣으세요.

```
OPENAI_API_KEY=sk-실제키
KAKAO_API_KEY=실제키
```

`.env`는 `.gitignore`에 등록되어 있어 Git에는 올라가지 않습니다. 작업 종료 후에는 파일을 삭제하거나 최소한 실제 값을 지우는 것을 권장합니다.

---

## 6. 실행 방법

```
python travel_planner.py --date "2025-03-15"
```

- `--date`는 필수이며 `YYYY-MM-DD` 형식이어야 합니다.
- 형식이 틀리면 사용법을 안내하고 종료합니다. (예: `--date "2026-13-99"` → 오류 안내 후 종료)
- `--date` 옵션 자체를 생략하면 `argparse`가 자동으로 필수 인자 누락 오류를 출력하고 종료합니다.

### 정상 실행 시 출력 예시

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

### 결과물 확인 방법

```
type results\2025-03-15_travel_plan.md
```
또는 VSCode/메모장으로 `results/` 폴더의 `.md`, `.json` 파일을 직접 열어 확인합니다.

---

## 7. 결과물 설명

실행이 끝나면 `results/` 폴더에 아래 2개 파일이 생성됩니다.

### `{date}_data.json`

```json
{
  "date": "2025-03-15",
  "recommendation": {
    "recommended_city": "제주도",
    "weather": "3월 중순의 제주도는 온화한 날씨로, 평균 기온은 10도에서 15도 사이입니다.",
    "events": ["제주 봄꽃 축제", "제주 해비치 아트 페스티벌"],
    "reason": "제주도는 아름다운 자연경관과 다양한 문화행사가 있어 여행객들에게 인기가 많습니다."
  },
  "restaurants": [
    {
      "name": "원담",
      "address": "제주특별자치도 제주시 이도일동 1260-11",
      "category": "음식점 > 한식",
      "url": "http://place.map.kakao.com/...",
      "x": "126.xxxxx",
      "y": "33.xxxxx"
    }
  ],
  "errors": []
}
```

### `{date}_travel_plan.md`

아래 섹션을 항상 포함합니다.

```markdown
# 2025-03-15 국내 여행 추천 리포트

## 추천 지역
## 추천 이유
## 날씨 요약
## 행사/축제
## 맛집 추천
## 1일 일정 제안 (오전/오후/저녁)
## 오류 요약(errors)
```

맛집 검색 결과가 없는 경우 "맛집 추천" 섹션에는 "데이터 없음"이 표기되며, 오류/경고가 발생한 경우 "오류 요약(errors)" 섹션에 `[step] type: message` 형식으로 기록됩니다. 정상 실행 시에는 "없음"으로 표기됩니다.

---

## 8. 에러 처리 정책

| 상황 | 코드 | 동작 |
|---|---|---|
| API 키 미설정 (`OPENAI_API_KEY` 또는 `KAKAO_API_KEY` 없음) | `load_api_keys()` | 즉시 종료 + 어떤 키가 없는지, 설정 방법(PowerShell/.env)을 안내 |
| OpenAI 인증 실패 (401/403) | `get_recommendation()` | 핵심 기능이므로 즉시 종료 |
| OpenAI JSON 파싱 실패 | `get_recommendation()` | 프롬프트를 더 엄격하게 보강해 **최대 1회 재시도**. 그래도 실패하면 "정보없음" 기본값으로 프로그램은 계속 진행 |
| Kakao 인증 실패 (401/403) | `search_restaurants()` | 맛집 섹션을 "데이터 없음"으로 처리하고, **리포트 생성은 중단 없이 계속 진행** |
| Kakao 검색 결과 0건 (`EMPTY_RESULT`) | `search_restaurants()` | 검색어를 `"{city} 맛집"` → `"{city} 음식점"` → `"{city}"` 순으로 바꿔가며 **최대 2회 재시도** 후, 그래도 0건이면 "데이터 없음"으로 표기 |
| 네트워크 오류 (Kakao 호출 실패) | `search_restaurants()` | 맛집을 "데이터 없음"으로 처리하고 계속 진행 |
| 최종 리포트 생성 중 OpenAI 오류 | `generate_report()` | Python으로 직접 조립한 기본 템플릿으로 대체하여 리포트 생성은 계속 진행 |

모든 오류/경고는 `errors` 배열(빈 배열이어도 항상 포함되는 구조)과 리포트의 "오류 요약" 섹션에 기록되어, 실행 후 무엇이 어디서 실패했는지 추적할 수 있습니다.

---

## 9. 테스트 검증 내역

아래 항목들은 실제로 오류 상황을 재현하여 정상 동작을 확인했습니다.

| 테스트 | 재현 방법 | 결과 |
|---|---|---|
| CLI 옵션 누락 | `--date` 없이 실행 | `argparse`가 필수 인자 오류 출력 후 종료 |
| 날짜 형식 오류 | `--date "2026-13-99"` | 사용법 안내 후 종료 |
| API 키 미설정 | `$env:OPENAI_API_KEY=""` 후 실행 | `[AUTH_ERROR]` 즉시 종료 + 설정 안내 |
| OpenAI 인증 실패 | 잘못된 형식의 키로 실행 | `[AUTH_ERROR] OpenAI 인증에 실패했습니다 (401/403)` 즉시 종료 |
| Kakao 인증 실패 (401) | `$env:KAKAO_API_KEY="invalid_test_key_1234"` | 맛집 "데이터 없음" 처리, `[3/3]`까지 정상 완주, `errors`에 기록 |
| 맛집 검색 0건 | 존재하지 않는 임의 지명으로 `search_restaurants()` 직접 호출 | 검색어 3종 순차 재시도 후 빈 리스트 반환, `errors`에 3건 기록 |
| 정상 실행 (2회 이상) | 서로 다른 날짜(2025-03-15, 2025-09-15)로 반복 실행 | 제주도/강릉 등 매번 다른 지역 추천, 맛집 5곳, 리포트 정상 생성 |

> 💡 개발 중 발견되어 수정된 이슈: 최종 리포트에 OpenAI가 응답을 코드블록으로 감싸거나 자체 제목을 중복으로 넣는 경우가 있어, 코드에서 코드펜스 제거 및 중복 제목 제거 로직(`strip_code_fence()`)을 추가하고 프롬프트에도 형식 규칙을 명시하여 해결했습니다.

---

## 10. 자체 점검표

제출 전 아래 체크리스트로 스스로 확인하세요.

### 📁 최종 결과물
- [x] CLI 기반 Python 프로그램 (`travel_planner.py`) 완성
- [x] `--date "YYYY-MM-DD"` 옵션으로 실행됨
- [x] 실행 시 진행 로그(`[1/3]~[3/3]`) + 결과 저장 경로 출력
- [x] `results/` 폴더에 원본 데이터 JSON 1개 이상 생성됨 (1차 추천 + 맛집 검색 결과 포함)
- [x] 최종 여행 리포트 `.md` 파일 생성됨
- [x] `README.md` 작성 (개요/실행법/키설정/결과확인 포함)
- [x] README에 API 키 유출 방지 주의사항 포함

### ⚙️ 기능 요구사항
- [x] `argparse`로 CLI 실행 가능, 필수 옵션 검증
- [x] 날짜 형식 틀리면 사용법 출력 후 종료
- [x] LLM API = OpenAI 사용
- [x] 지도/장소 API = Kakao Local 사용
- [x] 1차 JSON에 `recommended_city`(string), `weather`(string), `events`(array), `reason`(string) 모두 포함
- [x] 맛집 필드에 `name`, `address`, `category`, `url`, `x`, `y` 포함
- [x] 맛집 5곳(권장) 검색
- [x] 맛집 0건이어도 프로그램 중단 없이 계속 진행
- [x] 최종 리포트에 추천지역/이유, 날씨, 행사, 맛집, 1일 일정 모두 포함

### 🖥️ 개발 환경
- [x] Python 3.10 이상 사용
- [x] 터미널(PowerShell)에서 실행 가능 (웹 UI 아님)
- [x] `openai`, `requests`, `python-dotenv` 패키지 `requirements.txt`로 관리

### 🔒 제약사항 (보안)
- [x] 코드에 API 키 직접 작성 안 함 (`os.getenv()`로만 로드)
- [x] `.env` 또는 환경변수로 키 관리
- [x] `.gitignore`에 `.env` 등록됨
- [x] README/결과물에 실제 키 값 미포함
- [x] 키 미설정 시 즉시 종료 + 안내
- [x] 지도 API 실패해도 리포트 생성은 진행됨
- [x] LLM JSON 파싱 실패 시 재시도 최대 1회로 제한
- [x] `errors` 배열로 모든 오류 기록

### 🧪 실제 검증 여부
- [x] 정상 실행 케이스 2회 이상 (서로 다른 날짜)
- [x] API 키 미설정 케이스 직접 재현
- [x] OpenAI/Kakao 인증 실패(401) 케이스 직접 재현
- [x] 맛집 검색 0건(EMPTY_RESULT) 케이스 직접 재현
- [x] CLI 옵션 누락/날짜 형식 오류 케이스 직접 재현

### 🧹 제출 전 정리
- [x] 연습용 임시 파일(`test.py`, `test_empty.py` 등) 삭제 또는 이동
- [x] `results/` 폴더에서 테스트로 쌓인 불필요한 결과 파일 정리
- [x] `__pycache__/` 폴더는 `.gitignore`에 등록되어 있어 제출물에서 무시되어도 무방

---

## 11. 보안 주의사항 (공용PC 필독)

- API 키를 코드나 README, 결과 파일에 **절대 직접 작성하지 마세요.** 이 프로그램은 `os.getenv()`로만 키를 읽으므로 코드 안에는 키가 전혀 존재하지 않습니다.
- 공용PC에서는 `.env` 파일 대신 **세션 환경변수(`$env:`) 방식을 권장**합니다. PowerShell 창을 닫으면 키가 자동으로 사라집니다.
- `.env` 파일을 사용했다면 작업 종료 후 반드시 파일을 삭제하세요.
- 키 값을 확인할 때는 `$env:OPENAI_API_KEY` 전체를 출력하지 말고, `.Substring(0,3)`이나 `.Length`처럼 **일부/길이만** 확인하는 습관을 들이세요.
- 작업 종료 후 프로젝트 폴더 삭제, 휴지통 비우기, 클립보드 비우기, 브라우저 캐시 삭제를 진행하세요.
- 이 저장소를 Git/GitHub에 올릴 경우 `.env`가 실제로 제외되었는지 `git status`로 반드시 확인하세요.

---

## 12. 자주 발생하는 문제 (트러블슈팅)

**Q. `$env:OPENAI_API_KEY`를 확인했는데 아무 값도 안 나와요.**
→ 키가 세션에 설정되지 않은 것입니다. `$env:OPENAI_API_KEY="본인 키"`를 다시 실행하세요. PowerShell 창을 새로 열었다면 이전 설정은 사라진 상태입니다.

**Q. `[AUTH_ERROR] OpenAI 인증에 실패했습니다`가 계속 떠요. 결제 잔액도 있는데요.**
→ 키 형식부터 확인하세요. `$env:OPENAI_API_KEY.Substring(0,3)`을 실행했을 때 `sk-`가 아닌 다른 문자열이 나온다면, 키가 잘못 복사되었거나 다른 값이 들어간 것입니다. platform.openai.com에서 키를 다시 확인하거나 새로 발급받으세요.

**Q. VSCode에 `가져오기 "dotenv"을(를) 확인할 수 없습니다` 경고가 떠요.**
→ 이건 VSCode의 코드 분석 도구(Pylance)가 뜨는 편집기 경고일 뿐, 실행 오류가 아닙니다. 코드에 `try/except ImportError`로 처리되어 있어 `python-dotenv` 없이도 정상 동작합니다.

**Q. 리포트 파일을 열었는데 이전 내용 그대로예요.**
→ `results/{date}_travel_plan.md`는 프로그램을 **다시 실행할 때마다 덮어쓰기**됩니다. 코드를 수정했다면 반드시 다시 `python travel_planner.py --date "..."`를 실행해야 새 내용이 반영됩니다. VSCode에서 파일을 열어둔 상태였다면 탭을 닫았다 다시 열어 확인하세요.

---

## 13. 전체 소스 코드 (`travel_planner.py`)

```python
"""
Python 응용: API 활용 국내 여행지 추천 프로그램
- LLM(OpenAI)으로 날짜 기반 1차 여행지 추천(JSON)
- Kakao Local API로 추천 도시의 맛집 검색
- LLM(OpenAI)으로 최종 여행 리포트(Markdown) 생성
- 결과를 results/ 폴더에 JSON + Markdown으로 저장

실행 예시:
    python travel_planner.py --date "2025-03-15"
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


# =========================================================
# 유틸: LLM 응답에서 코드펜스(```markdown ... ``` 등) 제거
# =========================================================
def strip_code_fence(text: str) -> str:
    """LLM 응답이 코드블록(```json ... ``` 또는 ```markdown ... ```)으로 감싸져 오는 경우 제거"""
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
# =========================================================
def parse_args():
    parser = argparse.ArgumentParser(
        description="국내 여행지 추천 프로그램",
        usage='python travel_planner.py --date "YYYY-MM-DD"'
    )
    parser.add_argument("--date", required=True, help="여행 날짜 (형식: YYYY-MM-DD)")
    args = parser.parse_args()

    try:
        datetime.strptime(args.date, "%Y-%m-%d")
    except ValueError:
        parser.print_usage()
        print('날짜 형식이 올바르지 않습니다. 예: --date "2025-03-15"')
        sys.exit(1)

    return args.date


# =========================================================
# 3. LLM 1차 추천 (JSON) — 파싱 실패 시 최대 1회 재시도
# =========================================================
def get_recommendation(client: OpenAI, date: str, errors: list):
    base_prompt = f"""
{date}에 여행하기 좋은 국내 도시를 1곳 추천해줘.
반드시 아래 JSON 형식으로만 답하고, 다른 설명은 절대 붙이지 마.

{{
  "recommended_city": "도시명",
  "weather": "해당 시기 일반적 날씨 요약",
  "events": ["행사/축제 후보1", "행사/축제 후보2"],
  "reason": "추천 근거 2~4문장"
}}
""".strip()

    prompt = base_prompt
    for attempt in range(1, LLM_JSON_RETRY_LIMIT + 2):  # 최초 1회 + 재시도 1회
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

            required_keys = ["recommended_city", "weather", "events", "reason"]
            if not all(k in data for k in required_keys):
                raise ValueError("필수 키 누락")

            return data

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
            return {
                "recommended_city": "정보없음",
                "weather": "정보없음",
                "events": [],
                "reason": "LLM 응답 파싱에 실패하여 추천 정보를 가져오지 못했습니다."
            }

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
            return {
                "recommended_city": "정보없음",
                "weather": "정보없음",
                "events": [],
                "reason": "API 오류로 추천 정보를 가져오지 못했습니다."
            }


# =========================================================
# 4. Kakao Local API 맛집 검색
#    - 인증 실패(401/403): 맛집=데이터없음 처리 후 계속 진행
#    - 결과 0건: 파라미터를 바꿔 최대 2회 재시도 후 "데이터 없음" 표기
# =========================================================
def search_restaurants(kakao_key: str, city: str, errors: list):
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {kakao_key}"}

    queries = [f"{city} 맛집", f"{city} 음식점", city]  # 재시도 시 쓸 파라미터 변형

    for attempt, query in enumerate(queries[:PLACE_EMPTY_RETRY_LIMIT + 1], start=1):
        try:
            res = requests.get(
                url, headers=headers,
                params={"query": query, "size": KAKAO_SEARCH_COUNT},
                timeout=10
            )

            if res.status_code in (401, 403):
                print(f"[AUTH_ERROR] Kakao 인증 실패({res.status_code}). 키 설정을 확인하세요.")
                print("→ 맛집 섹션은 '데이터 없음'으로 처리하고 리포트 생성은 계속 진행합니다.")
                errors.append({
                    "step": "place_search",
                    "type": "AUTH_ERROR",
                    "message": f"HTTP {res.status_code}"
                })
                return []

            res.raise_for_status()
            documents = res.json().get("documents", [])

            if documents:
                restaurants = []
                for d in documents:
                    restaurants.append({
                        "name": d.get("place_name", ""),
                        "address": d.get("address_name", ""),
                        "category": d.get("category_name", ""),
                        "url": d.get("place_url", ""),
                        "x": d.get("x", ""),
                        "y": d.get("y", ""),
                    })
                return restaurants

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

    print("[EMPTY_RESULT] 재시도 후에도 맛집 검색 결과가 없습니다. '데이터 없음'으로 표기합니다.")
    return []


# =========================================================
# 5. LLM 최종 리포트 생성 (Markdown)
# =========================================================
def generate_report(client: OpenAI, date: str, recommendation: dict, restaurants: list, errors: list) -> str:
    city = recommendation.get("recommended_city", "정보없음")
    weather = recommendation.get("weather", "정보없음")
    events = recommendation.get("events", [])
    reason = recommendation.get("reason", "")

    if restaurants:
        restaurant_text = "\n".join(
            f"- {r['name']} ({r['address']})" for r in restaurants
        )
    else:
        restaurant_text = "데이터 없음 (장소 검색 결과 0건 또는 API 오류)"

    prompt = f"""
아래 정보를 바탕으로 국내 여행 추천 리포트를 Markdown으로 작성해줘.

[출력 형식 규칙 - 반드시 지켜]
1. 코드블록(```)으로 감싸지 마. 순수 Markdown 텍스트만 출력해.
2. # 으로 시작하는 제목(H1)은 절대 넣지 마. 문서 제목은 이미 별도로 붙일 것이므로 필요 없음.
3. 출력의 맨 첫 줄은 반드시 "## 추천 지역" 이어야 해. 그 앞에 어떤 문장, 제목, 인사말도 넣지 마.

반드시 아래 섹션을 모두 포함해:
## 추천 지역
## 추천 이유
## 날씨 요약
## 행사/축제
## 맛집 추천
## 1일 일정 제안 (오전/오후/저녁)

[입력 정보]
- 날짜: {date}
- 추천 지역: {city}
- 날씨: {weather}
- 행사/축제 후보: {', '.join(events) if events else '없음'}
- 추천 이유: {reason}
- 맛집 목록:
{restaurant_text}

맛집 목록이 "데이터 없음"이면 리포트의 맛집 추천 섹션에도 "데이터 없음"이라고 그대로 표기해.
""".strip()

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
        )
        report_body = strip_code_fence(response.choices[0].message.content)

        # LLM이 지시를 무시하고 최상단에 # 제목(H1)을 넣은 경우, 중복 방지를 위해 제거
        # (빈 줄이 앞에 껴 있어도 실제 첫 텍스트 줄을 찾아서 확인)
        body_lines = report_body.split("\n")
        first_idx = 0
        while first_idx < len(body_lines) and body_lines[first_idx].strip() == "":
            first_idx += 1
        if first_idx < len(body_lines) and body_lines[first_idx].strip().startswith("# ") \
                and not body_lines[first_idx].strip().startswith("## "):
            body_lines = body_lines[first_idx + 1:]
        report_body = "\n".join(body_lines).strip()

    except (AuthenticationError, APIError) as e:
        print(f"[REPORT_ERROR] 리포트 생성 중 오류: {e}. 기본 템플릿으로 대체합니다.")
        errors.append({"step": "report_generation", "type": "API_ERROR", "message": str(e)})
        report_body = f"""## 추천 지역
{city}

## 추천 이유
{reason}

## 날씨 요약
{weather}

## 행사/축제
{', '.join(events) if events else '데이터 없음'}

## 맛집 추천
{restaurant_text}

## 1일 일정 제안
리포트 자동 생성에 실패하여 기본 템플릿으로 표시되었습니다."""

    if errors:
        errors_text = "\n".join(
            f"- [{e['step']}] {e['type']}: {e['message']}" for e in errors
        )
    else:
        errors_text = "없음"

    header = f"# {date} 국내 여행 추천 리포트\n\n"
    footer = f"\n\n## 오류 요약(errors)\n{errors_text}\n"

    return header + report_body + footer


# =========================================================
# 6. 결과 저장
# =========================================================
def save_results(date: str, recommendation: dict, restaurants: list, report: str, errors: list):
    results_dir = os.path.join(os.getcwd(), "results")
    os.makedirs(results_dir, exist_ok=True)

    raw_data = {
        "date": date,
        "recommendation": recommendation,
        "restaurants": restaurants,
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
# 7. 메인 실행 흐름
# =========================================================
def main():
    date = parse_args()
    openai_key, kakao_key = load_api_keys()
    client = OpenAI(api_key=openai_key)

    errors = []

    print(f'[1/3] 1차 추천 생성 중(LLM)... (날짜: {date})')
    recommendation = get_recommendation(client, date, errors)
    city = recommendation.get("recommended_city", "정보없음")
    print(f'  - recommended_city: "{city}"')

    print("[2/3] 맛집 검색 중(Kakao Local API)...")
    restaurants = search_restaurants(kakao_key, city, errors)
    print(f"  - 맛집 {len(restaurants)}곳 검색 완료" if restaurants else "  - 맛집 검색 결과 없음 (데이터 없음으로 진행)")

    print("[3/3] 최종 리포트 생성 중(LLM)...")
    report = generate_report(client, date, recommendation, restaurants, errors)
    print("  - 리포트 생성 완료")

    json_path, md_path = save_results(date, recommendation, restaurants, report, errors)

    print(f"\n완료! 아래 결과 파일을 확인하세요.")
    print(f"  - 원본 데이터: {json_path}")
    print(f"  - 여행 리포트: {md_path}")
    if errors:
        print(f"  - 처리 중 {len(errors)}건의 오류/경고가 기록되었습니다 (JSON의 errors 항목 참고).")


if __name__ == "__main__":
    main()
```
