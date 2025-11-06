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
    precio_unit: float = Field(..., ge=0)


# --- ORDER ---
class Order(BaseModel):
    id: Optional[str] = None
    cliente_id: str
    fecha: datetime
    canal: Canal
    moneda: Moneda
    total: float = Field(..., ge=0)
    items: List[Item] = Field(..., min_items=1)
