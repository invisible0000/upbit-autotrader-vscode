"""
배포용 디버그 코드 제거 도구
특수 마커를 사용해 배포 시 디버그 관련 코드를 완전히 제거
"""
import os
import re
import shutil
from pathlib import Path
from typing import List, Dict, Tuple

class DeploymentProcessor:
    """배포용 코드 처리기"""
    
    # 디버그 마커 패턴들
    DEBUG_MARKERS = {
        'block': (r'#\s*##DEBUG_START##.*?#\s*##DEBUG_END##', re.DOTALL),
        'line': (r'.*#\s*##DEBUG_LINE##.*', 0),
        'print_debug': (r'^\s*print\(.*[🔍⚠️✅❌ℹ️].*\).*$', re.MULTILINE),
        'console_output': (r'^\s*print\(f?".*\{.*\}".*\).*$', re.MULTILINE)
    }
    
    # 제거할 환경변수 체크 코드
    ENV_DEBUG_PATTERNS = [
        r'if\s+.*getenv\(.*DEBUG.*\).*:',
        r'debug_mode\s*=\s*os\.getenv\(',
        r'\.debug\(',
        r'logging\.DEBUG',
    ]
    
    def __init__(self, source_dir: str, target_dir: str):
        self.source_dir = Path(source_dir)
        self.target_dir = Path(target_dir)
        self.processed_files = []
        self.removed_lines_count = 0
        
    def process_deployment(self, 
                          remove_debug_blocks: bool = True,
                          remove_debug_prints: bool = True,
                          remove_env_checks: bool = True,
                          minimize_logging: bool = True) -> Dict:
        """
        배포용 코드 처리 실행
        
        Args:
            remove_debug_blocks: ##DEBUG_START/END## 블록 제거
            remove_debug_prints: 디버그 print 문 제거  
            remove_env_checks: 환경변수 디버그 체크 제거
            minimize_logging: 로깅 최소화
            
        Returns:
            처리 결과 딕셔너리
        """
        print("🚀 배포용 코드 처리 시작...")
        
        # 타겟 디렉토리 준비
        if self.target_dir.exists():
            shutil.rmtree(self.target_dir)
        shutil.copytree(self.source_dir, self.target_dir)
        
        # Python 파일들 처리
        python_files = list(self.target_dir.rglob("*.py"))
        
        for file_path in python_files:
            if self._should_process_file(file_path):
                original_size = file_path.stat().st_size
                
                # 파일 내용 읽기
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 디버그 코드 제거
                if remove_debug_blocks:
                    content = self._remove_debug_blocks(content)
                
                if remove_debug_prints:
                    content = self._remove_debug_prints(content)
                    
                if remove_env_checks:
                    content = self._remove_env_debug_checks(content)
                    
                if minimize_logging:
                    content = self._minimize_logging(content)
                
                # 빈 줄 정리
                content = self._cleanup_empty_lines(content)
                
                # 파일 쓰기
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                new_size = file_path.stat().st_size
                reduction = original_size - new_size
                
                if reduction > 0:
                    self.processed_files.append({
                        'file': str(file_path.relative_to(self.target_dir)),
                        'size_reduction': reduction,
                        'reduction_percent': (reduction / original_size) * 100
                    })
        
        # 결과 생성
        total_reduction = sum(f['size_reduction'] for f in self.processed_files)
        
        result = {
            'processed_files': len(self.processed_files),
            'total_files': len(python_files),
            'total_size_reduction': total_reduction,
            'removed_lines_estimate': self.removed_lines_count,
            'details': self.processed_files
        }
        
        print(f"✅ 배포 처리 완료: {result['processed_files']}/{result['total_files']} 파일 처리")
        print(f"📊 총 {total_reduction:,} 바이트 감소 (약 {self.removed_lines_count} 줄 제거)")
        
        return result
    
    def _should_process_file(self, file_path: Path) -> bool:
        """처리할 파일인지 확인"""
        # 제외할 파일/디렉토리
        exclude_patterns = [
            '__pycache__',
            '.git',
            'test_',
            'tests/',
            'debug_',
            'deployment_processor.py'  # 자기 자신 제외
        ]
        
        file_str = str(file_path)
        return not any(pattern in file_str for pattern in exclude_patterns)
    
    def _remove_debug_blocks(self, content: str) -> str:
        """##DEBUG_START##...##DEBUG_END## 블록 제거"""
        pattern, flags = self.DEBUG_MARKERS['block']
        
        def count_removals(match):
            self.removed_lines_count += match.group(0).count('\n')
            return ''
        
        return re.sub(pattern, count_removals, content, flags=flags)
    
    def _remove_debug_prints(self, content: str) -> str:
        """디버그 관련 print 문 제거"""
        # 이모지가 포함된 print 문 제거
        pattern = r'^\s*print\(.*[🔍⚠️✅❌ℹ️💡🎯🚀📊🔧].*\).*$'
        
        lines = content.split('\n')
        filtered_lines = []
        
        for line in lines:
            if re.match(pattern, line):
                self.removed_lines_count += 1
                # 디버그 print 라인을 주석으로 대체 (완전 제거 대신)
                filtered_lines.append(f"# [REMOVED DEBUG] {line.strip()}")
            else:
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)
    
    def _remove_env_debug_checks(self, content: str) -> str:
        """환경변수 디버그 체크 제거"""
        for pattern in self.ENV_DEBUG_PATTERNS:
            # 간단한 디버그 체크는 True로 대체
            if 'getenv' in pattern and 'DEBUG' in pattern:
                content = re.sub(
                    r'os\.getenv\([^)]*DEBUG[^)]*\)\.lower\(\)\s*==\s*[\'"]true[\'"]',
                    'False',  # 프로덕션에서는 False로 고정
                    content,
                    flags=re.IGNORECASE
                )
        
        return content
    
    def _minimize_logging(self, content: str) -> str:
        """로깅 최소화"""
        # DEBUG 레벨을 WARNING으로 변경
        content = re.sub(r'logging\.DEBUG', 'logging.WARNING', content)
        content = re.sub(r'\.debug\(', '.warning(', content)
        
        # 개발용 상세 로그 메시지 단순화
        content = re.sub(
            r'logger\.info\(f".*\{.*\}.*"\)',
            'logger.info("Operation completed")',
            content
        )
        
        return content
    
    def _cleanup_empty_lines(self, content: str) -> str:
        """연속된 빈 줄 정리"""
        # 3개 이상의 연속 빈 줄을 2개로 축소
        content = re.sub(r'\n\s*\n\s*\n\s*\n+', '\n\n\n', content)
        return content
    
    def create_production_config(self):
        """프로덕션 환경변수 설정 파일 생성"""
        production_env = """# 프로덕션 환경 설정
UPBIT_ENV=production
UPBIT_DEBUG_MODE=false
UPBIT_LOG_LEVEL=WARNING
PYTHONOPTIMIZE=1
"""
        
        env_file = self.target_dir / '.env.production'
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(production_env)
        
        print(f"📝 프로덕션 설정 파일 생성: {env_file}")


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='배포용 디버그 코드 제거 도구')
    parser.add_argument('--source', default='.', help='소스 디렉토리')
    parser.add_argument('--target', default='./dist', help='배포용 타겟 디렉토리')
    parser.add_argument('--keep-debug-comments', action='store_true', 
                       help='디버그 코드를 주석으로 보존')
    
    args = parser.parse_args()
    
    processor = DeploymentProcessor(args.source, args.target)
    result = processor.process_deployment()
    processor.create_production_config()
    
    print("\n📋 배포 처리 결과:")
    print(f"  - 처리된 파일: {result['processed_files']}")
    print(f"  - 코드 크기 감소: {result['total_size_reduction']:,} 바이트")
    print(f"  - 예상 제거 라인: {result['removed_lines_estimate']}")


if __name__ == "__main__":
    main()
