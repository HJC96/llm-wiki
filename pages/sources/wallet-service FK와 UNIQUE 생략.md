---
title: wallet-service FK와 UNIQUE 생략
type: source
kind: 대화
status: growing
tags: [mysql, lock, concurrency]
moc: ["[[MOC-출처]]", "[[MOC-결제시스템]]"]
created: 2026-08-31
updated: 2026-08-31
---

## 무엇

payment-system의 wallet-service가 `wallet_transactions.wallet_id`에 외래키를, `idempotency_key`에 UNIQUE를 걸지 않고 일반 인덱스만 두는 이유. InnoDB 락 동작을 따라가며 데드락 경로를 설명한다.

## 핵심 주장

1. InnoDB에서 자식 테이블 INSERT는 **부모 행에 공유락(S)** 을 걸고, 그 락은 커밋까지 유지된다.
2. 같은 트랜잭션이 그 부모 행을 UPDATE하면 배타락(X)이 필요하고, 두 트랜잭션이 서로의 S 락을 붙잡은 채 X를 기다리면 **락 승격 데드락**이 된다.
3. UNIQUE 인덱스 INSERT는 중복 검사를 위해 갭락/넥스트키락을 걸어, **서로 다른 키를 넣어도 인접 구간이 겹치면** 경합한다.
4. 그래서 DB 제약을 포기하고 동시 정산 처리량을 얻는 트레이드오프를 택했다. 참조 무결성과 중복 방지 책임이 애플리케이션으로 넘어온다.

## 여기서 나온 페이지

| 페이지 | 무엇을 가져갔나 |
|---|---|
| [[외래키 제약과 락 경합]] | S 락 → X 락 승격 데드락 경로, 택한 트레이드오프 표 |
| [[갭 락과 넥스트키 락]] | UNIQUE INSERT가 거는 락, 인덱스 없을 때 락 범위가 넓어지는 문제 |

## 기존 위키와의 관계

- **보강**: [[비관적 락]] — S/X 락이 명시적 `FOR UPDATE`뿐 아니라 **제약 때문에 조용히 걸린다**는 경로가 추가됐다
- **빈 링크 해소**: `[[갭 락과 넥스트키 락]]` (참조 3회. `[[비관적 락]]`과 `[[MOC-데이터베이스]]`가 기다리고 있었다)
- **⚠️ 충돌**: [[Inbox 패턴]]은 고유 제약을 중복 판정의 **최종 수단**으로 쓰라고 한다. 이 소스는 그 제약을 뺀다. 양쪽 페이지에 표시했고, 판단은 "조건이 다르다"로 남겼다

## 아직 안 다룬 것

- 🔴 **락 경합을 실제로 측정한 수치가 없다.** FK를 걸었을 때와 뺐을 때의 데드락 발생률·처리량 차이가 없으면 이 판단은 이론에 머문다. deep-dive 실험 후보로 가장 값이 큰 지점
- `SHOW ENGINE INNODB STATUS`의 실제 데드락 로그 — [[데드락 진단]] 페이지가 아직 없다
- MySQL `foreign_key_checks` 비활성화나 `READ COMMITTED` 전환 같은 다른 완화 수단과의 비교

## 원본

`raw/code/deep-dive-wallet-transactions-fk-unique-생략.md`
