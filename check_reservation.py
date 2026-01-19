#!/usr/bin/env python3
"""한라산 예약 모니터링 봇 - 2026년 2월 6일 예약 현황 체크"""

import os
import requests
from bs4 import BeautifulSoup

WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")
TARGET_DATE = "20260206"
MIN_AVAILABLE = 2

COURSES = {
    "성판악": 242,
}


def fetch_reservation_status(course_seq: int) -> str:
    """예약 현황 페이지 HTML을 가져옵니다."""
    url = "https://visithalla.jeju.go.kr/reservation/status.do"
    data = {
        "searchYear": "2026",
        "searchMonth": "02",
        "courseSeq": course_seq,
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    response = requests.post(url, data=data, headers=headers, timeout=30)
    response.raise_for_status()
    return response.text


def parse_available_count(html: str, target_date: str) -> int:
    """HTML에서 특정 날짜의 남은 자리 수를 파싱합니다."""
    soup = BeautifulSoup(html, "html.parser")
    td = soup.find("td", id=f"TD_{target_date}")

    if not td:
        return 0

    # rev_full 클래스가 있으면 마감
    if "rev_full" in td.get("class", []):
        return 0

    # span 태그에서 숫자 추출
    title_div = td.find("div", class_="title01")
    if title_div:
        span = title_div.find("span")
        if span:
            try:
                return int(span.get_text(strip=True))
            except ValueError:
                return 0

    return 0


def send_slack_notification(results: dict[str, int]) -> None:
    """Slack으로 알림을 보냅니다."""
    if not WEBHOOK_URL:
        print("SLACK_WEBHOOK_URL이 설정되지 않았습니다.")
        return

    lines = ["🏔️ *한라산 예약 알림!*", "", "📅 2026년 2월 6일", ""]

    for course_name, count in results.items():
        if count >= MIN_AVAILABLE:
            lines.append(f"✅ {course_name}: *{count}자리* 남음")

    lines.append("")
    lines.append("🔗 <https://visithalla.jeju.go.kr/reservation/status.do|지금 예약하러 가기>")

    payload = {"text": "\n".join(lines)}
    response = requests.post(WEBHOOK_URL, json=payload, timeout=10)
    response.raise_for_status()
    print("Slack 알림 전송 완료!")


def main():
    print(f"한라산 예약 현황 체크 중... (대상: 2026년 2월 6일)")

    results = {}
    available_courses = {}

    for course_name, course_seq in COURSES.items():
        html = fetch_reservation_status(course_seq)
        count = parse_available_count(html, TARGET_DATE)
        results[course_name] = count
        print(f"  {course_name}: {count}자리 남음")

        if count >= MIN_AVAILABLE:
            available_courses[course_name] = count

    if available_courses:
        print(f"\n🎉 {MIN_AVAILABLE}자리 이상 남은 코스 발견!")
        send_slack_notification(available_courses)
    else:
        print(f"\n아쉽지만 {MIN_AVAILABLE}자리 이상 남은 코스가 없습니다.")


if __name__ == "__main__":
    main()
