# OCR Test Samples

## Generate a sample image

```bash
pip install Pillow
python create_sample.py
# -> creates sample.png
```

## Test the OCR endpoint

```bash
# Health check
curl http://localhost:8000/health

# OCR with the generated sample image
curl -X POST http://localhost:8000/ocr \
  -F "file=@sample.png"

# OCR via the NestJS API (end-to-end)
curl -X POST http://localhost:3000/records/ocr \
  -F "image=@sample.png"
```

Expected response from `/ocr`:
```json
{
  "text": "Nutrition Facts\nServing Size 1 cup...",
  "engine": "tesseract"
}
```
