Set-Location "$PSScriptRoot\..\backend"
python -m uvicorn ai_proxy.main:app --host 127.0.0.1 --port 8100 --reload
