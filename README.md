# moveAI-VCM

Move AI VCM team TD-MDCVRPTW road-network and solver pipeline.

## TDVRPTW-Rerouting Road Network Pipeline

이 프로젝트는 국토교통부 ITS 국가표준 NODELINKDATA를 기반으로 대한민국 전국
road backbone, depot/customer physical layer, hourly time-dependent OD matrix를
생성한다. 최종적으로 MILP와 ALNS는 255-node physical graph를 직접 탐색하지 않고,
사전 계산된 55-node TDVRP virtual arc network를 lookup한다.

## Pipeline

```text
ITS NODELINKDATA
-> src/network/build_backbone.py
-> data/backbone/backbone_nodes.csv / backbone_edges.csv
-> src/network/add_service_nodes.py
-> data/physical/physical_nodes.csv / physical_edges.csv
-> src/network/build_edge_time_profiles.py
-> data/physical/edge_time_profiles.csv
-> src/network/build_tdvrp_graph.py
-> data/tdvrp/service_nodes.csv / td_od_matrix.csv / td_paths.csv
-> src/model/build_demo_instance.py
-> data/instances/instance_01/customers.csv / depots.csv / vehicles.csv / parameters.json
-> src/alns/alns.py
-> output/solutions/<OBJECTIVE>/best_solution.csv / best_schedule.csv / alns_log.csv
-> disruption
-> physical rerouting
-> TDVRP reoptimization
```

## Current Milestone

현재 완료된 network:

- Physical nodes: 255 = `ROAD 200 + DEPOT 5 + CUSTOMER 50`
- Physical directed edges: 1,528
- Service nodes: 55 = `DEPOT 5 + CUSTOMER 50`
- Hourly snapshots: 17 hours, `06:00-22:00`
- OD-hour entries: 50,490 = `55 x 54 x 17`
- Unreachable OD-hour pairs: 0

중요한 산출물:

```bash
data/physical/edge_time_profiles.csv
data/tdvrp/td_od_matrix.csv
data/tdvrp/td_paths.csv
```

## Run

Backbone부터 다시 만들려면 원본 ITS shapefile이 필요하며 시간이 걸린다.
현재는 이미 만들어진 backbone을 기준으로 Backbone 이후 pipeline을 실행할 수 있다.

```bash
python main.py all
```

단계별 실행:

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
python -m src.model.validate_milp_small
python main.py milp --objective DISTANCE --time-limit 30 --quiet
python main.py --objective TARDINESS
python main.py --objective ALL
```

## Data Layout

```text
data/
  raw/
    nodelink/
    traffic/
  backbone/
    backbone_nodes.csv
    backbone_edges.csv
    backbone_nodes.geojson
    backbone_edges.geojson
  physical/
    physical_nodes.csv
    physical_edges.csv
    edge_time_profiles.csv
  tdvrp/
    service_nodes.csv
    td_od_matrix.csv
    td_paths.csv
  instances/
    instance_01/
      customers.csv
      depots.csv
      vehicles.csv
      parameters.json
