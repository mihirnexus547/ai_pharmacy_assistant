"""
SQLAlchemy ORM models for the AI Pharmacy Assistant.
"""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.database import Base


# ==========================================================
# Enum
# ==========================================================

class OrderStatus(str, enum.Enum):
    """Available order statuses."""

    RESERVED = "Reserved"
    COLLECTED = "Collected"
    CANCELLED = "Cancelled"


# ==========================================================
# Medicine Model
# ==========================================================

class Medicine(Base):
    """Represents a medicine available in the pharmacy."""

    __tablename__ = "medicines"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    generic_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    strength: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    manufacturer: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    price: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    stock: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    orders: Mapped[list["Order"]] = relationship(
        back_populates="medicine",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Medicine(name={self.name}, stock={self.stock})>"


# ==========================================================
# Customer Model
# ==========================================================

class Customer(Base):
    """Represents a pharmacy customer."""

    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    phone: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # Relationships
    orders: Mapped[list["Order"]] = relationship(
        back_populates="customer",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Customer(name={self.name})>"


# ==========================================================
# Order Model
# ==========================================================

class Order(Base):
    """Represents a medicine reservation."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"),
        nullable=False,
    )

    medicine_id: Mapped[int] = mapped_column(
        ForeignKey("medicines.id"),
        nullable=False,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus),
        default=OrderStatus.RESERVED,
        nullable=False,
    )

    reserved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # Relationships
    customer: Mapped["Customer"] = relationship(
        back_populates="orders",
    )

    medicine: Mapped["Medicine"] = relationship(
        back_populates="orders",
    )

    def __repr__(self) -> str:
        return (
            f"<Order(id={self.id}, "
            f"medicine={self.medicine_id}, "
            f"quantity={self.quantity})>"
        )