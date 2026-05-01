# WinVision Macro 실행 가이드

이 문서는 Windows 환경에서 `WinVision Macro`를 처음 실행할 때 필요한 순서를 한 번에 정리한 안내서입니다.

## 1. 준비물

- Windows PC
- Python 3.11 이상 권장
- 게임 또는 대상 프로그램이 실행되는 화면
- `OpenCV`와 `pyautogui`를 설치할 수 있는 인터넷 연결
- YOLO를 쓸 경우 학습된 모델 파일 `.pt`

## 2. 프로젝트 설치

프로젝트 루트에서 아래 순서로 실행합니다.

```bat
setup-windows.bat
```

이 스크립트는 보통 아래 작업을 처리합니다.

- `.venv` 가상환경 생성
- `pip` 업그레이드
- `requirements.txt` 설치

YOLO까지 사용할 경우 추가로 설치합니다.

```bat
.venv\Scripts\python.exe -m pip install -r requirements-yolo.txt
```

## 3. YOLO 모델 파일 위치

학습된 YOLO 모델 파일은 기본적으로 아래 경로에 둡니다.

```text
models/best.pt
```

다른 파일명을 써도 괜찮지만, 그 경우 웹 대시보드의 `YOLO Model` 입력칸이나 `configs/default.json`의 `yolo.model_path`를 같은 경로로 바꿔야 합니다.

예시:

```text
models/game_enemy.pt
```

## 4. 웹 대시보드 실행

가장 추천하는 실행 방법은 웹 대시보드입니다.

```bat
run-windows.bat
```

실행 후 브라우저에서 아래 주소를 엽니다.

```text
http://127.0.0.1:8765
```

웹 화면에서 바로 보게 될 핵심 영역:

- `Safety Lock`: 실제 마우스와 키 입력 잠금
- `Config Snapshot`: 현재 설정 파일 내용 요약
- `Live Preview`: 현재 감지 상태 확인
- `Calibration Studio`: 화면 영역 및 템플릿 크롭 저장

## 5. 첫 실행 순서

처음에는 아래 순서대로 진행하면 됩니다.

1. `Write Sample Config`를 눌러 샘플 설정 파일을 만듭니다.
2. `Calibration Studio`에서 `Capture Desktop`을 눌러 전체 화면을 캡처합니다.
3. 게임 창 전체를 드래그해서 선택합니다.
4. `Apply Region To Config`를 눌러 선택 영역을 `capture_region`에 저장합니다.
5. 다시 작은 UI 요소를 드래그합니다.
6. `Save Template Crop`으로 `templates/` 아래에 템플릿 이미지를 저장합니다.
7. `Dry run only`를 켠 상태로 `Refresh Preview` 또는 `Run Once`로 감지 결과를 확인합니다.
8. 검출이 안정적일 때만 `Dry run only`를 끄고 `Start Loop`를 사용합니다.

정적 이미지로 테스트하고 싶다면 `Frame Image` 입력칸에 저장된 스크린샷 경로를 넣으면 됩니다.
예:

```text
captures/sample_screen.png
```

## 6. 템플릿 매칭 모드 사용

템플릿 매칭만 사용할 경우:

- `Detector`를 `Template Match`로 둡니다.
- `templates/` 폴더에 잘라낸 이미지가 있어야 합니다.
- `configs/default.json` 안의 `templates` 항목이 실제 파일 경로와 맞아야 합니다.

이 방식은 간단하지만 해상도, UI 배치, 창 크기 변화에 민감합니다.

## 7. YOLO 모드 사용

YOLO를 사용할 경우:

1. `requirements-yolo.txt`를 설치합니다.
2. 학습된 `.pt` 파일을 `models/`에 둡니다.
3. 웹 대시보드에서 `Detector`를 `YOLO`로 바꿉니다.
4. `YOLO Model`에 모델 경로를 입력합니다.
5. 필요하면 `YOLO Confidence`와 `YOLO Labels`를 조정합니다.

`YOLO Labels` 예시:

```text
enemy, confirm, skill_ready
```

## 8. CLI 실행 방법

웹 대신 터미널에서 한 번만 실행하고 싶다면:

```bat
run-cli-windows.bat
```

직접 명령으로 실행하려면:

```bat
.venv\Scripts\python.exe -m winvision_macro --mode cli --config configs/default.json --once
```

웹 서버 모드를 직접 띄우려면:

```bat
.venv\Scripts\python.exe -m winvision_macro --mode web --config configs/default.json --host 127.0.0.1 --port 8765
```

## 9. 매크로 액션 설정 방법

