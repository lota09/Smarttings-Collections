"""******************************************************************
  - Project          : Termux Battery Info Sync System
  - File name        : battery_info_sync.py (formerly battery_warning.py)
  - Description      : Transmit Termux battery status (level, power source) to SmartThings
  - Owner            : Seokmin Kang
  - Revision history : 1) 2025.11.28 : Warning logic removed, changed to information transmission only
                     : 2) 2025.11.28 : Updated to commands compatible with Custom Edge Driver
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

# 로그 식별자 (단순 정보 전달이므로 STATUS로 변경)
LOG_IDENTIFIER = "[BAT STATUS]"

# --- 사용자 설정 영역 ---
# vEdge Creator 등으로 생성된 커스텀 가상 장치의 ID
SMARTTHINGS_DEVICE_ID = "YOUR_DEVICE_ID_HERE"

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
        # status가 CHARGING 또는 FULL이면 충전 중(DC)으로 간주
        is_charging = battery_data.get("status") in ["CHARGING", "FULL"]
        
        # 상태 확인용 로그 (핵심 정보이므로 INFO 유지)
        logging.info(f"{LOG_IDENTIFIER} Retrieved: {percentage}% | Charging: {is_charging}")
        
        return percentage, is_charging
        
    # 명령어를 찾을 수 없는 경우 (Termux API 미설치 등)
    except FileNotFoundError:
        logging.error(f"{LOG_IDENTIFIER} 'termux-battery-status' command not found. (Termux-API error)")
        return None, None
    # 그 외 모든 예외 포괄 처리
    except Exception as e:
        logging.error(f"{LOG_IDENTIFIER} Unexpected error in battery retrieval: {e}")
        return None, None


def send_smartthings_command(device_id, command):
    """SmartThings CLI 명령을 실행합니다. 실패 시에만 로그를 남깁니다."""
    try:
        # 쉘 인젝션 방지를 위해 리스트 형태로 명령 구성
        # 주의: command 문자열 내부에 공백이나 따옴표가 있어도 하나의 인자로 전달됨
        full_command = ["smartthings", "devices:commands", device_id, command]
        
        # 명령 실행 (출력은 버림)
        subprocess.run(
            full_command, 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.PIPE, 
            check=True, 
            timeout=10
        )
        # 성공 시 로그 생략 (성능 및 로그 가독성 최적화)
        return True
    
    except subprocess.CalledProcessError as e:
        logging.warning(f"{LOG_IDENTIFIER} ST Command FAILED: {command}. Error: {e.stderr.decode().strip()}")
        return False
    except Exception as e:
        logging.error(f"{LOG_IDENTIFIER} Unexpected error sending command: {e}")
        return False

# --- 메인 로직 ---

def main():
    # 1. 배터리 상태 가져오기
    percentage, is_charging = get_termux_battery_status()
    
    if percentage is None:
        return

    # 2. SmartThings로 정보 전송
    # 경고 로직(if문)은 모두 제거되고, 순수하게 상태만 업데이트합니다.

    # 2-1. 배터리 잔량 전송 (Capability: partyvoice23922.vbatterylevel)
    level_cmd = f"partyvoice23922.vbatterylevel:setLevel({percentage})"
    send_smartthings_command(SMARTTHINGS_DEVICE_ID, level_cmd)

    # 2-2. 전원 소스 전송 (Capability: partyvoice23922.powersource)
    # 충전 중이면 "DC", 아니면 "Battery"
    source_value = "DC" if is_charging else "Battery"
    
    # 문자열 값은 따옴표로 감싸서 전송해야 함
    source_cmd = f'partyvoice23922.powersource:setSource("{source_value}")'
    send_smartthings_command(SMARTTHINGS_DEVICE_ID, source_cmd)


if __name__ == "__main__":
    main()