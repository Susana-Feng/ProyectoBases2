from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import datetime


# Enums for canal and moneda
class Canal(str, Enum):
    WEB = "WEB"
    TIENDA = "TIENDA"


class Moneda(str, Enum):
    CRC = "CRC"


# Item schema
class Item(BaseModel):
    producto_id: str
    cantidad: int = Field(..., ge=1)
    precio_unit: int = Field(..., ge=0)


# Metadatos schema
class Metadatos(BaseModel):
    cupon: Optional[str] = None


# Order schema
class order(BaseModel):
    cliente_id: str
    fecha: datetime
    canal: Canal
    moneda: Moneda
    total: int = Field(..., ge=0)
    items: List[Item] = Field(..., min_items=1)
    metadatos: Optional[Metadatos] = None
