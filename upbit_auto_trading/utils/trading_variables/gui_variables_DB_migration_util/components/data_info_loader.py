#!/usr/bin/env python3
"""
Variables Data Info 로더 - 변수/조건 빌더 전용 YAML 파일 관리
============================================================

variables_* 접두사를 가진 YAML 파일들을 로드하고 관리하는 모듈
condition builder에서 trigger 생성에 사용되는 variables 정보 전용
향후 DB 마이그레이션을 위한 임시 솔루션

관리 파일들:
- variables_indicator_categories.yaml: 지표 카테고리 정의
- variables_parameter_types.yaml: 파라미터 타입 가이드라인
- variables_indicator_library.yaml: 지표 라이브러리
- variables_help_texts.yaml: 도움말 텍스트
- variables_placeholder_texts.yaml: 플레이스홀더 예시
- variables_workflow_guide.yaml: 워크플로우 가이드

주요 기능:
- variables_* YAML 파일 일괄 로드
- 데이터 검증 및 표준화
- DB 마이그레이션 준비

작성일: 2025-07-30
수정일: 2025-07-30 (variables_ 접두사 적용)
"""

import os
import yaml
from typing import Dict, Any, Optional
from datetime import datetime


class DataInfoLoader:
    """variables_* 파일들을 관리하는 클래스 (condition builder용 variables 전용)"""
    
    def __init__(self, data_info_path: str = None):
        """
        초기화
        
        Args:
            data_info_path: data_info 폴더 경로 (자동 감지 가능)
        """
        self.data_info_path = data_info_path or self._find_data_info_path()
        self.loaded_data = {}
        self.load_status = {}
        self.last_loaded = None
    
    def _find_data_info_path(self) -> str:
        """data_info 폴더 경로 자동 감지"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_info_path = os.path.join(os.path.dirname(current_dir), 'data_info')
        
        if os.path.exists(data_info_path):
            return data_info_path
        
        # 대안 경로들 시도
        alternative_paths = [
            os.path.join(current_dir, '..', 'data_info'),
            os.path.join(current_dir, 'data_info'),
            os.path.join(os.getcwd(), 'data_info')
        ]
        
        for path in alternative_paths:
            abs_path = os.path.abspath(path)
            if os.path.exists(abs_path):
                return abs_path
        
        # 기본 경로 반환 (폴더가 없어도)
        return data_info_path
    
    def load_all_files(self, force_reload: bool = False) -> Dict[str, Any]:
        """
        모든 YAML 파일 로드
        
        Args:
            force_reload: 강제 재로드 여부
            
        Returns:
            로드된 모든 데이터
        """
        if not force_reload and self.loaded_data and self.last_loaded:
            return self.loaded_data
        
        yaml_files = {
            'indicator_categories': 'variables_indicator_categories.yaml',
            'parameter_types': 'variables_parameter_types.yaml',
            'indicator_library': 'variables_indicator_library.yaml',
            'help_texts': 'variables_help_texts.yaml',
            'placeholder_texts': 'variables_placeholder_texts.yaml',
            'workflow_guide': 'variables_workflow_guide.yaml'
        }
        
        self.loaded_data = {}
        self.load_status = {}
        
        for key, filename in yaml_files.items():
            file_path = os.path.join(self.data_info_path, filename)
            
            try:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                        self.loaded_data[key] = data
                        self.load_status[key] = "✅ 성공"
                else:
                    self.loaded_data[key] = None
                    self.load_status[key] = "❌ 파일 없음"
                    
            except Exception as e:
                self.loaded_data[key] = None
                self.load_status[key] = f"❌ 로드 실패: {str(e)}"
                print(f"⚠️ {filename} 로드 실패: {e}")
        
        self.last_loaded = datetime.now()
        return self.loaded_data
    
    def get_data(self, data_type: str) -> Optional[Dict[str, Any]]:
        """
        특정 데이터 타입 조회
        
        Args:
            data_type: 데이터 타입 (variables_indicator_categories, variables_parameter_types 등)
            
        Returns:
            해당 데이터 또는 None
        """
        if not self.loaded_data:
            self.load_all_files()
        
        return self.loaded_data.get(data_type)
    
    def get_indicator_library(self) -> Dict[str, Any]:
        """지표 라이브러리 데이터 조회"""
        return self.get_data('indicator_library') or {'indicators': {}}
    
    def get_help_texts(self) -> Dict[str, Any]:
        """도움말 텍스트 데이터 조회"""
        return self.get_data('help_texts') or {'parameter_help_texts': {}}
    
    def get_placeholder_texts(self) -> Dict[str, Any]:
        """플레이스홀더 텍스트 데이터 조회"""
        return self.get_data('placeholder_texts') or {'indicators': {}}
    
    def get_indicator_categories(self) -> Dict[str, Any]:
        """지표 카테고리 데이터 조회"""
        return self.get_data('indicator_categories') or {'categories': {}}
    
    def get_parameter_types(self) -> Dict[str, Any]:
        """파라미터 타입 데이터 조회"""
        return self.get_data('parameter_types') or {'parameter_types': {}}
    
    def get_load_status(self) -> Dict[str, str]:
        """로드 상태 정보 반환"""
        if not self.load_status:
            self.load_all_files()
        return self.load_status.copy()
    
    def get_summary(self) -> Dict[str, Any]:
        """data_info 요약 정보 반환"""
        if not self.loaded_data:
            self.load_all_files()
        
        summary = {
            "data_info_path": self.data_info_path,
            "path_exists": os.path.exists(self.data_info_path),
            "last_loaded": self.last_loaded.isoformat() if self.last_loaded else None,
            "load_status": self.load_status.copy(),
            "data_counts": {}
        }
        
        # 각 데이터 타입별 개수 정보
        indicator_lib = self.get_indicator_library()
        summary["data_counts"]["indicators"] = len(indicator_lib.get('indicators', {}))
        
        help_texts = self.get_help_texts()
        summary["data_counts"]["help_texts"] = len(help_texts.get('parameter_help_texts', {}))
        
        placeholder_texts = self.get_placeholder_texts()
        summary["data_counts"]["placeholders"] = len(placeholder_texts.get('indicators', {}))
        
        categories = self.get_indicator_categories()
        summary["data_counts"]["categories"] = len(categories.get('categories', {}))
        
        param_types = self.get_parameter_types()
        summary["data_counts"]["parameter_types"] = len(param_types.get('parameter_types', {}))
        
        return summary
    
    def validate_data_integrity(self) -> Dict[str, Any]:
        """데이터 무결성 검증"""
        if not self.loaded_data:
            self.load_all_files()
        
        validation_results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "checks": {}
        }
        
        # 1. 필수 파일 존재 여부
        required_files = ['indicator_library', 'help_texts', 'placeholder_texts']
        for file_key in required_files:
            if not self.loaded_data.get(file_key):
                validation_results["errors"].append(f"필수 파일 누락: {file_key}")
                validation_results["is_valid"] = False
        
        # 2. 지표 라이브러리 검증
        indicator_lib = self.get_indicator_library()
        indicators = indicator_lib.get('indicators', {})
        validation_results["checks"]["indicator_count"] = len(indicators)
        
        # 3. 도움말 텍스트 커버리지 검증
        help_texts = self.get_help_texts()
        help_params = help_texts.get('parameter_help_texts', {})
        validation_results["checks"]["help_text_count"] = len(help_params)
        
        # 4. 플레이스홀더 커버리지 검증
        placeholder_texts = self.get_placeholder_texts()
        placeholder_indicators = placeholder_texts.get('indicators', {})
        validation_results["checks"]["placeholder_count"] = len(placeholder_indicators)
        
        # 5. 데이터 일관성 검증
        missing_placeholders = set(indicators.keys()) - set(placeholder_indicators.keys())
        if missing_placeholders:
            validation_results["warnings"].append(
                f"플레이스홀더가 없는 지표: {list(missing_placeholders)}"
            )
        
        return validation_results
    
    def prepare_for_db_migration(self) -> Dict[str, Any]:
        """
        DB 마이그레이션을 위한 데이터 준비
        
        Returns:
            DB에 삽입할 수 있는 형태로 변환된 데이터
        """
        if not self.loaded_data:
            self.load_all_files()
        
        migration_data = {
            "indicators": [],
            "parameters": [],
            "categories": [],
            "help_texts": [],
            "placeholders": [],
            "metadata": {
                "source": "data_info_yaml",
                "converted_at": datetime.now().isoformat(),
                "data_info_path": self.data_info_path
            }
        }
        
        # 지표 라이브러리 → DB 형태 변환
        indicator_lib = self.get_indicator_library()
        for indicator_id, indicator_info in indicator_lib.get('indicators', {}).items():
            db_indicator = {
                "variable_id": indicator_id,
                "display_name_ko": indicator_info.get('display_name_ko', ''),
                "display_name_en": indicator_info.get('display_name_en', ''),
                "purpose_category": indicator_info.get('category', 'momentum'),
                "chart_category": indicator_info.get('chart_category', 'subplot'),
                "description": indicator_info.get('description', ''),
                "is_active": 1
            }
            migration_data["indicators"].append(db_indicator)
        
        # 도움말 텍스트 → DB 형태 변환
        help_texts = self.get_help_texts()
        for param_name, help_text in help_texts.get('parameter_help_texts', {}).items():
            migration_data["help_texts"].append({
                "parameter_name": param_name,
                "help_text": help_text
            })
        
        # 플레이스홀더 → DB 형태 변환
        placeholder_texts = self.get_placeholder_texts()
        for indicator_id, placeholder_info in placeholder_texts.get('indicators', {}).items():
            migration_data["placeholders"].append({
                "variable_id": indicator_id,
                "basic_usage": placeholder_info.get('basic_usage', ''),
                "advanced_usage": placeholder_info.get('advanced_usage', ''),
                "scenarios": yaml.dump(placeholder_info.get('scenarios', {}), default_flow_style=False)
            })
        
        return migration_data


# ===== 편의 함수들 =====

def load_data_info(data_info_path: str = None) -> Dict[str, Any]:
    """data_info 로드 편의 함수"""
    loader = DataInfoLoader(data_info_path)
    return loader.load_all_files()

def get_data_info_summary(data_info_path: str = None) -> Dict[str, Any]:
    """data_info 요약 정보 조회 편의 함수"""
    loader = DataInfoLoader(data_info_path)
    return loader.get_summary()

def validate_data_info(data_info_path: str = None) -> Dict[str, Any]:
    """data_info 검증 편의 함수"""
    loader = DataInfoLoader(data_info_path)
    return loader.validate_data_integrity()

def is_data_info_available(data_info_path: str = None) -> bool:
    """data_info 사용 가능 여부 확인"""
    loader = DataInfoLoader(data_info_path)
    summary = loader.get_summary()
    return summary["path_exists"] and len(summary["data_counts"]) > 0
