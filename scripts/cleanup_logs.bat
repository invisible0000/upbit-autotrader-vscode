@echo off
echo 로그 파일 정리 스크립트
echo ========================

REM 7일 이상 된 빈 로그 파일 삭제
forfiles /p logs /m *.log /d -7 /c "cmd /c if @fsize==0 del @path"

REM GUI 에러 로그가 50KB 이상이면 백업 후 초기화
for %%f in (logs\gui_error.log) do (
    if %%~zf gtr 51200 (
        echo GUI 에러 로그 크기 초과, 백업 중...
        copy "%%f" "%%f.backup.%date:~0,4%%date:~5,2%%date:~8,2%"
        echo. > "%%f"
    )
)

echo 정리 완료!
pause
