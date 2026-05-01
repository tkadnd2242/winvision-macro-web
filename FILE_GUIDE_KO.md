# WinVision Macro 파일 설명서

이 문서는 현재 저장소에 있는 주요 파일이 각각 어떤 역할을 하는지 빠르게 파악하기 위한 안내서입니다.

## 루트 문서와 설정 파일

### [README.md](/Users/ujinjo/Documents/Codex/2026-05-01-new-chat/README.md)
- 프로젝트 전체 개요 문서입니다.
- 지원 기능, 빠른 시작, 테스트 명령, 웹 보조 기능을 요약합니다.

### [RUN_GUIDE_KO.md](/Users/ujinjo/Documents/Codex/2026-05-01-new-chat/RUN_GUIDE_KO.md)
- Windows 기준 실행 방법을 한국어로 정리한 문서입니다.
- 설치, 웹 대시보드 사용, CLI 실행, 안전한 테스트 순서를 설명합니다.

### [TEST_CHECKLIST_KO.md](/Users/ujinjo/Documents/Codex/2026-05-01-new-chat/TEST_CHECKLIST_KO.md)
- 사용자가 직접 테스트할 때 체크박스처럼 따라갈 수 있는 수동 테스트 목록입니다.
- 드라이런, 정적 프레임 테스트, 라이브 입력 검증 순서를 담고 있습니다.

### [FILE_GUIDE_KO.md](/Users/ujinjo/Documents/Codex/2026-05-01-new-chat/FILE_GUIDE_KO.md)
- 이 문서 자체입니다.
- 각 파일의 역할과 읽는 순서를 정리합니다.

### [pyproject.toml](/Users/ujinjo/Documents/Codex/2026-05-01-new-chat/pyproject.toml)
- Python 패키지 메타데이터와 프로젝트 기본 설정 파일입니다.
- 패키지 이름과 빌드 관련 기준점을 제공합니다.

### [requirements.txt](/Users/ujinjo/Documents/Codex/2026-05-01-new-chat/requirements.txt)
- 기본 실행에 필요한 Python 의존성 목록입니다.
- OpenCV, `pyautogui` 같은 공통 런타임 패키지가 들어갑니다.

### [requirements-yolo.txt](/Users/ujinjo/Documents/Codex/2026-05-01-new-chat/requirements-yolo.txt)
- YOLO 기능을 쓸 때만 추가 설치하는 의존성 목록입니다.
- 주로 `ultralytics` 계열 패키지 설치를 위한 파일입니다.

### [configs/default.json](/Users/ujinjo/Documents/Codex/2026-05-01-new-chat/configs/default.json)
- 기본 샘플 설정 파일입니다.
- 화면 캡처 영역, 드라이런, 템플릿 목록, YOLO 타깃, 액션 시퀀스를 정의합니다.

## Windows 실행용 배치 파일

### [setup-windows.bat](/Users/ujinjo/Documents/Codex/2026-05-01-new-chat/setup-windows.bat)
- Windows에서 가상환경 생성과 기본 의존성 설치를 도와주는 스크립트입니다.
- 처음 한 번 실행하는 준비 단계용입니다.

### [run-windows.bat](/Users/ujinjo/Documents/Codex/2026-05-01-new-chat/run-windows.bat)
- 웹 대시보드 모드 실행용 배치 파일입니다.
- 브라우저 기반 제어 패널을 빠르게 띄울 때 사용합니다.

### [run-cli-windows.bat](/Users/ujinjo/Documents/Codex/2026-05-01-new-chat/run-cli-windows.bat)
- CLI 런타임을 바로 실행하는 배치 파일입니다.
- 웹 UI 없이 콘솔에서 빠르게 확인할 때 사용합니다.

## 템플릿과 모델 폴더

