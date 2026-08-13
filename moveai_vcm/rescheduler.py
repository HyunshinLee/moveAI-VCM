from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from itertools import combinations
from math import inf

from .models import Graph, RouteMetrics, RoutePlan, Stop, StrategyResult, VehicleState
from .routing import PathResult, expand_service_sequence, shortest_path


@dataclass(slots=True)
class ReschedulingConfig:
    delay_buffer_s: float = 15 * 60
    max_local_search_iterations: int = 80
    max_extra_trucks: int = 3
    willingness_to_pay_per_delay_hour: float = 100_000.0
    closed_arc_wait_s: float = 2 * 3600
    change_position_penalty: float = 90.0
    reassignment_penalty: float = 300.0


@dataclass(slots=True)
class Simulation:
    metrics: RouteMetrics
    paths: dict[str, list[list[str]]]
    arrivals: dict[str, float]


class Rescheduler:
    def __init__(
        self,
        graph: Graph,
        config: ReschedulingConfig | None = None,
        *,
        initial_paths: dict[str, list[list[str]]] | None = None,
    ):
        self.graph = graph
        self.config = config or ReschedulingConfig()
        self.initial_paths = initial_paths or {}

    def _simulate(
        self,
        plans: list[RoutePlan],
        initial: list[RoutePlan],
        *,
        fixed_paths: dict[str, list[list[str]]] | None = None,
    ) -> Simulation:
        total_time = total_distance = total_delay = max_delay = cost = 0.0
        late = changed = reassigned = 0
        paths: dict[str, list[list[str]]] = {}
        arrivals: dict[str, float] = {}
        original_owner = {
            (stop.job_id or stop.node_id): plan.vehicle.vehicle_id
            for plan in initial for stop in plan.stops
        }
        original_position = {
            (stop.job_id or stop.node_id): idx
            for plan in initial for idx, stop in enumerate(plan.stops)
        }
        all_stops = sum(len(p.stops) for p in plans)
        infeasible = None
        for plan in plans:
            vehicle = plan.vehicle
            clock = vehicle.available_at_s
            route_start = clock
            load = vehicle.current_load
            current = vehicle.current_node
            vehicle_distance = 0.0
            vehicle_paths: list[list[str]] = []
            legs = (fixed_paths or {}).get(vehicle.vehicle_id, [])
            for idx, stop in enumerate(plan.stops):
                path = self._fixed_path(legs[idx], clock) if idx < len(legs) else shortest_path(self.graph, current, stop.node_id, clock, use_live=True)
                if path is None:
                    infeasible = f"{vehicle.vehicle_id}: no path {current}->{stop.node_id}"
                    break
                clock += path.travel_time_s
                vehicle_distance += path.distance_m
                vehicle_paths.append(path.nodes)
                arrivals[stop.job_id or stop.node_id] = clock
                baseline = stop.planned_arrival_s if stop.planned_arrival_s is not None else clock
                delay = max(0.0, clock - baseline)
                total_delay += stop.priority * delay
                max_delay = max(max_delay, delay)
                if stop.due_time_s is not None and clock > stop.due_time_s:
                    late += 1
                load += stop.load_delta
                if load < -1e-9 or load > vehicle.capacity + 1e-9:
                    infeasible = f"{vehicle.vehicle_id}: capacity violation at {stop.node_id} ({load:.2f})"
                    break
                key = stop.job_id or stop.node_id
                if original_owner.get(key) != vehicle.vehicle_id:
                    reassigned += 1
                if original_position.get(key) != idx:
                    changed += 1
                clock += stop.service_time_s
                current = stop.node_id
            if infeasible:
                break
            final_idx = len(plan.stops)
            final_path = self._fixed_path(legs[final_idx], clock) if final_idx < len(legs) else shortest_path(self.graph, current, vehicle.end_depot, clock, use_live=True)
            if final_path is None:
                infeasible = f"{vehicle.vehicle_id}: no path to end depot {vehicle.end_depot}"
                break
            clock += final_path.travel_time_s
            vehicle_distance += final_path.distance_m
            vehicle_paths.append(final_path.nodes)
            duration = clock - route_start
            if duration > vehicle.max_route_time_s:
                infeasible = f"{vehicle.vehicle_id}: max route time exceeded"
                break
            total_time += duration
            total_distance += vehicle_distance
            cost += (
                vehicle.fixed_dispatch_cost
                + vehicle.cost_per_hour * duration / 3600
                + vehicle.cost_per_km * vehicle_distance / 1000
            )
            paths[vehicle.vehicle_id] = vehicle_paths
        metrics = RouteMetrics(
            total_travel_time_s=total_time, total_distance_m=total_distance,
            total_delay_s=total_delay, max_delay_s=max_delay, late_stops=late,
            on_time_rate=(all_stops - late) / all_stops if all_stops else 1.0,
            operating_cost=cost, changed_stop_positions=changed,
            reassigned_jobs=reassigned,
            extra_trucks=sum(p.vehicle.is_extra for p in plans),
            infeasible_reason=infeasible,
        )
        return Simulation(metrics, paths, arrivals)

    def _fixed_path(self, nodes: list[str], departure_s: float) -> PathResult | None:
        del departure_s
        elapsed = distance = 0.0
        for source, target in zip(nodes, nodes[1:]):
            edge = self.graph.edges.get((source, target))
            if edge is None:
                return None
            if edge.closed:
                # No action waits until the assumed disruption clears, then traverses
                # the original arc. This is the paper's accepting strategy baseline.
                elapsed += self.config.closed_arc_wait_s
                elapsed += edge.distance_m / max(edge.base_speed_kph, 0.1) * 3.6
            else:
                elapsed += edge.travel_time_s(use_live=True)
            distance += edge.distance_m
        return PathResult(nodes, distance, elapsed)

    def no_action(self, plans: list[RoutePlan]) -> StrategyResult:
        # With only a service sequence supplied by TDVRP, fixed road paths are not
        # available. No-action therefore means sequence unchanged on the updated graph.
        sim = self._simulate(deepcopy(plans), plans, fixed_paths=self.initial_paths)
        return StrategyResult("no_action", deepcopy(plans), sim.paths, sim.metrics)

    def detour(self, plans: list[RoutePlan]) -> StrategyResult:
        # Same customer sequence; detailed road paths are recomputed after all live
        # closures/congestion observations have updated the graph.
        candidate = deepcopy(plans)
        sim = self._simulate(candidate, plans)
        return StrategyResult(
            "detour", candidate, sim.paths, sim.metrics,
            ["고객 배정·방문순서는 유지하고 상세 도로 경로만 재계산"],
        )

    def _objective(self, sim: Simulation) -> float:
        if sim.metrics.infeasible_reason:
            return inf
        return (
            sim.metrics.total_delay_s
            + self.config.change_position_penalty * sim.metrics.changed_stop_positions
            + self.config.reassignment_penalty * sim.metrics.reassigned_jobs
        )

    def reroute(self, plans: list[RoutePlan]) -> StrategyResult:
        best = deepcopy(plans)
        best_sim = self._simulate(best, plans)
        for _ in range(self.config.max_local_search_iterations):
            improved = False
            candidates: list[list[RoutePlan]] = []
            # Within-route swap and relocate: customer visit order adjustment.
            for p_idx, plan in enumerate(best):
                n = len(plan.stops)
                for i, j in combinations(range(n), 2):
                    swapped = deepcopy(best)
                    swapped[p_idx].stops[i], swapped[p_idx].stops[j] = swapped[p_idx].stops[j], swapped[p_idx].stops[i]
                    candidates.append(swapped)
                for i in range(n):
                    for j in range(n):
                        if i == j:
                            continue
                        moved = deepcopy(best)
                        stop = moved[p_idx].stops.pop(i)
                        moved[p_idx].stops.insert(j, stop)
                        candidates.append(moved)
            # Cross-route relocate allows an unaffected existing truck to take a job.
            for source_idx, source in enumerate(best):
                for stop_idx in range(len(source.stops)):
                    for target_idx in range(len(best)):
                        if source_idx == target_idx:
                            continue
                        for position in range(len(best[target_idx].stops) + 1):
                            moved = deepcopy(best)
                            stop = moved[source_idx].stops.pop(stop_idx)
                            moved[target_idx].stops.insert(position, stop)
                            candidates.append(moved)
            for candidate in candidates:
                sim = self._simulate(candidate, plans)
                if self._objective(sim) + 1e-6 < self._objective(best_sim):
                    best, best_sim, improved = candidate, sim, True
            if not improved:
                break
        return StrategyResult(
            "reroute", best, best_sim.paths, best_sim.metrics,
            ["swap·relocate·차량 간 재삽입 local search", "용량·근무시간·종료 depot 제약 검사"],
        )

    def new_trucks(self, plans: list[RoutePlan], extras: list[VehicleState]) -> StrategyResult:
        baseline_sim = self._simulate(plans, plans)
        # Rank jobs by current weighted delay; larger-risk jobs are transferred first.
        scored: list[tuple[float, int, Stop]] = []
        for p_idx, plan in enumerate(plans):
            for stop in plan.stops:
                key = stop.job_id or stop.node_id
                arrival = baseline_sim.arrivals.get(key, stop.planned_arrival_s or 0)
                planned = stop.planned_arrival_s or arrival
                scored.append((stop.priority * max(0, arrival - planned), p_idx, stop))
        scored.sort(key=lambda item: item[0], reverse=True)

        best, best_sim = deepcopy(plans), baseline_sim
        max_count = min(self.config.max_extra_trucks, len(extras))
        for count in range(1, max_count + 1):
            candidate = deepcopy(plans)
            extra_plans = [RoutePlan(vehicle=deepcopy(v), stops=[]) for v in extras[:count]]
            # Greedy feasible assignment. Try high-delay jobs in every extra truck and
            # insertion position; keep the assignment with the best complete objective.
            for _, source_idx, original_stop in scored:
                key = original_stop.job_id or original_stop.node_id
                current_source = next((p for p in candidate if any((s.job_id or s.node_id) == key for s in p.stops)), None)
                if current_source is None:
                    continue
                trial_best = None
                trial_best_sim = None
                for e_idx, extra_plan in enumerate(extra_plans):
                    for pos in range(len(extra_plan.stops) + 1):
                        trial_base = deepcopy(candidate)
                        trial_extras = deepcopy(extra_plans)
                        source_pos = next(i for i, p in enumerate(trial_base) if any((s.job_id or s.node_id) == key for s in p.stops))
                        moved_stop = next(s for s in trial_base[source_pos].stops if (s.job_id or s.node_id) == key)
                        trial_base[source_pos].stops.remove(moved_stop)
                        trial_extras[e_idx].stops.insert(pos, moved_stop)
                        sim = self._simulate(trial_base + trial_extras, plans)
                        if trial_best_sim is None or self._objective(sim) < self._objective(trial_best_sim):
                            trial_best = (trial_base, trial_extras)
                            trial_best_sim = sim
                if trial_best and trial_best_sim and self._objective(trial_best_sim) < self._objective(self._simulate(candidate + extra_plans, plans)):
                    candidate, extra_plans = trial_best
            sim = self._simulate(candidate + extra_plans, plans)
            if self._objective(sim) < self._objective(best_sim):
                best, best_sim = candidate + extra_plans, sim
        return StrategyResult(
            "new_truck", best, best_sim.paths, best_sim.metrics,
            [f"가용 신규 트럭 최대 {max_count}대 동시 검토", "지연 위험순 업무 이관 후 feasible insertion"],
        )

    @staticmethod
    def _dominates(a: StrategyResult, b: StrategyResult) -> bool:
        ma, mb = a.metrics, b.metrics
        av = (ma.total_delay_s, ma.operating_cost, ma.total_distance_m, ma.changed_stop_positions + ma.reassigned_jobs)
        bv = (mb.total_delay_s, mb.operating_cost, mb.total_distance_m, mb.changed_stop_positions + mb.reassigned_jobs)
        return all(x <= y for x, y in zip(av, bv)) and any(x < y for x, y in zip(av, bv))

    def rank(self, results: list[StrategyResult]) -> list[StrategyResult]:
        feasible = [r for r in results if r.feasible]
        frontier = [r for r in feasible if not any(self._dominates(other, r) for other in feasible if other is not r)]
        frontier.sort(key=lambda r: r.metrics.operating_cost)
        if not frontier:
            return results
        chosen = frontier[0]
        for cheaper, expensive in zip(frontier, frontier[1:]):
            saved_hours = (cheaper.metrics.total_delay_s - expensive.metrics.total_delay_s) / 3600
            if saved_hours <= 0:
                continue
            icer = (expensive.metrics.operating_cost - cheaper.metrics.operating_cost) / saved_hours
            expensive.icer_cost_per_delay_hour_saved = icer
            if icer <= self.config.willingness_to_pay_per_delay_hour:
                chosen = expensive
        ordered = [chosen] + [r for r in frontier if r is not chosen]
        ordered += [r for r in results if r not in ordered]
        chosen.explanation.insert(0, "Pareto frontier와 지연 1시간 절감 ICER/WTP 기준의 추천안")
        return ordered

    def solve(self, plans: list[RoutePlan], extras: list[VehicleState]) -> list[StrategyResult]:
        candidates = [self.no_action(plans), self.detour(plans), self.reroute(plans)]
        if extras:
            candidates.append(self.new_trucks(plans, extras))
        return self.rank(candidates)
