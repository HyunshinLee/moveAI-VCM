import React, { useEffect, useRef, useState, useMemo } from 'react';
import L from 'leaflet';
import { RouteNode, PlannedTruckRoute, FleetVehicle, IncidentAlert, ScenarioOptionId } from '../types';
import { ALL_PHYSICAL_NODES, ROAD_BACKBONE_NODES, PhysicalNode } from '../data/physicalNetwork';
import { ALL_TRUCK_PRESETS } from '../data/routeData';

export interface RoutePlanningMapProps {
  nodes: RouteNode[];
  truckRoutes?: PlannedTruckRoute[];
  vehicles?: FleetVehicle[];
  activeIncident?: IncidentAlert | null;
  selectedVehicleId?: string | null;
  onSelectVehicle?: (vehicleId: string | null) => void;
  onOpenRerouteConsole?: () => void;
  simulatedTimeProgress?: number; // 0.0 to 1.0
  isPlaying?: boolean;
  onTogglePlay?: () => void;
  speedMultiplier?: 1 | 2 | 5;
  onChangeSpeed?: (speed: 1 | 2 | 5) => void;
  onTimeProgressChange?: (progress: number) => void;
  activeScenarioId?: ScenarioOptionId | null;
}

// Calculate interpolated position along polyline
const getInterpolatedCoordinate = (
  polyline: [number, number][],
  progress: number
): [number, number] => {
  if (!polyline || polyline.length === 0) return [37.5512, 126.9142];
  if (polyline.length === 1 || progress <= 0) return polyline[0];
  if (progress >= 1) return polyline[polyline.length - 1];

  const segmentLengths: number[] = [];
  let totalLength = 0;

  for (let i = 0; i < polyline.length - 1; i++) {
    const [lat1, lng1] = polyline[i];
    const [lat2, lng2] = polyline[i + 1];
    const dist = Math.hypot(lat2 - lat1, lng2 - lng1);
    segmentLengths.push(dist);
    totalLength += dist;
  }

  if (totalLength === 0) return polyline[0];

  const targetDist = progress * totalLength;
  let accumulatedDist = 0;

  for (let i = 0; i < polyline.length - 1; i++) {
    const segLen = segmentLengths[i];
    if (accumulatedDist + segLen >= targetDist) {
      const segProgress = segLen === 0 ? 0 : (targetDist - accumulatedDist) / segLen;
      const [lat1, lng1] = polyline[i];
      const [lat2, lng2] = polyline[i + 1];
      const lat = lat1 + segProgress * (lat2 - lat1);
      const lng = lng1 + segProgress * (lng2 - lng1);
      return [lat, lng];
    }
    accumulatedDist += segLen;
  }

  return polyline[polyline.length - 1];
};

// Format time from 0.0-1.0 to 09:00 AM -> 05:00 PM
const formatSimulatedTime = (progress: number): string => {
  const startHour = 9; // 09:00 AM
  const totalHours = 8; // 8 hours duration -> 17:00 (05:00 PM)
  const currentTotalMin = startHour * 60 + progress * (totalHours * 60);

  const hours = Math.floor(currentTotalMin / 60);
  const minutes = Math.floor(currentTotalMin % 60);

  const period = hours >= 12 ? 'PM' : 'AM';
  const displayHour = hours > 12 ? hours - 12 : hours === 0 ? 12 : hours;
  const formattedMin = minutes < 10 ? `0${minutes}` : minutes;

  return `${displayHour < 10 ? '0' : ''}${displayHour}:${formattedMin} ${period}`;
};

