'''*******************************************************************
  - Project          : Commute recorder
  - File name        : commute.py
  - Description      : Record commute log
  - Owner            : Seokmin.Kang
  - Revision history : 1) 2024.09.04 : Initial release
*******************************************************************'''

import subprocess
import datetime
import re
import os

# 상수 정의
LOG_LEVEL = "INFO"
DEVICE = "YOUR_DEVICE_HERE"
VERIFY_DEVICE= "YOUR_DEVICE_HERE"
FILE_PATH = "/data/data/com.termux/files/home/smartthings/logs/raw.log"

os.makedirs(os.path.dirname(FILE_PATH), exist_ok=True)

# commute.sh 스크립트를 실행하여 실시간으로 출력받음
process = subprocess.Popen(["tail", "-f", FILE_PATH], stdout=subprocess.PIPE, text=True)
output_file_path = "./commute.txt"

# 파일 경로를 절대 경로로 확장
output_file_path = subprocess.check_output(["realpath", output_file_path], text=True).strip()

# 출근 상태에 대한 한글 매핑
commute_map = {
    "on": "출근",
    "off": "퇴근",
}

# 실시간 출력 스트림을 읽음
for line in process.stdout:
    # INFO 유형과 서울 지역만 필터링
    if LOG_LEVEL in line and DEVICE in line:
        # UTC 시간, 유형, 장치, 장치상태 정보 추출
        #ex) 2024-09-04T08:33:34.510517130Z INFO Virtual Switch  <Device: 3a982628-a943-4bac-90be-483e7d478d30 (약 복용기록)> emitting event: {"attribute_id":"switch","capability_id":"switch","component_id":"main","state":{"value":"on"},"state_change":true}
        match = re.search(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\.\d+Z.*"state":{"value":"([^"]+)"}', line)
        if match:
            utc_time_str = match.group(1)
            commute_state = match.group(2)
            
            # UTC 시간을 한국 시간(GMT+9)으로 변환
            utc_time = datetime.datetime.strptime(utc_time_str, "%Y-%m-%dT%H:%M:%S")
            kst_time = utc_time + datetime.timedelta(hours=9)
            kst_time_str = kst_time.strftime("%Y-%m-%d %H:%M:%S")
            
            # 출근 정보 변환
            commute_korean = commute_map.get(commute_state, "알 수 없음")
            
            # 출력 내용 생성
            output_line = f"{kst_time_str} {commute_korean}\n"
            
            # 파일에 추가 모드로 기록
            with open(output_file_path, "a") as file:
                file.write(output_line)

            # 작동 확인 신호
            subprocess.run(["smartthings", "devices:commands", VERIFY_DEVICE, "switch:off"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)