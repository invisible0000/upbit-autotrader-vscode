"""
테스트 보고서 생성기 모듈

이 모듈은 업비트 자동매매 시스템의 GUI 자동화 테스트 결과를 보고서로 생성합니다.
"""

import os
import json
from datetime import datetime


class TestReportGenerator:
    """테스트 보고서 생성기 클래스"""
    
    def __init__(self, report_dir="test_reports"):
        """
        초기화
        
        Args:
            report_dir (str): 보고서 저장 디렉토리
        """
        self.report_dir = os.path.join("sample_QA_Automation", report_dir)
        os.makedirs(self.report_dir, exist_ok=True)
    
    def generate_markdown_report(self, result, execution_time):
        """
        마크다운 보고서 생성
        
        Args:
            result (unittest.TestResult): 테스트 결과
            execution_time (float): 테스트 실행 시간 (초)
        
        Returns:
            str: 생성된 보고서 경로
        """
        # 보고서 파일 이름 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(self.report_dir, f"test_report_{timestamp}.md")
        
        # 보고서 작성
        with open(report_file, "w") as f:
            f.write("# GUI 자동화 테스트 보고서\n\n")
            f.write(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## 테스트 요약\n")
            f.write(f"- 총 테스트 케이스: {result.testsRun}\n")
            f.write(f"- 성공: {result.testsRun - len(result.failures) - len(result.errors)}\n")
            f.write(f"- 실패: {len(result.failures)}\n")
            f.write(f"- 오류: {len(result.errors)}\n")
            f.write(f"- 테스트 실행 시간: {execution_time:.2f}초\n\n")
            
            if result.failures:
                f.write("## 실패한 테스트 케이스\n")
                for i, (test, error) in enumerate(result.failures, 1):
                    f.write(f"### {i}. {test}\n")
                    f.write("```\n")
                    f.write(error)
                    f.write("\n```\n\n")
            
            if result.errors:
                f.write("## 오류가 발생한 테스트 케이스\n")
                for i, (test, error) in enumerate(result.errors, 1):
                    f.write(f"### {i}. {test}\n")
                    f.write("```\n")
                    f.write(error)
                    f.write("\n```\n\n")
        
        print(f"마크다운 보고서가 생성되었습니다: {report_file}")
        return report_file
    
    def generate_json_report(self, result, execution_time):
        """
        JSON 보고서 생성
        
        Args:
            result (unittest.TestResult): 테스트 결과
            execution_time (float): 테스트 실행 시간 (초)
        
        Returns:
            str: 생성된 보고서 경로
        """
        # 보고서 파일 이름 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(self.report_dir, f"test_report_{timestamp}.json")
        
        # 보고서 데이터 생성
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": result.testsRun,
                "success": result.testsRun - len(result.failures) - len(result.errors),
                "failures": len(result.failures),
                "errors": len(result.errors),
                "execution_time": execution_time
            },
            "failures": [
                {
                    "test": str(test),
                    "error": error
                }
                for test, error in result.failures
            ],
            "errors": [
                {
                    "test": str(test),
                    "error": error
                }
                for test, error in result.errors
            ]
        }
        
        # 보고서 저장
        with open(report_file, "w") as f:
            json.dump(report_data, f, indent=4)
        
        print(f"JSON 보고서가 생성되었습니다: {report_file}")
        return report_file
    
    def generate_html_report(self, result, execution_time):
        """
        HTML 보고서 생성
        
        Args:
            result (unittest.TestResult): 테스트 결과
            execution_time (float): 테스트 실행 시간 (초)
        
        Returns:
            str: 생성된 보고서 경로
        """
        # 보고서 파일 이름 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(self.report_dir, f"test_report_{timestamp}.html")
        
        # 성공률 계산
        success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100 if result.testsRun > 0 else 0
        
        # 보고서 작성
        with open(report_file, "w") as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GUI 자동화 테스트 보고서</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            color: #333;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #2980b9;
            margin-top: 30px;
        }}
        h3 {{
            color: #3498db;
        }}
        .summary {{
            background-color: #f8f9fa;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 20px;
        }}
        .success {{
            color: #27ae60;
        }}
        .failure {{
            color: #e74c3c;
        }}
        .error {{
            color: #c0392b;
        }}
        .progress-bar {{
            background-color: #ecf0f1;
            border-radius: 5px;
            height: 20px;
            margin-bottom: 20px;
        }}
        .progress {{
            background-color: #2ecc71;
            border-radius: 5px;
            height: 20px;
            width: {success_rate}%;
        }}
        pre {{
            background-color: #f8f9fa;
            border-left: 4px solid #3498db;
            padding: 10px;
            overflow-x: auto;
        }}
    </style>
</head>
<body>
    <h1>GUI 자동화 테스트 보고서</h1>
    <p>실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <h2>테스트 요약</h2>
    <div class="summary">
        <p>총 테스트 케이스: <strong>{result.testsRun}</strong></p>
        <p>성공: <strong class="success">{result.testsRun - len(result.failures) - len(result.errors)}</strong></p>
        <p>실패: <strong class="failure">{len(result.failures)}</strong></p>
        <p>오류: <strong class="error">{len(result.errors)}</strong></p>
        <p>테스트 실행 시간: <strong>{execution_time:.2f}초</strong></p>
        <p>성공률: <strong>{success_rate:.2f}%</strong></p>
        <div class="progress-bar">
            <div class="progress"></div>
        </div>
    </div>
""")
            
            if result.failures:
                f.write("""    <h2>실패한 테스트 케이스</h2>
""")
                for i, (test, error) in enumerate(result.failures, 1):
                    f.write(f"""    <h3>{i}. {test}</h3>
    <pre>{error}</pre>
""")
            
            if result.errors:
                f.write("""    <h2>오류가 발생한 테스트 케이스</h2>
""")
                for i, (test, error) in enumerate(result.errors, 1):
                    f.write(f"""    <h3>{i}. {test}</h3>
    <pre>{error}</pre>
""")
            
            f.write("""</body>
</html>
""")
        
        print(f"HTML 보고서가 생성되었습니다: {report_file}")
        return report_file