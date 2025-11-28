"""******************************************************************
  - Project          : Termux Battery Warning System
  - File name        : battery_warning.py
  - Description      : Send Termux battery status to SmartThings
  - Owner            :
  - Revision history : 1) 2025.11.28 : Initial release
                     : 2) 2025.11.28 : Added log identifier [BATTERY WARNING], simplified logging, and unified exception handling.
                     : 3) 2025.11.28 : Removed non-critical INFO logs, unified most exceptions, and translated logs to English.
*******************************************************************"""

import subprocess
import json
import logging

# 로깅 설정 (로그 내용은 영어로 유지)
logging.basicConfig(
    format='%(asctime)s %(levelname)s:%(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%dT%H:%M:%S',
)

# 로그 식별자 상수 정의
LOG_IDENTIFIER = "[BATTERY WARNING]"

# --- 사용자 설정 영역 ---
SMARTTHINGS_DEVICE_ID = "" 
LOW_BATTERY_THRESHOLD = 30  # 경고 기준: 30% 이하 (비충전 시)
CRITICAL_BATTERY_THRESHOLD = 15 # 위험 기준: 15% 이하 (충전 여부 무관)

# --- 함수 정의 ---

def get_termux_battery_status():
    """termux-battery-status 명령을 실행하여 배터리 잔량과 충전 상태를 반환합니다."""
    try:
        # termux-battery-status 명령 실행
        result = subprocess.run(
            ["termux-battery-status"], 
            capture_output=True, 
            text=True, 
            check=True,
            timeout=5
        )
        
        # JSON 파싱 및 데이터 추출
        battery_data = json.loads(result.stdout)
        percentage = int(battery_data.get("percentage", 0))
        is_charging = battery_data.get("status") in ["CHARGING", "FULL"]
        
        # 핵심 상태 확인용 INFO 로그 (이 로그는 유지)
        logging.info(f"{LOG_IDENTIFIER} Status retrieved: {percentage}% | Charging: {is_charging}")
        
        return percentage, is_charging
        
    # 명령어를 찾을 수 없는 경우 (Termux API 미설치 등)에 대한 구체적인 처리
    except FileNotFoundError:
        logging.error(f"{LOG_IDENTIFIER} 'termux-battery-status' command not found. (Termux-API error)")
        return None, None
    # 그 외 모든 예외 (CalledProcessError, JSON 파싱 오류 등) 포괄 처리
    except Exception as e:
        logging.error(f"{LOG_IDENTIFIER} An unexpected error occurred in battery status retrieval : {e}")
        return None, None


def send_smartthings_command(device_id, command):
    """SmartThings CLI 명령을 실행합니다. 실패 시에만 로그를 남깁니다."""
    try:
        command_list = ["smartthings", "devices:commands", device_id, command]
        
        # 명령 실행 (출력은 버림)
        subprocess.run(
            command_list, 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.PIPE, 
            check=True, 
            timeout=10
        )
        # 성공 시 로그를 남기지 않음 (로그 혼잡 방지)
        return True
    
    # SmartThings 서버나 네트워크 문제로 인한 실패 처리
    except subprocess.CalledProcessError as e:
        logging.warning(f"{LOG_IDENTIFIER} SmartThings command FAILED: {command}. Error: {e.stderr.decode().strip()}")
        return False
    # 그 외 모든 예외 처리 (CLI 미설치, 타임아웃 등)
    except Exception as e:
        logging.error(f"{LOG_IDENTIFIER} An unexpected error occurred during SmartThings command : {e}")
        return False

# --- 메인 로직 ---

def main():

    # 1. 배터리 상태 가져오기
    percentage, is_charging = get_termux_battery_status()
    
    if percentage is None:
        return

    # 2. SmartThings 조광기 레벨 업데이트 (배터리 잔량 전송)
    level_command = f"switchLevel:setLevel({percentage})"
    send_smartthings_command(SMARTTHINGS_DEVICE_ID, level_command)

    # 3. 경고 조건 확인 및 SmartThings 스위치 제어
    
    # 조건 1: 배터리 30% 이하이고 충전 중이 아님
    condition_low = (percentage <= LOW_BATTERY_THRESHOLD) and (not is_charging)
    
    # 조건 2: 배터리 15% 이하 (충전 상태 무관)
    condition_critical = (percentage <= CRITICAL_BATTERY_THRESHOLD)

    if condition_low or condition_critical:
        # 경고 조건 충족 시 스위치 ON 전송
        reason = ""
        if condition_low and not condition_critical: reason = f"Below {LOW_BATTERY_THRESHOLD}% & Not Charging"
        elif condition_critical: reason = f"Critical below {CRITICAL_BATTERY_THRESHOLD}%"
        
        logging.warning(f"{LOG_IDENTIFIER} WARNING Triggered! Reason: {reason}")
        send_smartthings_command(SMARTTHINGS_DEVICE_ID, "switch:on")
    else:
        # 경고 해제 및 다음 알림을 위해 스위치 OFF 전송 (안전 상태 로그 생략)
        send_smartthings_command(SMARTTHINGS_DEVICE_ID, "switch:off")


if __name__ == "__main__":
    main()