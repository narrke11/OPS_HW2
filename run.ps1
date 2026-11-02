$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if ($pythonCmd) {
    $python = $pythonCmd.Source
} else {
    $fallback = Join-Path $env:TEMP 'wonscope-python\python.exe'
    if (-not (Test-Path $fallback)) { throw 'python 명령을 찾을 수 없습니다. Python 3.11 이상을 설치하고 PATH에 추가한 뒤 다시 실행하세요.' }
    $python = $fallback
    Write-Host "PATH의 python이 없어 임시 로컬 런타임을 사용합니다: $python" -ForegroundColor Yellow
}
& $python -m pip install -r requirements.txt
& $python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
