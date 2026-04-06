import fitz  # PyMuPDF
import os

def list_pdfs(directory):
    pdf_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(root, file))
    return pdf_files

def extract_text_from_pdf(pdf_path, max_pages=5):
    """Extracts text from the first few pages of a PDF."""
    text = ""
    try:
        doc = fitz.open(pdf_path)
        for i in range(min(max_pages, len(doc))):
            page = doc.load_page(i)
            text += page.get_text()
        doc.close()
    except Exception as e:
        text = f"Error reading {pdf_path}: {e}"
    return text

if __name__ == "__main__":
    base_dir = "."
    pdfs = list_pdfs(base_dir)
    print(f"Found {len(pdfs)} PDF files.")
    
    for pdf in pdfs[:3]:  # Test with first 3
        print(f"\n--- Processing: {os.path.basename(pdf)} ---")
        content = extract_text_from_pdf(pdf, max_pages=1)
        print(content[:500] + "...")
