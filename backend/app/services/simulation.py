from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import asyncio
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import (
    District, Warehouse, Hospital, Medicine, Inventory, Truck, Route,
    Shipment, HealthStorm, SimulationEvent, RiskLevel, TruckStatus, ShipmentStatus,
    HealthStormStatus
)
from app.schemas import (
    DistrictResponse, DistrictRiskUpdate, HealthStormResponse,
    HealthStormTrigger, TruckResponse, ShipmentResponse,
    InventorySummary, NetworkMetricsResponse
)


class HealthStormSimulator:
    """Simulates health storms and their effects on the logistics network."""
    
    def __init__(self, db: Session):
        self.db = db
        self.storms: Dict[int, HealthStorm] = {}
    
    async def trigger_health_storm(
        self, 
        district_id: int, 
        intensity: float = 1.0,
        duration_minutes: int = 30,
        affected_categories: Optional[List[str]] = None
    ) -> dict:
        """Trigger a health storm in a district."""
        
        # Find or create health storm
        stmt = select(HealthStorm).where(HealthStorm.district_id == district_id)
        result = await self.db.execute(stmt)
        storm = result.scalar_one_or_none()
        
        if storm is None:
            storm = HealthStorm(
                code=f"STORM-{district_id}-{int(datetime.utcnow().timestamp())}",
                name=f"Health Storm - District {district_id}",
                district_id=district_id,
                intensity=intensity,
                demand_multiplier=3.0 + (intensity * 2.0),
                affected_medicines=affected_categories or [],
                status="active",
            )
            self.db.add(storm)
            await self.db.flush()
        else:
            storm.intensity = intensity
            storm.demand_multiplier = 3.0 + (intensity * 2.0)
            storm.status = "active"
        
        # Update district risk level
        district = await self.db.get(District, district_id)
        if district:
            # Determine risk level based on intensity
            if intensity >= 1.5:
                new_risk = "red"
            elif intensity >= 1.0:
                new_risk = "orange"
            elif intensity >= 0.5:
                new_risk = "yellow"
            else:
                new_risk = "green"
            
            district.risk_level = new_risk
            district.storm_intensity = intensity
            district.is_health_storm_active = True
            district.current_demand = district.base_demand * storm.demand_multiplier
            district.demand_multiplier = storm.demand_multiplier
        
        # Check for shortages
        await self._check_shortages(district, storm)
        
        # Calculate rerouting needs
        await self._calculate_rerouting(district, storm)
        
        await self.db.flush()
        
        return HealthStormResponse(
            id=storm.id,
            code=storm.code,
            name=storm.name,
            district_id=storm.district_id,
            status=HealthStormStatus(storm.status) if isinstance(storm.status, str) else storm.status,
            intensity=storm.intensity,
            demand_multiplier=storm.demand_multiplier,
            affected_medicines=storm.affected_medicines or [],
            total_shortage_predicted=storm.total_shortage_predicted or 0.0,
            total_rerouted_trucks=storm.total_rerouted_trucks or 0,
            total_supplies_delivered=storm.total_supplies_delivered or 0.0,
            started_at=storm.started_at,
            resolved_at=storm.resolved_at,
            estimated_resolution=storm.estimated_resolution,
            created_at=storm.created_at,
            updated_at=storm.updated_at,
        )
    
    async def _check_shortages(self, district: District, storm: HealthStorm):
        """Check for medicine shortages in the district."""
        
        # Get inventory items for this district
        stmt = select(Inventory).where(Inventory.district_id == district.id)
        result = await self.db.execute(stmt)
        inventories = result.scalars().all()
        
        total_shortage = 0.0
        critical_items = 0
        
        for inv in inventories:
            medicine = await self.db.get(Medicine, inv.medicine_id)
            if not medicine:
                continue
            
            # Calculate shortage
            demand_ratio = district.current_demand / max(inv.quantity, 1)
            
            # If demand exceeds inventory by significant margin
            if demand_ratio > medicine.critical_level / max(inv.min_threshold, 1):
                shortage = district.current_demand - inv.quantity
                if shortage > 0:
                    total_shortage += shortage
                    # Reserve some stock
                    inv.reserved_quantity = min(inv.quantity, inv.reserved_quantity + shortage * 0.3)
                    inv.quantity = max(0, inv.quantity - shortage * 0.3)
                    
                    if shortage > medicine.critical_level:
                        critical_items += 1
        
        # Update storm with shortage data
        storm.total_shortage_predicted = total_shortage
        
        # Record critical inventory events
        if critical_items > 0:
            event = SimulationEvent(
                event_type="shortage_detected",
                entity_type="district",
                entity_id=district.id,
                description=f"Shortage detected: {critical_items} medicine categories critically low",
                data={
                    "total_shortage": total_shortage,
                    "critical_items": critical_items,
                    "district_risk": district.risk_level,
                },
                severity="high" if total_shortage > district.base_demand * 0.5 else "medium",
            )
            self.db.add(event)
    
    async def _calculate_rerouting(self, district: District, storm: HealthStorm):
        """Calculate truck rerouting needs based on shortage."""
        
        # Find nearby warehouses with stock using a simple query
        stmt = select(Warehouse).where(
            Warehouse.is_active == True,
            Warehouse.current_stock > 500
        )
        result = await self.db.execute(stmt)
        warehouses = result.scalars().all() or []
        
        if not warehouses:
            return
        
        # Get truck IDs that home at these warehouses
        warehouse_ids = [w.id for w in warehouses]
        stmt = select(Truck).where(Truck.home_warehouse_id.in_(warehouse_ids))
        result = await self.db.execute(stmt)
        trucks = result.scalars().all() or []
        
        rerouted_count = 0
        
        for truck in trucks:
            # Check if truck should be rerouted to this district
            if truck.status in [TruckStatus.IDLE, TruckStatus.LOADING]:
                # Reroute truck to district
                truck.status = TruckStatus.REROUTING
                truck.is_rerouted = True
                truck.target_latitude = district.latitude
                truck.target_longitude = district.longitude
                rerouted_count += 1
                
                # Record event
                event = SimulationEvent(
                    event_type="truck_rerouted",
                    entity_type="truck",
                    entity_id=truck.id,
                    description=f"Truck rerouted to district {district.id} due to health storm",
                    data={
                        "truck_id": truck.id,
                        "district_id": district.id,
                        "storm_intensity": storm.intensity,
                    },
                    severity="medium",
                )
                self.db.add(event)
        
        storm.total_rerouted_trucks = rerouted_count
        
        # Record rerouting event
        if rerouted_count > 0:
            event = SimulationEvent(
                event_type="network_rerouting_initiated",
                entity_type="network",
                entity_id=district.id,
                description=f"{rerouted_count} trucks rerouted to district {district.id}",
                data={
                    "rerouted_trucks": rerouted_count,
                    "district_risk": district.risk_level,
                    "storm_intensity": storm.intensity,
                },
                severity="high",
            )
            self.db.add(event)
    
    async def resolve_health_storm(self, district_id: int) -> dict:
        """Resolve a health storm and restore normal operations."""
        
        storm = await self.db.get(HealthStorm, district_id)
        if not storm:
            return None
        
        storm.status = "resolved"
        storm.resolved_at = datetime.utcnow()
        
        # Update district back to normal
        district = await self.db.get(District, district_id)
        if district:
            district.risk_level = "green"
            district.is_health_storm_active = False
            district.storm_intensity = 0.0
            district.current_demand = district.base_demand
            district.demand_multiplier = 1.0
            storm.total_shortage_predicted = 0.0
            storm.total_rerouted_trucks = 0
        
        # Release rerouted trucks
        stmt = select(Truck).where(
            Truck.is_rerouted == True,
            Truck.original_route_id.isnot(None)
        )
        result = await self.db.execute(stmt)
        rerouted_trucks = result.scalars().all()
        
        for truck in rerouted_trucks:
            truck.status = TruckStatus.IDLE
            truck.is_rerouted = False
            truck.target_latitude = None
            truck.target_longitude = None
        
        await self.db.flush()
        
        # Record resolution event
        event = SimulationEvent(
            event_type="health_storm_resolved",
            entity_type="district",
            entity_id=district_id,
            description=f"Health storm resolved in district {district_id}",
            data={
                "total_shortage_predicted": storm.total_shortage_predicted or 0.0,
                "total_rerouted_trucks": storm.total_rerouted_trucks or 0,
            },
            severity="info",
        )
        self.db.add(event)
        
        await self.db.flush()
        await self.db.refresh(storm)
        
        return {
            "id": storm.id,
            "district_id": district_id,
            "status": storm.status,
            "total_shortage_predicted": storm.total_shortage_predicted or 0.0,
            "total_rerouted_trucks": storm.total_rerouted_trucks or 0
        }


