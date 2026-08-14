# 작 업 과 정 보 고 서

### Python 응용 — API 활용 국내 여행지 추천 프로그램 개발

LLM API와 지도 API를 연동한 여행지 추천 CLI 프로그램 제작 기록  
작성일: 2026년 8월 13일  
미션: AI 활용 학습 · Python 응용 5  
학습 진행 방식: Claude와의 대화를 통한 단계별 실습

| 구분 | 내용 |
|---|---|
| LLM API | OpenAI 계열 (gpt-4o-mini) |
| 지도/장소 API | Kakao Local API (키워드 기반 국내 장소 검색) |
| 개발·실행 환경 | Windows 공용PC · PowerShell / VS Code · Python 3.10 이상 |
| 핵심 보안 원칙 | API 키는 코드에 직접 작성하지 않고 세션 환경변수 또는 .env로만 관리 |
| 결과물 | travel_planner.py, README.md, results/*.json·*.md, GitHub 저장소(A1-2) |

> 본 보고서는 실제 개발 화면(터미널·PowerShell·VS Code·GitHub 캡처) 약 50장을 근거로, 개발 순서(개발 환경 → API 키 발급 → 개별 테스트 → 기능 연결 → 에러 처리 → 결과 확인 → GitHub 업로드) 그대로 정리했다.

---

# 보고서 개요

본 보고서는 사용자가 입력한 날짜를 바탕으로 LLM API(OpenAI)가 국내 여행지를 1차 추천하고, 지도/장소 검색 API(Kakao Local)가 해당 지역의 맛집을 검색한 뒤, LLM API가 두 결과를 종합해 최종 여행 리포트(Markdown)를 생성하는 CLI 프로그램을 개발한 과정을 담고 있다.

개발 환경 준비, API 키 발급과 공용PC 보안 정책 수립, 개별 API 테스트, 인코딩 오류 등 실제 발생한 시행착오와 해결 과정, 에러 처리 정책 수립과 실제 검증(터미널·PowerShell REPL을 이용한 직접 재현 포함), 최종 결과물과 GitHub 업로드 내역, 전체 소스 코드, 요구사항 자체 점검표까지 실제 작업 화면 캡처를 근거로 순서대로 정리했다. 사용한 LLM API·지도 API·개발 환경·보안 원칙·결과물 구성은 표지의 표를 참고한다.

### 목차

| 1. 미션 개요 | 3 |
|---|---|
| 2. 학습 진행 방식 | 3 |
| 3. 초보자를 위한 용어 살짝 알아보기 | 4 |
| 4. 개발 환경 구축 및 폴더 준비 | 5 |
| 5. API 키 발급 및 보안 정책 수립 | 6 |
| 6. 작은 조각부터 — API 개별 테스트 | 7 |
| 7. 시행착오 — 인코딩 오류와 그 해결 | 9 |
| 8. 조각 연결 — 전체 프로그램 완성 | 9 |
| 9. 에러 처리 정책 수립 및 실제 검증 | 11 |
| 10. 최종 결과물 확인 | 15 |
| 11. 결과 리포트 예시 | 18 |
| 12. 프로젝트 구조 및 README 구성 | 19 |
| 13. 전체 소스 코드 (travel_planner.py) | 20 |
| 14. GitHub 최종 업로드 결과물 | 23 |
| 15. 요구사항 자체 점검표 | 27 |
| 16. 작업 과정에서 배운 점 | 28 |
| 17. 제출 자료 최종 확인 | 29 |

> 일러두기 — 본 보고서는 Claude와의 대화 기록과 실제 실행 화면(터미널·PowerShell·VS Code·GitHub 캡처)을 근거로 작성되었으며, 개발 순서(개발 환경 → API 키 발급 → 개별 테스트 → 기능 연결 → 에러 처리 → 결과 확인 → GitHub 업로드)를 그대로 따라 구성했다. 각 소제목 아래에는 관련 설명·코드·표·캡처 화면을 함께 배치해, 해당 절만 읽어도 그 단계의 작업 내용과 근거를 바로 확인할 수 있도록 했다.

## 1. 미션 개요

이번 미션은 Python 응용 — API 활용 국내 여행지 추천 프로그램 개발이다. 지금까지 단일 API 하나를 호출하는 연습을 해왔다면, 이번에는 서로 다른 두 종류의 API(LLM API, 지도/장소 검색 API)를 엮어서 하나의 인사이트를 만드는 흐름을 직접 구현하는 것이 핵심 과제였다. 사용자가 터미널에서 여행 날짜를 입력하면, ① LLM API가 그 시기에 여행하기 좋은 국내 도시를 JSON 형태로 1차 추천하고, ② 지도/장소 검색 API가 추천된 도시의 맛집을 검색하며, ③ LLM API가 두 결과를 다시 종합해 사람이 읽을 수 있는 최종 여행 리포트를 Markdown으로 작성하는 3단계 파이프라인을 완성해야 했다.

최종 결과물은 ① argparse 기반 CLI 프로그램 1개, ② results/ 폴더에 저장되는 원본 데이터 JSON과 최종 리포트 Markdown, ③ 프로그램 개요·실행법·API 키 설정법·유의사항을 담은 README.md, 이렇게 세 가지로 구성하도록 요구되었다. 또한 REST API의 요청/응답 구조와 GET/POST의 차이, LLM 출력을 다음 단계 입력으로 넘기는 구조화(JSON) 설계, 인증·쿼터·네트워크·파싱 오류에 대한 대응 원칙, API 키를 코드에 직접 쓰지 않고 .env/환경변수로 관리하는 이유까지 스스로 설명할 수 있어야 한다는 학습 목표가 함께 제시되었다.

| 항목 | 선택/결정 내용 |
|---|---|
| LLM API | OpenAI 계열 API (gpt-4o-mini) 사용 |
| 지도/장소 API | Kakao Local API (키워드 기반 장소 검색) 사용 |
| 개발 환경 | Windows 공용PC, PowerShell·VS Code, Python 3.10 이상 |
| 보안 원칙 | 공용PC이므로 API 키를 파일에 영구 저장하지 않고, PowerShell 세션 임시 환경변수($env:)를 기본으로 사용 |

## 2. 학습 진행 방식

본 미션은 Claude와의 대화를 통해 진행했다. 처음 API를 다뤄보는 상태였기 때문에, 먼저 전체 로드맵을 요청해 개념 학습 → 개발 환경 세팅 → API 키 발급 → 개별 API 테스트 → 조각 연결 → CLI 완성 → 에러 처리 → 결과 저장까지의 순서를 먼저 안내받은 뒤 단계별로 진행했다. 전체 프로그램을 한 번에 작성하지 않고, 작은 조각(맛집 검색 → LLM 질의 → JSON 파싱)부터 따로 테스트한 뒤 연결하는 방식을 취한 것이 이번 작업의 핵심 전략이었다.

작업 도중에는 파일 경로를 착각해 프로그램을 찾지 못하는 오류, 한글 인코딩이 깨져 API 요청 자체가 실패하는 오류, 응답 필드가 비어 있는 경우의 예외 처리 누락, IDE(VS Code)의 JSON·패키지 경고, PowerShell 프롬프트에 Python 코드를 잘못 입력해 발생한 파서 오류 등 실제 초보자가 흔히 겪는 문제들을 그대로 마주쳤고, 그때마다 오류 메시지를 그대로 Claude에게 전달해 원인을 진단받고 수정하는 방식으로 학습을 이어갔다. 이 보고서는 그 과정을 순서대로, 실제 캡처 화면과 함께 정리한 기록이다.

## 3. 초보자를 위한 용어 살짝 알아보기

본 보고서에는 API·터미널 관련 용어가 자주 등장한다. 처음 접하면 낯설 수 있는 용어들을 발음과 쉬운 뜻으로 미리 정리했다. 뒤에서 실제 사용 장면이 나올 때 참고하면 이해가 쉽다.

| 용어 | 읽는 법 | 쉬운 설명 |
|---|---|---|
| API | 에이피아이 | 서로 다른 프로그램끼리 데이터를 주고받기 위해 정해 놓은 "대화 규칙". 이 프로그램에서는 AI(LLM)와 지도 서비스 두 곳에 각각 요청을 보내고 답을 받는다. |
| LLM | 엘엘엠 | Large Language Model(대규모 언어 모델)의 줄임말. 질문을 하면 사람처럼 문장으로 답해주는 AI를 가리키며, 이 프로그램에서는 OpenAI가 이 역할을 한다. |
| JSON | 제이슨 | {"키": "값"} 형태로 데이터를 정리해서 주고받는 표준 형식. AI의 답변을 다음 단계 프로그램이 읽기 쉬운 구조로 받기 위해 사용한다. |
| GET / POST | 겟 / 포스트 | API에 요청을 보내는 두 가지 방식. GET은 "정보를 조회"할 때(예: 맛집 검색), POST는 "데이터를 함께 보내며 요청"할 때(예: AI에게 질문 전달) 사용한다. |
| CLI | 씨엘아이 | Command Line Interface(명령줄 인터페이스)의 줄임말. 마우스 클릭 없이 터미널에 글자로 명령을 입력해 프로그램을 실행하는 방식을 뜻한다. |
| .env | 닷 엔브이 | "environment(환경)"의 줄임말인 env 앞에 점(.)이 붙은 파일명. API 키처럼 외부에 노출되면 안 되는 값을 코드와 분리해서 저장해두는 파일이다. |
| 환경변수 | 환경변수 | 프로그램 코드 밖에서 값을 저장해두고, 코드가 실행될 때 불러와 쓰는 값. API 키를 코드에 직접 적지 않고 이 방식으로 관리한다. |
| .gitignore | 닷 깃이그노어 | Git이 기록·추적하지 않도록 제외할 파일·폴더 목록을 적어두는 설정 파일이다. |
| argparse | 아그파스 | 터미널에서 입력한 --date "2025-03-15" 같은 옵션 값을 프로그램이 읽어 쓸 수 있게 해주는 파이썬 표준 도구다. |
| pip | 핍 | 파이썬 라이브러리(남이 만들어 둔 코드 묶음)를 설치할 때 쓰는 명령어. pip install requests처럼 사용한다. |
| 인코딩 | 인코딩 | 컴퓨터가 문자를 저장하는 방식. 한글처럼 특수한 문자는 UTF-8이라는 방식으로 저장해야 글자가 깨지지 않는다. |
| try-except | 트라이-익셉트 | "시도해보고, 예외(오류)가 나면 이렇게 처리해라"를 뜻하는 파이썬 오류 처리 문법. |
| 파싱(Parsing) | 파싱 | 글자로 된 텍스트를 프로그램이 다룰 수 있는 데이터 구조로 "분석해서 변환"하는 것. AI가 준 JSON 텍스트를 파이썬 딕셔너리로 바꾸는 과정이다. |
| REPL | 레플 | Read-Eval-Print Loop의 줄임말. 터미널에 python만 입력해 한 줄씩 코드를 바로 실행하고 결과를 확인하는 대화형 모드. |

## 4. 개발 환경 구축 및 폴더 준비

맨 처음 작성한 테스트 코드(test.py)를 실행하자 can't open file 'C:\Windows\System32\test.py' 오류가 발생했다. PowerShell을 열었을 때 기본 위치가 시스템 폴더(System32)로 되어 있었는데, 파일은 다른 곳에 저장해두고 그 사실을 인지하지 못한 채 실행한 것이 원인이었다. 이후 명령어를 python 파일명.py 형태로 그대로(치환하지 않고) 입력해 또 한 번 파일을 찾지 못하는 오류를 만나기도 했다.

![](images/img43.png)

*그림 1. "python 파일명.py"를 실제 파일명으로 바꾸지 않고 그대로 입력해 발생한 FileNotFoundError*

이 오류를 계기로 작업 전용 폴더를 먼저 만들고 그 안에서만 작업하는 습관을 들이기로 하고, 아래 순서로 프로젝트 폴더를 준비했다.

```
cd C:\Users\user\Desktop
mkdir travel_project
cd travel_project
```

이후 모든 코드 파일과 결과물은 바탕화면의 travel_project 폴더 안에서만 생성·실행하도록 통일했다. 필요한 라이브러리는 아래와 같이 설치했다.

```
pip install requests python-dotenv openai
```

> 배운 점 — 터미널에서 python 파일명.py를 실행할 때는 반드시 그 파일이 현재 터미널이 위치한 폴더 안에 있는지, 그리고 파일명 자리에 실제 파일명을 정확히 입력했는지 먼저 확인해야 한다. 파일 생성 위치와 터미널의 현재 위치(작업 디렉터리)는 서로 별개라는 점을 이 오류를 통해 체감했다.

## 5. API 키 발급 및 보안 정책 수립

LLM API는 이미 발급되어 있던 OpenAI API 키를 재사용했고(Settings → Billing에서 크레딧 잔액 확인 후 재발급 없이 사용), 지도/장소 API는 국내 장소 검색에 강점이 있는 Kakao Local API의 REST API 키를 새로 발급받았다. 이 과정에서 카카오 개발자 콘솔의 잘못된 메뉴를 보고 있어 원하는 화면을 찾지 못한 시행착오가 있었으나, 화면 캡처를 Claude에게 공유해 정확한 메뉴 위치를 안내받아 해결했다.

### 5-1. 공용PC 보안 정책 결정

이번 작업은 개인 소유가 아닌 공용PC에서 진행했기 때문에, 키 관리 방식을 신중하게 결정해야 했다. .env 파일에 키를 저장하면 로그아웃 후에도 파일이 남아 다음 사용자에게 노출될 위험이 있다는 점을 확인하고, 아래와 같이 이중 전략을 세웠다.

| 상황 | 키 관리 방식 | 이유 |
|---|---|---|
| 실제 작업(공용PC) | PowerShell 세션 임시 환경변수 $env: | 터미널 창을 닫으면 자동 소멸, 파일로 남지 않음 |
| 제출용 템플릿 | .env.example (키 값 없이 형식만) | 실제 키 없이도 설정 방법을 문서로 남기기 위함 |

![](images/img50.png)

*그림 2. .env.example — 실제 키 값 없이 형식만 담은 제출용 템플릿*

![](images/img51.png)

*그림 3. .gitignore — venv/, .env, __pycache__/, *.pyc 등 Git 제외 목록*

```
# PowerShell 세션 환경변수 설정
$env:OPENAI_API_KEY="본인 키"
$env:KAKAO_API_KEY="본인 키"

# 값 노출 없이 형식만 확인 (전체 출력 금지)
$env:OPENAI_API_KEY.Substring(0,3)   # "sk-" 가 나오면 정상
$env:KAKAO_API_KEY.Length            # 숫자가 나오면 값이 들어있는 것
```

![](images/img75.png)

*그림 4. 실제 검증 화면 — .Substring(0,7)로 키 앞부분만 확인하여 화면 캡처 시에도 전체 키가 노출되지 않도록 함*

> 공용PC 보안 체크리스트 — 작업 종료 후 프로젝트 폴더 삭제 → 클립보드 비우기 → 휴지통 비우기 → 브라우저 캐시/기록 삭제 → 재부팅. 특히 키 값을 확인할 때 $env:OPENAI_API_KEY를 통째로 출력하지 않고 .Substring()이나 .Length로만 확인해, 화면 캡처를 Claude와 공유해도 키가 노출되지 않도록 했다.

## 6. 작은 조각부터 — API 개별 테스트

전체 프로그램을 한 번에 작성하지 않고, 아래 순서로 작은 조각씩 나누어 테스트했다.

- 환경변수 로드 테스트 — os.environ.get()으로 두 키가 정상적으로 읽히는지, 앞 5글자만 출력해 확인
- LLM 단독 호출 테스트 — 간단한 질문을 보내고 응답이 오는지 확인
- LLM에 JSON 형식 응답 요청 — response_format={"type": "json_object"}로 구조화된 응답을 받고 json.loads()로 파싱
- Kakao Local API 단독 호출 테스트 — "제주 맛집" 키워드로 검색해 결과가 오는지 확인

```
openai_key = os.environ.get("OPENAI_API_KEY")
kakao_key = os.environ.get("KAKAO_API_KEY")
print("OpenAI 키:", openai_key[:5], "...")   # 앞 5글자만 출력 → 키 전체 노출 방지
print("Kakao 키:", kakao_key[:5], "...")
```

환경변수 로드 테스트는 첫 시도에 성공했다. 이후 실제로 test.py 단계에서 LLM 1차 추천 + 장소 검색 + 리포트 저장까지 이어지는 최소 기능을 먼저 시험 삼아 완성해 실행해 보았다.

![](images/img40.png)

*그림 5. 초기 test.py 실행 결과 — 해운대 해수욕장·광안리 해수욕장·용두산 공원이 추천되고, 여행리포트.md와 travel_places.json 저장 완료 메시지가 출력된 최초 성공 화면*

![](images/img41.png)

*그림 6. 탐색기 화면 — test.py 실행으로 생성된 travel_places.json, 여행리포트 파일 확인*

### 6-1. 본 프로그램(travel_planner.py) 골격 작성

초기 조각 테스트가 성공적으로 끝난 뒤, 요구사항에 맞춰 travel_planner.py 메인 파일을 새로 작성하기 시작했다. 파일 상단에는 프로그램 설명(docstring), 필요한 모듈 임포트, 그리고 설정값(OPENAI_MODEL, KAKAO_SEARCH_COUNT, 재시도 횟수 등)을 정리했다.

![](images/img42.png)

*그림 7. VS Code — travel_planner.py 최초 작성 화면. docstring, import 구문, 0. 설정값 영역*

코드를 작성하는 도중 VS Code의 문제(Problems) 패널에서 JSON 파일 문법 오류와 dotenv 모듈을 찾지 못한다는 Pylance 경고가 함께 표시된 적이 있었다. JSON 오류는 결과 파일(2026-09-15_data.json)을 아직 프로그램이 완주하지 못한 상태에서 열람해 발생한 것이었고, dotenv 경고는 가상환경이 아닌 전역 인터프리터를 바라보고 있어 발생한 것으로, 실제 실행에는 영향이 없어 무시하고 진행했다.

![](images/img67.png)

*그림 8. VS Code 문제 패널 — JSON 리터럴 오류, dotenv import 확인 불가 경고 (실행에는 영향 없음)*

## 7. 시행착오 — 인코딩 오류와 그 해결

한글로 작성한 프롬프트("3월 15일에 여행하기 좋은 국내 도시를 추천해줘…")를 메모장에 저장하고 실행했더니, type test.py로 파일 내용을 확인한 결과 한글이 완전히 깨져 있었다. 파일을 저장할 때 편집기의 기본 인코딩이 UTF-8이 아닌 다른 방식(ANSI/CP949 계열)으로 지정되어 있었던 것이 원인이었다. 텍스트가 깨지면서 프롬프트 안에 있던 "JSON"이라는 단어까지 함께 손상되어, LLM이 JSON 형식으로 응답해야 한다는 지시 자체를 인식하지 못하는 연쇄적인 오류로 이어졌다.

| 구분 | 내용 |
|---|---|
| 원인 | 편집기가 UTF-8이 아닌 인코딩으로 파일을 저장 → 한글이 깨짐 → 프롬프트 속 "JSON" 키워드까지 손상 → LLM이 지시를 이해하지 못함 |
| 해결 | 테스트 단계의 프롬프트를 영어로 작성해 인코딩 문제 자체를 우회했다. AI는 영어 질문에도 한국 지명은 한글로 정확히 답변했다. |

```
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user",
        "content": "Recommend 3 travel spots in Jeju Island. Return JSON with a 'places' array of names."}],
    response_format={"type": "json_object"}
)
data = json.loads(response.choices[0].message.content)
print(data)
# 결과: {'places': ['Seongsan Ilchulbong', 'Hallasan Mountain', 'Manjanggul Cave']}
```

> 배운 점 — 한글처럼 다국어 문자를 다루는 프로그램에서는 인코딩(UTF-8) 설정이 실행 성공 여부를 가르는 요소가 될 수 있다는 것을 체감했다. 이후 실제 제출 코드에서는 모든 파일 입출력에 encoding="utf-8"을 명시해 이 문제를 원천적으로 방지했다.

## 8. 조각 연결 — 전체 프로그램 완성

개별 테스트가 끝난 뒤, 6장에서 만든 조각들을 실제 요구사항에 맞춰 하나의 파이프라인으로 연결하는 작업을 진행했다. 핵심은 앞 단계의 결과(JSON)를 다음 단계의 입력으로 그대로 넘기는 것이었다.

```
1차_추천 = LLM에게_물어보기(날짜)                       # → {"recommended_city": "제주도", ...}
맛집목록 = 카카오에서_검색(1차_추천["recommended_city"])   # → 맛집 5곳
최종리포트 = LLM에게_리포트_요청(1차_추천, 맛집목록)         # → Markdown 문자열
```

연결 과정에서 여러 차례 실제 실행 오류를 마주쳤고, 그때마다 원인을 진단하고 코드를 보완했다.

### 8-1. 맛집 정보 필드 누락 및 예외 처리 보강

검색된 맛집 중 일부의 주소 필드가 비어 있는 경우를 발견했다. 카카오 API 응답에서 특정 장소는 address_name 대신 다른 필드에 값이 들어있을 수 있다는 점을 확인하고, or 연산자를 활용한 대체값 처리 방식을 적용했다. 또한 네트워크 자체가 끊기는 상황(requests.exceptions.RequestException)에 대비해, 맛집을 "데이터 없음"으로 처리하고 프로그램은 계속 진행하도록 search_restaurants() 함수의 예외 처리 블록을 완성했다.

![](images/img44.png)

*그림 9. search_restaurants() 함수의 네트워크 오류(NETWORK_ERROR) 처리 및 재시도 종료 후 결과 리포트 생성 로직(generate_report) 시작 부분*

### 8-2. 긴 코드를 여러 번에 나누어 전달받기

완성된 코드가 340줄에 달해 한 번에 전달되지 못하고 중간에 잘리는 상황이 발생했다. 이때는 몇 번째 줄까지 도착했는지를 확인한 뒤, 잘린 지점부터 이어서 요청하는 방식으로 전체 코드를 빠짐없이 완성했다. 또한 코드가 여러 차례 수정되며 구조가 헷갈리는 시점에는 처음부터 다시 깔끔하게 작성해 달라고 요청해, 누적된 임시 수정 대신 일관된 구조의 코드로 재정비했다.

### 8-3. CLI 인터페이스 구성

argparse를 사용해 --date "YYYY-MM-DD" 필수 옵션을 구현하고, datetime.strptime()으로 날짜 형식을 검증해 형식이 틀리면 사용법을 출력하고 종료하도록 했다. 옵션 없이 실행하면 argparse가 자동으로 필수 인자 누락 오류를 출력한다.

```
parser.add_argument("--date", required=True, help="여행 날짜 (형식: YYYY-MM-DD)")
args = parser.parse_args()
try:
    datetime.strptime(args.date, "%Y-%m-%d")
except ValueError:
    parser.print_usage()
    print('날짜 형식이 올바르지 않습니다. 예: --date "2025-03-15"')
    sys.exit(1)
```

![](images/img45.png)

*그림 10. --date 옵션 없이 실행 시 argparse가 출력하는 필수 인자 오류*

![](images/img68.png)

*그림 11. VS Code 내장 터미널에서도 동일하게 --date 필수 오류가 재현됨을 확인*

## 9. 에러 처리 정책 수립 및 실제 검증

과제 제약사항에 따라 try-except로 API 호출·파싱 오류를 처리하고, 지도 API 실패 시에도 프로그램이 중단되지 않고 "데이터 없음"으로 표기한 뒤 리포트 생성까지 계속 진행하도록 설계했다. 아래는 최종적으로 수립한 에러 처리 정책이다.

| 상황 | 담당 함수 | 동작 |
|---|---|---|
| API 키 미설정 | load_api_keys() | 즉시 종료 + 어떤 키가 없는지와 설정 방법 안내 |
| OpenAI 인증 실패(401/403) | get_recommendation() | 핵심 기능이므로 즉시 종료 |
| OpenAI JSON 파싱 실패 | get_recommendation() | 프롬프트를 보강해 최대 1회 재시도, 이후 "정보없음" 기본값으로 계속 진행 |
| Kakao 인증 실패(401/403) | search_restaurants() | 맛집을 "데이터 없음"으로 처리, 리포트 생성은 중단 없이 계속 |
| Kakao 검색 결과 0건 | search_restaurants() | 검색어를 "맛집→음식점→도시명" 순으로 바꿔 최대 2회 재시도 |
| 네트워크 오류 | search_restaurants() | 맛집을 "데이터 없음"으로 처리하고 계속 진행 |
| 리포트 생성 중 오류 | generate_report() | Python으로 조립한 기본 템플릿으로 대체 |

### 9-0. 코드펜스·중복 제목 버그의 실제 발견

개발 도중, LLM이 최종 리포트를 코드블록(```)으로 감싸서 반환하거나 지시를 무시하고 자체 제목(H1)을 리포트 제목과 중복으로 넣는 문제를 실제로 발견했다. 아래는 그 버그가 그대로 남아 있는 초기 결과 파일(2026-09-15_travel_plan.md)의 원문이다.

![](images/img53.png)

*그림 12. 원문(raw) 확인 — 첫 줄 제목 아래 ```markdown 코드펜스와 중복된 "# 국내 여행 추천 리포트: 부산" H1 제목이 그대로 포함된 모습*

코드펜스를 제거하는 1차 수정을 반영한 뒤에도, 이후 9-1의 Kakao 401 인증 실패 테스트를 진행하던 중 같은 계열의 버그(중복 H1 제목)가 한 번 더 재현되었다. 아래 화면은 그 시점에 생성된 리포트로, 코드펜스는 사라졌지만 제목이 "2025-03-15 국내 여행 추천 리포트"와 "부산 여행 추천 리포트" 두 번 겹쳐 나타나고, 하단 오류 요약에는 당시 함께 테스트 중이던 [place_search] AUTH_ERROR: HTTP 401이 그대로 기록되어 있다.

![](images/img73.png)

*그림 13. 코드펜스 제거 후에도 남아 있던 중복 제목 버그 — 제목이 두 번(2025-03-15 국내 여행 추천 리포트 / 부산 여행 추천 리포트) 겹쳐 보이고, Kakao 401 테스트의 오류 요약이 함께 기록된 실제 화면*

이를 완전히 해결하기 위해 strip_code_fence() 함수로 코드펜스를 제거하고, 응답의 첫 줄이 #으로 시작하는 중복 제목이면 잘라내는 로직을 추가했으며, 프롬프트에도 "코드블록으로 감싸지 말 것", "출력의 첫 줄은 반드시 '## 추천 지역'일 것" 등 형식 규칙을 명시해 재발을 방지했다.

![](images/img71.png)

*그림 14. VS Code — 코드펜스 제거 유틸리티 strip_code_fence()와 관련 설정값이 반영된 travel_planner.py 실제 코드*

### 9-1. 실제 오류 상황 재현 테스트

코드를 영구히 손상시키지 않는 방식으로, 아래 상황들을 실제로 발생시켜 정상 동작을 검증했다.

| 테스트 항목 | 재현 방법 | 결과 |
|---|---|---|
| 날짜 형식 오류 | --date "2026-13-99" 사용 | 사용법 안내 후 종료 |
| API 키 미설정 | $env:OPENAI_API_KEY="" 후 실행 | [AUTH_ERROR] 즉시 종료 + 설정 안내 |
| OpenAI 인증 실패 | 잘못된 형식의 키로 실행 | [AUTH_ERROR] 즉시 종료 |
| Kakao 인증 실패(401) | $env:KAKAO_API_KEY="invalid_test_key_1234" | 맛집 "데이터 없음" 처리 후 [3/3]까지 정상 완주 |
| 맛집 검색 0건 | 존재하지 않는 임의 지명으로 REPL에서 직접 호출 | 검색어 3종 순차 재시도 후 "데이터 없음" 표기 |
| 정상 실행(2회 이상) | 서로 다른 날짜(2025-03-15, 2025-09-15)로 반복 실행 | 제주도·강릉 등 매번 다른 지역 추천, 맛집 5곳, 리포트 정상 생성 |

#### ① CLI 옵션·날짜 형식 오류

![](images/img54.png)

*그림 15. --date "2026-13-99" 실행 시 argparse의 사용법 안내 후 종료되는 화면*

#### ② API 키 미설정 / OpenAI 인증 실패

![](images/img55.png)

*그림 16. OPENAI_API_KEY 환경변수가 없을 때 즉시 종료되며 PowerShell·.env 두 가지 설정 방법을 함께 안내하는 화면*

![](images/img56.png)

*그림 17. $env:OPENAI_API_KEY 값을 직접 조회해 비어 있음을 확인 — 위 오류 재현을 위한 사전 확인*

![](images/img74.png)

*그림 18. 형식이 잘못된 키로 실행했을 때 [AUTH_ERROR] OpenAI 인증 실패(401/403) 메시지와 함께 즉시 종료*

#### ③ Kakao 인증 실패(401) — 지도 API 실패해도 계속 진행

![](images/img59.png)

*그림 19. KAKAO_API_KEY를 잘못된 값으로 바꾼 뒤 실행 — [AUTH_ERROR] Kakao 인증 실패(401) 발생 후에도 맛집을 "데이터 없음"으로 처리하고 [3/3] 리포트 생성까지 정상 완주, 오류 1건이 기록됨*

#### ④ 맛집 검색 0건(EMPTY_RESULT) — REPL 직접 호출로 재현

실제 존재하지 않는 임의의 지명으로 search_restaurants()를 직접 호출해 0건 재시도 로직을 검증했다. 처음에는 PowerShell 프롬프트에 Python 문법을 그대로 입력해 "'from' 키워드는 이 언어 버전에서 지원되지 않습니다"라는 오류를 만났는데, 이는 PowerShell과 Python REPL을 착각한 실수였다.

![](images/img60.png)

*그림 20. PowerShell 프롬프트에 Python 문법(from ... import ...)을 그대로 입력해 발생한 파서 오류 — python 명령으로 REPL을 먼저 진입해야 함을 확인*

![](images/img61.png)

*그림 21. python REPL 진입 후 travel_planner에서 search_restaurants를 임포트하고, 존재하지 않는 가상의 지명으로 함수를 직접 호출*

![](images/img62.png)

*그림 22. "맛집→음식점→도시명" 3종 검색어로 순차 재시도했으나 모두 0건이 나와 최종적으로 "데이터 없음"으로 표기되는 로그*

![](images/img63.png)

*그림 23. print(errors)로 확인한 EMPTY_RESULT 오류 기록 3건 — step, type, message가 각각 정상적으로 누적됨*

#### ⑤ 정상 실행(2회 이상, 서로 다른 날짜)

![](images/img58.png)

*그림 24. --date "2025-03-15" 정상 실행 — recommended_city "제주도", 맛집 5곳 검색, 리포트 생성까지 [1/3]~[3/3] 정상 완주*

![](images/img76.png)

*그림 25. 서로 다른 두 날짜(2025-03-15 → 제주도, 2025-09-15 → 강릉)를 연속으로 실행해 매번 다른 지역이 추천됨을 확인*

## 10. 최종 결과물 확인

완성된 프로그램을 서로 다른 날짜로 실행해 results/ 폴더에 결과가 정상적으로 쌓이는지 확인했다. 실행 시 [1/3] 1차 추천 생성 중 → [2/3] 맛집 검색 중 → [3/3] 최종 리포트 생성 중 순서로 진행 로그가 출력되었고, 완료 후에는 저장된 파일의 전체 경로를 안내하도록 했다. 아래는 본 프로그램(travel_planner.py) 파일 구축이 모두 완료된 시점의 travel_project 폴더 모습이며, 실제 최종 데이터 파일 내용은 14장 GitHub 최종 업로드 결과물에서 확인할 수 있다.

![](images/img49b.png)

*그림 26. 본 프로그램 구축 완료 — travel_project 최상위 폴더에 results, .env.example, .gitignore, README, requirements, travel_planner.py 구성이 모두 갖춰진 모습*

![](images/img71.png)

*그림 27. 최종 구현 화면 — VS Code에서 확인한 travel_planner.py 완성 코드(설정값, strip_code_fence() 유틸리티 등 최종 구현 상태)*

![](images/img65.png)

*그림 28. __pycache__ 폴더 내부 — travel_planner.cpython-314 컴파일 캐시 파일. 실행 시 자동 생성되며 제출 정리 단계에서 함께 삭제 대상*

테스트 과정에서 함께 생성되었던 부가 결과물은 제출 정리 단계에서 삭제하고, 정상적으로 검증된 2025-03-15(제주도), 2025-09-15(강릉) 두 세트만 최종 결과물로 남겼다. __pycache__ 폴더는 실행 시 자동 재생성되는 캐시이므로 함께 정리했다.

![](images/img66.png)

*그림 29. 정리 이전 results 폴더 — 검증용 데이터와 부가 테스트 데이터가 함께 남아 있던 중간 상태*

![](images/img79.png)

*그림 30. 최종 정리된 travel_project 폴더 — __pycache__, results, .env.example, .gitignore, requirements, travel_planner.py, README.md(최종 26KB)만 남은 상태*

![](images/img80.png)

*그림 31. 최종 정리된 results 폴더 — 2025-03-15, 2025-09-15 두 세트(JSON+Markdown)만 남은 최종 제출 상태*

## 11. 결과 리포트 예시

--date "2025-03-15"로 실행했을 때 생성된 최종 리포트(2025-03-15_travel_plan.md)의 실제 내용은 아래와 같다. 추천 지역, 추천 이유, 날씨 요약, 행사/축제, 맛집 5곳, 1일 일정 제안, 오류 요약까지 요구된 항목이 모두 포함되어 있으며, 9장에서 발견했던 코드펜스·중복 제목 버그가 후처리 로직 적용 후 더 이상 나타나지 않는 것도 함께 확인된다.

![](images/img77.png)

*그림 32. 2025-03-15_travel_plan.md 렌더링 화면 — 제주도, 봄꽃축제, 맛집 5곳, 1일 일정, 오류 요약(없음)까지 모든 섹션 정상 포함*

```
# 2025-03-15 국내 여행 추천 리포트

## 추천 지역
제주도

## 추천 이유
제주도는 아름다운 자연경관과 다양한 문화행사가 있어 여행객들에게 인기가 많습니다.
3월은 봄꽃이 만개하는 시기로, 특히 제주 봄꽃 축제가 열려 화사한 경치를 즐길 수 있습니다.

## 날씨 요약
3월 중순의 제주도는 온화한 날씨로, 평균 기온은 10도에서 15도 사이입니다.

## 행사/축제
- 제주 봄꽃 축제
- 제주 해비치 아트 페스티벌

## 맛집 추천
- 원담 (제주특별자치도 제주시 이도일동 1260-11)
- 봉주르마담 (제주특별자치도 서귀포시 강정동 208-4)
- 중문수두리보말칼국수 (제주특별자치도 서귀포시 중문동 2056-2)
- 대춘해장국 본점 (제주특별자치도 제주시 도남동 380-2)
- 소금바치순이네 (제주특별자치도 제주시 구좌읍 종달리 42-5)

## 1일 일정 제안 (오전/오후/저녁)
오전: 제주 봄꽃 축제 방문 오후: 중문수두리보말칼국수에서 점심 후 아트 페스티벌 관람
저녁: 원담에서 저녁 식사 후 해변 산책

## 오류 요약(errors)
없음
```

같은 방식으로 --date "2025-09-15"를 실행한 결과에서는 강릉이 추천되었고, 강릉 커피 축제·단오제 등 행사 정보와 해성집·회산장칼국수 등 맛집 5곳이 포함된 리포트가 생성되었다. 날짜만 바꾸어도 추천 지역과 행사·맛집 정보가 매번 다르게 생성되는 것을 확인해, LLM 추천 결과가 실제 입력값에 반응해 동작함을 검증했다.

![](images/img78.png)

*그림 33. 2025-09-15_travel_plan.md 렌더링 화면 — 강릉, 커피 축제·단오제, 맛집 5곳, 1일 일정까지 정상 생성됨*

## 12. 프로젝트 구조 및 README 구성

```
travel_project/
├── travel_planner.py     ← 메인 프로그램
├── requirements.txt      ← 필요 패키지 목록 (openai, requests, python-dotenv)
├── README.md              ← 프로그램 설명 문서
├── .gitignore             ← .env, __pycache__, venv 등 Git 제외 목록
├── .env.example            ← API 키 입력 템플릿 (실제 키 없음)
└── results/                ← 실행 결과 저장 폴더 (자동 생성)
    ├── 2025-03-15_data.json / 2025-03-15_travel_plan.md
    └── 2025-09-15_data.json / 2025-09-15_travel_plan.md
```

![](images/img64.png)

*그림 34. 개발 중 travel_project 폴더 구조 — __pycache__, results, .env.example, .gitignore, README, requirements, travel_planner.py*

![](images/img52.png)

*그림 35. requirements.txt 내용 — openai, requests, python-dotenv 버전 명시*

README.md에는 미션 개요, 기능 목록, 프로그램 흐름도, 설치 방법, API 키 설정(세션 환경변수/.env 두 방식), 실행 방법과 출력 예시, 결과물(JSON/Markdown) 형식 설명, 에러 처리 정책 표, 실제 테스트 검증 내역, 자체 점검표, 공용PC 보안 주의사항, 트러블슈팅 Q&A, 전체 소스 코드까지 포함해 이 문서 하나만으로 프로젝트를 이해·재현할 수 있도록 구체적으로 작성했다. README.md의 실제 내용은 14장 GitHub 최종 업로드 결과물에서 확인할 수 있다.

## 13. 전체 소스 코드 (travel_planner.py)

최종 제출된 travel_planner.py는 아래와 같이 7개 영역(설정값, 코드펜스 제거 유틸, 키 로드/검증, CLI 인자 처리, LLM 1차 추천, Kakao 맛집 검색, 리포트 생성/저장, 메인 흐름)으로 역할을 분리해 구현했다. 전체 코드(약 325줄)는 GitHub 저장소 및 14장에 원본 그대로 수록되어 있으며, 핵심 로직을 아래에 요약해 정리한다.

```
"""
Python 응용: API 활용 국내 여행지 추천 프로그램
- LLM(OpenAI)으로 날짜 기반 1차 여행지 추천(JSON)
- Kakao Local API로 추천 도시의 맛집 검색
- LLM(OpenAI)으로 최종 여행 리포트(Markdown) 생성
- 결과를 results/ 폴더에 JSON + Markdown으로 저장

실행 예시:
    python travel_planner.py --date "2025-03-15"
"""
import os, sys, json, time, argparse
from datetime import datetime
import requests

try:
    from dotenv import load_dotenv
    load_dotenv()   # .env 파일이 있으면 읽어서 환경변수로 등록 (없어도 에러 아님)
except ImportError:
    pass  # python-dotenv 미설치 시에도 세션 환경변수($env:)만으로 동작 가능

from openai import OpenAI
from openai import AuthenticationError, APIError

OPENAI_MODEL = "gpt-4o-mini"
KAKAO_SEARCH_COUNT = 5
LLM_JSON_RETRY_LIMIT = 1
PLACE_EMPTY_RETRY_LIMIT = 2

def strip_code_fence(text: str) -> str:
    """LLM 응답이 코드블록(```json ... ```)으로 감싸져 오는 경우 제거"""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text

def load_api_keys():
    """제약사항: 키 미설정 시 즉시 종료 + 안내"""
    openai_key = os.getenv("OPENAI_API_KEY")
    kakao_key = os.getenv("KAKAO_API_KEY")
    missing = [n for n, v in [("OPENAI_API_KEY", openai_key), ("KAKAO_API_KEY", kakao_key)] if not v]
    if missing:
        print(f"[AUTH_ERROR] 다음 환경변수가 설정되지 않았습니다: {', '.join(missing)}")
        print('→ PowerShell 예시: $env:OPENAI_API_KEY="본인 키"')
        sys.exit(1)
    return openai_key, kakao_key

def parse_args():
    parser = argparse.ArgumentParser(usage='python travel_planner.py --date "YYYY-MM-DD"')
    parser.add_argument("--date", required=True, help="여행 날짜 (형식: YYYY-MM-DD)")
    args = parser.parse_args()
    try:
        datetime.strptime(args.date, "%Y-%m-%d")
    except ValueError:
        parser.print_usage()
        print('날짜 형식이 올바르지 않습니다. 예: --date "2025-03-15"')
        sys.exit(1)
    return args.date

def get_recommendation(client, date, errors):
    """LLM 1차 추천(JSON) — 파싱 실패 시 프롬프트 보강 후 최대 1회 재시도"""
    base_prompt = f'''{date}에 여행하기 좋은 국내 도시를 1곳 추천해줘.
반드시 아래 JSON 형식으로만 답하고, 다른 설명은 절대 붙이지 마.
{{"recommended_city": "도시명", "weather": "날씨 요약",
 "events": ["행사1", "행사2"], "reason": "추천 근거 2~4문장"}}'''
    prompt = base_prompt
    for attempt in range(1, LLM_JSON_RETRY_LIMIT + 2):
        try:
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}], temperature=0.7)
            content = strip_code_fence(response.choices[0].message.content)
            data = json.loads(content)
            if not all(k in data for k in ["recommended_city","weather","events","reason"]):
                raise ValueError("필수 키 누락")
            return data
        except (json.JSONDecodeError, ValueError) as e:
            print(f"[LLM_PARSE_ERROR] {attempt}번째 시도 파싱 실패: {e}")
            errors.append({"step": "recommendation", "type": "LLM_PARSE_ERROR", "message": str(e)})
            if attempt <= LLM_JSON_RETRY_LIMIT:
                prompt = base_prompt + "\n반드시 JSON 객체만 출력해."
                time.sleep(1); continue
            return {"recommended_city": "정보없음", "weather": "정보없음", "events": [],
                    "reason": "LLM 응답 파싱 실패로 추천 정보를 가져오지 못했습니다."}
        except AuthenticationError:
            print("[AUTH_ERROR] OpenAI 인증 실패(401/403).")
            errors.append({"step": "recommendation", "type": "AUTH_ERROR", "message": "OpenAI 401/403"})
            sys.exit(1)  # 핵심 기능이므로 즉시 종료
        except APIError as e:
            errors.append({"step": "recommendation", "type": "API_ERROR", "message": str(e)})
            if attempt <= LLM_JSON_RETRY_LIMIT:
                time.sleep(1); continue
            return {"recommended_city": "정보없음", "weather": "정보없음", "events": [],
                    "reason": "API 오류로 추천 정보를 가져오지 못했습니다."}

def search_restaurants(kakao_key, city, errors):
    """Kakao Local — 401/403은 즉시 데이터없음, 0건은 검색어를 바꿔 최대 2회 재시도"""
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {kakao_key}"}
    queries = [f"{city} 맛집", f"{city} 음식점", city]
    for attempt, query in enumerate(queries[:PLACE_EMPTY_RETRY_LIMIT + 1], start=1):
        try:
            res = requests.get(url, headers=headers,
                params={"query": query, "size": KAKAO_SEARCH_COUNT}, timeout=10)
            if res.status_code in (401, 403):
                print(f"[AUTH_ERROR] Kakao 인증 실패({res.status_code}).")
                errors.append({"step": "place_search", "type": "AUTH_ERROR", "message": f"HTTP {res.status_code}"})
                return []
            res.raise_for_status()
            documents = res.json().get("documents", [])
            if documents:
                return [{"name": d.get("place_name",""), "address": d.get("address_name",""),
                          "category": d.get("category_name",""), "url": d.get("place_url",""),
                          "x": d.get("x",""), "y": d.get("y","")} for d in documents]
            print(f"[EMPTY_RESULT] '{query}' 검색 결과 0건 ({attempt}/{PLACE_EMPTY_RETRY_LIMIT+1}차)")
            errors.append({"step": "place_search", "type": "EMPTY_RESULT", "message": f"0 results for query='{query}'"})
            time.sleep(0.5)
        except requests.exceptions.RequestException as e:
            errors.append({"step": "place_search", "type": "NETWORK_ERROR", "message": str(e)})
            return []
    return []  # 재시도 후에도 0건 → 데이터 없음

def generate_report(client, date, recommendation, restaurants, errors):
    """LLM 2차 호출 — 최종 Markdown 리포트 생성 (실패 시 기본 템플릿 대체)"""
    city = recommendation.get("recommended_city", "정보없음")
    restaurant_text = "\n".join(f"- {r['name']} ({r['address']})" for r in restaurants) \
        if restaurants else "데이터 없음 (장소 검색 결과 0건 또는 API 오류)"
    prompt = f'''아래 정보로 여행 리포트를 Markdown으로 작성해줘. 코드블록으로 감싸지 말고,
첫 줄은 반드시 "## 추천 지역"으로 시작해. 섹션: 추천 지역/이유, 날씨 요약, 행사/축제,
맛집 추천, 1일 일정 제안(오전/오후/저녁). 맛집: {restaurant_text}'''
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL, messages=[{"role": "user", "content": prompt}], temperature=0.6)
        report_body = strip_code_fence(response.choices[0].message.content)
        lines = report_body.split("\n")
        i = 0
        while i < len(lines) and lines[i].strip() == "": i += 1
        if i < len(lines) and lines[i].strip().startswith("# ") and not lines[i].strip().startswith("## "):
            lines = lines[i+1:]
        report_body = "\n".join(lines).strip()
    except (AuthenticationError, APIError) as e:
        errors.append({"step": "report_generation", "type": "API_ERROR", "message": str(e)})
        report_body = f"## 추천 지역\n{city}\n\n## 맛집 추천\n{restaurant_text}"
    errors_text = "\n".join(f"- [{e['step']}] {e['type']}: {e['message']}" for e in errors) if errors else "없음"
    return f"# {date} 국내 여행 추천 리포트\n\n{report_body}\n\n## 오류 요약(errors)\n{errors_text}\n"

def save_results(date, recommendation, restaurants, report, errors):
    results_dir = os.path.join(os.getcwd(), "results")
    os.makedirs(results_dir, exist_ok=True)
    raw_data = {"date": date, "recommendation": recommendation, "restaurants": restaurants, "errors": errors}
    json_path = os.path.join(results_dir, f"{date}_data.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(raw_data, f, ensure_ascii=False, indent=2)
    md_path = os.path.join(results_dir, f"{date}_travel_plan.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(report)
    return json_path, md_path

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
    print(f"  - 맛집 {len(restaurants)}곳 검색 완료" if restaurants else "  - 검색 결과 없음")
    print("[3/3] 최종 리포트 생성 중(LLM)...")
    report = generate_report(client, date, recommendation, restaurants, errors)
    print("  - 리포트 생성 완료")
    json_path, md_path = save_results(date, recommendation, restaurants, report, errors)
    print(f"\n완료! 원본 데이터: {json_path}\n 여행 리포트: {md_path}")
    if errors:
        print(f"  - 처리 중 {len(errors)}건의 오류/경고가 기록되었습니다.")

if __name__ == "__main__":
    main()
```

> ※ 위 코드는 실제 travel_planner.py(약 325줄, 15.5KB)와 동일한 로직을 유지하되 주석·공백을 일부 축약해 수록했다. 전체 원본 파일은 14장 GitHub 저장소 캡처(그림 46) 및 제출 폴더의 travel_planner.py에서 확인할 수 있다.

## 14. GitHub 최종 업로드 결과물

정리가 끝난 최종 결과물은 GitHub 저장소(A1-2)에 업로드해 제출했다. 아래는 실제 저장소에 반영된 최종 파일 목록과, 각 파일이 GitHub 상에서 정상적으로 열람되는 모습을 캡처한 것이다. 이 장의 내용은 로컬 PC가 아닌 GitHub에 실제로 업로드·보존된 최종 산출물을 기준으로 작성했다.

![](images/img81.png)

*그림 36. GitHub 저장소(A1-2, main 브랜치, 3 Commits) — .env.example, .gitignore, 2025-03-15_data.json, 2025-03-15_travel_plan.md, 2025-09-15_data.json, 2025-09-15_travel_plan.md, README.md, requirements.txt, travel_planner.cpython-314.pyc, travel_planner.py 총 10개 파일 업로드 완료*

### 14-1. 설정·보안 파일

![](images/img82.png)

*그림 37. GitHub — .env.example (2 lines) — 실제 키 값 없이 OPENAI_API_KEY / KAKAO_API_KEY 형식만 표시*

![](images/img83.png)

*그림 38. GitHub — .gitignore (4 lines) — venv/, .env, __pycache__/, *.pyc 제외 목록*

> 주의할 점 — .gitignore에 *.pyc를 등록해 두었음에도, 저장소 루트에 travel_planner.cpython-314.pyc 파일이 실제로 업로드되어 있음을 그림 45에서 확인했다(아래 14-3 참고). 이는 __pycache__ 폴더 밖에 남아 있던 캐시 파일을 함께 업로드한 실수로, 제출물 정리 시 .gitignore 규칙이 이미 추적 중인 파일에는 소급 적용되지 않는다는 점을 실무적으로 확인한 사례다.

### 14-2. 결과 데이터 (results)

![](images/img84.png)

*그림 39. GitHub — 2025-03-15_data.json 원본 데이터 (recommendation, restaurants 필드 포함)*

![](images/img85.png)

*그림 40. GitHub — 2025-03-15_travel_plan.md 미리보기(Preview) — 제주도 여행 리포트가 정상 렌더링됨*

![](images/img86.png)

*그림 41. GitHub — 2025-09-15_data.json 원본 데이터 (recommended_city "강릉" 등)*

![](images/img87.png)

*그림 42. GitHub — 2025-09-15_travel_plan.md 미리보기 — 강릉 여행 리포트가 정상 렌더링됨*

### 14-3. README 및 소스 코드

![](images/img88.png)

*그림 43. GitHub — README.md 미리보기 (734 lines / 31KB) — 미션 개요, 기능 목록, 에러 처리 정책 표 등이 정상 렌더링됨*

![](images/img89.png)

*그림 44. GitHub — requirements.txt (3 lines) — openai, requests, python-dotenv 버전 명시*

![](images/img90.png)

*그림 45. GitHub — travel_planner.cpython-314.pyc (16.6KB, 바이너리) — 캐시 파일이 실수로 함께 업로드된 모습*

![](images/img91.png)

*그림 46. GitHub — travel_planner.py 원본 (398 lines / 15.5KB) — 13장에 요약 수록한 전체 소스 코드의 실제 업로드본*

## 15. 요구사항 자체 점검표

미션 소개 자료의 최종 결과물·기능 요구사항·개발 환경·제약 사항을 기준으로 스스로 반영 여부를 점검했다.

### 15-1. 최종 결과물

| 항목 | 확인 | 비고 |
|---|---|---|
| CLI 기반 Python 프로그램(travel_planner.py) 완성 | V |  |
| --date "YYYY-MM-DD" 옵션으로 실행, 형식 검증 포함 | V |  |
| 실행 시 진행 로그([1/3]~[3/3]) + 결과 저장 경로 출력 | V |  |
| results/ 폴더에 원본 데이터 JSON 1개 이상 생성 | V | 1차 추천 + 맛집 검색 결과 포함 |
| 최종 여행 리포트 Markdown 파일 생성 | V |  |
| README.md 작성 (개요/실행법/키 설정/결과 확인) | V |  |
| README에 API 키 유출 방지 주의사항 포함 | V |  |
| GitHub 저장소 업로드 및 최종 반영 확인 | V | 14장 참고 |

### 15-2. 기능 요구사항

| 항목 | 확인 | 비고 |
|---|---|---|
| argparse로 CLI 실행, 날짜 형식 틀리면 사용법 출력 후 종료 | V |  |
| LLM API 택1 구현 — OpenAI 계열 | V | gpt-4o-mini |
| 지도/장소 API 택1 구현 — Kakao Local | V | 국내 장소 검색 가능 |
| 1차 JSON에 recommended_city / weather / events / reason 포함 | V |  |
| 맛집 필드 name / address / category / url / x,y 포함, 5곳 검색 | V |  |
| 맛집 0건이어도 프로그램 중단 없이 계속 진행 | V |  |
| 최종 리포트에 추천지역/이유·날씨·행사·맛집·1일 일정 모두 포함 | V |  |
| try-except로 호출/파싱 오류 처리 | V | 7가지 상황별 정책 수립 |
| 결과를 results/에 JSON + Markdown으로 저장 | V |  |

### 15-3. 개발 환경·제약 사항(보안)

| 항목 | 확인 | 비고 |
|---|---|---|
| Python 3.10 이상 사용, 터미널(PowerShell)에서 실행 가능 | V | 웹 UI 구현 없음 |
| 코드에 API 키 직접 작성 안 함 (os.getenv()로만 로드) | V |  |
| .env 또는 환경변수로 키 관리 | V | 공용PC → 세션 환경변수 우선 |
| .gitignore에 .env 등록 | V |  |
| README/결과물에 실제 키 값 미포함 | V |  |
| 키 미설정 시 즉시 종료 + 설정 방법 안내 | V |  |
| 지도 API 실패해도 리포트 생성은 진행 | V |  |
| LLM JSON 파싱 실패 시 재시도 최대 1회로 제한 | V |  |

### 15-4. 실제 검증 여부 / 보너스

| 항목 | 확인 | 비고 |
|---|---|---|
| 정상 실행 케이스 2회 이상(서로 다른 날짜) | V | 2025-03-15 / 2025-09-15 |
| API 키 미설정·인증 실패(401) 케이스 직접 재현 | V |  |
| 맛집 검색 0건(EMPTY_RESULT) 케이스 직접 재현 | V | REPL 직접 호출로 검증 |
| CLI 옵션 누락/날짜 형식 오류 케이스 직접 재현 | V |  |
| (보너스) 복수 지역 추천, 결과 캐싱 | - | 미구현 (기본 요구사항 우선 완료) |

## 16. 작업 과정에서 배운 점

- 터미널에서 파일을 실행할 때는 파일이 저장된 위치와 터미널의 현재 작업 폴더가 일치해야 하고, 명령어의 "파일명" 자리에는 실제 파일명을 입력해야 한다는 점을, System32 FileNotFoundError와 python 파일명.py 오타를 통해 직접 체감했다.
- 한글 등 비ASCII 문자를 다루는 프로그램에서는 인코딩(UTF-8) 설정이 실행 성공 여부를 좌우할 수 있으며, 파일 입출력 시 encoding="utf-8"을 명시하는 습관이 왜 중요한지 실제 오류를 통해 배웠다.
- API 응답 필드는 항상 값이 채워져 있다고 가정하면 안 되며, or 연산자나 .get(key, 기본값)과 같은 방어적 코드로 빈 값·누락 필드에 대비해야 한다는 것을 확인했다.
- LLM은 형식 지시(코드블록 금지, 제목 중복 금지 등)를 완벽히 지키지 않을 수 있으므로, 프롬프트 설계뿐 아니라 후처리 코드(코드펜스 제거, 중복 제목 제거)로 이중 안전장치를 마련하는 것이 안정적인 결과를 만든다는 점을 실제 버그 발생 화면(그림 12, 13)을 통해 배웠다.
- 앞 단계의 출력을 다음 단계의 입력으로 그대로 넘기는 파이프라인 설계(1차 추천 JSON → 맛집 검색 → 최종 리포트)를 통해, 여러 API를 엮어 하나의 인사이트를 만드는 흐름을 직접 구현해볼 수 있었다.
- 공용PC에서는 .env 파일보다 세션 임시 환경변수가 안전하며, 화면을 캡처해 공유할 때도 키 값을 부분(.Substring())만 노출하는 습관이 필요하다는 보안 감각을 익혔다.
- 오류 발생을 무조건 프로그램 중단으로 처리하지 않고, "어떤 오류는 즉시 종료해야 하고 어떤 오류는 기본값으로 계속 진행해야 하는지"를 상황별로 구분해 설계하는 것이 실무적인 에러 처리 방식이라는 점을 이해했다.
- 완성 후 REPL로 함수를 직접 호출하거나 환경변수를 의도적으로 잘못 설정하는 등 오류 상황을 하나씩 재현해 검증하는 과정을 거치면서, "동작하는 것처럼 보이는 코드"와 "검증된 코드"의 차이를 체감했다.
- .gitignore에 *.pyc를 등록해도 이미 커밋된 파일에는 소급 적용되지 않는다는 것을 GitHub 업로드 결과(그림 45)에서 실제로 확인하며, Git의 추적 규칙에 대한 실무 감각을 얻었다.

## 17. 제출 자료 최종 확인

| 제출 항목 | 내용 | 확인 |
|---|---|---|
| 메인 프로그램 | travel_planner.py | V |
| 실행 결과 데이터 | results/2025-03-15_data.json, results/2025-09-15_data.json 등 원본 데이터 + 오류 기록 | V |
| 최종 여행 리포트 | results/2025-03-15_travel_plan.md, results/2025-09-15_travel_plan.md | V |
| README.md | 미션 개요·기능 목록·흐름도·설치·실행법·에러 정책·검증 내역·점검표·전체 코드 포함 | V |
| requirements.txt | openai, requests, python-dotenv | V |
| .env.example | 키 값 없이 형식만 담은 템플릿 | V |
| .gitignore | .env, __pycache__/, *.pyc 등 제외 목록 | V |
| GitHub 업로드 | A1-2 저장소 main 브랜치에 10개 파일 최종 반영 | V |
| 보안 처리 | 코드/README/결과물 어디에도 실제 API 키 값 미포함 | V |
| 실제 오류 재현 검증 | 키 미설정, 인증 실패, 검색 0건, CLI 옵션 오류 등 총 7가지 케이스 | V |

위 표를 기준으로 미션 소개 자료의 최종 결과물·기능 요구사항·개발 환경·제약 사항 4개 영역을 모두 충족했음을 확인했다. 본 보고서는 실제 작업 과정에서 발생한 오류와 그 해결 과정을 포함하여 Claude와의 대화 기록 및 실제 캡처 화면을 근거로 작성되었다.

### 17-1. 제출 스크린샷 예시

아래는 실제 제출 폴더와 GitHub 저장소에 결과물이 정상 반영된 모습을 다시 한 번 확인할 수 있는 캡처 화면이다.

![](images/img80.png)

*그림 47. results/ 폴더 — 2025-03-15, 2025-09-15 두 날짜의 JSON·Markdown 결과 파일만 남은 최종 제출 상태*

![](images/img81.png)

*그림 48. GitHub 저장소(A1-2) — travel_planner.py, README.md, requirements.txt, .env.example, .gitignore, 결과 파일까지 업로드 완료된 최종 모습*

> 보고서를 마치며 — 이번 미션은 단일 API 호출을 넘어, 서로 다른 두 API(LLM·지도 검색)의 결과를 이어 붙여 하나의 결과물을 만드는 경험이었다. 파일 경로 오류, 인코딩 문제, 응답 필드 누락, LLM의 형식 무시(코드펜스·중복 제목)처럼 실제로 부딪힌 문제들을 하나씩 해결해 나가면서, 오류 메시지를 읽고 원인을 좁혀가는 과정 자체가 이번 학습의 핵심이었다는 것을 느꼈다. 완성된 travel_planner.py와 README.md, GitHub 저장소, 그리고 이 보고서를 통해 프로그램의 동작 원리와 검증 과정을 누구나 다시 확인할 수 있도록 정리했다.
