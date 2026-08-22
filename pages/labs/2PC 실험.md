---
title: 2PC 실험
type: lab
status: growing
tags: [distributed-transaction, transaction, mysql]
sources: ["[[deep-dive 실험실]]"]
moc: ["[[MOC-실험]]", "[[MOC-분산시스템]]"]
repo: deep-dive/labs/distributed-transaction-2pc
created: 2026-08-16
updated: 2026-08-16
---

## 확인하려던 것

MySQL `XA` SQL로 prepare·commit을 **직접 실행**해서, [[2PC]]가 부분 커밋을 없애는 대신 무엇을 대가로 내주는지 눈으로 본다.

## 실험 설계

- Testcontainers **MySQL 8** 두 개 (`seat_db`, `wallet_db`)
- 코디네이터는 **테스트 메서드의 제어 흐름** — 라이브러리 없이 `XA START` → `XA END` → `XA PREPARE` → `XA COMMIT`을 직접 실행
- 한 프로세스가 두 DB에 직접 붙는다 (HTTP로 서비스를 나누지 않음)
- 시나리오: ① 전원 성공 ② 지갑 실패 → 전원 롤백 ③ **prepare 직후 코디네이터 사망**

## 결과

**① in-doubt 트랜잭션이 실제로 매달린다**

`prepare_직후_코디네이터가_죽으면_결정이_올_때까지_락이_남는다` — 좌석이 prepare한 직후 코디네이터가 죽고 커넥션까지 끊긴다.

🟢 **prepared 트랜잭션은 커넥션이 끊겨도 사라지지 않는다.** 문제는 원래 커넥션이 없어졌으니 *이 트랜잭션이 매달려 있다는 사실 자체를 아무도 모른다*는 것.

```sql
XA RECOVER;
-- formatID=1  gtrid_length=13  bqual_length=4  data=reservation-1seat
```

`XA RECOVER`는 "이 서버에 지금 prepare된 채 결정을 기다리는 트랜잭션이 뭐가 있는지"를 **서버에 직접 묻는 명령**이다. 어느 커넥션이 만들었는지와 무관하게 찾아주므로, 새로 접속한 커넥션에서 `XA COMMIT`/`XA ROLLBACK`으로 마무리할 수 있다.

**② 그동안 다른 요청은 그냥 막힌다**

```sql
SET SESSION innodb_lock_wait_timeout = 3;
UPDATE workshop_seat SET reserved_count = reserved_count + 1 WHERE id = 100;
-- ERROR 1205: Lock wait timeout exceeded
```

| 다른 커넥션이 하는 일 | 결과 |
|---|---|
| 같은 행 UPDATE | **ERROR 1205** 락 대기 타임아웃 |
| 같은 행 SELECT | 커밋 전 옛 값 `0` |

## 해석

🟡 **투표를 받고도 결정을 못 들으면 참여자는 혼자서 커밋도 롤백도 판단할 수 없다.** 커밋하자니 다른 참여자가 NO였을 수 있고, 롤백하자니 이미 YES를 약속했다. 이 교착이 [[2PC]]가 "블로킹 프로토콜"인 이유의 전부다.

🟢 **JTA를 쓰면 편해지는 건 코드지 성질이 아니다.**

| 이 실험실 | 실무 (JTA) |
|---|---|
| 테스트 메서드의 제어 흐름 | Narayana · Atomikos |
| `XA START` … `XA PREPARE` SQL | `XAResource.start()` … `prepare()` |
| 결정을 어디에도 안 적음 | 트랜잭션 로그 (ObjectStore, `tmlog`) |
| 손으로 `XA RECOVER` | 매니저가 재기동 시 자동 복구 |

애플리케이션 코드는 `@Transactional` 하나로 끝나지만 **블로킹은 그대로 남는다.**

💬 그래서 "2PC 아세요?"에 *"느려서요"*가 아니라 *"결정을 아는 쪽이 나타날 때까지 락을 쥔 채 멈춥니다"*라고 답해야 한다. → [[2PC의 문제는 무엇인가]]

## 한계

🔴 **코디네이터 결정 로그가 없다.** 실제 트랜잭션 매니저는 결정을 파일에 적고 재기동 시 읽어 복구하는데, 이 실험은 "결정을 아는 쪽이 없으면 못 푼다"까지만 보이고 멈춘다. **복구 자동화는 재현되지 않았다.**

🔴 **서비스를 나누지 않았다.** 한 프로세스가 두 DB에 직접 붙는다. 실제 MSA라면 prepare한 트랜잭션을 *요청과 요청 사이에* 열어 둬야 하는데, 그 어려움 자체가 "왜 MSA에서 안 쓰나"의 내용이라 실험에서는 피해 갔다.

🔴 **H2로는 재현이 안 된다.** prepare로 멈춘 트랜잭션이 커넥션 종료 후에도 살아남고 `XA RECOVER`로 찾을 수 있어야 하는데 H2는 지원하지 않는다 → [[H2와 실제 DB의 방언 차이]]

🔴 시간·처리량을 재지 않았다. 이 실험이 보여주는 것은 **동작의 성질**이지 성능 수치가 아니다.

## 연결

- 개념: [[2PC]] — 이 실험이 뒷받침하는 개념
- 실험: [[TCC 실험]] — **같은 자리에 같은 SQL을 놓고 결과가 뒤집힌다.** 반드시 나란히 읽을 것
- 개념: [[실패 사실의 기록]] — in-doubt를 발견 가능하게 만드는 것이 왜 필요한지
- 코드: `~/Desktop/git/deep-dive/labs/distributed-transaction-2pc/`
- 원본: `raw/code/distributed-transaction-2pc.md`
- 면접: [[2PC의 문제는 무엇인가]]
