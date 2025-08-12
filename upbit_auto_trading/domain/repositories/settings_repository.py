#!/usr/bin/env python3
"""
설정 데이터 Repository 인터페이스 (읽기 전용)
==============================================

settings.sqlite3 데이터베이스의 읽기 전용 접근을 위한 Repository 인터페이스입니다.
매매 변수 정의, 파라미터, 호환성 규칙 등 시스템 설정 데이터에 대한 추상화된 접근을 제공합니다.

Design Principles:
- Read-Only Interface: settings.sqlite3의 불변성 반영
- Domain Entity Mapping: TradingVariable 도메인 엔티티와 완전 호환
- 3중 카테고리 지원: purpose_category, chart_category, comparison_group 시스템 지원
- Business Logic Abstraction: 데이터베이스 구현 세부사항으로부터 도메인 로직 분리

Mapped Tables:
- tv_trading_variables: 매매 변수 정의
- tv_variable_parameters: 변수별 파라미터 정의
- tv_indicator_categories: 지표 카테고리 정보
- tv_help_texts: 도움말 텍스트
- tv_comparison_groups: 비교 그룹 규칙 (YAML 매핑)
- cfg_app_settings: 애플리케이션 설정
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

# Domain Entity 및 Value Object imports
from upbit_auto_trading.domain.entities.trigger import TradingVariable
from upbit_auto_trading.domain.value_objects.compatibility_rules import ComparisonGroupRules

class SettingsRepository(ABC):
    """
    설정 데이터 접근을 위한 Repository 인터페이스 (읽기 전용)
    
    settings.sqlite3의 매매 변수 정의, 파라미터, 호환성 규칙 등에 대한
    도메인 중심의 추상화된 접근을 제공합니다.
    
    주요 특징:
    - 읽기 전용: settings 데이터의 불변성 보장
    - 도메인 엔티티 매핑: TradingVariable 객체로 반환
    - 3중 카테고리 지원: 호환성 검증을 위한 카테고리 기반 조회
    - 성능 최적화: 캐싱 및 효율적인 조회 메서드 제공
    """

    # ===================================
    # 매매 변수 조회 메서드
    # ===================================

    @abstractmethod
    def get_trading_variables(self) -> List[TradingVariable]:
        """
        모든 활성 매매 변수 정의 조회
        
        Returns:
            List[TradingVariable]: 활성화된 모든 매매 변수 엔티티 목록
            
        Example:
            variables = settings_repo.get_trading_variables()
            # [TradingVariable(variable_id='SMA', ...), TradingVariable(variable_id='RSI', ...)]
        """
        pass

    @abstractmethod
    def find_trading_variable_by_id(self, variable_id: str) -> Optional[TradingVariable]:
        """
        변수 ID로 매매 변수 조회
        
        Args:
            variable_id: 조회할 변수 ID (예: 'SMA', 'RSI', 'MACD')
            
        Returns:
            Optional[TradingVariable]: 해당 변수 엔티티 또는 None
            
        Example:
            sma_variable = settings_repo.find_trading_variable_by_id('SMA')
            if sma_variable:
                print(f"SMA 지표: {sma_variable.display_name}")
        """
        pass

    @abstractmethod
    def get_trading_variables_by_category(self, purpose_category: str) -> List[TradingVariable]:
        """
        목적 카테고리별 매매 변수 조회
        
        Args:
            purpose_category: 목적 카테고리 ('trend', 'momentum', 'volatility', 'volume', 'price')
            
        Returns:
            List[TradingVariable]: 해당 카테고리의 변수 목록
            
        Example:
            trend_variables = settings_repo.get_trading_variables_by_category('trend')
            # [SMA, EMA, Bollinger Bands 등 추세 지표들]
        """
        pass

    @abstractmethod
    def get_trading_variables_by_chart_category(self, chart_category: str) -> List[TradingVariable]:
        """
        차트 카테고리별 매매 변수 조회
        
        Args:
            chart_category: 차트 카테고리 ('overlay', 'subplot')
            
        Returns:
            List[TradingVariable]: 해당 차트 카테고리의 변수 목록
            
        Example:
            overlay_variables = settings_repo.get_trading_variables_by_chart_category('overlay')
            # [SMA, EMA, Bollinger Bands 등 차트 오버레이 지표들]
        """
        pass

    @abstractmethod
    def get_trading_variables_by_comparison_group(self, comparison_group: str) -> List[TradingVariable]:
        """
        비교 그룹별 매매 변수 조회
        
        Args:
            comparison_group: 비교 그룹 ('price_comparable', 'percentage_comparable', 'zero_centered', 'volume_comparable')
            
        Returns:
            List[TradingVariable]: 해당 비교 그룹의 변수 목록
            
        Example:
            price_variables = settings_repo.get_trading_variables_by_comparison_group('price_comparable')
            # [SMA, EMA, Close Price 등 가격 비교 가능한 지표들]
        """
        pass

    @abstractmethod
    def get_compatible_variables(self, variable_id: str) -> List[TradingVariable]:
        """
        특정 변수와 호환 가능한 모든 변수 조회
        
        Args:
            variable_id: 기준 변수 ID
            
        Returns:
            List[TradingVariable]: 호환 가능한 변수 목록
            
        Example:
            compatible_with_sma = settings_repo.get_compatible_variables('SMA')
            # SMA와 같은 comparison_group의 모든 변수들
        """
        pass

    # ===================================
    # 변수 파라미터 조회 메서드
    # ===================================

    @abstractmethod
    def get_variable_parameters(self, variable_id: str) -> Dict[str, Any]:
        """
        변수의 파라미터 정의 조회
        
        Args:
            variable_id: 변수 ID
            
        Returns:
            Dict[str, Any]: 파라미터 정의 딕셔너리
            
        Example:
            rsi_params = settings_repo.get_variable_parameters('RSI')
            # {
            #     'period': {'type': 'integer', 'default': 14, 'min': 2, 'max': 100},
            #     'source': {'type': 'enum', 'default': 'close', 'values': ['open', 'high', 'low', 'close']}
            # }
        """
        pass

    @abstractmethod
    def get_parameter_definition(self, variable_id: str, parameter_name: str) -> Optional[Dict[str, Any]]:
        """
        특정 파라미터의 상세 정의 조회
        
        Args:
            variable_id: 변수 ID
            parameter_name: 파라미터 이름
            
        Returns:
            Optional[Dict[str, Any]]: 파라미터 정의 또는 None
            
        Example:
            period_def = settings_repo.get_parameter_definition('RSI', 'period')
            # {'type': 'integer', 'default': 14, 'min': 2, 'max': 100, 'required': True}
        """
        pass

    @abstractmethod
    def get_required_parameters(self, variable_id: str) -> List[str]:
        """
        변수의 필수 파라미터 목록 조회
        
        Args:
            variable_id: 변수 ID
            
        Returns:
            List[str]: 필수 파라미터 이름 목록
            
        Example:
            required = settings_repo.get_required_parameters('RSI')
            # ['period']  (RSI는 period가 필수)
        """
        pass

    # ===================================
    # 호환성 규칙 조회 메서드
    # ===================================

    @abstractmethod
    def get_compatibility_rules(self) -> ComparisonGroupRules:
        """
        3중 카테고리 호환성 규칙 조회
        
        Returns:
            ComparisonGroupRules: 호환성 검증을 위한 규칙 Value Object
            
        Example:
            rules = settings_repo.get_compatibility_rules()
            is_compatible = rules.check_compatibility('price_comparable', 'percentage_comparable')
        """
        pass

    @abstractmethod
    def get_comparison_groups(self) -> Dict[str, Dict[str, Any]]:
        """
        모든 비교 그룹 정보 조회
        
        Returns:
            Dict[str, Dict[str, Any]]: 비교 그룹별 메타데이터
            
        Example:
            groups = settings_repo.get_comparison_groups()
            # {
            #     'price_comparable': {'name': '가격 비교 가능', 'units': ['KRW', '원'], ...},
            #     'percentage_comparable': {'name': '퍼센트 비교 가능', 'range': '0-100', ...}
            # }
        """
        pass

    @abstractmethod
    def is_variable_compatible_with(self, variable_id1: str, variable_id2: str) -> bool:
        """
        두 변수 간 호환성 확인
        
        Args:
            variable_id1: 첫 번째 변수 ID
            variable_id2: 두 번째 변수 ID
            
        Returns:
            bool: 호환 가능 여부
            
        Example:
            compatible = settings_repo.is_variable_compatible_with('SMA', 'EMA')
            # True (둘 다 price_comparable)
        """
        pass

    # ===================================
    # 지표 카테고리 조회 메서드
    # ===================================

    @abstractmethod
    def get_indicator_categories(self) -> Dict[str, List[str]]:
        """
        지표 카테고리 정보 조회
        
        Returns:
            Dict[str, List[str]]: 카테고리별 변수 ID 목록
            
        Example:
            categories = settings_repo.get_indicator_categories()
            # {
            #     'trend': ['SMA', 'EMA', 'MACD'],
            #     'momentum': ['RSI', 'Stochastic', 'CCI'],
            #     'volatility': ['BollingerBands', 'ATR']
            # }
        """
        pass

    @abstractmethod
    def get_category_metadata(self, category_type: str, category_key: str) -> Optional[Dict[str, Any]]:
        """
        특정 카테고리의 메타데이터 조회
        
        Args:
            category_type: 카테고리 타입 ('purpose', 'chart', 'comparison')
            category_key: 카테고리 키 ('trend', 'overlay', 'price_comparable' 등)
            
        Returns:
            Optional[Dict[str, Any]]: 카테고리 메타데이터 또는 None
            
        Example:
            trend_meta = settings_repo.get_category_metadata('purpose', 'trend')
            # {'name': '추세', 'description': '추세 분석 지표', 'icon': 'trend-up'}
        """
        pass

    # ===================================
    # 변수 상태 및 메타데이터 조회
    # ===================================

    @abstractmethod
    def is_variable_active(self, variable_id: str) -> bool:
        """
        변수 활성화 상태 확인
        
        Args:
            variable_id: 변수 ID
            
        Returns:
            bool: 활성화 상태 (True: 활성, False: 비활성)
            
        Example:
            active = settings_repo.is_variable_active('SMA')
            # True
        """
        pass

    @abstractmethod
    def requires_parameters(self, variable_id: str) -> bool:
        """
        변수가 파라미터를 필요로 하는지 확인
        
        Args:
            variable_id: 변수 ID
            
        Returns:
            bool: 파라미터 필요 여부
            
        Example:
            needs_params = settings_repo.requires_parameters('RSI')
            # True (RSI는 period 파라미터 필요)
        """
        pass

    @abstractmethod
    def get_variable_source(self, variable_id: str) -> Optional[str]:
        """
        변수의 출처 정보 조회
        
        Args:
            variable_id: 변수 ID
            
        Returns:
            Optional[str]: 출처 ('built-in', 'tradingview', 'custom') 또는 None
            
        Example:
            source = settings_repo.get_variable_source('SMA')
            # 'built-in'
        """
        pass

    # ===================================
    # 도움말 및 텍스트 조회 메서드
    # ===================================

    @abstractmethod
    def get_variable_help_text(self, variable_id: str) -> Optional[str]:
        """
        변수 도움말 텍스트 조회
        
        Args:
            variable_id: 변수 ID
            
        Returns:
            Optional[str]: 도움말 텍스트 또는 None
            
        Example:
            help_text = settings_repo.get_variable_help_text('RSI')
            # "RSI는 가격의 상승압력과 하락압력을 비교하여..."
        """
        pass

    @abstractmethod
    def get_parameter_help_text(self, variable_id: str, parameter_name: str) -> Optional[str]:
        """
        파라미터 도움말 텍스트 조회
        
        Args:
            variable_id: 변수 ID
            parameter_name: 파라미터 이름
            
        Returns:
            Optional[str]: 파라미터 도움말 텍스트 또는 None
            
        Example:
            help_text = settings_repo.get_parameter_help_text('RSI', 'period')
            # "RSI 계산에 사용할 기간입니다. 일반적으로 14를 사용합니다."
        """
        pass

    @abstractmethod
    def get_variable_placeholder_text(self, variable_id: str, parameter_name: str) -> Optional[str]:
        """
        파라미터 입력 필드의 플레이스홀더 텍스트 조회
        
        Args:
            variable_id: 변수 ID
            parameter_name: 파라미터 이름
            
        Returns:
            Optional[str]: 플레이스홀더 텍스트 또는 None
            
        Example:
            placeholder = settings_repo.get_variable_placeholder_text('RSI', 'period')
            # "14 (기본값)"
        """
        pass

    # ===================================
    # 애플리케이션 설정 조회 메서드
    # ===================================

    @abstractmethod
    def get_app_settings(self) -> Dict[str, Any]:
        """
        애플리케이션 설정 조회
        
        Returns:
            Dict[str, Any]: 설정 키-값 딕셔너리
            
        Example:
            settings = settings_repo.get_app_settings()
            # {'theme': 'dark', 'language': 'ko', 'auto_save': True}
        """
        pass

    @abstractmethod
    def get_app_setting(self, key: str) -> Optional[str]:
        """
        특정 애플리케이션 설정값 조회
        
        Args:
            key: 설정 키
            
        Returns:
            Optional[str]: 설정값 또는 None
            
        Example:
            theme = settings_repo.get_app_setting('theme')
            # 'dark'
        """
        pass

    @abstractmethod
    def get_system_settings(self) -> Dict[str, Any]:
        """
        시스템 설정 조회
        
        Returns:
            Dict[str, Any]: 시스템 설정 딕셔너리
            
        Example:
            sys_settings = settings_repo.get_system_settings()
            # {'max_memory_usage': '1GB', 'cache_size': '100MB'}
        """
        pass

    # ===================================
    # 통계 및 메타데이터 조회 메서드
    # ===================================

    @abstractmethod
    def get_variables_count(self) -> int:
        """
        활성 변수 총 개수 조회
        
        Returns:
            int: 활성 변수 개수
            
        Example:
            count = settings_repo.get_variables_count()
            # 15 (활성 상태인 변수 15개)
        """
        pass

    @abstractmethod
    def get_variables_count_by_category(self, purpose_category: str) -> int:
        """
        카테고리별 변수 개수 조회
        
        Args:
            purpose_category: 목적 카테고리
            
        Returns:
            int: 해당 카테고리의 변수 개수
            
        Example:
            trend_count = settings_repo.get_variables_count_by_category('trend')
            # 5 (추세 지표 5개)
        """
        pass

    @abstractmethod
    def get_available_categories(self) -> Dict[str, List[str]]:
        """
        사용 가능한 모든 카테고리 조회
        
        Returns:
            Dict[str, List[str]]: 카테고리 타입별 사용 가능한 카테고리 목록
            
        Example:
            categories = settings_repo.get_available_categories()
            # {
            #     'purpose': ['trend', 'momentum', 'volatility', 'volume', 'price'],
            #     'chart': ['overlay', 'subplot'],
            #     'comparison': ['price_comparable', 'percentage_comparable', 'zero_centered']
            # }
        """
        pass

    @abstractmethod
    def search_variables(self, query: str) -> List[TradingVariable]:
        """
        변수 이름이나 설명으로 검색
        
        Args:
            query: 검색 쿼리 (변수 ID, 표시 이름, 설명에서 검색)
            
        Returns:
            List[TradingVariable]: 검색 결과 변수 목록
            
        Example:
            results = settings_repo.search_variables('평균')
            # [SMA(단순이동평균), EMA(지수이동평균), ...] 
        """
        pass
