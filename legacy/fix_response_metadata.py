#!/usr/bin/env python3
"""smart_data_provider.py 파일에서 ResponseMetadata를 dict로 안전하게 변환"""

import re

def fix_response_metadata():
    file_path = r"upbit_auto_trading\infrastructure\market_data_backbone\smart_data_provider\core\smart_data_provider.py"

    # 파일 읽기
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # ResponseMetadata( ... ) 패턴을 { ... } 로 변환
    # 간단한 케이스들부터 처리

    # 1. metadata=ResponseMetadata( -> metadata={
    content = content.replace("metadata=ResponseMetadata(", "metadata={")

    # 2. ResponseMetadata( -> {
    content = content.replace("ResponseMetadata(", "{")

    # 3. 다중 라인 ResponseMetadata도 처리
    # ) 만 있는 라인들을 } 로 변환 (문맥상 적절한 것만)
    lines = content.split('\n')
    for i, line in enumerate(lines):
        stripped = line.strip()
        # ResponseMetadata의 닫는 괄호로 보이는 라인들
        if stripped == ')' and i > 0:
            prev_lines = lines[max(0, i-10):i]
            # 이전 라인들 중에 metadata={ 가 있으면 } 로 변환
            prev_content = '\n'.join(prev_lines)
            if 'metadata={' in prev_content and not '}' in prev_content:
                lines[i] = line.replace(')', '}')

    content = '\n'.join(lines)

    # 4. 키워드 인수를 딕셔너리 형태로 변환
    # source= -> 'source':
    # response_time_ms= -> 'response_time_ms':
    # cache_hit= -> 'cache_hit':
    # records_count= -> 'records_count':

    content = re.sub(r'\bsource=', "'source': ", content)
    content = re.sub(r'\bresponse_time_ms=', "'response_time_ms': ", content)
    content = re.sub(r'\bcache_hit=', "'cache_hit': ", content)
    content = re.sub(r'\brecords_count=', "'records_count': ", content)
    content = re.sub(r'\bpriority_used=', "'priority_used': ", content)

    # 파일 저장
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("ResponseMetadata를 dict로 변환 완료")

if __name__ == "__main__":
    fix_response_metadata()
