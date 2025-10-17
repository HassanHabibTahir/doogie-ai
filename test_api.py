from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import shutil
import PyPDF2
import fitz  # PyMuPDF
from PIL import Image
import io
import openai

# ------------------- OpenAI Setup -------------------
# Set your OpenAI API key here
openai.api_key = "YOUR_OPENAI_API_KEY"

def translate_to_english(text: str) -> str:
    """
    Translate any text to English using OpenAI
    """
    if not text.strip():
        return ""
    prompt = (
        "You are a helpful assistant. Translate the following text to English, "
        "keeping the meaning accurate and formatting intact:\n\n"
        f"{text}"
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a translation assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
        )
        translated_text = response.choices[0].message.content.strip()
        return translated_text
    except Exception as e:
        return f"Error in translation: {str(e)}"

def detect_language(text: str) -> str:
    """
    Detect language using OpenAI
    """
    if not text.strip():
        return "unknown"
    try:
        prompt = f"Detect the language of this text: {text}"
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a language detection assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        language = response.choices[0].message.content.strip()
        return language
    except Exception as e:
        return f"Error detecting language: {str(e)}"

# ------------------- FastAPI Setup -------------------
app = FastAPI(title="Doogie AI - PDF Processing & Translation API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory to save uploads
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# ------------------- Upload Endpoint -------------------
@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed!")
    safe_filename = Path(file.filename).name
    file_path = UPLOAD_DIR / safe_filename
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return JSONResponse(content={
            "message": "PDF uploaded successfully!",
            "filename": safe_filename,
            "file_path": str(file_path)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

# ------------------- PDF Info & Text Extraction -------------------
def extract_pdf_info(pdf_path: Path) -> dict:
    info = {}
    try:
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            doc_info = reader.metadata
            if doc_info:
                info = {k: str(v) for k, v in doc_info.items()}
            info["num_pages"] = len(reader.pages)
    except Exception as e:
        info["error"] = str(e)
    return info

def extract_pdf_text(pdf_path: Path) -> str:
    text = ""
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            text += page.get_text()
        doc.close()
    except Exception as e:
        text = f"Error extracting text: {str(e)}"
    return text

def extract_pdf_images(pdf_path: Path):
    images = []
    try:
        doc = fitz.open(pdf_path)
        for page_index in range(len(doc)):
            page = doc[page_index]
            for img_index, img in enumerate(page.get_images(full=True)):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_data = base_image["image"]
                image = Image.open(io.BytesIO(image_data))
                images.append({
                    "id": f"page{page_index}_img{img_index}",
                    "width": image.width,
                    "height": image.height
                })
        doc.close()
    except Exception as e:
        print("⚠️ Image extraction error:", e)
    return images

# ------------------- Read PDF & Translate -------------------
@app.get("/read-pdf/{filename}")
async def read_pdf_file(
    filename: str,
    extract_text: bool = Query(True),
    extract_images: bool = Query(False),
    translate: bool = Query(True)
):
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files supported")

    try:
        result = {
            "filename": filename,
            "file_path": str(file_path),
            "file_size": file_path.stat().st_size,
            "metadata": extract_pdf_info(file_path)
        }

        text = ""
        if extract_text:
            text = extract_pdf_text(file_path)
            result["text_content"] = text
            result["char_count"] = len(text)
            result["word_count"] = len(text.split())

            # Detect language
            language = detect_language(text)
            result["language_detected"] = language

            # Translate if not English
            translated_text = text
            if translate and language.lower() != "english":
                translated_text = translate_to_english(text)
            result["translated_text"] = translated_text

        if extract_images:
            images = extract_pdf_images(file_path)
            result["images"] = images

        return JSONResponse(content=result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading PDF: {str(e)}")

# ------------------- Root & Health -------------------
@app.get("/")
async def read_root():
    return {"message": "🚀 Doogie AI PDF API with Translation is running!"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

# ------------------- Run Server -------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
