# MOVE AI 2026 - VCM

## 실시간 교통 정보를 반영한 차량 경로 재최적화 시스템

현대글로비스 **MOVE AI Challenge 2026**
**Team VCM**

본 프로젝트는 물류 차량의 초기 배송 경로를 최적화하고, 운행 중 발생하는 **교통사고, 돌발상황, 교통 정체 등 실시간 교통 변화에 대응하여 차량 경로를 재최적화하는 의사결정 지원 시스템**입니다.

기존의 정적인 차량 경로 계획에서 나아가 다음 기능을 하나의 시스템으로 구현하는 것을 목표로 합니다.

* 시간대별 교통상황을 고려한 초기 운송계획 수립
* 실시간 교통 및 돌발상황 모니터링
* 사고 및 정체 발생 시 영향 차량 탐지
* 실시간 교통상황을 반영한 경로 재계산
* 다양한 Rerouting 대안 생성 및 비교
* 의사결정자가 선택한 수정 경로를 차량 운영계획에 반영

---

# 1. 프로젝트 개요

물류 차량의 운송계획은 출발 시점에 최적의 경로를 생성하는 것만으로 충분하지 않습니다.

실제 도로에서는 차량 운행 중 다음과 같은 상황이 지속적으로 발생할 수 있습니다.

* 교통사고
* 도로 정체
* 도로 통제
* 공사
* 기상 악화
* 특정 구간의 예상치 못한 이동시간 증가

이러한 상황이 발생하면 초기 시점에 생성한 최적 경로가 더 이상 최적이지 않을 수 있으며, 배송 지연과 추가 운송비용이 발생할 수 있습니다.

VCM은 이를 해결하기 위해 **Time-Dependent Multi-Depot Vehicle Routing Problem with Time Windows(TD-MDVRPTW)**를 기반으로 초기 운송계획을 생성합니다.

이후 차량 운행 중 실시간 교통상황이 변화하면 해당 정보를 도로 네트워크에 반영하고, 기존 운송계획에 대한 영향을 분석하여 새로운 Rerouting 대안을 생성합니다.

---

# 2. 핵심 기능

본 시스템은 크게 다음 네 가지 기능으로 구성됩니다.

## 2.1 Initial Route 생성

운행 시작 전 **ALNS(Adaptive Large Neighborhood Search)**를 이용하여 초기 차량 경로를 생성합니다.

초기 경로 생성 시 다음 요소를 함께 고려합니다.

* 다중 Depot
* 차량별 고객 할당
* 고객 방문 순서
* 차량 적재용량
* 고객 Time Window
* 시간대별 교통상황
* 차량 운행거리
* 차량 이동시간
* 배송 지연
* 차량 운영비용

사용자는 웹 애플리케이션에서 운영 목적과 배차 조건을 설정한 뒤 Initial Route를 생성할 수 있습니다.

---

## 2.2 실시간 교통상황 반영

차량 운행 중 교통사고 또는 정체가 발생하면 해당 도로 구간의 이동시간을 업데이트합니다.

실시간 교통 이벤트를 기존 Physical Road Network와 연결하여 사고가 발생한 도로 구간을 식별하고 새로운 이동시간을 반영합니다.

이를 통해 초기 계획에서 사용한 이동시간과 현재 교통상황을 반영한 이동시간을 구분할 수 있습니다.

---

## 2.3 실시간 Rerouting

돌발상황으로 기존 차량 경로에 지연이 예상될 경우 새로운 운송계획을 생성합니다.

현재 시스템에서는 다음 세 가지 대응방안을 고려합니다.

1. **경로 우회**
2. **방문 순서 변경**
3. **업무 승계 및 재배차**

각 대안별 예상 지연시간, 이동시간, 이동거리, 차량 운영비용 등을 비교하여 의사결정자가 적절한 대응방안을 선택할 수 있도록 지원합니다.

---

## 2.4 Dynamic Fleet Control Tower

최적화 및 Rerouting 결과를 운영자가 직관적으로 확인할 수 있도록 웹 기반 Control Tower를 구현했습니다.

웹 애플리케이션은 크게 다음 세 화면으로 구성됩니다.

* 통합 관제 Dashboard
* Initial Route
* Rerouting

---

# 3. 시간대별 교통상황 반영

본 프로젝트는 단순한 거리 기반 VRP가 아니라 **시간대에 따라 이동시간이 달라지는 Time-Dependent VRP**를 사용합니다.

예를 들어 동일한 구간 `A → B`라도 출발 시간에 따라 이동시간이 달라질 수 있습니다.

```text
08:00 출발 → 32분
09:00 출발 → 47분
10:00 출발 → 39분
```

따라서 각 도로 Edge별로 시간대별 이동시간 정보를 관리합니다.

```text
edge_id
hour
travel_time_min
speed_kph
data_source
```

