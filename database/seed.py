"""
seed.py
=======
Seed the database with Store and Product master data.
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from database.connection import SessionLocal, create_all_tables
from database.models import Store, Product
from config.constants import STORE_NAMES, ITEM_CATEGORIES
from config.logging_config import get_logger

logger = get_logger(__name__)

WAREHOUSES = [
    "Hyderabad Central WH", "Mumbai Metro WH", "Delhi North WH",
    "Bangalore South WH", "Chennai East WH", "Kolkata West WH",
    "Pune City WH", "Ahmedabad Hub WH", "Jaipur Royal WH",
    "Surat Diamond WH",
]

SUPPLIERS = [
    "FreshCo Distributors", "Metro Supply Chain", "AgriFirst Ltd",
    "GlobalFoods Inc", "QuickShip Logistics",
]

CITIES = [
    "Hyderabad", "Mumbai", "Delhi", "Bangalore", "Chennai",
    "Kolkata", "Pune", "Ahmedabad", "Jaipur", "Surat",
]

REAL_ITEM_NAMES = [
    'Whole Milk',      'Butter',         'Cheddar Cheese',  'Yogurt',         'Cream',
    'Orange Juice',    'Apple Juice',    'Mango Juice',     'Cola 2L',        'Green Tea',
    'Potato Chips',   'Popcorn',       'Biscuits',       'Cookies',       'Crackers',
    'Rice 5kg',       'Wheat Flour',   'Sugar 1kg',      'Salt 500g',     'Cooking Oil',
    'Frozen Pizza',   'Frozen Peas',   'Ice Cream',      'Frozen Chicken','Frozen Fish',
    'Shampoo 200ml',  'Conditioner',   'Soap Bar',       'Toothpaste',    'Body Lotion',
    'Dishwash Liquid','Laundry Powder','Floor Cleaner',  'Toilet Paper',  'Paper Towels',
    'White Bread',    'Brown Bread',   'Croissant',      'Bagel',         'Sourdough',
    'Banana 1kg',     'Apple 1kg',     'Tomato 500g',    'Spinach',       'Carrot 500g',
    'Chicken Breast', 'Beef Mince',    'Pork Ribs',      'Lamb Chops',    'Tuna Can',
]


def seed_stores(db) -> int:
    """Insert Store master records if they do not already exist."""
    inserted = 0
    for i, name in enumerate(STORE_NAMES, start=1):
        existing = db.query(Store).filter(Store.store_code == i).first()
        if existing is None:
            store = Store(
                store_code=i,
                name=name,
                city=CITIES[i - 1],
                region="India",
                warehouse=WAREHOUSES[(i - 1) % len(WAREHOUSES)],
                is_active=True,
            )
            db.add(store)
            inserted += 1
        else:
            # Update name if it is generic
            if existing.name != name:
                existing.name = name
                db.add(existing)
    db.commit()
    logger.info("Stores seeded: %d new records inserted.", inserted)
    return len(STORE_NAMES)


def seed_products(db) -> int:
    """Insert Product master records if they do not already exist."""
    inserted = 0
    for i, name in enumerate(REAL_ITEM_NAMES, start=1):
        existing = db.query(Product).filter(Product.item_code == i).first()
        if existing is None:
            category = ITEM_CATEGORIES[(i - 1) % len(ITEM_CATEGORIES)]
            base_price = round(50 + (i * 7) % 450, 2)
            product = Product(
                item_code=i,
                name=name,
                category=category,
                supplier=SUPPLIERS[(i - 1) % len(SUPPLIERS)],
                base_price=base_price,
                is_active=True,
            )
            db.add(product)
            inserted += 1
        else:
            # Update name to real name
            if existing.name != name:
                existing.name = name
                db.add(existing)
    db.commit()
    logger.info("Products seeded: %d new records inserted.", inserted)
    return len(REAL_ITEM_NAMES)


def run_seed() -> None:
    """Orchestrate full database seeding."""
    logger.info("Starting database seed ...")
    create_all_tables()

    with SessionLocal() as db:
        stores   = seed_stores(db)
        products = seed_products(db)

    logger.info("Seed complete — %d stores, %d products.", stores, products)
    print(f"Seed complete: {stores} stores and {products} products.")


if __name__ == "__main__":
    run_seed()
