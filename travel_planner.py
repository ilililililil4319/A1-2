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
