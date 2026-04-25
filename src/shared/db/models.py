"""Shared SQLAlchemy ORM models for AzL Pools."""

from datetime import datetime
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text,
    create_engine
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True)
    parcel_id = Column(String(50), unique=True, nullable=False)
    address = Column(Text, nullable=False)
    city = Column(String(100))
    county = Column(String(100))
    state = Column(String(2), default="FL")
    zip = Column(String(10))
    owner_name = Column(Text)
    mailing_address = Column(Text)
    avm_value = Column(Numeric(12, 2))
    lot_sqft = Column(Integer)
    living_sqft = Column(Integer)
    year_built = Column(Integer)
    bedrooms = Column(Integer)
    bathrooms = Column(Numeric(3, 1))
    has_pool = Column(Boolean, default=None)
    pool_detected = Column(Boolean, default=None)
    latitude = Column(Numeric(10, 7))
    longitude = Column(Numeric(10, 7))
    ingested_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    analyses = relationship("PoolAnalysis", back_populates="property")
    designs = relationship("PoolDesign", back_populates="property")
    contacts = relationship("Contact", back_populates="property")


class PoolAnalysis(Base):
    __tablename__ = "pool_analysis"

    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"))
    image_url = Column(Text)
    detection_score = Column(Numeric(5, 4))
    has_pool = Column(Boolean)
    analyzed_at = Column(DateTime, default=datetime.utcnow)

    property = relationship("Property", back_populates="analyses")


class PoolDesign(Base):
    __tablename__ = "pool_designs"

    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"))
    design_params = Column(JSONB)
    design_output = Column(JSONB)
    render_path = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    property = relationship("Property", back_populates="designs")


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"))
    owner_name = Column(Text)
    mailing_address = Column(Text)
    phone = Column(Text)
    email = Column(Text)
    enrichment_src = Column(String(50))
    enriched_at = Column(DateTime, default=datetime.utcnow)

    property = relationship("Property", back_populates="contacts")
    outreach_items = relationship("Outreach", back_populates="contact")


class Outreach(Base):
    __tablename__ = "outreach"

    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey("contacts.id", ondelete="CASCADE"))
    design_id = Column(Integer, ForeignKey("pool_designs.id", ondelete="SET NULL"))
    channel = Column(String(20))
    status = Column(String(20), default="pending")
    sent_at = Column(DateTime)
    response = Column(Text)

    contact = relationship("Contact", back_populates="outreach_items")
    design = relationship("PoolDesign")


def get_engine(database_url: str):
    return create_engine(database_url)
