# Refrigerator Management API


FastAPI와 SQLAlchemy를 사용한 MySQL 기반 API , 기본 식재료 관리 기능과 한글 영수증 이미지를 OCR로 읽어 MySQL에 저장
</br>

<img width="250" height="259" alt="receipt" src="https://github.com/user-attachments/assets/3a18b7a5-01e6-4ec4-a910-0104cca994a4" />
<img width="550" height="259" alt="스크린샷 2026-04-15 오후 6 07 50" src="https://github.com/user-attachments/assets/62c0b06b-d7c7-43c3-865e-07dd84741a91" />




## 실행 방법

1. 가상환경 활성화
2. 패키지 설치

```bash
pip install -r requirements.txt
```

3. 환경변수 설정

```bash
cp .env.example .env
```

`.env` 또는 셸 환경변수에 `DATABASE_URL`을 설정하세요.

예시:

```bash
export DATABASE_URL="mysql+pymysql://root:password@localhost:3306/fridge_db?charset=utf8mb4"
```

4. 서버 실행

```bash
uvicorn main:app --reload
```

## 주요 엔드포인트

- `GET /health`
- `GET /categories/`
- `POST /categories/`
- `GET /ingredients/`
- `POST /ingredients/`
- `GET /ingredients/{ingredient_id}`
- `PATCH /ingredients/{ingredient_id}`
- `DELETE /ingredients/{ingredient_id}`
- `POST /receipts/ocr`
- `GET /receipts/`
- `GET /receipts/{receipt_id}`

## 영수증 OCR 저장

`POST /receipts/ocr`로 이미지 파일을 업로드하면 다음 과정으로 진행

1. 영수증 이미지 업로드
2. PaddleOCR로 한글 텍스트 추출
3. 상호명, 일시, 총액, 품목 후보를 파싱
4. MySQL의 `receipts`, `receipt_items` 테이블에 저장

예시 요청:

```bash
curl -X POST "http://127.0.0.1:8000/receipts/ocr" \
  -F "image=@/absolute/path/to/receipt.jpg"
```

루트의 `receipt.jpg`를 바로 업로드하려면:

```bash
chmod +x upload_receipt.sh
./upload_receipt.sh
```

서버 시작부터 업로드, DB 저장 결과 조회까지 한 번에 하려면:

```bash
chmod +x run_and_upload_receipt.sh
./run_and_upload_receipt.sh
```

다른 파일을 올리려면:

```bash
./upload_receipt.sh /absolute/path/to/other-receipt.jpg
```

또는:

```bash
./run_and_upload_receipt.sh /absolute/path/to/other-receipt.jpg
```

저장 확인:

```bash
curl "http://127.0.0.1:8000/receipts/"
```

또는 MySQL Workbench에서:

```sql
USE fridge_db;

SELECT * FROM receipts ORDER BY id DESC;
SELECT * FROM receipt_items ORDER BY id DESC;
```

주의:

- PaddleOCR는 첫 실행 시 모델 다운로드가 발생할 수 있음
- PaddleOCR 캐시는 기본 홈 디렉터리 대신 프로젝트 내부 `.paddlex/`를 사용하도록 설정
- 영수증 양식이 매장마다 달라서 품목 파싱은 휴리스틱 기반
- 정확도를 더 높이려면 추후 영수증 전용 파서 규칙을 추가 권장
