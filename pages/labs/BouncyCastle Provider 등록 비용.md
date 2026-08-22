---
title: BouncyCastle Provider 등록 비용
type: lab
status: growing
tags: [java, performance, concurrency]
sources: ["[[deep-dive 실험실]]"]
moc: ["[[MOC-실험]]", "[[MOC-Java]]"]
repo: deep-dive/labs/java-sandbox
created: 2026-08-16
updated: 2026-08-16
---

## 확인하려던 것

AES 암호화 때 **BouncyCastle Provider를 매 호출 등록하는 것과 한 번만 등록하는 것**의 비용 차이. JMH로 재고 프로파일러로 원인을 확정한다.

## 실험 설계

- JMH 벤치마크 2종 — `withProviderInitializedOnce` vs `withRepeatedProviderRegistration`
- 암호화 본 연산(`init` + `doFinal`)은 **양쪽 동일**. Provider 준비 방식만 다름
- 단일 스레드 / 8스레드 두 조건
- **18코어** 머신 실측. `-prof gc`, `-prof stack`으로 원인 검증

## 결과

| 벤치마크 | 단일(1스레드당) | 8스레드 합계 | **확장 배수** |
|---|---:|---:|---:|
| `withProviderInitializedOnce` (1회 등록) | **853,343** | 1,221,121 | **×1.4** |
| `withRepeatedProviderRegistration` (매번 등록) | 559 | 3,756 | **×6.7** |
| 격차 (once ÷ repeated) | 약 **1,526배** | 약 **325배** | |

🟢 **단일 스레드에서 1,526배 차이.** gc 프로파일이 정체를 못박는다 — repeated는 op당 **2.85MB** 할당(once 4KB의 **707배**). 매 호출 `new BouncyCastleProvider()`가 수백 개 알고리즘 매핑을 채우는 무거운 생성자라서다.

### 🔴 반전 — 빠른 쪽이 오히려 확장이 안 된다

**"전역 락을 쓰는 느린 repeated가 멀티스레드에서 더 손해 볼 것"이라는 직관과 정반대다.**

- **repeated**: ×6.7로 잘 확장(559 → 3,756). 지배 비용(객체 생성·할당)이 **스레드 로컬**이라 코어를 나눠 병렬 처리된다. `addProvider`의 전역 락은 전체에서 티끌.
- **once**: ×1.4로 거의 확장 안 됨. stack 프로파일상 **시간의 51%를 `BouncyCastleProvider.getService`(synchronized) 락 대기**로 쓴다. 18코어가 있어도 공유 Provider 모니터 하나에 줄 선다.

🟢 그래서 격차가 1,526배 → 325배로 좁혀진다. **repeated가 빨라져서가 아니라 repeated가 훨씬 더 잘 확장해서.**

## 해석

🟡 **암달의 법칙이다.** 병목은 "느려 보이는 쪽"이 아니라 **"직렬 구간 비중이 큰 쪽"**에서 터진다. once는 일 자체가 적어서 `synchronized getService` 한 군데가 곧 전체 시간이 되고, repeated는 일(할당)이 많아 그 작은 락을 병렬 작업 뒤에 숨긴다.

🔴 **프로파일러 없이는 원인을 거꾸로 짚을 뻔했다.** "멀티스레드면 차이가 무조건 커진다"는 추측이 측정 앞에서 빗나갔다. 💬 이 실험의 진짜 수확은 수치가 아니라 **추측이 틀렸다는 사실을 측정이 잡아낸 과정**이다.

🟡 **다만 결론은 불변** — 매 호출 Provider 등록을 피하라. once 경로의 `getService` 경합은 그와 별개인 BouncyCastle 내부 특성이고, 이 실험에서는 관찰까지만 한다.

## 한계

🔴 **once의 8스레드 수치는 변동이 크다.** 다른 run에서 55만~122만이 관측됐다. **"×8에 한참 못 미친다"는 경향이 핵심이지 절대값이 핵심이 아니다.**

🔴 **18코어 특정 머신·JVM의 실측값이다.** 절대값은 환경에 따라 달라진다.

🔴 **Provider 목록은 JVM 전역 상태**고 같은 fork 안에서 두 벤치마크가 순차 실행되므로 한쪽 등록분이 다른 쪽에 남는다. 초점은 "실제 추가 횟수"가 아니라 **"매 호출 생성·등록을 시도하는 경로의 비용"**이다.

🔴 `getService` 경합을 **해결하지 않았다.** 원인만 확정하고 대안(Provider 인스턴스 분리 등)은 범위 밖이다.

## 연결

- 개념: [[암달의 법칙]] — 이 실험의 결론
- 개념: [[JIT 컴파일과 워밍업]] — 벤치마크가 JMH를 쓰는 이유
- 개념: [[synchronized의 동작]] — `getService`의 모니터 경합
- 개념: [[로컬 부하 테스트의 한계]] — 절대값이 아니라 경향으로 읽기
- 코드: `~/Desktop/git/deep-dive/labs/java-sandbox/`
- 원본: `raw/code/java-sandbox.md`
