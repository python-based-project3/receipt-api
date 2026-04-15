from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List

import models, schemas, crud
from database import engine, get_db
from ocr_service import OCRUnavailableError, extract_receipt_from_upload

# 애플리케이션 시작 시 데이터베이스 스키마 생성
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Refrigerator Management API")


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}

# --- Category 라우터 ---

@app.post("/categories/", response_model=schemas.Category, tags=["Categories"])
def create_category(category: schemas.CategoryCreate, db: Session = Depends(get_db)):
    return crud.create_category(db=db, category=category)

@app.get("/categories/", response_model=List[schemas.Category], tags=["Categories"])
def read_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_categories(db, skip=skip, limit=limit)


# --- Ingredient 라우터 ---

@app.post("/ingredients/", response_model=schemas.Ingredient, tags=["Ingredients"])
def create_ingredient(ingredient: schemas.IngredientCreate, db: Session = Depends(get_db)):
    return crud.create_ingredient(db=db, ingredient=ingredient)

@app.get("/ingredients/", response_model=List[schemas.Ingredient], tags=["Ingredients"])
def read_ingredients(skip: int = 0, limit: int = 100, storage_type: models.StorageType = None, db: Session = Depends(get_db)):
    return crud.get_ingredients(db, skip=skip, limit=limit, storage_type=storage_type)

@app.get("/ingredients/{ingredient_id}", response_model=schemas.Ingredient, tags=["Ingredients"])
def read_ingredient(ingredient_id: int, db: Session = Depends(get_db)):
    db_ingredient = crud.get_ingredient(db, ingredient_id=ingredient_id)
    if db_ingredient is None:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    return db_ingredient

@app.patch("/ingredients/{ingredient_id}", response_model=schemas.Ingredient, tags=["Ingredients"])
def update_ingredient(ingredient_id: int, ingredient: schemas.IngredientUpdate, db: Session = Depends(get_db)):
    db_ingredient = crud.update_ingredient(db, ingredient_id=ingredient_id, ingredient_update=ingredient)
    if db_ingredient is None:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    return db_ingredient

@app.delete("/ingredients/{ingredient_id}", tags=["Ingredients"])
def delete_ingredient(ingredient_id: int, db: Session = Depends(get_db)):
    success = crud.delete_ingredient(db, ingredient_id=ingredient_id)
    if not success:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    return {"message": "Ingredient successfully deleted"}


@app.post("/receipts/ocr", response_model=schemas.Receipt, tags=["Receipts"])
def upload_receipt_image(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        parsed = extract_receipt_from_upload(image)
        receipt = schemas.ReceiptCreate(
            store_name=parsed.store_name,
            receipt_date=parsed.receipt_date,
            total_amount=parsed.total_amount,
            currency=parsed.currency,
            image_path=parsed.image_path,
            raw_text=parsed.raw_text,
            raw_ocr=parsed.raw_ocr,
            items=[
                schemas.ReceiptItemCreate(
                    name=item.name,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    line_total=item.line_total,
                )
                for item in parsed.items
            ],
        )
        return crud.create_receipt(db, receipt)
    except OCRUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    finally:
        image.file.close()


@app.get("/receipts/", response_model=List[schemas.Receipt], tags=["Receipts"])
def read_receipts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_receipts(db, skip=skip, limit=limit)


@app.get("/receipts/{receipt_id}", response_model=schemas.Receipt, tags=["Receipts"])
def read_receipt(receipt_id: int, db: Session = Depends(get_db)):
    db_receipt = crud.get_receipt(db, receipt_id=receipt_id)
    if db_receipt is None:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return db_receipt