현재 기본 네트워크에서는 **06:00부터 22:00까지 1시간 단위의 시간대별 Snapshot**을 사용합니다.

차량이 특정 시간대에 출발하면 해당 시간대의 도로 가중치를 기준으로 이동시간과 최단경로를 계산합니다.

---

# 4. 도로 네트워크

## 4.1 데이터

도로 네트워크는 국토교통부 ITS 국가표준 **NODELINKDATA**를 기반으로 구축합니다.

전국 전체 도로 네트워크를 그대로 최적화에 사용할 경우 계산량이 매우 커질 수 있기 때문에 주요 도로 연결 구조를 보존하면서 네트워크를 단순화합니다.

네트워크 구축 과정은 다음과 같습니다.

```text
ITS NODELINKDATA
        ↓
고속도로 / 도시고속도로 / 주요 일반국도 추출
        ↓
주요 IC / JCT / 분기점 유지
        ↓
단순 통과 노드 축소
        ↓
도로 Backbone 생성
        ↓
Depot / Customer 연결
        ↓
Physical Network 생성
        ↓
시간대별 Edge 이동시간 생성
        ↓
TDVRP Virtual Network 생성
```

---

# 5. Physical Network

현재 구축된 Physical Network는 다음과 같습니다.

```text
Physical Node : 255개
 ├─ ROAD     : 200개
 ├─ DEPOT    : 5개
 └─ CUSTOMER : 50개

Directed Edge : 1,528개
```

Depot과 Customer는 실제 Backbone의 인접 도로 Node와 Connector Edge를 이용하여 연결됩니다.

Physical Network는 실제 차량이 이동할 수 있는 도로 수준의 경로를 표현합니다.

---

# 6. Physical Network와 TDVRP Network

최적화 알고리즘이 매번 255개의 Physical Node 전체에 대해 최단경로를 탐색하면 계산시간이 크게 증가할 수 있습니다.

이를 해결하기 위해 **Service Node 기반의 Virtual Network**를 별도로 구성합니다.

Service Node는 다음과 같습니다.

```text
Depot    : 5개
Customer : 50개
----------------
총       : 55개
```

ALNS와 MILP는 기본적으로 55개의 Service Node를 대상으로 최적화 문제를 해결합니다.

예를 들어 최적화 모델에서

```text
C001 → C007
```

이라는 Arc는 실제 도로에서 하나의 Edge를 의미하지 않습니다.

실제로는 다음과 같은 Physical Path가 될 수 있습니다.

```text
C001
 ↓
R017
 ↓
R042
 ↓
R061
 ↓
C007
```

해당 Physical Path와 이동시간을 사전에 계산하여 저장함으로써 최적화 과정에서는 빠른 Lookup이 가능합니다.

---

# 7. TD OD Matrix

최적화 알고리즘에서 사용하는 시간대별 OD 이동시간은 `td_od_matrix.csv`에 저장됩니다.

```text
from_node
to_node
hour
travel_time_min
distance_km
```

각 Service Node 쌍에 대하여 시간대별 이동시간과 거리를 저장합니다.

---

# 8. TD Path

실제 도로 경로를 복원하기 위한 정보는 `td_paths.csv`에 저장됩니다.

```text
from_node
to_node
hour
travel_time_min
distance_km
path_nodes
path_edges
```

Initial Route 시각화 및 실시간 Rerouting 단계에서는 해당 데이터를 이용하여 Virtual Arc를 실제 Physical Road Path로 변환할 수 있습니다.

---

# 9. 현재 TDVRP Network 규모

현재 생성된 네트워크의 규모는 다음과 같습니다.

```text
Physical Nodes         : 255
Physical Directed Edge : 1,528

Service Nodes          : 55
 ├─ Depot              : 5
 └─ Customer           : 50

시간대                 : 17개
운영시간               : 06:00 ~ 22:00

OD-Hour Entry          : 50,490
Unreachable OD Pair    : 0
```

Service Node 55개에 대해 자기 자신을 제외한 모든 OD Pair와 17개 시간대를 고려하면 다음과 같습니다.

```text
55 × 54 × 17 = 50,490
```

ALNS는 해당 데이터를 Lookup하여 시간대별 이동시간을 평가합니다.

---

# 10. 차량경로 최적화 문제

본 프로젝트의 기본 최적화 문제는 **TD-MDVRPTW**입니다.

주요 의사결정은 다음과 같습니다.

* 어떤 차량을 사용할 것인가
* 어떤 고객을 어떤 차량에 할당할 것인가
* 각 차량이 고객을 어떤 순서로 방문할 것인가
* 각 구간을 어느 시간대에 이동할 것인가
* 차량이 마지막 고객 방문 후 어느 Depot으로 이동할 것인가

