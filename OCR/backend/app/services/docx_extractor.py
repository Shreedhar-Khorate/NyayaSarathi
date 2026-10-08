import docx
from typing import List, Dict, Any

class DOCXExtractor:
    @staticmethod
    def extract_text(file_path: str) -> List[Dict[str, Any]]:
        doc = docx.Document(file_path)
        
        full_text = []
        for para in doc.paragraphs:
            if para.text.strip():
                full_text.append(para.text)
                
        # Also extract tables
        for table in doc.tables:
            for row in table.rows:
                row_data = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_data:
                    full_text.append(" \t ".join(row_data))
                
        joined_text = "\n".join(full_text)
        
        pages_data = [{
            "page_number": 1,
            "text": joined_text,
            "confidence": None,
            "blocks": []
        }]
        
        return pages_data
