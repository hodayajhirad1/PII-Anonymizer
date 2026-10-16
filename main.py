from fastapi import FastAPI
from pydantic import BaseModel
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine

app = FastAPI()

analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

tz_pattern = Pattern(name="israeli_tz", regex=r"\b\d{4}\b", score=0.9)
tz_recognizer = PatternRecognizer(supported_entity="IL_TZ", patterns=[tz_pattern])
analyzer.registry.add_recognizer(tz_recognizer)

hebrew_names_recognizer = PatternRecognizer(
    supported_entity="HEBREW_NAME", 
    deny_list=["ישראל ישראלי", "משה כהן", "גאיה", "שני"]
)
analyzer.registry.add_recognizer(hebrew_names_recognizer)

class DocumentRequest(BaseModel):
    text: str

def mask_pii(text: str) -> str:
    results = analyzer.analyze(text=text, entities=["PERSON", "IL_TZ", "HEBREW_NAME"], language='en')

    anonymized_result = anonymizer.anonymize(text=text, analyzer_results=results)

    return anonymized_result.text


@app.get("/")
def read_root():
    return {"message":"hello, privacy gateway is running"}

@app.post("/scrub")
def scrub_text(request: DocumentRequest):
    print("Received new text:", request.text)
    
    safe_text = mask_pii(request.text)


    return {
        "original_text": request.text,
        "safe_text": safe_text
        }
    