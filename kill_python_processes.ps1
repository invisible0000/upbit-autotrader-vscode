# PowerShell 스크립트: Python 백그라운드 프로세스 확인 및 정리
# kill_python_processes.ps1

Write-Host "🔍 Python 프로세스 확인 및 정리 스크립트" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Yellow

# 1. 현재 실행 중인 Python 프로세스 확인
Write-Host ""
Write-Host "📊 현재 실행 중인 Python 프로세스:" -ForegroundColor Cyan

$pythonProcesses = Get-Process -Name "python*" -ErrorAction SilentlyContinue

if ($pythonProcesses) {
    $pythonProcesses | Select-Object Id, ProcessName, CPU, StartTime, @{Name="WorkingSet(MB)"; Expression={[math]::Round($_.WorkingSet/1MB,2)}} | Format-Table -AutoSize

    Write-Host ""
    Write-Host "🔥 발견된 Python 프로세스 수: $($pythonProcesses.Count)개" -ForegroundColor Red

    # 사용자 확인 요청
    $response = Read-Host "모든 Python 프로세스를 종료하시겠습니까? (y/N)"

    if ($response -eq "y" -or $response -eq "Y") {
        Write-Host ""
        Write-Host "⚡ Python 프로세스 종료 중..." -ForegroundColor Yellow

        foreach ($process in $pythonProcesses) {
            try {
                Write-Host "  └─ 종료 중: PID $($process.Id) - $($process.ProcessName)" -ForegroundColor Gray
                Stop-Process -Id $process.Id -Force
                Write-Host "    ✅ 성공적으로 종료됨" -ForegroundColor Green
            }
            catch {
                Write-Host "    ❌ 종료 실패: $($_.Exception.Message)" -ForegroundColor Red
            }
        }

        # 1초 대기 후 재확인
        Start-Sleep -Seconds 1

        Write-Host ""
        Write-Host "🔍 종료 후 상태 재확인:" -ForegroundColor Cyan
        $remainingProcesses = Get-Process -Name "python*" -ErrorAction SilentlyContinue

        if ($remainingProcesses) {
            Write-Host "⚠️  여전히 실행 중인 Python 프로세스:" -ForegroundColor Yellow
            $remainingProcesses | Select-Object Id, ProcessName | Format-Table -AutoSize
        } else {
            Write-Host "✅ 모든 Python 프로세스가 성공적으로 종료되었습니다!" -ForegroundColor Green
        }
    } else {
        Write-Host "❌ 사용자가 취소했습니다." -ForegroundColor Yellow
    }
} else {
    Write-Host "✅ 실행 중인 Python 프로세스가 없습니다." -ForegroundColor Green
}

Write-Host ""
Write-Host "🏁 프로세스 정리 완료!" -ForegroundColor Green
Write-Host "이제 simple_private_test_v2.py를 다시 실행할 수 있습니다." -ForegroundColor Cyan
