#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
차트 렌더링 엔진

변수 카테고리에 따른 차트 표현을 실제로 구현하는 엔진
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import numpy as np

from PyQt6.QtWidgets import QApplication

from .chart_variable_service import get_chart_variable_service, ChartLayoutInfo


class ChartRenderingEngine:
    """차트 렌더링 엔진"""

    def __init__(self):
        self.service = get_chart_variable_service()
        self.default_colors = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ]

    def render_chart(self, data: pd.DataFrame, variable_configs: List[Dict[str, Any]],
                    external_variables: Dict[str, Any] = None,
                    template_name: str = 'standard_trading') -> go.Figure:
        """
        차트 렌더링 메인 함수
        
        Args:
            data: 시계열 데이터 (timestamp, open, high, low, close, volume 포함)
            variable_configs: 표시할 변수 설정 리스트
            external_variables: 외부 변수 값들
            template_name: 레이아웃 템플릿명
        
        Returns:
            Plotly Figure 객체
        """
        start_time = datetime.now()
        
        # 변수 ID 추출
        variable_ids = [config.get('variable_id', config.get('name', '')) 
                       for config in variable_configs]
        
        # 레이아웃 정보 생성
        layout_info = self.service.get_chart_layout_info(variable_ids, template_name)
        
        # 서브플롯 생성
        fig = self._create_subplots(layout_info)
        
        # 메인 차트 (캔들스틱) 추가
        self._add_candlestick_chart(fig, data, 1)
        
        # 메인 차트 오버레이 변수들 추가
        self._add_main_chart_overlays(fig, data, layout_info.main_chart_variables, 
                                    variable_configs, external_variables)
        
        # 서브플롯 변수들 추가
        self._add_subplot_indicators(fig, data, layout_info.subplots, 
                                   variable_configs, external_variables)
        
        # 차트 스타일링
        self._apply_chart_styling(fig, layout_info)
        
        # 사용 로그 기록
        render_time = int((datetime.now() - start_time).total_seconds() * 1000)
        for var_id in variable_ids:
            self.service.register_variable_usage(
                var_id, 
                usage_context='chart_render',
                render_time_ms=render_time
            )
        
        return fig

    def _create_subplots(self, layout_info: ChartLayoutInfo) -> go.Figure:
        """서브플롯 구조 생성"""
        subplot_count = 1 + len(layout_info.subplots)
        
        # 서브플롯 제목 생성
        subplot_titles = ['가격 차트']
        for subplot in layout_info.subplots:
            subplot_titles.append(subplot['name'])
        
        # 서브플롯 생성
        fig = make_subplots(
            rows=subplot_count,
            cols=1,
            shared_xaxes=True,
            row_heights=layout_info.height_ratios,
            subplot_titles=subplot_titles,
            vertical_spacing=0.05
        )
        
        return fig

    def _add_candlestick_chart(self, fig: go.Figure, data: pd.DataFrame, row: int):
        """캔들스틱 차트 추가"""
        if 'timestamp' not in data.columns:
            # 인덱스를 timestamp로 사용
            data = data.reset_index()
            if 'index' in data.columns:
                data['timestamp'] = data['index']
        
        candlestick = go.Candlestick(
            x=data['timestamp'],
            open=data.get('open', data.get('Open', [])),
            high=data.get('high', data.get('High', [])),
            low=data.get('low', data.get('Low', [])),
            close=data.get('close', data.get('Close', [])),
            name='가격',
            showlegend=False
        )
        
        fig.add_trace(candlestick, row=row, col=1)

    def _add_main_chart_overlays(self, fig: go.Figure, data: pd.DataFrame,
                               main_variables: List[Dict[str, Any]],
                               variable_configs: List[Dict[str, Any]],
                               external_variables: Dict[str, Any] = None):
        """메인 차트 오버레이 추가"""
        if not main_variables:
            return
        
        for var_info in main_variables:
            config = var_info['config']
            var_config = self._find_variable_config(variable_configs, var_info['variable_id'])
            
            if config.display_type == 'main_line':
                self._add_line_overlay(fig, data, var_info, var_config, external_variables, 1)
            elif config.display_type == 'main_band':
                self._add_band_overlay(fig, data, var_info, var_config, external_variables, 1)
            elif config.display_type == 'main_level':
                self._add_level_overlay(fig, data, var_info, var_config, external_variables, 1)

    def _add_subplot_indicators(self, fig: go.Figure, data: pd.DataFrame,
                              subplots: List[Dict[str, Any]],
                              variable_configs: List[Dict[str, Any]],
                              external_variables: Dict[str, Any] = None):
        """서브플롯 지표들 추가"""
        for i, subplot_info in enumerate(subplots):
            row = i + 2  # 메인 차트가 1번째 행
            config = subplot_info['config']
            var_config = self._find_variable_config(variable_configs, subplot_info['variable_id'])
            
            if config.display_type == 'subplot_line':
                self._add_subplot_line(fig, data, subplot_info, var_config, external_variables, row)
            elif config.display_type == 'subplot_histogram':
                self._add_subplot_histogram(fig, data, subplot_info, var_config, external_variables, row)
            elif config.display_type == 'subplot_level':
                self._add_subplot_level(fig, data, subplot_info, var_config, external_variables, row)

    def _find_variable_config(self, variable_configs: List[Dict[str, Any]], 
                            variable_id: str) -> Optional[Dict[str, Any]]:
        """변수 설정 찾기"""
        for config in variable_configs:
            if (config.get('variable_id') == variable_id or 
                config.get('name') == variable_id):
                return config
        return None

    def _add_line_overlay(self, fig: go.Figure, data: pd.DataFrame, 
                         var_info: Dict[str, Any], var_config: Dict[str, Any],
                         external_variables: Dict[str, Any], row: int):
        """선 오버레이 추가 (이동평균 등)"""
        if not var_config:
            return
        
        # 실제 지표 계산 (예: 이동평균)
        if var_info['variable_id'] == 'moving_average':
            period = var_config.get('parameters', {}).get('period', 20)
            close_prices = data.get('close', data.get('Close', []))
            ma_values = pd.Series(close_prices).rolling(window=period).mean()
            
            fig.add_trace(
                go.Scatter(
                    x=data['timestamp'],
                    y=ma_values,
                    mode='lines',
                    name=f"이동평균({period})",
                    line=dict(color=var_info['color'], width=2),
                    showlegend=True
                ),
                row=row, col=1
            )

    def _add_band_overlay(self, fig: go.Figure, data: pd.DataFrame,
                         var_info: Dict[str, Any], var_config: Dict[str, Any],
                         external_variables: Dict[str, Any], row: int):
        """밴드 오버레이 추가 (볼린저 밴드 등)"""
        if not var_config:
            return
        
        # 볼린저 밴드 계산
        if var_info['variable_id'] == 'bollinger_band':
            period = var_config.get('parameters', {}).get('period', 20)
            std_dev = var_config.get('parameters', {}).get('std_dev', 2)
            
            close_prices = pd.Series(data.get('close', data.get('Close', [])))
            sma = close_prices.rolling(window=period).mean()
            std = close_prices.rolling(window=period).std()
            
            upper_band = sma + (std * std_dev)
            lower_band = sma - (std * std_dev)
            
            # 상단 밴드
            fig.add_trace(
                go.Scatter(
                    x=data['timestamp'],
                    y=upper_band,
                    mode='lines',
                    name='볼린저 상단',
                    line=dict(color=var_info['color'], width=1, dash='dash'),
                    showlegend=True
                ),
                row=row, col=1
            )
            
            # 하단 밴드
            fig.add_trace(
                go.Scatter(
                    x=data['timestamp'],
                    y=lower_band,
                    mode='lines',
                    name='볼린저 하단',
                    line=dict(color=var_info['color'], width=1, dash='dash'),
                    fill='tonexty',
                    fillcolor=f"rgba{(*self._hex_to_rgb(var_info['color']), 0.1)}",
                    showlegend=True
                ),
                row=row, col=1
            )

    def _add_level_overlay(self, fig: go.Figure, data: pd.DataFrame,
                          var_info: Dict[str, Any], var_config: Dict[str, Any],
                          external_variables: Dict[str, Any], row: int):
        """수평선 오버레이 추가 (고정 가격 레벨 등)"""
        if not var_config:
            return
        
        # 고정값 또는 외부변수 처리
        target_value = var_config.get('target_value')
        if target_value and target_value.replace('.', '').isdigit():
            level_value = float(target_value)
            
            fig.add_hline(
                y=level_value,
                line=dict(color=var_info['color'], width=2, dash='dot'),
                annotation_text=f"{var_info['name']}: {level_value:,.0f}",
                row=row, col=1
            )

    def _add_subplot_line(self, fig: go.Figure, data: pd.DataFrame,
                         subplot_info: Dict[str, Any], var_config: Dict[str, Any],
                         external_variables: Dict[str, Any], row: int):
        """서브플롯 선 차트 추가 (RSI, MACD 등)"""
        if not var_config:
            return
        
        var_id = subplot_info['variable_id']
        
        # RSI 계산
        if var_id == 'rsi':
            period = var_config.get('parameters', {}).get('period', 14)
            close_prices = pd.Series(data.get('close', data.get('Close', [])))
            rsi_values = self._calculate_rsi(close_prices, period)
            
            fig.add_trace(
                go.Scatter(
                    x=data['timestamp'],
                    y=rsi_values,
                    mode='lines',
                    name=f"RSI({period})",
                    line=dict(color=subplot_info['color'], width=2),
                    showlegend=True
                ),
                row=row, col=1
            )
            
            # RSI 기준선 추가 (30, 70)
            fig.add_hline(y=30, line=dict(color='red', width=1, dash='dash'), row=row, col=1)
            fig.add_hline(y=70, line=dict(color='red', width=1, dash='dash'), row=row, col=1)
        
        # MACD 계산
        elif var_id == 'macd':
            fast = var_config.get('parameters', {}).get('fast', 12)
            slow = var_config.get('parameters', {}).get('slow', 26)
            signal = var_config.get('parameters', {}).get('signal', 9)
            
            close_prices = pd.Series(data.get('close', data.get('Close', [])))
            macd_line, signal_line, histogram = self._calculate_macd(close_prices, fast, slow, signal)
            
            fig.add_trace(
                go.Scatter(
                    x=data['timestamp'],
                    y=macd_line,
                    mode='lines',
                    name='MACD',
                    line=dict(color=subplot_info['color'], width=2),
                    showlegend=True
                ),
                row=row, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=data['timestamp'],
                    y=signal_line,
                    mode='lines',
                    name='Signal',
                    line=dict(color='orange', width=1),
                    showlegend=True
                ),
                row=row, col=1
            )

    def _add_subplot_histogram(self, fig: go.Figure, data: pd.DataFrame,
                             subplot_info: Dict[str, Any], var_config: Dict[str, Any],
                             external_variables: Dict[str, Any], row: int):
        """서브플롯 히스토그램 추가 (거래량 등)"""
        if not var_config:
            return
        
        if subplot_info['variable_id'] == 'volume':
            volume_data = data.get('volume', data.get('Volume', []))
            
            fig.add_trace(
                go.Bar(
                    x=data['timestamp'],
                    y=volume_data,
                    name='거래량',
                    marker=dict(color=subplot_info['color'], opacity=0.7),
                    showlegend=True
                ),
                row=row, col=1
            )

    def _add_subplot_level(self, fig: go.Figure, data: pd.DataFrame,
                          subplot_info: Dict[str, Any], var_config: Dict[str, Any],
                          external_variables: Dict[str, Any], row: int):
        """서브플롯 수평선 추가"""
        target_value = var_config.get('target_value')
        if target_value and target_value.replace('.', '').isdigit():
            level_value = float(target_value)
            
            fig.add_hline(
                y=level_value,
                line=dict(color=subplot_info['color'], width=2, dash='dot'),
                annotation_text=f"{subplot_info['name']}: {level_value}",
                row=row, col=1
            )

    def _apply_chart_styling(self, fig: go.Figure, layout_info: ChartLayoutInfo):
        """차트 스타일링 적용"""
        # 테마 감지 - QApplication의 palette를 이용해 다크 테마 판별
        is_dark_theme = False
        try:
            if QApplication.instance():
                palette = QApplication.instance().palette()
                bg_color_obj = palette.color(palette.ColorRole.Window)
                is_dark_theme = bg_color_obj.lightness() < 128
        except Exception:
            pass
        
        # 테마에 따른 plotly 템플릿 적용
        if is_dark_theme:
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor='rgba(0,0,0,0)',  # 투명 배경
                plot_bgcolor='rgba(0,0,0,0)',   # 투명 플롯 배경
                font=dict(color='white')
            )
        else:
            fig.update_layout(
                template="plotly_white",
                paper_bgcolor='rgba(255,255,255,0)',  # 투명 배경
                plot_bgcolor='rgba(255,255,255,0)',   # 투명 플롯 배경
                font=dict(color='black')
            )
        
        fig.update_layout(
            title="트레이딩 차트",
            xaxis_rangeslider_visible=False,
            height=600,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # X축 설정 (시간축 공유) - 테마에 따른 그리드 색상 적용
        grid_color = 'rgba(255,255,255,0.2)' if is_dark_theme else 'lightgray'
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor=grid_color)
        
        # Y축 설정 - 테마에 따른 그리드 색상 적용
        for i in range(1, len(layout_info.height_ratios) + 1):
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor=grid_color, row=i, col=1)

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """RSI 계산"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, 
                       signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """MACD 계산"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """HEX 색상을 RGB로 변환"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


# 전역 렌더링 엔진 인스턴스
_chart_rendering_engine = None


def get_chart_rendering_engine() -> ChartRenderingEngine:
    """차트 렌더링 엔진 싱글톤 반환"""
    global _chart_rendering_engine
    if _chart_rendering_engine is None:
        _chart_rendering_engine = ChartRenderingEngine()
    return _chart_rendering_engine
