#!/usr/bin/env python3
"""
🔄 Super DB YAML Simple Diff Tool
DB와 YAML 파일 간 차이점 분석 및 누락 데이터 확인

📋 **주요 기능**:
- DB에서 추출된 YAML과 기존 YAML 파일 비교
- 누락된 변수나 파라미터 식별
- 간단한 병합 및 업데이트 기능
- 현재 워크플로우에 최적화

🎯 **사용법**:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📖 1. **DB와 YAML 비교**:
   python tools/super_db_yaml_simple_diff.py --compare tv_variable_parameters

📖 2. **누락된 데이터 확인**:
   python tools/super_db_yaml_simple_diff.py --check-missing tv_variable_parameters

📖 3. **누락된 데이터 자동 병합**:
   python tools/super_db_yaml_simple_diff.py --auto-merge tv_variable_parameters

📖 4. **백업에서 현재 YAML로 업데이트**:
   python tools/super_db_yaml_simple_diff.py --update-from-backup tv_variable_parameters_backup_20250802_101223.yaml

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import sys
import yaml
import logging
import argparse
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Set, List

# 프로젝트 루트를 파이썬 패스에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 로그 디렉토리 생성
log_dir = PROJECT_ROOT / "logs"
log_dir.mkdir(exist_ok=True)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_dir / 'super_db_yaml_simple_diff.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class SuperDBYAMLSimpleDiff:
    """DB YAML 간단 비교 및 차이점 분석 도구"""
    
    def __init__(self):
        """초기화"""
        self.project_root = PROJECT_ROOT
        data_info_base = self.project_root / "upbit_auto_trading" / "utils"
        self.data_info_path = (
            data_info_base / "trading_variables" / 
            "gui_variables_DB_migration_util" / "data_info"
        )
        
        logger.info("🔄 Super DB YAML Simple Diff 초기화")
        logger.info(f"📂 Data Info Path: {self.data_info_path}")
    
    def load_yaml_safely(self, file_path: Path) -> Dict[str, Any]:
        """YAML 파일을 안전하게 로드 (주석 무시)"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 주석 라인 제거하고 YAML 데이터만 추출
            lines = content.split('\n')
            yaml_lines = []
            
            for line in lines:
                stripped = line.strip()
                if not stripped.startswith('#'):
                    yaml_lines.append(line)
            
            yaml_content = '\n'.join(yaml_lines)
            return yaml.safe_load(yaml_content) or {}
            
        except Exception as e:
            logger.error(f"❌ YAML 파일 로드 실패 ({file_path}): {e}")
            return {}
    
    def compare_variable_parameters(self, table_name: str) -> Dict[str, Any]:
        """변수 파라미터 비교 분석"""
        
        # 현재 YAML 파일
        current_yaml = self.data_info_path / f"{table_name}.yaml"
        
        # 최근 백업 파일 찾기
        backup_files = list(self.data_info_path.glob(f"{table_name}_backup_*.yaml"))
        if not backup_files:
            logger.error(f"❌ {table_name}의 백업 파일을 찾을 수 없습니다")
            return {}
        
        # 가장 최근 백업 파일
        latest_backup = max(backup_files, key=lambda p: p.stat().st_mtime)
        
        logger.info(f"📊 비교 분석 시작")
        logger.info(f"  • 현재 YAML: {current_yaml.name}")
        logger.info(f"  • DB 백업: {latest_backup.name}")
        
        # YAML 데이터 로드
        current_data = self.load_yaml_safely(current_yaml)
        backup_data = self.load_yaml_safely(latest_backup)
        
        # 비교 결과
        comparison = {
            'current_file': str(current_yaml),
            'backup_file': str(latest_backup),
            'analysis_time': datetime.now().isoformat(),
            'current_variables': set(),
            'backup_variables': set(),
            'missing_in_current': set(),
            'missing_in_backup': set(),
            'current_parameters': {},
            'backup_parameters': {},
            'missing_parameters': {},
            'recommendations': []
        }
        
        # 변수 목록 추출
        if 'variable_parameters' in current_data and current_data['variable_parameters']:
            for param_key, param_data in current_data['variable_parameters'].items():
                if isinstance(param_data, dict) and 'variable_id' in param_data:
                    var_id = param_data['variable_id']
                    comparison['current_variables'].add(var_id)
                    if var_id not in comparison['current_parameters']:
                        comparison['current_parameters'][var_id] = []
                    comparison['current_parameters'][var_id].append(param_key)
        
        if 'variable_parameters' in backup_data and backup_data['variable_parameters']:
            for param_key, param_data in backup_data['variable_parameters'].items():
                if isinstance(param_data, dict) and 'variable_id' in param_data:
                    var_id = param_data['variable_id']
                    comparison['backup_variables'].add(var_id)
                    if var_id not in comparison['backup_parameters']:
                        comparison['backup_parameters'][var_id] = []
                    comparison['backup_parameters'][var_id].append(param_key)
        
        # 차이점 분석
        comparison['missing_in_current'] = comparison['backup_variables'] - comparison['current_variables']
        comparison['missing_in_backup'] = comparison['current_variables'] - comparison['backup_variables']
        
        # 파라미터 레벨 차이점
        for var_id in comparison['backup_variables']:
            if var_id in comparison['current_parameters']:
                current_params = set(comparison['current_parameters'][var_id])
                backup_params = set(comparison['backup_parameters'][var_id])
                missing_params = backup_params - current_params
                if missing_params:
                    comparison['missing_parameters'][var_id] = list(missing_params)
        
        # 권장사항 생성
        if comparison['missing_in_current']:
            comparison['recommendations'].append(
                f"현재 YAML에 누락된 변수 {len(comparison['missing_in_current'])}개를 추가하세요"
            )
        
        if comparison['missing_parameters']:
            total_missing = sum(len(params) for params in comparison['missing_parameters'].values())
            comparison['recommendations'].append(
                f"누락된 파라미터 {total_missing}개를 추가하세요"
            )
        
        # 결과 출력
        self._print_comparison_report(comparison)
        
        return comparison
    
    def _print_comparison_report(self, comparison: Dict[str, Any]) -> None:
        """비교 결과 리포트 출력"""
        print("\n" + "=" * 80)
        print("🔍 DB YAML 비교 분석 보고서")
        print("=" * 80)
        
        print(f"📅 분석 시점: {comparison['analysis_time']}")
        print(f"📄 현재 YAML: {Path(comparison['current_file']).name}")
        print(f"💾 DB 백업: {Path(comparison['backup_file']).name}")
        
        print("\n📊 변수 비교:")
        print(f"  • 현재 YAML 변수: {len(comparison['current_variables'])}개")
        print(f"  • DB 백업 변수: {len(comparison['backup_variables'])}개")
        
        if comparison['missing_in_current']:
            print(f"\n❌ 현재 YAML에 누락된 변수 ({len(comparison['missing_in_current'])}개):")
            for var_id in sorted(comparison['missing_in_current']):
                param_count = len(comparison['backup_parameters'].get(var_id, []))
                print(f"  • {var_id} ({param_count}개 파라미터)")
        
        if comparison['missing_in_backup']:
            print(f"\n➕ DB에 없는 변수 ({len(comparison['missing_in_backup'])}개):")
            for var_id in sorted(comparison['missing_in_backup']):
                print(f"  • {var_id}")
        
        if comparison['missing_parameters']:
            print(f"\n🔧 누락된 파라미터:")
            for var_id, missing_params in comparison['missing_parameters'].items():
                print(f"  • {var_id}: {len(missing_params)}개 - {missing_params}")
        
        if comparison['recommendations']:
            print(f"\n💡 권장사항:")
            for rec in comparison['recommendations']:
                print(f"  • {rec}")
        
        print("\n" + "=" * 80)
        
        if not comparison['missing_in_current'] and not comparison['missing_parameters']:
            print("✅ 현재 YAML이 DB와 일치합니다!")
        else:
            print("⚠️ 차이점이 발견되었습니다. --auto-merge로 자동 병합할 수 있습니다.")
        
        print("=" * 80)
    
    def auto_merge_missing_data(self, table_name: str) -> bool:
        """누락된 데이터 자동 병합"""
        try:
            logger.info(f"🔄 {table_name} 자동 병합 시작")
            
            # 비교 분석 실행
            comparison = self.compare_variable_parameters(table_name)
            
            if not comparison['missing_in_current'] and not comparison['missing_parameters']:
                logger.info("📝 병합할 데이터가 없습니다")
                return True
            
            # 현재 YAML과 백업 YAML 로드
            current_yaml = Path(comparison['current_file'])
            backup_yaml = Path(comparison['backup_file'])
            
            current_data = self.load_yaml_safely(current_yaml)
            backup_data = self.load_yaml_safely(backup_yaml)
            
            # 누락된 변수/파라미터 추가
            if 'variable_parameters' not in current_data:
                current_data['variable_parameters'] = {}
            
            merged_count = 0
            
            # 누락된 변수의 모든 파라미터 추가
            for var_id in comparison['missing_in_current']:
                if var_id in comparison['backup_parameters']:
                    for param_key in comparison['backup_parameters'][var_id]:
                        if param_key in backup_data['variable_parameters']:
                            current_data['variable_parameters'][param_key] = backup_data['variable_parameters'][param_key]
                            merged_count += 1
            
            # 누락된 파라미터 추가
            for var_id, missing_params in comparison['missing_parameters'].items():
                for param_key in missing_params:
                    if param_key in backup_data['variable_parameters']:
                        current_data['variable_parameters'][param_key] = backup_data['variable_parameters'][param_key]
                        merged_count += 1
            
            if merged_count > 0:
                # 백업 생성
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"{table_name}_backup_before_merge_{timestamp}.yaml"
                backup_path = self.data_info_path / "_BACKUPS_" / backup_name
                backup_path.parent.mkdir(exist_ok=True)
                shutil.copy2(current_yaml, backup_path)
                
                # 병합된 내용으로 현재 YAML 업데이트
                self._save_yaml_with_metadata(current_data, current_yaml, "Auto-merged missing data")
                
                logger.info(f"✅ 자동 병합 완료: {merged_count}개 항목 추가")
                logger.info(f"📦 원본 백업: {backup_name}")
                
                print(f"\n🎉 자동 병합 성공!")
                print(f"  • 병합된 항목: {merged_count}개")
                print(f"  • 원본 백업: {backup_name}")
                print(f"  • 업데이트된 파일: {current_yaml.name}")
                
                return True
            else:
                logger.info("📝 병합할 새로운 데이터가 없습니다")
                return True
                
        except Exception as e:
            logger.error(f"❌ 자동 병합 실패: {e}")
            return False
    
    def _save_yaml_with_metadata(self, data: Dict[str, Any], target_file: Path, operation: str) -> None:
        """메타데이터와 함께 YAML 저장"""
        try:
            # 메타데이터 주석 생성
            metadata_comment = f"""# ════════════════════════════════════════════════════════════════
# 🔄 Super DB YAML Simple Diff - {operation}
# ════════════════════════════════════════════════════════════════
# 처리 시점: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# 처리 도구: super_db_yaml_simple_diff.py
# 작업 내용: {operation}
# ────────────────────────────────────────────────────────────────
# 📝 이 파일은 DB 백업 데이터와 병합되었습니다
# ════════════════════════════════════════════════════════════════

"""
            
            # YAML 데이터를 문자열로 변환
            yaml_content = yaml.dump(data, allow_unicode=True, indent=2, sort_keys=False)
            
            # 메타데이터 + 데이터 결합하여 저장
            with open(target_file, 'w', encoding='utf-8') as f:
                f.write(metadata_comment + yaml_content)
            
            logger.info(f"✅ YAML 저장 완료: {target_file.name}")
            
        except Exception as e:
            logger.error(f"❌ YAML 저장 실패: {e}")
            raise
    
    def update_from_backup(self, backup_file: str) -> bool:
        """지정된 백업 파일로 현재 YAML 업데이트"""
        try:
            backup_path = Path(backup_file)
            if not backup_path.exists():
                backup_path = self.data_info_path / backup_file
                if not backup_path.exists():
                    raise FileNotFoundError(f"백업 파일을 찾을 수 없습니다: {backup_file}")
            
            # 테이블명 추출
            table_name = self._extract_table_name_from_backup(backup_path)
            target_yaml = self.data_info_path / f"{table_name}.yaml"
            
            logger.info(f"🔄 백업에서 업데이트: {backup_path.name} → {target_yaml.name}")
            
            # 백업 데이터 로드
            backup_data = self.load_yaml_safely(backup_path)
            
            if not backup_data:
                raise ValueError("백업 파일에 유효한 데이터가 없습니다")
            
            # 현재 파일 백업
            if target_yaml.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"{table_name}_backup_before_update_{timestamp}.yaml"
                backup_target = self.data_info_path / "_BACKUPS_" / backup_name
                backup_target.parent.mkdir(exist_ok=True)
                shutil.copy2(target_yaml, backup_target)
                logger.info(f"📦 현재 파일 백업: {backup_name}")
            
            # 백업 데이터로 업데이트
            self._save_yaml_with_metadata(backup_data, target_yaml, f"Updated from {backup_path.name}")
            
            logger.info(f"✅ 백업에서 업데이트 완료")
            
            print(f"\n🎉 백업에서 업데이트 성공!")
            print(f"  • 소스: {backup_path.name}")
            print(f"  • 대상: {target_yaml.name}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 백업에서 업데이트 실패: {e}")
            return False
    
    def _extract_table_name_from_backup(self, backup_path: Path) -> str:
        """백업 파일명에서 테이블명 추출"""
        stem = backup_path.stem
        
        if '_backup_' in stem:
            return stem.split('_backup_')[0]
        elif '_EDIT_' in stem:
            return stem.split('_EDIT_')[0]
        else:
            return stem


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description="🔄 Super DB YAML Simple Diff - DB와 YAML 간 차이점 분석",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # DB와 YAML 비교
  python tools/super_db_yaml_simple_diff.py --compare tv_variable_parameters
  
  # 누락된 데이터 확인
  python tools/super_db_yaml_simple_diff.py --check-missing tv_variable_parameters
  
  # 자동 병합
  python tools/super_db_yaml_simple_diff.py --auto-merge tv_variable_parameters
  
  # 백업에서 업데이트
  python tools/super_db_yaml_simple_diff.py --update-from-backup tv_variable_parameters_backup_20250802_101223.yaml
        """
    )
    
    parser.add_argument('--compare',
                       help='DB 백업과 현재 YAML 파일 비교')
    
    parser.add_argument('--check-missing',
                       help='누락된 데이터 확인 (--compare와 동일)')
    
    parser.add_argument('--auto-merge',
                       help='누락된 데이터 자동 병합')
    
    parser.add_argument('--update-from-backup',
                       help='지정된 백업 파일로 현재 YAML 업데이트')
    
    args = parser.parse_args()
    
    tool = SuperDBYAMLSimpleDiff()
    
    try:
        if args.compare or args.check_missing:
            table_name = args.compare or args.check_missing
            comparison = tool.compare_variable_parameters(table_name)
            return 0 if comparison else 1
            
        elif args.auto_merge:
            success = tool.auto_merge_missing_data(args.auto_merge)
            return 0 if success else 1
            
        elif args.update_from_backup:
            success = tool.update_from_backup(args.update_from_backup)
            return 0 if success else 1
            
        else:
            parser.print_help()
            return 1
            
    except Exception as e:
        logger.error(f"❌ 예상치 못한 오류: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
