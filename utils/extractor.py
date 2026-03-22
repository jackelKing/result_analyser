import re, io, os
import pdfplumber
import numpy as np

# Lazy-load EasyOCR to avoid slow startup when not needed
_reader = None
def _get_reader():
    global _reader
    if _reader is None:
        import easyocr
        _reader = easyocr.Reader(["en"], gpu=False, verbose=False)
    return _reader

# VTU grade table
GRADE_POINTS = {"O": 10, "A+": 9, "A": 8, "B+": 7, "B": 6, "C": 5, "P": 4, "F": 0, "AB": 0}

# ---- VTU subject-code pattern (e.g. 21CS42, 21MAT31, 18ENG28L) ----------
_SUBJ_RE = re.compile(r"\b(\d{2}[A-Z]{2,5}\d{2}[A-Z]?)\b")
_GRADE_RE = re.compile(r"\b(O|A\+|A|B\+|B|C|P|F|AB)\b")
_USN_RE   = re.compile(r"\b([1-4][A-Z]{2}\d{2}[A-Z]{2}\d{3})\b", re.IGNORECASE)

def _vtu_fix(code: str) -> str:
    """Best-effort correction of common OCR misreads in VTU subject codes."""
    ocr_map = {"0": "O", "I": "1", "l": "1", "S": "5", "G": "6", "B": "8"}
    fixed = []
    for i, ch in enumerate(code):
        if i < 2:          # first 2 chars must be digits (year prefix)
            fixed.append(ocr_map.get(ch, ch) if not ch.isdigit() else ch)
        elif i < 4:        # chars 3-4 are letters (dept code)
            fixed.append(ch if ch.isalpha() else "X")
        else:
            fixed.append(ch)
    return "".join(fixed).upper()

def _extract_text_pdfplumber(path: str) -> str:
    text = ""
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
    except Exception:
        pass
    return text

def _extract_text_ocr(path: str) -> str:
    try:
        from pdf2image import convert_from_path
        import cv2
        pages = convert_from_path(path, dpi=200)
        reader = _get_reader()
        full = ""
        for img in pages:
            arr = np.array(img)
            gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            result = reader.readtext(thresh, detail=0, paragraph=True)
            full += " ".join(result) + "\n"
        return full
    except Exception:
        return ""

def extract(pdf_path: str, use_ocr_fallback: bool = True) -> dict:
    """
    Returns:
        {
          "usn": str | None,
          "grades": { subject_code: letter_grade },
          "error": str | None
        }
    """
    text = _extract_text_pdfplumber(pdf_path)
    if len(text.strip()) < 50 and use_ocr_fallback:
        text = _extract_text_ocr(pdf_path)

    if not text.strip():
        return {"usn": None, "grades": {}, "error": "Could not extract text from PDF"}

    # Extract USN
    usn_matches = _USN_RE.findall(text)
    usn = usn_matches[0].upper() if usn_matches else None

    # Extract subject-grade pairs  (they appear on the same line typically)
    grades = {}
    for line in text.splitlines():
        subjects_in_line = _SUBJ_RE.findall(line)
        grades_in_line   = _GRADE_RE.findall(line)
        if subjects_in_line and grades_in_line:
            for subj, grade in zip(subjects_in_line, grades_in_line):
                fixed = _vtu_fix(subj)
                grades[fixed] = grade

    return {"usn": usn, "grades": grades, "error": None}
