"""
Reading Order Reconstruction for Legal Documents.
Groups bounding boxes into natural horizontal lines and orders columns left-to-right
and lines top-to-bottom.
"""

import logging
from typing import List, Dict, Any
from services.ocr.layout_analyzer import LayoutAnalyzer

logger = logging.getLogger("nyayasarathi.ocr.reading_order")


class ReadingOrder:
    @staticmethod
    def _group_into_lines(blocks: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        Groups blocks that are on the same visual horizontal line.
        Two blocks belong to the same line if:
        1. They do NOT overlap horizontally (horizontal overlap <= 8px).
        2. Their vertical centers are aligned (diff <= min_height * 0.45).
        3. Their vertical overlap is significant (>= 40% of min_height).
        """
        if not blocks:
            return []

        # Sort blocks by vertical center first, then X
        sorted_blocks = sorted(blocks, key=lambda b: ((b["bbox"][1] + b["bbox"][3]) / 2, b["bbox"][0]))
        lines: List[List[Dict[str, Any]]] = []

        for b in sorted_blocks:
            b_y0, b_y1 = b["bbox"][1], b["bbox"][3]
            b_x0, b_x1 = b["bbox"][0], b["bbox"][2]
            b_yc = (b_y0 + b_y1) / 2
            b_h = max(1, b_y1 - b_y0)

            placed = False
            for line in lines:
                line_ycs = [(item["bbox"][1] + item["bbox"][3]) / 2 for item in line]
                line_yc = sum(line_ycs) / len(line_ycs)
                line_hs = [max(1, item["bbox"][3] - item["bbox"][1]) for item in line]
                line_h = sum(line_hs) / len(line_hs)

                min_h = min(b_h, line_h)
                center_diff = abs(b_yc - line_yc)

                if center_diff <= min_h * 0.45:
                    line_y0 = min(item["bbox"][1] for item in line)
                    line_y1 = max(item["bbox"][3] for item in line)
                    v_overlap = max(0, min(b_y1, line_y1) - max(b_y0, line_y0))

                    if (v_overlap / min_h) >= 0.4:
                        # Check horizontal non-overlap with all blocks in line
                        h_overlaps = False
                        for item in line:
                            item_x0, item_x1 = item["bbox"][0], item["bbox"][2]
                            h_overlap = max(0, min(b_x1, item_x1) - max(b_x0, item_x0))
                            if h_overlap > 8:
                                h_overlaps = True
                                break
                        if not h_overlaps:
                            line.append(b)
                            placed = True
                            break
            if not placed:
                lines.append([b])

        # Sort lines top-to-bottom by their top Y coordinate
        lines.sort(key=lambda l: (min(item["bbox"][1] for item in l), min(item["bbox"][0] for item in l)))

        # Within each line, sort blocks left-to-right by X coordinate
        for line in lines:
            line.sort(key=lambda item: item["bbox"][0])

        return lines

    @staticmethod
    def sort_blocks(blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sorts OCR or PDF extraction blocks into natural reading order:
        1. Detects columns (left-to-right).
        2. Within each column, sorts blocks into horizontal lines (top-to-bottom).
        3. Within each line, sorts blocks left-to-right.
        """
        if not blocks:
            return []

        columns = LayoutAnalyzer.detect_columns(blocks)
        ordered_blocks = []

        for column in columns:
            lines = ReadingOrder._group_into_lines(column)
            for line in lines:
                ordered_blocks.extend(line)

        return ordered_blocks


__all__ = ["ReadingOrder"]