이제 각 템플릿이나 YOLO 타깃은 단일 `action` 하나만 써도 되고, 여러 단계를 가진 `actions` 배열도 쓸 수 있습니다.

지원하는 대표 액션:

- `click_center`
- `double_click_center`
- `right_click_center`
- `move_center`
- `press_key`
- `hotkey`
- `type_text`
- `scroll`
- `wait`

자주 쓰는 필드:

- `priority`: 어떤 감지가 먼저 실행될지 결정
- `repeat`: 클릭 또는 키 입력 반복 횟수
- `interval_seconds`: 반복 간격
- `duration_seconds`: 마우스 이동 시간 또는 wait 시간
- `offset_x`, `offset_y`: 감지 중심점 기준 클릭 오프셋
- `post_delay_seconds`: 액션 직후 대기

예시:

```json
{
  "name": "confirm_button",
  "path": "templates/confirm_button.png",
  "threshold": 0.94,
  "cooldown_seconds": 1.0,
  "priority": 30,
  "actions": [
    { "type": "move_center", "duration_seconds": 0.05 },
    { "type": "double_click_center", "post_delay_seconds": 0.1 },
    { "type": "press_key", "key": "1" }
  ]
}
```

## 10. 매크로를 안전하게 테스트하는 방법

드라이런으로 먼저 테스트하면 실제 마우스와 키 입력 없이 로그만 확인할 수 있습니다.

1회 테스트:

```bat
.venv\Scripts\python.exe -m winvision_macro --mode cli --config configs/default.json --once --dry-run
```

짧은 루프 테스트:

```bat
.venv\Scripts\python.exe -m winvision_macro --mode cli --config configs/default.json --max-loops 10 --dry-run
```

실제 입력 테스트:

```bat
.venv\Scripts\python.exe -m winvision_macro --mode cli --config configs/default.json --max-loops 10 --live
```

저장된 프레임 이미지로 테스트:

```bat
.venv\Scripts\python.exe -m winvision_macro --mode cli --config configs/default.json --once --dry-run --frame-image captures/sample_screen.png
```

현재 설정 요약만 보고 싶을 때:

```bat
.venv\Scripts\python.exe -m winvision_macro --config configs/default.json --print-config-summary
```

## 11. 자동 테스트 실행

코드 자체가 깨지지 않았는지 확인하려면 아래 테스트를 실행합니다.

```bat
set PYTHONPATH=src
python -m unittest discover -s tests
```

현재 테스트에는 아래 내용이 포함됩니다.

- 설정 파일 파싱
- 액션 시퀀스 실행
- 감지 우선순위 처리
- 쿨다운 처리
- 웹 UI 주요 요소 존재 여부

## 12. 자주 확인할 파일

- `configs/default.json`: 실행 설정 파일
- `templates/`: 템플릿 매칭용 이미지
- `models/`: YOLO 모델 파일
- `src/winvision_macro/web_control.py`: 웹 대시보드
- `src/winvision_macro/vision.py`: 템플릿 매칭과 YOLO 검출기

## 13. 문제 생길 때 먼저 볼 것

- `pyautogui is not installed`
  - `setup-windows.bat`를 다시 실행하거나 `requirements.txt` 설치를 확인합니다.

- `opencv-python is not installed`
  - `requirements.txt` 설치 상태를 확인합니다.

- `YOLO mode needs ultralytics`
  - `requirements-yolo.txt`를 추가 설치합니다.

- 템플릿 검출이 안 됨
  - 캡처 영역이 정확한지 확인합니다.
  - 템플릿 이미지가 현재 화면과 같은 해상도와 UI 상태인지 확인합니다.
  - `threshold`를 조금 낮춰봅니다.

- YOLO 검출이 안 됨
  - `.pt` 파일 경로가 맞는지 확인합니다.
  - 학습한 클래스 이름과 `YOLO Labels`가 같은지 확인합니다.
  - confidence 값이 너무 높은지 확인합니다.

## 14. 안전하게 테스트하는 방법

- 처음에는 항상 `Dry run only`를 켭니다.
- `Run Once`로 1회 동작만 먼저 확인합니다.
- `Live Preview`에서 박스 위치가 맞는지 보고 진행합니다.
- 실제 입력은 충분히 검증된 뒤에만 켭니다.
- 웹 대시보드에서 라이브 입력 전에는 `Safety Lock`을 먼저 해제해야 합니다.

## 15. 추천 작업 순서

1. 웹 대시보드 실행
2. 캘리브레이션으로 게임 창 영역 저장
3. 템플릿 몇 개 저장
4. `Template Match`로 기본 동작 확인
5. 필요하면 YOLO 모델 연결
6. dry-run 검증
7. 실제 입력 활성화
