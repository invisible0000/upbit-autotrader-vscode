#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scripts 폴더 파일 사용성 분석 스크립트
- 현재 사용 중인 파일 vs 사용하지 않는 파일 분석
- 중복 기능 파일 검출
- 정리 추천안 제시
"""

import os
from pathlib import Path
import json
from datetime import datetime

class ScriptsFolderAnalyzer:
    """Scripts 폴더 분석기"""
    
    def __init__(self, project_root="."):
        self.project_root = Path(project_root)
        self.scripts_dir = self.project_root / "scripts"
        self.utility_dir = self.scripts_dir / "utility"
        self.archive_dir = self.scripts_dir / "archive"
        
    def analyze_file_usage(self):
        """파일 사용성 분석"""
        analysis = {
            'active_tools': [],           # 현재 활발히 사용 중
            'utility_scripts': [],        # 유용한 유틸리티
            'outdated_scripts': [],       # 구버전/더 이상 사용 안함
            'duplicate_functionality': [], # 중복 기능
            'one_time_scripts': [],       # 일회성 스크립트
            'unclear_purpose': []         # 목적 불명확
        }
        
        # Scripts 메인 폴더 분석
        main_scripts = [
            'cleanup_project.py',
            'cleanup_main_folder.py', 
            'dev_workspace_manager.py'
        ]
        
        for script in main_scripts:
            script_path = self.scripts_dir / script
            if script_path.exists():
                if script == 'cleanup_project.py':
                    analysis['active_tools'].append({
                        'file': script,
                        'purpose': '프로젝트 임시 파일 정리',
                        'status': '활성 사용',
                        'location': 'scripts/'
                    })
                elif script == 'cleanup_main_folder.py':
                    analysis['one_time_scripts'].append({
                        'file': script,
                        'purpose': '메인 폴더 정리 (완료됨)',
                        'status': '임무 완료, 삭제 가능',
                        'location': 'scripts/'
                    })
                elif script == 'dev_workspace_manager.py':
                    analysis['active_tools'].append({
                        'file': script,
                        'purpose': '개발 환경 격리 관리',
                        'status': '활성 사용',
                        'location': 'scripts/'
                    })
        
        # Utility 폴더 분석
        utility_files = list(self.utility_dir.glob("*.py"))
        
        for file_path in utility_files:
            filename = file_path.name
            
            # 시뮬레이션 관련 (중복 기능)
            if 'simulation' in filename:
                if filename == 'enhanced_real_data_simulation_engine.py':
                    analysis['utility_scripts'].append({
                        'file': filename,
                        'purpose': '고급 시뮬레이션 엔진',
                        'status': '현재 사용 중',
                        'location': 'scripts/utility/'
                    })
                else:
                    analysis['duplicate_functionality'].append({
                        'file': filename,
                        'purpose': '시뮬레이션 엔진 (구버전)',
                        'status': '중복, 삭제 검토',
                        'location': 'scripts/utility/'
                    })
            
            # 데이터베이스 관련
            elif 'database' in filename or 'db' in filename:
                if 'backtest' in filename:
                    analysis['utility_scripts'].append({
                        'file': filename,
                        'purpose': '백테스트 데이터베이스 엔진',
                        'status': '백테스트용 유틸리티',
                        'location': 'scripts/utility/'
                    })
                else:
                    analysis['outdated_scripts'].append({
                        'file': filename,
                        'purpose': 'DB 관련 (구버전)',
                        'status': '통합 DB 이후 불필요',
                        'location': 'scripts/utility/'
                    })
            
            # 마이그레이션 관련 (일회성)
            elif 'migrate' in filename:
                analysis['one_time_scripts'].append({
                    'file': filename,
                    'purpose': 'DB 마이그레이션 (완료됨)',
                    'status': '일회성, 삭제 가능',
                    'location': 'scripts/utility/'
                })
            
            # 체크/분석 스크립트
            elif filename.startswith(('check_', 'analyze_')):
                analysis['utility_scripts'].append({
                    'file': filename,
                    'purpose': 'DB/시스템 상태 확인',
                    'status': '디버깅용 유틸리티',
                    'location': 'scripts/utility/'
                })
            
            # 매니저 클래스들
            elif 'manager' in filename:
                if 'position' in filename or 'trading' in filename:
                    analysis['outdated_scripts'].append({
                        'file': filename,
                        'purpose': '매니저 클래스 (구버전)',
                        'status': '메인 코드로 통합됨',
                        'location': 'scripts/utility/'
                    })
                else:
                    analysis['unclear_purpose'].append({
                        'file': filename,
                        'purpose': '목적 불명확',
                        'status': '검토 필요',
                        'location': 'scripts/utility/'
                    })
            
            # UI 관련
            elif 'show_' in filename or 'notification' in filename:
                analysis['outdated_scripts'].append({
                    'file': filename,
                    'purpose': 'UI 테스트 (구버전)',
                    'status': '메인 UI로 통합됨',
                    'location': 'scripts/utility/'
                })
            
            # 기타
            else:
                analysis['unclear_purpose'].append({
                    'file': filename,
                    'purpose': '목적 불명확',
                    'status': '수동 검토 필요',
                    'location': 'scripts/utility/'
                })
        
        # Archive 폴더 분석 (모두 백업용)
        archive_files = list(self.archive_dir.glob("*.py"))
        for file_path in archive_files:
            analysis['outdated_scripts'].append({
                'file': file_path.name,
                'purpose': '백업/아카이브',
                'status': '보관용, 정기 정리 대상',
                'location': 'scripts/archive/'
            })
        
        return analysis
    
    def generate_cleanup_recommendations(self, analysis):
        """정리 추천안 생성"""
        recommendations = {
            'keep_active': [],      # 유지할 활성 도구
            'keep_utility': [],     # 유지할 유틸리티
            'delete_safe': [],      # 안전하게 삭제 가능
            'archive_old': [],      # 구버전 아카이브
            'manual_review': []     # 수동 검토 필요
        }
        
        # 활성 도구는 유지
        for item in analysis['active_tools']:
            recommendations['keep_active'].append(item)
        
        # 유틸리티 스크립트는 유지
        for item in analysis['utility_scripts']:
            recommendations['keep_utility'].append(item)
        
        # 일회성 스크립트는 삭제
        for item in analysis['one_time_scripts']:
            recommendations['delete_safe'].append(item)
        
        # 중복 기능은 삭제
        for item in analysis['duplicate_functionality']:
            recommendations['delete_safe'].append(item)
        
        # 구버전은 아카이브로 이동
        for item in analysis['outdated_scripts']:
            if item['location'] == 'scripts/archive/':
                recommendations['delete_safe'].append(item)  # 이미 아카이브된 것은 삭제
            else:
                recommendations['archive_old'].append(item)
        
        # 불명확한 것은 수동 검토
        for item in analysis['unclear_purpose']:
            recommendations['manual_review'].append(item)
        
        return recommendations
    
    def print_analysis_report(self):
        """분석 보고서 출력"""
        print("🔍 Scripts 폴더 사용성 분석 보고서")
        print("=" * 60)
        
        analysis = self.analyze_file_usage()
        recommendations = self.generate_cleanup_recommendations(analysis)
        
        # 현재 상태 요약
        total_files = sum(len(category) for category in analysis.values())
        print(f"📊 총 분석 대상: {total_files}개 파일")
        print()
        
        # 카테고리별 분석
        categories = {
            'active_tools': '🚀 활성 도구',
            'utility_scripts': '🔧 유용한 유틸리티',
            'outdated_scripts': '📦 구버전/사용 안함',
            'duplicate_functionality': '🔄 중복 기능',
            'one_time_scripts': '⚡ 일회성 스크립트',
            'unclear_purpose': '❓ 목적 불명확'
        }
        
        for category, files in analysis.items():
            if not files:
                continue
                
            print(f"{categories[category]} - {len(files)}개")
            for item in files:
                print(f"  • {item['file']} - {item['purpose']}")
                print(f"    Status: {item['status']}")
                print(f"    Location: {item['location']}")
                print()
        
        print("\n" + "=" * 60)
        print("💡 정리 추천안")
        print("=" * 60)
        
        # 추천안 출력
        rec_categories = {
            'keep_active': '✅ 유지 (활성 도구)',
            'keep_utility': '🔧 유지 (유틸리티)',
            'delete_safe': '🗑️ 안전 삭제',
            'archive_old': '📦 아카이브 이동',
            'manual_review': '🤔 수동 검토'
        }
        
        for category, files in recommendations.items():
            if not files:
                continue
                
            print(f"\n{rec_categories[category]} - {len(files)}개")
            for item in files:
                print(f"  • {item['file']}")
        
        return recommendations
    
    def execute_cleanup_plan(self, recommendations, dry_run=True):
        """정리 계획 실행"""
        if dry_run:
            print("\n🧪 드라이런 모드 - 실제 파일 이동/삭제 안함")
        else:
            print("\n🚀 실제 정리 작업 실행")
        
        print("=" * 60)
        
        # 안전 삭제 실행
        for item in recommendations['delete_safe']:
            file_path = self.scripts_dir / item['location'].replace('scripts/', '') / item['file']
            if file_path.exists():
                if not dry_run:
                    file_path.unlink()
                print(f"🗑️ 삭제: {item['file']} ({item['purpose']})")
        
        # 구버전 파일들 추가 아카이브
        for item in recommendations['archive_old']:
            src_path = self.utility_dir / item['file']
            dest_path = self.archive_dir / item['file']
            
            if src_path.exists():
                if not dry_run:
                    src_path.rename(dest_path)
                print(f"📦 아카이브: {item['file']} → scripts/archive/")
        
        print(f"\n📈 정리 결과:")
        print(f"  • 삭제: {len(recommendations['delete_safe'])}개")
        print(f"  • 아카이브: {len(recommendations['archive_old'])}개")
        print(f"  • 유지: {len(recommendations['keep_active']) + len(recommendations['keep_utility'])}개")

def main():
    """메인 함수"""
    analyzer = ScriptsFolderAnalyzer()
    
    # 분석 보고서 출력
    recommendations = analyzer.print_analysis_report()
    
    # 사용자 확인
    print("\n❓ Scripts 폴더 정리를 진행하시겠습니까?")
    print("   1) y/yes - 실제 정리 실행")
    print("   2) d/dry - 드라이런만 실행")
    print("   3) n/no - 취소")
    
    choice = input("\n선택 (y/d/n): ").lower().strip()
    
    if choice in ['y', 'yes']:
        analyzer.execute_cleanup_plan(recommendations, dry_run=False)
        print("\n✅ Scripts 폴더 정리 완료!")
        
    elif choice in ['d', 'dry']:
        analyzer.execute_cleanup_plan(recommendations, dry_run=True)
        print("\n✅ 드라이런 완료!")
        
    else:
        print("\n❌ 정리 작업 취소됨")

if __name__ == "__main__":
    main()