class NetworkMonitor:
    """Monitors overall network health metrics."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def update_metrics(self) -> dict:
        """Calculate and update network-wide metrics."""
        
        # Total districts
        total_districts = (await self.db.execute(select(District))).scalars().all()
        total_districts_count = len(total_districts) if total_districts else 0
        
        # Critical districts (red risk)
        critical_districts = (await self.db.execute(
            select(District).where(District.risk_level == "red")
        )).scalars().all()
        critical_count = len(critical_districts)
        
        # Active storms
        active_storms = (await self.db.execute(
            select(HealthStorm).where(HealthStorm.status == "active")
        )).scalars().all()
        active_storm_count = len(active_storms)
        
        # Warehouses
        total_warehouses = (await self.db.execute(select(Warehouse).where(Warehouse.is_active == True))).scalars().all()
        active_warehouses = len([w for w in total_warehouses if w.current_stock > 0])
        
        # Hospitals
        total_hospitals = (await self.db.execute(select(Hospital).where(Hospital.is_active == True))).scalars().all()
        
        # Trucks
        all_trucks = (await self.db.execute(select(Truck))).scalars().all()
        active_trucks = len([t for t in all_trucks if t.status in [TruckStatus.IN_TRANSIT, TruckStatus.LOADING]])
        idle_trucks = len([t for t in all_trucks if t.status == TruckStatus.IDLE])
        in_transit_trucks = len([t for t in all_trucks if t.status == TruckStatus.IN_TRANSIT])
        rerouted_trucks = len([t for t in all_trucks if t.is_rerouted])
        
        # Shipments
        all_shipments = (await self.db.execute(select(Shipment))).scalars().all()
        pending_shipments = len([s for s in all_shipments if s.status == "pending"])
        in_transit_shipments = len([s for s in all_shipments if s.status == "in_transit"])
        delivered_shipments = len([s for s in all_shipments if s.status == "delivered"])
        
        # Inventory metrics
        all_inventory = (await self.db.execute(select(Inventory))).scalars().all()
        total_inventory = sum(i.quantity for i in all_inventory)
        critical_inventory = len([i for i in all_inventory if i.quantity < i.min_threshold])
        
        # Calculate network health score (0-100)
        health_score = 100.0
        if active_storm_count > 0:
            health_score -= active_storm_count * 15.0
        if critical_count > 0:
            health_score -= critical_count * 10.0
        if critical_inventory > 0:
            health_score -= critical_inventory * 2.0
        if rerouted_trucks > 0:
            health_score -= min(20.0, rerouted_trucks * 3.0)
        
        health_score = max(0.0, min(100.0, health_score))
        
        return {
            "total_districts": total_districts_count,
            "critical_districts": critical_count,
            "active_storms": active_storm_count,
            "total_warehouses": len(total_warehouses),
            "active_warehouses": active_warehouses,
            "total_hospitals": len(total_hospitals),
            "active_trucks": active_trucks,
            "idle_trucks": idle_trucks,
            "in_transit_trucks": in_transit_trucks,
            "rerouted_trucks": rerouted_trucks,
            "pending_shipments": pending_shipments,
            "in_transit_shipments": in_transit_shipments,
            "delivered_shipments": delivered_shipments,
            "total_inventory": round(total_inventory, 2),
            "critical_inventory_items": critical_inventory,
            "network_health_score": round(health_score, 2)
        }


class RouteCalculator:
    """Calculates routes between locations."""
    
    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance in km between two points."""
        from geopy.distance import geodesic
        try:
            return geodesic((lat1, lon1), (lat2, lon2)).km
        except Exception:
            return 0.0
    
    @staticmethod
    def calculate_route(
        origin_lat: float, origin_lon: float,
        dest_lat: float, dest_lon: float,
        waypoints: Optional[List[tuple]] = None
    ) -> dict:
        """Calculate a route with optional waypoints."""
        distance = RouteCalculator.calculate_distance(origin_lat, origin_lon, dest_lat, dest_lon)
        estimated_time = distance / 40.0 if distance > 0 else 0.0
        
        return {
            "distance_km": round(distance, 2),
            "estimated_time_hours": round(estimated_time, 2),
            "path_coordinates": [[origin_lat, origin_lon], [dest_lat, dest_lon]]
        }