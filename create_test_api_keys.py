"""API 키 생성 및 테스트 스크립트"""
import os
import json
from cryptography.fernet import Fernet

def create_test_api_keys():
    """테스트용 API 키를 생성합니다"""
    # data 디렉터리 설정
    data_dir = "upbit_auto_trading/data"
    settings_dir = os.path.join(data_dir, "settings")
    
    # 디렉터리 생성
    if not os.path.exists(settings_dir):
        os.makedirs(settings_dir)
    
    # 암호화 키 생성
    key_path = os.path.join(settings_dir, "encryption_key.key")
    if not os.path.exists(key_path):
        key = Fernet.generate_key()
        with open(key_path, "wb") as key_file:
            key_file.write(key)
        print(f"✅ 암호화 키 생성: {key_path}")
    
    # 암호화 키 로드
    with open(key_path, "rb") as key_file:
        encryption_key = key_file.read()
    fernet = Fernet(encryption_key)
    
    # 테스트용 더미 API 키 (실제로는 작동하지 않지만 형식은 맞음)
    dummy_access_key = "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
    dummy_secret_key = "abcdefghijklmnopqrstuvwxyz1234567890abcdefghijklmnopqrstuvwxyz123456"
    
    # API 키 암호화
    encrypted_access_key = fernet.encrypt(dummy_access_key.encode()).decode()
    encrypted_secret_key = fernet.encrypt(dummy_secret_key.encode()).decode()
    
    # API 키 파일 저장
    api_keys_path = os.path.join(settings_dir, "api_keys.json")
    settings = {
        "access_key": encrypted_access_key,
        "secret_key": encrypted_secret_key,
        "trade_permission": False
    }
    
    with open(api_keys_path, "w", encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 테스트용 API 키 생성: {api_keys_path}")
    print(f"📝 Access Key: {dummy_access_key}")
    print(f"📝 Secret Key: {dummy_secret_key}")
    print("\n⚠️ 이것은 테스트용 더미 키입니다. 실제 API 통신은 실패할 것입니다.")
    print("🔑 실제 키를 넣으려면 프로그램 설정에서 직접 입력하세요.")

if __name__ == "__main__":
    create_test_api_keys()
