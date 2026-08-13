# Re-scheduling 알고리즘 및 연동 계약

## 1. 전체 파이프라인

```mermaid
flowchart LR
  A["Backbone graph\nnode·arc·기준속도"] --> C["초기 상세 path 확장"]
  B["TDVRP 결과\n차량별 최종 customer sequence"] --> C
  C --> D["실시간 교통 API 수집"]
  D --> E["복수 disruption 일괄 반영\nclosure·speed·timestamp"]
  E --> F1["No-action"]
  E --> F2["Detour"]
  E --> F3["Re-route"]
  E --> F4["New trucks 1..N"]
  F1 --> G["제약 검증 및 KPI 계산"]
  F2 --> G
  F3 --> G
  F4 --> G
  G --> H["Pareto frontier + ICER/WTP"]
  H --> I["추천안·상세 경로·비교지표 JSON"]
```

TDVRP 최적화 자체는 이 저장소의 범위가 아닙니다. `routes[].stops`의 순서를 그대로 초기해로 받아, 교통 갱신 이전 backbone에서 각 service leg의 상세 path를 한 번 저장합니다.

## 2. 실시간 그래프 갱신

```mermaid
flowchart TD
  A["모든 backbone arc"] --> B["arc 중점 또는 provider segment ID"]
  B --> C["Traffic API 병렬 호출"]
  C --> D{"호출 성공?"}
  D -- Yes --> E["current speed·closure·confidence 추출"]
  D -- No --> F["직전 속도 유지 + error metadata"]
  E --> G["(source,target) arc 갱신"]
  F --> G
  G --> H["모든 observation을 동일 snapshot으로 반영"]
  H --> I["updated directed graph"]
```

`traffic_snapshot.json`의 observation 여러 행은 동시에 발생한 장애를 뜻합니다. 존재하지 않는 arc observation은 무시합니다.

## 3. 방안별 알고리즘

### Detour — 고객 순서 고정, 도로 경로 우회

```mermaid
flowchart TD
  A["차량별 current node → customer들 → end depot"] --> B["각 leg의 출발시각 계산"]
  B --> C["폐쇄 arc 제외·live speed 가중치 적용"]
  C --> D["FIFO time-dependent Dijkstra"]
  D --> E{"모든 leg 연결 가능?"}
  E -- Yes --> F["waypoint 포함 상세 path 결합"]
  E -- No --> G["infeasible 표시"]
  F --> H["초기 경로 대비 KPI 계산"]
```

### Re-route — 고객 방문 순서/차량 배정 수정

```mermaid
flowchart TD
  A["Detour 해를 시작해로 사용"] --> B["이웃해 생성"]
  B --> B1["동일 차량 swap"]
  B --> B2["동일 차량 relocate"]
  B --> B3["차량 간 feasible reinsert"]
  B1 --> C["updated graph에서 상세 path 재계산"]
  B2 --> C
  B3 --> C
  C --> D["capacity·route time·end depot 검증"]
  D --> E["weighted delay + 변경/재배정 penalty"]
  E --> F{"개선?"}
  F -- Yes --> B
  F -- No --> G["best local solution 반환"]
```

### New trucks — 복수 신규 차량 투입

```mermaid
flowchart TD
  A["기존 해의 job별 weighted delay 계산"] --> B["지연 위험 내림차순 정렬"]
  B --> C["투입 대수 k = 1..min(N, 가용차량)"]
  C --> D["각 job을 각 신규차량·모든 위치에 삽입 시험"]
  D --> E["원 차량에서 제거 후 전체 제약 검증"]
  E --> F["가장 좋은 feasible insertion 채택"]
  F --> G{"다음 job?"}
  G -- Yes --> D
  G -- No --> H["k별 완성 해 비교"]
  H --> I["최적 투입 대수와 배차 반환"]
```

## 4. 입력 계약

### Backbone graph

- `nodes`: `id`, `lat`, `lon`, `kind(depot|customer|waypoint)`
- `edges`: `source`, `target`, `distance_m`, `base_speed_kph`
- 선택: `bidirectional`, `current_speed_kph`, `closed`, `metadata`

### TDVRP solution

- `vehicle`: `vehicle_id`, `current_node`, `end_depot`, `capacity`, `current_load`
- 선택 비용/시간: `available_at_s`, `max_route_time_s`, `fixed_dispatch_cost`, `cost_per_km`, `cost_per_hour`
- `stops`: 순서가 확정된 업무 목록
- stop의 `load_delta`: pickup은 양수, delivery는 음수
- stop의 `planned_arrival_s`는 초기해 대비 지연 계산 기준

## 5. 비교 지표와 추천

각 대안에 총 운행시간, 거리, 우선순위 가중 지연, 최대 지연, 지각 stop 수, 정시율, 운영비, 순서 변경 수, 재배정 job 수, 신규 트럭 수를 계산합니다. 지연·비용·거리·변경량에서 다른 해에 지배되는 대안을 제거하고, Pareto frontier에서 지연 1시간 절감 증분비용(ICER)이 사용자 WTP 이하인 대안을 추천합니다.

이 구조는 Karam & Reinau(2022)의 disruption 대응 프레임—accepting/no-action, detouring, rerouting, extra tractor—을 last-mile/customer-sequence 문맥에 맞게 확장한 것입니다.