### [templates/README.md](/Users/ujinjo/Documents/Codex/2026-05-01-new-chat/templates/README.md)
- 템플릿 이미지를 어떻게 준비할지 설명하는 문서입니다.
- 어떤 UI 조각을 잘라서 저장하면 좋은지 방향을 잡아줍니다.

### [templates/.gitkeep](/Users/ujinjo/Documents/Codex/2026-05-01-new-chat/templates/.gitkeep)
- 비어 있는 `templates/` 폴더를 버전 관리에 남기기 위한 자리표시 파일입니다.
- 실행 기능은 없습니다.

### [models/README.md](/Users/ujinjo/Documents/Codex/2026-05-01-new-chat/models/README.md)
- YOLO `.pt` 모델 파일을 어디에 두는지 안내하는 문서입니다.
- 기본 경로인 `models/best.pt` 기준을 설명합니다.

### [models/.gitkeep](/Users/ujinjo/Documents/Codex/2026-05-01-new-chat/models/.gitkeep)
- 비어 있는 `models/` 폴더를 버전 관리에 남기기 위한 자리표시 파일입니다.
- 실행 기능은 없습니다.

## Python 패키지 진입점과 기본 구조

### [src/winvision_macro/__init__.py](/Users/ujinjo/Documents/Codex/2026-05-01-new-chat/src/winvision_macro/__init__.py)
- 패키지를 Python 모듈로 인식시키는 초기화 파일입니다.
- 외부에서 `winvision_macro` 패키지를 import할 수 있게 합니다.

### [src/winvision_macro/__main__.py](/Users/ujinjo/Documents/Codex/2026-05-01-new-chat/src/winvision_macro/__main__.py)
- `python -m winvision_macro` 형태로 실행할 때 호출되는 진입점 파일입니다.
- 내부적으로 메인 CLI 로직으로 연결됩니다.

### [src/winvision_macro/main.py](/Users/ujinjo/Documents/Codex/2026-05-01-new-chat/src/winvision_macro/main.py)
- 명령행 인자 처리와 실행 모드 분기를 담당합니다.
- `cli`, `web`, `--dry-run`, `--live`, `--frame-image`, `--print-config-summary` 옵션을 다룹니다.

## 설정과 데이터 모델

### [src/winvision_macro/config.py](/Users/ujinjo/Documents/Codex/2026-05-01-new-chat/src/winvision_macro/config.py)
- JSON 설정 파일을 읽고 쓰는 중심 모듈입니다.
- `capture_region`, 런타임 옵션, 템플릿 설정, YOLO 설정, 액션 시퀀스를 dataclass로 표현합니다.

### [src/winvision_macro/interfaces.py](/Users/ujinjo/Documents/Codex/2026-05-01-new-chat/src/winvision_macro/interfaces.py)
- 프레임, 감지 결과, 액션 구조, 프로토콜 인터페이스를 정의합니다.
- 다른 모듈이 공통으로 공유하는 타입 기준점 역할을 합니다.

## 캡처와 보정

### [src/winvision_macro/capture.py](/Users/ujinjo/Documents/Codex/2026-05-01-new-chat/src/winvision_macro/capture.py)
- 실제 데스크톱 화면을 캡처하는 로직이 들어 있습니다.
- `pyautogui` 기반 실시간 캡처와 저장된 이미지 또는 `.npy` 프레임 파일 로딩을 담당합니다.

### [src/winvision_macro/calibration.py](/Users/ujinjo/Documents/Codex/2026-05-01-new-chat/src/winvision_macro/calibration.py)
- 캘리브레이션 화면용 이미지 인코딩, 선택 영역 계산, 크롭 저장을 담당합니다.
- 웹에서 선택한 영역을 템플릿 파일로 저장할 때 사용됩니다.

### [src/winvision_macro/preview.py](/Users/ujinjo/Documents/Codex/2026-05-01-new-chat/src/winvision_macro/preview.py)
- 감지 결과를 이미지 위에 박스와 텍스트로 덧그려서 미리보기용 데이터로 만듭니다.
- 웹 대시보드의 `Live Preview`가 이 모듈을 사용합니다.

