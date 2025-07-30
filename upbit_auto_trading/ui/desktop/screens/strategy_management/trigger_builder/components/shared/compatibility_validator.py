#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DB 기반 통합 호환성 검증기 (CompatibilityValidator) - 변수 간 의미론적 호환성 검증
====================================================================================

🚀 **DB 기반 설계**: 모든 데이터를 upbit_auto_trading/data/settings.sqlite3에서 실시간 로드
- 하드코딩 제거: 모든 지표 정보를 DB에서 동적으로 가져옴
- 실시간 반영: DB 변경 시 즉시 적용, 코드 수정 불필요
- 전역 DB 매니저: upbit_auto_trading/data/settings.sqlite3 활용

역할: 변수 간 비교가 논리적으로 의미있는지 검증
- DB 기반 호환성 규칙 (comparison_group 기반 자동 판정)
- 레거시 시스템과의 호환성 유지
- 대안 제안 및 신뢰도 점수 계산

호환성 예시:
- ✅ RSI ↔ 스토캐스틱 (같은 percentage_comparable 그룹)
- ✅ 현재가 ↔ 단순이동평균 (같은 price_comparable 그룹)
- ❌ RSI ↔ SMA (percentage_comparable ≠ price_comparable)
- ❌ 현재가 ↔ 거래량 (price_comparable ≠ volume_comparable)

