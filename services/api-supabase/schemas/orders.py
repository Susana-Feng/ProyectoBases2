from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import datetime


# --- ENUMS ---
class Genero(str, Enum):
    M = "M"
    F = "F"


class Moneda(str, Enum):
    CRC = "CRC"
    USD = "USD"


class Canal(str, Enum):
    WEB = "WEB"
    APP = "APP"
    PARTNER = "PARTNER"

# --- PAGINATION PARAMS ---
class PaginationParams(BaseModel):
    offset: int = Field(0, ge=0)
    limit: int = Field(10, ge=1, le=100)


# --- CLIENTE ---
class Client(BaseModel):
    id: Optional[str] = None
    nombre: str
    email: Optional[str] = None
    genero: Genero
    pais: str
    fecha_registro: Optional[datetime] = None


# --- PRODUCTO ---
class Product(BaseModel):
    id: Optional[str] = None
    sku: Optional[str] = None
    nombre: str
    categoria: str


# --- ITEM ---
class Item(BaseModel):
    producto_id: str
    cantidad: int = Field(..., ge=1)
    precio_unitario: float = Field(..., ge=0)


# --- ORDER ---
class Order(BaseModel):
    cliente_id: str
    fecha: datetime
    canal: Canal
    moneda: Moneda
    items: List[Item] = Field(..., min_items=1)
