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

## 13. 요구사항 자체 점검표

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

## 14. 보너스 과제 제안 — 결과 캐싱 (미구현)

기본 요구사항(단일 지역 추천 + 실제 오류 재현 검증)을 우선 완료하는 것을 목표로 했기 때문에, 아래 보너스 기능은 이번 제출 범위에서 실제로 구현하지는 않았습니다. 다만 설계 방향은 정리해 둡니다.

### 14-1. 결과 캐싱 (간단한 파일 기반 캐시)

- **목적**: 동일한 날짜로 반복 실행할 때 불필요한 API 재호출을 막아 응답 속도를 높이고 쿼터·비용을 절약
- **설계 방향**
  - `main()` 시작 시 `results/{date}_data.json` 파일이 이미 존재하는지 확인
  - 존재하면 해당 파일을 읽어 `recommendation`/`restaurants`를 그대로 재사용
  - `--refresh` 같은 옵션을 추가해, 사용자가 원할 때는 캐시를 무시하고 강제로 새로 조회할 수 있도록 예외 처리
  - 코드 스케치:

```python
def load_cache_if_exists(date):
    path = os.path.join("results", f"{date}_data.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

# main() 안에서
cached = load_cache_if_exists(date)
if cached and not args.refresh:
    print(f"[CACHE] 기존 결과를 재사용합니다 → {date}_data.json")
    recommendation = cached["recommendation"]
    restaurants = cached["restaurants"]
else:
    recommendation = get_recommendation(client, date, errors)
    restaurants = search_restaurants(kakao_key, recommendation["recommended_city"], errors)
```

- **기대 효과**: 같은 날짜로 여러 번 테스트하거나 리포트만 다시 만들고 싶을 때 API 호출 없이 즉시 결과를 확인할 수 있습니다.
- **8장(캐시 파일 관리)과의 차이**: 8장에서 다룬 `__pycache__`/`.pyc`는 파이썬 인터프리터가 코드를 다시 컴파일하지 않도록 돕는 **실행 최적화 캐시**이고, 이번 14-1의 결과 캐싱은 **API 호출 결과(데이터)를 재사용하는 애플리케이션 레벨 캐시**입니다. 성격은 다르지만 "한 번 계산·조회한 값을 저장해 두었다가 재사용한다"는 개념은 동일합니다.

### 14-2. 구현 여부

설계 방향과 예시 코드만 정리했으며, 실제 코드에는 반영하지 않았습니다. 이후 확장한다면 위 스케치를 기반으로 `get_recommendation()`·`search_restaurants()`·`main()`을 수정하는 것으로 시작할 수 있습니다.

---

*본 README는 실제 개발·검증 과정을 거쳐 작성되었습니다. 개발 과정의 시행착오와 상세 검증 기록은 별도 작업과정보고서를 참고하세요.*
