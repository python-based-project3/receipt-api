from sqlalchemy.orm import Session
import models
import schemas
from typing import Optional

# === CATEGORY CRUD ===

def get_category(db: Session, category_id: int):
    return db.query(models.Category).filter(models.Category.id == category_id).first()

def get_categories(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Category).offset(skip).limit(limit).all()

def create_category(db: Session, category: schemas.CategoryCreate):
    db_category = models.Category(name=category.name)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

# === INGREDIENT CRUD ===

def get_ingredient(db: Session, ingredient_id: int):
    return db.query(models.Ingredient).filter(models.Ingredient.id == ingredient_id).first()

def get_ingredients(db: Session, skip: int = 0, limit: int = 100, storage_type: Optional[models.StorageType] = None):
    query = db.query(models.Ingredient)
    if storage_type:
        query = query.filter(models.Ingredient.storage_type == storage_type)
    return query.offset(skip).limit(limit).all()

def create_ingredient(db: Session, ingredient: schemas.IngredientCreate):
    db_ingredient = models.Ingredient(**ingredient.model_dump())
    db.add(db_ingredient)
    db.commit()
    db.refresh(db_ingredient)
    return db_ingredient

def update_ingredient(db: Session, ingredient_id: int, ingredient_update: schemas.IngredientUpdate):
    db_ingredient = get_ingredient(db, ingredient_id)
    if db_ingredient:
        update_data = ingredient_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_ingredient, key, value)
        db.commit()
        db.refresh(db_ingredient)
    return db_ingredient

def delete_ingredient(db: Session, ingredient_id: int):
    db_ingredient = get_ingredient(db, ingredient_id)
    if db_ingredient:
        db.delete(db_ingredient)
        db.commit()
        return True
    return False


def get_receipts(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(models.Receipt)
        .order_by(models.Receipt.created_at.desc(), models.Receipt.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_receipt(db: Session, receipt_id: int):
    return db.query(models.Receipt).filter(models.Receipt.id == receipt_id).first()


def create_receipt(db: Session, receipt: schemas.ReceiptCreate):
    payload = receipt.model_dump(exclude={"items"})
    db_receipt = models.Receipt(**payload)
    db.add(db_receipt)
    db.flush()

    for item in receipt.items:
        db_item = models.ReceiptItem(
            receipt_id=db_receipt.id,
            **item.model_dump(),
        )
        db.add(db_item)

    db.commit()
    db.refresh(db_receipt)
    return db_receipt
