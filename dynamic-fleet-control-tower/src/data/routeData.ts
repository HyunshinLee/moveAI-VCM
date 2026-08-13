import { PlannedTruckRoute, OptimizationSettings } from '../types';

export const ALL_TRUCK_PRESETS: PlannedTruckRoute[] = [
  {
    vehicleId: 'TRK-T01',
    vehicleCode: 'V-01',
    vehicleName: 'Truck T01',
    driverName: '정동원 기사',
    routeColor: '#4d8eff',
    routeName: '경로 T01 (마포-여의도-종로)',
    assignedDepotId: 'D01',
    assignedNodes: ['D01', 'N01', 'C09', 'D01'],
    polyline: [
      [37.5512, 126.9142], // D01 Mapo Depot
      [37.5350, 126.9180],
      [37.5219, 126.9242], // N01 Yeouido
      [37.5450, 126.9580],
      [37.5704, 126.9922], // C09 Jongno
      [37.5610, 126.9450],
      [37.5512, 126.9142], // D01 Mapo Depot
    ],
    totalDistanceKm: 38.5,
    travelTimeMin: 72,
    assignedCustomersCount: 2,
    capacityKg: 3000,
    currentLoadKg: 2100,
    loadPercentage: 70,
    tardinessRatePct: 0.0,
    status: 'active',
  },
  {
    vehicleId: 'TRK-T02',
    vehicleCode: 'V-02',
    vehicleName: 'Truck T02',
    driverName: '김민수 기사',
    routeColor: '#ffb95f',
    routeName: '경로 T02 (마포-용산-성수-강남)',
    assignedDepotId: 'D01',
    assignedNodes: ['D01', 'C03', 'C07', 'D12'],
    polyline: [
      [37.5512, 126.9142], // D01 Mapo
      [37.5400, 126.9420],
      [37.5326, 126.9652], // C03 Yongsan
      [37.5385, 127.0105],
      [37.5445, 127.0558], // C07 Seongsu
      [37.5200, 127.0420],
      [37.4981, 127.0276], // D12 Gangnam
    ],
    totalDistanceKm: 42.8,
    travelTimeMin: 95,
    assignedCustomersCount: 2,
    capacityKg: 3000,
    currentLoadKg: 2550,
    loadPercentage: 85,
    tardinessRatePct: 0.0,
    status: 'active',
  },
  {
    vehicleId: 'TRK-T03',
    vehicleCode: 'V-03',
    vehicleName: 'Truck T03',
    driverName: '최영호 기사',
    routeColor: '#4edea3',
    routeName: '경로 T03 (강남-서초-용산-강남)',
    assignedDepotId: 'D12',
    assignedNodes: ['D12', 'S01', 'C03', 'D12'],
    polyline: [
      [37.4981, 127.0276], // D12 Gangnam
      [37.4900, 127.0180],
      [37.4832, 127.0112], // S01 Seocho
      [37.5100, 126.9850],
      [37.5326, 126.9652], // C03 Yongsan
      [37.5050, 127.0080],
      [37.4981, 127.0276], // D12 Gangnam
    ],
    totalDistanceKm: 34.2,
    travelTimeMin: 68,
    assignedCustomersCount: 2,
    capacityKg: 2500,
    currentLoadKg: 1800,
    loadPercentage: 72,
    tardinessRatePct: 0.0,
    status: 'active',
  },
  {
    vehicleId: 'TRK-T04',
    vehicleCode: 'V-04',
    vehicleName: 'Truck T04',
    driverName: '이성민 기사',
    routeColor: '#a855f7',
    routeName: '경로 T04 (마포-노원-성수-마포)',
    assignedDepotId: 'D01',
    assignedNodes: ['D01', 'N12', 'C07', 'D01'],
    polyline: [
      [37.5512, 126.9142], // D01 Mapo
      [37.6000, 126.9800],
      [37.6542, 127.0568], // N12 Nowon
      [37.6000, 127.0600],
      [37.5445, 127.0558], // C07 Seongsu
      [37.5600, 126.9700],
      [37.5512, 126.9142], // D01 Mapo
    ],
    totalDistanceKm: 52.0,
    travelTimeMin: 110,
    assignedCustomersCount: 2,
    capacityKg: 3500,
    currentLoadKg: 2800,
    loadPercentage: 80,
    tardinessRatePct: 0.0,
    status: 'active',
  },
  {
    vehicleId: 'TRK-T05',
    vehicleCode: 'V-05',
    vehicleName: 'Truck T05',
    driverName: '박준혁 기사',
    routeColor: '#06b6d4',
    routeName: '경로 T05 (강남-성수-종로-강남)',
    assignedDepotId: 'D12',
    assignedNodes: ['D12', 'C07', 'C09', 'D12'],
    polyline: [
      [37.4981, 127.0276], // D12 Gangnam
      [37.5180, 127.0450],
      [37.5445, 127.0558], // C07 Seongsu
      [37.5580, 127.0150],
      [37.5704, 126.9922], // C09 Jongno
      [37.5300, 127.0100],
      [37.4981, 127.0276], // D12 Gangnam
    ],
    totalDistanceKm: 36.8,
    travelTimeMin: 80,
    assignedCustomersCount: 2,
    capacityKg: 3000,
    currentLoadKg: 1950,
    loadPercentage: 65,
    tardinessRatePct: 0.0,
    status: 'active',
  },
  {
    vehicleId: 'TRK-T06',
    vehicleCode: 'V-06',
    vehicleName: 'Truck T06',
    driverName: '한승우 기사',
    routeColor: '#ec4899',
    routeName: '경로 T06 (마포-서초-강남)',
    assignedDepotId: 'D01',
    assignedNodes: ['D01', 'S01', 'D12'],
    polyline: [
      [37.5512, 126.9142],
      [37.5050, 126.9600],
      [37.4832, 127.0112],
      [37.4981, 127.0276],
    ],
    totalDistanceKm: 28.4,
    travelTimeMin: 58,
    assignedCustomersCount: 1,
    capacityKg: 2500,
    currentLoadKg: 1500,
    loadPercentage: 60,
    tardinessRatePct: 0.0,
    status: 'active',
  },
  {
    vehicleId: 'TRK-T07',
    vehicleCode: 'V-07',
    vehicleName: 'Truck T07',
    driverName: '강태호 기사',
    routeColor: '#eab308',
    routeName: '경로 T07 (노원-종로-마포)',
    assignedDepotId: 'D01',
    assignedNodes: ['N12', 'C09', 'D01'],
    polyline: [
      [37.6542, 127.0568],
      [37.6100, 127.0200],
      [37.5704, 126.9922],
      [37.5512, 126.9142],
    ],
    totalDistanceKm: 31.6,
    travelTimeMin: 64,
    assignedCustomersCount: 2,
    capacityKg: 3000,
    currentLoadKg: 2100,
    loadPercentage: 70,
    tardinessRatePct: 0.0,
    status: 'active',
  },
  {
    vehicleId: 'TRK-T08',
    vehicleCode: 'V-08',
    vehicleName: 'Truck T08',
    driverName: '윤서준 기사',
    routeColor: '#6366f1',
    routeName: '경로 T08 (강남-여의도-서초)',
    assignedDepotId: 'D12',
    assignedNodes: ['D12', 'N01', 'S01', 'D12'],
    polyline: [
      [37.4981, 127.0276],
      [37.5100, 126.9600],
      [37.5219, 126.9242],
      [37.4832, 127.0112],
      [37.4981, 127.0276],
    ],
    totalDistanceKm: 39.1,
    travelTimeMin: 82,
    assignedCustomersCount: 2,
    capacityKg: 3000,
    currentLoadKg: 2200,
    loadPercentage: 73,
    tardinessRatePct: 0.0,
    status: 'active',
  },
  {
    vehicleId: 'TRK-T09',
    vehicleCode: 'V-09',
    vehicleName: 'Truck T09',
    driverName: '오현우 기사',
    routeColor: '#14b8a6',
    routeName: '경로 T09 (성수-노원-강남)',
    assignedDepotId: 'D12',
    assignedNodes: ['C07', 'N12', 'D12'],
    polyline: [
      [37.5445, 127.0558],
      [37.6000, 127.0600],
      [37.6542, 127.0568],
      [37.5800, 127.0400],
      [37.4981, 127.0276],
    ],
    totalDistanceKm: 35.0,
    travelTimeMin: 75,
    assignedCustomersCount: 2,
    capacityKg: 2800,
    currentLoadKg: 1960,
    loadPercentage: 70,
    tardinessRatePct: 0.0,
    status: 'active',
  },
  {
    vehicleId: 'TRK-T10',
    vehicleCode: 'V-10',
    vehicleName: 'Truck T10',
    driverName: '임재범 기사',
    routeColor: '#f97316',
    routeName: '경로 T10 (마포-종로-용산)',
    assignedDepotId: 'D01',
    assignedNodes: ['D01', 'C09', 'C03', 'D01'],
    polyline: [
      [37.5512, 126.9142],
      [37.5650, 126.9600],
      [37.5704, 126.9922],
      [37.5326, 126.9652],
      [37.5512, 126.9142],
    ],
    totalDistanceKm: 29.8,
    travelTimeMin: 60,
    assignedCustomersCount: 2,
    capacityKg: 3000,
    currentLoadKg: 2400,
    loadPercentage: 80,
    tardinessRatePct: 0.0,
    status: 'active',
  },
];

