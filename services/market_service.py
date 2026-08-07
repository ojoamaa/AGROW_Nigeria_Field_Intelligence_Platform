from datetime import datetime
from typing import Optional

import pandas as pd
from sqlalchemy import text

from core.db import get_engine

engine = get_engine()


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def create_market_listing(
    farmer_id: str,
    commodity: str,
    product: str,
    quantity: float,
    unit: str,
    price: float,
    ready_date: str,
    state: str,
    lga: str,
    community: str,
    description: str,
    created_by: str,
) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO market_listings (
                    farmer_id, commodity, product, quantity, available_quantity, unit,
                    price, ready_date, state, lga, community, description, status,
                    created_by, created_at, updated_at
                ) VALUES (
                    :farmer_id, :commodity, :product, :quantity, :quantity, :unit,
                    :price, :ready_date, :state, :lga, :community, :description, 'AVAILABLE',
                    :created_by, :created_at, :updated_at
                )
                """
            ),
            dict(
                farmer_id=farmer_id,
                commodity=commodity,
                product=product,
                quantity=float(quantity),
                unit=unit,
                price=float(price),
                ready_date=ready_date,
                state=state,
                lga=lga,
                community=community,
                description=description,
                created_by=created_by,
                created_at=_now(),
                updated_at=_now(),
            ),
        )


def fetch_market_listings(status: Optional[str] = None) -> pd.DataFrame:
    where = ""
    params = {}
    if status:
        where = "WHERE ml.status=:status"
        params["status"] = status
    return pd.read_sql_query(
        text(
            f"""
            SELECT
                ml.*,
                f.farmer_full_name,
                f.phone_number,
                f.nin_status,
                f.photo_path,
                f.primary_crop,
                f.latitude,
                f.longitude
            FROM market_listings ml
            LEFT JOIN farmers f ON f.farmer_id = ml.farmer_id
            {where}
            ORDER BY ml.created_at DESC
            """
        ),
        engine,
        params=params,
    )


def update_listing_status(listing_id: int, status: str) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                "UPDATE market_listings SET status=:status, updated_at=:updated_at WHERE id=:id"
            ),
            dict(status=status, updated_at=_now(), id=int(listing_id)),
        )


def create_input_product(
    supplier_name: str,
    supplier_phone: str,
    category: str,
    product_name: str,
    applicable_commodities: str,
    quantity: float,
    unit: str,
    price: float,
    state: str,
    lga: str,
    description: str,
    created_by: str,
) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO input_products (
                    supplier_name, supplier_phone, category, product_name,
                    applicable_commodities, quantity, unit, price, state, lga,
                    description, status, created_by, created_at, updated_at
                ) VALUES (
                    :supplier_name, :supplier_phone, :category, :product_name,
                    :applicable_commodities, :quantity, :unit, :price, :state, :lga,
                    :description, 'AVAILABLE', :created_by, :created_at, :updated_at
                )
                """
            ),
            dict(
                supplier_name=supplier_name,
                supplier_phone=supplier_phone,
                category=category,
                product_name=product_name,
                applicable_commodities=applicable_commodities,
                quantity=float(quantity),
                unit=unit,
                price=float(price),
                state=state,
                lga=lga,
                description=description,
                created_by=created_by,
                created_at=_now(),
                updated_at=_now(),
            ),
        )


def fetch_input_products(status: Optional[str] = None) -> pd.DataFrame:
    where = ""
    params = {}
    if status:
        where = "WHERE status=:status"
        params["status"] = status
    return pd.read_sql_query(
        text(
            f"""
            SELECT * FROM input_products
            {where}
            ORDER BY created_at DESC
            """
        ),
        engine,
        params=params,
    )


def update_input_status(product_id: int, status: str) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                "UPDATE input_products SET status=:status, updated_at=:updated_at WHERE id=:id"
            ),
            dict(status=status, updated_at=_now(), id=int(product_id)),
        )


def create_market_enquiry(
    listing_id: int,
    buyer_name: str,
    buyer_phone: str,
    quantity_requested: float,
    message: str,
) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO market_enquiries (
                    listing_id, buyer_name, buyer_phone, quantity_requested,
                    message, status, created_at
                ) VALUES (
                    :listing_id, :buyer_name, :buyer_phone, :quantity_requested,
                    :message, 'NEW', :created_at
                )
                """
            ),
            dict(
                listing_id=int(listing_id),
                buyer_name=buyer_name,
                buyer_phone=buyer_phone,
                quantity_requested=float(quantity_requested),
                message=message,
                created_at=_now(),
            ),
        )


def fetch_market_enquiries() -> pd.DataFrame:
    return pd.read_sql_query(
        text(
            """
            SELECT me.*, ml.farmer_id, ml.commodity, ml.product
            FROM market_enquiries me
            JOIN market_listings ml ON ml.id=me.listing_id
            ORDER BY me.created_at DESC
            """
        ),
        engine,
    )
