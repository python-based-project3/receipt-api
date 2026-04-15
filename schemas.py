from pydantic import BaseModel
from datetime import date
from datetime import datetime
from decimal import Decimal
from typing import Optional, Any
from models import StorageType

# --- Category Schemas ---
class CategoryBase(BaseModel):
    name: str

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    id: int

    class Config:
        from_attributes = True

# --- Ingredient Schemas ---
class IngredientBase(BaseModel):
    name: str
    quantity: int
    unit: str
    expiration_date: date
    storage_type: StorageType
    category_id: Optional[int] = None

class IngredientCreate(IngredientBase):
    pass

class IngredientUpdate(BaseModel):
    name: Optional[str] = None
    quantity: Optional[int] = None
    unit: Optional[str] = None
    expiration_date: Optional[date] = None
    storage_type: Optional[StorageType] = None
    category_id: Optional[int] = None

class Ingredient(IngredientBase):
    id: int

    class Config:
        from_attributes = True


class ReceiptItemBase(BaseModel):
    name: str
    quantity: Decimal = Decimal("1")
    unit_price: Optional[Decimal] = None
    line_total: Optional[Decimal] = None


class ReceiptItemCreate(ReceiptItemBase):
    pass


class ReceiptItem(ReceiptItemBase):
    id: int

    class Config:
        from_attributes = True


class ReceiptBase(BaseModel):
    store_name: Optional[str] = None
    receipt_date: Optional[datetime] = None
    total_amount: Optional[Decimal] = None
    currency: str = "KRW"
    image_path: str
    raw_text: str
    raw_ocr: Optional[Any] = None


class ReceiptCreate(ReceiptBase):
    items: list[ReceiptItemCreate] = []


class Receipt(ReceiptBase):
    id: int
    created_at: datetime
    items: list[ReceiptItem] = []

    class Config:
        from_attributes = True