export const generatePlannedRoutes = (settings: OptimizationSettings): PlannedTruckRoute[] => {
  const { objective, truckCount, depotSelection } = settings;

  // Select base preset count
  let routes = ALL_TRUCK_PRESETS.slice(0, Math.min(truckCount, ALL_TRUCK_PRESETS.length));

  // Filter by depot selection if specified
  if (depotSelection === 'D01') {
    routes = routes.map((r) => ({
      ...r,
      assignedDepotId: 'D01',
      polyline: r.polyline.map((p, idx) =>
        idx === 0 || idx === r.polyline.length - 1 ? [37.5512, 126.9142] as [number, number] : p
      ),
    }));
  } else if (depotSelection === 'D12') {
    routes = routes.map((r) => ({
      ...r,
      assignedDepotId: 'D12',
      polyline: r.polyline.map((p, idx) =>
        idx === 0 || idx === r.polyline.length - 1 ? [37.4981, 127.0276] as [number, number] : p
      ),
    }));
  }

  // Objective specific transformations
  return routes.map((route) => {
    let distanceFactor = 1.0;
    let timeFactor = 1.0;
    let tardinessRate = 0.0;
    let loadPct = route.loadPercentage;

    switch (objective) {
      case 'fast':
        timeFactor = 0.82; // 18% faster routes
        distanceFactor = 1.05;
        tardinessRate = 0.0;
        break;
      case 'satisfaction':
        timeFactor = 0.95;
        tardinessRate = 0.0; // 0% delay rate
        break;
      case 'cost':
        distanceFactor = 0.88; // 12% shorter distance
        timeFactor = 0.92;
        loadPct = Math.min(98, Math.round(route.loadPercentage * 1.15)); // Higher load efficiency
        break;
      case 'balanced':
      default:
        distanceFactor = 1.0;
        timeFactor = 1.0;
        tardinessRate = 0.0;
        break;
    }

    const totalDist = Math.round(route.totalDistanceKm * distanceFactor * 10) / 10;
    const travelTime = Math.round(route.travelTimeMin * timeFactor);

    return {
      ...route,
      totalDistanceKm: totalDist,
      travelTimeMin: travelTime,
      loadPercentage: loadPct,
      currentLoadKg: Math.round((route.capacityKg * loadPct) / 100),
      tardinessRatePct: tardinessRate,
    };
  });
};
