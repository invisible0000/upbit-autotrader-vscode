#!/usr/bin/env python3
"""
🔄 Super DB YAML Merger
Manual YAML + Runtime YAML → Merged YAML 통합 도구

🤖 LLM 사용 가이드:
===================
이 도구는 수동 작성된 YAML(LLM 친화적)과 DB 추출 YAML(시스템 정확)을
지능적으로 병합하여 완전한 통합 YAML을 생성합니다.

📋 주요 명령어 (tools 폴더에서 실행):
1. python super_db_yaml_merger.py --manual tv_trading_variables.yaml --runtime tv_trading_variables_backup.yaml
2. python super_db_yaml_merger.py --auto-detect --table tv_trading_variables
3. python super_db_yaml_merger.py --batch-merge --output-dir merged/

🎯 언제 사용하면 좋은가:
- LLM 편집용 YAML과 DB 추출 YAML을 통합할 때
- 시스템 정확성 + LLM 친화성 모두 확보하고 싶을 때
- 양방향 동기화가 필요할 때
- 완전한 메타데이터가 포함된 YAML이 필요할 때

💡 출력 해석:
- 🟢 Manual 우선: LLM 작성 주석, 가이드, 설명 우선 채택
- 🔵 Runtime 우선: DB 메타데이터, 시스템 정보 우선 채택
- 🟡 스마트 병합: 양쪽 정보를 지능적으로 결합
- 🟠 충돌 해결: 불일치 시 우선순위 규칙 적용

기능:
1. Manual + Runtime YAML 지능적 병합
2. 충돌 해결 및 우선순위 적용
3. 메타데이터 보존 및 최적화
4. 배치 처리 및 자동 감지
5. 백업 및 버전 관리

작성일: 2025-08-01
작성자: Upbit Auto Trading Team
"""

import argparse
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class MergeMetadata:
    """병합 메타데이터 정보"""
    merge_timestamp: str
    manual_source: str
    runtime_source: str
    output_target: str
    merge_strategy: str
    conflict_resolution: str
    tool_version: str = "super_db_yaml_merger.py v1.0"
    
    def generate_header_comment(self) -> str:
        return f"""# ═══════════════════════════════════════════════════════════════════
# 🔄 Super DB YAML Merger - 통합 메타데이터
# ═══════════════════════════════════════════════════════════════════
# 병합 시점: {self.merge_timestamp}
# Manual 소스: {self.manual_source}
# Runtime 소스: {self.runtime_source}
# 출력 파일: {self.output_target}
# 병합 전략: {self.merge_strategy}
# 충돌 해결: {self.conflict_resolution}
# 병합 도구: {self.tool_version}
# ───────────────────────────────────────────────────────────────────
# 📝 통합 정보:
# - 🟢 Manual 우선: 주석, 가이드, LLM 친화적 설명
# - 🔵 Runtime 우선: 시스템 메타데이터, DB 정확성 정보
# - 🟡 스마트 병합: 양쪽 장점을 지능적으로 결합
# - 🟠 충돌 해결: 데이터 타입별 우선순위 규칙 적용
# ═══════════════════════════════════════════════════════════════════

"""


@dataclass
class ConflictRule:
    """충돌 해결 규칙"""
    field_name: str
    priority: str  # 'manual', 'runtime', 'merge', 'newer'
    merge_strategy: str  # 'override', 'append', 'combine', 'validate'
    description: str


