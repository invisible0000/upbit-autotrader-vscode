# ===================================================================
# 설정: 스크립트 파일을 합칠 폴더 경로를 지정하세요.
# ===================================================================
# !! 중요 !!: 아래 큰따옴표("") 안에 합칠 파일이 있는 폴더의 전체 경로를 입력하세요.
# 예시: $sourceFolder = "C:\Users\사용자명\Documents\내문서"
$sourceFolder = "D:\projects\매매 전략 개발 기획 실체화 방안 01"

# 합쳐진 결과 파일의 이름을 지정합니다.
$outputFileName = "자동매매전략개발01.txt"
# ===================================================================


# --- 스크립트 본문 (여기는 수정할 필요 없습니다) ---

# 결과 파일이 저장될 전체 경로 설정
$outputFilePath = Join-Path -Path $sourceFolder -ChildPath $outputFileName

Write-Host "----------------------------------------------------"
Write-Host "스크립트 합치기 프로세스를 시작합니다 (강화 모드)."
Write-Host "대상 폴더: $sourceFolder" -ForegroundColor Yellow

# 정규표현식을 사용해 '두 자리 숫자 + 언더바'로 시작하는 txt 파일만 찾고 이름순으로 정렬
$filesToMerge = Get-ChildItem -Path $sourceFolder -Filter "*.txt" | Where-Object { $_.Name -match '^\d{2}_' } | Sort-Object Name

if ($null -eq $filesToMerge) {
    Write-Host "----------------------------------------------------"
    Write-Warning "경고: 지정된 폴더에서 '숫자두자리_'로 시작하는 .txt 파일을 찾을 수 없습니다."
    Write-Host "----------------------------------------------------"
    exit
}

Write-Host "총 $($filesToMerge.Count)개의 파일을 발견했습니다. 아래 파일들을 순서대로 합칩니다:"
$filesToMerge.Name | ForEach-Object { Write-Host "- $_" }

# ========================== [최종 해결 로직] ==========================
#
# 1. 먼저 결과 파일을 깨끗하게 비우고, 가장 표준적인 UTF-8 방식으로 생성합니다.
Set-Content -Path $outputFilePath -Value "" -Encoding utf8

# 2. 루프를 돌면서 각 파일을 하나씩 처리합니다.
foreach ($file in $filesToMerge) {
    Write-Host "처리 중: $($file.Name)"
    
    # 3. [핵심] 파일을 '구형 윈도우 한글(코드페이지 949)'로 명확히 지정해서 읽어옵니다.
    $content = [System.IO.File]::ReadAllText($file.FullName, [System.Text.Encoding]::GetEncoding(949))
    
    # 4. 읽어온 내용을 UTF-8 결과 파일에 추가합니다.
    Add-Content -Path $outputFilePath -Value $content
}
#
# ====================================================================

Write-Host "----------------------------------------------------"
Write-Host "✅ 성공! 모든 파일이 아래 경로에 합쳐졌습니다:" -ForegroundColor Green
Write-Host $outputFilePath -ForegroundColor Cyan
Write-Host "----------------------------------------------------"