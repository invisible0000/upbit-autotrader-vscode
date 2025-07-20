"""
캔들스틱 차트 모듈

이 모듈은 PyQtGraph를 사용하여 캔들스틱 차트를 구현합니다.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGraphicsView
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush

import pyqtgraph as pg
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class CandlestickItem(pg.GraphicsObject):
    """캔들스틱 아이템 클래스"""
    
    def __init__(self, data):
        """캔들스틱 아이템 초기화"""
        super().__init__()
        
        # 데이터 저장
        self.data = data
        
        # 색상 설정
        self.bull_color = QColor(76, 175, 80)  # 상승봉 색상 (녹색)
        self.bear_color = QColor(244, 67, 54)  # 하락봉 색상 (적색)
        
        # 경계 상자 생성
        self.picture = None
        self.generatePicture()
    
    def generatePicture(self):
        """캔들스틱 그림 생성"""
        # 그림 객체 생성
        self.picture = pg.QtGui.QPicture()
        
        # 페인터 생성
        painter = pg.QtGui.QPainter(self.picture)
        
        # 안티앨리어싱 활성화
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 데이터 순회
        for i in range(len(self.data)):
            # 캔들 데이터 추출
            t = i  # x 좌표 (인덱스)
            open_price = self.data['open'].iloc[i]
            high_price = self.data['high'].iloc[i]
            low_price = self.data['low'].iloc[i]
            close_price = self.data['close'].iloc[i]
            
            # 상승/하락 여부 확인
            is_bull = close_price >= open_price
            
            # 색상 설정
            color = self.bull_color if is_bull else self.bear_color
            
            # 캔들 몸통 그리기
            painter.setPen(pg.mkPen(color))
            painter.setBrush(pg.mkBrush(color))
            
            # 캔들 몸통 너비 설정 (0.8은 캔들 사이 간격을 위한 값)
            rect_width = 0.8
            
            # 캔들 몸통 그리기
            rect = QRectF(
                t - rect_width/2,
                min(open_price, close_price),
                rect_width,
                abs(close_price - open_price)
            )
            painter.drawRect(rect)
            
            # 캔들 심지 그리기
            painter.setPen(pg.mkPen(color, width=1))
            
            # 상단 심지
            painter.drawLine(
                pg.QtCore.QPointF(t, high_price),
                pg.QtCore.QPointF(t, max(open_price, close_price))
            )
            
            # 하단 심지
            painter.drawLine(
                pg.QtCore.QPointF(t, min(open_price, close_price)),
                pg.QtCore.QPointF(t, low_price)
            )
        
        # 페인터 종료
        painter.end()
    
    def paint(self, painter, option, widget):
        """캔들스틱 그리기"""
        painter.drawPicture(0, 0, self.picture)
    
    def boundingRect(self):
        """경계 상자 반환"""
        # 데이터가 없는 경우 기본 경계 상자 반환
        if len(self.data) == 0:
            return QRectF(0, 0, 1, 1)
        
        # 데이터 범위 계산
        min_x = 0
        max_x = len(self.data)
        min_y = self.data['low'].min()
        max_y = self.data['high'].max()
        
        # 여백 추가
        margin = (max_y - min_y) * 0.1
        
        # 경계 상자 반환
        return QRectF(min_x - 1, min_y - margin, max_x + 1, (max_y - min_y) + 2 * margin)


class CandlestickChart(pg.PlotWidget):
    """캔들스틱 차트 클래스"""
    
    def __init__(self, parent=None):
        """캔들스틱 차트 초기화"""
        # 데이터 초기화 (super() 호출 전에 설정)
        self.data = None
        self.candlesticks = None
        self.indicator_overlays = {}
        self.trade_markers = []
        
        # 뷰 범위 초기화
        self.view_range = [0, 100, 0, 100]  # [xMin, xMax, yMin, yMax]
        
        # PlotWidget 초기화
        super().__init__(parent)
        
        # 차트 설정
        self._setup_chart()
    
    def _setup_chart(self):
        """차트 설정"""
        # 크기 정책 설정
        from PyQt6.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # 최소 크기 설정
        self.setMinimumSize(400, 300)
        
        # 배경색 설정
        self.setBackground('w')
        
        # 그리드 설정
        self.showGrid(x=True, y=True, alpha=0.3)
        
        # 십자선 설정
        self.crosshair = pg.CrosshairROI((0, 0), size=(0, 0), movable=False)
        self.addItem(self.crosshair)
        self.crosshair.setZValue(1000)  # 최상위 레이어에 표시
        
        # 마우스 이벤트 연결
        self.scene().sigMouseMoved.connect(self._on_mouse_moved)
        
        # 축 설정
        self.getAxis('bottom').setLabel('시간')
        self.getAxis('left').setLabel('가격')
        
        # 뷰박스 설정
        self.setMouseEnabled(x=True, y=True)  # 마우스로 확대/축소 및 이동 가능
        self.enableAutoRange(False)  # 자동 범위 조정 비활성화
        
        # 범례 설정
        self.legend = self.addLegend()
    
    def update_data(self, data, preserve_viewport=True):
        """데이터 업데이트 - 자동 범위 조정 완전 비활성화
        
        Args:
            data: 새로운 차트 데이터
            preserve_viewport: 뷰포트 보존 여부 (기본값: True)
        """
        print(f"🔄 캔들 데이터 업데이트 시작 (preserve_viewport: {preserve_viewport})")
        
        # 🚫 자동 범위 조정 강제 비활성화 (핵심 해결책)
        view_box = self.getViewBox()
        view_box.disableAutoRange()  # 이것이 핵심!
        
        # 현재 뷰포트 저장 (preserve_viewport가 True인 경우)
        current_viewport = None
        if preserve_viewport:
            try:
                current_viewport = view_box.viewRange()
                print(f"  💾 현재 뷰포트 저장: x={current_viewport[0]}, y={current_viewport[1]}")
            except Exception as e:
                print(f"  ❌ 뷰포트 저장 실패: {e}")
                current_viewport = None
        
        # 데이터 저장
        self.data = data
        
        # 기존 캔들스틱 제거
        if self.candlesticks is not None:
            self.removeItem(self.candlesticks)
            print(f"  🗑️ 기존 캔들스틱 제거")
        
        # 새 캔들스틱 생성
        self.candlesticks = CandlestickItem(data)
        self.addItem(self.candlesticks)
        print(f"  📊 새 캔들스틱 생성 완료 ({len(data)}개 캔들)")
        
        # 🚫 다시 한번 자동 범위 조정 비활성화 확인
        view_box.disableAutoRange()
        
        # 뷰포트 복원 (자동 범위 조정 없이)
        if preserve_viewport and current_viewport is not None:
            try:
                x_range, y_range = current_viewport
                # 📍 자동 범위 조정 없이 직접 뷰포트 설정
                view_box.setRange(
                    xRange=x_range, 
                    yRange=y_range, 
                    padding=0,
                    update=False  # 자동 업데이트 방지
                )
                print(f"  ✅ 뷰포트 복원 완료")
            except Exception as e:
                print(f"  ❌ 뷰포트 복원 실패: {e}")
        elif not preserve_viewport:
            # 전체 데이터 표시 (한 번만)
            try:
                view_box.autoRange(padding=0.1)
                view_box.disableAutoRange()  # 즉시 다시 비활성화
                print(f"  🔍 전체 데이터 범위 설정 후 자동 조정 비활성화")
            except Exception as e:
                print(f"  ❌ 전체 범위 설정 실패: {e}")
        
        # 날짜 축 설정
        self._setup_date_axis()
        
        # 🚫 마지막으로 자동 범위 조정 비활성화 보장
        view_box.disableAutoRange()
        
        # 기존 지표들은 데이터만 업데이트 (재생성 없음)
        if hasattr(self, 'indicator_overlays') and self.indicator_overlays:
            print(f"  🔄 기존 지표 {len(self.indicator_overlays)}개 데이터 업데이트")
            for indicator_id in list(self.indicator_overlays.keys()):
                self._update_indicator_data_only(indicator_id)
        
        print(f"🔄 캔들 데이터 업데이트 완료")
    
    def _update_indicator_data_only(self, indicator_id):
        """지표 시각 객체는 유지하고 데이터만 업데이트"""
        try:
            if indicator_id not in self.indicator_overlays:
                return
            
            overlay = self.indicator_overlays[indicator_id]
            
            # 부모 차트에서 새로운 지표 데이터 계산
            parent = self.parent()
            while parent and not hasattr(parent, 'calculate_indicator_data'):
                parent = parent.parent() if hasattr(parent, 'parent') else None
            
            if parent and hasattr(parent, 'active_indicators') and indicator_id in parent.active_indicators:
                params = parent.active_indicators[indicator_id]
                new_data = parent.calculate_indicator_data(params)
                
                if new_data is not None and hasattr(overlay, 'setData'):
                    # 데이터만 업데이트 (객체 재생성 없음)
                    if hasattr(new_data, 'values'):
                        overlay.setData(x=range(len(new_data)), y=new_data.values)
                    else:
                        overlay.setData(x=range(len(new_data)), y=new_data)
                    print(f"    ✅ {indicator_id} 데이터 업데이트 완료")
                else:
                    print(f"    ❌ {indicator_id} 새 데이터 없음")
            else:
                print(f"    ❌ {indicator_id} 부모 차트 찾기 실패")
                
        except Exception as e:
            print(f"    ❌ {indicator_id} 데이터 업데이트 실패: {e}")
            # 실패한 경우 해당 지표만 제거하고 다시 추가
            try:
                if indicator_id in self.indicator_overlays:
                    self.remove_indicator_overlay(indicator_id)
                    print(f"    🔄 {indicator_id} 지표 제거 후 재추가 예정")
            except Exception as remove_error:
                print(f"    ❌ {indicator_id} 제거 실패: {remove_error}")
    
    def _update_view_range(self):
        """뷰 범위 업데이트"""
        if self.data is None or len(self.data) == 0:
            return
        
        # 데이터 범위 계산
        min_x = 0
        max_x = len(self.data) - 1
        min_y = self.data['low'].min()
        max_y = self.data['high'].max()
        
        # 여백 추가
        y_margin = (max_y - min_y) * 0.1
        
        # 뷰 범위 설정
        self.view_range = [min_x, max_x, min_y - y_margin, max_y + y_margin]
        self.setXRange(min_x, max_x)
        self.setYRange(min_y - y_margin, max_y + y_margin)
    
    def _setup_date_axis(self):
        """날짜 축 설정"""
        if self.data is None or len(self.data) == 0:
            return
        
        # 날짜 문자열 변환 함수
        def timestamp_to_str(x):
            if x < 0 or x >= len(self.data):
                return ""
            
            # 인덱스를 정수로 변환
            idx = int(x)
            if idx >= len(self.data):
                idx = len(self.data) - 1
            
            try:
                # 날짜 포맷팅
                date = self.data.index[idx]
                
                # pandas.Timestamp인지 확인
                if hasattr(date, 'strftime'):
                    return date.strftime('%Y-%m-%d')
                # datetime 객체가 아닌 경우 문자열로 변환
                elif hasattr(date, 'to_pydatetime'):
                    return date.to_pydatetime().strftime('%Y-%m-%d')
                else:
                    # 그 외의 경우 문자열로 변환
                    return str(date)
            except Exception as e:
                # 오류 발생 시 인덱스 번호 반환
                return f"#{idx}"
        
        # 축 설정
        axis = self.getAxis('bottom')
        axis.setTicks([[(i, timestamp_to_str(i)) for i in range(0, len(self.data), max(1, len(self.data) // 10))]])
    
    def _on_mouse_moved(self, pos):
        """마우스 이동 이벤트 처리"""
        # 뷰포트 좌표로 변환
        view_pos = self.getViewBox().mapSceneToView(pos)
        
        # 십자선 위치 업데이트
        self.crosshair.setPos((view_pos.x(), view_pos.y()))
    
    def add_indicator_overlay(self, indicator_id, indicator_data):
        """지표 오버레이 추가"""
        if self.data is None or len(self.data) == 0:
            print(f"❌ 지표 추가 실패: 데이터 없음 ({indicator_id})")
            return
        
        # 기존 지표가 있다면 먼저 제거 (중복 방지)
        if indicator_id in self.indicator_overlays:
            print(f"🔄 기존 지표 제거 후 재생성: {indicator_id}")
            self.remove_indicator_overlay(indicator_id)
        
        print(f"📈 지표 추가 시작: {indicator_id}")
        
        # 지표 유형 확인
        if indicator_id.startswith("SMA") or indicator_id.startswith("EMA"):
            # 이동 평균선 - indicator_data는 이미 계산된 Series
            data = indicator_data
            
            # NaN 값 제거 및 유효성 검사
            if hasattr(data, 'dropna'):
                data = data.dropna()
            
            if len(data) == 0:
                print(f"❌ 지표 데이터가 비어있음: {indicator_id}")
                return
            
            # 이상값 확인 및 필터링
            if hasattr(data, 'quantile'):
                q1 = data.quantile(0.25)
                q3 = data.quantile(0.75)
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                
                # 이상값 제거
                data = data[(data >= lower_bound) & (data <= upper_bound)]
                print(f"  📊 이상값 필터링 완료: {len(data)}개 유효 데이터")
            
            # 색상 설정
            if indicator_id.startswith("SMA"):
                color = (0, 0, 255)  # 파란색
                line_style = pg.QtCore.Qt.PenStyle.SolidLine
            else:
                color = (255, 165, 0)  # 주황색
                line_style = pg.QtCore.Qt.PenStyle.DashLine
            
            # 선 그리기
            overlay = self.plot(
                x=range(len(data)),
                y=data.values,
                pen=pg.mkPen(color=color, width=2, style=line_style),
                name=indicator_id
            )
            
            # 데이터 저장 (재적용을 위해)
            overlay.data = data
            
            # 오버레이 저장
            self.indicator_overlays[indicator_id] = overlay
            print(f"  ✅ {indicator_id} 추가 완료 (데이터: {len(data)}개)")
        
        elif indicator_id.startswith("BBANDS"):
            # 볼린저 밴드 - 키 이름 동적 처리
            try:
                # 키 이름을 동적으로 찾기
                upper_key = [k for k in indicator_data.keys() if k.endswith('_upper')][0]
                middle_key = [k for k in indicator_data.keys() if k.endswith('_middle')][0]
                lower_key = [k for k in indicator_data.keys() if k.endswith('_lower')][0]
                
                upper = indicator_data[upper_key]
                middle = indicator_data[middle_key]
                lower = indicator_data[lower_key]
                
                # 상단 밴드
                upper_overlay = self.plot(
                    x=range(len(upper)),
                    y=upper.values,
                    pen=pg.mkPen(color=(255, 0, 0), width=1),
                    name=f"{indicator_id} 상단"
                )
                
                # 중간 밴드
                middle_overlay = self.plot(
                    x=range(len(middle)),
                    y=middle.values,
                    pen=pg.mkPen(color=(0, 0, 255), width=1),
                    name=f"{indicator_id} 중간"
                )
                
                # 하단 밴드
                lower_overlay = self.plot(
                    x=range(len(lower)),
                    y=lower.values,
                    pen=pg.mkPen(color=(255, 0, 0), width=1),
                    name=f"{indicator_id} 하단"
                )
                
                # 밴드 영역 채우기
                fill = pg.FillBetweenItem(
                    upper_overlay,
                    lower_overlay,
                    brush=pg.mkBrush(color=(255, 0, 0, 50))
                )
                self.addItem(fill)
                
                # 오버레이 저장
                self.indicator_overlays[f"{indicator_id}_upper"] = upper_overlay
                self.indicator_overlays[f"{indicator_id}_middle"] = middle_overlay
                self.indicator_overlays[f"{indicator_id}_lower"] = lower_overlay
                self.indicator_overlays[f"{indicator_id}_fill"] = fill
                
                print(f"✅ 볼린저밴드 표시 완료: 상단/중간/하단 밴드")
                
            except Exception as e:
                print(f"❌ 볼린저밴드 표시 오류: {e}")
                print(f"📊 사용 가능한 키: {list(indicator_data.keys())}")
        
        elif indicator_id.startswith("RSI"):
            # RSI (임시로 메인 차트에 표시 - 정규화 적용)
            data = indicator_data[list(indicator_data.keys())[0]]  # 첫 번째 키의 데이터 사용
            
            # RSI를 가격 범위로 정규화 (0-100 -> 현재 가격 범위)
            if self.data is not None and len(self.data) > 0:
                price_min = self.data['low'].min()
                price_max = self.data['high'].max()
                price_range = price_max - price_min
                
                # RSI (0-100)를 가격 범위로 변환
                normalized_data = price_min + (data / 100) * price_range
                
                # RSI 선 그리기
                overlay = self.plot(
                    x=range(len(normalized_data)),
                    y=normalized_data.values,
                    pen=pg.mkPen(color=(128, 0, 128), width=2),
                    name=f"{indicator_id} (정규화됨)"
                )
                
                # 오버레이 저장
                self.indicator_overlays[indicator_id] = overlay
                print(f"✅ RSI가 정규화되어 메인 차트에 표시됨 (원본: 0-100 → 가격: {price_min:.0f}-{price_max:.0f})")
            else:
                print("❌ RSI 정규화 실패: 차트 데이터 없음")
        
        elif indicator_id.startswith("MACD"):
            # MACD (임시로 메인 차트에 표시 - 정규화 적용)
            macd_line_key = [k for k in indicator_data.keys() if k.endswith('_line')][0]
            macd_line = indicator_data[macd_line_key]
            
            # MACD를 가격 범위로 정규화
            if self.data is not None and len(self.data) > 0:
                price_min = self.data['low'].min()
                price_max = self.data['high'].max()
                price_range = price_max - price_min
                
                # MACD 값의 범위 계산
                macd_min = macd_line.min()
                macd_max = macd_line.max()
                macd_range = macd_max - macd_min
                
                if macd_range > 0:
                    # MACD를 가격 범위로 정규화
                    normalized_macd = price_min + ((macd_line - macd_min) / macd_range) * price_range * 0.2  # 20% 범위 사용
                    
                    # MACD 선 그리기
                    overlay = self.plot(
                        x=range(len(normalized_macd)),
                        y=normalized_macd.values,
                        pen=pg.mkPen(color=(0, 0, 255), width=2),
                        name=f"{indicator_id} (정규화됨)"
                    )
                    
                    # 오버레이 저장
                    self.indicator_overlays[indicator_id] = overlay
                    print(f"✅ MACD가 정규화되어 메인 차트에 표시됨 (원본: {macd_min:.4f}-{macd_max:.4f} → 가격 20% 범위)")
                else:
                    print("❌ MACD 정규화 실패: MACD 범위가 0")
            else:
                print("❌ MACD 정규화 실패: 차트 데이터 없음")
        
        elif indicator_id.startswith("Stochastic"):
            # 스토캐스틱 (임시로 메인 차트에 표시 - 나중에 서브플롯으로 이동)
            k_line_key = [k for k in indicator_data.keys() if k.endswith('_k')][0]
            k_line = indicator_data[k_line_key]
            
            # %K 선 그리기
            overlay = self.plot(
                x=range(len(k_line)),
                y=k_line.values,
                pen=pg.mkPen(color=(0, 0, 255), width=2),
                name=f"{indicator_id} %K"
            )
            
            # 오버레이 저장
            self.indicator_overlays[indicator_id] = overlay
            print(f"⚠️ 스토캐스틱이 메인 차트에 임시 표시됨")
    
    def remove_indicator_overlay(self, indicator_id):
        """지표 오버레이 제거 - 강화된 버전"""
        print(f"🗑️ 지표 제거 시작: {indicator_id}")
        
        removed_count = 0
        
        # 1. 직접 매칭되는 지표 제거
        if indicator_id in self.indicator_overlays:
            overlay = self.indicator_overlays[indicator_id]
            try:
                if hasattr(overlay, 'scene') and overlay.scene():
                    overlay.scene().removeItem(overlay)
                else:
                    self.removeItem(overlay)
                print(f"  ✅ {indicator_id} 직접 제거 완료")
                removed_count += 1
            except Exception as e:
                print(f"  ❌ {indicator_id} 직접 제거 실패: {e}")
            
            # 딕셔너리에서 제거
            del self.indicator_overlays[indicator_id]
        
        # 2. 복합 지표 (볼린저 밴드 등) 제거
        if indicator_id.startswith("BBANDS"):
            # 볼린저 밴드의 모든 구성 요소 찾기
            keys_to_remove = []
            for key in list(self.indicator_overlays.keys()):
                if key.startswith(indicator_id):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                overlay = self.indicator_overlays[key]
                try:
                    if hasattr(overlay, 'scene') and overlay.scene():
                        overlay.scene().removeItem(overlay)
                    else:
                        self.removeItem(overlay)
                    print(f"  ✅ {key} 구성요소 제거 완료")
                    removed_count += 1
                except Exception as e:
                    print(f"  ❌ {key} 구성요소 제거 실패: {e}")
                
                # 딕셔너리에서 제거
                del self.indicator_overlays[key]
        
        # 3. 모든 plot item 중에서 해당 이름을 가진 항목 강제 제거
        try:
            plot_items = self.plotItem.listDataItems()
            for item in plot_items:
                if hasattr(item, 'name') and item.name() == indicator_id:
                    self.removeItem(item)
                    print(f"  🔍 plot item에서 강제 제거: {indicator_id}")
                    removed_count += 1
                elif hasattr(item, 'name') and item.name() and indicator_id in item.name():
                    self.removeItem(item)
                    print(f"  🔍 plot item에서 관련 항목 제거: {item.name()}")
                    removed_count += 1
        except Exception as e:
            print(f"  ❌ plot item 강제 제거 실패: {e}")
        
        # 4. 범례에서 제거
        try:
            if hasattr(self, 'legend') and self.legend:
                # 범례 아이템 중에서 해당 지표 제거
                legend_items = self.legend.items[:]  # 복사본 생성
                for item, label in legend_items:
                    if hasattr(label, 'text') and (label.text == indicator_id or indicator_id in label.text):
                        self.legend.removeItem(item)
                        print(f"  🏷️ 범례에서 제거: {label.text}")
                        removed_count += 1
        except Exception as e:
            print(f"  ❌ 범례 제거 실패: {e}")
        
        # 5. 강제 화면 갱신
        try:
            self.update()
            self.repaint()
        except Exception as e:
            print(f"  ❌ 화면 갱신 실패: {e}")
        
        print(f"🗑️ 지표 제거 완료: {indicator_id}, 제거된 항목 수: {removed_count}")
        
        # 남은 지표 수 확인
        remaining_count = len(self.indicator_overlays)
        print(f"  📊 남은 지표 수: {remaining_count}")
        
        return removed_count > 0
    
    def add_trade_marker(self, marker):
        """거래 마커 추가"""
        if self.data is None or len(self.data) == 0:
            return
        
        # 마커 타임스탬프에 해당하는 인덱스 찾기
        timestamp = marker.timestamp
        
        # 가장 가까운 인덱스 찾기
        closest_idx = 0
        min_diff = float('inf')
        
        for i, date in enumerate(self.data.index):
            diff = abs((date - timestamp).total_seconds())
            if diff < min_diff:
                min_diff = diff
                closest_idx = i
        
        # 마커 위치 설정
        marker.setPos(closest_idx, marker.price)
        
        # 마커 추가
        self.addItem(marker)
        
        # 마커 목록에 추가
        self.trade_markers.append(marker)
    
    def remove_trade_marker(self, marker):
        """거래 마커 제거"""
        # 마커 제거
        self.removeItem(marker)
        
        # 마커 목록에서 제거
        if marker in self.trade_markers:
            self.trade_markers.remove(marker)
    
    def zoom_in(self):
        """확대"""
        # 현재 뷰 범위 가져오기
        x_min, x_max = self.getViewBox().viewRange()[0]
        y_min, y_max = self.getViewBox().viewRange()[1]
        
        # 중심점 계산
        x_center = (x_min + x_max) / 2
        y_center = (y_min + y_max) / 2
        
        # 범위 축소 (확대)
        x_range = (x_max - x_min) * 0.8
        y_range = (y_max - y_min) * 0.8
        
        # 새 범위 설정
        self.setXRange(x_center - x_range/2, x_center + x_range/2)
        self.setYRange(y_center - y_range/2, y_center + y_range/2)
        
        # 뷰 범위 업데이트
        self.view_range = [x_center - x_range/2, x_center + x_range/2, y_center - y_range/2, y_center + y_range/2]
    
    def zoom_out(self):
        """축소"""
        # 현재 뷰 범위 가져오기
        x_min, x_max = self.getViewBox().viewRange()[0]
        y_min, y_max = self.getViewBox().viewRange()[1]
        
        # 중심점 계산
        x_center = (x_min + x_max) / 2
        y_center = (y_min + y_max) / 2
        
        # 범위 확대 (축소)
        x_range = (x_max - x_min) * 1.25
        y_range = (y_max - y_min) * 1.25
        
        # 새 범위 설정
        self.setXRange(x_center - x_range/2, x_center + x_range/2)
        self.setYRange(y_center - y_range/2, y_center + y_range/2)
        
        # 뷰 범위 업데이트
        self.view_range = [x_center - x_range/2, x_center + x_range/2, y_center - y_range/2, y_center + y_range/2]
    
    def save_image(self, file_path):
        """차트 이미지 저장"""
        # 이미지로 내보내기
        exporter = pg.exporters.ImageExporter(self.plotItem)
        exporter.export(file_path)
    
    def remove_trade_marker(self, marker):
        """거래 마커 제거"""
        if marker in self.trade_markers:
            self.removeItem(marker)
            self.trade_markers.remove(marker)
    
    def set_indicator_visibility(self, indicator_id, visible):
        """지표 가시성 설정"""
        overlay = self.indicator_overlays.get(indicator_id)
        if overlay:
            overlay.setVisible(visible)
    
    def set_volume_visible(self, visible):
        """거래량 표시 설정"""
        # 거래량 차트는 별도 구현 필요
        pass
    
    def set_grid_visible(self, visible):
        """그리드 표시 설정"""
        self.showGrid(x=visible, y=visible, alpha=0.3)
    
    def set_crosshair_visible(self, visible):
        """십자선 표시 설정"""
        self.crosshair.setVisible(visible)
    
    def resizeEvent(self, event):
        """크기 변경 이벤트 처리"""
        super().resizeEvent(event)
        
        # 뷰 범위 다시 계산
        if self.data is not None:
            self._update_view_range()
        
        # 차트 다시 그리기
        self.update()
        self.repaint()