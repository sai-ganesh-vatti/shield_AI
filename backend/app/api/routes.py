from fastapi import APIRouter, Depends, HTTPException, WebSocket
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models import (
    District, Warehouse, Hospital, Medicine, Inventory, Truck, Route,
    Shipment, HealthStorm, SimulationEvent, RiskLevel, TruckStatus,
    ShipmentStatus, HealthStormStatus
)
from app.schemas import (
    DistrictResponse, DistrictUpdate, DistrictDetail,
    WarehouseResponse, WarehouseUpdate,
    HospitalResponse, HospitalUpdate,
    MedicineResponse, InventoryResponse, InventorySummary,
    TruckResponse, TruckUpdate, RouteResponse, RouteUpdate,
    ShipmentResponse, ShipmentUpdate, HealthStormResponse,
    HealthStormTrigger, HealthStormUpdate, SimulationEventResponse,
    NetworkMetricsResponse, TruckPosition, MapViewport,
    RiskLevel, TruckStatus, ShipmentStatus, HealthStormStatus,
    DistrictRiskUpdate, WebSocketMessage, PaginatedResponse
)
from app.services.simulation import HealthStormSimulator, NetworkMonitor, RouteCalculator
from app.websockets import ws_manager

router = APIRouter(prefix="/api/v1", tags=["pharma-twin"])


# District endpoints
@router.get("/districts", response_model=List[DistrictDetail])
async def get_districts(
    skip: int = 0,
    limit: int = 100,
    risk_level: Optional[RiskLevel] = None,
    db: Session = Depends(get_db),
):
    """Get all districts with optional risk level filter."""
    stmt = select(District).offset(skip).limit(limit)
    if risk_level:
        stmt = stmt.where(District.risk_level == risk_level)
    
    result = await db.execute(stmt)
    districts = result.scalars().all()
    
    # Build detailed responses
    details = []
    for district in districts:
        # Get hospitals
        stmt_h = select(Hospital).where(Hospital.district_id == district.id)
        h_result = await db.execute(stmt_h)
        hospitals = h_result.scalars().all()
        
        # Get warehouses
        stmt_w = select(Warehouse).where(Warehouse.district_id == district.id)
        w_result = await db.execute(stmt_w)
        warehouses = w_result.scalars().all()
        
        # Get inventory
        stmt_i = select(Inventory).where(Inventory.district_id == district.id)
        i_result = await db.execute(stmt_i)
        inventories = i_result.scalars().all()
        
        # Get active health storm
        stmt_s = select(HealthStorm).where(HealthStorm.district_id == district.id)
        s_result = await db.execute(stmt_s)
        storm = s_result.scalar_one_or_none()
        
        # Get active shipments
        stmt_sh = select(Shipment).where(
            Shipment.destination_type == "district",
            Shipment.destination_id == district.id,
            Shipment.status.in_([ShipmentStatus.PENDING, ShipmentStatus.IN_TRANSIT])
        )
        sh_result = await db.execute(stmt_sh)
        shipments = sh_result.scalars().all()
        
        # Get incoming shipments
        stmt_ish = select(Shipment).where(
            Shipment.destination_type == "district",
            Shipment.destination_id == district.id,
            Shipment.status == ShipmentStatus.PENDING
        )
        ish_result = await db.execute(stmt_ish)
        incoming_shipments = ish_result.scalars().all()
        
        detail = DistrictDetail(
            **DistrictResponse(
                id=district.id,
                code=district.code,
                name=district.name,
                state=district.state,
                latitude=district.latitude,
                longitude=district.longitude,
                population=district.population,
                base_demand=district.base_demand,
                current_demand=district.current_demand,
                demand_multiplier=district.demand_multiplier,
                is_health_storm_active=district.is_health_storm_active,
                storm_intensity=district.storm_intensity,
                risk_level=district.risk_level,
                hospitals_count=district.hospitals_count,
                created_at=district.created_at,
                updated_at=district.updated_at,
            ).model_dump(),
            hospitals=[HospitalResponse.model_validate(h) for h in hospitals],
            warehouses=[WarehouseResponse.model_validate(w) for w in warehouses],
            inventory_summary=[],
            active_shipments=[ShipmentResponse.model_validate(s) for s in shipments],
            incoming_shipments=[ShipmentResponse.model_validate(s) for s in incoming_shipments],
        )
        details.append(detail)
    
    return details


