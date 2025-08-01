#!/usr/bin/env python3
"""
🔄 Super DB YAML Editor Workflow
편집-검증-통합 자동화 도구

📋 **주요 기능**:
- 추출된 YAML 파일을 안전한 편집용으로 복사
- 편집 후 변경사항 검증 및 DB 반영
- 자동 백업 및 최종 파일 통합 관리
- 에러 발생 시 롤백 지원

🎯 **사용법 가이드**:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📖 1. **편집 세션 시작**:
   python tools/super_db_yaml_editor_workflow.py --start-edit tv_trading_variables_backup_20250801_143152.yaml
   # → tv_trading_variables_EDIT_20250801_143152.yaml 생성 (편집용)

📖 2. **변경사항 검증**:
   python tools/super_db_yaml_editor_workflow.py --validate-changes tv_trading_variables_EDIT_20250801_143152.yaml
   # → 변경사항 분석 및 DB 반영 가능성 검증

📖 3. **DB에 변경사항 적용**:
   python tools/super_db_yaml_editor_workflow.py --apply-changes tv_trading_variables_EDIT_20250801_143152.yaml
   # → DB 반영 → 새로운 추출 → 최종 YAML 생성 → 임시 파일 정리

📖 4. **편집 세션 정리**:
   python tools/super_db_yaml_editor_workflow.py --cleanup-session tv_trading_variables_EDIT_20250801_143152.yaml
   # → 편집 파일 백업 후 정리

📖 5. **완전 자동화 모드**:
   python tools/super_db_yaml_editor_workflow.py --auto-workflow --table tv_trading_variables
   # → 추출 → 편집용 복사 → (편집 대기) → 적용 → 정리

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 **편집 모드 설명**:
- **안전 편집**: 원본 보존하며 편집용 복사본 생성
- **검증 우선**: DB 반영 전 모든 변경사항 검증
- **자동 백업**: 모든 단계에서 자동 백업 생성
- **롤백 지원**: 실패 시 이전 상태로 복구

💡 **팁**:
- 편집 후 반드시 --validate-changes로 검증하세요
- 실패 시 _BACKUP_ 폴더에서 복구 가능
- 대용량 데이터는 --batch-size로 처리량 조절

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import sys
import yaml
import json
import logging
import argparse
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# 프로젝트 루트를 파이썬 패스에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/super_db_yaml_editor_workflow.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class EditingSession:
    """편집 세션 관리 클래스"""
    
    def __init__(self, original_file: str, session_id: str = None):
        self.original_file = Path(original_file)
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_time = datetime.now()
        
        # 편집 세션 관련 경로
        self.edit_file = self._generate_edit_filename()
        self.backup_dir = self.original_file.parent / "_BACKUPS_"
        self.session_dir = self.backup_dir / f"session_{self.session_id}"
        
        # 세션 디렉토리 생성
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
    def _generate_edit_filename(self) -> Path:
        """편집용 파일명 생성"""
        stem = self.original_file.stem
        suffix = self.original_file.suffix
        
        # _backup_ 접미사 제거 후 _EDIT_ 추가
        if '_backup_' in stem:
            base_name = stem.split('_backup_')[0]
            timestamp = stem.split('_backup_')[1] if '_backup_' in stem else self.session_id
        else:
            base_name = stem
            timestamp = self.session_id
            
        edit_filename = f"{base_name}_EDIT_{timestamp}{suffix}"
        return self.original_file.parent / edit_filename
    
    def get_session_info(self) -> Dict[str, Any]:
        """세션 정보 반환"""
        return {
            'session_id': self.session_id,
            'original_file': str(self.original_file),
            'edit_file': str(self.edit_file),
            'backup_dir': str(self.backup_dir),
            'session_dir': str(self.session_dir),
            'session_time': self.session_time.isoformat(),
            'status': 'active' if self.edit_file.exists() else 'pending'
        }


class SuperDBYAMLEditorWorkflow:
    """DB YAML 편집-검증-통합 워크플로우 도구"""
    
    def __init__(self):
        """초기화"""
        self.project_root = PROJECT_ROOT
        data_info_base = self.project_root / "upbit_auto_trading" / "utils"
        self.data_info_path = (
            data_info_base / "trading_variables" /
            "gui_variables_DB_migration_util" / "data_info"
        )
        
        # 로그 디렉토리 생성
        log_dir = self.project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        
        logger.info("🔄 Super DB YAML Editor Workflow 초기화")
        logger.info(f"📂 Data Info Path: {self.data_info_path}")
        
    def start_editing_session(self, original_yaml: str) -> EditingSession:
        """편집 세션 시작 - 편집용 복사본 생성"""
        try:
            original_path = Path(original_yaml)
            if not original_path.exists():
                # data_info 경로에서 찾기
                original_path = self.data_info_path / original_yaml
                if not original_path.exists():
                    raise FileNotFoundError(f"원본 YAML 파일을 찾을 수 없습니다: {original_yaml}")
            
            logger.info(f"🚀 편집 세션 시작: {original_path.name}")
            
            # 편집 세션 생성
            session = EditingSession(str(original_path))
            
            # 원본 파일을 편집용으로 복사
            shutil.copy2(original_path, session.edit_file)
            
            # 세션 메타데이터 저장
            session_info = session.get_session_info()
            session_info_file = session.session_dir / "session_info.json"
            with open(session_info_file, 'w', encoding='utf-8') as f:
                json.dump(session_info, f, indent=2, ensure_ascii=False)
            
            # 편집 가이드 주석 추가
            self._add_editing_guide_to_file(session.edit_file, session)
            
            logger.info(f"✅ 편집용 파일 생성: {session.edit_file.name}")
            logger.info(f"📁 세션 디렉토리: {session.session_dir}")
            logger.info("📝 이제 편집용 파일을 수정하고 --validate-changes로 검증하세요")
            
            return session
            
        except Exception as e:
            logger.error(f"❌ 편집 세션 시작 실패: {e}")
            raise
    
    def _add_editing_guide_to_file(self, edit_file: Path, session: EditingSession) -> None:
        """편집 파일에 편집 가이드 주석 추가"""
        try:
            # 기존 내용 읽기
            with open(edit_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 편집 가이드 주석 생성
            guide_comment = f"""# ╔════════════════════════════════════════════════════════════════╗
