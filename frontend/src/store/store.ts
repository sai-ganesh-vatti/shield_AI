import { configureStore, createSlice, type PayloadAction } from '@reduxjs/toolkit';
import { useDispatch, useSelector, type TypedUseSelectorHook } from 'react-redux';
import {
  fetchDistricts,
  fetchWarehouses,
  fetchHospitals,
  fetchTrucks,
  fetchHealthStorms,
  fetchNetworkMetrics,
  triggerHealthStorm,
  resolveHealthStorm,
} from './api';

export interface StoreState {
  district: DistrictState;
  warehouse: WarehouseState;
  hospital: HospitalState;
  truck: TruckState;
  healthStorm: HealthStormState;
  networkMetrics: NetworkMetrics;
  simulation: SimulationState;
  isLoading: boolean;
  error: string | null;
}

export interface District {
  id: number;
  code: string;
  name: string;
  state: string;
  lat: number;
  lon: number;
  population: number;
  riskLevel: RiskLevel;
  baseDemand: number;
  currentDemand: number;
  demandMultiplier: number;
  isHealthStormActive: boolean;
  stormIntensity: number;
  hospitalsCount: number;
}

export enum RiskLevel {
  GREEN = 'green',
  YELLOW = 'yellow',
  ORANGE = 'orange',
  RED = 'red',
}

export interface DistrictState {
  items: District[];
  selected: District | null;
  loading: boolean;
  error: string | null;
}

export interface Warehouse {
  id: number;
  code: string;
  name: string;
  districtId: number;
  lat: number;
  lon: number;
  capacity: number;
  currentStock: number;
  type: string;
}

export interface WarehouseState {
  items: Warehouse[];
}

export interface Hospital {
  id: number;
  code: string;
  name: string;
  districtId: number;
  lat: number;
  lon: number;
  bedCapacity: number;
  type: string;
}

export interface HospitalState {
  items: Hospital[];
}

export interface Truck {
  id: number;
  code: string;
  homeWarehouseId: number;
  currentLatitude: number;
  currentLongitude: number;
  targetLatitude: number | null;
  targetLongitude: number | null;
  status: TruckStatus;
  currentLoad: number;
  progress: number;
  isRerouted: boolean;
  routePath: number[][] | null;
}

export enum TruckStatus {
  IDLE = 'idle',
  LOADING = 'loading',
  IN_TRANSIT = 'in_transit',
  UNLOADING = 'unloading',
  REROUTING = 'rerouting',
  MAINTENANCE = 'maintenance',
}

export interface TruckState {
  items: Truck[];
}

export interface HealthStorm {
  id: number;
  code: string;
  name: string;
  districtId: number;
  status: HealthStormStatus;
  intensity: number;
  demandMultiplier: number;
  affectedMedicines: number[];
  startedAt: string;
  resolvedAt: string | null;
  estimatedResolution: string | null;
  totalShortagePredicted: number;
  totalReroutedTrucks: number;
  totalSuppliesDelivered: number;
}

export enum HealthStormStatus {
  ACTIVE = 'active',
  RESOLVED = 'resolved',
  MONITORING = 'monitoring',
}

export interface HealthStormState {
  items: HealthStorm[];
}

export interface NetworkMetrics {
  totalDistricts: number;
  criticalDistricts: number;
  activeStorms: number;
  totalWarehouses: number;
  activeWarehouses: number;
  totalHospitals: number;
  activeTrucks: number;
  idleTrucks: number;
  inTransitTrucks: number;
  reroutedTrucks: number;
  pendingShipments: number;
  inTransitShipments: number;
  deliveredShipments: number;
  totalInventory: number;
  criticalInventoryItems: number;
  networkHealthScore: number;
}

export interface SimulationState {
  isRunning: boolean;
  tick: number;
  lastUpdate: string;
}

// Initial state
const initialDistrictState: DistrictState = {
  items: [],
  selected: null,
  loading: false,
  error: null,
};

const initialWarehouseState: WarehouseState = { items: [] };
const initialHospitalState: HospitalState = { items: [] };
const initialTruckState: TruckState = { items: [] };
const initialHealthStormState: HealthStormState = { items: [] };

const initialNetworkMetrics: NetworkMetrics = {
  totalDistricts: 0,
  criticalDistricts: 0,
  activeStorms: 0,
  totalWarehouses: 0,
  activeWarehouses: 0,
  totalHospitals: 0,
  activeTrucks: 0,
  idleTrucks: 0,
  inTransitTrucks: 0,
  reroutedTrucks: 0,
  pendingShipments: 0,
  inTransitShipments: 0,
  deliveredShipments: 0,
  totalInventory: 0,
  criticalInventoryItems: 0,
  networkHealthScore: 100,
};

