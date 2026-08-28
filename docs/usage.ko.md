# libwipi 사용 가이드

이 문서는 현재 실제로 빌드하고 에뮬레이터에서 검증한 libwipi 경로를
기준으로 새 WIPI-C 애플리케이션을 만드는 방법을 설명합니다.

이 가이드에서 기본으로 사용하는 조합은 ARAM과 WIE의 공통 테스트 경로입니다.

```text
API_LEVEL=1.2.1
PROFILE=lgt-raptor
INSTALL_PROFILE=aram-wie-raptor
```

축약 표기는 `1.2.1/lgt-raptor/aram-wie-raptor`입니다. 별도로 검증된
`1.2.1/lgt-raptor/aram-raptor` 조합은 SDK 테스트를 위한 ARAM 전용 합성
메서드를 추가합니다. 어느 조합도 LGT 실기기 전체나 다른 WIPI 버전까지
지원한다는 의미는 아닙니다.

## 1. 준비물

권장 빌드 방법은 Docker입니다.

- Git
- Docker Desktop 또는 Docker Engine
- Python 3

Docker 없이 빌드하려면 다음 도구가 PATH에 있어야 합니다.

- GNU Make
- `arm-none-eabi-gcc`
- `arm-none-eabi-ar`
- `arm-none-eabi-objdump`
- `arm-none-eabi-nm`
- Python 3

전용 상용 WIPI SDK나 devkitARM은 필요하지 않습니다.

## 2. SDK 받기와 기본 확인

```powershell
git clone https://github.com/mirusu400/libwipi.git
Set-Location libwipi
python tools/generate.py --check
python -m unittest discover -s tests -p "test_*.py"
```

재현 가능한 Arm 도구 모음 이미지를 만듭니다.

```powershell
docker build -t libwipi-toolchain -f docker/toolchain.Dockerfile .
```

SDK 전체 타깃 검사는 다음 명령으로 실행합니다.

```powershell
docker run --rm -v "${PWD}:/work" -w /work libwipi-toolchain `
  make clean all test-target
```

이 검사는 두 ABI 어댑터, 생성 코드, ARM 오브젝트 코드, ELF 구조,
패키지 구조, 시작용 애플리케이션과 플랫폼 게임 예제를 확인합니다.

## 3. Sky Hopper 예제 바로 실행하기

저장소에 포함된 `examples/platformer`는 외부 게임 자료를 사용하지 않는
원본 예제입니다. 이동, 점프, 충돌, 스크롤, 수집 요소, 장애물, 점수와
목표 지점을 구현합니다.

```powershell
docker run --rm -v "${PWD}:/work" -w /work libwipi-toolchain `
  make platformer
```

생성되는 패키지는 다음 위치에 있습니다.

```text
examples/platformer/build/wipi-1.2.1/lgt-raptor/aram-wie-raptor/libwipi-sky-hopper.zip
```

조작 방법은 다음과 같습니다.

| 동작 | 방향키 | 숫자 키패드 |
|---|---|---|
| 왼쪽 이동 | 왼쪽 | 4 |
| 오른쪽 이동 | 오른쪽 | 6 |
| 점프 | 위쪽 또는 확인 | 2 또는 5 |
| 클리어 뒤 재시작 | 확인 | 5 |

## 4. 새 애플리케이션 만들기

가장 간단한 시작 방법은 템플릿을 복사하는 것입니다.

```powershell
Copy-Item -Recurse examples/template examples/my-app
```

`examples/my-app/Makefile`에서 애플리케이션 정보를 바꿉니다.

```make
LIBWIPI_ROOT ?= ../..

APP_AID := my-wipi-app
APP_NAME := My WIPI application
APP_SOURCES := main.c
# APP_RESOURCES := assets/title.bin=res/title.bin

include $(LIBWIPI_ROOT)/mk/application.mk
```

각 변수의 의미는 다음과 같습니다.

- `APP_AID`: 패키지 식별자와 ZIP 파일 이름의 기준
- `APP_NAME`: 패키지에 기록되는 표시 이름
- `APP_SOURCES`: 공백으로 구분한 C 소스 파일 목록
- `APP_RESOURCES`: `로컬파일=패키지경로` 형식의 리소스 목록
- `LIBWIPI_ROOT`: libwipi 저장소 경로

애플리케이션 Makefile에서 ARM CPU, Thumb, soft-float, CRT, 링커 스크립트
옵션을 다시 정의하지 마십시오. `mk/application.mk`와 `mk/wipi.mk`가 이
설정을 한 묶음으로 관리합니다.

