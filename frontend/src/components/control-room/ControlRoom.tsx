import React from 'react';
import { useStore, useAppDispatch, setSelectedDistrict } from '@/store/store';
import { selectNetworkMetrics, selectHealthStorms, selectCriticalDistricts, selectActiveTrucks, selectActiveStorms } from '@/store/selectors';
import { resolveHealthStorm, triggerHealthStorm } from '@/store/api';
import './ControlRoom.css';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  variant?: 'primary' | 'success' | 'warning' | 'danger';
  icon?: string;
}

const MetricCard: React.FC<MetricCardProps> = ({
  title, value, subtitle, variant = 'primary', icon
}) => {
  const variantColors = {
    primary: 'primary',
    success: 'success',
    warning: 'warning',
    danger: 'error',
  };

  return (
    <div className="metric-card bg-dark-900 rounded-xl p-4 border border-neutral-600 hover:transition-all hover:duration-300 hover:border-primary/50">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-sm font-medium text-neutral-400 mb-1">{title}</h3>
          <p className="text-3xl font-bold text-primary">{typeof value === 'number' ? value.toLocaleString() : value}</p>
        </div>
        <div className={`w-8 h-8 rounded-xl flex items-center justify-center text-lg ${variantColors[variant]}`}>
          {icon}
        </div>
      </div>
      {subtitle && <p className="text-xs text-neutral-500 mt-1">{subtitle}</p>}
    </div>
  );
};

interface StormCardProps {
  storm: any;
  onResolve: () => void;
}

const StormCard: React.FC<StormCardProps> = ({ storm, onResolve }) => {
  const intensity = storm.intensity;
  const riskLevel = intensity >= 1.5 ? 'RED' : intensity >= 1.0 ? 'ORANGE' : intensity >= 0.5 ? 'YELLOW' : 'GREEN';

  return (
    <div className="storm-card bg-dark-900 rounded-xl p-4 border border-orange-500/30 hover:border-orange-500/50 transition-colors">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-sm font-medium text-orange-400 mb-1">Health Storm</h3>
          <p className="text-xl font-bold text-orange-300">{storm.name}</p>
          <p className="text-sm text-neutral-400">District: {storm.districtName}</p>
        </div>
        <div>
          <p className="text-2xl font-bold text-orange-400">{intensity.toFixed(2)}</p>
          <p className="text-xs text-orange-300">Intensity</p>
        </div>
      </div>
      <div className="mt-3">
        <div className="w-full h-2 bg-neutral-700 rounded-full overflow-hidden">
          <div 
            className={`h-full bg-${riskLevel.toLowerCase()} rounded-full transition-all duration-500`}
            style={{ width: `${Math.min(intensity * 20, 100)}%` }}
          ></div>
        </div>
        <p className="text-xs text-neutral-400 mt-1">{riskLevel}</p>
      </div>
    </div>
  );
};

export default function ControlRoom() {
  const dispatch = useAppDispatch();
  const { data: metrics = null, isLoading } = useStore(selectNetworkMetrics);
  const { data: storms = [] } = useStore(selectHealthStorms);
  const { data: criticalDistricts = [] } = useStore(selectCriticalDistricts);
  const { data: activeTrucks = [] } = useStore(selectActiveTrucks);
  const { data: activeStorms = [] } = useStore(selectActiveStorms);

  // Handle start health storm
  const handleStartStorm = async (districtId: number) => {
    await dispatch(triggerHealthStorm(districtId));
  };

  // Handle resolve storm
  const handleResolveStorm = async (stormId: number) => {
    await dispatch(resolveHealthStorm(stormId));
  };

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <span>Loading...</span>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <header className="mb-6 p-4 bg-dark-900 rounded-xl border border-neutral-600">
        <h2 className="text-xl font-bold">Control Room</h2>
        <p className="text-neutral-400 mt-1">Pharmaceutical Logistics Network Status</p>
      </header>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <MetricCard
          title="Critical Districts"
          value={criticalDistricts.length}
          subtitle="Red Risk Level"
          variant="danger"
          icon="⚠️"
        />
        <MetricCard
          title="Active Health Storms"
          value={activeStorms.length}
          subtitle="Currently Active"
          variant="warning"
          icon="🌪️"
        />
        <MetricCard
          title="Active Trucks"
          value={activeTrucks.length}
          subtitle="In Transit"
          variant="primary"
          icon="🚚"
        />
        <MetricCard
          title="Network Health"
          value={metrics?.networkHealthScore ?? 0}
          subtitle="Overall Score"
          variant={metrics?.networkHealthScore && metrics.networkHealthScore > 80 ? 'success' : metrics?.networkHealthScore && metrics.networkHealthScore > 50 ? 'warning' : 'danger'}
          icon={(metrics?.networkHealthScore ?? 0) > 80 ? '✓' : (metrics?.networkHealthScore ?? 0) > 50 ? '!' : '✗'}
        />
      </div>

      {/* Active Health Storms */}
      {storms.length > 0 && (
        <div className="mb-6 p-4 bg-dark-900 rounded-xl border border-warning/30">
          <h3 className="text-semibold mb-3">Active Health Storms</h3>
          <div className="space-y-3">
            {storms.map((storm: any) => (
              <StormCard key={storm.id} storm={storm} onResolve={() => handleResolveStorm(storm.id)} />
            ))}
          </div>
        </div>
      )}

      {/* Critical Districts */}
      {criticalDistricts.length > 0 && (
        <div>
          <h3 className="text-semibold mb-3">Critical Districts</h3>
          <div className="space-y-2">
            {criticalDistricts.map((district: any) => (
              <div 
                key={district.id}
                className="p-3 bg-dark-800 rounded-xl border border-orange-500/30 hover:border-orange-500/50 transition-colors cursor-pointer"
                onClick={() => dispatch(setSelectedDistrict(district))}
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium">{district.name}</span>
                  <span className="text-orange-400 text-sm font-bold">{district.riskLevel.toUpperCase()}</span>
                </div>
                <p className="text-xs text-neutral-400 mt-1">{district.population.toLocaleString()} population</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
