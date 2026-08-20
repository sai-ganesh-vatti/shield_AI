from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class RiskLevel(str, Enum):
    GREEN = "green"
    YELLOW = "yellow"
    ORANGE = "orange"
    RED = "red"


class TruckStatus(str, Enum):
    IDLE = "idle"
    LOADING = "loading"
    IN_TRANSIT = "in_transit"
    UNLOADING = "unloading"
    REROUTING = "rerouting"
    MAINTENANCE = "maintenance"


class ShipmentStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REROUTED = "rerouted"


class HealthStormStatus(str, Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    MONITORING = "monitoring"


class DistrictBase(BaseModel):
    code: str
    name: str
    state: str
    latitude: float
    longitude: float
    population: int
    base_demand: float = 100.0


class DistrictCreate(DistrictBase):
    pass


class DistrictUpdate(BaseModel):
    risk_level: Optional[RiskLevel] = None
    current_demand: Optional[float] = None
    demand_multiplier: Optional[float] = None
    is_health_storm_active: Optional[bool] = None
    storm_intensity: Optional[float] = None


class DistrictResponse(DistrictBase):
    id: int
    risk_level: RiskLevel
    current_demand: float
    demand_multiplier: float
    is_health_storm_active: bool
    storm_intensity: float
    hospitals_count: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class DistrictDetail(DistrictResponse):
    hospitals: List["HospitalResponse"] = []
    warehouses: List["WarehouseResponse"] = []
    inventory_summary: List["InventorySummary"] = []
    active_shipments: List["ShipmentResponse"] = []
    incoming_shipments: List["ShipmentResponse"] = []


class WarehouseBase(BaseModel):
    code: str
    name: str
    district_id: int
    latitude: float
    longitude: float
    capacity: float = 10000.0
    warehouse_type: str = "central"


class WarehouseCreate(WarehouseBase):
    pass


class WarehouseUpdate(BaseModel):
    current_stock: Optional[float] = None
    is_active: Optional[bool] = None


class WarehouseResponse(WarehouseBase):
    id: int
    current_stock: float
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class HospitalBase(BaseModel):
    code: str
    name: str
    district_id: int
    latitude: float
    longitude: float
    bed_capacity: int = 100
    hospital_type: str = "general"


class HospitalCreate(HospitalBase):
    pass


class HospitalUpdate(BaseModel):
    current_occupancy: Optional[int] = None
    is_active: Optional[bool] = None


class HospitalResponse(HospitalBase):
    id: int
    current_occupancy: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class MedicineBase(BaseModel):
    code: str
    name: str
    category: str
    unit: str = "units"
    critical_level: float = 100.0
    shelf_life_days: int = 365
    requires_cold_chain: bool = False


class MedicineCreate(MedicineBase):
    pass


class MedicineResponse(MedicineBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class InventoryBase(BaseModel):
    medicine_id: int
    warehouse_id: Optional[int] = None
    hospital_id: Optional[int] = None
    district_id: int
    quantity: float = 0.0
    reserved_quantity: float = 0.0
    min_threshold: float = 50.0
    max_threshold: float = 5000.0


class InventoryCreate(InventoryBase):
    pass


class InventoryUpdate(BaseModel):
    quantity: Optional[float] = None
    reserved_quantity: Optional[float] = None


class InventoryResponse(InventoryBase):
    id: int
    last_restocked: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class InventorySummary(BaseModel):
    medicine_id: int
    medicine_name: str
    medicine_code: str
    category: str
    total_quantity: float
    available_quantity: float
    reserved_quantity: float
    min_threshold: float
    is_critical: bool
    location_type: str
    location_id: int
    location_name: str


class TruckBase(BaseModel):
    code: str
    home_warehouse_id: int
    capacity: float = 1000.0
    speed_kmh: float = 40.0


class TruckCreate(TruckBase):
    current_latitude: float
    current_longitude: float


class TruckUpdate(BaseModel):
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None
    target_latitude: Optional[float] = None
    target_longitude: Optional[float] = None
    status: Optional[TruckStatus] = None
    current_load: Optional[float] = None
    progress: Optional[float] = None
    is_rerouted: Optional[bool] = None


class TruckResponse(TruckBase):
    id: int
    current_latitude: float
    current_longitude: float
    target_latitude: Optional[float] = None
    target_longitude: Optional[float] = None
    status: TruckStatus
    current_load: float
    route_id: Optional[int] = None
    progress: float
    assigned_shipment_id: Optional[int] = None
    is_rerouted: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class RouteBase(BaseModel):
    code: str
    name: str
    origin_warehouse_id: int
    destination_id: int
    destination_type: str
    distance_km: float
    estimated_time_hours: float
    path_coordinates: List[List[float]]


class RouteCreate(RouteBase):
    pass


class RouteUpdate(BaseModel):
    is_active: Optional[bool] = None
    is_rerouted: Optional[bool] = None


class RouteResponse(RouteBase):
    id: int
    is_active: bool
    is_rerouted: bool
    original_route_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ShipmentBase(BaseModel):
    code: str
    route_id: int
    medicine_id: int
    quantity: float
    priority: int = 1
    origin_type: str
    origin_id: int
    destination_type: str
    destination_id: int


class ShipmentCreate(ShipmentBase):
    pass


class ShipmentUpdate(BaseModel):
    truck_id: Optional[int] = None
    status: Optional[ShipmentStatus] = None
    actual_departure: Optional[datetime] = None
    estimated_arrival: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None
    is_rerouted: Optional[bool] = None


class ShipmentResponse(ShipmentBase):
    id: int
    truck_id: Optional[int] = None
    status: ShipmentStatus
    scheduled_departure: Optional[datetime] = None
    actual_departure: Optional[datetime] = None
    estimated_arrival: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None
    is_rerouted: bool
    original_shipment_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class HealthStormBase(BaseModel):
    code: str
    name: str
    district_id: int
    intensity: float = 1.0
    demand_multiplier: float = 3.0
    affected_medicines: List[int] = []


class HealthStormCreate(HealthStormBase):
    pass


class HealthStormUpdate(BaseModel):
    status: Optional[HealthStormStatus] = None
    total_shortage_predicted: Optional[float] = None
    total_rerouted_trucks: Optional[int] = None
    total_supplies_delivered: Optional[float] = None


class HealthStormResponse(HealthStormBase):
    id: int
    status: HealthStormStatus
    total_shortage_predicted: float
    total_rerouted_trucks: int
    total_supplies_delivered: float
    started_at: datetime
    resolved_at: Optional[datetime] = None
    estimated_resolution: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class SimulationEventResponse(BaseModel):
    id: int
    event_type: str
    entity_type: str
    entity_id: int
    description: str
    data: Dict[str, Any]
    severity: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class NetworkMetricsResponse(BaseModel):
    id: int
    timestamp: datetime
    total_districts: int
    critical_districts: int
    active_storms: int
    total_warehouses: int
    active_warehouses: int
    total_hospitals: int
    active_trucks: int
    idle_trucks: int
    in_transit_trucks: int
    rerouted_trucks: int
    pending_shipments: int
    in_transit_shipments: int
    delivered_shipments: int
    total_inventory: float
    critical_inventory_items: int
    network_health_score: float
    
    model_config = ConfigDict(from_attributes=True)


class HealthStormTrigger(BaseModel):
    intensity: float = Field(default=1.0, ge=0.1, le=2.0)
    duration_minutes: int = Field(default=30, ge=5, le=120)
    affected_medicine_categories: Optional[List[str]] = None


class RerouteRequest(BaseModel):
    truck_id: int
    new_destination_type: str
    new_destination_id: int
    priority: int = 1


class MapViewport(BaseModel):
    latitude: float
    longitude: float
    zoom: float
    bearing: float = 0
    pitch: float = 0


class TruckPosition(BaseModel):
    truck_id: int
    code: str
    latitude: float
    longitude: float
    target_latitude: Optional[float] = None
    target_longitude: Optional[float] = None
    status: TruckStatus
    progress: float
    is_rerouted: bool
    route_path: Optional[List[List[float]]] = None


class DistrictRiskUpdate(BaseModel):
    district_id: int
    risk_level: RiskLevel
    current_demand: float
    demand_multiplier: float
    is_health_storm_active: bool


class WebSocketMessage(BaseModel):
    type: str
    payload: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int