class SuperDBYAMLMerger:
    """
    🔄 Manual YAML + Runtime YAML → Merged YAML 통합 도구
    
    🤖 LLM 사용 패턴:
    merger = SuperDBYAMLMerger()
    merger.merge_yamls("manual.yaml", "runtime.yaml", "merged.yaml")
    merger.auto_detect_and_merge("tv_trading_variables")
    merger.batch_merge_all()
    
    💡 핵심 기능: LLM 친화성 + 시스템 정확성 완벽 조화
    """
    
    def __init__(self, data_info_path: str = None):
        """
        Super DB YAML Merger 초기화
        
        Args:
            data_info_path: data_info 폴더 경로 (기본값: 자동 감지)
        """
        logger.info("🔄 Super DB YAML Merger 초기화")
        
        if data_info_path:
            self.data_info_path = Path(data_info_path)
        else:
            # 자동 경로 감지
            current_dir = Path.cwd()
            base_path1 = (current_dir / "upbit_auto_trading" / "utils"
                          / "trading_variables" / "gui_variables_DB_migration_util")
            base_path2 = (Path(__file__).parent.parent / "upbit_auto_trading"
                          / "utils" / "trading_variables" / "gui_variables_DB_migration_util")
            
            possible_paths = [
                base_path1 / "data_info",
                current_dir / "data_info",
                base_path2 / "data_info"
            ]
            
            for path in possible_paths:
                if path.exists():
                    self.data_info_path = path
                    break
            else:
                raise FileNotFoundError("❌ data_info 폴더를 찾을 수 없습니다")
        
        logger.info(f"📂 Data Info Path: {self.data_info_path}")
        
        # 백업 디렉토리 생성
        self.backup_dir = self.data_info_path / "_BACKUPS_"
        self.merged_dir = self.data_info_path / "_MERGED_"
        self.backup_dir.mkdir(exist_ok=True)
        self.merged_dir.mkdir(exist_ok=True)
        
        # 충돌 해결 규칙 설정
        self._setup_conflict_rules()
    
    def _setup_conflict_rules(self) -> None:
        """충돌 해결 규칙 설정"""
        self.conflict_rules = {
            # LLM 편집용 필드들 - Manual 우선
            'typical_usage': ConflictRule('typical_usage', 'manual', 'override', 'LLM 학습용 정보'),
            'compatibility_notes': ConflictRule('compatibility_notes', 'manual', 'override', 'LLM 가이드'),
            'examples': ConflictRule('examples', 'manual', 'override', 'LLM 예시'),
            'description': ConflictRule('description', 'manual', 'combine', 'Manual 설명 + Runtime 보완'),
            'display_name_ko': ConflictRule('display_name_ko', 'manual', 'override', 'Manual 한글명 우선'),
            'display_name_en': ConflictRule('display_name_en', 'manual', 'override', 'Manual 영문명 우선'),
            
            # 시스템 메타데이터 - Runtime 우선
            'is_active': ConflictRule('is_active', 'runtime', 'override', '실제 활성 상태'),
            'created_at': ConflictRule('created_at', 'runtime', 'override', '실제 생성 시점'),
            'updated_at': ConflictRule('updated_at', 'runtime', 'override', '실제 수정 시점'),
            'source': ConflictRule('source', 'runtime', 'override', '실제 데이터 소스'),
            
            # 구조적 정보 - Runtime 우선 (DB 정확성)
            'purpose_category': ConflictRule('purpose_category', 'runtime', 'validate', 'DB 기준 검증'),
            'chart_category': ConflictRule('chart_category', 'runtime', 'validate', 'DB 기준 검증'),
            'comparison_group': ConflictRule('comparison_group', 'runtime', 'validate', 'DB 기준 검증'),
            
            # ID 및 키 필드 - Runtime 우선
            'variable_id': ConflictRule('variable_id', 'runtime', 'override', 'DB 정확성'),
            'parameter_id': ConflictRule('parameter_id', 'runtime', 'override', 'DB 정확성'),
            'category_id': ConflictRule('category_id', 'runtime', 'override', 'DB 정확성'),
        }
    
    def _load_yaml_safely(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """YAML 파일 안전 로드"""
        try:
            if not file_path.exists():
                logger.warning(f"⚠️ 파일이 존재하지 않습니다: {file_path}")
                return None
                
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 주석 제거 (메타데이터 헤더 주석만 제거)
            lines = content.split('\n')
            yaml_start_idx = 0
            
            for i, line in enumerate(lines):
                if line.strip() and not line.strip().startswith('#'):
                    yaml_start_idx = i
                    break
            
            clean_content = '\n'.join(lines[yaml_start_idx:])
            data = yaml.safe_load(clean_content)
            
            logger.info(f"✅ YAML 로드 성공: {file_path.name}")
            return data
            
        except Exception as e:
            logger.error(f"❌ YAML 로드 실패: {file_path} - {e}")
            return None
    
    def _merge_single_item(self, key: str, manual_item: Dict, runtime_item: Dict) -> Dict[str, Any]:
        """단일 아이템 지능적 병합"""
        merged_item = {}
        all_fields = set(manual_item.keys()) | set(runtime_item.keys())
        
        for field in all_fields:
            manual_value = manual_item.get(field)
            runtime_value = runtime_item.get(field)
            
            # 충돌 해결 규칙 적용
            if field in self.conflict_rules:
                rule = self.conflict_rules[field]
                merged_value = self._apply_conflict_rule(field, manual_value, runtime_value, rule)
            else:
                # 기본 규칙: Runtime 우선, Manual 보완
                merged_value = runtime_value if runtime_value is not None else manual_value
            
            if merged_value is not None:
                merged_item[field] = merged_value
        
        return merged_item
    
    def _apply_conflict_rule(self, field: str, manual_value: Any, runtime_value: Any, rule: ConflictRule) -> Any:
        """충돌 해결 규칙 적용"""
        if rule.priority == 'manual':
            return manual_value if manual_value is not None else runtime_value
        elif rule.priority == 'runtime':
            return runtime_value if runtime_value is not None else manual_value
        elif rule.priority == 'merge':
            if rule.merge_strategy == 'combine':
                return self._combine_values(manual_value, runtime_value)
            elif rule.merge_strategy == 'append':
                return self._append_values(manual_value, runtime_value)
        elif rule.priority == 'validate':
            # 검증 후 결정
            return self._validate_and_choose(field, manual_value, runtime_value)
        
        # 기본: Runtime 우선
        return runtime_value if runtime_value is not None else manual_value
    
    def _combine_values(self, manual_value: Any, runtime_value: Any) -> Any:
        """값 결합 (문자열의 경우 병합)"""
        if isinstance(manual_value, str) and isinstance(runtime_value, str):
            if manual_value and runtime_value:
                if manual_value != runtime_value:
                    return f"{manual_value} (Manual) | {runtime_value} (Runtime)"
                else:
                    return manual_value
            return manual_value or runtime_value
        return runtime_value if runtime_value is not None else manual_value
    
    def _append_values(self, manual_value: Any, runtime_value: Any) -> Any:
        """값 추가 (리스트의 경우 병합)"""
        if isinstance(manual_value, list) and isinstance(runtime_value, list):
            combined = list(manual_value) if manual_value else []
            if runtime_value:
                for item in runtime_value:
                    if item not in combined:
                        combined.append(item)
            return combined
        return runtime_value if runtime_value is not None else manual_value
    
    def _validate_and_choose(self, field: str, manual_value: Any, runtime_value: Any) -> Any:
        """검증 후 값 선택"""
        # 실제 구현에서는 더 정교한 검증 로직 추가 가능
        # 현재는 Runtime 우선, Manual 보완
        if runtime_value is not None:
            logger.debug(f"🔍 검증: {field} = {runtime_value} (Runtime 채택)")
            return runtime_value
        else:
            logger.debug(f"🔍 검증: {field} = {manual_value} (Manual 채택)")
            return manual_value
    
    def merge_yamls(self, manual_file: str, runtime_file: str, output_file: str = None, 
                   merge_strategy: str = "smart") -> bool:
        """
        🤖 LLM 추천: 핵심 병합 메서드
        Manual YAML과 Runtime YAML을 지능적으로 병합
        
        Args:
            manual_file: 수동 작성 YAML 파일명
            runtime_file: DB 추출 YAML 파일명  
            output_file: 출력 파일명 (기본값: 자동 생성)
            merge_strategy: 병합 전략 ('smart', 'manual_priority', 'runtime_priority')
        
        Returns:
            bool: 병합 성공 여부
        """
        logger.info(f"🔄 YAML 병합 시작: {manual_file} + {runtime_file}")
        
        # 파일 경로 설정
        manual_path = self.data_info_path / manual_file
        runtime_path = self.data_info_path / runtime_file
        
        if not output_file:
            base_name = manual_file.replace('.yaml', '').replace('_manual', '')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"{base_name}_merged_{timestamp}.yaml"
        
        output_path = self.merged_dir / output_file
        
        # YAML 로드
        manual_data = self._load_yaml_safely(manual_path)
        runtime_data = self._load_yaml_safely(runtime_path)
        
        if not manual_data and not runtime_data:
            logger.error(f"❌ 로드할 YAML 데이터가 없습니다")
            return False
        
        # 데이터 확인 및 기본값 설정
        manual_data = manual_data or {}
        runtime_data = runtime_data or {}
        
        # 최상위 키 추출 (보통 테이블명)
        manual_keys = set(manual_data.keys())
        runtime_keys = set(runtime_data.keys())
        all_keys = manual_keys | runtime_keys
        
        logger.info(f"📊 병합 대상 키: {len(all_keys)}개 - {list(all_keys)}")
        
        # 병합 실행
        merged_data = {}
        conflict_count = 0
        
        for top_key in all_keys:
            manual_section = manual_data.get(top_key, {})
            runtime_section = runtime_data.get(top_key, {})
            
            if isinstance(manual_section, dict) and isinstance(runtime_section, dict):
                merged_section = {}
                
                # 개별 아이템 병합
                all_item_keys = set(manual_section.keys()) | set(runtime_section.keys())
                
                for item_key in all_item_keys:
                    manual_item = manual_section.get(item_key, {})
                    runtime_item = runtime_section.get(item_key, {})
                    
                    if isinstance(manual_item, dict) and isinstance(runtime_item, dict):
                        merged_item = self._merge_single_item(item_key, manual_item, runtime_item)
                        merged_section[item_key] = merged_item
                        
                        # 충돌 감지
                        common_fields = set(manual_item.keys()) & set(runtime_item.keys())
                        for field in common_fields:
                            if manual_item.get(field) != runtime_item.get(field):
                                conflict_count += 1
                    else:
                        # 딕셔너리가 아닌 경우 Runtime 우선
                        merged_section[item_key] = runtime_item if runtime_item else manual_item
                
                merged_data[top_key] = merged_section
            else:
                # 최상위가 딕셔너리가 아닌 경우
                merged_data[top_key] = runtime_section if runtime_section else manual_section
        
        # 메타데이터 생성
        metadata = MergeMetadata(
            merge_timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            manual_source=str(manual_path),
            runtime_source=str(runtime_path),
            output_target=str(output_path),
            merge_strategy=merge_strategy,
            conflict_resolution=f"{conflict_count}개 충돌 해결"
        )
        
        # YAML 저장
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                # 메타데이터 헤더 작성
                f.write(metadata.generate_header_comment())
                
                # YAML 데이터 작성
                yaml.dump(merged_data, f, default_flow_style=False, 
                         allow_unicode=True, sort_keys=False, indent=2)
            
            logger.info(f"✅ 병합 완료: {output_path}")
            logger.info(f"📊 충돌 해결: {conflict_count}개")
            logger.info(f"📝 데이터 항목: {sum(len(section) if isinstance(section, dict) else 1 for section in merged_data.values())}개")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 병합 파일 저장 실패: {e}")
            return False
    
    def auto_detect_and_merge(self, table_name: str) -> bool:
        """
        🤖 LLM 추천: 자동 감지 병합
        테이블명을 기반으로 Manual과 Runtime YAML을 자동 감지하여 병합
        
        Args:
            table_name: 테이블명 (예: tv_trading_variables)
        
        Returns:
            bool: 병합 성공 여부
        """
        logger.info(f"🔍 자동 감지 병합: {table_name}")
        
        # 가능한 파일명 패턴 검색
        manual_patterns = [
            f"{table_name}.yaml",
            f"{table_name}_manual.yaml",
        ]
        
        runtime_patterns = [
            f"{table_name}_backup*.yaml",
            f"{table_name}_runtime*.yaml",
            f"{table_name}_extracted*.yaml",
        ]
        
        # Manual 파일 찾기
        manual_file = None
        for pattern in manual_patterns:
            files = list(self.data_info_path.glob(pattern))
            if files:
                manual_file = files[0].name
                break
        
        # Runtime 파일 찾기 (가장 최신)
        runtime_file = None
        runtime_files = []
        for pattern in runtime_patterns:
            runtime_files.extend(self.data_info_path.glob(pattern))
        
        if runtime_files:
            # 가장 최신 파일 선택
            runtime_file = max(runtime_files, key=lambda f: f.stat().st_mtime).name
        
        if not manual_file and not runtime_file:
            logger.error(f"❌ {table_name}에 대한 YAML 파일을 찾을 수 없습니다")
            return False
        
        logger.info(f"📁 감지된 파일: Manual={manual_file}, Runtime={runtime_file}")
        
        # 병합 실행
        return self.merge_yamls(
            manual_file=manual_file or "empty.yaml",
            runtime_file=runtime_file or "empty.yaml",
            merge_strategy="smart"
        )
    
    def batch_merge_all(self, output_dir: str = None) -> List[str]:
        """
        🤖 LLM 추천: 배치 병합
        data_info 폴더의 모든 Manual/Runtime 쌍을 자동 감지하여 배치 병합
        
        Args:
            output_dir: 출력 디렉토리 (기본값: _MERGED_)
        
        Returns:
            List[str]: 생성된 병합 파일 목록
        """
        logger.info("🚀 배치 병합 시작: 모든 YAML 파일 자동 감지")
        
        # 테이블명 추출
        yaml_files = list(self.data_info_path.glob("*.yaml"))
        table_names = set()
        
        for file in yaml_files:
            name = file.stem
            # 패턴 분석으로 테이블명 추출
            if name.startswith('tv_'):
                table_name = name.replace('_manual', '').replace('_runtime', '')
                table_name = table_name.split('_backup')[0]
                table_name = table_name.split('_extracted')[0]
                table_names.add(table_name)
        
        logger.info(f"📋 감지된 테이블: {len(table_names)}개 - {sorted(table_names)}")
        
        # 각 테이블별 병합 실행
        merged_files = []
        for table_name in sorted(table_names):
            try:
                if self.auto_detect_and_merge(table_name):
                    # 생성된 파일명 추정
                    merged_pattern = f"{table_name}_merged_*.yaml"
                    merged_candidates = list(self.merged_dir.glob(merged_pattern))
                    if merged_candidates:
                        latest_merged = max(merged_candidates, key=lambda f: f.stat().st_mtime)
                        merged_files.append(latest_merged.name)
                        logger.info(f"✅ {table_name} 병합 성공: {latest_merged.name}")
                else:
                    logger.warning(f"⚠️ {table_name} 병합 실패")
            except Exception as e:
                logger.error(f"❌ {table_name} 병합 중 오류: {e}")
        
        logger.info(f"🎉 배치 병합 완료: {len(merged_files)}개 파일 생성")
        return merged_files
    
    def compare_yamls(self, manual_file: str, runtime_file: str) -> Dict[str, Any]:
        """
        🤖 LLM 추천: YAML 비교 분석
        Manual과 Runtime YAML의 차이점을 상세 분석
        
        Args:
            manual_file: Manual YAML 파일명
            runtime_file: Runtime YAML 파일명
        
        Returns:
            Dict[str, Any]: 비교 분석 결과
        """
        logger.info(f"🔍 YAML 비교 분석: {manual_file} vs {runtime_file}")
        
        manual_data = self._load_yaml_safely(self.data_info_path / manual_file)
        runtime_data = self._load_yaml_safely(self.data_info_path / runtime_file)
        
        if not manual_data or not runtime_data:
            return {"error": "YAML 로드 실패"}
        
        comparison = {
            "analysis_timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "manual_file": manual_file,
            "runtime_file": runtime_file,
            "structure_comparison": {},
            "content_differences": {},
            "field_statistics": {},
            "recommendations": []
        }
        
        # 구조 비교
        manual_keys = set(manual_data.keys())
        runtime_keys = set(runtime_data.keys())
        
        comparison["structure_comparison"] = {
            "manual_only": list(manual_keys - runtime_keys),
            "runtime_only": list(runtime_keys - manual_keys),
            "common": list(manual_keys & runtime_keys)
        }
        
        # 상세 차이점 분석
        differences = {}
        field_stats = {"manual_unique": 0, "runtime_unique": 0, "conflicts": 0}
        
        for key in manual_keys & runtime_keys:
            manual_section = manual_data[key]
            runtime_section = runtime_data[key]
            
            if isinstance(manual_section, dict) and isinstance(runtime_section, dict):
                section_diff = self._compare_sections(manual_section, runtime_section)
                if section_diff:
                    differences[key] = section_diff
                    field_stats["conflicts"] += section_diff.get("conflict_count", 0)
        
        comparison["content_differences"] = differences
        comparison["field_statistics"] = field_stats
        
        # 권장사항 생성
        recommendations = []
        if field_stats["conflicts"] > 0:
            recommendations.append("🔄 병합 필요: 충돌하는 필드들을 스마트 병합으로 해결")
        if len(comparison["structure_comparison"]["manual_only"]) > 0:
            recommendations.append("📝 Manual 전용 필드: LLM 친화적 정보 활용 권장")
        if len(comparison["structure_comparison"]["runtime_only"]) > 0:
            recommendations.append("⚙️ Runtime 전용 필드: 시스템 메타데이터 보존 권장")
        
        comparison["recommendations"] = recommendations
        
        return comparison


    def _compare_sections(self, manual_section: Dict, runtime_section: Dict) -> Dict[str, Any]:
        """섹션별 상세 비교"""
        manual_items = set(manual_section.keys())
        runtime_items = set(runtime_section.keys())
        
        section_diff = {
            "manual_only_items": list(manual_items - runtime_items),
            "runtime_only_items": list(runtime_items - manual_items),
            "common_items": list(manual_items & runtime_items),
            "field_conflicts": {},
            "conflict_count": 0
        }
        
        # 공통 아이템의 필드별 비교
        for item_key in manual_items & runtime_items:
            manual_item = manual_section[item_key]
            runtime_item = runtime_section[item_key]
            
            if isinstance(manual_item, dict) and isinstance(runtime_item, dict):
                item_conflicts = {}
                
                for field in set(manual_item.keys()) & set(runtime_item.keys()):
                    manual_val = manual_item.get(field)
                    runtime_val = runtime_item.get(field)
                    
                    if manual_val != runtime_val:
                        item_conflicts[field] = {
                            "manual": manual_val,
                            "runtime": runtime_val
                        }
                        section_diff["conflict_count"] += 1
                
                if item_conflicts:
                    section_diff["field_conflicts"][item_key] = item_conflicts
        
        return section_diff if section_diff["conflict_count"] > 0 or section_diff["manual_only_items"] or section_diff["runtime_only_items"] else None


def main():
    """
    🤖 LLM 사용 가이드: 메인 실행 함수
    
    명령행 인수에 따라 다른 기능 실행:
    - --manual + --runtime: 지정된 파일들 병합
    - --auto-detect + --table: 테이블명 기반 자동 감지 병합
    - --batch-merge: 모든 테이블 배치 병합
    - --compare: YAML 파일 비교 분석
    
    🎯 LLM이 자주 사용할 패턴:
    1. python super_db_yaml_merger.py --auto-detect --table tv_trading_variables
    2. python super_db_yaml_merger.py --batch-merge
    3. python super_db_yaml_merger.py --compare --manual tv_trading_variables.yaml --runtime tv_trading_variables_backup.yaml
    """
    parser = argparse.ArgumentParser(
        description='🔄 Super DB YAML Merger - Manual + Runtime YAML 통합 도구',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 지정된 파일 병합
  python super_db_yaml_merger.py --manual tv_trading_variables.yaml --runtime tv_trading_variables_backup.yaml
  
  # 자동 감지 병합
  python super_db_yaml_merger.py --auto-detect --table tv_trading_variables
  
  # 배치 병합
  python super_db_yaml_merger.py --batch-merge
  
  # 비교 분석
  python super_db_yaml_merger.py --compare --manual tv_trading_variables.yaml --runtime tv_trading_variables_backup.yaml
        """
    )
    
    # 메인 동작 옵션
    parser.add_argument('--manual', type=str, help='Manual YAML 파일명')
    parser.add_argument('--runtime', type=str, help='Runtime YAML 파일명')
    parser.add_argument('--output', type=str, help='출력 파일명 (선택적)')
    
    # 자동 감지 옵션
    parser.add_argument('--auto-detect', action='store_true', help='자동 감지 모드')
    parser.add_argument('--table', type=str, help='테이블명 (자동 감지용)')
    
    # 배치 처리 옵션
    parser.add_argument('--batch-merge', action='store_true', help='모든 YAML 배치 병합')
    parser.add_argument('--output-dir', type=str, help='출력 디렉토리 (배치용)')
    
    # 비교 분석 옵션
    parser.add_argument('--compare', action='store_true', help='YAML 비교 분석')
    
    # 기타 옵션
    parser.add_argument('--data-info-path', type=str, help='data_info 폴더 경로')
    parser.add_argument('--merge-strategy', type=str, default='smart', 
                       choices=['smart', 'manual_priority', 'runtime_priority'],
                       help='병합 전략')
    
    args = parser.parse_args()
    
    try:
        # 병합기 초기화
        merger = SuperDBYAMLMerger(args.data_info_path)
        
        # 기능별 실행
        if args.compare:
            # 비교 분석
            if not args.manual or not args.runtime:
                print("❌ 비교를 위해서는 --manual과 --runtime 파일을 모두 지정해야 합니다")
                return
            
            comparison = merger.compare_yamls(args.manual, args.runtime)
            
            print("🔍 === YAML 비교 분석 결과 ===")
            print(f"📅 분석 시점: {comparison['analysis_timestamp']}")
            print(f"📄 Manual: {comparison['manual_file']}")
            print(f"📄 Runtime: {comparison['runtime_file']}")
            print()
            
            # 구조 비교
            struct = comparison['structure_comparison']
            print(f"📊 구조 비교:")
            print(f"  • 공통 섹션: {len(struct['common'])}개")
            print(f"  • Manual 전용: {len(struct['manual_only'])}개")
            print(f"  • Runtime 전용: {len(struct['runtime_only'])}개")
            print()
            
            # 충돌 통계
            stats = comparison['field_statistics']
            print(f"⚠️ 충돌 통계:")
            print(f"  • 충돌 필드: {stats['conflicts']}개")
            print()
            
            # 권장사항
            if comparison['recommendations']:
                print("💡 권장사항:")
                for rec in comparison['recommendations']:
                    print(f"  • {rec}")
            
        elif args.batch_merge:
            # 배치 병합
            merged_files = merger.batch_merge_all(args.output_dir)
            print(f"🎉 배치 병합 완료: {len(merged_files)}개 파일 생성")
            for file in merged_files:
                print(f"  ✅ {file}")
        
        elif args.auto_detect and args.table:
            # 자동 감지 병합
            success = merger.auto_detect_and_merge(args.table)
            if success:
                print(f"✅ {args.table} 자동 병합 완료")
            else:
                print(f"❌ {args.table} 자동 병합 실패")
        
        elif args.manual and args.runtime:
            # 직접 지정 병합
            success = merger.merge_yamls(
                args.manual, 
                args.runtime, 
                args.output, 
                args.merge_strategy
            )
            if success:
                print(f"✅ YAML 병합 완료: {args.manual} + {args.runtime}")
            else:
                print(f"❌ YAML 병합 실패")
        
        else:
            # 도움말 표시
            parser.print_help()
            print("\n💡 빠른 시작:")
            print("  python super_db_yaml_merger.py --auto-detect --table tv_trading_variables")
            print("  python super_db_yaml_merger.py --batch-merge")
    
    except Exception as e:
        logger.error(f"❌ 실행 중 오류: {e}")
        print(f"❌ 실행 실패: {e}")


if __name__ == "__main__":
    main()