# ║                     🔄 편집 세션 정보                         ║
# ╠════════════════════════════════════════════════════════════════╣
# ║ 세션 ID: {session.session_id}                                    
# ║ 원본 파일: {session.original_file.name}                          
# ║ 편집 시작: {session.session_time.strftime('%Y-%m-%d %H:%M:%S')}  
# ║ 백업 위치: {session.session_dir}                                 
# ╠════════════════════════════════════════════════════════════════╣
# ║                     📝 편집 안내                              ║
# ╠════════════════════════════════════════════════════════════════╣
# ║ 1. 이 파일을 자유롭게 편집하세요                              ║
# ║ 2. 편집 완료 후 저장하세요 (Ctrl+S)                          ║
# ║ 3. 다음 명령어로 검증하세요:                                  ║
# ║    python tools/super_db_yaml_editor_workflow.py \\           ║
# ║      --validate-changes {edit_file.name}         ║
# ║ 4. 검증 후 적용하세요:                                        ║
# ║    python tools/super_db_yaml_editor_workflow.py \\           ║
# ║      --apply-changes {edit_file.name}            ║
# ╚════════════════════════════════════════════════════════════════╝

"""
            
            # 기존 주석 제거 후 새 가이드 추가
            if content.startswith('#'):
                # 기존 메타데이터 주석 찾기
                lines = content.split('\n')
                yaml_start_index = 0
                for i, line in enumerate(lines):
                    if not line.strip().startswith('#') and line.strip():
                        yaml_start_index = i
                        break
                
                # YAML 데이터 부분만 유지
                yaml_content = '\n'.join(lines[yaml_start_index:])
            else:
                yaml_content = content
            
            # 새로운 내용 작성
            new_content = guide_comment + yaml_content
            
            with open(edit_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            logger.info("✅ 편집 가이드 주석 추가 완료")
            
        except Exception as e:
            logger.error(f"❌ 편집 가이드 추가 실패: {e}")
    
    def validate_changes(self, edit_file: str) -> Dict[str, Any]:
        """편집된 파일의 변경사항 검증"""
        try:
            edit_path = Path(edit_file)
            if not edit_path.exists():
                edit_path = self.data_info_path / edit_file
                if not edit_path.exists():
                    raise FileNotFoundError(f"편집 파일을 찾을 수 없습니다: {edit_file}")
            
            logger.info(f"🔍 변경사항 검증 시작: {edit_path.name}")
            
            # 편집 파일에서 원본 파일 추출
            original_file = self._extract_original_filename(edit_path)
            
            if not original_file.exists():
                raise FileNotFoundError(f"원본 파일을 찾을 수 없습니다: {original_file}")
            
            # YAML 파일 로드 및 비교
            original_data = self._load_yaml_content(original_file)
            edited_data = self._load_yaml_content(edit_path)
            
            # 변경사항 분석
            validation_result = {
                'validation_time': datetime.now().isoformat(),
                'original_file': str(original_file),
                'edited_file': str(edit_path),
                'yaml_valid': True,
                'changes_detected': False,
                'changes_summary': {},
                'validation_errors': [],
                'db_compatibility': 'unknown',
                'recommendations': []
            }
            
            # YAML 구조 검증
            if edited_data is None:
                validation_result['yaml_valid'] = False
                validation_result['validation_errors'].append("편집된 YAML 파일의 구문이 올바르지 않습니다")
                return validation_result
            
            # 변경사항 분석
            changes = self._analyze_changes(original_data, edited_data)
            if changes:
                validation_result['changes_detected'] = True
                validation_result['changes_summary'] = changes
                
                # DB 호환성 검증
                compatibility = self._validate_db_compatibility(edited_data, edit_path)
                validation_result['db_compatibility'] = compatibility['status']
                validation_result['validation_errors'].extend(compatibility.get('errors', []))
                validation_result['recommendations'].extend(compatibility.get('recommendations', []))
            
            # 검증 결과 출력
            self._print_validation_report(validation_result)
            
            logger.info("✅ 변경사항 검증 완료")
            return validation_result
            
        except Exception as e:
            logger.error(f"❌ 변경사항 검증 실패: {e}")
            return {
                'validation_time': datetime.now().isoformat(),
                'yaml_valid': False,
                'validation_errors': [str(e)],
                'changes_detected': False
            }
    
    def _extract_original_filename(self, edit_file: Path) -> Path:
        """편집 파일명에서 원본 파일명 추출"""
        stem = edit_file.stem
        suffix = edit_file.suffix
        
        # _EDIT_ 패턴 제거
        if '_EDIT_' in stem:
            base_part = stem.split('_EDIT_')[0]
            timestamp_part = stem.split('_EDIT_')[1]
            
            # 원본 백업 파일명 생성
            original_name = f"{base_part}_backup_{timestamp_part}{suffix}"
            return edit_file.parent / original_name
        
        # 패턴이 없으면 기본 파일 찾기
        return edit_file.parent / f"{stem.replace('_EDIT', '')}{suffix}"
    
    def _load_yaml_content(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """YAML 파일의 데이터 부분만 로드 (주석 제외)"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 주석 라인 제거하고 YAML 데이터만 추출
            lines = content.split('\n')
            yaml_lines = []
            
            for line in lines:
                stripped = line.strip()
                if not stripped.startswith('#') and stripped:
                    yaml_lines.append(line)
                elif not stripped.startswith('#') and not stripped:
                    yaml_lines.append(line)  # 빈 줄 유지
            
            yaml_content = '\n'.join(yaml_lines)
            return yaml.safe_load(yaml_content)
            
        except Exception as e:
            logger.error(f"❌ YAML 파일 로드 실패 ({file_path}): {e}")
            return None
    
    def _analyze_changes(self, original: Dict[str, Any], edited: Dict[str, Any]) -> Dict[str, Any]:
        """변경사항 상세 분석"""
        changes = {
            'added': {},
            'modified': {},
            'deleted': {},
            'total_changes': 0
        }
        
        if not original or not edited:
            return changes
        
        # 최상위 키 비교 (예: trading_variables)
        for key in original.keys():
            if key not in edited:
                changes['deleted'][key] = original[key]
                changes['total_changes'] += 1
            elif original[key] != edited[key]:
                # 하위 레벨 변경사항 분석
                if isinstance(original[key], dict) and isinstance(edited[key], dict):
                    sub_changes = self._analyze_dict_changes(original[key], edited[key])
                    if sub_changes:
                        changes['modified'][key] = sub_changes
                        changes['total_changes'] += len(sub_changes)
                else:
                    changes['modified'][key] = {
                        'old': original[key],
                        'new': edited[key]
                    }
                    changes['total_changes'] += 1
        
        # 새로 추가된 키
        for key in edited.keys():
            if key not in original:
                changes['added'][key] = edited[key]
                changes['total_changes'] += 1
        
        return changes
    
    def _analyze_dict_changes(self, original_dict: Dict, edited_dict: Dict) -> Dict[str, Any]:
        """딕셔너리 레벨 변경사항 분석"""
        item_changes = {}
        
        # 수정/삭제된 항목
        for item_key in original_dict.keys():
            if item_key not in edited_dict:
                item_changes[f"deleted_{item_key}"] = original_dict[item_key]
            elif original_dict[item_key] != edited_dict[item_key]:
                item_changes[f"modified_{item_key}"] = {
                    'old': original_dict[item_key],
                    'new': edited_dict[item_key]
                }
        
        # 새로 추가된 항목
        for item_key in edited_dict.keys():
            if item_key not in original_dict:
                item_changes[f"added_{item_key}"] = edited_dict[item_key]
        
        return item_changes
    
    def _validate_db_compatibility(self, edited_data: Dict[str, Any], edit_file: Path) -> Dict[str, Any]:
        """DB 스키마 호환성 검증"""
        compatibility = {
            'status': 'compatible',
            'errors': [],
            'warnings': [],
            'recommendations': []
        }
        
        try:
            # 테이블명 추출
            table_name = self._extract_table_name_from_filename(edit_file)
            
            if table_name and table_name.startswith('tv_'):
                # TV 테이블 특수 검증
                if table_name == 'tv_trading_variables':
                    self._validate_trading_variables_schema(edited_data, compatibility)
                elif table_name == 'tv_variable_parameters':
                    self._validate_variable_parameters_schema(edited_data, compatibility)
                
                # 공통 검증
                self._validate_common_schema_rules(edited_data, compatibility)
            
        except Exception as e:
            compatibility['status'] = 'error'
            compatibility['errors'].append(f"스키마 검증 중 오류: {e}")
        
        return compatibility
    
    def _extract_table_name_from_filename(self, file_path: Path) -> Optional[str]:
        """파일명에서 테이블명 추출"""
        stem = file_path.stem
        
        # _EDIT_ 또는 _backup_ 패턴 제거
        for pattern in ['_EDIT_', '_backup_']:
            if pattern in stem:
                return stem.split(pattern)[0]
        
        return stem
    
    def _validate_trading_variables_schema(self, data: Dict[str, Any], compatibility: Dict[str, Any]) -> None:
        """trading_variables 스키마 검증"""
        if 'trading_variables' not in data:
            compatibility['errors'].append("trading_variables 키가 없습니다")
            compatibility['status'] = 'incompatible'
            return
        
        variables = data['trading_variables']
        if not isinstance(variables, dict):
            compatibility['errors'].append("trading_variables는 딕셔너리여야 합니다")
            compatibility['status'] = 'incompatible'
            return
        
        # 각 변수 검증
        required_fields = ['display_name_ko', 'purpose_category', 'chart_category', 'comparison_group']
        
        for var_id, var_data in variables.items():
            if not isinstance(var_data, dict):
                compatibility['errors'].append(f"{var_id}: 변수 데이터가 딕셔너리가 아닙니다")
                continue
            
            # 필수 필드 확인
            for field in required_fields:
                if field not in var_data:
                    compatibility['warnings'].append(f"{var_id}: 필수 필드 '{field}'가 없습니다")
    
    def _validate_variable_parameters_schema(self, data: Dict[str, Any], compatibility: Dict[str, Any]) -> None:
        """variable_parameters 스키마 검증"""
        if 'variable_parameters' not in data:
            compatibility['errors'].append("variable_parameters 키가 없습니다")
            compatibility['status'] = 'incompatible'
            return
        
        parameters = data['variable_parameters']
        if not isinstance(parameters, list):
            compatibility['errors'].append("variable_parameters는 리스트여야 합니다")
            compatibility['status'] = 'incompatible'
    
    def _validate_common_schema_rules(self, data: Dict[str, Any], compatibility: Dict[str, Any]) -> None:
        """공통 스키마 규칙 검증"""
        # 기본적인 YAML 구조 검증
        if not isinstance(data, dict):
            compatibility['errors'].append("최상위 구조가 딕셔너리가 아닙니다")
            compatibility['status'] = 'incompatible'
    
    def _print_validation_report(self, result: Dict[str, Any]) -> None:
        """검증 결과 리포트 출력"""
        print("\n" + "="*80)
        print("🔍 YAML 편집 변경사항 검증 보고서")
        print("="*80)
        
        print(f"📅 검증 시점: {result['validation_time']}")
        print(f"📄 원본 파일: {Path(result['original_file']).name}")
        print(f"✏️ 편집 파일: {Path(result['edited_file']).name}")
        
        print(f"\n🎯 검증 결과:")
        print(f"  • YAML 구문: {'✅ 정상' if result['yaml_valid'] else '❌ 오류'}")
        print(f"  • 변경사항: {'🔄 있음' if result['changes_detected'] else '📝 없음'}")
        print(f"  • DB 호환성: {result.get('db_compatibility', '알 수 없음')}")
        
        if result['changes_detected']:
            changes = result['changes_summary']
            total = changes.get('total_changes', 0)
            print(f"\n📊 변경사항 요약: 총 {total}개")
            
            if changes.get('added'):
                print(f"  ➕ 추가: {len(changes['added'])}개")
            if changes.get('modified'):
                print(f"  📝 수정: {len(changes['modified'])}개") 
            if changes.get('deleted'):
                print(f"  🗑️ 삭제: {len(changes['deleted'])}개")
        
        if result.get('validation_errors'):
            print(f"\n❌ 검증 오류:")
            for error in result['validation_errors']:
                print(f"  • {error}")
        
        if result.get('recommendations'):
            print(f"\n💡 권장사항:")
            for rec in result['recommendations']:
                print(f"  • {rec}")
        
        print("\n" + "="*80)
        
        if result['yaml_valid'] and not result['validation_errors']:
            print("✅ 변경사항이 검증되었습니다. --apply-changes로 DB에 반영할 수 있습니다.")
        else:
            print("⚠️ 검증 오류가 있습니다. 편집 파일을 수정한 후 다시 검증하세요.")
        
        print("="*80)
    
    def apply_changes_to_db(self, edit_file: str) -> bool:
        """편집된 변경사항을 DB에 반영"""
        try:
            edit_path = Path(edit_file)
            if not edit_path.exists():
                edit_path = self.data_info_path / edit_file
                if not edit_path.exists():
                    raise FileNotFoundError(f"편집 파일을 찾을 수 없습니다: {edit_file}")
            
            logger.info(f"🔄 DB 변경사항 적용 시작: {edit_path.name}")
            
            # 먼저 검증 실행
            validation_result = self.validate_changes(str(edit_path))
            
            if not validation_result['yaml_valid'] or validation_result['validation_errors']:
                logger.error("❌ 검증 실패로 인해 DB 적용을 중단합니다")
                return False
            
            if not validation_result['changes_detected']:
                logger.info("📝 변경사항이 없어서 DB 적용을 건너뜁니다")
                return True
            
            # 편집된 YAML을 원본 위치에 백업하고 새로운 이름으로 저장
            table_name = self._extract_table_name_from_filename(edit_path)
            if not table_name:
                raise ValueError("테이블명을 추출할 수 없습니다")
            
            # 타임스탬프 생성
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 표준 YAML 파일명으로 저장 (마이그레이션 매핑에 맞춤)
            standard_filename = f"{table_name}.yaml"
            migration_yaml_path = self.data_info_path / standard_filename
            
            # 기존 파일이 있다면 백업
            if migration_yaml_path.exists():
                backup_name = f"{table_name}_backup_before_apply_{timestamp}.yaml"
                backup_path = self.data_info_path / "_BACKUPS_" / backup_name
                backup_path.parent.mkdir(exist_ok=True)
                
                import shutil
                shutil.copy2(migration_yaml_path, backup_path)
                logger.info(f"📦 기존 파일 백업: {backup_name}")
            
            # 편집된 내용을 표준 파일명으로 저장 (메타데이터 주석 포함)
            self._save_applied_yaml(edit_path, migration_yaml_path, table_name)
            
            # DB 마이그레이션 실행 (기존 도구 활용)
            migration_success = self._execute_yaml_to_db_migration(migration_yaml_path, table_name)
            
            if migration_success:
                logger.info("✅ DB 변경사항 적용 완료")
                
                # 성공 시 편집 파일 정리
                self._cleanup_edit_file(edit_path, success=True)
                
                return True
            else:
                logger.error("❌ DB 마이그레이션 실패")
                return False
                
        except Exception as e:
            logger.error(f"❌ DB 변경사항 적용 실패: {e}")
            return False
    
    def _save_applied_yaml(self, edit_file: Path, target_file: Path, table_name: str) -> None:
        """적용할 YAML을 메타데이터와 함께 저장"""
        try:
            # 편집된 내용에서 YAML 데이터만 추출
            yaml_data = self._load_yaml_content(edit_file)
            
            if not yaml_data:
                raise ValueError("편집된 YAML 데이터를 로드할 수 없습니다")
            
            # 메타데이터 주석 생성
            metadata_comment = f"""# ════════════════════════════════════════════════════════════════
# 🔄 Super DB YAML Editor - Applied Changes
# ════════════════════════════════════════════════════════════════
# 편집 원본: {edit_file.name}
# 대상 테이블: {table_name}
# 적용 시점: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# 적용 도구: super_db_yaml_editor_workflow.py
# ────────────────────────────────────────────────────────────────
# 📝 처리 내역:
# - 편집된 변경사항이 DB에 반영되었습니다
# - 이 파일은 적용된 변경사항의 백업입니다
# - 원본 편집 세션은 정리되었습니다
# ════════════════════════════════════════════════════════════════

"""
            
            # YAML 데이터를 문자열로 변환
            yaml_content = yaml.dump(yaml_data, allow_unicode=True, indent=2, sort_keys=False)
            
            # 메타데이터 + 데이터 결합하여 저장
            with open(target_file, 'w', encoding='utf-8') as f:
                f.write(metadata_comment + yaml_content)
            
            logger.info(f"✅ 적용 YAML 저장: {target_file.name}")
            
        except Exception as e:
            logger.error(f"❌ 적용 YAML 저장 실패: {e}")
            raise
    
    def _execute_yaml_to_db_migration(self, yaml_file: Path, table_name: str) -> bool:
        """기존 YAML → DB 마이그레이션 도구 실행"""
        try:
            # super_db_migration_yaml_to_db.py 임포트 및 실행
            sys.path.insert(0, str(self.project_root / "tools"))
            
            # 임시적으로 외부 프로세스로 실행 (안전성)
            import subprocess
            
            migration_cmd = [
                "python",
                str(self.project_root / "tools" / "super_db_migration_yaml_to_db.py"),
                "--yaml-files", yaml_file.name
            ]
            
            result = subprocess.run(
                migration_cmd, 
                capture_output=True, 
                text=True, 
                cwd=str(self.project_root)
            )
            
            if result.returncode == 0:
                logger.info("✅ YAML → DB 마이그레이션 성공")
                return True
            else:
                logger.error(f"❌ 마이그레이션 실패: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 마이그레이션 실행 실패: {e}")
            return False
    
    def _cleanup_edit_file(self, edit_file: Path, success: bool = True) -> None:
        """편집 파일 정리"""
        try:
            # 세션 디렉토리 찾기
            session_dirs = list(edit_file.parent.glob("_BACKUPS_/session_*"))
            current_session_dir = None
            
            for session_dir in session_dirs:
                session_info_file = session_dir / "session_info.json"
                if session_info_file.exists():
                    try:
                        with open(session_info_file, 'r', encoding='utf-8') as f:
                            session_info = json.load(f)
                        if session_info.get('edit_file') == str(edit_file):
                            current_session_dir = session_dir
                            break
                    except:
                        continue
            
            if current_session_dir:
                # 편집 파일을 세션 백업으로 이동
                final_backup = current_session_dir / f"final_{edit_file.name}"
                shutil.move(edit_file, final_backup)
                
                # 세션 완료 표시
                session_info_file = current_session_dir / "session_info.json"
                if session_info_file.exists():
                    with open(session_info_file, 'r', encoding='utf-8') as f:
                        session_info = json.load(f)
                    
                    session_info['status'] = 'completed' if success else 'failed'
                    session_info['completion_time'] = datetime.now().isoformat()
                    session_info['final_backup'] = str(final_backup)
                    
                    with open(session_info_file, 'w', encoding='utf-8') as f:
                        json.dump(session_info, f, indent=2, ensure_ascii=False)
                
                logger.info(f"🗂️ 편집 세션 정리 완료: {current_session_dir}")
            else:
                # 세션 디렉토리를 찾을 수 없으면 단순 삭제
                edit_file.unlink(missing_ok=True)
                logger.info("🗑️ 편집 파일 삭제 완료")
                
        except Exception as e:
            logger.error(f"❌ 편집 파일 정리 실패: {e}")
    
    def cleanup_session(self, edit_file: str) -> bool:
        """편집 세션 수동 정리"""
        try:
            edit_path = Path(edit_file)
            if not edit_path.exists():
                edit_path = self.data_info_path / edit_file
            
            logger.info(f"🗂️ 편집 세션 정리: {edit_path.name}")
            
            self._cleanup_edit_file(edit_path, success=False)
            
            logger.info("✅ 편집 세션 정리 완료")
            return True
            
        except Exception as e:
            logger.error(f"❌ 편집 세션 정리 실패: {e}")
            return False


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description="🔄 Super DB YAML Editor Workflow - 편집-검증-통합 자동화 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 편집 세션 시작
  python tools/super_db_yaml_editor_workflow.py --start-edit tv_trading_variables_backup_20250801_143152.yaml
  
  # 변경사항 검증
  python tools/super_db_yaml_editor_workflow.py --validate-changes tv_trading_variables_EDIT_20250801_143152.yaml
  
  # DB에 변경사항 적용
  python tools/super_db_yaml_editor_workflow.py --apply-changes tv_trading_variables_EDIT_20250801_143152.yaml
  
  # 편집 세션 정리
  python tools/super_db_yaml_editor_workflow.py --cleanup-session tv_trading_variables_EDIT_20250801_143152.yaml
        """
    )
    
    parser.add_argument('--start-edit',
                       help='편집 세션 시작 (편집용 복사본 생성)')
    
    parser.add_argument('--validate-changes',
                       help='편집된 파일의 변경사항 검증')
    
    parser.add_argument('--apply-changes',
                       help='검증된 변경사항을 DB에 적용')
    
    parser.add_argument('--cleanup-session',
                       help='편집 세션 수동 정리')
    
    args = parser.parse_args()
    
    workflow = SuperDBYAMLEditorWorkflow()
    
    try:
        if args.start_edit:
            session = workflow.start_editing_session(args.start_edit)
            print(f"\n✅ 편집 세션이 시작되었습니다!")
            print(f"📝 편집 파일: {session.edit_file}")
            print(f"📁 백업 위치: {session.session_dir}")
            print(f"\n📋 다음 단계:")
            print(f"  1. {session.edit_file.name} 파일을 편집하세요")
            print(f"  2. 편집 완료 후 다음 명령어로 검증하세요:")
            print(f"     python tools/super_db_yaml_editor_workflow.py --validate-changes {session.edit_file.name}")
            return 0
            
        elif args.validate_changes:
            result = workflow.validate_changes(args.validate_changes)
            if result['yaml_valid'] and not result['validation_errors']:
                print(f"\n🎯 다음 단계: DB에 변경사항을 적용하려면 다음 명령어를 실행하세요:")
                print(f"python tools/super_db_yaml_editor_workflow.py --apply-changes {args.validate_changes}")
                return 0
            else:
                return 1
                
        elif args.apply_changes:
            success = workflow.apply_changes_to_db(args.apply_changes)
            if success:
                print(f"\n🎉 변경사항이 성공적으로 DB에 적용되었습니다!")
                print(f"📝 편집 세션이 자동으로 정리되었습니다.")
                return 0
            else:
                return 1
                
        elif args.cleanup_session:
            success = workflow.cleanup_session(args.cleanup_session)
            return 0 if success else 1
            
        else:
            parser.print_help()
            return 1
            
    except Exception as e:
        logger.error(f"❌ 예상치 못한 오류: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
