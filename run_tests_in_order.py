#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
개발 순서에 따라 유닛 테스트를 실행하는 스크립트
"""

import os
import sys
import unittest
import glob
import re
import datetime
import inspect
import ast
from io import StringIO

def extract_test_info(file_path):
    """테스트 파일에서 테스트 정보를 추출합니다."""
    test_info = {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        # 파일 docstring 추출
        module = ast.parse(file_content)
        module_docstring = ast.get_docstring(module)
        
        if module_docstring:
            # 개발 순서 추출
            dev_order_match = re.search(r'개발 순서: (.*)', module_docstring)
            if dev_order_match:
                dev_order = dev_order_match.group(1).strip()
                test_info['dev_order'] = dev_order
        
        # 테스트 메서드 정보 추출
        for node in ast.walk(module):
            if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                method_name = node.name
                method_docstring = ast.get_docstring(node)
                
                if method_docstring:
                    test_info[method_name] = {
                        'description': method_docstring.strip()
                    }
                    
                    # 테스트 ID 추출
                    for line in ast.unparse(node).split('\n'):
                        id_match = re.search(r'=== 테스트 id ([0-9_]+): ([a-zA-Z0-9_]+) ===', line)
                        if id_match:
                            test_id = id_match.group(1)
                            test_info[method_name]['id'] = test_id
                            break
                    
                    # 입력 및 출력 정보 추출
                    input_output = {}
                    for line in ast.unparse(node).split('\n'):
                        # 입력 정보 추출
                        if '# 테스트 데이터' in line or '# 입력' in line:
                            input_output['input'] = line.strip()
                        # 출력 정보 추출
                        elif '# 결과' in line or '# 출력' in line or 'print(f"' in line:
                            if 'output' not in input_output:
                                input_output['output'] = []
                            input_output['output'].append(line.strip())
                    
                    if input_output:
                        test_info[method_name]['input_output'] = input_output
    
    except Exception as e:
        print(f"테스트 정보 추출 중 오류 발생: {e}")
    
    return test_info

def run_tests_in_order():
    """개발 순서에 따라 테스트 파일을 실행합니다."""
    # 현재 디렉토리 저장
    current_dir = os.getcwd()
    
    # 테스트 디렉토리로 이동
    test_dir = os.path.join(current_dir, "upbit_auto_trading", "tests", "unit")
    
    # 테스트 파일 패턴
    test_pattern = "test_*.py"
    
    # 모든 테스트 파일 찾기
    all_test_files = glob.glob(os.path.join(test_dir, test_pattern))
    
    # 번호가 붙은 테스트 파일만 필터링
    numbered_test_files = [f for f in all_test_files if os.path.basename(f).startswith("test_0") or os.path.basename(f).startswith("test_1")]
    
    # 파일 이름으로 정렬
    numbered_test_files.sort()
    
    # 테스트 실행 결과
    results = []
    
    # 테스트 ID와 결과를 저장할 딕셔너리
    test_id_results = {}
    
    # 테스트 파일 정보 추출
    test_files_info = {}
    for test_file in numbered_test_files:
        test_files_info[os.path.basename(test_file)] = extract_test_info(test_file)
    
    # 테스트 출력을 캡처하기 위한 함수
    def capture_test_output(test_file):
        # 원래 stdout 저장
        old_stdout = sys.stdout
        # 출력을 캡처하기 위한 StringIO 객체 생성
        captured_output = StringIO()
        sys.stdout = captured_output
        
        test_name = os.path.basename(test_file)
        print(f"\n{'='*80}\n실행 중: {test_name}\n{'='*80}")
        
        # 테스트 로더 생성
        loader = unittest.TestLoader()
        
        # 테스트 파일 경로에서 모듈 이름 추출
        rel_path = os.path.relpath(test_file, current_dir)
        module_name = os.path.splitext(rel_path)[0].replace(os.path.sep, '.')
        
        test_result = {}
        test_ids = []
        
        try:
            # 테스트 모듈 로드
            test_module = __import__(module_name, fromlist=['*'])
            
            # 테스트 스위트 생성
            suite = loader.loadTestsFromModule(test_module)
            
            # 테스트 실행
            runner = unittest.TextTestRunner(verbosity=2)
            result = runner.run(suite)
            
            # 결과 저장
            test_result = {
                'file': test_name,
                'run': result.testsRun,
                'errors': len(result.errors),
                'failures': len(result.failures),
                'skipped': len(result.skipped),
                'success': len(result.errors) == 0 and len(result.failures) == 0
            }
            
        except Exception as e:
            print(f"오류 발생: {e}")
            test_result = {
                'file': test_name,
                'run': 0,
                'errors': 1,
                'failures': 0,
                'skipped': 0,
                'success': False,
                'exception': str(e)
            }
        
        # 출력 복원
        sys.stdout = old_stdout
        
        # 캡처된 출력에서 테스트 ID 추출
        output = captured_output.getvalue()
        test_id_pattern = r"=== 테스트 id ([0-9_]+): ([a-zA-Z0-9_]+) ==="
        matches = re.findall(test_id_pattern, output)
        
        for test_id, test_name in matches:
            test_ids.append({
                'id': test_id,
                'name': test_name,
                'success': test_result['success']
            })
        
        # 원래 출력으로 출력
        print(output)
        
        return test_result, test_ids
    
    # 각 테스트 파일 실행
    for test_file in numbered_test_files:
        test_result, test_ids = capture_test_output(test_file)
        results.append(test_result)
        
        # 테스트 ID와 결과 저장
        for test_id_info in test_ids:
            test_id_results[test_id_info['id']] = {
                'name': test_id_info['name'],
                'file': test_result['file'],
                'success': test_id_info['success']
            }
    
    # 결과 요약 출력
    print(f"\n{'='*80}\n테스트 결과 요약\n{'='*80}")
    print(f"{'파일명':<40} {'실행':<10} {'오류':<10} {'실패':<10} {'건너뜀':<10}")
    print(f"{'-'*80}")
    
    total_run = 0
    total_errors = 0
    total_failures = 0
    total_skipped = 0
    
    for result in results:
        print(f"{result['file']:<40} {result['run']:<10} {result['errors']:<10} {result['failures']:<10} {result.get('skipped', 0):<10}")
        total_run += result['run']
        total_errors += result['errors']
        total_failures += result['failures']
        total_skipped += result.get('skipped', 0)
    
    print(f"{'-'*80}")
    print(f"{'총계':<40} {total_run:<10} {total_errors:<10} {total_failures:<10} {total_skipped:<10}")
    
    # 테스트 결과를 마크다운 파일로 저장
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = f"test_results_summary.md"
    
    with open(result_file, "w", encoding="utf-8") as f:
        f.write("# 테스트 결과 요약\n\n")
        f.write(f"실행 일시: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # 테스트 파일별 요약
        f.write("## 테스트 파일별 요약\n\n")
        f.write("| 파일명 | 실행 | 오류 | 실패 | 건너뜀 | 상태 |\n")
        f.write("|--------|------|------|------|--------|------|\n")
        
        for result in results:
            status = "✅ 성공" if result['errors'] == 0 and result['failures'] == 0 else "❌ 실패"
            f.write(f"| {result['file']} | {result['run']} | {result['errors']} | {result['failures']} | {result.get('skipped', 0)} | {status} |\n")
        
        f.write(f"\n**총계:** {total_run}개 테스트 실행, {total_errors}개 오류, {total_failures}개 실패, {total_skipped}개 건너뜀\n\n")
        
        # 테스트 ID별 상세 결과
        f.write("## 테스트 ID별 상세 결과\n\n")
        f.write("| 테스트 ID | 테스트 이름 | 파일 | 개발 단계 | 테스트 내용 | 상태 |\n")
        f.write("|-----------|------------|------|----------|------------|------|\n")
        
        # 테스트 ID를 정렬하여 출력
        sorted_test_ids = sorted(test_id_results.keys(), key=lambda x: [int(part) if part.isdigit() else part for part in x.split('_')])
        
        for test_id in sorted_test_ids:
            test_info = test_id_results[test_id]
            status = "✅ 성공" if test_info['success'] else "❌ 실패"
            
            # 테스트 파일 정보에서 추가 정보 가져오기
            file_name = test_info['file']
            test_name = test_info['name']
            dev_stage = ""
            test_description = ""
            
            if file_name in test_files_info:
                file_info = test_files_info[file_name]
                
                # 개발 단계 정보
                if 'dev_order' in file_info:
                    dev_stage = file_info['dev_order']
                
                # 테스트 설명 정보
                for method_name, method_info in file_info.items():
                    if isinstance(method_info, dict) and 'id' in method_info and method_info['id'] == test_id:
                        if 'description' in method_info:
                            test_description = method_info['description']
                        break
            
            f.write(f"| {test_id} | {test_name} | {file_name} | {dev_stage} | {test_description} | {status} |\n")
        
        # 테스트 단계별 요약
        f.write("\n## 개발 단계별 테스트 현황\n\n")
        
        # 단계별로 그룹화
        stages = {}
        for test_id in sorted_test_ids:
            stage = test_id.split('_')[0]
            if stage not in stages:
                stages[stage] = {'total': 0, 'success': 0, 'failure': 0}
            
            stages[stage]['total'] += 1
            if test_id_results[test_id]['success']:
                stages[stage]['success'] += 1
            else:
                stages[stage]['failure'] += 1
        
        f.write("| 개발 단계 | 총 테스트 수 | 성공 | 실패 | 성공률 |\n")
        f.write("|-----------|-------------|------|------|--------|\n")
        
        for stage in sorted(stages.keys()):
            total = stages[stage]['total']
            success = stages[stage]['success']
            failure = stages[stage]['failure']
            success_rate = (success / total) * 100 if total > 0 else 0
            
            f.write(f"| {stage} | {total} | {success} | {failure} | {success_rate:.2f}% |\n")
    
    print(f"\n테스트 결과가 {result_file} 파일에 저장되었습니다.")
    
    # 성공 여부 반환
    return total_errors == 0 and total_failures == 0

if __name__ == "__main__":
    success = run_tests_in_order()
    sys.exit(0 if success else 1)