```

The original heavy NODELINKDATA files are left in `[2026-08-12]NODELINKDATA/`.
Set `NODELINKDATA_DIR=/path/to/NODELINKDATA` to override this location.

## Network Meaning

`physical_nodes.csv` contains:

- `ROAD`: 200 backbone road nodes
- `DEPOT`: 5 Hyundai Glovis industrial-material depot nodes
- `CUSTOMER`: 50 synthetic nationwide customer nodes

`physical_edges.csv` contains:

- `ROAD`: directed road backbone arcs
- `CONNECTOR`: bidirectional access arcs from depot/customer nodes to nearby backbone nodes

`backbone_edges.csv` preserves `original_link_ids` and `original_node_path` so the simplified
edge can be traced back to the original ITS network.

## Time-Dependent Travel Time

The project uses hourly static snapshots, not continuous time-dependent shortest path.

If a vehicle departs during hour `h`, every physical edge on that shortest path uses
that same hour's edge travel time. For example:

```text
tau_ij^9 = shortest-path travel time from i to j using the 09:00-10:00 snapshot
```

If travel crosses 10:00, the edge weights are not changed mid-path.

`edge_time_profiles.csv` schema:

```text
edge_id,hour,travel_time_min,speed_kph,data_source
```

Current profiles are prototype values derived from distance, road class, free-flow speed,
and hourly congestion factors in `config/network.yaml`. The interface is replaceable through
`get_edge_travel_time(edge_id, hour)`.

## 55-Node TDVRP Graph

The 55-node TDVRP graph is a virtual complete directed service-node graph.
An arc such as:

```text
C001 -> C007
```

is not a physical road edge. It is a compressed shortest path over the 255-node physical graph,
for example:

```text
C001 -> R017 -> R042 -> R061 -> C007
```

`td_od_matrix.csv` stores the travel-time lookup used by MILP/ALNS:

```text
from_node,to_node,hour,travel_time_min,distance_km
```

`td_paths.csv` stores the underlying physical path for rerouting/disruption analysis:

```text
from_node,to_node,hour,travel_time_min,distance_km,path_nodes,path_edges
```

MILP/ALNS should load `td_od_matrix.csv` into a lookup such as:

```python
travel_time[i][j][h]
```

If a vehicle leaves `C03` at `09:32`, use `h = 9` and lookup
`travel_time["C03"]["C17"][9]`.

## Demo Instance

`src/model/build_demo_instance.py` creates a deterministic demo TD-MDVRPTW instance from
the 55 service nodes:

- Customers are assigned to the nearest depot by 08:00 TD OD travel time.
- Customer demand `Q` is synthetic but deterministic, between 4 and 20 tons.
- Customer time windows use five business-hour patterns: `08:00-12:00`, `09:00-15:00`,
  `10:00-17:00`, `13:00-18:00`, and `08:00-16:00`.
- Customer service time is demand-based.
- Depot vehicles use 30-ton capacity. Fleet size is
  `max(min_depot_fleet, ceil(assigned_demand * 1.25 / 30))`.

The loadable model inputs are:

```text
data/tdvrp/service_nodes.csv
data/tdvrp/td_od_matrix.csv
data/tdvrp/td_paths.csv
data/instances/instance_01/vehicles.csv
data/instances/instance_01/parameters.json
```

## ALNS Objective Selection

The ALNS solver uses a decision-maker-selected single objective. It does not use weighted
multi-objective optimization by default.

Allowed objective modes:

```text
TARDINESS
TRAVEL_TIME
DISTANCE
VEHICLE_COST
```

For example, `ACTIVE_OBJECTIVE = DISTANCE` means:

```text
tardiness weight = 0
travel_time weight = 0
distance weight = 1
vehicle_cost weight = 0
```

All performance metrics are still calculated for every solution:

```text
total_tardiness
total_travel_time
total_distance
vehicle_cost
used_vehicle_count
```

Only the selected objective is used for ALNS comparison, simulated annealing acceptance,
operator rewards, insertion deltas, local-search improvements, and flexible end depot choice.

Run one objective:

```bash
python main.py --objective TARDINESS
python main.py --objective TRAVEL_TIME
python main.py --objective DISTANCE
python main.py --objective VEHICLE_COST
```

Run all four objectives independently:

```bash
python main.py --objective ALL
```

Override iterations or time-window mode:

```bash
python main.py --objective ALL --iterations 100
python main.py --objective DISTANCE --time-window-mode HARD
```

The default `time_window_mode` is `SOFT`. Customer service start after `tw_end` is allowed and
recorded as `tardiness`; it is not treated as route infeasibility. Hard feasibility still includes
customer exactly once, no duplicate customer, vehicle capacity, valid vehicle/start depot/end
depot, route connectivity through the TD OD lookup, vehicle operating horizon, and route duration.

Objective selection changes only the value minimized by ALNS; it does not relax those hard
feasibility constraints. Use `--time-window-mode HARD` only for experiments where lateness itself
should make a route infeasible.

ALNS outputs:

```text
output/solutions/TARDINESS/best_solution.csv
output/solutions/TARDINESS/best_schedule.csv
output/solutions/TARDINESS/alns_log.csv
output/solutions/TRAVEL_TIME/...
output/solutions/DISTANCE/...
output/solutions/VEHICLE_COST/...
output/experiments/objective_comparison.csv
```

## MILP Formulation

`src/model/milp_solver.py` implements the flexible-end-depot TD-MDCVRPTW MILP from
`TDVRP_Flexible_End_Depot_Final_Formulation.docx`.

Core decision variables:

```text
x[v,i,j]        vehicle v directly traverses arc i -> j
y[v,i]          customer i is assigned to vehicle v
z[v]            vehicle v is used
r[v,d]          vehicle v ends at depot d
lambda[v,i,j,h] vehicle v departs i -> j during hour h
a[v,i]          arrival time
b[v,i]          customer service start time
theta[v,i]      departure time
T[i]            customer tardiness
```

The route structure is:

```text
fixed start depot d_v -> customer sequence -> flexible end depot d
```

The full 5-depot/50-customer MILP is intentionally large. The implementation is therefore
validated on a small 2-depot/4-customer graph:

```bash
python -m src.model.validate_milp_small
```

Run the full-instance MILP when needed:

```bash
python main.py milp --objective TARDINESS --time-limit 60 --quiet
python main.py milp --objective TRAVEL_TIME --time-limit 60 --quiet
python main.py milp --objective DISTANCE --time-limit 60 --quiet
python main.py milp --objective VEHICLE_COST --time-limit 60 --quiet
```

MILP outputs are written to:

```text
output/milp/<OBJECTIVE>/best_solution.csv
output/milp/<OBJECTIVE>/best_schedule.csv
output/milp/<OBJECTIVE>/summary.json
```

## Code Layout

```text
src/
  network/
    inspect_nodelink.py
    build_backbone.py
    validate_backbone.py
    add_service_nodes.py
    build_edge_time_profiles.py
    build_tdvrp_graph.py
    visualize_network.py
  model/
    build_demo_instance.py
    data_loader.py
    formulation.py
    milp_solver.py
    objective.py
    problem_data.py
    validate_milp_small.py
    solution.py
  alns/
    alns.py
    initial_solution.py
    destroy_operators.py
    repair_operators.py
    local_search.py
    evaluation.py
    acceptance.py
    operator_weights.py
  rerouting/
    disruption.py
    physical_rerouting.py
    reoptimization.py
  utils/
    config.py
    io.py
    time_utils.py
```

## Config

Main network settings are in:

```bash
config/network.yaml
config/tdvrp.yaml
config/alns.yaml
```

`START_HOUR`, `END_HOUR`, congestion factors, and prototype free-flow speeds can be changed
without editing the TDVRP graph builder.
