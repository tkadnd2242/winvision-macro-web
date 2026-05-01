# WinVision Macro 테스트 체크리스트

이 문서는 직접 Windows에서 `WinVision Macro`를 검증할 때 순서대로 체크할 수 있는 수동 테스트 목록입니다.

## 1. 사전 준비

- [ ] 프로젝트 루트에서 `setup-windows.bat` 실행
- [ ] 필요하면 `.venv\Scripts\python.exe -m pip install -r requirements-yolo.txt` 실행
- [ ] `templates/` 폴더에 템플릿 이미지가 있거나, 웹에서 새로 크롭할 준비 완료
- [ ] YOLO를 사용할 경우 `models/best.pt` 또는 원하는 `.pt` 파일 준비
- [ ] 테스트할 프로그램 또는 게임 화면 준비

## 2. 기본 명령 확인

- [ ] `set PYTHONPATH=src`
- [ ] `python -m unittest discover -s tests` 실행
- [ ] 테스트가 통과하는지 확인
- [ ] `python -m winvision_macro --config configs/default.json --print-config-summary` 실행
- [ ] 설정 요약이 정상 출력되는지 확인

## 3. 웹 대시보드 기동

- [ ] `run-windows.bat` 실행
- [ ] 브라우저에서 `http://127.0.0.1:8765` 접속
- [ ] 메인 화면에서 `Safety Lock`, `Config Snapshot`, `Live Preview`, `Calibration Studio`가 보이는지 확인
- [ ] `Config Snapshot`에 템플릿 수와 YOLO 타깃 수가 표시되는지 확인

## 4. Safety Lock 확인

- [ ] 처음 진입 시 `Safety Lock` 상태가 `Locked`인지 확인
- [ ] `Dry run only` 체크가 기본으로 켜져 있는지 확인
- [ ] `ARM LIVE INPUT` 이외의 문자열로 arm 시도
- [ ] arm 실패 메시지가 보이는지 확인
- [ ] `ARM LIVE INPUT`를 입력하고 arm 시도
- [ ] 상태가 `Armed`로 바뀌는지 확인
- [ ] `Disarm` 클릭 시 다시 `Locked`로 바뀌는지 확인

## 5. Calibration Studio 확인

- [ ] `Capture Desktop` 클릭
- [ ] 전체 데스크톱 이미지가 보이는지 확인
- [ ] 마우스로 드래그하여 선택 박스가 그려지는지 확인
- [ ] `Left`, `Top`, `Width`, `Height` 값이 자동으로 채워지는지 확인
- [ ] 게임 창 전체를 선택 후 `Apply Region To Config` 클릭
- [ ] `Config Snapshot`에서 `capture_region` 관련 상태가 바뀌는지 확인

## 6. 템플릿 크롭 저장 확인

- [ ] 캘리브레이션 이미지에서 작은 UI 요소를 드래그
- [ ] `Template Name` 입력
- [ ] `Template Path` 비우거나 직접 입력
- [ ] `Save template metadata into the config file` 체크 유지
- [ ] `Save Template Crop` 클릭
- [ ] 지정한 파일이 `templates/` 아래에 생성되는지 확인
- [ ] `Config Snapshot` 템플릿 목록에 새 항목 또는 갱신된 항목이 보이는지 확인

## 7. Live Preview 확인

- [ ] `Detector`를 `Template Match`로 둠
- [ ] `Refresh Preview` 클릭
- [ ] 현재 화면이 미리보기로 보이는지 확인
- [ ] 감지된 템플릿이 있으면 `Detection Feed`에 이름, 점수, 액션이 표시되는지 확인
- [ ] 감지된 박스 위치가 실제 화면 요소와 맞는지 확인

## 8. CLI 드라이런 확인

- [ ] 아래 명령 실행

```bat
.venv\Scripts\python.exe -m winvision_macro --mode cli --config configs/default.json --once --dry-run
```

- [ ] 감지 결과가 콘솔에 출력되는지 확인
- [ ] 실제 마우스나 키 입력은 발생하지 않는지 확인

## 9. 정적 프레임 테스트 확인

- [ ] 테스트용 스크린샷 파일 준비
- [ ] `Frame Image`에 예: `captures/sample_screen.png` 입력
- [ ] 웹에서 `Refresh Preview` 클릭
- [ ] 실제 데스크톱 대신 저장된 이미지 기준으로 감지가 되는지 확인
- [ ] CLI에서도 아래 명령 실행

```bat
.venv\Scripts\python.exe -m winvision_macro --mode cli --config configs/default.json --once --dry-run --frame-image captures/sample_screen.png
```

- [ ] 출력이 반복 가능하게 동일하게 나오는지 확인

## 10. 액션 시퀀스 확인

- [ ] `configs/default.json`에서 `actions` 배열이 들어간 항목 확인
- [ ] `Run Once` 또는 CLI 드라이런 실행
- [ ] 로그에 `step=1`, `step=2`처럼 순서가 남는지 확인
- [ ] `move_center -> double_click_center` 같은 시퀀스가 예상대로 표시되는지 확인
- [ ] `priority`가 높은 항목이 먼저 실행되는지 확인

## 11. YOLO 연결 확인

- [ ] YOLO를 쓰지 않으면 이 섹션은 건너뜀
- [ ] `Detector`를 `YOLO`로 변경
- [ ] `YOLO Model` 경로 확인
- [ ] `YOLO Labels` 입력 또는 비움
- [ ] `Refresh Preview` 클릭
- [ ] YOLO 검출 결과가 `Detection Feed`에 보이는지 확인

## 12. 짧은 루프 드라이런 확인

- [ ] 아래 명령 실행

```bat
.venv\Scripts\python.exe -m winvision_macro --mode cli --config configs/default.json --max-loops 10 --dry-run
```

- [ ] 여러 루프가 정상 출력되는지 확인
- [ ] 쿨다운 때문에 같은 항목이 연속으로 무한 반복되지 않는지 확인

## 13. 라이브 입력 최종 확인

- [ ] 반드시 테스트 대상 창만 열어둠
- [ ] 웹에서 `Safety Lock`을 `Armed` 상태로 전환
- [ ] `Dry run only`를 끔
- [ ] 먼저 `Run Once`로 1회만 실행
- [ ] 실제 클릭/키 입력이 예상한 위치와 대상에만 발생하는지 확인
- [ ] 이상 없을 때만 `Start Loop` 사용
- [ ] 테스트 후 `Disarm`으로 다시 잠금

## 14. 실패 시 바로 볼 것

- [ ] 감지가 안 되면 `capture_region`과 템플릿 이미지 크기 확인
- [ ] 템플릿 매칭이 약하면 `threshold` 조정
- [ ] 액션이 안 나가면 `Dry run only` 상태와 `Safety Lock` 상태 확인
- [ ] CLI가 모듈을 못 찾으면 `set PYTHONPATH=src` 확인
- [ ] YOLO가 안 되면 `.pt` 경로, `ultralytics` 설치, 라벨 이름 일치 여부 확인

## 15. 테스트 결과 기록

- [ ] 어떤 화면 해상도에서 테스트했는지 기록
- [ ] 어떤 템플릿이 잘 동작했는지 기록
- [ ] 오탐이 난 UI 요소 기록
- [ ] 실제 입력 시 위험했던 상황 기록
- [ ] 다음 수정 우선순위 정리
