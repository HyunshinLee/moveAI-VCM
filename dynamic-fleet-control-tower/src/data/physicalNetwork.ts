export interface PhysicalNode {
  id: string; // e.g. "R001", "D01", "C001"
  type: 'road_backbone' | 'depot' | 'customer';
  name: string;
  latitude: number;
  longitude: number;
  x?: number;
  y?: number;
  role?: string;
  nearestBackboneNode?: string;
  nearestBackboneDistanceKm?: number;
  connectorBackboneNodes?: string[];
}

export interface PhysicalEdge {
  id: string;
  source: string;
  target: string;
  distanceKm: number;
  travelTimeMin: number;
  roadType?: string;
  speedLimit?: number;
}

export interface PhysicalNetwork {
  nodes: PhysicalNode[];
  edges: PhysicalEdge[];
  statusMessage?: string;
}

// 1. Road Backbone Nodes (R001 - R200)
export const ROAD_BACKBONE_NODES: PhysicalNode[] = [
  { id: 'R001', type: 'road_backbone', name: '점촌함창IC', latitude: 36.587439, longitude: 128.15661, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R001', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R001'] },
  { id: 'R002', type: 'road_backbone', name: '문경새재IC', latitude: 36.697932, longitude: 128.111228, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R002', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R002'] },
  { id: 'R003', type: 'road_backbone', name: '점촌함창IC', latitude: 36.583825, longitude: 128.152303, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R003', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R003'] },
  { id: 'R004', type: 'road_backbone', name: '북상주IC', latitude: 36.53258, longitude: 128.167499, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R004', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R004'] },
  { id: 'R005', type: 'road_backbone', name: '남이JC', latitude: 36.593109, longitude: 127.424279, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R005', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R005'] },
  { id: 'R006', type: 'road_backbone', name: '일죽IC삼거리', latitude: 37.086409, longitude: 127.450854, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R006', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R006'] },
  { id: 'R007', type: 'road_backbone', name: '김천IC앞', latitude: 36.127732, longitude: 128.094852, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R007', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R007'] },
  { id: 'R008', type: 'road_backbone', name: '낙동Jct', latitude: 36.37286, longitude: 128.239475, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R008', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R008'] },
  { id: 'R009', type: 'road_backbone', name: '익산IC(남측)', latitude: 35.98816, longitude: 127.113793, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R009', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R009'] },
  { id: 'R010', type: 'road_backbone', name: '추풍령IC(남측)', latitude: 36.197006, longitude: 128.00201, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R010', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R010'] },
  { id: 'R011', type: 'road_backbone', name: '김천IC(남측)', latitude: 36.131952, longitude: 128.094697, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R011', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R011'] },
  { id: 'R012', type: 'road_backbone', name: '청주JC', latitude: 36.570234, longitude: 127.428856, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R012', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R012'] },
  { id: 'R013', type: 'road_backbone', name: '적석교차로', latitude: 36.758478, longitude: 127.984643, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R013', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R013'] },
  { id: 'R014', type: 'road_backbone', name: '검승교차로', latitude: 36.801985, longitude: 127.829865, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R014', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R014'] },
  { id: 'R015', type: 'road_backbone', name: '쌍곡2교차로', latitude: 36.780527, longitude: 127.902693, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R015', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R015'] },
  { id: 'R016', type: 'road_backbone', name: '안성JC(북측)', latitude: 37.044566, longitude: 127.137117, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R016', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R016'] },
  { id: 'R017', type: 'road_backbone', name: '동군위IC', latitude: 36.095711, longitude: 128.663058, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R017', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R017'] },
  { id: 'R018', type: 'road_backbone', name: '낙동JC', latitude: 36.367407, longitude: 128.246437, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R018', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R018'] },
  { id: 'R019', type: 'road_backbone', name: '상주IC', latitude: 36.42004, longitude: 128.214304, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R019', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R019'] },
  { id: 'R020', type: 'road_backbone', name: '상주IC', latitude: 36.425416, longitude: 128.21309, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R020', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R020'] },
  { id: 'R021', type: 'road_backbone', name: '북상주IC', latitude: 36.528541, longitude: 128.171853, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R021', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R021'] },
  { id: 'R022', type: 'road_backbone', name: '익산JC', latitude: 35.950296, longitude: 127.097094, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R022', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R022'] },
  { id: 'R023', type: 'road_backbone', name: '음성IC교차로', latitude: 36.98515, longitude: 127.618384, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R023', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R023'] },
  { id: 'R024', type: 'road_backbone', name: '안성IC(북측)', latitude: 36.996815, longitude: 127.153349, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R024', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R024'] },
  { id: 'R025', type: 'road_backbone', name: '안성JC(남측)', latitude: 37.026256, longitude: 127.141553, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R025', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R025'] },
  { id: 'R026', type: 'road_backbone', name: '도동JC', latitude: 35.91453, longitude: 128.656286, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R026', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R026'] },
  { id: 'R027', type: 'road_backbone', name: '문경새재IC', latitude: 36.701292, longitude: 128.114697, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R027', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R027'] },
  { id: 'R028', type: 'road_backbone', name: '신녕IC교차로', latitude: 36.037132, longitude: 128.812267, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R028', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R028'] },
  { id: 'R029', type: 'road_backbone', name: '천안IC', latitude: 36.824682, longitude: 127.167477, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R029', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R029'] },
  { id: 'R030', type: 'road_backbone', name: '신녕IC교차로', latitude: 36.037146, longitude: 128.812399, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R030', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R030'] },
  { id: 'R031', type: 'road_backbone', name: '신녕IC', latitude: 36.041004, longitude: 128.810419, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R031', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R031'] },
  { id: 'R032', type: 'road_backbone', name: '고령JC', latitude: 35.760456, longitude: 128.371504, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R032', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R032'] },
  { id: 'R033', type: 'road_backbone', name: '영동IC(남측)', latitude: 36.267436, longitude: 127.835667, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R033', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R033'] },
  { id: 'R034', type: 'road_backbone', name: '황간IC', latitude: 36.22184, longitude: 127.905717, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R034', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R034'] },
  { id: 'R035', type: 'road_backbone', name: '황간IC(동측)', latitude: 36.222414, longitude: 127.912068, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R035', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R035'] },
  { id: 'R036', type: 'road_backbone', name: '추풍령IC(북측)', latitude: 36.204067, longitude: 128.001134, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R036', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R036'] },
  { id: 'R037', type: 'road_backbone', name: '김천IC(서측)', latitude: 36.133906, longitude: 128.091948, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R037', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R037'] },
  { id: 'R038', type: 'road_backbone', name: '김천IC앞', latitude: 36.127772, longitude: 128.094977, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R038', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R038'] },
  { id: 'R039', type: 'road_backbone', name: '현풍JC', latitude: 35.668075, longitude: 128.435697, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R039', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R039'] },
  { id: 'R040', type: 'road_backbone', name: '죽산교차로', latitude: 37.080881, longitude: 127.434929, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R040', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R040'] },
  { id: 'R041', type: 'road_backbone', name: '연풍IC교차로', latitude: 36.757269, longitude: 127.99892, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R041', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R041'] },
  { id: 'R042', type: 'road_backbone', name: '적석교차로', latitude: 36.758855, longitude: 127.977198, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R042', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R042'] },
  { id: 'R043', type: 'road_backbone', name: '동진교차로', latitude: 36.809367, longitude: 127.812272, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R043', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R043'] },
  { id: 'R044', type: 'road_backbone', name: '검승교차로', latitude: 36.803534, longitude: 127.825469, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R044', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R044'] },
  { id: 'R045', type: 'road_backbone', name: '칠성교차로', latitude: 36.790607, longitude: 127.854046, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R045', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R045'] },
  { id: 'R046', type: 'road_backbone', name: '동진교차로', latitude: 36.809384, longitude: 127.812146, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R046', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R046'] },
  { id: 'R047', type: 'road_backbone', name: '칠성교차로', latitude: 36.792442, longitude: 127.84813, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R047', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R047'] },
  { id: 'R048', type: 'road_backbone', name: '쌍곡1교차로', latitude: 36.781776, longitude: 127.882097, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R048', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R048'] },
  { id: 'R049', type: 'road_backbone', name: '논산JC', latitude: 36.076008, longitude: 127.101804, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R049', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R049'] },
  { id: 'R050', type: 'road_backbone', name: '익산IC(북측)', latitude: 35.994484, longitude: 127.113313, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R050', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R050'] },
  { id: 'R051', type: 'road_backbone', name: '신녕IC', latitude: 36.043689, longitude: 128.807889, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R051', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R051'] },
  { id: 'R052', type: 'road_backbone', name: '상주JC', latitude: 36.375245, longitude: 128.269237, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R052', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R052'] },
  { id: 'R053', type: 'road_backbone', name: '성서IC', latitude: 35.85332, longitude: 128.52224, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R053', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R053'] },
  { id: 'R054', type: 'road_backbone', name: '천안IC', latitude: 36.831178, longitude: 127.172535, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R054', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R054'] },
  { id: 'R055', type: 'road_backbone', name: '북천안IC', latitude: 36.895281, longitude: 127.189275, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R055', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R055'] },
  { id: 'R056', type: 'road_backbone', name: '북천안IC', latitude: 36.900071, longitude: 127.189241, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R056', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R056'] },
  { id: 'R057', type: 'road_backbone', name: '안성IC(남측)', latitude: 36.991658, longitude: 127.155325, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R057', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R057'] },
  { id: 'R058', type: 'road_backbone', name: '공주분기점', latitude: 36.481154, longitude: 127.08943, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R058', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R058'] },
  { id: 'R059', type: 'road_backbone', name: '공주IC', latitude: 36.5031, longitude: 127.104068, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R059', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R059'] },
  { id: 'R060', type: 'road_backbone', name: '남대구IC', latitude: 35.83797, longitude: 128.52784, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R060', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R060'] },
  { id: 'R061', type: 'road_backbone', name: '성서IC', latitude: 35.845167, longitude: 128.524906, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R061', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R061'] },
  { id: 'R062', type: 'road_backbone', name: '유천IC(남측)', latitude: 35.811905, longitude: 128.502586, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R062', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R062'] },
  { id: 'R063', type: 'road_backbone', name: '남풍세IC', latitude: 36.721446, longitude: 127.137774, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R063', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R063'] },
  { id: 'R064', type: 'road_backbone', name: '정안IC', latitude: 36.627904, longitude: 127.120473, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R064', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R064'] },
  { id: 'R065', type: 'road_backbone', name: '도개IC', latitude: 36.315907, longitude: 128.320429, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R065', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R065'] },
  { id: 'R066', type: 'road_backbone', name: '진천IC', latitude: 36.866514, longitude: 127.475538, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R066', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R066'] },
  { id: 'R067', type: 'road_backbone', name: '신녕IC교차로', latitude: 36.037223, longitude: 128.815594, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R067', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R067'] },
  { id: 'R068', type: 'road_backbone', name: '익산JC', latitude: 35.939474, longitude: 127.084151, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R068', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R068'] },
  { id: 'R069', type: 'road_backbone', name: '삼례IC(남측)', latitude: 35.923337, longitude: 127.077669, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R069', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R069'] },
  { id: 'R070', type: 'road_backbone', name: '공주분기점', latitude: 36.481105, longitude: 127.089573, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R070', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R070'] },
  { id: 'R071', type: 'road_backbone', name: '서군위하이패스IC', latitude: 36.247479, longitude: 128.477973, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R071', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R071'] },
  { id: 'R072', type: 'road_backbone', name: '남공주IC', latitude: 36.42917, longitude: 127.079785, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R072', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R072'] },
  { id: 'R073', type: 'road_backbone', name: '동군위IC', latitude: 36.099348, longitude: 128.659001, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R073', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R073'] },
  { id: 'R074', type: 'road_backbone', name: '천안IC', latitude: 36.824537, longitude: 127.167852, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R074', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R074'] },
  { id: 'R075', type: 'road_backbone', name: '남이JC', latitude: 36.59319, longitude: 127.424412, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R075', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R075'] },
  { id: 'R076', type: 'road_backbone', name: '청주JC', latitude: 36.570282, longitude: 127.429003, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R076', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R076'] },
  { id: 'R077', type: 'road_backbone', name: '음성IC교차로', latitude: 36.979448, longitude: 127.622096, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R077', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R077'] },
  { id: 'R078', type: 'road_backbone', name: '일죽IC삼거리', latitude: 37.086333, longitude: 127.450988, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R078', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R078'] },
  { id: 'R079', type: 'road_backbone', name: '일죽IC삼거리', latitude: 37.086298, longitude: 127.450883, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R079', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R079'] },
  { id: 'R080', type: 'road_backbone', name: '천안JC', latitude: 36.774984, longitude: 127.177491, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R080', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R080'] },
  { id: 'R081', type: 'road_backbone', name: '창녕IC', latitude: 35.546297, longitude: 128.47604, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R081', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R081'] },
  { id: 'R082', type: 'road_backbone', name: '창녕IC(북측)', latitude: 35.544738, longitude: 128.476314, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R082', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R082'] },
  { id: 'R083', type: 'road_backbone', name: '군산IC(북측)', latitude: 36.012351, longitude: 126.798077, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R083', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R083'] },
  { id: 'R084', type: 'road_backbone', name: '익산IC(북측)', latitude: 35.994504, longitude: 127.113519, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R084', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R084'] },
  { id: 'R085', type: 'road_backbone', name: '판교JC(남측)', latitude: 37.402283, longitude: 127.09841, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R085', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R085'] },
  { id: 'R086', type: 'road_backbone', name: '동군위IC', latitude: 36.097364, longitude: 128.660682, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R086', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R086'] },
  { id: 'R087', type: 'road_backbone', name: '오창IC', latitude: 36.713655, longitude: 127.441747, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R087', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R087'] },
  { id: 'R088', type: 'road_backbone', name: '남천안IC', latitude: 36.750882, longitude: 127.164304, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R088', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R088'] },
  { id: 'R089', type: 'road_backbone', name: '음성１교차로', latitude: 36.913633, longitude: 127.692654, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R089', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R089'] },
  { id: 'R090', type: 'road_backbone', name: '청주IC', latitude: 36.624789, longitude: 127.383884, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R090', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R090'] },
  { id: 'R091', type: 'road_backbone', name: '대동IC', latitude: 35.253834, longitude: 128.983505, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R091', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R091'] },
  { id: 'R092', type: 'road_backbone', name: '안성JC(북측)', latitude: 37.044547, longitude: 127.136893, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R092', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R092'] },
  { id: 'R093', type: 'road_backbone', name: '목천IC', latitude: 36.758437, longitude: 127.218521, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R093', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R093'] },
  { id: 'R094', type: 'road_backbone', name: '고령JC', latitude: 35.75506, longitude: 128.374168, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R094', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R094'] },
  { id: 'R095', type: 'road_backbone', name: '현풍JC', latitude: 35.679848, longitude: 128.432434, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R095', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R095'] },
  { id: 'R096', type: 'road_backbone', name: '문의IC', latitude: 36.528473, longitude: 127.510537, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R096', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R096'] },
  { id: 'R097', type: 'road_backbone', name: '창녕IC사거리', latitude: 35.539264, longitude: 128.47932, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R097', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R097'] },
  { id: 'R098', type: 'road_backbone', name: '북천안IC', latitude: 36.895279, longitude: 127.189062, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R098', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R098'] },
  { id: 'R099', type: 'road_backbone', name: '상용사거리', latitude: 36.270949, longitude: 127.825089, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R099', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R099'] },
  { id: 'R100', type: 'road_backbone', name: '상용사거리', latitude: 36.271037, longitude: 127.825025, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R100', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R100'] },
  { id: 'R101', type: 'road_backbone', name: '안성IC(남측)', latitude: 36.9916, longitude: 127.155112, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R101', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R101'] },
  { id: 'R102', type: 'road_backbone', name: '서대구IC', latitude: 35.873677, longitude: 128.531537, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R102', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R102'] },
  { id: 'R103', type: 'road_backbone', name: '북대구IC', latitude: 35.909571, longitude: 128.583046, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R103', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R103'] },
  { id: 'R104', type: 'road_backbone', name: '정안IC', latitude: 36.62181, longitude: 127.120408, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R104', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R104'] },
  { id: 'R105', type: 'road_backbone', name: '공주JC', latitude: 36.489516, longitude: 127.093935, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R105', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R105'] },
  { id: 'R106', type: 'road_backbone', name: '남청주IC', latitude: 36.537146, longitude: 127.430794, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R106', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R106'] },
  { id: 'R107', type: 'road_backbone', name: '남대구IC', latitude: 35.836119, longitude: 128.527182, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R107', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R107'] },
  { id: 'R108', type: 'road_backbone', name: '서논산IC', latitude: 36.221995, longitude: 127.052121, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R108', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R108'] },
  { id: 'R109', type: 'road_backbone', name: '성주IC', latitude: 35.922897, longitude: 128.245822, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R109', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R109'] },
  { id: 'R110', type: 'road_backbone', name: '이서JC', latitude: 35.807953, longitude: 127.026106, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R110', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R110'] },
  { id: 'R111', type: 'road_backbone', name: '군위JC', latitude: 36.161391, longitude: 128.565482, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R111', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R111'] },
  { id: 'R112', type: 'road_backbone', name: '함양JCT1교', latitude: 35.537444, longitude: 127.768367, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R112', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R112'] },
  { id: 'R113', type: 'road_backbone', name: '양지IC(서측)', latitude: 37.239104, longitude: 127.290934, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R113', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R113'] },
  { id: 'R114', type: 'road_backbone', name: '남제천IC(북측)', latitude: 37.077178, longitude: 128.180614, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R114', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R114'] },
  { id: 'R115', type: 'road_backbone', name: '팔탄JC', latitude: 37.190793, longitude: 126.872071, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R115', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R115'] },
  { id: 'R116', type: 'road_backbone', name: '북양주IC교차로', latitude: 37.856158, longitude: 127.053985, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R116', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R116'] },
  { id: 'R117', type: 'road_backbone', name: '동충주교차로', latitude: 37.06753, longitude: 127.930701, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R117', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R117'] },
  { id: 'R118', type: 'road_backbone', name: '군산IC(남측)', latitude: 36.005315, longitude: 126.801977, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R118', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R118'] },
  { id: 'R119', type: 'road_backbone', name: '남원IC(동측)', latitude: 35.432862, longitude: 127.402124, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R119', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R119'] },
  { id: 'R120', type: 'road_backbone', name: '대동IC교차로', latitude: 35.252204, longitude: 128.981964, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R120', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R120'] },
  { id: 'R121', type: 'road_backbone', name: '보은IC', latitude: 36.457432, longitude: 127.715952, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R121', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R121'] },
  { id: 'R122', type: 'road_backbone', name: '장성JC', latitude: 35.333435, longitude: 126.808339, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R122', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R122'] },
  { id: 'R123', type: 'road_backbone', name: '청송IC', latitude: 36.455074, longitude: 129.023435, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R123', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R123'] },
  { id: 'R124', type: 'road_backbone', name: '대덕밸리IC', latitude: 36.410729, longitude: 127.380192, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R124', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R124'] },
  { id: 'R125', type: 'road_backbone', name: '일직JC', latitude: 37.428216, longitude: 126.895823, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R125', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R125'] },
  { id: 'R126', type: 'road_backbone', name: '남원JC', latitude: 35.404306, longitude: 127.302796, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R126', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R126'] },
  { id: 'R127', type: 'road_backbone', name: '지리산IC(동측)', latitude: 35.485175, longitude: 127.591215, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R127', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R127'] },
  { id: 'R128', type: 'road_backbone', name: '서평택IC(남측)', latitude: 36.995694, longitude: 126.869217, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R128', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R128'] },
  { id: 'R129', type: 'road_backbone', name: '금산IC', latitude: 36.106899, longitude: 127.516459, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R129', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R129'] },
  { id: 'R130', type: 'road_backbone', name: '생초IC', latitude: 35.483539, longitude: 127.821851, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R130', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R130'] },
  { id: 'R131', type: 'road_backbone', name: '함안IC', latitude: 35.289398, longitude: 128.387463, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R131', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R131'] },
  { id: 'R132', type: 'road_backbone', name: '덕유산IC', latitude: 35.844276, longitude: 127.646532, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R132', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R132'] },
  { id: 'R133', type: 'road_backbone', name: '가조IC(서측)', latitude: 35.703068, longitude: 128.024454, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R133', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R133'] },
  { id: 'R134', type: 'road_backbone', name: '부안IC(북측)', latitude: 35.72874, longitude: 126.771108, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R134', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R134'] },
  { id: 'R135', type: 'road_backbone', name: '서진주IC', latitude: 35.185236, longitude: 128.040528, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R135', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R135'] },
  { id: 'R136', type: 'road_backbone', name: '진주JC', latitude: 35.139903, longitude: 128.092783, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R136', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R136'] },
  { id: 'R137', type: 'road_backbone', name: '가작교차로', latitude: 35.28125, longitude: 126.792533, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R137', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R137'] },
  { id: 'R138', type: 'road_backbone', name: '해인사IC(동측)', latitude: 35.696355, longitude: 128.190459, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R138', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R138'] },
  { id: 'R139', type: 'road_backbone', name: '순천JC', latitude: 34.995451, longitude: 127.532972, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R139', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R139'] },
  { id: 'R140', type: 'road_backbone', name: '풍기IC앞교차로', latitude: 36.848405, longitude: 128.527058, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R140', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R140'] },
  { id: 'R141', type: 'road_backbone', name: '김포IC', latitude: 37.595305, longitude: 126.779068, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R141', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R141'] },
  { id: 'R142', type: 'road_backbone', name: '황전IC', latitude: 35.148268, longitude: 127.455983, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R142', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R142'] },
  { id: 'R143', type: 'road_backbone', name: '여주JC(남측)', latitude: 37.227009, longitude: 127.592149, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R143', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R143'] },
  { id: 'R144', type: 'road_backbone', name: '청도IC', latitude: 35.654554, longitude: 128.746566, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R144', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R144'] },
  { id: 'R145', type: 'road_backbone', name: '만종JC', latitude: 37.369336, longitude: 127.899063, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R145', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R145'] },
  { id: 'R146', type: 'road_backbone', name: '홍천IC', latitude: 37.670914, longitude: 127.852552, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R146', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R146'] },
  { id: 'R147', type: 'road_backbone', name: '서산IC앞', latitude: 36.812925, longitude: 126.56945, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R147', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R147'] },
  { id: 'R148', type: 'road_backbone', name: '안동JC', latitude: 36.42705, longitude: 128.618554, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R148', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R148'] },
  { id: 'R149', type: 'road_backbone', name: '남밀양IC', latitude: 35.454226, longitude: 128.773087, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R149', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R149'] },
  { id: 'R150', type: 'road_backbone', name: '주암IC입구', latitude: 35.064406, longitude: 127.264564, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R150', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R150'] },
  { id: 'R151', type: 'road_backbone', name: '동광양IC(동측)', latitude: 34.97142, longitude: 127.661777, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R151', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R151'] },
  { id: 'R152', type: 'road_backbone', name: '담양JC', latitude: 35.248427, longitude: 126.969593, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R152', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R152'] },
  { id: 'R153', type: 'road_backbone', name: '하동IC', latitude: 35.000615, longitude: 127.811344, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R153', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R153'] },
  { id: 'R154', type: 'road_backbone', name: '동안동IC', latitude: 36.436815, longitude: 128.890786, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R154', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R154'] },
  { id: 'R155', type: 'road_backbone', name: '옥천IC', latitude: 36.310669, longitude: 127.570009, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R155', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R155'] },
  { id: 'R156', type: 'road_backbone', name: '청량IC교차로', latitude: 35.479585, longitude: 129.290143, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R156', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R156'] },
  { id: 'R157', type: 'road_backbone', name: '장유IC(서측)', latitude: 35.195402, longitude: 128.805541, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R157', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R157'] },
  { id: 'R158', type: 'road_backbone', name: '동양평IC', latitude: 37.399426, longitude: 127.756394, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R158', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R158'] },
  { id: 'R159', type: 'road_backbone', name: '무주IC', latitude: 35.975809, longitude: 127.647552, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R159', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R159'] },
  { id: 'R160', type: 'road_backbone', name: '문덕교차로램프', latitude: 35.9455, longitude: 129.39337, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R160', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R160'] },
  { id: 'R161', type: 'road_backbone', name: '남이천IC(북측)', latitude: 37.187474, longitude: 127.441587, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R161', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R161'] },
  { id: 'R162', type: 'road_backbone', name: '서포항IC입구', latitude: 36.065125, longitude: 129.224423, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R162', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R162'] },
  { id: 'R163', type: 'road_backbone', name: '영덕IC', latitude: 36.388242, longitude: 129.369332, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R163', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R163'] },
  { id: 'R164', type: 'road_backbone', name: '화서IC앞', latitude: 36.445442, longitude: 127.955881, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R164', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R164'] },
  { id: 'R165', type: 'road_backbone', name: '서부여IC', latitude: 36.237578, longitude: 126.788904, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R165', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R165'] },
  { id: 'R166', type: 'road_backbone', name: '대강교차로', latitude: 36.919151, longitude: 128.371617, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R166', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R166'] },
  { id: 'R167', type: 'road_backbone', name: '신림IC앞', latitude: 37.235964, longitude: 128.086245, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R167', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R167'] },
  { id: 'R168', type: 'road_backbone', name: '함평JC', latitude: 35.025612, longitude: 126.487163, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R168', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R168'] },
  { id: 'R169', type: 'road_backbone', name: '속사IC앞', latitude: 37.636479, longitude: 128.494188, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R169', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R169'] },
  { id: 'R170', type: 'road_backbone', name: '벌교IC', latitude: 34.839647, longitude: 127.301454, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R170', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R170'] },
  { id: 'R171', type: 'road_backbone', name: '정읍IC(남측)', latitude: 35.578286, longitude: 126.83199, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R171', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R171'] },
  { id: 'R172', type: 'road_backbone', name: '남안동IC', latitude: 36.473567, longitude: 128.622002, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R172', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R172'] },
  { id: 'R173', type: 'road_backbone', name: '현충교차로', latitude: 36.796078, longitude: 127.044832, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R173', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R173'] },
  { id: 'R174', type: 'road_backbone', name: '예천IC', latitude: 36.669632, longitude: 128.543584, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R174', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R174'] },
  { id: 'R175', type: 'road_backbone', name: '일로IC앞', latitude: 34.861434, longitude: 126.47955, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R175', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R175'] },
  { id: 'R176', type: 'road_backbone', name: '문평IC교차로', latitude: 35.064856, longitude: 126.599602, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R176', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R176'] },
  { id: 'R177', type: 'road_backbone', name: '내포IC', latitude: 37.852706, longitude: 126.765476, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R177', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R177'] },
  { id: 'R178', type: 'road_backbone', name: '춘천IC입구(남측)', latitude: 37.841651, longitude: 127.765395, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R178', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R178'] },
  { id: 'R179', type: 'road_backbone', name: '공항신도시JC도윽', latitude: 37.48221, longitude: 126.494065, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R179', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R179'] },
  { id: 'R180', type: 'road_backbone', name: '임고하이패스IC(서측)', latitude: 36.054904, longitude: 129.004391, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R180', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R180'] },
  { id: 'R181', type: 'road_backbone', name: '서마산IC', latitude: 35.235922, longitude: 128.564305, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R181', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R181'] },
  { id: 'R182', type: 'road_backbone', name: '진안IC', latitude: 35.771584, longitude: 127.446508, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R182', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R182'] },
  { id: 'R183', type: 'road_backbone', name: '동청송영양IC교차로', latitude: 36.502692, longitude: 129.122112, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R183', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R183'] },
  { id: 'R184', type: 'road_backbone', name: '문수IC교차로', latitude: 35.51219, longitude: 129.236796, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R184', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R184'] },
  { id: 'R185', type: 'road_backbone', name: '달뫼IC', latitude: 37.660314, longitude: 127.329068, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R185', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R185'] },
  { id: 'R186', type: 'road_backbone', name: '원거교차로', latitude: 37.909459, longitude: 128.046219, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R186', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R186'] },
  { id: 'R187', type: 'road_backbone', name: '유목교차로', latitude: 37.979639, longitude: 128.093129, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R187', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R187'] },
  { id: 'R188', type: 'road_backbone', name: '예산예당호휴게소하이패스IC', latitude: 36.626643, longitude: 126.780613, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R188', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R188'] },
  { id: 'R189', type: 'road_backbone', name: '오수IC', latitude: 35.551785, longitude: 127.319847, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R189', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R189'] },
  { id: 'R190', type: 'road_backbone', name: '서원주IC', latitude: 37.394774, longitude: 127.865052, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R190', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R190'] },
  { id: 'R191', type: 'road_backbone', name: '방흥교차로', latitude: 36.461894, longitude: 127.047865, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R191', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R191'] },
  { id: 'R192', type: 'road_backbone', name: '강릉JC', latitude: 37.764191, longitude: 128.837041, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R192', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R192'] },
  { id: 'R193', type: 'road_backbone', name: '양평IC', latitude: 37.523253, longitude: 127.444607, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R193', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R193'] },
  { id: 'R194', type: 'road_backbone', name: '포천IC교차로', latitude: 37.883762, longitude: 127.211504, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R194', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R194'] },
  { id: 'R195', type: 'road_backbone', name: '양양JC', latitude: 38.063867, longitude: 128.605167, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R195', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R195'] },
  { id: 'R196', type: 'road_backbone', name: '북양양IC', latitude: 38.152373, longitude: 128.585308, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R196', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R196'] },
  { id: 'R197', type: 'road_backbone', name: '월곶JC(남측)', latitude: 37.383609, longitude: 126.76072, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R197', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R197'] },
  { id: 'R198', type: 'road_backbone', name: '영천JC', latitude: 35.917105, longitude: 129.006623, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R198', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R198'] },
  { id: 'R199', type: 'road_backbone', name: '통일로IC', latitude: 37.673712, longitude: 126.890505, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R199', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R199'] },
  { id: 'R200', type: 'road_backbone', name: '새말IC앞', latitude: 37.4514, longitude: 128.072676, role: 'anchor|named_interchange_or_intersection', nearestBackboneNode: 'R200', nearestBackboneDistanceKm: 0.0, connectorBackboneNodes: ['R200'] },
];

