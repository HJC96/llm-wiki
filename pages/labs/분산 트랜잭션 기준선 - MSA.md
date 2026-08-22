---
title: 분산 트랜잭션 기준선 - MSA
type: lab
status: growing
tags: [distributed-transaction, transaction, architecture]
sources: ["[[deep-dive 실험실]]"]
moc: ["[[MOC-실험]]", "[[MOC-분산시스템]]"]
repo: deep-dive/labs/distributed-transaction-msa
created: 2026-08-16
updated: 2026-08-16
---

## 확인하려던 것

[[분산 트랜잭션 기준선 - 모놀리식]]을 세 서비스로 쪼갰을 때 **정확히 무엇이 깨지는가.** [[2PC]]·[[TCC]] 없이 그냥 나눴을 때의 상태를 재현한다.

## 실험 설계

- 서비스 3개 · **DB 3개** — `reservation_db` / `seat_db` / `wallet_db`
- 서비스 간 통신은 HTTP
- **예약 ID를 요청 ID로 사용** — 모놀리식에서 쓰던 `reservationId`를 그대로 `requestId`로 넘긴다

## 결과

### `@Transactional`이 각자 자기 DB만 본다

```text
Reservation @Transactional → reservation_db
Seat        @Transactional → seat_db
Wallet      @Transactional → wallet_db
```

```java
@Transactional
public long reserve(long requestId, long workshopId, int seatCount) {
    WorkshopSeat workshop = workshopRepository.findById(workshopId).orElseThrow(...);
    long amount = workshop.reserve(seatCount);
    historyRepository.save(new SeatReservationHistory(requestId, workshopId, seatCount, amount));
    return amount;   // ← 응답 전에 이미 커밋된다
}
```

🟡 **HTTP 호출은 같은 트랜잭션에 참여하지 않는다.** Reservation Service가 자기 트랜잭션 안에서 Seat Service를 불러도, Seat Service는 **자신의 트랜잭션을 시작하고 응답 전에 커밋**한다.

### 부분 커밋이 실제로 남는다

좌석 커밋 후 지갑이 실패하면:

| | 상태 |
|---|---|
| 좌석 | **이미 커밋됨. 되돌릴 수단 없음** |
| 지갑·원장 | 변경 없음 |
| 예약 | 실패 |

🔴 모놀리식에서는 `ROLLBACK` 한 줄이던 것이, 여기서는 **아무것도 되돌리지 못한다.** 좌석 서비스는 자기 트랜잭션을 이미 성공적으로 끝냈고, 그걸 취소하라는 신호를 받을 통로가 없다.

## 해석

🟡 **이 실험의 값어치는 "고쳤다"가 아니라 "깨지는 걸 재현했다"에 있다.** [[2PC]]·[[TCC]]가 무엇을 푸는지는 이 상태를 본 뒤에야 의미가 생긴다.

🟢 `requestId`를 통과시킨 게 유일한 대비책이다 — 각 서비스가 이력 테이블에 `requestId`를 남기므로 **재시도가 왔을 때 이미 처리했는지 판정**할 수 있다. [[멱등성]]의 기반은 깔았지만, **되돌리는 수단은 아직 없다.**

💬 [[분산 트랜잭션 학습노트]]가 말로 설명한 "각 서비스는 자기 트랜잭션만 보장한다"가 여기서 코드와 상태로 확인된다. 두 소스가 같은 결론에 서로 다른 방식으로 닿았다.

## 한계

🔴 **보상 수단이 없다.** 이 실험은 문제를 만들고 멈춘다. 해결은 [[2PC 실험]]·[[TCC 실험]]으로 넘어간다.

🔴 **동시 요청을 다루지 않았다.** 서로 다른 요청이 같은 좌석을 동시에 잡는 [[Lost Update]]는 범위 밖이다.

🔴 네트워크 실패(타임아웃·"알 수 없음")를 재현하지 않았다. 실패는 지갑의 비즈니스 예외로만 발생시킨다.

🔴 서비스가 실제로 다른 프로세스로 뜨는지, 한 프로세스 안에서 DB만 나눈 것인지에 따라 재현도가 달라진다.

## 연결

- 실험: [[분산 트랜잭션 기준선 - 모놀리식]] — **이 실험의 대조군. 먼저 읽을 것**
- 실험: [[2PC 실험]] · [[TCC 실험]] — 여기서 깨진 것을 각각 다르게 푸는 다음 편
- 개념: [[분산 트랜잭션이 필요한 순간]] · [[부분 커밋]]
- 개념: [[멱등성]] — `requestId` 전파가 그 기반
- 코드: `~/Desktop/git/deep-dive/labs/distributed-transaction-msa/`
- 원본: `raw/code/distributed-transaction-msa.md`