각 차량은 지정된 출발 Depot에서 출발하지만 반드시 동일한 Depot으로 돌아올 필요는 없습니다.

즉, 다음과 같은 **Flexible End Depot** 구조를 사용합니다.

```text
지정된 출발 Depot
        ↓
     Customer
        ↓
     Customer
        ↓
       ...
        ↓
선택 가능한 종료 Depot
```

---

# 11. 주요 제약조건

최적화 과정에서는 다음 제약조건을 고려합니다.

* 모든 고객은 정확히 한 번 서비스
* 차량별 고객 할당
* 차량 방문 순서 연결
* 차량 적재용량 제한
* 고객 Time Window
* 차량 운행 가능시간
* 시간대별 이동시간
* Depot 출발 조건
* 종료 Depot 선택
* 차량 사용 여부
* 경로 연결 가능성

기본 Time Window 방식은 `SOFT`입니다.

따라서 Time Window를 초과하더라도 해당 경로를 불가능한 것으로 처리하지 않고 **Tardiness**로 계산합니다.

필요한 경우 다음 옵션을 통해 HARD Time Window도 사용할 수 있습니다.

```bash
--time-window-mode HARD
```

---

# 12. 최적화 목적

본 시스템에서는 다음 목적함수를 독립적으로 사용할 수 있습니다.

```text
TARDINESS
TRAVEL_TIME
DISTANCE
VEHICLE_COST
```

각 목적은 다음을 의미합니다.

### TARDINESS

고객의 Time Window를 초과한 배송 지연시간을 최소화합니다.

### TRAVEL_TIME

전체 차량의 총 이동시간을 최소화합니다.

### DISTANCE

전체 차량의 총 운행거리를 최소화합니다.

### VEHICLE_COST

운영에 투입되는 차량 수 및 차량 운영비용을 최소화합니다.

웹 애플리케이션에서는 해당 목적들을 운영자가 쉽게 이해할 수 있도록 다음과 같은 운영 목표 형태로 제공합니다.

* 균형 설정
* 빠른 배송
* 고객 만족도
* 비용 절감

---

# 13. ALNS

대규모 TDVRP 문제를 빠르게 해결하기 위해 **Adaptive Large Neighborhood Search(ALNS)**를 사용합니다.

ALNS는 초기해를 생성한 후 현재 해의 일부 고객을 제거하고 다시 삽입하는 과정을 반복하면서 해를 개선합니다.

기본 탐색 과정은 다음과 같습니다.

```text
초기해 생성
   ↓
Destroy Operator
   ↓
Repair Operator
   ↓
Local Search
   ↓
후보해 평가
   ↓
수락 여부 결정
   ↓
Operator Weight 갱신
   ↓
반복 탐색
```

ALNS는 선택된 목적함수를 기준으로 후보해를 평가합니다.

주요 구성요소는 다음과 같습니다.

* Initial Solution
* Destroy Operator
* Repair Operator
* Local Search
* Simulated Annealing Acceptance
* Operator Reward
* Adaptive Operator Weight Update

---

# 14. Initial Route 생성

웹 애플리케이션의 **Initial Route** 화면에서는 차량 운행 전 초기 운송계획을 생성할 수 있습니다.

사용자는 다음 운영조건을 설정할 수 있습니다.

```text
최적화 목표
배차 트럭 수
출발 Depot
Time Window 중요도
차량 적재용량
교통 데이터 반영 여부
```

조건을 설정한 후 **최적화 실행** 버튼을 선택하면 ALNS가 초기 경로를 생성합니다.

Initial Route에서는 다음 의사결정을 동시에 수행합니다.

* 차량 사용 여부
* 고객별 차량 할당
* 고객 방문 순서
* 시간대별 이동시간 반영
* 차량별 운송경로 생성

---

# 15. Initial Route 결과

최적화가 완료되면 차량별 경로를 지도에서 확인할 수 있습니다.

차량별로 다음 정보를 제공합니다.

* 차량 ID
* 담당 운전자
* 출발 Depot
* 종료 Depot
* 할당 고객
* 고객 방문 순서
* 총 운행거리
* 예상 운행시간
* 차량 적재량
* 적재율
* 배송 예정시간

전체 Fleet에 대해서는 다음 KPI를 제공합니다.

* 총 운행거리
* 총 운행시간
* 사용 차량 수
* 배송 지연 건수
* 총 배송 지연시간

---

# 16. 운행 시뮬레이션

Initial Route 화면에서는 생성된 차량 운행계획을 시간 흐름에 따라 확인할 수 있도록 운행 시뮬레이션 기능을 제공합니다.

차량은 다음과 같이 이동합니다.

```text
Depot
  ↓
Customer
  ↓
Customer
  ↓
Customer
  ↓
End Depot
```

시뮬레이션을 통해 시간에 따른 차량의 위치와 배송 진행상황을 확인할 수 있습니다.

