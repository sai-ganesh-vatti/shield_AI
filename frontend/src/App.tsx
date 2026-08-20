import { useEffect } from 'react';
import {
  useAppDispatch,
  useStore,
  startSimulation,
  stopSimulation,
} from '@/store/store';
import {
  fetchDistricts,
  fetchWarehouses,
  fetchHospitals,
  fetchTrucks,
  fetchHealthStorms,
  fetchNetworkMetrics,
  triggerHealthStorm,
} from '@/store/api';
import { selectSelectedDistrict, selectSimulation } from '@/store/selectors';
import DistrictPanel from '@/components/panels/DistrictPanel';
import ControlRoom from '@/components/control-room/ControlRoom';
import MapComponent from '@/components/map/MapComponent';

function App() {
  const dispatch = useAppDispatch();

  const { data: selectedDistrict } = useStore(selectSelectedDistrict);
  const { data: simulation } = useStore(selectSimulation);

  useEffect(() => {
    dispatch(fetchDistricts());
    dispatch(fetchWarehouses());
    dispatch(fetchHospitals());
    dispatch(fetchTrucks());
    dispatch(fetchHealthStorms());
    dispatch(fetchNetworkMetrics());
  }, [dispatch]);

  const handleToggleSimulation = () => {
    if (simulation?.isRunning) {
      dispatch(stopSimulation());
    } else {
      dispatch(startSimulation());
    }
  };

  return (
    <div className="app">
      <header className="flex items-center justify-between p-4 bg-dark-900 border-b border-neutral-700">
        <div>
          <h1 className="text-xl font-bold">Digital Twin: India Pharmaceutical Logistics Network</h1>
          <p className="subtitle text-neutral-400">Real-time simulation of pharmaceutical supply chain across India</p>
        </div>
        <div className="header-actions flex gap-3">
          <button
            onClick={handleToggleSimulation}
            className="btn btn-primary"
            title="Start/Pause Simulation"
          >
            {simulation?.isRunning ? 'Pause' : 'Start'} Simulation
          </button>
          <button
            onClick={() => selectedDistrict && dispatch(triggerHealthStorm(selectedDistrict.id))}
            className="btn btn-warning"
            title="Start Health Storm"
            disabled={!selectedDistrict}
          >
            Start Health Storm
          </button>
        </div>
      </header>

      <main className="flex flex-col lg:flex-row h-screen">
        {/* Left Panel: Map */}
        <section className="w-full lg:w-3/4 bg-dark-900 h-full border-r lg:border-b lg:border-0">
          <MapComponent />
        </section>

        {/* Right Panel: Control Room */}
        <section className="w-full lg:w-1/4 bg-dark-800 overflow-y-auto p-4">
          <ControlRoom />
          <DistrictPanel />
        </section>
      </main>
    </div>
  );
}

export default App;