## 5. Clet 생명주기 구현하기

애플리케이션은 `<wipi/wipi.h>`를 포함하고 아래 여섯 콜백을 구현해야
합니다.

```c
#include <wipi/wipi.h>

void startClet(M_Int32 argc, M_Char *argv[]);
void destroyClet(void);
void pauseClet(void);
void resumeClet(void);
void paintClet(M_Int32 x, M_Int32 y, M_Int32 width, M_Int32 height);
void handleCletEvent(M_Int32 type, M_Int32 param1, M_Int32 param2);
```

역할은 다음과 같습니다.

- `startClet`: 초기 상태, 화면, 폰트, 타이머와 리소스를 준비합니다.
- `destroyClet`: 소유 중인 타이머, 메모리와 미디어 객체를 정리합니다.
- `pauseClet`: 백그라운드 전환에 필요한 상태를 멈춥니다.
- `resumeClet`: 일시 정지한 상태를 복구하고 화면을 다시 그립니다.
- `paintClet`: 요청된 화면 영역을 그립니다.
- `handleCletEvent`: 키 입력과 플랫폼 이벤트를 처리합니다.

최소 화면 그리기 코드는
[`examples/template/main.c`](../examples/template/main.c)에 있습니다. 게임
루프와 입력 상태를 포함한 예시는
[`examples/platformer/main.c`](../examples/platformer/main.c)를 참고하십시오.

키 이벤트는 다음 상수를 사용합니다.

```c
WIPI_CLET_EVENT_KEY_PRESS
WIPI_CLET_EVENT_KEY_RELEASE

WIPI_CLET_KEY_UP
WIPI_CLET_KEY_DOWN
WIPI_CLET_KEY_LEFT
WIPI_CLET_KEY_RIGHT
WIPI_CLET_KEY_SELECT
```

애플리케이션 코드에는 ARAM 또는 WIE 감지 분기를 넣지 마십시오. 에뮬레이터
입력값 차이는 `lgt-raptor` ABI 어댑터가 위 상수로 정규화합니다.

## 6. 메모리와 포인터 규칙

`MC_knlAlloc`과 `MC_knlCalloc`의 반환값은 C 포인터가 아니라 `M_MemID`입니다.
실제 데이터에 접근할 때마다 `MC_GETDPTR`로 현재 포인터를 얻어야 합니다.

```c
M_MemID memory_id = MC_knlAlloc(256);
M_Byte *bytes;

if (memory_id == 0) {
    return;
}
bytes = (M_Byte *)MC_GETDPTR(memory_id);
if (bytes != 0) {
    bytes[0] = 0;
}
MC_knlFree(memory_id);
```

메모리 압축이 일어날 수 있는 호출을 지난 뒤에는 이전 포인터를 계속
사용하지 마십시오. 메모리 ID는 유지하고 포인터만 다시 구해야 합니다.
리소스, 이미지, 공유 버퍼와 미디어 객체도 각 API의 소유권 규칙에 맞게
해제해야 합니다.

## 7. 빌드하고 패키지 검사하기

복사한 애플리케이션을 Docker에서 빌드하고 검사합니다.

```powershell
docker run --rm -v "${PWD}:/work" -w /work libwipi-toolchain `
  make -C examples/my-app clean package inspect