// 2. Depot Nodes (D01 - D05)
export const DEPOT_NODES: PhysicalNode[] = [
  { id: 'D01', type: 'depot', name: '인천 산업재 물류센터', latitude: 37.489623, longitude: 126.649354, x: 168989.65, y: 543410.15, role: '수도권 Depot', nearestBackboneNode: 'R179', nearestBackboneDistanceKm: 17.158134, connectorBackboneNodes: ['R179', 'R197', 'R141'] },
  { id: 'D02', type: 'depot', name: '당진 산업재 물류센터', latitude: 36.973697, longitude: 126.698506, x: 173154.26, y: 486136.45, role: '충청권 Depot', nearestBackboneNode: 'R128', nearestBackboneDistanceKm: 19.198614, connectorBackboneNodes: ['R128', 'R147', 'R115'] },
  { id: 'D03', type: 'depot', name: '포항 산업재 물류센터', latitude: 35.950499, longitude: 129.381956, x: 414919.44, y: 375175.79, role: '경북권 Depot', nearestBackboneNode: 'R160', nearestBackboneDistanceKm: 1.460335, connectorBackboneNodes: ['R160', 'R162', 'R198'] },
  { id: 'D04', type: 'depot', name: '울산 산업재 물류센터', latitude: 35.576814, longitude: 129.36589, x: 414471.09, y: 333667.12, role: '울산·경남권 Depot', nearestBackboneNode: 'R156', nearestBackboneDistanceKm: 16.001653, connectorBackboneNodes: ['R156', 'R184', 'R160'] },
  { id: 'D05', type: 'depot', name: '광양 산업재 물류센터', latitude: 34.935993, longitude: 127.579675, x: 252958.92, y: 260147.36, role: '전남권 Depot', nearestBackboneNode: 'R139', nearestBackboneDistanceKm: 9.828481, connectorBackboneNodes: ['R139', 'R151', 'R153'] },
];

