"""
models.py  (database layer)
============================
SQLAlchemy ORM models for the Retail Demand Forecasting application.

Tables
------
- Store          : retail store master data
- Product        : product / item master data
- Sale           : daily historical sales (fact table)
- User           : application users (admin / analyst)
- Forecast       : stored forecast results
- PredictionLog  : audit trail for every prediction request
- ModelMetadata  : registry of trained model artefacts

Design notes
------------
- All primary keys are auto-incrementing integers.
- Foreign-key constraints are enforced at the ORM level.
- Timestamps use UTC.
- The schema is normalised to 3NF to support future expansion.
"""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# ---------------------------------------------------------------------------
# Base class — all models inherit from this
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    """Declarative base shared by all ORM models."""
    pass


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------
class UserRole(str, enum.Enum):
    """Application user roles."""
    ADMIN  = "admin"
    USER   = "user"


class ModelStatus(str, enum.Enum):
    """Training / evaluation status for a model artefact."""
    PENDING   = "pending"
    TRAINING  = "training"
    READY     = "ready"
    FAILED    = "failed"


class ForecastStatus(str, enum.Enum):
    """Status of a forecast generation request."""
    PENDING   = "pending"
    SUCCESS   = "success"
    FAILED    = "failed"


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------
class Store(Base):
    """
    Master table for retail stores.
    One row per physical or logical store location.
    """

    __tablename__ = "stores"

    id: Mapped[int]         = mapped_column(Integer, primary_key=True, index=True)
    store_code: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    name: Mapped[str]       = mapped_column(String(200), nullable=False)
    city: Mapped[str | None]        = mapped_column(String(100))
    region: Mapped[str | None]      = mapped_column(String(100))
    warehouse: Mapped[str | None]   = mapped_column(String(100))
    is_active: Mapped[bool]         = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime]    = mapped_column(DateTime, server_default=func.now())

    # Relationships
    sales: Mapped[list["Sale"]]         = relationship("Sale",     back_populates="store")
    forecasts: Mapped[list["Forecast"]] = relationship("Forecast", back_populates="store")

    def __repr__(self) -> str:
        return f"<Store id={self.store_code} name={self.name!r}>"


# ---------------------------------------------------------------------------
# Product
# ---------------------------------------------------------------------------
class Product(Base):
    """
    Master table for products / items sold across stores.
    One row per SKU.
    """

    __tablename__ = "products"

    id: Mapped[int]          = mapped_column(Integer, primary_key=True, index=True)
    item_code: Mapped[int]   = mapped_column(Integer, unique=True, nullable=False)
    name: Mapped[str]        = mapped_column(String(200), nullable=False)
    category: Mapped[str | None]   = mapped_column(String(100))
    supplier: Mapped[str | None]   = mapped_column(String(200))
    base_price: Mapped[float | None] = mapped_column(Float)
    is_active: Mapped[bool]        = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime]   = mapped_column(DateTime, server_default=func.now())

    # Relationships
    sales: Mapped[list["Sale"]]         = relationship("Sale",     back_populates="product")
    forecasts: Mapped[list["Forecast"]] = relationship("Forecast", back_populates="product")

    def __repr__(self) -> str:
        return f"<Product item_code={self.item_code} name={self.name!r}>"


# ---------------------------------------------------------------------------
# Sale  (fact table)
# ---------------------------------------------------------------------------
class Sale(Base):
    """
    Daily sales fact table.
    Each row records observed sales for one Store × Item × Date combination.
    """

    __tablename__ = "sales"
    __table_args__ = (
        UniqueConstraint("store_id", "product_id", "date", name="uq_sale_store_item_date"),
        Index("ix_sale_date", "date"),
        Index("ix_sale_store_item", "store_id", "product_id"),
    )

    id: Mapped[int]           = mapped_column(Integer, primary_key=True, index=True)
    store_id: Mapped[int]     = mapped_column(ForeignKey("stores.id"),   nullable=False)
    product_id: Mapped[int]   = mapped_column(ForeignKey("products.id"), nullable=False)
    date: Mapped[datetime]    = mapped_column(DateTime, nullable=False)
    sales: Mapped[int]        = mapped_column(Integer, nullable=False)
    promotion: Mapped[bool]   = mapped_column(Boolean, default=False)
    holiday: Mapped[bool]     = mapped_column(Boolean, default=False)
    festival: Mapped[bool]    = mapped_column(Boolean, default=False)
    weekend: Mapped[bool]     = mapped_column(Boolean, default=False)
    temperature: Mapped[float | None] = mapped_column(Float)
    rainfall: Mapped[float | None]    = mapped_column(Float)
    inventory: Mapped[int | None]     = mapped_column(Integer)
    price: Mapped[float | None]       = mapped_column(Float)
    discount: Mapped[float | None]    = mapped_column(Float)

    # Relationships
    store:   Mapped["Store"]   = relationship("Store",   back_populates="sales")
    product: Mapped["Product"] = relationship("Product", back_populates="sales")

    def __repr__(self) -> str:
        return f"<Sale store={self.store_id} item={self.product_id} date={self.date} sales={self.sales}>"


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------
class User(Base):
    """
    Application user with role-based access control.
    Passwords are stored as bcrypt hashes (never plaintext).
    """

    __tablename__ = "users"

    id: Mapped[int]              = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str]        = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[str]           = mapped_column(String(200), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole]       = mapped_column(Enum(UserRole), default=UserRole.USER)
    is_active: Mapped[bool]      = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_login: Mapped[datetime | None] = mapped_column(DateTime)

    # Relationships
    prediction_logs: Mapped[list["PredictionLog"]] = relationship(
        "PredictionLog", back_populates="user"
    )
    forecasts: Mapped[list["Forecast"]] = relationship(
        "Forecast", back_populates="user"
    )

    def __repr__(self) -> str:
        return f"<User username={self.username!r} role={self.role}>"


