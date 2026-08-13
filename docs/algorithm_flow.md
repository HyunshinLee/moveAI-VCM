# Real-time re-scheduling algorithm flow

## Shared input contract

- Physical graph: `data/physical/physical_nodes.csv`, `physical_edges.csv`
- Hourly weights: `data/physical/edge_time_profiles.csv`
- Initial routes: ALNS/MILP `best_solution.csv`, converted to `src.model.solution.Solution`
- Fleet/capacity/time windows: `ProblemData.from_files()`
- Delivery only: each route starts with total assigned demand, and load decreases after delivery

## Graph update

```mermaid
flowchart LR
  A[UTIC events] --> B[Normalize standard link IDs]
  B --> C[Join physical_edges.original_link_ids]
  C --> D[Update affected edge-hour profiles]
  D --> E[build_td_matrices]
  E --> F[Updated TD OD matrix and detailed paths]
```

Several closures or congestion events may be applied in one snapshot. A closure uses a large
travel-time multiplier so the shortest-path routine selects a feasible alternative whenever one
exists. If the traffic-flow API later supplies measured speeds, the provider only needs to emit a
normalized `TrafficEvent.speed_factor`; the graph-update and optimization layers do not change.

## Strategy flows

```mermaid
flowchart TB
  S[Initial Solution plus updated ProblemData] --> D
  S --> R
  S --> N
  D[DETOUR: keep assignment and customer order] --> DP[Rebuild physical paths]
  R[REROUTE: team local search] --> RM[Swap and relocate customer sequence]
  RM --> RF[Capacity, time window, end-depot feasibility]
  N[NEW_TRUCK: find unused registered vehicles] --> NM[Move delay-reducing customers]
  NM --> NF[Allow up to N additional vehicles]
  DP --> C[Compare against initial solution]
  RF --> C
  NF --> C
```

Reported comparison fields are total tardiness, travel time, distance, vehicle cost, used vehicle
count, changed positions, reassigned customers, new trucks, feasibility, and time/distance/tardiness
deltas against the initial network. The recommendation uses a transparent lexicographic order:
feasibility, tardiness, vehicle cost, travel time, distance, and finally operational change count.
