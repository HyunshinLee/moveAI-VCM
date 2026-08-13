# moveAI-VCM 실시간 Re-scheduling 엔진

다른 팀원이 산출한 **트럭별 TDVRP 최종 방문 순서**와 도로 backbone graph를 입력받아, 실시간 교통으로 그래프를 갱신하고 다음 대안을 비교합니다.

1. `no_action`: 갱신 전 상세 경로를 유지(폐쇄 구간은 복구 대기)
2. `detour`: 고객 순서는 유지하고 중간 도로 경로만 재탐색
3. `reroute`: 기존 차량들의 고객 순서를 swap/relocate/reinsert
4. `new_truck`: 지연 위험 업무를 최대 N대의 신규 트럭에 이관

초기 TDVRP를 다시 풀지 않습니다. 입력·출력 계약과 전체 알고리즘은 [docs/algorithm_flow.md](docs/algorithm_flow.md)에 정리했습니다.

## 빠른 실행

Python 3.11 이상에서 외부 패키지 없이 실행됩니다.

```bash
python -m moveai_vcm.cli \
  --graph examples/backbone_graph.json \
  --solution examples/tdvrp_solution.json \
  --extras examples/extra_trucks.json \
  --provider mock \
  --traffic-snapshot examples/traffic_snapshot.json \
  --updated-graph updated_graph.json \
  --output rescheduling_results.json
```

### UTIC 실시간 돌발정보

팀 backbone의 `original_link_ids`가 국토교통부 표준링크 ID이므로 UTIC의
`linkId`/`lineLinkId`와 직접 결합할 수 있습니다. 키는 저장소에 넣지 않습니다.

```bash
export UTIC_API_KEY="발급받은 키"
python -m moveai_vcm.cli \
  --graph graph \
  --solution tdvrp_solution.json \
  --extras extra_trucks.json \
  --provider utic
```

UTIC 돌발 API는 사고·공사·통제의 실제 발생 여부를 제공하지만 실측 속도는 제공하지
않습니다. 전면통제는 `closed=true`, 부분 장애는 기본속도의 55%라는 정책 추정값으로
처리하고 결과 metadata에 `speed_value_type=policy_estimate`를 남깁니다. 실측 소통속도는
UTIC 발급 시 안내된 지도 URL과 등록 IP가 추가로 필요합니다.

## 테스트

```bash
python -m unittest discover -s tests -v
```

## MVP 범위

- 한 번의 API snapshot에서 폐쇄·속도 저하 등 여러 disruption을 동시에 반영
- directed graph와 서로 다른 출발/종료 depot 지원
- 배송 수량, 차량 잔여 적재량, 최대 운행시간 검사
- updated graph 위에서 상세 waypoint 경로 산출
- 시간·거리·지연·정시율·운영비·변경량·재배정 수·신규 트럭 수 비교
- Pareto dominance와 지연 1시간 절감 비용(ICER/WTP)으로 추천안 제시

API 실패 arc는 직전 속도를 보존하고 오류를 metadata에 남깁니다. 해커톤 데모와 테스트는 재현 가능한 mock snapshot을 사용합니다.
