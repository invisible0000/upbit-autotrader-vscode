#!/usr/bin/env python3
"""requests.py 파일 완전 수정"""

def fix_requests_file_complete():
    file_path = r"upbit_auto_trading\infrastructure\market_data_backbone\smart_data_provider\models\requests.py"

    # 파일 읽기
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 줄별로 처리
    for i, line in enumerate(lines):
        # UnifiedDataRequest가 아직 남아있는 곳들 수정
        if "'UnifiedDataRequest'" in line:
            lines[i] = line.replace("'UnifiedDataRequest'", "'DataRequest'")
        elif "UnifiedDataRequest" in line:
            lines[i] = line.replace("UnifiedDataRequest", "DataRequest")

    # 파일 저장
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print("requests.py 파일 완전 수정 완료")

if __name__ == "__main__":
    fix_requests_file_complete()
