import enum
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Enum, ForeignKey, 
    Boolean, Text, Index, JSON, UniqueConstraint
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.database import Base


class RiskLevel(str, enum.Enum):
    GREEN = "green"
    YELLOW = "yellow"
    ORANGE = "orange"
    RED = "red"


class TruckStatus(str, enum.Enum):
    IDLE = "idle"
    LOADING = "loading"
    IN_TRANSIT = "in_transit"
    UNLOADING = "unloading"
    REROUTING = "rerouting"
    MAINTENANCE = "maintenance"


class ShipmentStatus(str, enum.Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REROUTED = "rerouted"


class HealthStormStatus(str, enum.Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    MONITORING = "monitoring"


class District(Base):
    __tablename__ = "districts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    state: Mapped[str] = mapped_column(String(50), index=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    population: Mapped[int] = mapped_column(Integer)
    risk_level: Mapped[RiskLevel] = mapped_column(Enum(RiskLevel), default=RiskLevel.GREEN, index=True)
    base_demand: Mapped[float] = mapped_column(Float, default=100.0)
    current_demand: Mapped[float] = mapped_column(Float, default=100.0)
    demand_multiplier: Mapped[float] = mapped_column(Float, default=1.0)
    is_health_storm_active: Mapped[bool] = mapped_column(Boolean, default=False)
    storm_intensity: Mapped[float] = mapped_column(Float, default=0.0)
    hospitals_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    hospitals: Mapped[List["Hospital"]] = relationship("Hospital", back_populates="district")
    warehouses: Mapped[List["Warehouse"]] = relationship("Warehouse", back_populates="district")
    inventory_items: Mapped[List["Inventory"]] = relationship("Inventory", back_populates="district")
    
    __table_args__ = (
        Index("ix_district_location", "latitude", "longitude"),
        Index("ix_district_risk", "risk_level"),
    )


class Warehouse(Base):
    __tablename__ = "warehouses"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    district_id: Mapped[int] = mapped_column(Integer, ForeignKey("districts.id"), index=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    capacity: Mapped[float] = mapped_column(Float, default=10000.0)
    current_stock: Mapped[float] = mapped_column(Float, default=0.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    warehouse_type: Mapped[str] = mapped_column(String(50), default="central")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    district: Mapped["District"] = relationship("District", back_populates="warehouses")
    inventory_items: Mapped[List["Inventory"]] = relationship("Inventory", back_populates="warehouse")
    trucks: Mapped[List["Truck"]] = relationship("Truck", back_populates="home_warehouse")
    
    __table_args__ = (
        Index("ix_warehouse_location", "latitude", "longitude"),
    )


class Hospital(Base):
    __tablename__ = "hospitals"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    district_id: Mapped[int] = mapped_column(Integer, ForeignKey("districts.id"), index=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    bed_capacity: Mapped[int] = mapped_column(Integer, default=100)
    current_occupancy: Mapped[int] = mapped_column(Integer, default=0)
    hospital_type: Mapped[str] = mapped_column(String(50), default="general")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    district: Mapped["District"] = relationship("District", back_populates="hospitals")
    inventory_items: Mapped[List["Inventory"]] = relationship("Inventory", back_populates="hospital")
    
    __table_args__ = (
        Index("ix_hospital_location", "latitude", "longitude"),
    )


class Medicine(Base):
    __tablename__ = "medicines"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    category: Mapped[str] = mapped_column(String(50), index=True)
    unit: Mapped[str] = mapped_column(String(20), default="units")
    critical_level: Mapped[float] = mapped_column(Float, default=100.0)
    shelf_life_days: Mapped[int] = mapped_column(Integer, default=365)
    requires_cold_chain: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    inventory_items: Mapped[List["Inventory"]] = relationship("Inventory", back_populates="medicine")


class Inventory(Base):
    __tablename__ = "inventory"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    medicine_id: Mapped[int] = mapped_column(Integer, ForeignKey("medicines.id"), index=True)
    warehouse_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("warehouses.id"), index=True, nullable=True)
    hospital_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("hospitals.id"), index=True, nullable=True)
    district_id: Mapped[int] = mapped_column(Integer, ForeignKey("districts.id"), index=True)
    quantity: Mapped[float] = mapped_column(Float, default=0.0)
    reserved_quantity: Mapped[float] = mapped_column(Float, default=0.0)
    min_threshold: Mapped[float] = mapped_column(Float, default=50.0)
    max_threshold: Mapped[float] = mapped_column(Float, default=5000.0)
    last_restocked: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    medicine: Mapped["Medicine"] = relationship("Medicine", back_populates="inventory_items")
    warehouse: Mapped[Optional["Warehouse"]] = relationship("Warehouse", back_populates="inventory_items")
    hospital: Mapped[Optional["Hospital"]] = relationship("Hospital", back_populates="inventory_items")
    district: Mapped["District"] = relationship("District", back_populates="inventory_items")
    
    __table_args__ = (
        UniqueConstraint("medicine_id", "warehouse_id", "hospital_id", "district_id", name="uq_inventory_location"),
        Index("ix_inventory_district_medicine", "district_id", "medicine_id"),
    )


class Truck(Base):
    __tablename__ = "trucks"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    home_warehouse_id: Mapped[int] = mapped_column(Integer, ForeignKey("warehouses.id"), index=True)
    current_latitude: Mapped[float] = mapped_column(Float)
    current_longitude: Mapped[float] = mapped_column(Float)
    target_latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    target_longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[TruckStatus] = mapped_column(Enum(TruckStatus), default=TruckStatus.IDLE, index=True)
    capacity: Mapped[float] = mapped_column(Float, default=1000.0)
    current_load: Mapped[float] = mapped_column(Float, default=0.0)
    speed_kmh: Mapped[float] = mapped_column(Float, default=40.0)
    route_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("routes.id"), nullable=True, index=True)
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    assigned_shipment_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("shipments.id"), nullable=True, index=True)
    is_rerouted: Mapped[bool] = mapped_column(Boolean, default=False)
    original_route_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    home_warehouse: Mapped["Warehouse"] = relationship("Warehouse", back_populates="trucks")
    route: Mapped[Optional["Route"]] = relationship("Route", back_populates="trucks")
    shipment: Mapped[Optional["Shipment"]] = relationship(
    "Shipment", 
    back_populates="truck",
    foreign_keys=[assigned_shipment_id]
)
    
    __table_args__ = (
        Index("ix_truck_location", "current_latitude", "current_longitude"),
        Index("ix_truck_status", "status"),
    )


class Route(Base):
    __tablename__ = "routes"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    origin_warehouse_id: Mapped[int] = mapped_column(Integer, ForeignKey("warehouses.id"), index=True)
    destination_id: Mapped[int] = mapped_column(Integer, index=True)
    destination_type: Mapped[str] = mapped_column(String(20))
    distance_km: Mapped[float] = mapped_column(Float)
    estimated_time_hours: Mapped[float] = mapped_column(Float)
    path_coordinates: Mapped[List[List[float]]] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_rerouted: Mapped[bool] = mapped_column(Boolean, default=False)
    original_route_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    trucks: Mapped[List["Truck"]] = relationship("Truck", back_populates="route")
    shipments: Mapped[List["Shipment"]] = relationship("Shipment", back_populates="route")
    
    __table_args__ = (
        Index("ix_route_origin_dest", "origin_warehouse_id", "destination_id", "destination_type"),
    )


class Shipment(Base):
    __tablename__ = "shipments"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    route_id: Mapped[int] = mapped_column(Integer, ForeignKey("routes.id"), index=True)
    truck_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("trucks.id"), nullable=True, index=True)
    medicine_id: Mapped[int] = mapped_column(Integer, ForeignKey("medicines.id"), index=True)
    quantity: Mapped[float] = mapped_column(Float)
    status: Mapped[ShipmentStatus] = mapped_column(Enum(ShipmentStatus), default=ShipmentStatus.PENDING, index=True)
    priority: Mapped[int] = mapped_column(Integer, default=1)
    origin_type: Mapped[str] = mapped_column(String(20))
    origin_id: Mapped[int] = mapped_column(Integer)
    destination_type: Mapped[str] = mapped_column(String(20))
    destination_id: Mapped[int] = mapped_column(Integer)
    scheduled_departure: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    actual_departure: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    estimated_arrival: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    actual_arrival: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_rerouted: Mapped[bool] = mapped_column(Boolean, default=False)
    original_shipment_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    route: Mapped["Route"] = relationship("Route", back_populates="shipments")
    truck: Mapped[Optional["Truck"]] = relationship("Truck", foreign_keys=[truck_id])
    medicine: Mapped["Medicine"] = relationship("Medicine")
    
    __table_args__ = (
        Index("ix_shipment_status", "status"),
        Index("ix_shipment_origin_dest", "origin_type", "origin_id", "destination_type", "destination_id"),
    )


