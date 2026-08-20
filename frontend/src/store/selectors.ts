import { createSelector } from '@reduxjs/toolkit';
import type { RootState } from './store';

export const selectDistricts = (state: RootState) => state.district.items;
export const selectSelectedDistrict = (state: RootState) => state.district.selected;
export const selectIsDistrictLoading = (state: RootState) => state.district.loading;
export const selectDistrictError = (state: RootState) => state.district.error;

export const selectWarehouses = (state: RootState) => state.warehouse.items;
export const selectHospitals = (state: RootState) => state.hospital.items;
export const selectTrucks = (state: RootState) => state.truck.items;
export const selectHealthStorms = (state: RootState) => state.healthStorm.items;
export const selectNetworkMetrics = (state: RootState) => state.networkMetrics;
export const selectSimulation = (state: RootState) => state.simulation;
export const selectSelectedDistrictId = (state: RootState) => state.district.selected?.id ?? null;

// Selector for districts with active health storms
export const selectDistrictsWithStorms = createSelector(
  [selectDistricts, selectHealthStorms],
  (districts, storms) => districts.map(d => ({
    ...d,
    isHealthStormActive: storms.some(s => s.districtId === d.id && s.status === 'active'),
    stormIntensity: storms.find(s => s.districtId === d.id && s.status === 'active')?.intensity || 0,
  }))
);

// Selector for critical districts
export const selectCriticalDistricts = createSelector([selectDistricts],
  (districts) => districts.filter(d => d.riskLevel === 'red')
);

// Selector for active trucks
export const selectActiveTrucks = createSelector([selectTrucks],
  (trucks) => trucks.filter(t => t.status !== 'idle')
);

// Selector for active health storms
export const selectActiveStorms = createSelector([selectHealthStorms],
  (storms) => storms.filter(s => s.status === 'active')
);