운행 도중 돌발상황이 발생할 경우 해당 차량의 기존 운송계획에 미치는 영향을 분석하고 Rerouting 단계로 연결합니다.

---

# 17. 실시간 교통 및 돌발상황 감지

Initial Route가 생성된 이후 실제 차량 운행 중에는 새로운 교통상황이 발생할 수 있습니다.

시스템에서는 다음과 같은 돌발상황을 고려할 수 있습니다.

* 교통사고
* 교통 정체
* 도로 통제
* 공사
* 기상 변화
* 특정 구간의 이동시간 증가

돌발상황이 발생하면 다음 정보를 확인할 수 있습니다.

* 사고 위치
* 사고 유형
* 사고 발생시간
* 예상 지속시간
* 해당 도로구간
* 예상 추가 지연시간
* 영향 차량
* 영향받는 운송경로

---

# 18. 실시간 도로 그래프 업데이트

실시간 교통 이벤트가 발생하면 기존 Physical Network의 해당 Edge에 새로운 이동시간을 반영합니다.

처리 과정은 다음과 같습니다.

```text
실시간 교통 이벤트 입력
        ↓
ITS Link ID 확인
        ↓
Physical Edge와 매칭
        ↓
해당 Edge의 이동시간 수정
        ↓
시간대별 Edge Profile 업데이트
        ↓
Shortest Path 재계산
        ↓
TD OD Matrix 업데이트
        ↓
영향 차량 탐지
        ↓
Rerouting 실행
```

UTIC 등 외부 교통정보에서 제공되는 `linkId` 또는 `lineLinkId`를 Physical Edge의 원본 ITS Link ID와 연결하여 실제 사고가 발생한 도로구간을 찾을 수 있도록 구성합니다.

여러 개의 사고 또는 교통 이벤트가 동시에 발생하는 경우에도 동일한 Physical Network에 함께 반영할 수 있습니다.

---

# 19. Rerouting

돌발상황 발생 이후 시스템은 전체 차량의 계획을 처음부터 다시 생성하는 대신 기존 계획을 최대한 활용하면서 필요한 부분만 수정하는 Rerouting 방식을 사용합니다.

현재 시스템에서는 세 가지 주요 대응 대안을 제공합니다.

```text
① 경로 우회
② 방문 순서 변경
③ 업무 승계 / 재배차
```

각 전략은 기존 운송계획의 변경 수준이 서로 다릅니다.

---

# 20. 경로 우회

**내부 전략명: `DETOUR`**

현재 차량의 고객 할당과 방문 순서를 유지하면서 사고 또는 정체가 발생한 도로만 우회합니다.

기존 경로가 다음과 같다고 가정합니다.

```text
Depot
  ↓
C01
  ↓
C03
  ↓
사고 발생 도로
  ↓
C07
  ↓
C09
```

사고 발생 후에는 고객 방문 순서는 유지하면서 Physical Road Path만 변경합니다.

```text
Depot
  ↓
C01
  ↓
C03
  ↘
   대체 도로
       ↘
        C07
         ↓
        C09
```

### 특징

* 차량 변경 없음
* 고객 할당 변경 없음
* 방문 순서 변경 없음
* 실제 이동 도로만 변경
* 기존 운영계획 변경 최소화

세 가지 전략 중 가장 보수적인 대응 방법입니다.

---

# 21. 방문 순서 변경

**내부 전략명: `REROUTE`**

단순한 도로 우회만으로 배송 지연을 충분히 줄이기 어려운 경우 현재 차량이 담당하는 고객의 방문 순서를 변경합니다.

예를 들어 기존 경로가

```text
Depot → C01 → C03 → C07 → C09
```

라면 다음과 같이 변경할 수 있습니다.

```text
Depot → C01 → C09 → C03 → C07
```

새로운 교통상황이 반영된 TD OD Matrix를 기준으로 남은 고객들의 방문 순서를 다시 평가합니다.

### 특징

* 기존 차량 유지
* 고객 할당은 최대한 유지
* 고객 방문 순서 변경 가능
* 사고 및 정체 구간 회피 가능
* 배송 지연 감소 가능
* DETOUR보다 기존 계획의 변경 수준이 큼

---

# 22. 업무 승계 및 재배차

**내부 전략명: `NEW_TRUCK`**

심각한 사고 또는 정체로 인해 기존 차량만으로 배송 지연을 해결하기 어려운 경우 새로운 차량을 추가로 투입합니다.

기존 계획이 다음과 같다고 가정합니다.

```text
Truck T02

C01 → C03 → C07 → C09
```

Truck T02가 사고로 인해 큰 지연을 받으면 일부 작업을 다른 차량에 이관할 수 있습니다.

```text
Truck T02
C01 → C03

Truck T05
C07 → C09
```

### 특징

