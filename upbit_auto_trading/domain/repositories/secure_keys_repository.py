#!/usr/bin/env python3
"""
보안 키 저장소 Repository 인터페이스

DDD Domain Layer에서 정의하는 보안 키 관리를 위한 Repository 인터페이스입니다.
API 키 암호화에 사용되는 키와 기타 보안 관련 데이터의 영속화를 추상화합니다.

Features:
- 암호화 키 CRUD 연산
- 키 타입별 관리 (encryption, auth, etc.)
- 보안 메타데이터 추적
- DDD Repository 패턴 준수

Security:
- settings.sqlite3의 secure_keys 테이블과 매핑
- 키 타입별 UNIQUE 제약조건 지원
- 안전한 삭제 및 교체 연산
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

class SecureKeysRepository(ABC):
    """
    보안 키 관리를 위한 Repository 인터페이스

    DDD 패턴에 따라 보안 키의 영속화를 추상화합니다.
    settings.sqlite3 데이터베이스의 secure_keys 테이블과 매핑되며,
    API 키 암호화에 사용되는 키의 안전한 저장과 관리를 담당합니다.

    Key Features:
    - 타입별 키 관리 (encryption, signature 등)
    - 안전한 키 교체 연산 (INSERT OR REPLACE)
    - 키 존재 여부 확인
    - 키 메타데이터 추적 (생성/수정 시간)

    Security Considerations:
    - 키 데이터는 BLOB 타입으로 안전하게 저장
    - UNIQUE 제약조건으로 키 타입별 단일성 보장
    - 삭제 연산의 안전성 확보
    """

    @abstractmethod
    def save_key(self, key_type: str, key_data: bytes) -> bool:
        """
        보안 키 저장 (기존 키 교체)

        Args:
            key_type (str): 키 타입 (예: "encryption", "signature")
            key_data (bytes): 키 데이터 (BLOB 형태)

        Returns:
            bool: 저장 성공 여부

        Raises:
            ValueError: 잘못된 입력 데이터
            RepositoryError: 저장 작업 실패

        Example:
            >>> repo.save_key("encryption", encryption_key_bytes)
            True
        """
        pass

    @abstractmethod
    def load_key(self, key_type: str) -> Optional[bytes]:
        """
        키 타입으로 보안 키 조회

        Args:
            key_type (str): 키 타입

        Returns:
            Optional[bytes]: 키 데이터 (없으면 None)

        Raises:
            RepositoryError: 조회 작업 실패

        Example:
            >>> key_data = repo.load_key("encryption")
            >>> if key_data:
            ...     fernet = Fernet(key_data)
        """
        pass

    @abstractmethod
    def delete_key(self, key_type: str) -> bool:
        """
        키 타입으로 보안 키 삭제

        Args:
            key_type (str): 삭제할 키 타입

        Returns:
            bool: 삭제 성공 여부 (없어도 True)

        Raises:
            RepositoryError: 삭제 작업 실패

        Example:
            >>> repo.delete_key("encryption")
            True
        """
        pass

    @abstractmethod
    def key_exists(self, key_type: str) -> bool:
        """
        키 존재 여부 확인

        Args:
            key_type (str): 확인할 키 타입

        Returns:
            bool: 키 존재 여부

        Example:
            >>> if repo.key_exists("encryption"):
            ...     print("암호화 키가 존재합니다")
        """
        pass

    @abstractmethod
    def list_key_types(self) -> List[str]:
        """
        저장된 모든 키 타입 목록 조회

        Returns:
            List[str]: 키 타입 목록

        Example:
            >>> types = repo.list_key_types()
            >>> print(types)  # ["encryption", "signature"]
        """
        pass

    @abstractmethod
    def get_key_metadata(self, key_type: str) -> Optional[Dict[str, Any]]:
        """
        키 메타데이터 조회 (생성/수정 시간 등)

        Args:
            key_type (str): 키 타입

        Returns:
            Optional[Dict[str, Any]]: 메타데이터 (없으면 None)
            - id: 키 ID
            - key_type: 키 타입
            - created_at: 생성 시간
            - updated_at: 수정 시간
            - key_size: 키 크기 (bytes)

        Example:
            >>> metadata = repo.get_key_metadata("encryption")
            >>> print(f"생성일: {metadata['created_at']}")
        """
        pass

    @abstractmethod
    def replace_key(self, key_type: str, old_key: bytes, new_key: bytes) -> bool:
        """
        안전한 키 교체 (old_key 검증 후 교체)

        Args:
            key_type (str): 키 타입
            old_key (bytes): 기존 키 (검증용)
            new_key (bytes): 새로운 키

        Returns:
            bool: 교체 성공 여부

        Raises:
            ValueError: 기존 키 불일치
            RepositoryError: 교체 작업 실패

        Example:
            >>> success = repo.replace_key("encryption", old_key, new_key)
            >>> if success:
            ...     print("키 교체 완료")
        """
        pass

    @abstractmethod
    def delete_all_keys(self) -> int:
        """
        모든 보안 키 삭제 (초기화)

        Returns:
            int: 삭제된 키 개수

        Raises:
            RepositoryError: 삭제 작업 실패

        Warning:
            매우 위험한 연산입니다. 신중하게 사용하세요.

        Example:
            >>> deleted_count = repo.delete_all_keys()
            >>> print(f"{deleted_count}개 키 삭제 완료")
        """
        pass
