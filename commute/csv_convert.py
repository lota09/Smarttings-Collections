"""******************************************************************
  - Project          : Termux Commute Log to CSV Converter
  - File name        : txt_to_csv_converter.py
  - Description      : Convert commute.txt to commute_report.csv
  - Owner            : User
  - Revision history : 1) 2025.03.XX : Initial release
                     : 2) 2025.03.XX : Handle duplicates & absolute timestamps
*******************************************************************"""

import csv
import datetime
import os

# --- 설정 영역 ---
INPUT_FILE = "./commute.txt"
OUTPUT_FILE = "./commute_report.csv"
HOURLY_WAGE = 10030  # 2025년 최저시급

def parse_log_line(line):
    """로그 한 줄을 파싱하여 (datetime, type) 튜플로 반환"""
    try:
        parts = line.strip().split(" ")
        if len(parts) < 3:
            return None
        
        date_str = parts[0]
        time_str = parts[1]
        action = parts[2]
        
        full_time_str = f"{date_str} {time_str}"
        dt = datetime.datetime.strptime(full_time_str, "%Y-%m-%d %H:%M:%S")
        
        return dt, action
    except ValueError:
        return None

def convert_to_csv():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} 파일을 찾을 수 없습니다.")
        return

    logs = []
    
    # 1. 로그 파일 읽기
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            parsed = parse_log_line(line)
            if parsed:
                logs.append(parsed)
    
    # 2. 시간순 정렬
    logs.sort(key=lambda x: x[0])

    csv_rows = []
    last_clock_in = None

    # 3. 데이터 가공 및 근무시간 계산
    for dt, action in logs:
        if action == "출근":
            # 이미 출근 상태라면 연속된 출근 기록(중복 터치 등)은 무시하고 첫 기록 유지
            if last_clock_in is None:
                last_clock_in = dt
            else:
                print(f"[중복 무시] {last_clock_in}에 이미 출근했는데 {dt}에 또 출근이 감지되었습니다.")
            
        elif action == "퇴근":
            if last_clock_in:
                # 파이썬 datetime 객체끼리의 연산이므로 날짜가 넘어가도(Overnight) 정확히 계산됨
                duration = dt - last_clock_in
                seconds = duration.total_seconds()
                hours = seconds / 3600
                pay = int(hours * HOURLY_WAGE)
                
                # 엑셀 호환을 위해 'YYYY-MM-DD HH:MM:SS' 절대 시간 형식으로 저장
                start_time_str = last_clock_in.strftime("%Y-%m-%d %H:%M:%S")
                end_time_str = dt.strftime("%Y-%m-%d %H:%M:%S")

                csv_rows.append({
                    "날짜": last_clock_in.strftime("%Y-%m-%d"), # 기준 일자
                    "출근시간": start_time_str, # 절대 시간
                    "퇴근시간": end_time_str,   # 절대 시간
                    "근무시간": round(hours, 2),
                    "급여": pay
                })
                
                # 정산 완료 후 초기화 (이후 연속된 퇴근 기록은 last_clock_in이 None이라 자동 무시됨)
                last_clock_in = None
            else:
                 print(f"[무시됨] 출근 기록 없이 퇴근 기록만 있습니다: {dt}")

    # 4. CSV 파일 쓰기 (utf-8-sig 사용으로 엑셀 한글 깨짐 방지)
    with open(OUTPUT_FILE, "w", encoding="utf-8-sig", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["날짜", "출근시간", "퇴근시간", "근무시간", "급여"])
        writer.writeheader()
        writer.writerows(csv_rows)

    print(f"변환 완료! 결과 파일: {OUTPUT_FILE}")
    print(f"총 {len(csv_rows)}건의 근무 기록이 변환되었습니다.")

if __name__ == "__main__":
    convert_to_csv()