* 신규 차량 투입 가능
* 고객 재할당 가능
* 기존 차량의 일부 업무 승계
* 심각한 배송 지연 감소 가능
* 추가 차량 운영비 발생 가능

세 가지 Rerouting 전략 중 가장 적극적인 대응 방법입니다.

---

# 23. Rerouting 대안 비교

각 Rerouting 전략은 다음과 같은 지표를 통해 비교할 수 있습니다.

```text
총 배송 지연시간
배송 지연 고객 수
총 이동시간
총 이동거리
차량 운영비용
사용 차량 수
방문 순서 변경 수
재할당 고객 수
신규 투입 차량 수
Feasibility
```

이를 통해 단순히 가장 빠른 경로를 선택하는 것이 아니라,

**배송 지연 감소 효과와 기존 운송계획 변경 비용 사이의 Trade-off**

를 의사결정자가 비교할 수 있도록 합니다.

---

# 24. Dynamic Fleet Control Tower

최적화 결과와 실시간 차량 운영상황을 운영자가 쉽게 확인할 수 있도록 웹 기반 **Dynamic Fleet Control Tower**를 구현했습니다.

웹 애플리케이션은 크게 다음 세 페이지로 구성됩니다.

```text
① 통합 관제 Dashboard
② Initial Route
③ Rerouting
```

---

# 25. 통합 관제 Dashboard

Dashboard에서는 전체 Fleet의 운영상태를 확인할 수 있습니다.

주요 KPI는 다음과 같습니다.

* 운행 중 차량 수
* 총 주문 건수
* 경로 위험 지수
* 총 운행거리
* 예상 운행시간
* Fleet 운영 효율성

지도에서는 다음 정보를 확인할 수 있습니다.

* Depot
* Customer
* 차량 위치
* 차량별 운행경로
* 사고 위치
* 위험 구간

---

# 26. 차량 상세정보

Dashboard에서 특정 차량을 선택하면 해당 차량의 상세정보를 확인할 수 있습니다.

예시 정보는 다음과 같습니다.

* 차량 ID
* 담당 운전자
* 현재 위치
* 현재 이동구간
* 차량 속도
* 적재량
* 적재율
* 다음 방문 고객
* 예상 도착시간
* 현재 예상 지연시간
* 담당 운송경로

---

# 27. 실시간 알림

Control Tower에서는 차량 운행과 관련된 주요 이벤트를 실시간 알림 형태로 제공합니다.

예시는 다음과 같습니다.

```text
교통사고 발생
도로 정체 발생
예상 배송 지연
경로 위험 증가
Rerouting 필요
신규 차량 배차 필요
```

돌발상황 발생 시 사고 유형과 예상 지연시간을 확인하고 Rerouting 화면에서 대응 대안을 비교할 수 있습니다.

---

# 28. Rerouting 화면

Rerouting 화면에서는 현재 발생한 돌발상황과 영향을 받는 차량을 확인할 수 있습니다.

운영자는 다음 세 가지 옵션 중 하나를 선택할 수 있습니다.

```text
경로 우회
방문 순서 변경
업무 승계 / 재배차
```

각 대안에 대해 다음 정보를 비교할 수 있습니다.

* 변경 전 예상 지연시간
* 변경 후 예상 지연시간
* 지연 감소량
* 총 이동거리
* 총 이동시간
* 추가 차량 필요 여부
* 추가 운영비
* 변경된 고객 방문 순서
* 기존 계획 대비 변경 수준

운영자가 대안을 선택하면 선택된 수정 계획을 새로운 차량 운송계획에 반영할 수 있습니다.

---

# 29. 실제 운영 시나리오

본 시스템의 실제 사용 시나리오는 다음과 같습니다.

### STEP 1. 운영조건 설정

운영자가 Initial Route 화면에서 다음 조건을 선택합니다.

```text
운영 목표
배차 트럭 수
출발 Depot
Time Window 중요도
적재용량
교통정보 반영 여부
```

### STEP 2. Initial Route 생성

ALNS를 실행하여 차량별 고객 할당 및 방문 순서를 결정합니다.

### STEP 3. 운행 시작

생성된 운송계획을 기반으로 차량이 배송을 시작합니다.

### STEP 4. 차량 모니터링

Control Tower에서 차량 위치와 배송 진행상황을 확인합니다.

### STEP 5. 돌발상황 발생

운행 중 교통사고 또는 정체가 발생합니다.

### STEP 6. 영향 분석

사고 도로를 기존 차량 경로와 비교하여 영향 차량과 예상 지연시간을 분석합니다.

### STEP 7. Rerouting

다음 세 가지 대응 대안을 생성합니다.

```text
경로 우회
방문 순서 변경
업무 승계 / 재배차
```

### STEP 8. 대안 비교

