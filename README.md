오픈소스SW개발방법및도구 HW2

# WonScope FX

대한민국 원화(KRW)를 기준으로 미국·영국·일본·중국·베트남·필리핀·호주·유럽연합·러시아·캐나다의 현재 환율, 최근 30일 추이, 7일/30일 방향성 전망을 확인하는 로컬 FastAPI 서비스입니다.

환율은 Frankfurter/ECB에서 가져오고, 국제 정세 신호는 국가별 Google News RSS 검색 결과에서 추출합니다. 예측은 최근 추이·변동성·뉴스 키워드를 결합한 설명 가능한 휴리스틱 모델이며 투자 조언이 아닙니다.

## 실행 (PowerShell)

Python 3.11 이상이 설치되어 있고 `python` 명령이 PATH에 있어야 합니다.

```powershell
Set-Location 'C:\Users\LCY\Documents\2026-2 오픈소스SW\OPS_HW2'
.\run.ps1
```

처음 실행 시 `requirements.txt`의 FastAPI/Uvicorn을 설치한 뒤 `http://127.0.0.1:8000`에서 엽니다. 종료는 서버 창에서 `Ctrl+C`입니다.

`run.ps1`은 먼저 PATH의 `python`을 사용합니다. Python이 PATH에 없으면 이 프로젝트 검증에 사용한 임시 런타임 경로를 확인하고, 없을 경우 Python 3.11 이상을 설치해 PATH에 추가하라는 오류를 표시합니다.

## 설치 방법

1. Python 3.11 이상을 설치합니다.
2. 이 폴더를 내려받아 PowerShell에서 엽니다.
3. 아래 명령으로 의존성을 설치합니다.

```powershell
python -m pip install -r requirements.txt
```

## 실행 방법

```powershell
.\run.ps1
```

브라우저에서 `http://127.0.0.1:8000`을 열고 관찰 국가를 선택합니다. 서비스는 로컬 주소에만 바인딩하며 Windows 보안 설정을 변경하지 않습니다.

## 데이터와 모델

- 환율: Frankfurter API(ECB 기준), 매 서비스 실행/페이지 조회 시 갱신
- 국제 정세: Google News RSS의 국가별 검색 결과 요약
- 전망: 최근 30일 변화 50%, 최근 변화 20%, 뉴스의 전쟁·제재·관세·금리·성장 키워드 신호 30%를 사용한 설명 가능한 휴리스틱 모델
- 외부 연결 실패 시 앱을 유지하기 위해 표시 가능한 오프라인 추정값으로 폴백하며, 화면에 출처와 기준일을 표시

## 보안 및 데이터 메모

API 키나 인증정보는 필요하지 않으며 저장하지 않습니다. 외부 API 연결 실패 시 화면에 오프라인 추정값과 출처 상태를 표시합니다. `__pycache__`, 로그, 실행 산출물, 로컬 환경 파일은 Git에 포함하지 않습니다.