export const RoutePlanningMap: React.FC<RoutePlanningMapProps> = ({
  nodes,
  truckRoutes: propTruckRoutes,
  vehicles = [],
  activeIncident,
  selectedVehicleId = null,
  onSelectVehicle: propOnSelectVehicle,
  onOpenRerouteConsole,
  simulatedTimeProgress: propSimulatedTimeProgress,
  isPlaying: propIsPlaying,
  onTogglePlay: propOnTogglePlay,
  speedMultiplier: propSpeedMultiplier,
  onChangeSpeed: propOnChangeSpeed,
  onTimeProgressChange: propOnTimeProgressChange,
  activeScenarioId,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const leafletMapRef = useRef<L.Map | null>(null);
  const layerGroupRef = useRef<L.LayerGroup | null>(null);
  const [trafficLayerEnabled, setTrafficLayerEnabled] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Internal state fallbacks if props are not passed
  const [internalTimeProgress, setInternalTimeProgress] = useState<number>(0.15);
  const [internalIsPlaying, setInternalIsPlaying] = useState<boolean>(false);
  const [internalSpeedMultiplier, setInternalSpeedMultiplier] = useState<1 | 2 | 5>(1);

  const simulatedTimeProgress = propSimulatedTimeProgress !== undefined ? propSimulatedTimeProgress : internalTimeProgress;
  const isPlaying = propIsPlaying !== undefined ? propIsPlaying : internalIsPlaying;
  const speedMultiplier = propSpeedMultiplier !== undefined ? propSpeedMultiplier : internalSpeedMultiplier;

  const handleTogglePlay = () => {
    if (propOnTogglePlay) {
      propOnTogglePlay();
    } else {
      setInternalIsPlaying((prev) => !prev);
    }
  };

  const handleChangeSpeed = (speed: 1 | 2 | 5) => {
    if (propOnChangeSpeed) {
      propOnChangeSpeed(speed);
    } else {
      setInternalSpeedMultiplier(speed);
    }
  };

  const handleTimeProgressChange = (progress: number) => {
    if (propOnTimeProgressChange) {
      propOnTimeProgressChange(progress);
    } else {
      setInternalTimeProgress(progress);
    }
  };

  const handleSelectVehicle = (vehicleId: string | null) => {
    if (propOnSelectVehicle) {
      propOnSelectVehicle(vehicleId);
    }
  };

  const effectiveTruckRoutes = useMemo(() => {
    if (propTruckRoutes && propTruckRoutes.length > 0) {
      return propTruckRoutes;
    }
    return ALL_TRUCK_PRESETS;
  }, [propTruckRoutes]);

  // Internal ticker when simulation state is un-controlled
  useEffect(() => {
    if (propIsPlaying !== undefined) return;
    if (!internalIsPlaying) return;

    const interval = setInterval(() => {
      setInternalTimeProgress((prev) => {
        const step = 0.0012 * internalSpeedMultiplier;
        if (prev + step >= 1.0) {
          setInternalIsPlaying(false);
          return 1.0;
        }
        return prev + step;
      });
    }, 40);

    return () => clearInterval(interval);
  }, [propIsPlaying, internalIsPlaying, internalSpeedMultiplier]);

  // Physical Network Layer States
  const [showPhysicalLayer, setShowPhysicalLayer] = useState(true);
  const [showBackboneNodes, setShowBackboneNodes] = useState(true);
  const [showPhysicalDepots, setShowPhysicalDepots] = useState(true);
  const [showPhysicalCustomers, setShowPhysicalCustomers] = useState(true);
  const [isLayerControlOpen, setIsLayerControlOpen] = useState(false);

  // Invalidate map size and preserve center/zoom when toggling fullscreen
  useEffect(() => {
    if (leafletMapRef.current) {
      const map = leafletMapRef.current;
      const currentCenter = map.getCenter();
      const currentZoom = map.getZoom();
      const timer = setTimeout(() => {
        map.invalidateSize();
        map.setView(currentCenter, currentZoom, { animate: false });
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [isFullscreen]);

  // Map Center: Seoul Metropolitan Area
  const centerLat = 37.5385;
  const centerLng = 126.985;

  // Precalculate Physical Network Backbone Highway Connections
  const backboneEdges = useMemo(() => {
    const edges: [[number, number], [number, number]][] = [];
    const nodes = ROAD_BACKBONE_NODES;
    for (let i = 0; i < nodes.length; i++) {
      const n1 = nodes[i];
      const neighbors: { dist: number; coord: [number, number] }[] = [];
      for (let j = 0; j < nodes.length; j++) {
        if (i === j) continue;
        const n2 = nodes[j];
        const dist = Math.hypot(n1.latitude - n2.latitude, n1.longitude - n2.longitude);
        if (dist < 0.22) {
          neighbors.push({ dist, coord: [n2.latitude, n2.longitude] });
        }
      }
      neighbors.sort((a, b) => a.dist - b.dist);
      for (const neighbor of neighbors.slice(0, 2)) {
        edges.push([[n1.latitude, n1.longitude], neighbor.coord]);
      }
    }
    return edges;
  }, []);

  // Initialize map instance
  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!leafletMapRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: [centerLat, centerLng],
        zoom: 12,
        zoomControl: false,
        attributionControl: false,
      });

      // CartoDB Voyager Tile Layer (Google Maps-like Road Navigation Style)
      L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        maxZoom: 19,
        subdomains: 'abcd',
      }).addTo(map);

      // Click on map background resets selected truck
      map.on('click', (e) => {
        if ((e.originalEvent.target as HTMLElement).tagName.toLowerCase() === 'div') {
          handleSelectVehicle(null);
        }
      });

      const layerGroup = L.layerGroup().addTo(map);
      layerGroupRef.current = layerGroup;
      leafletMapRef.current = map;
    }
  }, []);

  // Update map polylines and markers whenever effectiveTruckRoutes, selectedVehicleId, activeIncident, or time progress changes
  useEffect(() => {
    const map = leafletMapRef.current;
    const layerGroup = layerGroupRef.current;
    if (!map || !layerGroup) return;

    layerGroup.clearLayers();

    const isIncidentActive = activeIncident && !activeIncident.resolved;

    // 1. Draw Physical Road Network Layer (Road Backbone Highways & Connector Feeders)
    if (showPhysicalLayer) {
      // 1A. Physical Backbone Highways (Integrated Royal Blue Network on Google Maps Basemap)
      if (showBackboneNodes && backboneEdges.length > 0) {
        L.polyline(backboneEdges, {
          color: '#2563eb',
          weight: 3.5,
          opacity: 0.7,
          lineCap: 'round',
          lineJoin: 'round',
        }).addTo(layerGroup);
      }

      // 1B. Feeder lines connecting Customers and Depots to nearest backbone nodes
      const feederLines: [[number, number], [number, number]][] = [];
      ALL_PHYSICAL_NODES.forEach((pNode) => {
        if (
          (pNode.type === 'customer' && showPhysicalCustomers) ||
          (pNode.type === 'depot' && showPhysicalDepots)
        ) {
          if (pNode.nearestBackboneNode) {
            const bNode = ALL_PHYSICAL_NODES.find((n) => n.id === pNode.nearestBackboneNode);
            if (bNode) {
              feederLines.push([
                [pNode.latitude, pNode.longitude],
                [bNode.latitude, bNode.longitude],
              ]);
            }
          }
        }
      });

      if (feederLines.length > 0) {
        L.polyline(feederLines, {
          color: '#0284c7',
          weight: 1.5,
          opacity: 0.6,
          dashArray: '4, 4',
        }).addTo(layerGroup);
      }
    }

    // 2. Draw Incident Hazard Area (`C03 ─────── ⚠ INCIDENT ─────── C07`) & Detour Polylines
    if (isIncidentActive) {
      const hazardSegmentPoints: [number, number][] = [
        [37.5326, 126.9652], // C03
        [37.5385, 127.0105], // Incident location
        [37.5445, 127.0558], // C07
      ];

      // Red hazard glow line
      L.polyline(hazardSegmentPoints, {
        color: '#fca5a5',
        weight: 12,
        opacity: 0.4,
        lineCap: 'round',
      }).addTo(layerGroup);

      // Red dashed hazard line
      L.polyline(hazardSegmentPoints, {
        color: '#dc2626',
        weight: 6,
        opacity: 1.0,
        dashArray: '8, 6',
        lineCap: 'round',
      }).addTo(layerGroup);

      // Detour Option A line if scenario is applied
      if (activeScenarioId === 'OPTION_A') {
        const optionADetourPoints: [number, number][] = [
          [37.5326, 126.9652], // C03
          [37.5550, 127.0000], // Northern bypass
          [37.5580, 127.0400],
          [37.5445, 127.0558], // C07
        ];

        L.polyline(optionADetourPoints, {
          color: '#a7f3d0',
          weight: 10,
          opacity: 0.4,
          lineCap: 'round',
        }).addTo(layerGroup);

        L.polyline(optionADetourPoints, {
          color: '#059669',
          weight: 5,
          opacity: 1.0,
          dashArray: '6, 6',
          lineCap: 'round',
        }).addTo(layerGroup);
      }
    }

    // 3. Draw Active Truck Route Polylines (With white underlay stroke for pop & high contrast)
    effectiveTruckRoutes.forEach((route) => {
      const isSelected = selectedVehicleId === route.vehicleId;
      const hasSelection = selectedVehicleId !== null;

      let opacity = 0.9;
      let weight = 4.5;

      if (hasSelection) {
        if (isSelected) {
          opacity = 1.0;
          weight = 6.5;
        } else {
          opacity = 0.25;
          weight = 3;
        }
      }

      // High-contrast white border underlay stroke
      L.polyline(route.polyline, {
        color: '#ffffff',
        weight: weight + 3,
        opacity: isSelected ? 0.95 : hasSelection && !isSelected ? 0.2 : 0.7,
        lineCap: 'round',
        lineJoin: 'round',
      }).addTo(layerGroup);

      // Main colored route polyline
      const mainPolyline = L.polyline(route.polyline, {
        color: hasSelection && !isSelected ? '#94a3b8' : route.routeColor,
        weight,
        opacity,
        dashArray: isSelected ? undefined : '8, 6',
        lineCap: 'round',
        lineJoin: 'round',
      }).addTo(layerGroup);

      mainPolyline.on('click', (e) => {
        L.DomEvent.stopPropagation(e);
        handleSelectVehicle(route.vehicleId);
      });

      mainPolyline.bindTooltip(
        `<div class="font-sans font-bold text-xs" style="color: ${route.routeColor}">${route.routeName} (${route.vehicleName})</div>`,
        { sticky: true }
      );
    });

    // 4. Draw Physical Network Nodes (Hierarchy: Depot > Customer > Backbone)
    if (showPhysicalLayer) {
      ALL_PHYSICAL_NODES.forEach((pNode) => {
        if (pNode.type === 'road_backbone' && !showBackboneNodes) return;
        if (pNode.type === 'depot' && !showPhysicalDepots) return;
        if (pNode.type === 'customer' && !showPhysicalCustomers) return;

        if (pNode.type === 'road_backbone') {
          const isKeyInterchange =
            pNode.name.includes('IC') || pNode.name.includes('JC') || pNode.name.includes('Jct');
          const iconHtml = `
            <div class="w-2.5 h-2.5 rounded-full bg-[#334155] border border-[#0f172a] hover:bg-[#2563eb] hover:scale-150 transition-all shadow-sm cursor-pointer" title="${pNode.id}: ${pNode.name}"></div>
          `;
          const icon = L.divIcon({
            html: iconHtml,
            className: 'custom-physical-backbone',
            iconSize: [10, 10],
            iconAnchor: [5, 5],
          });
          const marker = L.marker([pNode.latitude, pNode.longitude], { icon, zIndexOffset: 200 }).addTo(layerGroup);

          marker.bindPopup(`
            <div class="p-1 font-sans">
              <div class="text-[10px] font-bold text-[#8c909f] uppercase">🛣️ Road Backbone Node</div>
              <div class="font-bold text-sm text-[#adc6ff] mt-0.5">${pNode.name} (${pNode.id})</div>
              <div class="text-xs text-[#c2c6d6] font-mono mt-1">위도: ${pNode.latitude.toFixed(5)}, 경도: ${pNode.longitude.toFixed(5)}</div>
            </div>
          `);
        } else if (pNode.type === 'depot') {
          const iconHtml = `
            <div class="relative flex flex-col items-center justify-center cursor-pointer group">
              <div class="w-7 h-7 rounded-lg bg-[#0f172a] border-2 border-[#2563eb] flex items-center justify-center shadow-xl hover:scale-110 transition-transform">
                <span class="text-[10px] font-mono font-bold text-white">${pNode.id}</span>
              </div>
              <div class="mt-1 whitespace-nowrap bg-[#0f172a] text-[#f8fafc] px-2 py-0.5 rounded-md text-[10px] font-mono font-bold border border-[#3b82f6] shadow-lg pointer-events-none flex items-center gap-1">
                <span class="w-2 h-2 rounded-full bg-[#3b82f6]"></span>
                <span>${pNode.name}</span>
              </div>
            </div>
          `;
          const icon = L.divIcon({
            html: iconHtml,
            className: 'custom-physical-depot',
            iconSize: [32, 48],
            iconAnchor: [16, 16],
          });
          const marker = L.marker([pNode.latitude, pNode.longitude], { icon, zIndexOffset: 800 }).addTo(layerGroup);

          marker.bindPopup(`
            <div class="p-1.5 font-sans">
              <div class="text-[10px] font-bold text-[#8c909f] uppercase">🏭 Physical Depot / Hub</div>
              <div class="font-bold text-sm text-[#adc6ff] mt-0.5">${pNode.name} (${pNode.id})</div>
              <div class="text-xs text-[#c2c6d6] font-mono mt-1">위도: ${pNode.latitude.toFixed(5)}, 경도: ${pNode.longitude.toFixed(5)}</div>
            </div>
          `);
        } else if (pNode.type === 'customer') {
          const iconHtml = `
            <div class="relative flex flex-col items-center justify-center cursor-pointer group">
              <div class="w-5 h-5 rounded-full bg-[#0f766e] border-2 border-[#14b8a6] flex items-center justify-center shadow-lg hover:scale-125 transition-transform">
                <span class="text-[8px] font-mono font-bold text-white">${pNode.id.replace('C', '')}</span>
              </div>
              <div class="mt-0.5 hidden group-hover:flex whitespace-nowrap bg-[#0f172a] text-[#ccfbf1] px-1.5 py-0.5 rounded text-[9px] font-mono font-semibold border border-[#14b8a6]/60 shadow-md pointer-events-none z-30 items-center gap-1">
                <span>🛒 ${pNode.name}</span>
              </div>
            </div>
          `;
          const icon = L.divIcon({
            html: iconHtml,
            className: 'custom-physical-customer',
            iconSize: [20, 20],
            iconAnchor: [10, 10],
          });
          const marker = L.marker([pNode.latitude, pNode.longitude], { icon, zIndexOffset: 500 }).addTo(layerGroup);

          marker.bindPopup(`
            <div class="p-1.5 font-sans">
              <div class="text-[10px] font-bold text-[#8c909f] uppercase">🛒 Physical Customer Point</div>
              <div class="font-bold text-sm text-[#adc6ff] mt-0.5">${pNode.name} (${pNode.id})</div>
              <div class="text-xs text-[#c2c6d6] font-mono mt-1">위도: ${pNode.latitude.toFixed(5)}, 경도: ${pNode.longitude.toFixed(5)}</div>
            </div>
          `);
        }
      });
    }

    // 5. Draw Planning Depot & Customer Overlay Node Markers
    nodes.forEach((node) => {
      const isDepot = node.type === 'depot';

      if (isDepot) {
        const iconHtml = `
          <div class="relative flex flex-col items-center justify-center cursor-pointer">
            <div class="w-8 h-8 rounded-lg bg-[#0f172a] border-2 border-[#3b82f6] flex items-center justify-center shadow-xl">
              <span class="text-xs font-mono font-bold text-white">${node.id}</span>
            </div>
            <div class="mt-1 whitespace-nowrap bg-[#0f172a] text-[#e2e8f0] px-2 py-0.5 rounded-md text-[10px] font-mono font-bold border border-[#3b82f6]/60 shadow-md">
              ${node.name}
            </div>
          </div>
        `;
        const customIcon = L.divIcon({
          html: iconHtml,
          className: 'custom-node-icon',
          iconSize: [32, 48],
          iconAnchor: [16, 16],
        });
        const marker = L.marker([node.lat, node.lng], { icon: customIcon, zIndexOffset: 850 }).addTo(layerGroup);

        marker.bindPopup(`
          <div class="p-1 font-sans">
            <div class="font-bold text-sm text-[#adc6ff]">${node.name} (${node.id})</div>
            <div class="text-xs text-[#c2c6d6] mt-0.5">${node.address || '노드 위치'}</div>
          </div>
        `);
      } else {
        const iconHtml = `
          <div class="relative flex flex-col items-center justify-center cursor-pointer">
            <div class="w-5.5 h-5.5 rounded-full bg-[#0284c7] border-2 border-white flex items-center justify-center shadow-md">
              <span class="text-[9px] font-mono font-bold text-white">${node.id}</span>
            </div>
            <div class="mt-0.5 whitespace-nowrap bg-[#0f172a]/90 text-[#e2e8f0] px-1.5 py-0.5 rounded text-[9px] font-mono border border-slate-700 shadow-sm">
              ${node.name}
            </div>
          </div>
        `;
        const customIcon = L.divIcon({
          html: iconHtml,
          className: 'custom-node-icon',
          iconSize: [22, 38],
          iconAnchor: [11, 11],
        });
        const marker = L.marker([node.lat, node.lng], { icon: customIcon, zIndexOffset: 550 }).addTo(layerGroup);

        marker.bindPopup(`
          <div class="p-1 font-sans">
            <div class="font-bold text-sm text-[#adc6ff]">${node.name} (${node.id})</div>
            <div class="text-xs text-[#c2c6d6] mt-0.5">${node.address || '노드 위치'}</div>
            ${
              node.timeWindow
                ? `<div class="text-[11px] text-[#ffb95f] font-mono mt-1">⏰ 시간창: ${node.timeWindow}</div>`
                : ''
            }
            ${
              node.demandKg
                ? `<div class="text-[11px] text-[#4edea3] font-mono">📦 물동량: ${node.demandKg} kg</div>`
                : ''
            }
          </div>
        `);
      }
    });

    // 6. Draw Incident Hazard Marker if active
    if (isIncidentActive) {
      const incidentLat = 37.5385;
      const incidentLng = 127.0105;

      const incidentIconHtml = `
        <div class="relative flex items-center justify-center cursor-pointer group">
          <div class="absolute w-12 h-12 rounded-full bg-red-500/40 animate-ping"></div>
          <div class="w-9 h-9 rounded-full bg-[#b91c1c] border-2 border-[#fef2f2] flex items-center justify-center shadow-2xl text-white z-10">
            <span class="material-symbols-outlined text-base font-bold">car_crash</span>
          </div>
          <div class="absolute -top-8 whitespace-nowrap bg-[#7f1d1d] text-[#fef2f2] px-2.5 py-1 rounded-lg text-xs font-bold border border-[#fca5a5] shadow-2xl flex items-center gap-1.5 z-20">
            <span class="w-2 h-2 rounded-full bg-red-400 animate-pulse"></span>
            <span>🚨 INCIDENT: C03-C07 (+45m)</span>
          </div>
        </div>
      `;

      const incidentIcon = L.divIcon({
        html: incidentIconHtml,
        className: 'custom-incident-icon',
        iconSize: [36, 36],
        iconAnchor: [18, 18],
      });

      const incidentMarker = L.marker([incidentLat, incidentLng], {
        icon: incidentIcon,
        zIndexOffset: 2500, // Highest zIndex
      }).addTo(layerGroup);

      incidentMarker.on('click', (e) => {
        L.DomEvent.stopPropagation(e);
        handleSelectVehicle('TRK-T02');
      });
    }

    // 7. Draw Moving & Risk Vehicles (Top Hierarchy)
    effectiveTruckRoutes.forEach((route) => {
      const isSelected = selectedVehicleId === route.vehicleId;
      const vehicleState = vehicles.find((v) => v.id === route.vehicleId);
      const isRisk = vehicleState?.status === 'risk' || (route.vehicleId === 'TRK-T02' && isIncidentActive);
      const isWarning = vehicleState?.status === 'warning';

      const currentCoord = isRisk
        ? ([37.5326, 126.9652] as [number, number]) // Positioned at C03 risk segment
        : getInterpolatedCoordinate(route.polyline, simulatedTimeProgress);

      const truckIconHtml = `
        <div class="relative flex flex-col items-center justify-center cursor-pointer group transition-transform ${
          isSelected || isRisk ? 'scale-125 z-40' : 'hover:scale-110 z-30'
        }">
          ${
            isRisk
              ? '<div class="absolute w-12 h-12 rounded-xl bg-red-500/40 animate-ping"></div>'
              : isSelected
              ? `<div class="absolute w-10 h-10 rounded-lg opacity-50 animate-ping" style="background-color: ${route.routeColor}"></div>`
              : ''
          }
          <div class="w-8.5 h-8.5 rounded-lg border-2 flex items-center justify-center shadow-2xl transition-all"
               style="background-color: ${isRisk ? '#dc2626' : isWarning ? '#d97706' : route.routeColor}; border-color: ${isRisk ? '#facc15' : isSelected ? '#ffffff' : '#0f172a'};">
            <span class="material-symbols-outlined text-white text-base font-bold">
              ${isRisk ? 'warning' : 'local_shipping'}
            </span>
          </div>
          <div class="mt-1 whitespace-nowrap px-2 py-0.5 rounded-md text-[10px] font-mono font-bold border shadow-xl flex items-center gap-1 ${
            isRisk ? 'bg-[#7f1d1d] text-[#fef2f2] border-[#fca5a5]' : 'bg-[#0f172a] text-white border-slate-700'
          }">
            <span>${route.vehicleName}</span>
            ${isRisk ? '<span class="text-[#fef2f2] bg-[#dc2626] px-1 rounded text-[9px]">⚠️ RISK</span>' : ''}
          </div>
        </div>
      `;

      const vehicleIcon = L.divIcon({
        html: truckIconHtml,
        className: 'custom-moving-vehicle-icon',
        iconSize: [36, 48],
        iconAnchor: [18, 18],
      });

      const vehicleMarker = L.marker(currentCoord, {
        icon: vehicleIcon,
        zIndexOffset: isRisk ? 2000 : isSelected ? 1800 : 1200,
      }).addTo(layerGroup);

      vehicleMarker.on('click', (e) => {
        L.DomEvent.stopPropagation(e);
        handleSelectVehicle(route.vehicleId);
      });

      vehicleMarker.bindPopup(`
        <div class="p-1 font-sans">
          <div class="flex items-center justify-between gap-2 border-b border-[#424754]/40 pb-1 mb-1">
            <span class="font-bold text-sm text-[#adc6ff]">${route.vehicleName} (${route.vehicleCode})</span>
            <span class="text-[10px] font-bold px-1.5 py-0.5 rounded ${
              isRisk
                ? 'bg-[#93000a] text-[#ffdad6]'
                : isWarning
                ? 'bg-[#ca8100] text-[#ffb95f]'
                : 'bg-[#00a572]/20 text-[#4edea3]'
            }">
              ${isRisk ? '위험 (RISK)' : isWarning ? '경고' : '정상 운행'}
            </span>
          </div>
          <div class="text-xs text-[#c2c6d6]">담당 기사: <span class="text-white font-semibold">${route.driverName}</span></div>
          <div class="text-xs text-[#c2c6d6]">현재 구간: <span class="font-mono text-[#d4e4fa]">${vehicleState?.currentSegment || 'C03 ➔ C07'}</span></div>
          ${
            isRisk
              ? '<div class="text-xs text-[#ffb4ab] font-bold mt-1">🚨 돌발 정체 영향: +45분 지연 예상</div>'
              : ''
          }
        </div>
      `);
    });
  }, [
    nodes,
    effectiveTruckRoutes,
    vehicles,
    activeIncident,
    selectedVehicleId,
    simulatedTimeProgress,
    handleSelectVehicle,
    activeScenarioId,
    showPhysicalLayer,
    showBackboneNodes,
    showPhysicalDepots,
    showPhysicalCustomers,
    backboneEdges,
  ]);

  const handleZoomIn = () => leafletMapRef.current?.zoomIn();
  const handleZoomOut = () => leafletMapRef.current?.zoomOut();
  const handleResetLocation = () => leafletMapRef.current?.setView([centerLat, centerLng], 12);

  return (
    <div
      className={
        isFullscreen
          ? 'fixed inset-0 z-50 bg-[#061321] flex flex-col p-2'
          : 'w-full h-full relative overflow-hidden rounded-xl border border-[#424754]/30 shadow-2xl'
      }
    >
      {/* Map Element */}
      <div ref={mapContainerRef} className="w-full h-full z-0 cursor-default" />

      {/* Fullscreen Header Badge & Minimize [−] Button */}
      {isFullscreen ? (
        <>
          <div className="absolute top-4 left-1/2 -translate-x-1/2 z-30 glass-panel rounded-xl px-5 py-2.5 border border-[#4d8eff]/60 shadow-2xl bg-[#081829]/95 flex items-center gap-3 pointer-events-auto">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-[#4edea3] animate-ping" />
              <span className="text-xs font-bold text-[#d4e4fa] font-mono tracking-wide">
                FULLSCREEN MAP VIEW — 실시간 관제 모드
              </span>
            </div>
          </div>

          <div className="absolute top-4 right-4 z-30 pointer-events-auto flex items-center gap-2">
            <button
              type="button"
              onClick={() => setIsFullscreen(false)}
              className="px-3.5 py-2 bg-[#93000a]/80 hover:bg-[#93000a] text-[#ffdad6] rounded-xl text-xs font-bold border border-[#ffb4ab]/60 flex items-center gap-1.5 shadow-2xl transition-all active:scale-95"
              title="지도 축소"
            >
              <span className="material-symbols-outlined text-base">fullscreen_exit</span>
              <span>지도 축소 [−]</span>
            </button>
          </div>
        </>
      ) : (
        /* Normal Mode Top-Right Quick Expand Button */
        <div className="absolute top-4 right-16 z-20 pointer-events-auto">
          <button
            type="button"
            onClick={() => setIsFullscreen(true)}
            className="px-3 py-1.5 bg-[#081829]/90 hover:bg-[#122438] text-[#adc6ff] rounded-lg text-xs font-bold border border-[#4d8eff]/40 flex items-center gap-1.5 shadow-lg transition-all active:scale-95 hover:border-[#4d8eff]"
            title="지도 크게 보기"
          >
            <span className="material-symbols-outlined text-sm">fullscreen</span>
            <span>지도 크게 보기</span>
          </button>
        </div>
      )}

      {/* Floating Map Controls */}
      <div className="absolute right-4 top-14 z-20 flex flex-col gap-2 pointer-events-auto">
        <div className="glass-panel rounded-lg shadow-2xl border border-white/10">
          <button
            type="button"
            onClick={() => setIsFullscreen(!isFullscreen)}
            className={`p-2 transition-colors rounded-lg flex items-center justify-center ${
              isFullscreen
                ? 'text-[#ffb4ab] bg-[#93000a]/40'
                : 'text-[#c2c6d6] hover:text-[#adc6ff] hover:bg-white/10'
            }`}
            title={isFullscreen ? '지도 축소' : '지도 크게 보기'}
          >
            <span className="material-symbols-outlined text-[20px]">
              {isFullscreen ? 'fullscreen_exit' : 'fullscreen'}
            </span>
          </button>
        </div>

        <div className="glass-panel rounded-lg flex flex-col overflow-hidden shadow-2xl border border-white/10">
          <button
            type="button"
            onClick={handleZoomIn}
            className="p-2 text-[#c2c6d6] hover:text-[#adc6ff] hover:bg-white/10 transition-colors border-b border-white/10"
            title="Zoom In"
          >
            <span className="material-symbols-outlined text-[20px]">add</span>
          </button>
          <button
            type="button"
            onClick={handleZoomOut}
            className="p-2 text-[#c2c6d6] hover:text-[#adc6ff] hover:bg-white/10 transition-colors"
            title="Zoom Out"
          >
            <span className="material-symbols-outlined text-[20px]">remove</span>
          </button>
        </div>

        <div className="glass-panel rounded-lg shadow-2xl border border-white/10">
          <button
            type="button"
            onClick={handleResetLocation}
            className="p-2 text-[#c2c6d6] hover:text-[#adc6ff] hover:bg-white/10 transition-colors rounded-lg flex items-center justify-center"
            title="Recenter Map"
          >
            <span className="material-symbols-outlined text-[20px]">my_location</span>
          </button>
        </div>

        <div className="glass-panel rounded-lg shadow-2xl border border-white/10 relative">
          <button
            type="button"
            onClick={() => setIsLayerControlOpen(!isLayerControlOpen)}
            className={`p-2 transition-colors rounded-lg flex items-center justify-center ${
              showPhysicalLayer ? 'text-[#4d8eff] bg-[#4d8eff]/20' : 'text-[#c2c6d6]'
            }`}
            title="Physical Network Layers"
          >
            <span className="material-symbols-outlined text-[20px]">hub</span>
          </button>

          {/* Layer Flyout Menu */}
          {isLayerControlOpen && (
            <div className="absolute right-12 top-0 z-40 bg-[#081829]/95 border border-[#4d8eff]/50 rounded-xl p-3 shadow-2xl w-64 glass-panel text-xs space-y-2.5">
              <div className="flex items-center justify-between border-b border-[#424754]/40 pb-2">
                <span className="font-bold text-[#d4e4fa] flex items-center gap-1.5">
                  <span className="material-symbols-outlined text-sm text-[#4d8eff]">hub</span>
                  Physical Layer Control
                </span>
                <button
                  type="button"
                  onClick={() => setIsLayerControlOpen(false)}
                  className="text-[#8c909f] hover:text-white"
                >
                  ✕
                </button>
              </div>

              {/* Master Toggle */}
              <div className="flex items-center justify-between bg-[#122131] p-2 rounded-lg">
                <span className="font-semibold text-[#c2c6d6]">물리 네트워크 전체</span>
                <button
                  type="button"
                  onClick={() => setShowPhysicalLayer(!showPhysicalLayer)}
                  className={`w-9 h-4.5 rounded-full transition-colors relative flex items-center p-0.5 ${
                    showPhysicalLayer ? 'bg-[#4d8eff]' : 'bg-[#273647]'
                  }`}
                >
                  <div
                    className={`w-3.5 h-3.5 rounded-full bg-white transition-transform ${
                      showPhysicalLayer ? 'translate-x-4.5' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>

              {showPhysicalLayer && (
                <div className="space-y-1.5 pl-1">
                  {/* Road Backbone Toggle */}
                  <label className="flex items-center justify-between text-[11px] text-[#c2c6d6] cursor-pointer hover:text-white p-1 rounded hover:bg-white/5">
                    <span className="flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-[#7d8696]" />
                      도로 백본 노드 (200)
                    </span>
                    <input
                      type="checkbox"
                      checked={showBackboneNodes}
                      onChange={(e) => setShowBackboneNodes(e.target.checked)}
                      className="form-checkbox h-3.5 w-3.5 text-[#4d8eff] rounded border-[#424754] bg-[#122131]"
                    />
                  </label>

                  {/* Physical Depots Toggle */}
                  <label className="flex items-center justify-between text-[11px] text-[#c2c6d6] cursor-pointer hover:text-white p-1 rounded hover:bg-white/5">
                    <span className="flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded bg-[#00478d]" />
                      물리 차고지/Hub (5)
                    </span>
                    <input
                      type="checkbox"
                      checked={showPhysicalDepots}
                      onChange={(e) => setShowPhysicalDepots(e.target.checked)}
                      className="form-checkbox h-3.5 w-3.5 text-[#4d8eff] rounded border-[#424754] bg-[#122131]"
                    />
                  </label>

                  {/* Physical Customers Toggle */}
                  <label className="flex items-center justify-between text-[11px] text-[#c2c6d6] cursor-pointer hover:text-white p-1 rounded hover:bg-white/5">
                    <span className="flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-[#005236]" />
                      물리 고객 노드 (50)
                    </span>
                    <input
                      type="checkbox"
                      checked={showPhysicalCustomers}
                      onChange={(e) => setShowPhysicalCustomers(e.target.checked)}
                      className="form-checkbox h-3.5 w-3.5 text-[#4edea3] rounded border-[#424754] bg-[#122131]"
                    />
                  </label>
                </div>
              )}

              <div className="pt-2 border-t border-[#424754]/30 text-[10px] text-[#8c909f] font-mono leading-tight">
                ℹ️ Physical Layer network graph active. Structured Edge dataset required for routing optimization.
              </div>
            </div>
          )}
        </div>

        <div className="glass-panel rounded-lg shadow-2xl border border-white/10">
          <button
            type="button"
            onClick={() => setTrafficLayerEnabled(!trafficLayerEnabled)}
            className={`p-2 transition-colors rounded-lg flex items-center justify-center ${
              trafficLayerEnabled ? 'text-[#4edea3] bg-[#00a572]/20' : 'text-[#c2c6d6]'
            }`}
            title="Toggle Traffic Layer"
          >
            <span className="material-symbols-outlined text-[20px]">layers</span>
          </button>
        </div>
      </div>

      {/* Selected Vehicle Focus Status Banner or Incident Panel */}
      {selectedVehicleId === 'TRK-T02' && activeIncident && !activeIncident.resolved ? (
        <div className="absolute top-4 left-4 z-30 glass-panel rounded-2xl p-4 border border-[#ffb4ab]/60 shadow-2xl bg-[#081829]/95 max-w-sm pointer-events-auto flex flex-col gap-3">
          <div className="flex items-center justify-between pb-2.5 border-b border-[#ffb4ab]/30">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-[#ffdad6] bg-[#93000a] p-1.5 rounded-lg text-xl animate-pulse">
                car_crash
              </span>
              <div>
                <h4 className="text-sm font-bold text-[#ffdad6]">🚨 Incident Detected</h4>
                <p className="text-[10px] text-[#ffb4ab] font-mono">돌발 상황 및 위험 차량 감지</p>
              </div>
            </div>
            <span className="bg-[#93000a] text-[#ffdad6] text-[10px] font-bold px-2 py-0.5 rounded border border-[#ffb4ab]/40 uppercase tracking-wider">
              {activeIncident.severity.toUpperCase()}
            </span>
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex justify-between items-center bg-[#122131]/70 p-2 rounded-lg border border-[#424754]/30">
              <span className="text-[#8c909f]">대상 차량:</span>
              <span className="font-mono font-bold text-[#d4e4fa]">Truck T02 (TRK-T02)</span>
            </div>

            <div className="flex justify-between items-center bg-[#122131]/70 p-2 rounded-lg border border-[#424754]/30">
              <span className="text-[#8c909f]">위험 구간:</span>
              <span className="font-mono font-bold text-[#ffb95f]">{activeIncident.locationName}</span>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div className="bg-[#93000a]/20 p-2 rounded-lg border border-[#ffb4ab]/30">
                <div className="text-[10px] text-[#8c909f] font-bold">사고 유형</div>
                <div className="font-bold text-[#ffdad6] text-xs mt-0.5 flex items-center gap-1">
                  <span className="material-symbols-outlined text-sm text-[#ffb95f]">warning</span>
                  {activeIncident.type}
                </div>
              </div>
              <div className="bg-[#93000a]/20 p-2 rounded-lg border border-[#ffb4ab]/30">
                <div className="text-[10px] text-[#8c909f] font-bold">위험 지수</div>
                <div className="font-bold font-mono text-[#ffb4ab] text-sm mt-0.5">
                  {activeIncident.riskScore} (HIGH)
                </div>
              </div>
            </div>

            <div className="flex justify-between items-center bg-[#ca8100]/20 p-2 rounded-lg border border-[#ffb95f]/30">
              <span className="text-[#ffb95f] font-bold">예상 지연 시간:</span>
              <span className="font-mono font-bold text-[#ffdad6] text-sm">+45 min</span>
            </div>
          </div>

          {onOpenRerouteConsole && (
            <button
              type="button"
              onClick={onOpenRerouteConsole}
              className="w-full mt-1 bg-[#4d8eff] hover:bg-[#d8e2ff] text-[#00285d] py-2.5 px-4 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-2 shadow-lg shadow-[#4d8eff]/20 active:scale-95"
            >
              <span className="material-symbols-outlined text-base">psychology</span>
              View Re-routing Scenarios
            </button>
          )}
        </div>
      ) : selectedVehicleId ? (
        <div className="absolute top-4 left-4 z-20 glass-panel rounded-xl px-4 py-2 flex items-center gap-3 border border-[#4d8eff]/50 shadow-2xl bg-[#0a1827]/90 pointer-events-auto">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-[#4d8eff] text-sm animate-pulse">
              location_searching
            </span>
            <span className="text-xs font-bold text-[#d4e4fa]">
              경로 강조 상태:{' '}
              <span className="text-[#adc6ff]">
                {effectiveTruckRoutes.find((r) => r.vehicleId === selectedVehicleId)?.vehicleName ||
                  selectedVehicleId}
              </span>
            </span>
          </div>
          <button
            type="button"
            onClick={() => handleSelectVehicle(null)}
            className="text-[10px] font-bold text-[#c2c6d6] bg-white/10 hover:bg-white/20 px-2 py-1 rounded transition-colors"
          >
            전체 경로 보기
          </button>
        </div>
      ) : null}

      {/* Bottom Simulation Control Bar */}
      <div className="absolute bottom-4 left-4 right-4 z-20 glass-panel rounded-xl px-5 py-3 border border-[#424754]/50 shadow-2xl bg-[#091726]/90 flex flex-col md:flex-row items-center gap-4 pointer-events-auto">
        {/* Play / Pause Controls */}
        <div className="flex items-center gap-3 flex-shrink-0">
          <button
            type="button"
            onClick={handleTogglePlay}
            className={`w-10 h-10 rounded-full flex items-center justify-center transition-all shadow-lg active:scale-95 ${
              isPlaying
                ? 'bg-[#ffb95f] text-[#001f3f] shadow-[#ffb95f]/30'
                : 'bg-[#4d8eff] text-[#00285d] shadow-[#4d8eff]/30 hover:bg-[#d8e2ff]'
            }`}
            title={isPlaying ? '시뮬레이션 일시정지' : '시뮬레이션 시작'}
          >
            <span className="material-symbols-outlined text-xl">
              {isPlaying ? 'pause' : 'play_arrow'}
            </span>
          </button>

          <div>
            <div className="text-[10px] font-bold uppercase tracking-wider text-[#8c909f]">
              실시간 운행 시뮬레이션
            </div>
            <div className="text-sm font-bold text-[#d4e4fa] font-mono flex items-center gap-1.5">
              <span>{formatSimulatedTime(simulatedTimeProgress)}</span>
              {isPlaying && (
                <span className="inline-block w-2 h-2 rounded-full bg-[#4edea3] animate-ping" />
              )}
            </div>
          </div>
        </div>

        {/* Timeline Slider */}
        <div className="flex-1 w-full flex flex-col justify-center px-2">
          <input
            type="range"
            min="0"
            max="1"
            step="0.001"
            value={simulatedTimeProgress}
            onChange={(e) => handleTimeProgressChange(Number(e.target.value))}
            className="w-full cursor-pointer accent-[#4d8eff]"
          />
          <div className="flex justify-between text-[10px] text-[#8c909f] font-mono mt-1">
            <span>09:00 AM</span>
            <span>11:00 AM</span>
            <span>01:00 PM</span>
            <span>03:00 PM</span>
            <span>05:00 PM</span>
          </div>
        </div>

        {/* Speed Toggles */}
        <div className="flex items-center gap-1.5 flex-shrink-0 bg-[#122131] p-1 rounded-lg border border-[#424754]/40">
          <span className="text-[10px] font-bold text-[#8c909f] px-1.5 uppercase">배속</span>
          {([1, 2, 5] as const).map((spd) => (
            <button
              key={spd}
              type="button"
              onClick={() => handleChangeSpeed(spd)}
              className={`px-2 py-0.5 rounded text-xs font-mono font-bold transition-all ${
                speedMultiplier === spd
                  ? 'bg-[#4d8eff] text-[#00285d] shadow-sm'
                  : 'text-[#c2c6d6] hover:bg-white/10'
              }`}
            >
              {spd}x
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
