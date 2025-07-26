"""
트레이딩 지표 자동 분류 시스템

SmartIndicatorClassifier:
- 30개 지표 패턴 학습 기반 지능형 분류
- 키워드 매칭 점수 시스템으로 신뢰도 측정
- 신뢰도 70% 이하 시 수동 확인 권장
- 일괄 추가 기능으로 인기 지표 자동 등록

사용법:
    classifier = SmartIndicatorClassifier()
    result = classifier.classify_indicator('Hull Moving Average')
    classifier.add_new_indicator('HULL_MA', '헐 이동평균', '매우 부드러운 이동평균')
"""

import re
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class SmartIndicatorClassifier:
    """새로운 지표의 카테고리 자동 분류 (30개 지표 학습 기반)"""
    
    def __init__(self):
        # 학습된 키워드 패턴 (30개 지표 분석 결과)
        self.trend_keywords = [
            'ma', 'average', 'moving', 'bollinger', 'ichimoku', 'parabolic', 'sar',
            'adx', 'aroon', 'supertrend', 'pivot', 'trend', 'hull', 'alma', 'dema', 'tema'
        ]
        
        self.momentum_keywords = [
            'rsi', 'stoch', 'cci', 'momentum', 'williams', 'roc', 'macd',
            'mfi', 'squeeze', 'oscillator', 'strength', 'awesome', 'tsi'
        ]
        
        self.volatility_keywords = [
            'atr', 'volatility', 'width', 'deviation', 'standard', 'true range',
            'keltner', 'channel', 'bands'
        ]
        
        self.volume_keywords = [
            'volume', 'obv', 'vwap', 'profile', 'flow', 'balance', 'weighted',
            'money flow', 'accumulation', 'distribution'
        ]
        
        self.price_keywords = [
            'price', 'open', 'high', 'low', 'close', 'current', 'ohlc', 'hlc'
        ]
        
        self.support_resistance_keywords = [
            'pivot', 'support', 'resistance', 'fibonacci', 'level', 'zone'
        ]
        
        # 특별 패턴 (정확한 매칭)
        self.special_patterns = {
            'rsi': 'momentum',
            'stochastic': 'momentum', 
            'macd': 'momentum',
            'bollinger': 'trend',
            'moving average': 'trend',
            'volume': 'volume',
            'price': 'price',
            'pivot': 'support_resistance'
        }
    
    def classify_indicator(self, name: str, description: str = '') -> Dict[str, any]:
        """30개 지표 패턴 기반 지능형 분류"""
        name_lower = name.lower()
        desc_lower = description.lower()
        combined_text = f"{name_lower} {desc_lower}"
        
        # 1. 특별 패턴 우선 확인
        for pattern, category in self.special_patterns.items():
            if pattern in combined_text:
                return self._build_classification_result(
                    category, name_lower, confidence=0.95
                )
        
        # 2. 키워드 매칭 점수 계산
        scores = {
            'trend': self._calculate_keyword_score(combined_text, self.trend_keywords),
            'momentum': self._calculate_keyword_score(combined_text, self.momentum_keywords),
            'volatility': self._calculate_keyword_score(combined_text, self.volatility_keywords),
            'volume': self._calculate_keyword_score(combined_text, self.volume_keywords),
            'price': self._calculate_keyword_score(combined_text, self.price_keywords),
            'support_resistance': self._calculate_keyword_score(combined_text, self.support_resistance_keywords)
        }
        
        # 3. 최고 점수 카테고리 선택
        max_score = max(scores.values())
        if max_score == 0:
            # 키워드 매칭이 없으면 기본값
            purpose_category = 'momentum'
            confidence = 0.5
        else:
            purpose_category = max(scores.items(), key=lambda x: x[1])[0]
            total_score = sum(scores.values())
            confidence = (max_score / total_score) if total_score > 0 else 0.5
        
        return self._build_classification_result(
            purpose_category, name_lower, confidence, scores
        )
    
    def _calculate_keyword_score(self, text: str, keywords: List[str]) -> int:
        """키워드 매칭 점수 계산"""
        score = 0
        for keyword in keywords:
            if keyword in text:
                # 정확한 단어 매칭에 더 높은 점수
                if re.search(rf'\b{re.escape(keyword)}\b', text):
                    score += 2
                else:
                    score += 1
        return score
    
    def _build_classification_result(self, purpose_category: str, name_lower: str, 
                                   confidence: float, keyword_scores: Dict[str, int] = None) -> Dict[str, any]:
        """분류 결과 구성"""
        
        # 4. 차트 카테고리 결정
        overlay_indicators = ['trend', 'price', 'support_resistance']
        if purpose_category in overlay_indicators:
            chart_category = 'overlay'
        elif purpose_category == 'volume' and any(kw in name_lower for kw in ['profile', 'vwap']):
            chart_category = 'overlay'  # 특정 거래량 지표는 overlay
        else:
            chart_category = 'subplot'
        
        # 5. 비교 그룹 결정 (30개 지표 분석 기반)
        comparison_group = self._determine_comparison_group(purpose_category, name_lower)
        
        # 6. 신뢰도 보정 (베이스 신뢰도 추가)
        adjusted_confidence = min(confidence + 0.3, 1.0)
        
        return {
            'purpose_category': purpose_category,
            'chart_category': chart_category,
            'comparison_group': comparison_group,
            'confidence': adjusted_confidence,
            'keyword_matches': keyword_scores or {},
            'name_analyzed': name_lower
        }
    
    def _determine_comparison_group(self, purpose_category: str, name_lower: str) -> str:
        """비교 그룹 결정"""
        
        # RSI 계열은 percentage_comparable
        if any(kw in name_lower for kw in ['rsi', 'stoch', 'williams', 'mfi']):
            return 'percentage_comparable'
        
        # 센터라인 오실레이터는 centered_oscillator  
        elif any(kw in name_lower for kw in ['cci', 'roc', 'macd', 'squeeze', 'awesome']):
            return 'centered_oscillator'
        
        # 카테고리별 기본 매핑
        comparison_groups = {
            'price': 'price_comparable',
            'trend': 'price_comparable', 
            'support_resistance': 'price_comparable',
            'volume': 'volume_comparable',
            'volatility': 'volatility_comparable',
            'momentum': 'percentage_comparable'  # 기본값
        }
        
        # 특별한 거래량 지표들
        if purpose_category == 'volume':
            if 'profile' in name_lower:
                return 'volume_distribution'
            elif any(kw in name_lower for kw in ['obv', 'flow']):
                return 'volume_flow'
            else:
                return 'volume_comparable'
        
        return comparison_groups.get(purpose_category, 'signal_conditional')
    
    def add_new_indicator(self, variable_id: str, display_name: str, description: str = '') -> bool:
        """새 지표 자동 분류 후 DB 추가 (검증 포함)"""
        
        # 분류 실행
        classification = self.classify_indicator(display_name, description)
        
        # 분류 결과 출력
        print(f"🔍 {display_name} 지표 분석 결과:")
        if classification['keyword_matches']:
            print(f"   키워드 매칭: {classification['keyword_matches']}")
        print(f"   신뢰도: {classification['confidence']:.1%}")
        print(f"   용도: {classification['purpose_category']}")
        print(f"   차트: {classification['chart_category']}")
        print(f"   비교: {classification['comparison_group']}")
        
        # 낮은 신뢰도 경고
        if classification['confidence'] < 0.7:
            print(f"⚠️  신뢰도가 낮습니다 ({classification['confidence']:.1%}). 수동 확인 권장.")
        
        # DB에 추가 시도
        try:
            from .variable_manager import SimpleVariableManager
            
            with SimpleVariableManager() as vm:
                success = vm.add_variable(
                    variable_id=variable_id,
                    display_name_ko=display_name,
                    display_name_en='',  # 영어명은 나중에 추가 가능
                    purpose_category=classification['purpose_category'],
                    chart_category=classification['chart_category'], 
                    comparison_group=classification['comparison_group'],
                    description=description,
                    source='auto_classified',
                    is_active=False  # 비활성 상태로 추가
                )
                
                if success:
                    print(f"✅ DB 추가 완료! activate_variable('{variable_id}')로 활성화 가능")
                    return True
                else:
                    print(f"❌ DB 추가 실패 (중복 ID일 가능성)")
                    return False
                    
        except ImportError:
            print("❌ SimpleVariableManager를 가져올 수 없습니다")
            return False
        except Exception as e:
            print(f"❌ DB 추가 실패: {e}")
            return False
    
    def batch_add_popular_indicators(self) -> int:
        """인기 지표들 일괄 추가"""
        
        popular_indicators = [
            ('HULL_MA', '헐 이동평균', '매우 부드럽고 반응이 빠른 이동평균'),
            ('KELTNER_CHANNEL', '켈트너 채널', '이동평균과 ATR로 만든 변동성 채널'),
            ('AWESOME_OSCILLATOR', '어썸 오실레이터', '5기간과 34기간 SMA의 차이를 막대그래프로 표시'),
            ('TRUE_STRENGTH_INDEX', 'TSI 지표', '이중 평활화된 모멘텀 지표'),
            ('ULTIMATE_OSCILLATOR', '궁극적 오실레이터', '단기, 중기, 장기 사이클을 모두 반영'),
            ('CHANDE_MOMENTUM', '찬드 모멘텀 오실레이터', '순수 모멘텀 측정 지표'),
            ('COMMODITY_CHANNEL_INDEX', 'CCI 지표', '현재 가격이 평균 가격과 얼마나 떨어져 있는지 측정'),
            ('MONEY_FLOW_INDEX', 'MFI 지표', '거래량을 고려한 RSI로 자금 흐름을 측정'),
            ('RATE_OF_CHANGE', 'ROC 지표', '현재 가격과 n일 전 가격의 변화율을 측정'),
            ('TRIPLE_EMA', '3중 지수이동평균', '지수 이동평균을 세 번 적용하여 지연을 최소화')
        ]
        
        success_count = 0
        print("🚀 인기 지표 일괄 추가 시작...")
        
        for var_id, name, desc in popular_indicators:
            print(f"\n📊 처리 중: {name}")
            if self.add_new_indicator(var_id, name, desc):
                success_count += 1
        
        print(f"\n🎯 {success_count}/{len(popular_indicators)}개 지표 추가 완료!")
        return success_count
    
    def analyze_existing_indicators(self) -> Dict[str, any]:
        """기존 지표들의 분류 정확도 분석"""
        try:
            from .variable_manager import SimpleVariableManager
            
            with SimpleVariableManager() as vm:
                all_vars = vm.get_all_variables()
                
                analysis = {
                    'total_analyzed': len(all_vars),
                    'high_confidence': 0,  # 70% 이상
                    'medium_confidence': 0,  # 50-70%
                    'low_confidence': 0,  # 50% 미만
                    'accuracy_by_category': {},
                    'reclassification_suggestions': []
                }
                
                for var in all_vars:
                    # 기존 변수를 다시 분류해보기
                    result = self.classify_indicator(
                        var['display_name_ko'], 
                        var.get('description', '')
                    )
                    
                    confidence = result['confidence']
                    if confidence >= 0.7:
                        analysis['high_confidence'] += 1
                    elif confidence >= 0.5:
                        analysis['medium_confidence'] += 1
                    else:
                        analysis['low_confidence'] += 1
                    
                    # 분류가 다른 경우 제안
                    if result['purpose_category'] != var['purpose_category']:
                        analysis['reclassification_suggestions'].append({
                            'variable_id': var['variable_id'],
                            'name': var['display_name_ko'],
                            'current': var['purpose_category'],
                            'suggested': result['purpose_category'],
                            'confidence': confidence
                        })
                
                return analysis
                
        except Exception as e:
            logger.error(f"기존 지표 분석 실패: {e}")
            return {}
    
    def get_classification_stats(self) -> Dict[str, List[str]]:
        """분류 시스템 통계"""
        return {
            'trend_keywords': self.trend_keywords,
            'momentum_keywords': self.momentum_keywords,
            'volatility_keywords': self.volatility_keywords,
            'volume_keywords': self.volume_keywords,
            'price_keywords': self.price_keywords,
            'support_resistance_keywords': self.support_resistance_keywords,
            'special_patterns': list(self.special_patterns.keys())
        }


if __name__ == "__main__":
    # 기본 테스트
    print("🧪 SmartIndicatorClassifier 기본 테스트")
    
    classifier = SmartIndicatorClassifier()
    
    # 테스트 케이스들
    test_cases = [
        ("Hull Moving Average", "매우 부드럽고 반응이 빠른 이동평균"),
        ("Relative Strength Index", "과매수/과매도를 측정하는 모멘텀 지표"),
        ("Volume Profile", "가격대별 거래량 분포"),
        ("Average True Range", "변동성을 측정하는 지표"),
        ("Pivot Point", "지지/저항 레벨 계산")
    ]
    
    print("\n🔍 테스트 케이스 분류:")
    for name, desc in test_cases:
        print(f"\n📊 {name}:")
        result = classifier.classify_indicator(name, desc)
        print(f"  카테고리: {result['purpose_category']}")
        print(f"  차트: {result['chart_category']}")
        print(f"  비교: {result['comparison_group']}")
        print(f"  신뢰도: {result['confidence']:.1%}")
    
    print("\n✅ 테스트 완료!")