각 전략의 예상 지연시간, 이동거리, 운영비용 등을 비교합니다.

### STEP 9. 의사결정

운영자가 가장 적절한 Rerouting 대안을 선택합니다.

### STEP 10. 수정 경로 반영

선택된 새로운 운송계획을 해당 차량에 반영합니다.

---

# 30. Demo Instance

현재 Demo Instance는 55개의 Service Node를 기반으로 생성됩니다.

## Customer

Customer Demand는 재현 가능한 Synthetic Data로 생성됩니다.

기본 Demand 범위는 다음과 같습니다.

```text
4 ~ 20 ton
```

## Vehicle

기본 차량 용량은 다음과 같습니다.

```text
30 ton
```

Depot별 Demand를 고려하여 필요한 차량을 생성합니다.

## Time Window

고객 Time Window는 다음과 같은 업무시간 패턴을 사용합니다.

```text
08:00 - 12:00
09:00 - 15:00
10:00 - 17:00
13:00 - 18:00
08:00 - 16:00
```

---

# 31. MILP

ALNS 결과 검증 및 수리모형 구현을 위해 TD-MDVRPTW MILP도 함께 구현되어 있습니다.

주요 Decision Variable은 다음과 같습니다.

```text
x[v,i,j]
차량 v가 i → j를 이동하는지 여부

y[v,i]
고객 i가 차량 v에 할당되는지 여부

z[v]
차량 v를 사용하는지 여부

r[v,d]
차량 v의 종료 Depot이 d인지 여부

lambda[v,i,j,h]
차량 v가 시간대 h에 i → j를 출발하는지 여부

a[v,i]
차량 v의 노드 i 도착시간

b[v,i]
고객 i의 서비스 시작시간

theta[v,i]
노드 i 출발시간

T[i]
고객 i의 배송 지연시간
```

Full Instance는 변수와 제약식의 수가 매우 크기 때문에 MILP는 주로 소규모 Instance의 최적해 검증 용도로 사용할 수 있습니다.

---

# 32. 데이터 처리 Pipeline

```text
ITS NODELINKDATA

↓ src/network/build_backbone.py

data/backbone/
├─ backbone_nodes.csv
└─ backbone_edges.csv

↓ src/network/add_service_nodes.py

data/physical/
├─ physical_nodes.csv
└─ physical_edges.csv

↓ src/network/build_edge_time_profiles.py

data/physical/
└─ edge_time_profiles.csv

↓ src/network/build_tdvrp_graph.py

data/tdvrp/
├─ service_nodes.csv
├─ td_od_matrix.csv
└─ td_paths.csv

↓ src/model/build_demo_instance.py

data/instances/instance_01/
├─ customers.csv
├─ depots.csv
├─ vehicles.csv
└─ parameters.json

↓ ALNS

output/solutions/

↓ 실시간 교통 이벤트

src/rerouting/

↓ Rerouting

DETOUR / REROUTE / NEW_TRUCK
```

---

# 33. 프로젝트 디렉터리

```text
moveAI-VCM/
│
├─ application/
│   └─ 애플리케이션 관련 파일
│
├─ dynamic-fleet-control-tower/
│   ├─ src/
│   │   ├─ components/
│   │   ├─ data/
│   │   ├─ pages/
│   │   │   ├─ DashboardPage.tsx
│   │   │   ├─ InitialRoutePage.tsx
│   │   │   └─ ReroutePage.tsx
│   │   ├─ App.tsx
│   │   ├─ mockData.ts
│   │   └─ types.ts
│   └─ package.json
│
├─ config/
│   ├─ network.yaml
│   ├─ tdvrp.yaml
│   └─ alns.yaml
│
├─ data/
│   ├─ raw/
│   ├─ backbone/
│   ├─ physical/
│   ├─ tdvrp/
│   └─ instances/
│
├─ docs/
│
├─ output/
│   ├─ solutions/
│   ├─ milp/
│   └─ experiments/
│
├─ src/
│   ├─ network/
│   │   ├─ inspect_nodelink.py
│   │   ├─ build_backbone.py
│   │   ├─ validate_backbone.py
│   │   ├─ visualize_network.py
│   │   ├─ add_service_nodes.py
│   │   ├─ build_edge_time_profiles.py
│   │   └─ build_tdvrp_graph.py
│   │
│   ├─ model/
│   │   ├─ build_demo_instance.py
│   │   ├─ data_loader.py
│   │   ├─ formulation.py
│   │   ├─ milp_solver.py
│   │   ├─ objective.py
│   │   ├─ problem_data.py
│   │   └─ solution.py
│   │
│   ├─ alns/
│   │   ├─ alns.py
│   │   ├─ initial_solution.py
│   │   ├─ destroy_operators.py
│   │   ├─ repair_operators.py
│   │   ├─ local_search.py
│   │   ├─ evaluation.py
│   │   ├─ acceptance.py
│   │   └─ operator_weights.py
│   │
│   ├─ rerouting/
│   │   ├─ disruption.py
│   │   ├─ traffic_api.py
│   │   ├─ graph_update.py
│   │   ├─ physical_rerouting.py
│   │   ├─ reoptimization.py
│   │   ├─ solution_io.py
│   │   └─ pipeline.py
│   │
│   └─ utils/
│
├─ main.py
├─ requirements.txt
└─ README.md
```

