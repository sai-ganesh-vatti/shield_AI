import { useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, Circle, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import {
  useAppDispatch,
  useStore,
  setSelectedDistrict,
  type District,
} from '@/store/store';
import { selectDistricts, selectWarehouses, selectHospitals, selectTrucks, selectHealthStorms } from '@/store/selectors';

function makeIcon(iconColorUrl: string, size: [number, number] = [25, 41]) {
  return L.icon({
    iconUrl: iconColorUrl,
    iconRetinaUrl: iconColorUrl,
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
    iconSize: size,
    iconAnchor: [size[0] / 2, size[1]],
    popupAnchor: [1, -34],
    shadowSize: [41, 41],
  });
}

const warehouseIcon = makeIcon('https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png');
const hospitalIcon = makeIcon('https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png');
const truckIcon = makeIcon('https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png', [20, 33]);

const riskColors: Record<string, string> = {
  green: '#4CAF50',
  yellow: '#FFC107',
  orange: '#FFA726',
  red: '#F44336',
};

function MapClickHandler({ onBackgroundClick }: { onBackgroundClick: () => void }) {
  useMapEvents({
    click: () => onBackgroundClick(),
  });
  return null;
}

export default function MapComponent() {
  const dispatch = useAppDispatch();
  const { data: districts = [] } = useStore(selectDistricts);
  const { data: warehouses = [] } = useStore(selectWarehouses);
  const { data: hospitals = [] } = useStore(selectHospitals);
  const { data: trucks = [] } = useStore(selectTrucks);
  const { data: healthStorms = [] } = useStore(selectHealthStorms);

  const center = useMemo<[number, number]>(() => {
    if (districts.length === 0) return [20.5937, 78.9629];
    const avgLat = districts.reduce((sum, d) => sum + d.lat, 0) / districts.length;
    const avgLon = districts.reduce((sum, d) => sum + d.lon, 0) / districts.length;
    return [avgLat, avgLon];
  }, [districts]);

  const handleDistrictClick = (district: District) => {
    dispatch(setSelectedDistrict(district));
  };

  const districtStormById = useMemo(() => {
    const map = new Map<number, (typeof healthStorms)[number]>();
    for (const storm of healthStorms) {
      if (storm.status === 'active') map.set(storm.districtId, storm);
    }
    return map;
  }, [healthStorms]);

  return (
    <MapContainer center={center} zoom={5} className="h-full w-full" style={{ height: '100%', width: '100%' }}>
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        maxZoom={18}
      />

      <MapClickHandler onBackgroundClick={() => dispatch(setSelectedDistrict(null))} />

      {/* Districts layer, colored by risk level */}
      {districts.map((district) => (
        <Circle
          key={`district-circle-${district.id}`}
          center={[district.lat, district.lon]}
          radius={30000}
          pathOptions={{
            color: riskColors[district.riskLevel] ?? riskColors.green,
            fillColor: riskColors[district.riskLevel] ?? riskColors.green,
            fillOpacity: 0.35,
          }}
          eventHandlers={{ click: () => handleDistrictClick(district) }}
        >
          <Popup>
            <div>
              <h4>{district.name}</h4>
              <p>State: {district.state}</p>
              <p>Population: {district.population.toLocaleString()}</p>
              <p>
                Risk Level: <span>{district.riskLevel.toUpperCase()}</span>
              </p>
              {district.isHealthStormActive && (
                <p>Health Storm Active (Intensity: {district.stormIntensity.toFixed(2)})</p>
              )}
            </div>
          </Popup>
        </Circle>
      ))}

      {/* Warehouses layer */}
      {warehouses.map((warehouse) => (
        <Marker key={`warehouse-${warehouse.id}`} position={[warehouse.lat, warehouse.lon]} icon={warehouseIcon}>
          <Popup>
            <div>
              <h4>{warehouse.name}</h4>
              <p>Stock: {warehouse.currentStock?.toLocaleString()}</p>
            </div>
          </Popup>
        </Marker>
      ))}

      {/* Hospitals layer */}
      {hospitals.map((hospital) => (
        <Marker key={`hospital-${hospital.id}`} position={[hospital.lat, hospital.lon]} icon={hospitalIcon}>
          <Popup>
            <div>
              <h4>{hospital.name}</h4>
              <p>Beds: {hospital.bedCapacity}</p>
            </div>
          </Popup>
        </Marker>
      ))}

      {/* Trucks layer */}
      {trucks.map((truck) => (
        <Marker
          key={`truck-${truck.id}`}
          position={[truck.currentLatitude, truck.currentLongitude]}
          icon={truckIcon}
        >
          <Popup>
            <div>
              <h4>Truck {truck.code}</h4>
              <p>Status: {truck.status}</p>
              <p>Progress: {(truck.progress * 100).toFixed(1)}%</p>
            </div>
          </Popup>
        </Marker>
      ))}

      {/* Supply routes: warehouse -> truck */}
      {trucks.map((truck) => {
        const warehouse = warehouses.find((w) => w.id === truck.homeWarehouseId);
        if (!warehouse) return null;
        return (
          <Polyline
            key={`route-${truck.id}`}
            positions={[
              [warehouse.lat, warehouse.lon],
              [truck.currentLatitude, truck.currentLongitude],
            ]}
            pathOptions={{
              color: truck.isRerouted ? '#ff6b6b' : '#00d4aa',
              weight: 2,
            }}
          />
        );
      })}

      {/* Health storm radius overlays */}
      {districts
        .filter((d) => districtStormById.has(d.id))
        .map((district) => {
          const storm = districtStormById.get(district.id)!;
          return (
            <Circle
              key={`storm-${storm.id}`}
              center={[district.lat, district.lon]}
              radius={50000 * storm.intensity}
              pathOptions={{
                color: '#ff6b6b',
                fillColor: '#ff6b6b',
                fillOpacity: 0.15,
                weight: 1,
              }}
            />
          );
        })}
    </MapContainer>
  );
}
