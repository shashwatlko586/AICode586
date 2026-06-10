"""Pydantic schemas for layout plan JSON output."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ZoneType(str, Enum):
    DECOMPRESSION = "decompression_zone"
    POWER_WALL = "power_wall"
    CIRCULATION = "circulation_path"
    MERCHANDISING = "merchandising"
    EXPERIENCE = "experience_zone"
    CHECKOUT = "checkout"
    SERVICE = "service_desk"
    BOPIS = "bopis_pickup"
    STORAGE = "storage"


class FixturePlacement(BaseModel):
    fixture_id: str = Field(description="Catalog fixture ID e.g. BRV-FX-HP03")
    fixture_name: str
    x_m: float = Field(ge=0, description="X position in meters from entrance")
    y_m: float = Field(ge=0, description="Y position in meters")
    width_m: float = Field(gt=0)
    depth_m: float = Field(gt=0)
    rotation_deg: float = 0
    notes: Optional[str] = None


class LayoutZone(BaseModel):
    zone_type: ZoneType
    name: str
    x_m: float
    y_m: float
    width_m: float
    depth_m: float
    priority_products: list[str] = Field(default_factory=list)
    compliance_notes: list[str] = Field(default_factory=list)


class ComplianceCheck(BaseModel):
    source_document: str
    requirement: str
    status: str = Field(description="pass | warn | fail")
    detail: str


class LayoutPlan(BaseModel):
    store_name: str
    city: str
    floor_area_sqm: float
    entrance_side: str = "south"
    zones: list[LayoutZone]
    fixtures: list[FixturePlacement]
    trending_products: list[str] = Field(default_factory=list)
    design_rationale: str
    compliance_checks: list[ComplianceCheck] = Field(default_factory=list)