// 3. Customer Nodes (C001 - C050)
export const CUSTOMER_NODES: PhysicalNode[] = [
  { id: 'C001', type: 'customer', name: 'Synthetic Customer 001', latitude: 34.865099, longitude: 126.474707, role: 'synthetic_customer', nearestBackboneNode: 'R175', nearestBackboneDistanceKm: 0.75146, connectorBackboneNodes: ['R175', 'R168', 'R176'] },
  { id: 'C002', type: 'customer', name: 'Synthetic Customer 002', latitude: 35.940094, longitude: 129.393952, role: 'synthetic_customer', nearestBackboneNode: 'R160', nearestBackboneDistanceKm: 0.754174, connectorBackboneNodes: ['R160', 'R162', 'R198'] },
  { id: 'C003', type: 'customer', name: 'Synthetic Customer 003', latitude: 34.843953, longitude: 127.305449, role: 'synthetic_customer', nearestBackboneNode: 'R170', nearestBackboneDistanceKm: 0.752338, connectorBackboneNodes: ['R170', 'R150', 'R139'] },
  { id: 'C004', type: 'customer', name: 'Synthetic Customer 004', latitude: 38.151428, longitude: 128.578559, role: 'synthetic_customer', nearestBackboneNode: 'R196', nearestBackboneDistanceKm: 0.749317, connectorBackboneNodes: ['R196', 'R195', 'R187'] },
  { id: 'C005', type: 'customer', name: 'Synthetic Customer 005', latitude: 36.584527, longitude: 128.162274, role: 'synthetic_customer', nearestBackboneNode: 'R001', nearestBackboneDistanceKm: 0.750628, connectorBackboneNodes: ['R001', 'R003', 'R004'] },
  { id: 'C006', type: 'customer', name: 'Synthetic Customer 006', latitude: 37.487451, longitude: 126.492301, role: 'synthetic_customer', nearestBackboneNode: 'R179', nearestBackboneDistanceKm: 0.753871, connectorBackboneNodes: ['R179', 'R197', 'R141'] },
  { id: 'C007', type: 'customer', name: 'Synthetic Customer 007', latitude: 36.007535, longitude: 126.795006, role: 'synthetic_customer', nearestBackboneNode: 'R083', nearestBackboneDistanceKm: 0.753147, connectorBackboneNodes: ['R083', 'R118', 'R165'] },
  { id: 'C008', type: 'customer', name: 'Synthetic Customer 008', latitude: 35.29126, longitude: 128.393665, role: 'synthetic_customer', nearestBackboneNode: 'R131', nearestBackboneDistanceKm: 0.749747, connectorBackboneNodes: ['R131', 'R181', 'R097'] },
  { id: 'C009', type: 'customer', name: 'Synthetic Customer 009', latitude: 37.401496, longitude: 127.750122, role: 'synthetic_customer', nearestBackboneNode: 'R158', nearestBackboneDistanceKm: 0.749887, connectorBackboneNodes: ['R158', 'R190', 'R145'] },
  { id: 'C010', type: 'customer', name: 'Synthetic Customer 010', latitude: 36.791164, longitude: 127.047685, role: 'synthetic_customer', nearestBackboneNode: 'R173', nearestBackboneDistanceKm: 0.753311, connectorBackboneNodes: ['R173', 'R063', 'R029'] },
  { id: 'C011', type: 'customer', name: 'Synthetic Customer 011', latitude: 35.849453, longitude: 127.648521, role: 'synthetic_customer', nearestBackboneNode: 'R132', nearestBackboneDistanceKm: 0.753759, connectorBackboneNodes: ['R132', 'R159', 'R182'] },
  { id: 'C012', type: 'customer', name: 'Synthetic Customer 012', latitude: 37.881041, longitude: 127.205596, role: 'synthetic_customer', nearestBackboneNode: 'R194', nearestBackboneDistanceKm: 0.750443, connectorBackboneNodes: ['R194', 'R116', 'R185'] },
  { id: 'C013', type: 'customer', name: 'Synthetic Customer 013', latitude: 35.908407, longitude: 128.589546, role: 'synthetic_customer', nearestBackboneNode: 'R103', nearestBackboneDistanceKm: 0.749397, connectorBackboneNodes: ['R103', 'R026', 'R102'] },
  { id: 'C014', type: 'customer', name: 'Synthetic Customer 014', latitude: 36.50713, longitude: 129.118255, role: 'synthetic_customer', nearestBackboneNode: 'R183', nearestBackboneDistanceKm: 0.752537, connectorBackboneNodes: ['R183', 'R123', 'R154'] },
  { id: 'C015', type: 'customer', name: 'Synthetic Customer 015', latitude: 35.328054, longitude: 126.807491, role: 'synthetic_customer', nearestBackboneNode: 'R122', nearestBackboneDistanceKm: 0.75413, connectorBackboneNodes: ['R122', 'R137', 'R152'] },
  { id: 'C016', type: 'customer', name: 'Synthetic Customer 016', latitude: 37.639976, longitude: 128.499392, role: 'synthetic_customer', nearestBackboneNode: 'R169', nearestBackboneDistanceKm: 0.751252, connectorBackboneNodes: ['R169', 'R192', 'R200'] },
  { id: 'C017', type: 'customer', name: 'Synthetic Customer 017', latitude: 37.402507, longitude: 127.091631, role: 'synthetic_customer', nearestBackboneNode: 'R085', nearestBackboneDistanceKm: 0.749166, connectorBackboneNodes: ['R085', 'R125', 'R113'] },
  { id: 'C018', type: 'customer', name: 'Synthetic Customer 018', latitude: 36.909805, longitude: 127.697432, role: 'synthetic_customer', nearestBackboneNode: 'R089', nearestBackboneDistanceKm: 0.751686, connectorBackboneNodes: ['R089', 'R077', 'R023'] },
  { id: 'C019', type: 'customer', name: 'Synthetic Customer 019', latitude: 35.259254, longitude: 128.983199, role: 'synthetic_customer', nearestBackboneNode: 'R091', nearestBackboneDistanceKm: 0.754202, connectorBackboneNodes: ['R091', 'R120', 'R157'] },
  { id: 'C020', type: 'customer', name: 'Synthetic Customer 020', latitude: 36.406562, longitude: 127.375902, role: 'synthetic_customer', nearestBackboneNode: 'R124', nearestBackboneDistanceKm: 0.752151, connectorBackboneNodes: ['R124', 'R106', 'R096'] },
  { id: 'C021', type: 'customer', name: 'Synthetic Customer 021', latitude: 36.132676, longitude: 128.101311, role: 'synthetic_customer', nearestBackboneNode: 'R011', nearestBackboneDistanceKm: 0.749245, connectorBackboneNodes: ['R011', 'R038', 'R007'] },
  { id: 'C022', type: 'customer', name: 'Synthetic Customer 022', latitude: 35.43596, longitude: 127.396694, role: 'synthetic_customer', nearestBackboneNode: 'R119', nearestBackboneDistanceKm: 0.750801, connectorBackboneNodes: ['R119', 'R126', 'R189'] },
  { id: 'C023', type: 'customer', name: 'Synthetic Customer 023', latitude: 37.904165, longitude: 128.047719, role: 'synthetic_customer', nearestBackboneNode: 'R186', nearestBackboneDistanceKm: 0.753971, connectorBackboneNodes: ['R186', 'R187', 'R178'] },
  { id: 'C024', type: 'customer', name: 'Synthetic Customer 024', latitude: 35.005323, longitude: 127.814615, role: 'synthetic_customer', nearestBackboneNode: 'R153', nearestBackboneDistanceKm: 0.752962, connectorBackboneNodes: ['R153', 'R151', 'R139'] },
  { id: 'C025', type: 'customer', name: 'Synthetic Customer 025', latitude: 37.075529, longitude: 128.174178, role: 'synthetic_customer', nearestBackboneNode: 'R114', nearestBackboneDistanceKm: 0.749634, connectorBackboneNodes: ['R114', 'R167', 'R117'] },
  { id: 'C026', type: 'customer', name: 'Synthetic Customer 026', latitude: 36.424775, longitude: 128.624635, role: 'synthetic_customer', nearestBackboneNode: 'R148', nearestBackboneDistanceKm: 0.750059, connectorBackboneNodes: ['R148', 'R172', 'R071'] },
  { id: 'C027', type: 'customer', name: 'Synthetic Customer 027', latitude: 36.817931, longitude: 126.56685, role: 'synthetic_customer', nearestBackboneNode: 'R147', nearestBackboneDistanceKm: 0.753457, connectorBackboneNodes: ['R147', 'R188', 'R128'] },
  { id: 'C028', type: 'customer', name: 'Synthetic Customer 028', latitude: 35.691249, longitude: 128.188214, role: 'synthetic_customer', nearestBackboneNode: 'R138', nearestBackboneDistanceKm: 0.753639, connectorBackboneNodes: ['R138', 'R133', 'R094'] },
  { id: 'C029', type: 'customer', name: 'Synthetic Customer 029', latitude: 36.85093, longitude: 128.53302, role: 'synthetic_customer', nearestBackboneNode: 'R140', nearestBackboneDistanceKm: 0.750246, connectorBackboneNodes: ['R140', 'R166', 'R174'] },
  { id: 'C030', type: 'customer', name: 'Synthetic Customer 030', latitude: 37.854088, longitude: 126.758875, role: 'synthetic_customer', nearestBackboneNode: 'R177', nearestBackboneDistanceKm: 0.749481, connectorBackboneNodes: ['R177', 'R199', 'R116'] },
  { id: 'C031', type: 'customer', name: 'Synthetic Customer 031', latitude: 35.478976, longitude: 127.825431, role: 'synthetic_customer', nearestBackboneNode: 'R130', nearestBackboneDistanceKm: 0.752743, connectorBackboneNodes: ['R130', 'R112', 'R127'] },
  { id: 'C032', type: 'customer', name: 'Synthetic Customer 032', latitude: 35.484933, longitude: 129.291263, role: 'synthetic_customer', nearestBackboneNode: 'R156', nearestBackboneDistanceKm: 0.754068, connectorBackboneNodes: ['R156', 'R184', 'R091'] },
  { id: 'C033', type: 'customer', name: 'Synthetic Customer 033', latitude: 36.051581, longitude: 128.999121, role: 'synthetic_customer', nearestBackboneNode: 'R180', nearestBackboneDistanceKm: 0.751068, connectorBackboneNodes: ['R180', 'R198', 'R067'] },
  { id: 'C034', type: 'customer', name: 'Synthetic Customer 034', latitude: 37.187027, longitude: 127.44833, role: 'synthetic_customer', nearestBackboneNode: 'R161', nearestBackboneDistanceKm: 0.749195, connectorBackboneNodes: ['R161', 'R006', 'R078'] },
  { id: 'C035', type: 'customer', name: 'Synthetic Customer 035', latitude: 36.225978, longitude: 127.047583, role: 'synthetic_customer', nearestBackboneNode: 'R108', nearestBackboneDistanceKm: 0.751877, connectorBackboneNodes: ['R108', 'R049', 'R072'] },
  { id: 'C036', type: 'customer', name: 'Synthetic Customer 036', latitude: 37.758765, longitude: 128.837075, role: 'synthetic_customer', nearestBackboneNode: 'R192', nearestBackboneDistanceKm: 0.754213, connectorBackboneNodes: ['R192', 'R169', 'R195'] },
  { id: 'C037', type: 'customer', name: 'Synthetic Customer 037', latitude: 36.717675, longitude: 127.446264, role: 'synthetic_customer', nearestBackboneNode: 'R087', nearestBackboneDistanceKm: 0.751927, connectorBackboneNodes: ['R087', 'R090', 'R075'] },
  { id: 'C038', type: 'customer', name: 'Synthetic Customer 038', latitude: 35.147767, longitude: 127.44942, role: 'synthetic_customer', nearestBackboneNode: 'R142', nearestBackboneDistanceKm: 0.749204, connectorBackboneNodes: ['R142', 'R139', 'R150'] },
  { id: 'C039', type: 'customer', name: 'Synthetic Customer 039', latitude: 35.651274, longitude: 128.75185, role: 'synthetic_customer', nearestBackboneNode: 'R144', nearestBackboneDistanceKm: 0.751019, connectorBackboneNodes: ['R144', 'R149', 'R081'] },
  { id: 'C040', type: 'customer', name: 'Synthetic Customer 040', latitude: 35.734078, longitude: 126.769918, role: 'synthetic_customer', nearestBackboneNode: 'R134', nearestBackboneDistanceKm: 0.75405, connectorBackboneNodes: ['R134', 'R171', 'R110'] },
  { id: 'C041', type: 'customer', name: 'Synthetic Customer 041', latitude: 36.102306, longitude: 127.512907, role: 'synthetic_customer', nearestBackboneNode: 'R129', nearestBackboneDistanceKm: 0.752789, connectorBackboneNodes: ['R129', 'R159', 'R155'] },
  { id: 'C042', type: 'customer', name: 'Synthetic Customer 042', latitude: 37.192229, longitude: 126.878596, role: 'synthetic_customer', nearestBackboneNode: 'R115', nearestBackboneDistanceKm: 0.749506, connectorBackboneNodes: ['R115', 'R128', 'R197'] },
  { id: 'C043', type: 'customer', name: 'Synthetic Customer 043', latitude: 37.67339, longitude: 127.846493, role: 'synthetic_customer', nearestBackboneNode: 'R146', nearestBackboneDistanceKm: 0.750204, connectorBackboneNodes: ['R146', 'R178', 'R190'] },
  { id: 'C044', type: 'customer', name: 'Synthetic Customer 044', latitude: 36.452344, longitude: 127.718283, role: 'synthetic_customer', nearestBackboneNode: 'R121', nearestBackboneDistanceKm: 0.753606, connectorBackboneNodes: ['R121', 'R096', 'R155'] },
  { id: 'C045', type: 'customer', name: 'Synthetic Customer 045', latitude: 37.049592, longitude: 127.139662, role: 'synthetic_customer', nearestBackboneNode: 'R016', nearestBackboneDistanceKm: 0.753493, connectorBackboneNodes: ['R016', 'R092', 'R025'] },
  { id: 'C046', type: 'customer', name: 'Synthetic Customer 046', latitude: 37.520928, longitude: 127.438467, role: 'synthetic_customer', nearestBackboneNode: 'R193', nearestBackboneDistanceKm: 0.750098, connectorBackboneNodes: ['R193', 'R185', 'R158'] },
  { id: 'C047', type: 'customer', name: 'Synthetic Customer 047', latitude: 36.31431, longitude: 128.326822, role: 'synthetic_customer', nearestBackboneNode: 'R065', nearestBackboneDistanceKm: 0.749605, connectorBackboneNodes: ['R065', 'R052', 'R018'] },
  { id: 'C048', type: 'customer', name: 'Synthetic Customer 048', latitude: 35.144584, longitude: 128.089449, role: 'synthetic_customer', nearestBackboneNode: 'R136', nearestBackboneDistanceKm: 0.752917, connectorBackboneNodes: ['R136', 'R135', 'R153'] },
  { id: 'C049', type: 'customer', name: 'Synthetic Customer 049', latitude: 35.94499, longitude: 127.095697, role: 'synthetic_customer', nearestBackboneNode: 'R022', nearestBackboneDistanceKm: 0.753992, connectorBackboneNodes: ['R022', 'R068', 'R069'] },
  { id: 'C050', type: 'customer', name: 'Synthetic Customer 050', latitude: 36.164534, longitude: 128.570924, role: 'synthetic_customer', nearestBackboneNode: 'R111', nearestBackboneDistanceKm: 0.750848, connectorBackboneNodes: ['R111', 'R073', 'R086'] },
];

