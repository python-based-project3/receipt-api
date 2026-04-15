from sqlalchemy import Column, Integer, String, Date, ForeignKey, Enum, DateTime, Numeric, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from database import Base

class StorageType(enum.Enum):
    FRIDGE = "FRIDGE"       # 냉장
    FREEZER = "FREEZER"     # 냉동
    PANTRY = "PANTRY"       # 실온

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False) # 유제품, 채소, 육류..
    
    # Category와 Ingredient 간 1:N
    ingredients = relationship("Ingredient", back_populates="category")

class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True, nullable=False)      # 식재료 이름
    quantity = Column(Integer, nullable=False, default=1)       # 수량
    unit = Column(String(20), nullable=False)                   # 단위 (개, g, ml)
    expiration_date = Column(Date, nullable=False)              # 유통기한/소비기한
    storage_type = Column(Enum(StorageType), nullable=False)    # 보관 장소 (냉장, 냉동, 실온)
    
    # Category에 대한 외래 키
    category_id = Column(Integer, ForeignKey("categories.id"))
    
    # 관계 설정
    category = relationship("Category", back_populates="ingredients")


class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, index=True)
    store_name = Column(String(255), nullable=True, index=True)
    receipt_date = Column(DateTime, nullable=True, index=True)
    total_amount = Column(Numeric(12, 2), nullable=True)
    currency = Column(String(10), nullable=False, default="KRW")
    image_path = Column(String(500), nullable=False)
    raw_text = Column(Text, nullable=False)
    raw_ocr = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    items = relationship(
        "ReceiptItem",
        back_populates="receipt",
        cascade="all, delete-orphan",
    )


class ReceiptItem(Base):
    __tablename__ = "receipt_items"

    id = Column(Integer, primary_key=True, index=True)
    receipt_id = Column(Integer, ForeignKey("receipts.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False, default=1)
    unit_price = Column(Numeric(12, 2), nullable=True)
    line_total = Column(Numeric(12, 2), nullable=True)

    receipt = relationship("Receipt", back_populates="items")
