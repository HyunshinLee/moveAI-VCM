import React from 'react';
import { RouteNode, FleetVehicle, IncidentAlert, ScenarioOptionId, PlannedTruckRoute } from '../types';
import { RoutePlanningMap } from './RoutePlanningMap';

export interface InteractiveMapProps {
  nodes: RouteNode[];
  vehicles: FleetVehicle[];
  activeIncident?: IncidentAlert | null;
  selectedVehicleId?: string | null;
  onSelectVehicle?: (vehicleId: string | null) => void;
  onOpenRerouteConsole?: () => void;
  showRiskOverlay?: boolean;
  activeScenarioId?: string | null;
  truckRoutes?: PlannedTruckRoute[];
}

/**
 * InteractiveMap component now delegates directly to RoutePlanningMap.
 * This guarantees that DashboardPage, InitialRoutePage, and ReroutePage share
 * the exact same basemap tile layer (CartoDB Voyager), node styling, road network,
 * vehicle markers, and incident overlays.
 */
export const InteractiveMap: React.FC<InteractiveMapProps> = ({
  nodes,
  vehicles,
  activeIncident,
  selectedVehicleId = null,
  onSelectVehicle,
  onOpenRerouteConsole,
  activeScenarioId,
  truckRoutes,
}) => {
  return (
    <RoutePlanningMap
      nodes={nodes}
      vehicles={vehicles}
      activeIncident={activeIncident}
      selectedVehicleId={selectedVehicleId}
      onSelectVehicle={onSelectVehicle}
      onOpenRerouteConsole={onOpenRerouteConsole}
      activeScenarioId={activeScenarioId as ScenarioOptionId | null}
      truckRoutes={truckRoutes}
    />
  );
};
