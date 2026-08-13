import {
  RouteNode,
  FleetVehicle,
  IncidentAlert,
  RerouteScenario,
  OptimizationResults,
  FleetEfficiencyStats
} from './types';

// Map Center: Seoul (37.5665, 126.9780)
export const INITIAL_NODES: RouteNode[] = [
  {
    id: 'D01',
    name: 'Mapo Main Depot',
    lat: 37.5512,
    lng: 126.9142,
    type: 'depot',
    address: '서울특별시 마포구 월드컵북로 120'
  },
  {
    id: 'D12',
    name: 'Gangnam Hub Depot',
    lat: 37.4981,
    lng: 127.0276,
    type: 'depot',
    address: '서울특별시 강남구 테헤란로 152'
  },
  {
    id: 'N01',
    name: 'N01 (Yeouido Terminal)',
    lat: 37.5219,
    lng: 126.9242,
    type: 'pickup',
    demandKg: 450,
    timeWindow: '09:00 - 11:30'
  },
  {
    id: 'C03',
    name: 'C03 (Yongsan Distribution)',
    lat: 37.5326,
    lng: 126.9652,
    type: 'both',
    demandKg: 820,
    timeWindow: '10:00 - 13:00'
  },
  {
    id: 'C07',
    name: 'C07 (Seongsu Smart Hub)',
    lat: 37.5445,
    lng: 127.0558,
    type: 'delivery',
    demandKg: 600,
    timeWindow: '11:00 - 14:00'
  },
  {
    id: 'C09',
    name: 'C09 (Jongno Commercial)',
    lat: 37.5704,
    lng: 126.9922,
    type: 'delivery',
    demandKg: 350,
    timeWindow: '09:30 - 12:00'
  },
  {
    id: 'N12',
    name: 'N12 (Nowon Depot Node)',
    lat: 37.6542,
    lng: 127.0568,
    type: 'both',
    demandKg: 500,
    timeWindow: '12:00 - 15:00'
  },
  {
    id: 'S01',
    name: 'S01 (Secho Logistics)',
    lat: 37.4832,
    lng: 127.0112,
    type: 'delivery',
    demandKg: 710,
    timeWindow: '13:00 - 16:00'
  }
];

export const INITIAL_VEHICLES: FleetVehicle[] = [
  {
    id: 'TRK-T02',
    code: 'V-02',
    name: 'Truck T02',
    status: 'risk',
    currentSegment: 'C03 ➔ C07',
    assignedRouteName: '경로 B (동부)',
    routeColor: '#ffb95f',
    currentLat: 37.5385,
    currentLng: 127.0105,
    speedKmH: 18,
    capacityKg: 3000,
    currentLoadKg: 2550,
    loadPercentage: 85,
    delayMinutes: 45,
    etaMinutes: 171,
    driverName: '김민수 기사',
    notes: '돌발 상황: C03-C07 전방 추돌 사고 발생로 인한 정체'
  },
  {
    id: 'TRK-T05',
    code: 'V-05',
    name: 'Truck T05 (Backup)',
    status: 'active',
    currentSegment: 'D12 ➔ C07',
    assignedRouteName: '경로 B-2 (유휴 지원)',
    routeColor: '#4d8eff',
    currentLat: 37.5120,
    currentLng: 127.0420,
    speedKmH: 48,
    capacityKg: 3000,
    currentLoadKg: 1200,
    loadPercentage: 40,
    delayMinutes: 0,
    etaMinutes: 28,
    driverName: '박준혁 기사',
    notes: '인근 유휴 대기 상태 - 임무 승계 가능'
  },
  {
    id: 'TRK-T14',
    code: 'V-14',
    name: 'Truck T14',
    status: 'warning',
    currentSegment: 'N12 ➔ N15',
    assignedRouteName: '경로 A (북부)',
    routeColor: '#4d8eff',
    currentLat: 37.6200,
    currentLng: 127.0450,
    speedKmH: 32,
    capacityKg: 3500,
    currentLoadKg: 2800,
    loadPercentage: 80,
    delayMinutes: 12,
    etaMinutes: 42,
    driverName: '이성민 기사'
  },
  {
    id: 'TRK-T08',
    code: 'V-08',
    name: 'Truck T08',
    status: 'warning',
    currentSegment: 'S01 ➔ S04',
    assignedRouteName: '경로 C (도심)',
    routeColor: '#4edea3',
    currentLat: 37.4900,
    currentLng: 127.0200,
    speedKmH: 28,
    capacityKg: 2500,
    currentLoadKg: 1800,
    loadPercentage: 72,
    delayMinutes: 8,
    etaMinutes: 35,
    driverName: '최영호 기사'
  },
  {
    id: 'TRK-7042',
    code: 'V-01',
    name: 'Truck 7042',
    status: 'active',
    currentSegment: 'N01 ➔ C03',
    assignedRouteName: '경로 A (북부)',
    routeColor: '#4d8eff',
    currentLat: 37.5280,
    currentLng: 126.9450,
    speedKmH: 52,
    capacityKg: 3000,
    currentLoadKg: 2100,
    loadPercentage: 70,
    delayMinutes: 0,
    etaMinutes: 15,
    driverName: '정동원 기사'
  }
];

