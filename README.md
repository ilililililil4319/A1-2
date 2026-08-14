# 국내 여행지 추천 프로그램

날짜를 입력하면 AI(OpenAI)가 국내 여행지를 1차 추천하고, Kakao Local API로 해당 지역의 맛집을 검색한 뒤, 두 정보를 종합해 최종 여행 리포트(Markdown)를 생성하는 CLI 프로그램입니다.

모든 기능과 에러 처리 로직은 실제 성공/실패 케이스를 직접 발생시켜 검증을 완료했습니다. (검증 내역은 "9. 테스트 검증 내역" 참고)

---

## 0. 미션 개요

**과제명**: Python 응용 — API 활용 국내 여행지 추천 프로그램 개발

단일 API 호출이 아니라, 서로 다른 API들을 엮어 하나의 인사이트를 만드는 흐름을 구현하는 것이 이 과제의 핵심입니다. 사용자가 여행 날짜를 입력하면:

1. **LLM API**(OpenAI)가 해당 시기에 여행하기 좋은 지역을 추천하고
2. **지도/장소 API**(Kakao Local)가 그 지역의 맛집을 검색하고
3. 다시 **LLM API**가 위 두 결과를 종합해 사람이 읽을 수 있는 최종 여행 리포트를 작성합니다

### 과제 목표 (학습자가 스스로 설명할 수 있어야 하는 것)

- REST API의 요청/응답 구조와 HTTP 메서드(GET/POST)의 차이 → 이 프로그램은 OpenAI(POST, JSON body)와 Kakao Local(GET, query parameter) 두 가지 호출 방식을 모두 사용합니다.
- LLM 출력 결과를 구조화(JSON)하여 다음 단계(지도/장소 검색)의 입력으로 활용하는 흐름 → `get_recommendation()`의 반환값 `recommended_city`가 그대로 `search_restaurants()`의 입력 파라미터로 전달됩니다.
- 외부 API 호출에서 발생하는 대표 오류(인증/쿼터/네트워크/파싱)와 대응 원칙 → 아래 "7. 에러 처리 정책" 표에 정리했고, 실제 상황을 재현해 검증했습니다.
- API 키를 코드에 직접 작성하지 않고 `.env`/환경변수로 관리하는 이유 → 협업/공유 시 실수로 키가 공개되는 것을 방지, 키 교체 시 코드 수정 불필요, 과금/쿼터 사고 예방.

---

## 1. 기능 목록

| 구분 | 내용 |
|---|---|
| CLI 인터페이스 | `argparse` 기반, `--date "YYYY-MM-DD"` 필수 옵션, 날짜 형식 검증 |
| 1차 LLM 추천 | OpenAI가 날짜 기반으로 도시 1곳을 JSON(`recommended_city`, `weather`, `events`, `reason`)으로 추천 |
| 장소 검색 | Kakao Local API로 추천 도시의 맛집 최대 5곳 검색(`name`, `address`, `category`, `url`, `x`, `y`) |
| 2차 LLM 리포트 생성 | 1차 추천 + 맛집 목록을 종합해 Markdown 리포트 작성(추천지역/이유, 날씨, 행사, 맛집, 1일 일정) |
| 에러 처리 | 키 미설정 즉시 종료, LLM JSON 파싱 실패 1회 재시도, 장소 검색 0건 최대 2회 재시도, 지도 API 인증 실패 시 "데이터 없음" 처리 후 계속 진행 |
| 결과 저장 | `results/` 폴더에 원본 데이터 JSON과 최종 리포트 Markdown을 날짜별로 저장 |

---

## 2. 프로그램 흐름도

```
사용자 입력(--date)
      │
      ▼
[1/3] LLM 1차 추천 (get_recommendation)
      │  recommended_city, weather, events, reason
      ▼
[2/3] Kakao 맛집 검색 (search_restaurants)
      │  맛집 최대 5곳 (0건이어도 계속 진행)
      ▼
[3/3] LLM 최종 리포트 생성 (generate_report)
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
python travel_planner.py --date "2025-03-15"
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

---

## 6. 결과물 형식

### `results/{date}_data.json`

```json
{
  "date": "2025-03-15",
  "recommendation": {
    "recommended_city": "제주도",
    "weather": "...",
    "events": ["...", "..."],
    "reason": "..."
  },
  "restaurants": [
    {"name": "...", "address": "...", "category": "...", "url": "...", "x": "...", "y": "..."}
  ],
  "errors": []
}
```

### `results/{date}_travel_plan.md`

`## 추천 지역`으로 시작하는 Markdown 문서로, 추천 지역/이유·날씨 요약·행사/축제·맛집 추천·1일 일정 제안·오류 요약(errors) 섹션을 포함합니다.

---

## 7. 에러 처리 정책