검증 시점: 변수 선택 및 조합 시 실시간 호환성 체크
"""

from typing import Dict, List, Tuple, Any
from enum import Enum
import logging
import sqlite3
import os


class VariableType(Enum):
    """변수 타입 분류 (레거시 호환용)"""
    PRICE = "price"
    PRICE_INDICATOR = "price_indicator"
    OSCILLATOR = "oscillator"
    MOMENTUM = "momentum"
    VOLUME = "volume"
    VOLATILITY = "volatility"
    FINANCIAL = "financial"
    CUSTOM = "custom"


class ScaleType(Enum):
    """척도 타입 분류 (레거시 호환용)"""
    PRICE_SCALE = "price_scale"
    PERCENT_SCALE = "percent_scale"
    VOLUME_SCALE = "volume_scale"
    RATIO_SCALE = "ratio_scale"
    NORMALIZED = "normalized"


class CompatibilityValidator:
    """DB 기반 통합 호환성 검증기 - 모든 정보를 DB에서 실시간 로드"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # DB 연결 상태 추적
        self.db_connection_status = "unknown"
        self.db_error_message = ""
        
        self.db_path = self._get_app_settings_db_path()
        
        # 초기화 시 DB 상태 검증
        self._validate_database_status()
    
    def _get_app_settings_db_path(self) -> str:
        """전역 DB 매니저에서 제공하는 정확한 경로 사용"""
        try:
            # 전역 DB 매니저에서 tv_trading_variables 테이블에 대한 DB 경로 가져오기
            from upbit_auto_trading.utils.global_db_manager import get_db_path
            db_path = get_db_path('tv_trading_variables')
            self.db_connection_status = "global_manager_success"
            return str(db_path)
        except Exception as e:
            self.logger.error(f"전역 DB 매니저 경로 가져오기 실패: {e}")
            self.db_connection_status = "global_manager_failed"
            self.db_error_message = f"전역 DB 매니저 오류: {str(e)}"
            # 폴백: 하드코딩된 기본 경로
            return "upbit_auto_trading/data/settings.sqlite3"
    
    def _validate_database_status(self):
        """데이터베이스 상태를 검증하고 사용자에게 알릴 준비"""
        if not os.path.exists(self.db_path):
            self.db_connection_status = "file_missing"
            self.db_error_message = f"데이터베이스 파일이 없습니다: {self.db_path}"
            return
        
        # 테이블 존재 여부 확인
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tv_trading_variables'")
            if not cursor.fetchone():
                self.db_connection_status = "table_missing"
                self.db_error_message = f"필수 테이블 'tv_trading_variables'가 없습니다: {self.db_path}"
            else:
                # 데이터 존재 여부 확인
                cursor.execute("SELECT COUNT(*) FROM tv_trading_variables WHERE is_active = 1")
                count = cursor.fetchone()[0]
                if count == 0:
                    self.db_connection_status = "data_empty"
                    self.db_error_message = "tv_trading_variables 테이블에 활성 데이터가 없습니다"
                else:
                    self.db_connection_status = "healthy"
                    self.db_error_message = ""
            conn.close()
        except Exception as e:
            self.db_connection_status = "connection_error"
            self.db_error_message = f"데이터베이스 연결 오류: {str(e)}"
    
    def get_database_status(self) -> Tuple[str, str]:
        """현재 데이터베이스 상태 반환 (UI에서 사용자에게 표시용)"""
        status_messages = {
            "healthy": ("정상", "데이터베이스가 정상적으로 연결되었습니다."),
            "global_manager_failed": ("경고", f"전역 DB 매니저 사용 불가: {self.db_error_message}"),
            "file_missing": ("오류", f"데이터베이스 파일 없음: {self.db_error_message}"),
            "table_missing": ("오류", f"필수 테이블 없음: {self.db_error_message}"),
            "data_empty": ("경고", f"데이터 없음: {self.db_error_message}"),
            "connection_error": ("오류", f"연결 실패: {self.db_error_message}"),
            "unknown": ("알 수 없음", "데이터베이스 상태를 확인할 수 없습니다.")
        }
        
        level, message = status_messages.get(self.db_connection_status, status_messages["unknown"])
        return level, message
    
    def _execute_db_query(self, query: str, params: tuple = ()) -> List[tuple]:
        """DB 쿼리 실행 (DB 존재 여부 검증 포함)"""
        # DB 파일 존재 여부 먼저 확인
        if not os.path.exists(self.db_path):
            self.logger.error(f"전역 DB 경로에 데이터베이스가 없습니다: {self.db_path}")
            return []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # tv_trading_variables 테이블 존재 여부 확인
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tv_trading_variables'")
            if not cursor.fetchone():
                self.logger.error(f"필수 테이블 'tv_trading_variables'가 존재하지 않습니다: {self.db_path}")
                conn.close()
                return []
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            conn.close()
            return results
            
        except Exception as e:
            self.logger.error(f"DB 쿼리 실행 오류: {e}")
            return []
    
    def _normalize_variable_id(self, var_id: str) -> str:
        """UI에서 전달되는 변수 이름을 DB의 실제 variable_id로 변환"""
        # 공통 변수 ID 매핑 테이블
        id_mapping = {
            # 스토캐스틱 관련 매핑
            'STOCHASTIC': 'STOCH',
            'stochastic': 'STOCH',
            '스토캐스틱': 'STOCH',
            
            # 기타 일반적인 매핑들
            'RSI_INDICATOR': 'RSI',
            'rsi_indicator': 'RSI',
            'RSI지표': 'RSI',
            
            'SIMPLE_MOVING_AVERAGE': 'SMA',
            'simple_moving_average': 'SMA',
            '단순이동평균': 'SMA',
            
            'EXPONENTIAL_MOVING_AVERAGE': 'EMA',
            'exponential_moving_average': 'EMA',
            '지수이동평균': 'EMA',
            
            'BOLLINGER_BANDS': 'BOLLINGER_BAND',
            'bollinger_bands': 'BOLLINGER_BAND',
            '볼린저밴드': 'BOLLINGER_BAND',
            
            'MACD_INDICATOR': 'MACD',
            'macd_indicator': 'MACD',
            'MACD지표': 'MACD',
            
            'CURRENT_PRICE': 'CURRENT_PRICE',
            'current_price': 'CURRENT_PRICE',
            '현재가': 'CURRENT_PRICE',
            
            'TRADING_VOLUME': 'VOLUME',
            'trading_volume': 'VOLUME',
            '거래량': 'VOLUME',
        }
        
        # 매핑 테이블에서 찾기
        normalized_id = id_mapping.get(var_id, var_id)
        
        # 매핑된 경우 로그 출력
        if normalized_id != var_id:
            self.logger.info(f"변수 ID 정규화: '{var_id}' -> '{normalized_id}'")
        
        return normalized_id
    
    def validate_compatibility(self, var1_id: str, var2_id: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        두 변수의 호환성을 DB 기반으로 검증
        
        Returns:
            Tuple[bool, str, Dict]: (호환 여부, 이유, 상세 정보)
        """
        # 🔧 변수 ID 정규화 (UI -> DB 매핑)
        original_var1_id = var1_id
        original_var2_id = var2_id
        var1_id = self._normalize_variable_id(var1_id)
        var2_id = self._normalize_variable_id(var2_id)
        
        # 정규화 결과 로깅
        if var1_id != original_var1_id or var2_id != original_var2_id:
            print(f"🔄 변수 ID 정규화: ({original_var1_id}, {original_var2_id}) -> ({var1_id}, {var2_id})")
        
        # 먼저 DB 상태 확인하여 사용자에게 명확한 피드백 제공
        if self.db_connection_status != "healthy":
            level, status_message = self.get_database_status()
            return False, f"❌ 데이터베이스를 찾을 수 없습니다: {status_message}", {
                'confidence_score': 0.0,
                'source': 'database_unavailable',
                'error': status_message,
                'db_status': self.db_connection_status,
                'requires_db_fix': True,
                'ui_status': 'error',  # UI 색상 제어용
                'status_color': 'red'  # 빨간색 상자 표시
            }
        
        try:
            # 🔧 같은 변수끼리 비교하는 경우 특별 처리
            if var1_id == var2_id:
                # 단일 변수 정보 조회
                results = self._execute_db_query("""
                    SELECT variable_id, display_name_ko, comparison_group, purpose_category
                    FROM tv_trading_variables
                    WHERE variable_id = ? AND is_active = 1
                """, (var1_id,))
                
                if not results:
                    return False, f"❌ 변수 정보를 데이터베이스에서 찾을 수 없습니다 ({var1_id})", {
                        'confidence_score': 0.0,
                        'source': 'variable_not_found',
                        'error': f"변수 '{var1_id}' 조회 실패 또는 비활성 상태",
                        'requires_db_fix': True,
                        'ui_status': 'warning',  # UI 색상 제어용
                        'status_color': 'yellow'  # 노란색 상자 표시
                    }
                
                # 같은 변수는 항상 호환 가능
                var_info = results[0]
                return True, f"✅ 동일 변수 (그룹: {var_info[2]})", {
                    'confidence_score': 100.0,
                    'var1_info': {
                        'id': var_info[0],
                        'name': var_info[1],
                        'comparison_group': var_info[2],
                        'purpose_category': var_info[3]
                    },
                    'var2_info': {
                        'id': var_info[0],
                        'name': var_info[1],
                        'comparison_group': var_info[2],
                        'purpose_category': var_info[3]
                    },
                    'source': 'database',
                    'requires_db_fix': False,
                    'ui_status': 'success',  # UI 색상 제어용
                    'status_color': 'green'  # 초록색 상자 표시
                }
            
            # DB에서 두 변수의 정보 조회
            results = self._execute_db_query("""
                SELECT variable_id, display_name_ko, comparison_group, purpose_category
                FROM tv_trading_variables
                WHERE variable_id IN (?, ?) AND is_active = 1
            """, (var1_id, var2_id))
            
            # DB 쿼리가 실패했거나 빈 결과인 경우
            if not results:
                return False, f"❌ 변수 정보를 데이터베이스에서 찾을 수 없습니다 ({var1_id}, {var2_id})", {
                    'confidence_score': 0.0,
                    'source': 'variables_not_found',
                    'error': "변수 정보 조회 실패 또는 비활성 상태",
                    'requires_db_fix': True,
                    'ui_status': 'warning',  # UI 색상 제어용
                    'status_color': 'yellow'  # 노란색 상자 표시
                }
            
            if len(results) != 2:
                missing_vars = [var1_id, var2_id]
                found_vars = [r[0] for r in results]
                missing = [v for v in missing_vars if v not in found_vars]
                return False, f"❌ 일부 변수를 데이터베이스에서 찾을 수 없습니다: {', '.join(missing)}", {
                    'confidence_score': 0.0,
                    'source': 'partial_variables_missing',
                    'error': f"누락된 변수: {missing}",
                    'found_count': len(results),
                    'required_count': 2,
                    'requires_db_fix': True,
                    'ui_status': 'warning',  # UI 색상 제어용
                    'status_color': 'yellow'  # 노란색 상자 표시
                }
            
            # 결과 파싱
            var1_info = next(r for r in results if r[0] == var1_id)
            var2_info = next(r for r in results if r[0] == var2_id)
            
            var1_group = var1_info[2]  # comparison_group
            var2_group = var2_info[2]
            
            # 호환성 판정: 같은 comparison_group이면 호환
            is_compatible = var1_group == var2_group
            
            # 상세 정보 구성
            details = {
                'confidence_score': 100.0 if is_compatible else 0.0,
                'var1_info': {
                    'id': var1_info[0],
                    'name': var1_info[1],
                    'comparison_group': var1_group,
                    'purpose_category': var1_info[3]
                },
                'var2_info': {
                    'id': var2_info[0],
                    'name': var2_info[1],
                    'comparison_group': var2_group,
                    'purpose_category': var2_info[3]
                },
                'source': 'database',
                'requires_db_fix': False,
                'ui_status': 'success' if is_compatible else 'normal',  # UI 색상 제어용
                'status_color': 'green' if is_compatible else 'default'  # 정상: 초록색, 비호환: 기본색
            }
            
            # 이유 생성
            if is_compatible:
                reason = f"✅ 호환 가능 (같은 그룹: {var1_group})"
            else:
                reason = f"❌ 호환 불가 (다른 그룹: {var1_group} ≠ {var2_group})"
            
            return is_compatible, reason, details
            
        except Exception as e:
            self.logger.error(f"DB 호환성 검증 오류: {e}")
            return False, f"❌ 데이터베이스 접근 중 오류가 발생했습니다: {str(e)}", {
                'confidence_score': 0.0,
                'source': 'database_error',
                'error': str(e),
                'requires_db_fix': True,
                'ui_status': 'error',  # UI 색상 제어용
                'status_color': 'red'  # 빨간색 상자 표시
            }
    
    def get_compatible_variables(self, target_var: str) -> List[Tuple[str, str, str]]:
        """특정 변수와 호환 가능한 모든 변수 목록 반환"""
        try:
            # 🔧 변수 ID 정규화
            normalized_target_var = self._normalize_variable_id(target_var)
            
            # 대상 변수의 comparison_group 조회
            target_results = self._execute_db_query("""
                SELECT comparison_group
                FROM tv_trading_variables
                WHERE variable_id = ? AND is_active = 1
            """, (normalized_target_var,))
            
            if not target_results:
                return []
            
            target_group = target_results[0][0]
            
            # 같은 그룹의 모든 변수 조회 (자기 제외)
            compatible_results = self._execute_db_query("""
                SELECT variable_id, display_name_ko, purpose_category
                FROM tv_trading_variables
                WHERE comparison_group = ? AND variable_id != ? AND is_active = 1
                ORDER BY variable_id
            """, (target_group, normalized_target_var))
            
            return compatible_results
            
        except Exception as e:
            self.logger.error(f"호환 변수 조회 오류: {e}")
            return []
    
    def validate_multiple_compatibility(self, variable_ids: List[str]) -> Tuple[bool, Dict[str, Any]]:
        """복수 변수들의 일괄 호환성 검증"""
        if len(variable_ids) < 2:
            return True, {'compatible_pairs': [], 'incompatible_pairs': [], 'overall_score': 100.0}
        
        compatible_pairs = []
        incompatible_pairs = []
        total_confidence = 0.0
        total_pairs = 0
        
        for i in range(len(variable_ids)):
            for j in range(i + 1, len(variable_ids)):
                var1, var2 = variable_ids[i], variable_ids[j]
                is_compatible, reason, details = self.validate_compatibility(var1, var2)
                
                confidence = details.get('confidence_score', 0.0)
                total_confidence += confidence
                total_pairs += 1
                
                if is_compatible:
                    compatible_pairs.append((var1, var2, reason, confidence))
                else:
                    incompatible_pairs.append((var1, var2, reason, confidence))
        
        overall_compatible = len(incompatible_pairs) == 0
        overall_score = total_confidence / total_pairs if total_pairs > 0 else 0.0
        
        result = {
            'compatible_pairs': compatible_pairs,
            'incompatible_pairs': incompatible_pairs,
            'overall_score': overall_score,
            'total_pairs': total_pairs
        }
        
        return overall_compatible, result
    
    def suggest_compatible_alternatives(self, target_var: str, candidate_vars: List[str], limit: int = 5) -> List[Tuple[str, float, str]]:
        """호환 가능한 대안 변수들 제안"""
        alternatives = []
        
        for candidate in candidate_vars:
            if candidate == target_var:
                continue
                
            is_compatible, reason, details = self.validate_compatibility(target_var, candidate)
            if is_compatible:
                confidence = details.get('confidence_score', 0.0)
                alternatives.append((candidate, confidence, reason))
        
        # 신뢰도 순으로 정렬하고 상위 N개 반환
        alternatives.sort(key=lambda x: x[1], reverse=True)
        return alternatives[:limit]
    
    def get_ui_status_info(self, details: Dict[str, Any]) -> Tuple[str, str, str]:
        """
        UI에서 사용할 상태 정보 반환
        
        Returns:
            Tuple[str, str, str]: (상태 레벨, 색상, 아이콘)
        """
        ui_status = details.get('ui_status', 'normal')
        status_color = details.get('status_color', 'default')
        
        status_mapping = {
            'success': ('성공', 'green', '✅'),
            'warning': ('경고', 'yellow', '⚠️'),
            'error': ('오류', 'red', '❌'),
            'normal': ('일반', 'default', '🔍')
        }
        
        level, color, icon = status_mapping.get(ui_status, status_mapping['normal'])
        return level, color, icon

    def get_compatibility_summary(self, variable_ids: List[str]) -> Dict[str, Any]:
        """변수들의 호환성 종합 분석 결과"""
        if not variable_ids:
            return {}
        
        overall_compatible, details = self.validate_multiple_compatibility(variable_ids)
        
        # 변수별 정보 수집
        variable_info = {}
        for var_id in variable_ids:
            # DB에서 정보 조회 시도
            var_results = self._execute_db_query("""
                SELECT display_name_ko, comparison_group, purpose_category
                FROM tv_trading_variables 
                WHERE variable_id = ? AND is_active = 1
            """, (var_id,))
            
            if var_results:
                variable_info[var_id] = {
                    'name': var_results[0][0],
                    'comparison_group': var_results[0][1],
                    'purpose_category': var_results[0][2],
                    'source': 'database'
                }
            else:
                # 레거시 정보로 폴백 (기본값)
                variable_info[var_id] = {
                    'legacy_category': 'unknown',
                    'source': 'legacy_fallback'
                }
        
        return {
            'overall_compatible': overall_compatible,
            'overall_score': details.get('overall_score', 0.0),
            'total_pairs': details.get('total_pairs', 0),
            'compatible_pairs': len(details.get('compatible_pairs', [])),
            'incompatible_pairs': len(details.get('incompatible_pairs', [])),
            'variable_info': variable_info,
            'incompatible_details': details.get('incompatible_pairs', [])
        }
    
    def get_all_compatibility_groups(self) -> Dict[str, List[Dict[str, str]]]:
        """모든 호환성 그룹과 포함된 변수들 반환"""
        # DB 파일 존재 여부 먼저 확인
        if not os.path.exists(self.db_path):
            self.logger.error(f"전역 DB 경로에 데이터베이스가 없습니다: {self.db_path}")
            return {
                "ERROR": [{
                    "variable_id": "DB_MISSING",
                    "display_name": "전역 DB 경로에 데이터베이스가 없습니다.",
                    "purpose_category": "error"
                }]
            }
        
        try:
            results = self._execute_db_query("""
                SELECT comparison_group, variable_id, display_name_ko, purpose_category
                FROM tv_trading_variables
                WHERE is_active = 1
                ORDER BY comparison_group, variable_id
            """)
            
            # DB 쿼리 실패하거나 테이블이 없는 경우
            if not results:
                return {
                    "ERROR": [{
                        "variable_id": "TABLE_MISSING",
                        "display_name": "tv_trading_variables 테이블이 없거나 빈 상태입니다.",
                        "purpose_category": "error"
                    }]
                }
            
            # 그룹별로 분류
            groups = {}
            for row in results:
                group, var_id, name_ko, category = row
                if group not in groups:
                    groups[group] = []
                
                groups[group].append({
                    'variable_id': var_id,
                    'display_name': name_ko,
                    'purpose_category': category
                })
            
            return groups
            
        except Exception as e:
            self.logger.error(f"호환성 그룹 조회 오류: {e}")
            return {
                "ERROR": [{
                    "variable_id": "QUERY_ERROR",
                    "display_name": f"DB 쿼리 오류: {str(e)}",
                    "purpose_category": "error"
                }]
            }


# 편의성을 위한 모듈 레벨 함수들
_validator_instance = None


def get_compatibility_validator() -> CompatibilityValidator:
    """싱글톤 호환성 검증기 인스턴스 반환"""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = CompatibilityValidator()
    return _validator_instance


def check_compatibility(var1_id: str, var2_id: str) -> Tuple[bool, str]:
    """간단한 호환성 검사 (기존 API와 호환)"""
    validator = get_compatibility_validator()
    is_compatible, reason, _ = validator.validate_compatibility(var1_id, var2_id)
    return is_compatible, reason


def check_compatibility_with_status(var1_id: str, var2_id: str) -> Tuple[int, str, str]:
    """상태 코드 기반 호환성 검사
    
    Returns:
        Tuple[int, str, str]: (상태코드, 사유, 아이콘)
        - 상태코드: 0=비호환, 1=호환, 2=DB문제
        - 사유: 상세 설명
        - 아이콘: UI 표시용 이모지
    """
    validator = get_compatibility_validator()
    
    # 먼저 DB 상태 확인
    if validator.db_connection_status != "healthy":
        return 2, validator.db_error_message, "⚠️"
    
    try:
        is_compatible, reason, details = validator.validate_compatibility(var1_id, var2_id)
        
        # DB 관련 문제인지 확인 (상세 정보에서 판단)
        ui_status = details.get('ui_status', 'normal')
        requires_db_fix = details.get('requires_db_fix', False)
        
        # DB 문제가 있으면 상태코드 2로 반환
        if requires_db_fix or ui_status == 'warning' or ui_status == 'error':
            return 2, reason, "⚠️"
        
        # 정상적인 호환성 검증 결과
        if is_compatible:
            return 1, reason, "✅"
        else:
            return 0, reason, "❌"
            
    except Exception as e:
        # 검증 중 오류 발생 시 DB 문제로 처리
        return 2, f"호환성 검증 중 오류가 발생했습니다: {str(e)}", "⚠️"


def validate_condition_variables(variable_ids: List[str]) -> bool:
    """조건에 사용된 변수들의 호환성 검증"""
    validator = get_compatibility_validator()
    is_compatible, _ = validator.validate_multiple_compatibility(variable_ids)
    return is_compatible


if __name__ == "__main__":
    # 테스트 코드
    print("🧪 DB 기반 통합 호환성 검증기 테스트")
    print("=" * 60)
    
    validator = CompatibilityValidator()
    print(f"📍 DB 경로: {validator.db_path}")
    print(f"📍 DB 존재 여부: {os.path.exists(validator.db_path)}")
    
    # 🚨 DB 상태 확인 및 사용자에게 명확한 피드백
    status_level, status_message = validator.get_database_status()
    print(f"🔍 DB 연결 상태: {status_level}")
    print(f"📋 상태 메시지: {status_message}")
    
    if validator.db_connection_status != "healthy":
        print("⚠️  경고: DB 문제가 감지되었습니다.")
        print("🔧 문제 해결: 전역 DB 매니저 설정을 확인하거나 데이터베이스 파일을 복구하세요.")
    
    print("\n" + "=" * 60)
    
    # 🔍 이동평균 관련 변수 조회 (UI 에러 분석용)
    print("\n🔍 이동평균 관련 변수 분석:")
    try:
        import sqlite3
        conn = sqlite3.connect(validator.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT variable_id, display_name_ko, display_name_en 
            FROM tv_trading_variables 
            WHERE display_name_ko LIKE '%이동평균%' OR variable_id LIKE '%MA%' 
            ORDER BY variable_id
        """)
        ma_vars = cursor.fetchall()
        for var_id, name_ko, name_en in ma_vars:
            print(f"   ID: {var_id} | 한글: {name_ko} | 영문: {name_en}")
        conn.close()
        
        # 특별 테스트: "단순이동평균" vs "SMA" 검증
        print("\n🧪 단순이동평균 문제 분석:")
        test_cases = [
            ("단순이동평균", "단순이동평균"),  # UI에서 전달되는 한글명
            ("SMA", "SMA"),                   # DB에 저장된 영문 ID
            ("단순이동평균", "SMA"),           # 혼합 케이스
        ]
        
        for var1, var2 in test_cases:
            is_compatible, reason, details = validator.validate_compatibility(var1, var2)
            level, color, icon = validator.get_ui_status_info(details)
            print(f"   {icon} {var1} ↔ {var2}: {reason}")
            print(f"      └─ UI 상태: {level} (색상: {color})")
            if not is_compatible and 'error' in details:
                print(f"      └─ 에러: {details['error']}")
                
    except Exception as e:
        print(f"   ❌ DB 조회 실패: {e}")
    
    print("\n" + "=" * 60)
    
    # 기본 테스트
    test_pairs = [
        ('RSI', 'STOCH'),           # percentage_comparable
        ('SMA', 'CURRENT_PRICE'),   # price_comparable
        ('RSI', 'SMA'),             # 다른 그룹
        ('VOLUME', 'OBV'),          # 다른 거래량 그룹
        ('MACD', 'BOLLINGER_BAND'),  # DB 테스트
        ('RSI', 'STOCHASTIC'),      # STOCHASTIC DB 문제 테스트
    ]
    
    print("\n1️⃣ 기본 호환성 테스트:")
    for var1, var2 in test_pairs:
        is_compatible, reason, details = validator.validate_compatibility(var1, var2)
        score = details.get('confidence_score', 0.0)
        source = details.get('source', 'unknown')
        requires_fix = details.get('requires_db_fix', False)
        status_icon = "�" if requires_fix else "🎯"
        print(f"{status_icon} {var1} ↔ {var2}: {is_compatible} ({score:.0f}%) - {reason} [{source}]")
        
        # DB 수정 필요 시 추가 정보 표시
        if requires_fix:
            error_detail = details.get('error', 'unknown')
            print(f"   └─ DB 문제: {error_detail}")
            print("   └─ 조치: 데이터베이스 연결 및 데이터 확인 필요")
    
    # 호환 변수 조회 테스트
    print("\n2️⃣ RSI와 호환 가능한 변수들:")
    compatible_vars = validator.get_compatible_variables('RSI')
    if compatible_vars:
        for var_id, name, category in compatible_vars[:5]:  # 상위 5개만
            print(f"   - {var_id}: {name} ({category})")
    else:
        print("   ⚠️ 호환 변수를 찾을 수 없습니다. DB 연결을 확인하세요.")
    
    # 호환성 그룹 조회
    print("\n3️⃣ 모든 호환성 그룹:")
    groups = validator.get_all_compatibility_groups()
    if "ERROR" in groups:
        print("   🚨 DB 오류로 인해 호환성 그룹을 로드할 수 없습니다:")
        for error_info in groups["ERROR"]:
            print(f"   ❌ {error_info['display_name']}")
    else:
        for group_name, variables in groups.items():
            print(f"   📊 {group_name}: {len(variables)}개 지표")
            for var in variables[:3]:  # 샘플 3개만
                print(f"      - {var['variable_id']}: {var['display_name']}")
            if len(variables) > 3:
                print(f"      ... 외 {len(variables) - 3}개")
    
    # 다중 변수 호환성 테스트
    print("\n4️⃣ 다중 변수 호환성 테스트:")
    test_groups = [
        ['RSI', 'STOCH', 'MFI'],           # 모두 percentage_comparable
        ['SMA', 'EMA', 'CURRENT_PRICE'],   # 모두 price_comparable
        ['RSI', 'SMA', 'VOLUME'],          # 서로 다른 그룹
    ]
    
    for variables in test_groups:
        is_compatible, details = validator.validate_multiple_compatibility(variables)
        score = details.get('overall_score', 0.0)
        pairs = details.get('total_pairs', 0)
        print(f"✓ {'+'.join(variables)}: {is_compatible} (점수: {score:.0f}%, 페어: {pairs}개)")
    
    print("\n✅ 테스트 완료!")
    
    # 최종 상태 요약
    if validator.db_connection_status != "healthy":
        print(f"\n🚨 주의: 현재 DB 상태가 '{validator.db_connection_status}'입니다.")
        print("📞 지원: 문제가 지속되면 시스템 관리자에게 문의하세요.")