---

# 34. Python 환경 실행

필요한 Python 패키지를 설치합니다.

```bash
pip install -r requirements.txt
```

이미 생성된 Backbone을 기준으로 전체 Pipeline을 실행하려면 다음 명령어를 사용합니다.

```bash
python main.py all
```

---

# 35. Network 단계별 실행

```bash
python -m src.network.inspect_nodelink
python -m src.network.build_backbone
python -m src.network.validate_backbone
python -m src.network.visualize_network
python -m src.network.add_service_nodes
python -m src.network.build_edge_time_profiles
python -m src.network.build_tdvrp_graph
python -m src.model.build_demo_instance
python -m src.model.data_loader
```

Backbone을 처음부터 다시 생성하려면 원본 ITS NODELINKDATA가 필요합니다.

---

# 36. ALNS 실행

배송 지연 최소화:

```bash
python main.py --objective TARDINESS
```

총 이동시간 최소화:

```bash
python main.py --objective TRAVEL_TIME
```

총 이동거리 최소화:

```bash
python main.py --objective DISTANCE
```

차량 운영비 최소화:

```bash
python main.py --objective VEHICLE_COST
```

모든 목적함수를 각각 실행하려면 다음과 같이 사용할 수 있습니다.

```bash
python main.py --objective ALL
```

Iteration 수도 별도로 지정할 수 있습니다.

```bash
python main.py --objective ALL --iterations 100
```

---

# 37. ALNS 결과

각 목적함수의 최적화 결과는 다음 디렉터리에 저장됩니다.

```text
output/solutions/TARDINESS/
├─ best_solution.csv
├─ best_schedule.csv
└─ alns_log.csv
```

동일한 구조로 다음 목적함수의 결과도 저장됩니다.

```text
TRAVEL_TIME
DISTANCE
VEHICLE_COST
```

목적함수별 결과 비교 파일은 다음과 같습니다.

```text
output/experiments/objective_comparison.csv
```

---

# 38. MILP 실행

소규모 Instance 검증은 다음과 같이 실행할 수 있습니다.

```bash
python -m src.model.validate_milp_small
```

Full Instance 실행 예시는 다음과 같습니다.

```bash
python main.py milp --objective TARDINESS --time-limit 60 --quiet
```

다른 목적함수도 동일한 방식으로 실행할 수 있습니다.

```bash
python main.py milp --objective TRAVEL_TIME --time-limit 60 --quiet

python main.py milp --objective DISTANCE --time-limit 60 --quiet

python main.py milp --objective VEHICLE_COST --time-limit 60 --quiet
```

MILP 결과는 다음 경로에 저장됩니다.

```text
output/milp/<OBJECTIVE>/
├─ best_solution.csv
├─ best_schedule.csv
└─ summary.json
```

---

# 39. 실시간 Rerouting 실행

UTIC 기반 교통 이벤트를 이용하는 경우 API Key를 환경변수로 설정합니다.

```bash
export UTIC_API_KEY="발급받은_API_KEY"
```

Rerouting Pipeline 실행 예시는 다음과 같습니다.

```bash
python -m src.rerouting.pipeline \
  --solution output/solutions/TARDINESS/best_solution.csv \
  --provider utic \
  --hours 9 10 \
  --max-new-trucks 3
```

API Key는 GitHub Repository에 직접 저장하지 않습니다.

---

# 40. 웹 애플리케이션 실행

Dynamic Fleet Control Tower 디렉터리로 이동합니다.

```bash
cd dynamic-fleet-control-tower
```

필요한 Dependency를 설치합니다.

```bash
npm install
```

개발 서버를 실행합니다.

```bash
npm run dev
```

이후 로컬 브라우저에서 Dynamic Fleet Control Tower를 확인할 수 있습니다.

---

# 41. 주요 설정 파일

## Network 설정

```text
config/network.yaml
```

다음 정보를 관리합니다.

* 도로 네트워크 설정
* 운영 시간대
* Free-flow Speed
* 시간대별 Congestion Factor

## TDVRP 설정

```text
config/tdvrp.yaml
```

TDVRP 문제와 관련된 주요 파라미터를 관리합니다.

## ALNS 설정

```text
config/alns.yaml
```

다음과 같은 ALNS 관련 파라미터를 관리합니다.