# ---------------------------------------------------------------------------
# Forecast
# ---------------------------------------------------------------------------
class Forecast(Base):
    """
    Stores generated forecast results.
    JSON columns hold the per-day predicted values and confidence intervals.
    """

    __tablename__ = "forecasts"
    __table_args__ = (
        Index("ix_forecast_store_item", "store_id", "product_id"),
        Index("ix_forecast_created", "created_at"),
    )

    id: Mapped[int]             = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    store_id: Mapped[int]       = mapped_column(ForeignKey("stores.id"),   nullable=False)
    product_id: Mapped[int]     = mapped_column(ForeignKey("products.id"), nullable=False)
    model_name: Mapped[str]     = mapped_column(String(100), nullable=False)
    horizon: Mapped[int]        = mapped_column(Integer, nullable=False)
    forecast_dates: Mapped[dict]     = mapped_column(JSON, nullable=False)   # list[str]
    predicted_sales: Mapped[dict]    = mapped_column(JSON, nullable=False)   # list[float]
    lower_bound: Mapped[dict | None] = mapped_column(JSON)                   # list[float]
    upper_bound: Mapped[dict | None] = mapped_column(JSON)                   # list[float]
    mae: Mapped[float | None]   = mapped_column(Float)
    rmse: Mapped[float | None]  = mapped_column(Float)
    mape: Mapped[float | None]  = mapped_column(Float)
    status: Mapped[ForecastStatus] = mapped_column(
        Enum(ForecastStatus), default=ForecastStatus.SUCCESS
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    user:    Mapped["User | None"] = relationship("User",    back_populates="forecasts")
    store:   Mapped["Store"]       = relationship("Store",   back_populates="forecasts")
    product: Mapped["Product"]     = relationship("Product", back_populates="forecasts")

    def __repr__(self) -> str:
        return (
            f"<Forecast store={self.store_id} item={self.product_id} "
            f"horizon={self.horizon} model={self.model_name!r}>"
        )


# ---------------------------------------------------------------------------
# PredictionLog  (audit trail)
# ---------------------------------------------------------------------------
class PredictionLog(Base):
    """
    Audit log capturing every prediction request received by the API.
    Useful for monitoring, debugging, and billing.
    """

    __tablename__ = "prediction_logs"
    __table_args__ = (
        Index("ix_log_user", "user_id"),
        Index("ix_log_created", "created_at"),
    )

    id: Mapped[int]              = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None]  = mapped_column(ForeignKey("users.id"))
    store_code: Mapped[int]      = mapped_column(Integer, nullable=False)
    item_code: Mapped[int]       = mapped_column(Integer, nullable=False)
    model_name: Mapped[str]      = mapped_column(String(100), nullable=False)
    horizon: Mapped[int]         = mapped_column(Integer, nullable=False)
    status: Mapped[str]          = mapped_column(String(20), default="success")
    error_message: Mapped[str | None] = mapped_column(Text)
    response_time_ms: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    user: Mapped["User | None"] = relationship("User", back_populates="prediction_logs")

    def __repr__(self) -> str:
        return f"<PredictionLog id={self.id} status={self.status!r}>"


# ---------------------------------------------------------------------------
# ModelMetadata
# ---------------------------------------------------------------------------
class ModelMetadata(Base):
    """
    Registry of trained model artefacts.
    Tracks version, file paths, hyper-parameters, and evaluation metrics.
    """

    __tablename__ = "model_metadata"
    __table_args__ = (
        Index("ix_meta_model_name", "model_name"),
    )

    id: Mapped[int]           = mapped_column(Integer, primary_key=True, index=True)
    model_name: Mapped[str]   = mapped_column(String(100), nullable=False)
    version: Mapped[str]      = mapped_column(String(50), nullable=False)
    store_code: Mapped[int | None]  = mapped_column(Integer)   # None = global model
    item_code: Mapped[int | None]   = mapped_column(Integer)
    file_path: Mapped[str]          = mapped_column(String(500), nullable=False)
    scaler_path: Mapped[str | None] = mapped_column(String(500))
    encoder_path: Mapped[str | None]= mapped_column(String(500))
    hyperparameters: Mapped[dict | None] = mapped_column(JSON)
    mae: Mapped[float | None]   = mapped_column(Float)
    rmse: Mapped[float | None]  = mapped_column(Float)
    mape: Mapped[float | None]  = mapped_column(Float)
    r2: Mapped[float | None]    = mapped_column(Float)
    training_time_s: Mapped[float | None] = mapped_column(Float)
    status: Mapped[ModelStatus] = mapped_column(
        Enum(ModelStatus), default=ModelStatus.READY
    )
    is_best: Mapped[bool]       = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime]= mapped_column(DateTime, server_default=func.now())
    trained_at: Mapped[datetime | None] = mapped_column(DateTime)

    def __repr__(self) -> str:
        return (
            f"<ModelMetadata model={self.model_name!r} "
            f"version={self.version!r} status={self.status}>"
        )
