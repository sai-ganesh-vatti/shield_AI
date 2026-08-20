import asyncio
import random
from datetime import datetime, timedelta

from sqlalchemy import select
from app.core.database import async_session_maker, engine, Base, init_db
from app.models import (
    District, Warehouse, Hospital, Medicine, Inventory, Truck, Route,
    Shipment, HealthStorm, RiskLevel, TruckStatus, ShipmentStatus,
    HealthStormStatus
)


async def init_db_and_seed():
    """Initialize database and seed with default data."""
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Check if data already exists
    async with async_session_maker() as db:
        stmt = select(District).limit(1)
        result = await db.execute(stmt)
        if result.scalar() is not None:
            print("Data already seeded, skipping...")
            return
    
    print("Seeding default data...")
    
    # Create districts
    districts_data = [
        {"code": "DL01", "name": "New Delhi", "state": "Delhi", "lat": 28.7041, "lon": 77.1025, "population": 18000000},
        {"code": "MH01", "name": "Mumbai", "state": "Maharashtra", "lat": 19.0761, "lon": 72.8777, "population": 20000000},
        {"code": "TN01", "name": "Chennai", "state": "Tamil Nadu", "lat": 13.0827, "lon": 80.2707, "population": 7100000},
    ]
    
    created_districts = []
    async with async_session_maker() as db:
        for d in districts_data:
            district = District(
                code=d["code"],
                name=d["name"],
                state=d["state"],
                latitude=d["lat"],
                longitude=d["lon"],
                population=d["population"],
                risk_level=RiskLevel.GREEN,
                base_demand=100.0,
                current_demand=100.0,
            )
            db.add(district)
            created_districts.append(district)
        await db.commit()
        await db.flush()
        
        # Create warehouses
        for district in created_districts:
            warehouse = Warehouse(
                code=f"WH-{district.code}-01",
                name=f"Warehouse {district.code}-01",
                district_id=district.id,
                latitude=district.latitude,
                longitude=district.longitude,
                capacity=10000.0,
                current_stock=5000.0,
                warehouse_type="central",
            )
            db.add(warehouse)
        
        # Create hospitals
        for district in created_districts:
            hospital = Hospital(
                code=f"H-{district.code}-01",
                name=f"Hospital {district.code}-01",
                district_id=district.id,
                latitude=district.latitude,
                longitude=district.longitude,
                bed_capacity=200,
                hospital_type="general",
            )
            db.add(hospital)
        
        # Create medicines
        medicines_data = [
            {"code": "PARA-001", "name": "Paracetamol", "category": "analgesic", "unit": "tablets", "critical_level": 500, "requires_cold_chain": False},
            {"code": "IBUP-001", "name": "Ibuprofen", "category": "analgesic", "unit": "tablets", "critical_level": 300, "requires_cold_chain": False},
        ]
        
        created_medicines = []
        for m in medicines_data:
            medicine = Medicine(
                code=m["code"],
                name=m["name"],
                category=m["category"],
                unit=m["unit"],
                critical_level=m["critical_level"],
                requires_cold_chain=m["requires_cold_chain"],
            )
            db.add(medicine)
            created_medicines.append(medicine)
        
        # Create inventory
        for warehouse in (await db.execute(select(Warehouse))).scalars().all():
            for medicine in created_medicines:
                inventory = Inventory(
                    medicine_id=medicine.id,
                    warehouse_id=warehouse.id,
                    district_id=warehouse.district_id,
                    quantity=1000.0,
                    min_threshold=medicine.critical_level,
                    max_threshold=5000.0,
                )
                db.add(inventory)
        
        await db.commit()
        print("Seed data created successfully!")


async def main():
    await init_db_and_seed()


if __name__ == "__main__":
    asyncio.run(main())