@router.get("/districts/{district_id}", response_model=DistrictDetail)
async def get_district(
    district_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific district with details."""
    stmt = select(District).where(District.id == district_id)
    result = await db.execute(stmt)
    district = result.scalar_one_or_none()
    
    if not district:
        raise HTTPException(status_code=404, detail="District not found")
    
    # Get hospitals
    stmt_h = select(Hospital).where(Hospital.district_id == district.id)
    h_result = await db.execute(stmt_h)
    hospitals = h_result.scalars().all()
    
    # Get warehouses
    stmt_w = select(Warehouse).where(Warehouse.district_id == district.id)
    w_result = await db.execute(stmt_w)
    warehouses = w_result.scalars().all()
    
    # Get inventory
    stmt_i = select(Inventory).where(Inventory.district_id == district.id)
    i_result = await db.execute(stmt_i)
    inventories = i_result.scalars().all()
    
    # Get active health storm
    stmt_s = select(HealthStorm).where(HealthStorm.district_id == district.id)
    s_result = await db.execute(stmt_s)
    storm = s_result.scalar_one_or_none()
    
    # Get active shipments
    stmt_sh = select(Shipment).where(
        Shipment.destination_type == "district",
        Shipment.destination_id == district.id,
        Shipment.status.in_([ShipmentStatus.PENDING, ShipmentStatus.IN_TRANSIT])
    )
    sh_result = await db.execute(stmt_sh)
    shipments = sh_result.scalars().all()
    
    # Get incoming shipments
    stmt_ish = select(Shipment).where(
        Shipment.destination_type == "district",
        Shipment.destination_id == district.id,
        Shipment.status == ShipmentStatus.PENDING
    )
    ish_result = await db.execute(stmt_ish)
    incoming_shipments = ish_result.scalars().all()
    
    # Build inventory summaries
    inventory_summaries = []
    for inv in inventories:
        medicine = await db.get(Medicine, inv.medicine_id)
        if medicine:
            inventory_summaries.append(InventorySummary(
                medicine_id=inv.medicine_id,
                medicine_name=medicine.name,
                medicine_code=medicine.code,
                category=medicine.category,
                total_quantity=inv.quantity,
                available_quantity=inv.quantity - inv.reserved_quantity,
                reserved_quantity=inv.reserved_quantity,
                min_threshold=inv.min_threshold,
                is_critical=inv.quantity < inv.min_threshold,
                location_type="district",
                location_id=district.id,
                location_name=district.name,
            ))
    
    # Build risk update
    risk_update = DistrictRiskUpdate(
        district_id=district.id,
        risk_level=district.risk_level,
        current_demand=district.current_demand,
        demand_multiplier=district.demand_multiplier,
        is_health_storm_active=district.is_health_storm_active,
    )
    
    detail = DistrictDetail(
        **DistrictResponse(
            id=district.id,
            code=district.code,
            name=district.name,
            state=district.state,
            latitude=district.latitude,
            longitude=district.longitude,
            population=district.population,
            base_demand=district.base_demand,
            current_demand=district.current_demand,
            demand_multiplier=district.demand_multiplier,
            is_health_storm_active=district.is_health_storm_active,
            storm_intensity=district.storm_intensity,
            hospitals_count=district.hospitals_count,
            created_at=district.created_at,
            updated_at=district.updated_at,
        ).model_dump(),
        hospitals=[HospitalResponse.model_validate(h) for h in hospitals],
        warehouses=[WarehouseResponse.model_validate(w) for w in warehouses],
        inventory_summary=inventory_summaries,
        active_shipments=[ShipmentResponse.model_validate(s) for s in shipments],
        incoming_shipments=[ShipmentResponse.model_validate(s) for s in incoming_shipments],
    )
    
    return detail


@router.post("/districts/{district_id}/trigger-storm", response_model=HealthStormResponse)
async def trigger_health_storm(
    district_id: int,
    trigger: HealthStormTrigger,
    db: Session = Depends(get_db),
):
    """Trigger a health storm in a district."""
    simulator = HealthStormSimulator(db)
    return await simulator.trigger_health_storm(
        district_id=district_id,
        intensity=trigger.intensity,
        duration_minutes=trigger.duration_minutes,
        affected_categories=trigger.affected_medicine_categories,
    )


@router.post("/districts/{district_id}/resolve-storm", response_model=HealthStormResponse)
async def resolve_health_storm(
    district_id: int,
    db: Session = Depends(get_db),
):
    """Resolve a health storm in a district."""
    simulator = HealthStormSimulator(db)
    return await simulator.resolve_health_storm(district_id)


# Warehouse endpoints
@router.get("/warehouses", response_model=List[WarehouseResponse])
async def get_warehouses(
    db: Session = Depends(get_db),
):
    """Get all warehouses."""
    stmt = select(Warehouse).where(Warehouse.is_active == True)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/warehouses/{warehouse_id}", response_model=WarehouseResponse)
async def get_warehouse(
    warehouse_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific warehouse."""
    stmt = select(Warehouse).where(Warehouse.id == warehouse_id)
    result = await db.execute(stmt)
    warehouse = result.scalar_one_or_none()
    
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    
    return warehouse


# Hospital endpoints
@router.get("/hospitals", response_model=List[HospitalResponse])
async def get_hospitals(
    db: Session = Depends(get_db),
):
    """Get all hospitals."""
    stmt = select(Hospital).where(Hospital.is_active == True)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/hospitals/{hospital_id}", response_model=HospitalResponse)
async def get_hospital(
    hospital_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific hospital."""
    stmt = select(Hospital).where(Hospital.id == hospital_id)
    result = await db.execute(stmt)
    hospital = result.scalar_one_or_none()
    
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")
    
    return hospital


# Truck endpoints
@router.get("/trucks", response_model=List[TruckResponse])
async def get_trucks(
    status: Optional[TruckStatus] = None,
    db: Session = Depends(get_db),
):
    """Get all trucks, optionally filtered by status."""
    stmt = select(Truck)
    if status:
        stmt = stmt.where(Truck.status == status)
    
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/trucks/{truck_id}", response_model=TruckResponse)
async def get_truck(
    truck_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific truck."""
    stmt = select(Truck).where(Truck.id == truck_id)
    result = await db.execute(stmt)
    truck = result.scalar_one_or_none()
    
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")
    
    return truck


@router.post("/trucks/{truck_id}/reroute", response_model=TruckResponse)
async def reroute_truck(
    truck_id: int,
    request: dict,
    db: Session = Depends(get_db),
):
    """Reroute a truck to a new destination."""
    stmt = select(Truck).where(Truck.id == truck_id)
    result = await db.execute(stmt)
    truck = result.scalar_one_or_none()
    
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")
    
    new_destination_type = request.get("new_destination_type", "district")
    new_destination_id = request.get("new_destination_id")
    priority = request.get("priority", 1)
    
    truck.status = TruckStatus.REROUTING
    truck.is_rerouted = True
    truck.original_route_id = truck.route_id
    
    if new_destination_type == "district":
        truck.target_latitude = (await db.get(District, new_destination_id)).latitude
        truck.target_longitude = (await db.get(District, new_destination_id)).longitude
    elif new_destination_type == "warehouse":
        truck.target_latitude = (await db.get(Warehouse, new_destination_id)).latitude
        truck.target_longitude = (await db.get(Warehouse, new_destination_id)).longitude
    
    truck.progress = 0.0
    
    # Record event
    event = SimulationEvent(
        event_type="truck_rerouted",
        entity_type="truck",
        entity_id=truck.id,
        description=f"Truck {truck.code} rerouted to {new_destination_type} {new_destination_id}",
        data={
            "new_destination_type": new_destination_type,
            "new_destination_id": new_destination_id,
            "priority": priority,
        },
        severity="medium",
    )
    db.add(event)
    await db.flush()
    
    await db.refresh(truck)
    return truck


# Route endpoints
@router.get("/routes", response_model=List[RouteResponse])
async def get_routes(
    db: Session = Depends(get_db),
):
    """Get all routes."""
    stmt = select(Route).where(Route.is_active == True)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/routes/{route_id}", response_model=RouteResponse)
async def get_route(
    route_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific route."""
    stmt = select(Route).where(Route.id == route_id)
    result = await db.execute(stmt)
    route = result.scalar_one_or_none()
    
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    return route


# Shipment endpoints
@router.get("/shipments", response_model=List[ShipmentResponse])
async def get_shipments(
    status: Optional[ShipmentStatus] = None,
    db: Session = Depends(get_db),
):
    """Get all shipments, optionally filtered by status."""
    stmt = select(Shipment)
    if status:
        stmt = stmt.where(Shipment.status == status)
    
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/shipments/{shipment_id}", response_model=ShipmentResponse)
async def get_shipment(
    shipment_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific shipment."""
    stmt = select(Shipment).where(Shipment.id == shipment_id)
    result = await db.execute(stmt)
    shipment = result.scalar_one_or_none()
    
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    return shipment


# Health storm endpoints
@router.get("/health-storms", response_model=List[HealthStormResponse])
async def get_health_storms(
    status: Optional[HealthStormStatus] = None,
    db: Session = Depends(get_db),
):
    """Get all health storms, optionally filtered by status."""
    stmt = select(HealthStorm)
    if status:
        stmt = stmt.where(HealthStorm.status == status)
    
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/health-storms/active", response_model=List[HealthStormResponse])
async def get_active_health_storms(
    db: Session = Depends(get_db),
):
    """Get active health storms."""
    stmt = select(HealthStorm).where(HealthStorm.status == HealthStormStatus.ACTIVE)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/network-metrics", response_model=NetworkMetricsResponse)
async def get_network_metrics(
    db: Session = Depends(get_db),
):
    """Get network-wide metrics."""
    monitor = NetworkMonitor(db)
    return await monitor.update_metrics()


# Simulation events
@router.get("/simulation-events", response_model=List[SimulationEventResponse])
async def get_simulation_events(
    skip: int = 0,
    limit: int = 100,
    severity: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get simulation events."""
    stmt = select(SimulationEvent).offset(skip).limit(limit)
    if severity:
        stmt = stmt.where(SimulationEvent.severity == severity)
    
    result = await db.execute(stmt)
    return result.scalars().all()


# WebSocket endpoint
@router.websocket("/ws/{client_id}")
async def websocket_route(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time updates."""
    await ws_manager.websocket_endpoint(websocket, client_id)