import { createAsyncThunk } from '@reduxjs/toolkit';
import type { District, Warehouse, Hospital, Truck, HealthStorm, NetworkMetrics } from './store';

const API_BASE =
  (import.meta as any).env?.VITE_API_URL ?? 'http://localhost:8000';
const API_V1 = `${API_BASE}/api/v1`;

async function apiFetch<T = any>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_V1}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

// --- Mappers: the FastAPI backend returns snake_case JSON, but the
// frontend types/components use camelCase throughout, so every response
// gets normalized here in one place. ---

function mapDistrict(d: any): District {
  return {
    id: d.id,
    code: d.code,
    name: d.name,
    state: d.state,
    lat: d.latitude,
    lon: d.longitude,
    population: d.population,
    riskLevel: d.risk_level,
    baseDemand: d.base_demand,
    currentDemand: d.current_demand,
    demandMultiplier: d.demand_multiplier,
    isHealthStormActive: d.is_health_storm_active,
    stormIntensity: d.storm_intensity,
    hospitalsCount: d.hospitals_count,
  };
}

function mapWarehouse(w: any): Warehouse {
  return {
    id: w.id,
    code: w.code,
    name: w.name,
    districtId: w.district_id,
    lat: w.latitude,
    lon: w.longitude,
    capacity: w.capacity,
    currentStock: w.current_stock,
    type: w.warehouse_type,
  };
}

function mapHospital(h: any): Hospital {
  return {
    id: h.id,
    code: h.code,
    name: h.name,
    districtId: h.district_id,
    lat: h.latitude,
    lon: h.longitude,
    bedCapacity: h.bed_capacity,
    type: h.hospital_type,
  };
}

function mapTruck(t: any): Truck {
  return {
    id: t.id,
    code: t.code,
    homeWarehouseId: t.home_warehouse_id,
    currentLatitude: t.current_latitude,
    currentLongitude: t.current_longitude,
    targetLatitude: t.target_latitude ?? null,
    targetLongitude: t.target_longitude ?? null,
    status: t.status,
    currentLoad: t.current_load,
    progress: t.progress,
    isRerouted: t.is_rerouted,
    routePath: null,
  };
}

function mapHealthStorm(s: any): HealthStorm {
  return {
    id: s.id,
    code: s.code,
    name: s.name,
    districtId: s.district_id,
    status: s.status,
    intensity: s.intensity,
    demandMultiplier: s.demand_multiplier,
    affectedMedicines: s.affected_medicines ?? [],
    startedAt: s.started_at,
    resolvedAt: s.resolved_at ?? null,
    estimatedResolution: s.estimated_resolution ?? null,
    totalShortagePredicted: s.total_shortage_predicted,
    totalReroutedTrucks: s.total_rerouted_trucks,
    totalSuppliesDelivered: s.total_supplies_delivered,
  };
}

function mapNetworkMetrics(m: any): NetworkMetrics {
  return {
    totalDistricts: m.total_districts,
    criticalDistricts: m.critical_districts,
    activeStorms: m.active_storms,
    totalWarehouses: m.total_warehouses,
    activeWarehouses: m.active_warehouses,
    totalHospitals: m.total_hospitals,
    activeTrucks: m.active_trucks,
    idleTrucks: m.idle_trucks,
    inTransitTrucks: m.in_transit_trucks,
    reroutedTrucks: m.rerouted_trucks,
    pendingShipments: m.pending_shipments,
    inTransitShipments: m.in_transit_shipments,
    deliveredShipments: m.delivered_shipments,
    totalInventory: m.total_inventory,
    criticalInventoryItems: m.critical_inventory_items,
    networkHealthScore: m.network_health_score,
  };
}

function mapShipment(s: any) {
  return {
    id: s.id,
    code: s.code,
    medicineId: s.medicine_id,
    routeId: s.route_id,
    quantity: s.quantity,
    status: s.status,
    estimatedArrival: s.estimated_arrival ?? null,
    isRerouted: s.is_rerouted,
  };
}

function mapDistrictDetail(d: any) {
  return {
    ...mapDistrict(d),
    hospitals: (d.hospitals ?? []).map(mapHospital),
    warehouses: (d.warehouses ?? []).map(mapWarehouse),
    inventorySummary: d.inventory_summary ?? [],
    activeShipments: (d.active_shipments ?? []).map(mapShipment),
    incomingShipments: (d.incoming_shipments ?? []).map(mapShipment),
  };
}

export const fetchDistricts = createAsyncThunk<District[]>(
  'district/fetchAll',
  async () => (await apiFetch<any[]>('/districts')).map(mapDistrict)
);

export const fetchDistrictDetails = createAsyncThunk<any, number>(
  'district/fetchDetails',
  async (districtId) => mapDistrictDetail(await apiFetch(`/districts/${districtId}`))
);

export const fetchWarehouses = createAsyncThunk<Warehouse[]>(
  'warehouse/fetchAll',
  async () => (await apiFetch<any[]>('/warehouses')).map(mapWarehouse)
);

export const fetchHospitals = createAsyncThunk<Hospital[]>(
  'hospital/fetchAll',
  async () => (await apiFetch<any[]>('/hospitals')).map(mapHospital)
);

export const fetchTrucks = createAsyncThunk<Truck[]>(
  'truck/fetchAll',
  async () => (await apiFetch<any[]>('/trucks')).map(mapTruck)
);

export const fetchHealthStorms = createAsyncThunk<HealthStorm[]>(
  'healthStorm/fetchAll',
  async () => (await apiFetch<any[]>('/health-storms')).map(mapHealthStorm)
);

export const fetchNetworkMetrics = createAsyncThunk<NetworkMetrics>(
  'networkMetrics/fetch',
  async () => mapNetworkMetrics(await apiFetch('/network-metrics'))
);

export const triggerHealthStorm = createAsyncThunk<any, number>(
  'district/triggerStorm',
  (districtId) =>
    apiFetch(`/districts/${districtId}/trigger-storm`, {
      method: 'POST',
      body: JSON.stringify({ intensity: 1.0, duration_minutes: 30 }),
    })
);

export const resolveHealthStorm = createAsyncThunk<any, number>(
  'district/resolveStorm',
  (districtId) =>
    apiFetch(`/districts/${districtId}/resolve-storm`, { method: 'POST' })
);
