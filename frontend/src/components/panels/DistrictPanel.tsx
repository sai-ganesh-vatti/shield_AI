import { useEffect, useState } from 'react';
import { useStore, useAppDispatch } from '@/store/store';
import { selectSelectedDistrict, selectDistricts } from '@/store/selectors';
import { fetchDistrictDetails, triggerHealthStorm, resolveHealthStorm } from '@/store/api';
import './DistrictPanel.css';

interface DistrictDetail {
  id: number;
  code: string;
  name: string;
  state: string;
  lat: number;
  lon: number;
  population: number;
  riskLevel: string;
  baseDemand: number;
  currentDemand: number;
  demandMultiplier: number;
  isHealthStormActive: boolean;
  stormIntensity: number;
  hospitals: any[];
  warehouses: any[];
  inventory: any[];
  activeShipments: any[];
  incomingShipments: any[];
}

export default function DistrictPanel() {
  const dispatch = useAppDispatch();
  const { data: selectedDistrict } = useStore(selectSelectedDistrict);
  const { data: districts = [] } = useStore(selectDistricts);
  const [detail, setDetail] = useState<DistrictDetail | null>(null);

  useEffect(() => {
    if (!selectedDistrict) {
      setDetail(null);
      return;
    }
    let cancelled = false;
    dispatch(fetchDistrictDetails(selectedDistrict.id))
      .unwrap()
      .then((result: DistrictDetail) => {
        if (!cancelled) setDetail(result);
      })
      .catch(() => {
        if (!cancelled) setDetail(null);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedDistrict?.id, dispatch]);

  if (!selectedDistrict) {
    return (
      <div className="panel-empty bg-dark-900 rounded-xl p-8 text-center">
        <h3>Click a District on the Map</h3>
        <p className="text-neutral-400 mt-2">Select a district to view detailed information</p>
      </div>
    );
  }

  // Use fetched detail (has hospitals/warehouses/shipments) once available,
  // falling back to the summary record while it loads.
  const summary = districts.find((d) => d.id === selectedDistrict.id) || selectedDistrict;
  const district: any = detail ?? summary;

  if (!district) {
    return <div>District data not available</div>;
  }

  return (
    <div className="panel-detail bg-dark-900 rounded-xl p-6 border border-neutral-600">
      <header className="mb-6">
        <h2 className="text-xl font-bold mb-2">{district.name}</h2>
        <p className="text-neutral-400">
          {district.state} • Population: {district.population.toLocaleString()}
        </p>
        {district.isHealthStormActive && (
          <div className="mt-3 p-3 bg-red-500/20 rounded-xl border border-red-500/30">
            <p className="text-sm font-medium text-red-300">🚨 Health Storm Active</p>
            <p className="text-xs text-red-400">Intensity: {district.stormIntensity.toFixed(2)}</p>
          </div>
        )}
      </header>

      {/* Risk Assessment */}
      <div className="risk-assessment mb-6">
        <h3 className="text-semibold mb-3">Risk Assessment</h3>
        <div className="flex gap-2">
          {['GREEN', 'YELLOW', 'ORANGE', 'RED'].map((level) => {
            const isCurrent = level.toLowerCase() === district.riskLevel;
            return (
              <div 
                key={level}
                className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${isCurrent ? 'ring-2 ring-primary' : ''} ${level === 'GREEN' ? 'text-green-400' : level === 'YELLOW' ? 'text-yellow-400' : level === 'ORANGE' ? 'text-orange-400' : 'text-red-400'}`}
              >
                {level[0]}
              </div>
            );
          })}
        </div>
        <p className="text-neutral-400 mt-2">Current Risk Level: <span className="font-bold text-primary">{district.riskLevel.toUpperCase()}</span></p>
        <p className="text-neutral-400 mt-1">Demand Multiplier: <span className="font-bold">{district.demandMultiplier.toFixed(2)}x</span></p>
      </div>

      {/* Medicine Demand & Inventory */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <InventoryCard
          title="Medicine Demand"
          value={district.currentDemand.toLocaleString()}
          minThreshold={district.baseDemand.toLocaleString()}
          critical={district.currentDemand > district.baseDemand * 1.5}
          category="General Medicines"
        />
        <InventoryCard
          title="Inventory Status"
          value={`Stock: ${district.warehouses?.length > 0 ? district.warehouses[0]?.currentStock?.toLocaleString() : 'N/A'}`}
          minThreshold="5000"
          critical={district.warehouses?.length > 0 && district.warehouses[0]?.currentStock < 1000}
          category="Warehouse Stock"
        />
      </div>

      {/* Hospitals Affected */}
      <div className="mt-6">
        <h3 className="text-semibold mb-3">Hospitals Affected</h3>
        {district.hospitals?.length > 0 ? (
          district.hospitals.map((h: any) => (
            <div key={h.id} className="p-3 bg-dark-800 rounded-xl border border-neutral-600 mb-2">
              <div className="flex items-center justify-between">
                <span className="font-medium">{h.name}</span>
                <span className="text-sm text-neutral-400">{h.bedCapacity} beds</span>
              </div>
              <p className="text-xs text-neutral-400">Location: {h.lat?.toFixed(2)}, {h.lon?.toFixed(2)}</p>
            </div>
          ))
        ) : (
          <p className="text-neutral-500 text-sm">No hospitals data available</p>
        )}
      </div>

      {/* Shipments */}
      <div className="mt-6">
        <h3 className="text-semibold mb-3">Active Shipments</h3>
        {district.incomingShipments?.length > 0 ? (
          district.incomingShipments.map((s: any) => (
            <div key={s.code ?? s.id} className="p-3 bg-dark-800 rounded-xl border border-primary/30 mb-2">
              <div className="flex items-center justify-between">
                <span className="font-medium">Medicine #{s.medicineId}</span>
                <span className="text-sm text-primary">{s.quantity} units</span>
              </div>
              <p className="text-xs text-neutral-400">Route #{s.routeId} • ETA: {s.estimatedArrival ? new Date(s.estimatedArrival).toLocaleString() : 'N/A'}</p>
            </div>
          ))
        ) : (
          <p className="text-neutral-500 text-sm">No active shipments</p>
        )}
      </div>

      {/* Action Buttons */}
      <div className="mt-6 p-4 bg-dark-800 rounded-xl border border-neutral-600">
        <h3 className="text-semibold mb-3">Actions</h3>
        <div className="flex gap-3 flex-wrap">
          <button
            onClick={() => dispatch(triggerHealthStorm(district.id))}
            className="btn btn-warning flex-1"
          >
            Start Health Storm
          </button>
          {district.isHealthStormActive && (
            <button
              onClick={() => dispatch(resolveHealthStorm(district.id))}
              className="btn btn-primary flex-1"
            >
              Resolve Storm
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

interface InventoryCardProps {
  title: string;
  value: string;
  minThreshold: string;
  critical: boolean;
  category: string;
}

function InventoryCard({ title, value, minThreshold, critical, category }: InventoryCardProps) {
  return (
    <div className={`p-4 rounded-xl border ${critical ? 'border-red-500/50 bg-red-500/10' : 'border-neutral-600 bg-dark-800'}`}>
      <h4 className="text-sm font-medium text-neutral-400 mb-1">{title}</h4>
      <p className={`text-lg font-bold ${critical ? 'text-red-400' : 'text-primary'}`}>{value}</p>
      <p className="text-xs text-neutral-500 mt-1">
        {category} · Min threshold: {minThreshold}
      </p>
      {critical && <p className="text-xs text-red-400 mt-1">⚠️ Below safe threshold</p>}
    </div>
  );
}