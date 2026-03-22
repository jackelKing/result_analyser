import os, tempfile, concurrent.futures
from utils.drive import download_pdf
from utils.extractor import extract

SEM_COLS = [
    "Sem1 result ", "Sem2 result ", "Sem3 result ",
    "Sem4 result ", "Sem5 result ", "Sem6 result",
]

def _process_one(args):
    """Download one PDF and extract grades. Returns (sem_index, result_dict)."""
    sem_idx, url, expected_usn, tmp_dir = args
    if not url or not isinstance(url, str) or url.strip() == "":
        return sem_idx, {"usn": None, "grades": {}, "error": "No URL"}

    pdf_path = os.path.join(tmp_dir, f"sem{sem_idx}_{expected_usn}.pdf")
    ok = download_pdf(url, pdf_path)
    if not ok or not os.path.exists(pdf_path):
        return sem_idx, {"usn": None, "grades": {}, "error": "Download failed"}

    result = extract(pdf_path)

    # USN cross-verification
    if result["usn"] and expected_usn:
        if result["usn"].upper() != expected_usn.upper():
            result["error"] = (
                f"USN mismatch: sheet={expected_usn}, PDF={result['usn']}"
            )
    return sem_idx, result

def run_student(row: dict, tmp_dir: str, max_workers: int = 6) -> dict:
    """
    Process all semesters for one student concurrently.
    Returns { sem_index (1-based): extraction_result_dict }
    """
    tasks = []
    for i, col in enumerate(SEM_COLS, start=1):
        url = row.get(col)
        tasks.append((i, url, row.get("USN", ""), tmp_dir))

    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        for sem_idx, res in ex.map(_process_one, tasks):
            results[sem_idx] = res
    return results
