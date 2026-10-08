import logging
import re
from typing import List, Dict, Any

logger = logging.getLogger("layout_analyzer")

class LayoutAnalyzer:
    @staticmethod
    def detect_columns(blocks: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        Groups blocks into columns based on horizontal gaps (gutters).
        Returns a list of columns, where each column is a list of blocks.
        Columns are sorted left-to-right.
        """
        if not blocks:
            return []
            
        # Sort blocks by x_min, then y_min
        sorted_by_x = sorted(blocks, key=lambda b: (b["bbox"][0], b["bbox"][1]))
        
        columns = []
        current_column = []
        current_col_x_max = sorted_by_x[0]["bbox"][2]
        
        GUTTER_THRESHOLD = 15
        
        for block in sorted_by_x:
            b_x_min = block["bbox"][0]
            b_x_max = block["bbox"][2]
            
            if not current_column:
                current_column.append(block)
                current_col_x_max = max(current_col_x_max, b_x_max)
                continue
                
            gap = b_x_min - current_col_x_max
            
            if gap >= GUTTER_THRESHOLD:
                # Start a new column
                columns.append(current_column)
                current_column = [block]
                current_col_x_max = b_x_max
            else:
                # Add to current column
                current_column.append(block)
                current_col_x_max = max(current_col_x_max, b_x_max)
                
        if current_column:
            columns.append(current_column)
            
        return columns

    @staticmethod
    def classify_block_region(block: Dict[str, Any], page_height: int = 1000) -> str:
        """
        Deterministically classifies an OCR/PDF text block into a legal document region
        using bounding box geometry and pattern heuristics.
        Regions: 'citation', 'case_number', 'date', 'bench', 'heading', 'header', 'footer', 'paragraph'
        """
        text = block.get("text", "").strip()
        bbox = block.get("bbox", [0, 0, 0, 0])
        y0, y1 = bbox[1], bbox[3]
        
        # Citation pattern: e.g. [2026] 9 S.C.R. 112 : 2026 INSC 864
        if re.search(r"\[\d{4}\].*S\.?C\.?R\.?|\d{4}\s*INSC\s*\d+|AIR\s*\d{4}|\(\d{4}\)\s*\d+\s*SCC", text, re.IGNORECASE):
            return "citation"
            
        # Case Number pattern: e.g. (Civil Appeal No. 10738 of 2026)
        if re.search(r"(?:Civil|Criminal|Writ)?\s*Appeal\s*(?:No\.?|Number)\s*\d+|SLP\s*\(C\)\s*No\.?\s*\d+|W\.P\.\s*\(C\)\s*No\.?\s*\d+", text, re.IGNORECASE):
            return "case_number"
            
        # Date pattern: e.g. 14 August 2026
        if re.search(r"\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b", text, re.IGNORECASE):
            return "date"
            
        # Bench / Judges pattern: e.g. [Nongmeikapam Kotiswar Singh and N.V. Anjaria,* JJ.]
        if re.search(r"\[.*(?:JJ\.?|J\.?|Hon'ble|Justice).*\]", text, re.IGNORECASE):
            return "bench"
            
        # Standard Legal Headings
        if text in ["Issue for Consideration", "Headnotes", "Headnotest", "JUDGMENT", "ORDER"]:
            return "heading"
            
        # Footer / Page numbers near bottom of page
        if page_height > 0 and y0 >= page_height * 0.92:
            return "footer"
            
        # Header near top of page
        if page_height > 0 and y1 <= page_height * 0.08:
            return "header"
            
        return "paragraph"
