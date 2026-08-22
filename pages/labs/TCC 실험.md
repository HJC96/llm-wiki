---
title: TCC 실험
type: lab
status: growing
tags: [distributed-transaction, concurrency, transaction]
sources: ["[[deep-dive 실험실]]"]
moc: ["[[MOC-실험]]", "[[MOC-분산시스템]]"]
repo: deep-dive/labs/distributed-transaction-tcc
created: 2026-08-16
updated: 2026-08-16
---

## 확인하려던 것

Try에서 자원을 잡고 **바로 커밋**한 뒤 Confirm·Cancel로 마무리하면, [[2PC]]의 블로킹이 정말 사라지는지. 그리고 **락이 사라진 자리에 무엇이 생기는지.**

## 실험 설계

- Testcontainers MySQL. 좌석(`seat`)·지갑(`wallet`) 두 참여자
- 확정된 것과 잡아 둔 것을 **따로 센다** — `reserved_count`(확정)와 `held_count`(예약)
- 참여자마다 상태 로그:
  ```sql
  seat_tcc_log   (request_id PK, workshop_id, seat_count, state)
  wallet_tcc_log (request_id PK, user_id,     amount,     state)
  -- state: TRIED / CONFIRMED / CANCELLED
  ```
- ★ **[[2PC 실험]]의 `PreparedLockTest`와 같은 자리에 같은 SQL을 놓고** 결과를 비교

## 결과

### ① 블로킹이 사라진다 — 같은 SQL, 뒤집힌 결과

예약 1이 Try만 해 두고 멈춘 상태에서:

```sql
SET SESSION innodb_lock_wait_timeout = 3;
UPDATE workshop_seat SET reserved_count = reserved_count + 1 WHERE id = 100;
```

| | **2PC** (`XA PREPARE` 후) | **TCC** (Try 후) |
|---|---|---|
| 같은 행 UPDATE | `ERROR 1205` 락 대기 타임아웃 | **통과** |
| 같은 행 SELECT | 커밋 전 옛 값 `0` | 잡힌 값 `2` 그대로 |
| 다른 요청의 Try | — | 통과. 나란히 잡힌다 |

🟢 **예약 1의 로컬 트랜잭션은 Try에서 이미 커밋됐으니 쥐고 있는 락 자체가 없다.** 코디네이터가 늦든 죽든 다른 요청은 영향받지 않는다.

🔴 **대신 읽는 쪽은 확정되지 않은 값을 본다. 격리를 포기한 것이다.** 2PC에서는 커밋 전 값이 아예 안 보였다.

### ② 락이 하던 일을 참여자가 떠맡는다

`TccSafetyTest`가 상태 로그 없이는 못 넘기는 네 가지를 재현한다.

| 상황 | 로그가 없으면 | 로그가 있으면 |
|---|---|---|
| Confirm이 두 번 | `reserved_count` 2 → **4. 초과 판매** | `CONFIRMED` 보고 넘어감 |
| Cancel이 두 번 | `held_count` **-2. 재고가 조용히 늘어남** | `CANCELLED` 보고 넘어감 |
| Try 없이 Cancel | 되돌릴 게 없다고 그냥 넘어감 | **빈 취소**로 `CANCELLED` 기록 |
| 그 뒤 늦은 Try | 좌석을 잡는데 아무도 확정·취소 안 함 (**매달림**) | `CANCELLED` 보고 거부 |

🟡 **마지막 두 줄이 한 쌍이다.** Try가 유실·지연돼도 코디네이터는 취소를 결정하고 Cancel을 보낸다. 참여자에게는 *본 적 없는 요청의 Cancel*이다. 되돌릴 게 없다고 그냥 넘기면 뒤늦게 도착한 Try가 잡은 좌석을 아무도 회수하지 않는다. **그래서 빈 취소는 무시가 아니라 기록이어야 한다.**

## 해석

🟡 **2PC는 데이터베이스에 맡기고 블로킹을 감수하고, TCC는 블로킹을 없애는 대신 그 몫을 애플리케이션 코드로 가져온다.**

| | 2PC | TCC |
|---|---|---|
| 1단계 | `XA PREPARE`로 멈춘다 | 자원을 잡고 **커밋한다** |
| 단계 사이 락 | 쥐고 있다 | 없다 |
| 되돌리는 주체 | DB (`XA ROLLBACK`) | **참여자가 짠 업무 로직** |
| 중간 상태 | 안 보인다 | **보인다** |
| 코디네이터 장애 | 참여자가 락을 쥔 채 멈춤 | 다른 요청은 멀쩡 |
| 참여자 조건 | XA를 지원해야 | **아무 DB나** |
| 참여자가 짤 코드 | 없다시피 | Try·Confirm·Cancel + [[멱등성]] + 빈 취소 |

🟢 **XA를 지원하지 않는 참여자(외부 결제 API·메시지 큐·NoSQL)도 낄 수 있다**는 게 실무에서 큰 차이다. 대신 참여자마다 세 벌의 로직과 상태 관리를 짜야 한다.

💬 이 표의 마지막 두 줄이 선택의 실질이다. "TCC가 더 좋다"가 아니라 **"어느 쪽 비용을 낼 것인가"**다.

## 한계

🔴 **코디네이터가 Try 다음에 죽는 경우를 안 다뤘다.** 잡아 둔 자원이 남는다. 실무는 트랜잭션 로그를 두고 재기동 시 미결 요청을 훑어 Confirm/Cancel을 마저 보내는데, 여기선 코디네이터가 테스트 메서드라 그 복구 장치가 없다.

🔴 **동시 요청을 안 다뤘다.** 테스트는 순차 실행이고 락을 하나도 안 걸었다. 서로 다른 요청이 같은 좌석을 동시에 잡으면 갱신 유실이 난다 — 둘 다 `held_count = 0`을 읽고 각자 2를 더하면 4가 아니라 2가 남는다.
> 원저자 주: **이건 TCC의 문제가 아니라 읽고-고쳐-쓰기의 문제**라 별개로 다뤄야 한다 → [[Lost Update]] · [[낙관적 락]]

🔴 시간·처리량을 재지 않았다. "블로킹이 없다"는 **성질**을 보인 것이지 빠르다는 증명이 아니다.

## 연결

- 개념: [[TCC]] — 이 실험이 뒷받침하는 개념
- 실험: [[2PC 실험]] — **같은 SQL, 뒤집힌 결과.** 반드시 나란히 읽을 것
- 개념: [[멱등성]] — 네 가지 안전 시나리오가 전부 이것
- 개념: [[Lost Update]] — 이 실험이 명시적으로 범위 밖으로 둔 것
- 개념: [[실패 사실의 기록]] — 상태 로그가 정확히 그 역할
- 코드: `~/Desktop/git/deep-dive/labs/distributed-transaction-tcc/`
- 원본: `raw/code/distributed-transaction-tcc.md`
- 면접: [[TCC는 2PC의 무엇을 해결하나]]