## 감지기와 런타임 조립

### [src/winvision_macro/vision.py](/Users/ujinjo/Documents/Codex/2026-05-01-new-chat/src/winvision_macro/vision.py)
- 템플릿 매칭 감지기와 YOLO 감지기를 구현합니다.
- 감지 결과를 우선순위와 점수 기준으로 정렬해 런타임으로 넘깁니다.

### [src/winvision_macro/bootstrap.py](/Users/ujinjo/Documents/Codex/2026-05-01-new-chat/src/winvision_macro/bootstrap.py)
- 설정, 캡처 소스, 감지기, 입력 컨트롤러, 러너를 한 번에 조립하는 모듈입니다.
- 웹과 CLI가 같은 런타임 스택을 재사용할 수 있게 해줍니다.

### [src/winvision_macro/runtime.py](/Users/ujinjo/Documents/Codex/2026-05-01-new-chat/src/winvision_macro/runtime.py)
- 메인 루프를 돌면서 `capture -> detect -> action` 흐름을 수행합니다.
- 우선순위, 쿨다운, 루프 중지 조건을 처리합니다.

## 액션 실행

### [src/winvision_macro/actions.py](/Users/ujinjo/Documents/Codex/2026-05-01-new-chat/src/winvision_macro/actions.py)
- 감지 결과에 연결된 액션을 실제 입력으로 실행하는 모듈입니다.
- 클릭, 더블클릭, 우클릭, 이동, 키 입력, 핫키, 텍스트 입력, 스크롤, 대기 액션을 지원합니다.

## 웹 제어 패널

### [src/winvision_macro/web_control.py](/Users/ujinjo/Documents/Codex/2026-05-01-new-chat/src/winvision_macro/web_control.py)
- 로컬 웹 서버와 브라우저 UI 전체를 담당하는 핵심 모듈입니다.
- `Safety Lock`, `Config Snapshot`, `Live Preview`, `Calibration Studio`, 작업 로그, 시작/중지 API가 모두 들어 있습니다.

## 테스트 코드

### [tests/test_config.py](/Users/ujinjo/Documents/Codex/2026-05-01-new-chat/tests/test_config.py)
- 설정 파일 파싱과 저장, 웹 UI 주요 요소, 안전잠금, 정적 프레임 소스 등을 검증합니다.
- 설정 계층과 웹 서비스 보조 기능의 회귀를 막는 테스트입니다.

### [tests/test_macro_runtime.py](/Users/ujinjo/Documents/Codex/2026-05-01-new-chat/tests/test_macro_runtime.py)
- 액션 시퀀스 실행, 우선순위 선택, 쿨다운 동작을 검증합니다.
- 실제 `pyautogui` 없이 가짜 백엔드를 써서 매크로 흐름을 테스트합니다.

## 추천 읽기 순서

1. [README.md](/Users/ujinjo/Documents/Codex/2026-05-01-new-chat/README.md)
2. [RUN_GUIDE_KO.md](/Users/ujinjo/Documents/Codex/2026-05-01-new-chat/RUN_GUIDE_KO.md)
3. [configs/default.json](/Users/ujinjo/Documents/Codex/2026-05-01-new-chat/configs/default.json)
4. [src/winvision_macro/main.py](/Users/ujinjo/Documents/Codex/2026-05-01-new-chat/src/winvision_macro/main.py)
5. [src/winvision_macro/web_control.py](/Users/ujinjo/Documents/Codex/2026-05-01-new-chat/src/winvision_macro/web_control.py)
6. [src/winvision_macro/actions.py](/Users/ujinjo/Documents/Codex/2026-05-01-new-chat/src/winvision_macro/actions.py)
7. [tests/test_macro_runtime.py](/Users/ujinjo/Documents/Codex/2026-05-01-new-chat/tests/test_macro_runtime.py)