export const ALL_PHYSICAL_NODES: PhysicalNode[] = [
  ...DEPOT_NODES,
  ...CUSTOMER_NODES,
  ...ROAD_BACKBONE_NODES,
];

export const PHYSICAL_NETWORK: PhysicalNetwork = {
  nodes: ALL_PHYSICAL_NODES,
  edges: [],
  statusMessage: 'Node data is available, but structured Edge data is required to construct the complete routing graph.',
};

// Helper utilities for graph operations and physical routing lookup
export const getPhysicalNode = (id: string): PhysicalNode | undefined => {
  return ALL_PHYSICAL_NODES.find((node) => node.id === id);
};

export const getNodesByType = (type: 'road_backbone' | 'depot' | 'customer'): PhysicalNode[] => {
  return ALL_PHYSICAL_NODES.filter((node) => node.type === type);
};

/**
 * Given an array of physical node IDs, returns their latitude/longitude coordinates.
 * This allows routes to be represented as actual physical graph paths (e.g. ['R001', 'R015', 'C003', ...])
 */
export const resolveGraphPathCoordinates = (pathNodeIds: string[]): [number, number][] => {
  const coords: [number, number][] = [];
  for (const nodeId of pathNodeIds) {
    const node = getPhysicalNode(nodeId);
    if (node) {
      coords.push([node.latitude, node.longitude]);
    }
  }
  return coords;
};

/**
 * Connector lookup: Find connector backbone nodes for customer or depot
 */
export const getCustomerBackboneConnectors = (nodeId: string): {
  nearestNode?: PhysicalNode;
  distanceKm?: number;
  connectorNodes: PhysicalNode[];
} => {
  const node = getPhysicalNode(nodeId);
  if (!node) return { connectorNodes: [] };

  const nearestNode = node.nearestBackboneNode ? getPhysicalNode(node.nearestBackboneNode) : undefined;
  const connectorNodes = (node.connectorBackboneNodes || [])
    .map((cId) => getPhysicalNode(cId))
    .filter((n): n is PhysicalNode => n !== undefined);

  return {
    nearestNode,
    distanceKm: node.nearestBackboneDistanceKm,
    connectorNodes,
  };
};