| 상황 | 담당 함수 | 동작 |
|---|---|---|
| API 키 미설정 | `load_api_keys()` | 즉시 종료 + 어떤 키가 없는지와 설정 방법 안내 |
| OpenAI 인증 실패(401/403) | `get_recommendation()` | 핵심 기능이므로 즉시 종료 |
| OpenAI JSON 파싱 실패 | `get_recommendation()` | 프롬프트를 보강해 최대 1회 재시도, 이후 "정보없음" 기본값으로 계속 진행 |
| Kakao 인증 실패(401/403) | `search_restaurants()` | 맛집을 "데이터 없음"으로 처리, 리포트 생성은 중단 없이 계속 |
| Kakao 검색 결과 0건 | `search_restaurants()` | 검색어를 "맛집→음식점→도시명" 순으로 바꿔 최대 2회 재시도 |
| 네트워크 오류 | `search_restaurants()` | 맛집을 "데이터 없음"으로 처리하고 계속 진행 |
| 리포트 생성 중 오류 | `generate_report()` | Python으로 조립한 기본 템플릿으로 대체 |

추가로, LLM이 최종 리포트를 코드블록(` ``` `)으로 감싸거나 제목(H1)을 중복으로 넣는 경우가 실제로 발생해, `strip_code_fence()` 함수와 중복 제목 제거 로직으로 후처리하도록 보강했습니다.

---

## 8. 캐시 파일(`__pycache__`, `*.pyc`) 관리

Python은 `.py` 파일을 실행할 때 `__pycache__/` 폴더 안에 컴파일된 `.pyc` 캐시 파일을 자동으로 생성합니다(예: `travel_planner.cpython-314.pyc`). 이 파일은 프로그램 동작에 필요한 원본이 아니라 **재실행 속도를 높이기 위한 부산물**이므로, 아래와 같이 관리합니다.

- `.gitignore`에 `__pycache__/`와 `*.pyc`를 등록해 Git 추적 대상에서 제외했습니다.
- 로컬 정리 시에도 제출 전 `__pycache__/` 폴더를 함께 삭제했습니다. 이 폴더는 프로그램을 다시 실행하면 자동으로 재생성되므로 삭제해도 문제가 없습니다.

> ⚠️ **주의 — `.gitignore`는 이미 커밋된 파일에는 소급 적용되지 않습니다.**
> 실제로 `.gitignore`에 `*.pyc`를 등록해 두었음에도, 정리 과정 중 `__pycache__/` 폴더 *밖에* 남아 있던 `travel_planner.cpython-314.pyc` 파일 하나가 실수로 GitHub 저장소 루트에 그대로 업로드된 사례가 있었습니다. `.gitignore`는 "앞으로 새로 생성/추적될 파일"만 걸러주기 때문에, 이미 `git add`로 추가되었거나 추적 이력이 있는 파일은 규칙을 등록해도 저장소에서 자동으로 빠지지 않습니다. 캐시 파일을 저장소에서 완전히 제외하려면 `.gitignore` 등록과 별개로 `git rm --cached <파일명>`으로 추적을 직접 해제해야 합니다.

이 프로젝트를 그대로 내려받아 실행하는 경우, 처음 실행 시 `__pycache__/` 폴더가 새로 생기는 것은 정상 동작입니다.

---

## 9. 테스트 검증 내역

아래 상황을 실제로 발생시켜 정상 동작을 검증했습니다.

| 테스트 항목 | 재현 방법 | 결과 |
|---|---|---|
| CLI 옵션 누락 / 날짜 형식 오류 | `--date` 없이 실행, `--date "2026-13-99"` | 사용법 안내 후 종료 |
| API 키 미설정 | `$env:OPENAI_API_KEY=""` 후 실행 | `[AUTH_ERROR]` 즉시 종료 + 설정 안내 |
| OpenAI 인증 실패 | 잘못된 형식의 키로 실행 | `[AUTH_ERROR]` 즉시 종료 |
| Kakao 인증 실패(401) | `$env:KAKAO_API_KEY="invalid_test_key_1234"` | 맛집 "데이터 없음" 처리 후 `[3/3]`까지 정상 완주 |
| 맛집 검색 0건 | 존재하지 않는 지명으로 `search_restaurants()` 직접 호출 | 검색어 3종 순차 재시도 후 "데이터 없음" 표기 |
| 정상 실행(2회 이상) | 서로 다른 날짜(2025-03-15, 2025-09-15)로 반복 실행 | 매번 다른 지역·맛집·리포트가 정상 생성 |

---

## 10. 공용PC 보안 주의사항

- 실제 작업은 개인 소유가 아닌 공용PC에서 진행했으므로, API 키는 `.env` 파일이 아닌 **PowerShell 세션 임시 환경변수**로 관리했습니다. 터미널 창을 닫으면 자동 소멸되어 파일로 남지 않습니다.
- 작업 종료 후에는 프로젝트 폴더 삭제 → 클립보드 비우기 → 휴지통 비우기 → 브라우저 캐시/기록 삭제 → 재부팅 순으로 정리했습니다.
- 화면 캡처를 공유할 때는 키 값을 `.Substring()`이나 `.Length`로만 확인해 전체 키가 노출되지 않도록 했습니다.
- 제출용으로는 `.env.example`(실제 키 없이 형식만) 파일을 별도로 남겼습니다.

---

## 11. 트러블슈팅 Q&A

**Q. `can't open file 'C:\...\파일명.py'` 오류가 뜹니다.**
A. 터미널의 현재 작업 폴더와 파일이 저장된 위치가 다르거나, 명령어의 "파일명" 자리에 실제 파일명을 입력하지 않고 그대로 입력한 경우입니다. `cd`로 파일이 있는 폴더로 이동한 뒤 정확한 파일명으로 실행하세요.

**Q. 한글이 깨져서 나옵니다.**
A. 파일 저장 인코딩이 UTF-8이 아닌 경우 발생합니다. 편집기의 인코딩을 UTF-8로 지정해 저장하고, 코드 내 모든 파일 입출력에 `encoding="utf-8"`을 명시하세요.

**Q. `usage: ... error: the following arguments are required: --date` 가 뜹니다.**
A. `--date "YYYY-MM-DD"` 옵션 없이 실행한 경우입니다. 정상 동작이며, 안내된 형식대로 옵션을 추가해 다시 실행하세요.

**Q. `__pycache__` 폴더는 지워도 되나요?**
A. 네. 실행 시 자동으로 재생성되는 컴파일 캐시이므로 삭제해도 프로그램 동작에는 영향이 없습니다. 자세한 내용은 "8. 캐시 파일 관리" 항목을 참고하세요.

**Q. 맛집 검색 결과가 "데이터 없음"으로 나옵니다.**
A. Kakao API 인증 실패이거나, 검색어 3종(맛집/음식점/도시명)으로 재시도해도 결과가 0건인 경우입니다. 프로그램은 중단되지 않고 리포트 생성까지 계속 진행합니다.

---

## 12. 프로젝트 구조

```
travel_project/
├── travel_planner.py      ← 메인 프로그램
├── requirements.txt       ← 필요 패키지 목록 (openai, requests, python-dotenv)
├── README.md               ← 이 문서
├── .gitignore               ← .env, __pycache__/, *.pyc 등 Git 제외 목록
├── .env.example              ← API 키 입력 템플릿 (실제 키 없음)
└── results/                  ← 실행 결과 저장 폴더 (자동 생성)
    ├── 2025-03-15_data.json / 2025-03-15_travel_plan.md
    └── 2025-09-15_data.json / 2025-09-15_travel_plan.md
```

---

## 13. 전체 소스 코드 (travel_planner.py)

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
    """LLM 응답이 ```json ... ``` 또는 ```markdown ... ``` 로 감싸져 오는 경우 제거"""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # 첫 줄이 ``` 또는 ```json, ```markdown 등이면 제거
        if lines[0].startswith("```"):
            lines = lines[1:]
        # 마지막 줄이 ``` 이면 제거
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

            # 최소 스키마 확인
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
                # 재시도 시 프롬프트를 더 엄격하게 보강
                prompt = base_prompt + "\n\n반드시 JSON 객체만 출력해. 앞뒤에 어떤 텍스트도 붙이지 마."
                time.sleep(1)
                continue
            # 재시도 소진 → 기본값으로 진행 (프로그램은 계속)
            return {
                "recommended_city": "정보없음",
                "weather": "정보없음",
                "events": [],
                "reason": "LLM 응답 파싱에 실패하여 추천 정보를 가져오지 못했습니다."
            }

        except AuthenticationError:
            print("[AUTH_ERROR] OpenAI 인증에 실패했습니다 (401/403). API 키를 다시 확인하세요.")
            errors.append({"step": "recommendation", "type": "AUTH_ERROR", "message": "OpenAI 401/403"})
            sys.exit(1)  # LLM 인증 실패는 프로그램의 핵심 기능이 불가하므로 즉시 종료

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
                return []  # 즉시 빈 리스트 반환, 재시도하지 않음 (인증 문제는 파라미터로 해결 안 됨)

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

            # 결과 0건 → EMPTY_RESULT, 다음 파라미터로 재시도
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
            return []  # 네트워크 오류도 맛집=데이터없음으로 계속 진행

    # 모든 재시도 후에도 0건
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

    # 오류 요약 섹션은 항상 Python에서 직접 붙여서, LLM이 누락해도 보장되게 함
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
| 캐시 파일(`__pycache__`, `*.pyc`) 관리 및 유의사항 문서화 | ✅ |
| 실제 오류 상황(키 미설정/인증 실패/검색 0건/옵션 오류) 재현 검증 | ✅ |

---

*본 README는 실제 개발·검증 과정을 거쳐 작성되었습니다. 개발 과정의 시행착오와 상세 검증 기록은 별도 작업과정보고서를 참고하세요.*