```

로컬 Arm 도구 모음을 사용하는 경우 저장소 루트에서 같은 Make 명령을
직접 실행할 수 있습니다.

```powershell
make -C examples/my-app clean package inspect
```

출력 위치는 다음 형식입니다.

```text
examples/my-app/build/wipi-1.2.1/lgt-raptor/aram-wie-raptor/my-wipi-app.zip
```

`inspect`는 외부 ZIP, 내부 JAR, `app_info`, `binary.mod`, 중복 항목,
위험한 경로와 리소스 배치를 검사합니다. 동일한 입력을 다시 빌드하면
동일한 패키지 바이트가 생성됩니다.

## 8. ARAM에서 실행하기

ARAM 개발 워크스페이스를 사용하는 경우 `aram-core`, `aram-frontend`,
`aram-authd`, `aram-emu`와 `libwipi`를 같은 상위 디렉터리에 둡니다. 패키지
절대 경로를 만든 뒤 일반 ARAM GUI 진입점으로 실행합니다.

```powershell
$package = (Resolve-Path `
  .\examples\platformer\build\wipi-1.2.1\lgt-raptor\aram-wie-raptor\libwipi-sky-hopper.zip).Path
Push-Location ..\aram-emu
try {
    go run ./cmd/aram $package
} finally {
    Pop-Location
}
```

동봉된 플랫폼 예제의 이동과 점프를 자동 검증하려면 다음 명령을
사용합니다.

```powershell
python tools/verify_aram.py --suite platformer --build-probe
```

이 검증기는 `spec/install/aram-wie-raptor.json`에 고정된 ARAM 소스 리비전을
확인합니다. 리비전이 다르면 우연히 다른 에뮬레이터 상태를 검증하지 않도록
명시적으로 실패합니다.

## 9. WIE에서 검증하기

Git, Cargo와 Rust 도구 모음이 준비되어 있으면 동봉된 플랫폼 예제를 WIE로
검증할 수 있습니다.

```powershell
python tools/verify_wie.py --suite platformer --prepare
```

`--prepare`는 `.cache/wie`에 고정된 공개 WIE 리비전을 준비합니다. 이 명령은
동봉된 예제 전용 자동 검증입니다. 새 애플리케이션은 자체 입력과 화면 변화
조건을 별도로 정의해야 합니다.

## 10. 저장소 밖에서 SDK 사용하기

애플리케이션을 별도 저장소에 둘 수도 있습니다. Makefile에서
`LIBWIPI_ROOT`를 libwipi 체크아웃의 절대 경로나 상대 경로로 지정합니다.

```make
LIBWIPI_ROOT ?= C:/sdk/libwipi

APP_AID := my-wipi-app
APP_NAME := My WIPI application
APP_SOURCES := src/main.c src/game.c
APP_RESOURCES := assets/title.bin=res/title.bin

include $(LIBWIPI_ROOT)/mk/application.mk
```

```powershell
make clean package inspect
```

`mk/application.mk`의 기본값은 `1.2.1/lgt-raptor/aram-wie-raptor`입니다.
ARAM 전용 테스트 계약이 필요하면 빌드할 때
`INSTALL_PROFILE=aram-raptor`를 지정할 수 있습니다. 이 프로필의 추가 FS,
DB, MDA 번호는 합성 에뮬레이터 계약이며 실제 LGT 기기 ABI 근거가 아닙니다.

## 11. 자주 만나는 오류

### `arm-none-eabi-gcc`를 찾지 못함

Docker 명령을 사용하거나 GNU Arm Embedded 도구 모음의 `bin` 디렉터리를
PATH에 추가하십시오.

### `API_LEVEL '2.0' is not implemented`

정상적인 실패입니다. 2.x는 명시적인 향후 목표이고 현재 구현된 API 레벨은
1.2.1입니다.

### 링크 단계의 `undefined reference`

헤더에 선언된 1.2.1 부트스트랩 API 중 일부는 해당 ABI의 제공자 메서드가
아직 확인되지 않았습니다. 현재 연결 가능한 Raptor 메서드는
[`spec/install/aram-wie-raptor.json`](../spec/install/aram-wie-raptor.json)의
`confirmed_public_methods`에서 확인할 수 있습니다.

### ARAM 검증기의 리비전 불일치

`spec/install/aram-wie-raptor.json`에 기록된 `aram`과 `runner` 리비전으로
각 저장소를 맞춘 뒤 다시 실행하십시오. 로컬 수정이 있다면 먼저 보존하고
전환해야 합니다.

### 패키지는 열리지만 화면이 나오지 않음

다음 순서로 확인하십시오.

1. `inspect`가 성공했는지 확인합니다.
2. 여섯 Clet 콜백의 이름과 시그니처를 확인합니다.
3. `MC_grpGetScreenFrameBuffer(0)` 결과가 0인지 확인합니다.
4. 그리기 뒤 `MC_grpFlushLcd`를 호출했는지 확인합니다.
5. ARAM 진단에서 미구현 WIPI 호출이 있는지 확인합니다.

## 12. 지원 범위와 실기기 검증

현재 공개 근거가 확인한 단계는 헤더, 컴파일, 링크, 패키징, 로드, 진입,
첫 프레임과 에뮬레이터 상호작용입니다. 완전한 WIPI-C 구현이나 실기기 검증
완료를 뜻하지 않습니다.

실기기 검증을 주장하려면 통신사, 제조사, 모델, 펌웨어, 설치 경로와 테스트한
패키지 해시를 함께 기록해야 합니다.

더 자세한 설계와 제한은 다음 문서를 참고하십시오.

- [영문 시작 가이드](getting-started.md)
- [아키텍처](architecture.md)
- [API 버전 정책](versioning.md)
- [메모리와 소유권](ownership.md)
- [근거와 클린룸 정책](provenance.md)
