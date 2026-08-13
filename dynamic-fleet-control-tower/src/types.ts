export type PageId = 'dashboard' | 'initial-route' | 'rerouting';

export type OptimizationObjective = 'balanced' | 'fast' | 'satisfaction' | 'cost';

export type DisruptionType = 'Accident' | 'Congestion' | 'Roadwork' | 'Weather' | 'Breakdown';

export type ScenarioOptionId = 'OPTION_A' | 'OPTION_B' | 'OPTION_C';

export interface RouteNode {
  id: string;
  name: string;
  lat: number;
  lng: number;
  type: 'depot' | 'pickup' | 'delivery' | 'both';
  demandKg?: number;
  timeWindow?: string;
  address?: string;
}

export interface RouteSegment {
  id: string;
  fromNodeId: string;
  toNodeId: string;
  distanceKm: number;
  travelTimeMin: number;
  riskScore: number; // 0.0 to 1.0
  status: 'clear' | 'warning' | 'critical' | 'blocked';
  incidentId?: string;
  coordinates: [number, number][]; // lat, lng points along the road
}

export interface FleetVehicle {
  id: string; // e.g. "T-02" or "TRK-T02"
  code: string; // "V-01", "V-03", "V-04"
  name: string;
  status: 'active' | 'risk' | 'warning' | 'idle';
  currentSegment: string; // "C03 ➔ C07"
  assignedRouteName: string; // "경로 A (북부)"
  routeColor: string; // hex or tailwind
  currentLat: number;
  currentLng: number;
  speedKmH: number;
  capacityKg: number;
  currentLoadKg: number;
  loadPercentage: number;
  delayMinutes: number;
  etaMinutes: number;
  driverName: string;
  notes?: string;
}

export interface IncidentAlert {
  id: string; // e.g., "INC-102" or "IC-102"
  type: DisruptionType;
  title: string;
  locationName: string; // "C03 ➔ C07" or "강남대로"
  riskScore: number; // 0.92
  severity: 'high' | 'medium' | 'low';
  affectedVehicleIds: string[]; // ["T-02", "T-05"]
  timestamp: string;
  description: string;
  resolved?: boolean;
  appliedScenario?: ScenarioOptionId;
}

export interface RerouteScenario {
  id: ScenarioOptionId;
  optionTitle: string; // "Option A"
  koreanName: string; // "경로 우회"
  subtitle: string; // "(경로 우회)"
  description: string;
  distanceKmChange: string; // "+8km"
  totalDistanceKm: number; // 134
  travelTimeMin: number; // 171
  delayReductionMin: number; // -21
  tardinessCount: number; // 0
  tardinessDescription?: string; // "1 명 지연"
  addedCostUsd: number; // 12.00
  isRecommended?: boolean;
}

export interface PlannedTruckRoute {
  vehicleId: string; // "TRK-T01"
  vehicleCode: string; // "V-01"
  vehicleName: string; // "Truck T01"
  driverName: string;
  routeColor: string; // "#4d8eff"
  routeName: string; // "경로 T01 (마포-여의도)"
  assignedDepotId: string; // "D01"
  assignedNodes: string[]; // ["D01", "N01", "C09", "D01"]
  polyline: [number, number][]; // Lat/Lng waypoints along the road
  totalDistanceKm: number;
  travelTimeMin: number;
  assignedCustomersCount: number;
  capacityKg: number;
  currentLoadKg: number;
  loadPercentage: number;
  tardinessRatePct: number;
  status: 'active' | 'risk' | 'warning' | 'idle';
}

export interface OptimizationSettings {
  objective: OptimizationObjective;
  truckCount: number;
  depotSelection: 'both' | 'D01' | 'D12';
  timeWindowWeight: 'low' | 'medium' | 'high';
  capacityLimit: number;
  realTimeTraffic: boolean;
}

export interface OptimizationResults {
  totalDistanceKm: number; // 1245
  totalTimeHours: number; // 48.5
  vehiclesUsed: number; // 5
  totalVehicles: number; // 10
  delayedDeliveriesCount: number; // 0
  activeRoutesLegend: {
    routeName: string; // "경로 A (북부)"
    vehicleCode: string; // "V-01"
    colorHex: string; // "#4d8eff"
  }[];
}

export interface FleetEfficiencyStats {
  efficiencyPercentage: number; // 94
  fuelConsumptionChange: string; // "-2.4%"
  avgIdlingMinutes: number; // 12
  activeTrucksCount: number; // 42
  activeTrucksDelta: number; // +3
  totalOrdersCount: number; // 1240
  routeRiskIndexLevel: 'Low' | 'Med-Low' | 'Medium' | 'High'; // "Med-Low"
  totalDistanceKmFormatted: string; // "12.4k"
  estimatedTotalHours: number; // 840
}
