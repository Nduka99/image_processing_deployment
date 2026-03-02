import sys
try:
    import fitz # PyMuPDF
    doc = fitz.open(sys.argv[1])
    with open("task_pdf.txt", "w", encoding="utf-8") as f:
        for page in doc:
            f.write(page.get_text() + "\n")
except ImportError:
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(sys.argv[1])
        with open("task_pdf.txt", "w", encoding="utf-8") as f:
            for page in reader.pages:
                f.write(page.extract_text() + "\n")
    except Exception as e:
        print("Failed:", e)
