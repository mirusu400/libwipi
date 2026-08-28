# libwipi 한국어 문서

`libwipi`는 WIPI-C 네이티브 애플리케이션을 GNU Arm Embedded 도구로 빌드하기
위한 독립형 C SDK입니다. 현재 구현된 공개 API 카탈로그는 WIPI-C 1.2.1이며,
지원 범위는 API 버전, 기기 ABI 프로필, 설치 프로필을 따로 지정해 표현합니다.

처음 애플리케이션을 만든다면 [상세 사용 가이드](../usage.ko.md)부터 읽으십시오.
문서와 SDK가 말하는 호환성의 경계는 [아키텍처 설명](architecture.md)에,
에뮬레이터와 피처폰 검증 절차는 [테스트 가이드](testing.md)에 정리했습니다.

## 빠른 길찾기

- [애플리케이션 만들기](../usage.ko.md): 스타터 복사, Clet 생명주기, 빌드,
  패키지 검사, ARAM/WIE 실행
- [API 사용 방식](../api-usage.md): 문서 상태, 프로필 가용성, 메모리 ID
- [WIPI-C 1.2.1 API 레퍼런스](../generated/api/1.2.1/index.md): 함수별
  프로토타입과 현재 근거
- [컴파일되는 예제 모음](../generated/examples/index.md): 소스와 테스트
  매니페스트에서 자동 추출된 API 사용 목록
- [지원표](../generated/support-matrix.md): 정확한 API/ABI/설치 조합별 현재 단계
- [테스트 번들 다운로드](../generated/downloads.md): 패키지, 소스, 근거,
  SHA-256 목록을 포함한 GitHub Release 자산

## 꼭 지켜야 할 경계

ARAM 또는 WIE에서 첫 화면과 입력을 확인했다는 사실은 실제 휴대전화 지원을
뜻하지 않습니다. 실기기 결과에는 통신사, 제조사, 모델, 펌웨어, 설치 경로,
테스트한 패키지 해시가 모두 필요합니다. 공개 헤더에 함수가 있다는 사실도
선택한 ABI 프로필에서 링크되거나 실행된다는 보장은 아닙니다.

```{toctree}
:hidden:

../usage.ko
architecture
testing
```
