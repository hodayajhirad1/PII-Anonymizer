from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine
import time # הוספנו את זה בשביל לדמות זמן המתנה ברשת

app = FastAPI()

analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

tz_pattern = Pattern(name="israeli_tz", regex=r"\b\d{9}\b", score=0.9)
tz_recognizer = PatternRecognizer(supported_entity="IL_TZ", patterns=[tz_pattern])
analyzer.registry.add_recognizer(tz_recognizer)

context_regex = r"(?:הלקוח|החולה|שם:|קוראים לי)\s+[א-ת]+(?:\s+[א-ת]+)?"
context_pattern = Pattern(name="hebrew_name_context", regex=context_regex, score=0.8)

context_recognizer = PatternRecognizer(
    supported_entity="HEBREW_NAME", 
    patterns=[context_pattern]
)
analyzer.registry.add_recognizer(context_recognizer)

class DocumentRequest(BaseModel):
    text: str

def mask_pii(text: str) -> str:
    results = analyzer.analyze(text=text, entities=["PERSON", "IL_TZ", "HEBREW_NAME"], language='en')
    anonymized_result = anonymizer.anonymize(text=text, analyzer_results=results)
    return anonymized_result.text

# ==========================================
# פונקציה חדשה: סימולציה של מודל בינה מלאכותית
# ==========================================
def call_ai_model(safe_prompt: str) -> str:
    """
    Simulates an API call to an external LLM (like OpenAI/Gemini).
    """
    print("Sending safe data to external AI API...")
    time.sleep(2) # מדמה המתנה של שתי שניות לעיבוד
    return f"AI System: I received the safe text starting with '{safe_prompt[:25]}...'. I can now safely process it!"

@app.get("/")
def read_root():
    return {"message":"hello, privacy gateway is running"}

@app.post("/scrub")
def scrub_text(request: DocumentRequest):
    safe_text = mask_pii(request.text)
    return {"original_text": request.text, "safe_text": safe_text}

@app.post("/upload-document")
async def upload_document(file: UploadFile = File(...)):
    content = await file.read()
    original_text = content.decode("utf-8")
    
    # 1. מצנזרים את המידע הרגיש
    safe_text = mask_pii(original_text)
    
    # 2. שולחים את הטקסט הנקי לבינה המלאכותית
    ai_response = call_ai_model(safe_text)

    # 3. מחזירים ללקוח את המידע המלא יחד עם התשובה של הבינה המלאכותית
    return {
        "filename": file.filename,
        "original_content": original_text,
        "safe_content": safe_text,
        "ai_analysis": ai_response
    }