export const INITIAL_INCIDENT: IncidentAlert = {
  id: 'INC-102',
  type: 'Accident',
  title: '치명적 돌발 상황 감지',
  locationName: 'C03 ➔ C07 (용산-성수 구간)',
  riskScore: 0.92,
  severity: 'high',
  affectedVehicleIds: ['TRK-T02', 'TRK-T05'],
  timestamp: '방금 전',
  description: 'C03와 C07 구간 사이에서 3중 추돌 사고가 발생하여 심각한 병목 현상이 발생하고 있습니다. 활성 함대에 대한 즉각적인 재경로 설정이 권장됩니다.'
};

export const INITIAL_ALERTS: IncidentAlert[] = [
  INITIAL_INCIDENT,
  {
    id: 'IC-105',
    type: 'Congestion',
    title: '교통 정체: 강남대로',
    locationName: '강남대로 (테헤란로 교차로)',
    riskScore: 0.65,
    severity: 'medium',
    affectedVehicleIds: ['TRK-T08'],
    timestamp: '2분 전',
    description: '극심한 정체가 감지되었습니다. TRK-7042 차량의 예상 지연 시간은 15분입니다.'
  },
  {
    id: 'IC-201',
    type: 'Weather',
    title: '배송 완료',
    locationName: 'Terminal B',
    riskScore: 0.1,
    severity: 'low',
    affectedVehicleIds: [],
    timestamp: '14분 전',
    description: 'TRK-219 has completed route ORD-9921 at Terminal B.'
  },
  {
    id: 'IC-205',
    type: 'Weather',
    title: '기상 정보 업데이트',
    locationName: '북부 구역',
    riskScore: 0.2,
    severity: 'low',
    affectedVehicleIds: [],
    timestamp: '1시간 전',
    description: 'Light rain expected in northern sectors. Visibility normal.'
  }
];

export const DEFAULT_SCENARIOS: RerouteScenario[] = [
  {
    id: 'OPTION_A',
    optionTitle: 'Option A',
    koreanName: '경로 우회',
    subtitle: '(경로 우회)',
    description: '현재 방문 순서를 유지하되, 사고 구간을 회피하여 운행 경로를 변경합니다.',
    distanceKmChange: '+8km',
    totalDistanceKm: 134,
    travelTimeMin: 171,
    delayReductionMin: -21,
    tardinessCount: 0,
    addedCostUsd: 12.00,
    isRecommended: true
  },
  {
    id: 'OPTION_B',
    optionTitle: 'Option B',
    koreanName: '방문 순서 변경',
    subtitle: '(방문 순서 변경)',
    description: '정체 구역을 피해 효율적인 방문을 위해 잔여 목적지 방문 순서를 재조정합니다.',
    distanceKmChange: '+2km',
    totalDistanceKm: 128,
    travelTimeMin: 180,
    delayReductionMin: -12,
    tardinessCount: 1,
    tardinessDescription: '1 명 지연',
    addedCostUsd: 4.00
  },
  {
    id: 'OPTION_C',
    optionTitle: 'Option C',
    koreanName: '업무 승계 / 재배차',
    subtitle: '(업무 승계 / 재배차)',
    description: '잔여 물량을 인근 유휴 트럭(T05)에게 이관하여 배송을 완료합니다.',
    distanceKmChange: '+19km',
    totalDistanceKm: 145,
    travelTimeMin: 160,
    delayReductionMin: -32,
    tardinessCount: 0,
    addedCostUsd: 45.00
  }
];

export const DEFAULT_OPTIMIZATION_RESULTS: OptimizationResults = {
  totalDistanceKm: 1245,
  totalTimeHours: 48.5,
  vehiclesUsed: 5,
  totalVehicles: 10,
  delayedDeliveriesCount: 0,
  activeRoutesLegend: [
    { routeName: '경로 A (북부)', vehicleCode: 'V-01', colorHex: '#4d8eff' },
    { routeName: '경로 B (동부)', vehicleCode: 'V-03', colorHex: '#ffb95f' },
    { routeName: '경로 C (도심)', vehicleCode: 'V-04', colorHex: '#4edea3' }
  ]
};

export const DEFAULT_EFFICIENCY_STATS: FleetEfficiencyStats = {
  efficiencyPercentage: 94,
  fuelConsumptionChange: '-2.4%',
  avgIdlingMinutes: 12,
  activeTrucksCount: 42,
  activeTrucksDelta: 3,
  totalOrdersCount: 1240,
  routeRiskIndexLevel: 'Med-Low',
  totalDistanceKmFormatted: '12.4k',
  estimatedTotalHours: 840
};
