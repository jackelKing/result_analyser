# High-Speed Academic Performance Analyser

An end-to-end automation pipeline that converts VTU result PDFs (shared via Google Drive links in an Excel sheet) into a structured SGPA/CGPA report.

## Features
- Concurrent PDF download & OCR extraction (ThreadPoolExecutor)
- Hybrid engine: `pdfplumber` for digital PDFs + `EasyOCR` for scanned images
- VTU-Fix algorithm: auto-corrects common OCR noise in subject codes
- Persistent SQLite subject-credit registry (enter each subject only once)
- Streamlit web UI with live progress tracking
- Downloadable output Excel with SGPA per semester and final CGPA

## Setup

```bash
git clone <your-repo-url>
cd academic_performance_analyser
python -m venv venv
# Windows:  venv\Scripts\activate
# Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
streamlit run app/main.py
```

## Input Excel Format
| Name | USN | Class | Section | Sem1 result | Sem2 result | ... | Sem6 result | CGPA |
|------|-----|-------|---------|-------------|-------------|-----|-------------|------|
| Student Name | 1RFxxCSxxx | VI | B | ... | ... | | |

## Grade → Points (VTU)
| Grade | O | A+ | A | B+ | B | C | P | F |
|-------|---|----|---|----|---|---|---|---|
| Points| 10| 9  | 8 | 7  | 6 | 5 | 4 | 0 |
