# Ingredients Management System

>MySQL based API, 한글 영수증 이미지를 OCR로 읽어 DB 저장

</br>

<img width="260" height="300" alt="receipt" src="https://github.com/user-attachments/assets/3a18b7a5-01e6-4ec4-a910-0104cca994a4" />
<img width="550" height="350" alt="스크린샷 2026-04-15 오후 6 07 50" src="https://github.com/user-attachments/assets/62c0b06b-d7c7-43c3-865e-07dd84741a91" />

---

## 실행 방법

1. 가상환경 활성화 

</br>

2. 패키지 설치

```bash
pip install -r requirements.txt
```
</br>

3. 환경변수 설정


```bash
export DATABASE_URL="mysql+pymysql://root:password@localhost:3306/fridge_db?charset=utf8mb4"
```

`.env` 또는 셸 환경변수에 `DATABASE_URL` 설정

</br>

4. 서버 실행

```bash
uvicorn main:app --reload
```
</br>

## 영수증 OCR 저장

1. 영수증 이미지 업로드
2. PaddleOCR로 한글 텍스트 추출
3. 상호명, 일시, 총액, 품목 후보를 파싱
4. MySQL의 `receipts`, `receipt_items` 테이블에 저장

</br>

루트의 `receipt.jpg`를 업로드

```bash
chmod +x upload_receipt.sh
./upload_receipt.sh
```

</br>

서버 시작, DB 저장 자동화:

```bash
chmod +x run_and_upload_receipt.sh
./run_and_upload_receipt.sh
```

</br>

다른 파일 업로드:

```bash
./upload_receipt.sh /absolute/path/to/other-receipt.jpg
```

</br>

저장 확인:

```bash
curl "http://127.0.0.1:8000/receipts/"
```

</br>

또는 MySQL Workbench:

```sql
USE fridge_db;

SELECT * FROM receipts ORDER BY id DESC;
SELECT * FROM receipt_items ORDER BY id DESC;
```