class HealthStorm(Base):
    __tablename__ = "health_storms"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    district_id: Mapped[int] = mapped_column(Integer, ForeignKey("districts.id"), index=True)
    status: Mapped[HealthStormStatus] = mapped_column(Enum(HealthStormStatus), default=HealthStormStatus.ACTIVE, index=True)
    intensity: Mapped[float] = mapped_column(Float, default=1.0)
    demand_multiplier: Mapped[float] = mapped_column(Float, default=3.0)
    affected_medicines: Mapped[List[int]] = mapped_column(JSON, default=list)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    estimated_resolution: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    total_shortage_predicted: Mapped[float] = mapped_column(Float, default=0.0)
    total_rerouted_trucks: Mapped[int] = mapped_column(Integer, default=0)
    total_supplies_delivered: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    district: Mapped["District"] = relationship("District")
    
    __table_args__ = (
        Index("ix_health_storm_status", "status"),
        Index("ix_health_storm_district", "district_id"),
    )


class SimulationEvent(Base):
    __tablename__ = "simulation_events"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_type: Mapped[str] = mapped_column(String(50), index=True)
    entity_type: Mapped[str] = mapped_column(String(20))
    entity_id: Mapped[int] = mapped_column(Integer, index=True)
    description: Mapped[str] = mapped_column(Text)
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    severity: Mapped[str] = mapped_column(String(20), default="info")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index("ix_simulation_event_entity", "entity_type", "entity_id"),
        Index("ix_simulation_event_time", "created_at"),
    )


class NetworkMetrics(Base):
    __tablename__ = "network_metrics"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    total_districts: Mapped[int] = mapped_column(Integer)
    critical_districts: Mapped[int] = mapped_column(Integer)
    active_storms: Mapped[int] = mapped_column(Integer)
    total_warehouses: Mapped[int] = mapped_column(Integer)
    active_warehouses: Mapped[int] = mapped_column(Integer)
    total_hospitals: Mapped[int] = mapped_column(Integer)
    active_trucks: Mapped[int] = mapped_column(Integer)
    idle_trucks: Mapped[int] = mapped_column(Integer)
    in_transit_trucks: Mapped[int] = mapped_column(Integer)
    rerouted_trucks: Mapped[int] = mapped_column(Integer)
    pending_shipments: Mapped[int] = mapped_column(Integer)
    in_transit_shipments: Mapped[int] = mapped_column(Integer)
    delivered_shipments: Mapped[int] = mapped_column(Integer)
    total_inventory: Mapped[float] = mapped_column(Float)
    critical_inventory_items: Mapped[int] = mapped_column(Integer)
    network_health_score: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_network_metrics_time", "timestamp"),
    )