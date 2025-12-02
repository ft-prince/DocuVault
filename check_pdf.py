
import os
import fitz  # PyMuPDF

def check_pdf():
    pdf_path = os.path.join(os.path.dirname(__file__), 'media', 'User Documentation_Minda.pdf')
    print(f"Checking PDF at: {pdf_path}")
    
    if not os.path.exists(pdf_path):
        print("❌ File not found!")
        return
        
    try:
        doc = fitz.open(pdf_path)
        print(f"✅ PDF opened successfully. Pages: {len(doc)}")
        
        text = ""
        for i, page in enumerate(doc):
            page_text = page.get_text()
            print(f"Page {i} text length: {len(page_text)}")
            text += page_text
            if i >= 2: break # Check first 3 pages
            
        if len(text.strip()) == 0:
            print("❌ No text extracted! PDF might be scanned/image-based.")
        else:
            print(f"✅ Extracted {len(text)} characters from first 3 pages.")
            print(f"Preview: {text[:200]}...")
            
    except Exception as e:
        print(f"❌ Error opening PDF: {e}")

if __name__ == "__main__":
    check_pdf()