const initialSimulationState: SimulationState = {
  isRunning: false,
  tick: 0,
  lastUpdate: new Date().toISOString(),
};

// Slices
const districtSlice = createSlice({
  name: 'district',
  initialState: initialDistrictState,
  reducers: {
    setSelectedDistrict(state, action: PayloadAction<District | null>) {
      state.selected = action.payload;
    },
    clearSelectedDistrict(state) {
      state.selected = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchDistricts.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchDistricts.fulfilled, (state, action: PayloadAction<District[]>) => {
        state.items = action.payload;
        state.loading = false;
      })
      .addCase(fetchDistricts.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message ?? 'Failed to fetch districts';
      });
  },
});

const warehouseSlice = createSlice({
  name: 'warehouse',
  initialState: initialWarehouseState,
  reducers: {},
  extraReducers: (builder) => {
    builder.addCase(fetchWarehouses.fulfilled, (state, action: PayloadAction<Warehouse[]>) => {
      state.items = action.payload;
    });
  },
});

const hospitalSlice = createSlice({
  name: 'hospital',
  initialState: initialHospitalState,
  reducers: {},
  extraReducers: (builder) => {
    builder.addCase(fetchHospitals.fulfilled, (state, action: PayloadAction<Hospital[]>) => {
      state.items = action.payload;
    });
  },
});

const truckSlice = createSlice({
  name: 'truck',
  initialState: initialTruckState,
  reducers: {
    updateTruck(state, action: PayloadAction<Partial<Truck> & { id: number }>) {
      const index = state.items.findIndex((t) => t.id === action.payload.id);
      if (index !== -1) {
        state.items[index] = { ...state.items[index], ...action.payload };
      }
    },
  },
  extraReducers: (builder) => {
    builder.addCase(fetchTrucks.fulfilled, (state, action: PayloadAction<Truck[]>) => {
      state.items = action.payload;
    });
  },
});

const healthStormSlice = createSlice({
  name: 'healthStorm',
  initialState: initialHealthStormState,
  reducers: {},
  extraReducers: (builder) => {
    builder.addCase(fetchHealthStorms.fulfilled, (state, action: PayloadAction<HealthStorm[]>) => {
      state.items = action.payload;
    });
  },
});

const networkMetricsSlice = createSlice({
  name: 'networkMetrics',
  initialState: initialNetworkMetrics,
  reducers: {},
  extraReducers: (builder) => {
    builder.addCase(fetchNetworkMetrics.fulfilled, (_state, action: PayloadAction<NetworkMetrics>) => {
      return action.payload;
    });
  },
});

const simulationSlice = createSlice({
  name: 'simulation',
  initialState: initialSimulationState,
  reducers: {
    startSimulation(state) {
      state.isRunning = true;
    },
    stopSimulation(state) {
      state.isRunning = false;
    },
    tickSimulation(state) {
      state.tick += 1;
      state.lastUpdate = new Date().toISOString();
    },
  },
});

// Actions
export const { setSelectedDistrict, clearSelectedDistrict } = districtSlice.actions;
export const { updateTruck } = truckSlice.actions;
export const { startSimulation, stopSimulation, tickSimulation } = simulationSlice.actions;

// Root reducer
const rootReducer = {
  district: districtSlice.reducer,
  warehouse: warehouseSlice.reducer,
  hospital: hospitalSlice.reducer,
  truck: truckSlice.reducer,
  healthStorm: healthStormSlice.reducer,
  networkMetrics: networkMetricsSlice.reducer,
  simulation: simulationSlice.reducer,
};

export function createStore() {
  return configureStore({
    reducer: rootReducer,
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware({
        serializableCheck: false,
      }),
  });
}

export const store = createStore();

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

// Typed hooks
export const useAppDispatch: () => AppDispatch = useDispatch;
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;

/**
 * Convenience hook matching the { data, isLoading, error } shape used
 * throughout the components. Wraps useAppSelector with the district
 * slice's loading/error state (the only slice that currently tracks it).
 */
export function useStore<T>(selector: (state: RootState) => T) {
  const data = useAppSelector(selector);
  const isLoading = useAppSelector((s) => s.district.loading);
  const error = useAppSelector((s) => s.district.error);
  return { data, isLoading, error };
}

// Re-export thunks so existing imports of `{ triggerHealthStorm, resolveHealthStorm }`
// from this module (if any) keep working.
export { triggerHealthStorm, resolveHealthStorm };