* Iteration
* Destroy Operator
* Repair Operator
* Acceptance
* Operator Weight
* Search 관련 Parameter

---

# 42. 현재 구현 범위

## 네트워크

* ITS NODELINKDATA 기반 Backbone 생성
* 고속도로 및 주요 간선도로 추출
* Depot 및 Customer 연결
* Physical Network 생성
* 시간대별 Edge 이동시간 생성
* TDVRP Virtual Network 생성
* Physical Path 저장
* Virtual Arc와 Physical Road Path 연결

## 최적화

* Time-Dependent VRP
* Multi-Depot
* Time Window
* Flexible End Depot
* 차량 용량 제약
* 차량 할당
* 고객 방문 순서 최적화
* ALNS
* MILP
* 복수 목적함수 독립 실행

## 실시간 대응

* 교통 이벤트 입력
* ITS Link와 Physical Edge 연결
* 사고 Edge 이동시간 업데이트
* TD OD Matrix 재계산
* Physical Path 재계산
* 영향 차량 탐지
* 예상 지연시간 분석
* 경로 우회
* 방문 순서 변경
* 신규 차량 투입
* 고객 재배차
* Rerouting 대안 비교

## 웹 애플리케이션

* 통합 관제 Dashboard
* 차량 위치 시각화
* 차량별 경로 시각화
* Depot 및 Customer 표시
* Fleet 운영 KPI
* 차량 상세정보
* 실시간 돌발상황 Alert
* Initial Route 조건 설정
* ALNS 기반 Initial Route 생성
* 차량별 최적 경로 확인
* 운행 시뮬레이션
* Rerouting 대상 차량 확인
* 경로 우회 대안
* 방문 순서 변경 대안
* 업무 승계 및 재배차 대안
* Rerouting 대안별 성능 비교
* 선택된 대안의 운영계획 반영

---

# 43. 현재 데이터에 대한 참고사항

현재 기본 시간대별 교통 Profile은 도로 거리, 도로 등급, Free-flow Speed 및 시간대별 Congestion Factor를 이용하여 생성한 프로토타입 데이터를 사용합니다.

실시간 Rerouting 모듈은 외부 교통정보를 이용하여 해당 Edge의 이동시간을 업데이트할 수 있도록 별도로 설계되어 있습니다.

현재 Time-Dependent Shortest Path는 **1시간 단위 Static Snapshot 방식**을 사용합니다.

예를 들어 차량이 09:32에 특정 구간을 출발한다면

```text
09:00 ~ 10:00
```

시간대의 도로 이동시간을 이용합니다.

즉, 하나의 이동구간을 운행하는 도중 다음 시간대로 넘어갔을 때 Edge Weight를 연속적으로 다시 변경하는 Continuous Time-Dependent 방식은 현재 사용하지 않습니다.

---

# 44. 프로젝트의 핵심 차별점

본 프로젝트의 목표는 단순히 가장 짧은 배송 경로를 찾는 것이 아닙니다.

기존 차량경로 최적화는 대부분 운행 전에 경로를 생성하는 **정적 계획 문제**에 초점을 둡니다.

하지만 실제 물류환경에서는 차량이 운행을 시작한 이후에도 교통사고와 도로 정체가 발생할 수 있습니다.

VCM은 이를 고려하여

**초기 운송계획 생성 → 실제 차량 운행 → 돌발상황 감지 → 영향 분석 → Rerouting → 운영자 의사결정**

까지 연결합니다.

특히 돌발상황 발생 시 하나의 최적해만 강제로 적용하는 것이 아니라,

```text
경로만 변경
방문 순서 변경
차량 및 업무 재배치
```

와 같이 운영 변경 수준이 다른 여러 대안을 제공한다는 점이 특징입니다.

이를 통해 알고리즘이 직접 모든 결정을 수행하는 것이 아니라 **의사결정자가 상황에 맞는 대응방안을 선택할 수 있는 Decision Support System**을 지향합니다.

---

# 45. 기대 효과

본 시스템을 실제 물류 차량 운영에 적용하면 다음과 같은 효과를 기대할 수 있습니다.

* 돌발상황 대응시간 단축
* 배송 지연 감소
* 불필요한 운행거리 감소
* 차량 운영비 절감
* 차량 가용성 향상
* 실시간 차량 운영 가시성 확보
* 사고 영향 차량의 빠른 식별
* 다양한 Rerouting 대안 비교
* 운영자의 데이터 기반 의사결정 지원

---

# 46. Team

**VCM**

현대글로비스 **MOVE AI Challenge 2026**

## 프로젝트 주제

**실시간 교통 정보를 반영한 차량 경로 재최적화 시스템**

## 핵심 기술

`TDVRP` · `ALNS` · `MILP` · `Rerouting` · `Real-time Traffic` · `Road Network` · `Fleet Optimization` · `Decision Support`
