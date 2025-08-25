#!/usr/bin/env python3
"""requests.py 파일에서 UnifiedDataRequest를 DataRequest로 일괄 변경"""

import re

def fix_requests_file():
    file_path = r"upbit_auto_trading\infrastructure\market_data_backbone\smart_data_provider\models\requests.py"

    # 파일 읽기
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # UnifiedDataRequest를 DataRequest로 변경
    content = content.replace("'UnifiedDataRequest'", "'DataRequest'")
    content = content.replace("UnifiedDataRequest", "DataRequest")

    # 마지막 별칭 부분 제거
    content = re.sub(r'\n# 하위 호환성을 위한 별칭\nDataRequest = DataRequest\n?', '\n', content)

    # 파일 저장
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("requests.py 파일 수정 완료")

if __name__ == "__main__":
    fix_requests_file()
