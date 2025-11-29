"""******************************************************************
  - Project          : Termux Commute Salary Calculator
  - File name        : salary_calculator.py
  - Description      : Calculate salary based on commute.txt log
  - Owner            : User
  - Revision history : 1) 2025.03.XX : Initial release (Based on 2025 min wage)
*******************************************************************"""

import datetime
import os

# --- 설정 영역 ---
INPUT_FILE = "./commute.txt"
HOURLY_WAGE = 10030  # 2025년 최저시급 (원)

def parse_log_line(line):
    """로그 한 줄을 파싱하여 (datetime, type) 튜플로 반환"""
    try:
        # 예: "2025-03-20 12:41:53 출근"
        parts = line.strip().split(" ")
        if len(parts) < 3:
            return None
        
        date_str = parts[0]
        time_str = parts[1]
        action = parts[2] # "출근" or "퇴근"
        
        full_time_str = f"{date_str} {time_str}"
        dt = datetime.datetime.strptime(full_time_str, "%Y-%m-%d %H:%M:%S")
        
        return dt, action
    except ValueError:
        return None

def calculate_salary(file_path):
    if not os.path.exists(file_path):
        print(f"Error: {file_path} 파일을 찾을 수 없습니다.")
        return

    logs = []
    
    # 1. 파일 읽기 및 파싱
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            parsed = parse_log_line(line)
            if parsed:
                logs.append(parsed)
    
    # 2. 시간순 정렬 (혹시 모를 뒤섞임 방지)
    logs.sort(key=lambda x: x[0])

    total_seconds = 0
    last_clock_in = None
    work_sessions = [] # 상세 내역 저장용

    print(f"--- [ 급여 정산 보고서 ] ---")
    print(f"기준 시급: {HOURLY_WAGE:,}원 (2025년 최저임금)\n")

    # 3. 근무 시간 계산 로직
    for dt, action in logs:
        if action == "출근":
            if last_clock_in is not None:
                print(f"[주의] {last_clock_in} 출근 기록 후 퇴근 없이 다시 출근이 찍혔습니다. 이전 기록 무시됨.")
            last_clock_in = dt
            
        elif action == "퇴근":
            if last_clock_in is None:
                # 출근 기록 없이 퇴근만 있는 경우 (로그 시작 전 출근 등)
                print(f"[무시됨] {dt} 퇴근 기록에 매칭되는 출근 기록이 없습니다.")
            else:
                # 정상적인 출퇴근 쌍
                duration = dt - last_clock_in
                seconds = duration.total_seconds()
                total_seconds += seconds
                
                hours = seconds / 3600
                pay = hours * HOURLY_WAGE
                
                work_sessions.append({
                    "start": last_clock_in,
                    "end": dt,
                    "hours": hours,
                    "pay": pay
                })
                
                # 계산 완료 후 출근 기록 초기화
                last_clock_in = None

    # 4. 결과 출력
    total_hours = total_seconds / 3600
    total_salary = total_hours * HOURLY_WAGE

    print(f"\n--- [ 상세 근무 내역 ] ---")
    for session in work_sessions:
        print(f"{session['start']} ~ {session['end']} | {session['hours']:.2f}시간 | {int(session['pay']):,}원")

    print(f"\n==============================")
    print(f"총 근무 시간 : {total_hours:.2f} 시간")
    print(f"총 예상 급여 : {int(total_salary):,} 원")
    print(f"==============================")

if __name__ == "__main__":
    calculate_salary(INPUT_FILE)