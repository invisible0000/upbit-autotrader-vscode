#!/usr/bin/env python3
"""smart_data_provider.py 파일에서 UnifiedDataResponse를 DataResponse로, ResponseMetadata를 dict로 일괄 변경"""

import re

def fix_smart_data_provider():
    file_path = r"upbit_auto_trading\infrastructure\market_data_backbone\smart_data_provider\core\smart_data_provider.py"

    # 파일 읽기
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # UnifiedDataResponse를 DataResponse로 변경
    content = content.replace("UnifiedDataResponse", "DataResponse")

    # ResponseMetadata 사용 패턴 수정 (클래스 형태에서 dict 형태로)
    # ResponseMetadata(key=value, ...) -> {'key': value, ...} 형태로 변경

    # 간단한 ResponseMetadata(...) 패턴 찾기
    pattern = r'ResponseMetadata\(\s*([^)]+)\s*\)'

    def replace_response_metadata(match):
        params_str = match.group(1)
        # key=value 형태를 'key': value 형태로 변환
        params_str = re.sub(r'(\w+)=', r"'\1': ", params_str)
        return f"{{{params_str}}}"

    content = re.sub(pattern, replace_response_metadata, content)

    # 일부 수동 수정이 필요한 특수 케이스들
    # metadata=ResponseMetadata -> metadata=
    content = content.replace("metadata=ResponseMetadata", "metadata=")

    # ResponseMetadata import 제거
    content = re.sub(r'from \.\.models\.responses import.*ResponseMetadata.*\n', '', content)

    # 파일 저장
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("smart_data_provider.py 파일 수정 완료")

if __name__ == "__main__":
    fix_smart_data_provider()
