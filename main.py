from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine

# Initialize the FastAPI application instance
app = FastAPI()

# Initialize Microsoft Presidio engines for PII detection and redaction.
# AnalyzerEngine is responsible for detecting PII entities.
# AnonymizerEngine is responsible for replacing detected PII with safe tags.
analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

# --- Custom PII Recognizers ---

# 1. Israeli ID (Teudat Zehut) Recognizer
# Uses a regular expression to find exactly 9 consecutive digits.
tz_pattern = Pattern(name="israeli_tz", regex=r"\b\d{9}\b", score=0.9)
tz_recognizer = PatternRecognizer(supported_entity="IL_TZ", patterns=[tz_pattern])
analyzer.registry.add_recognizer(tz_recognizer)

# 2. Context-Based Hebrew Name Recognizer
# Detects Hebrew names based on preceding context keywords (e.g., "Client:", "Name:").
# It captures 1-2 Hebrew words following the keywords to identify potential first/last names.
context_regex = r"(?:הלקוח|החולה|שם:|קוראים לי)\s+[א-ת]+(?:\s+[א-ת]+)?"
context_pattern = Pattern(name="hebrew_name_context", regex=context_regex, score=0.8)
context_recognizer = PatternRecognizer(
    supported_entity="HEBREW_NAME", 
    patterns=[context_pattern]
)
analyzer.registry.add_recognizer(context_recognizer)

# --- Data Models ---

# Define the expected JSON structure for standard text processing requests
class DocumentRequest(BaseModel):
    text: str

# --- Core Logic ---

def mask_pii(text: str) -> str:
    """
    Analyzes the input text for PII (English names, Israeli IDs, Context-based Hebrew names)
    and returns the anonymized version of the text.
    """
    # Analyze text to find target entities
    results = analyzer.analyze(text=text, entities=["PERSON", "IL_TZ", "HEBREW_NAME"], language='en')

    # Replace found entities with redaction tags (e.g., <PERSON>, <HEBREW_NAME>)
    anonymized_result = anonymizer.anonymize(text=text, analyzer_results=results)

    return anonymized_result.text

# --- API Endpoints ---

# Health check endpoint to verify the server is running
@app.get("/")
def read_root():
    return {"message": "hello, privacy gateway is running"}

# Endpoint for processing raw JSON text requests
@app.post("/scrub")
def scrub_text(request: DocumentRequest):
    safe_text = mask_pii(request.text)
    return {"original_text": request.text, "safe_text": safe_text}

# Endpoint for processing uploaded files (e.g., .txt documents)
@app.post("/upload-document")
async def upload_document(file: UploadFile = File(...)):
    # Read the file content asynchronously
    content = await file.read()
    
    # Decode the raw bytes into a UTF-8 string
    original_text = content.decode("utf-8")
    
    # Process the text through the PII masking logic
    safe_text = mask_pii(original_text)

    # Return the processed data, ready for downstream AI consumption
    return {
        "filename": file.filename,
        "original_content": original_text,
        "safe_content": safe_text,
        "status": "Ready for AI processing"
    }