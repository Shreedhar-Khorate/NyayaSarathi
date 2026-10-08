from app.services.layout_analyzer import LayoutAnalyzer

def test_detect_single_column():
    blocks = [
        {"text": "A", "bbox": [0, 0, 100, 20]},
        {"text": "B", "bbox": [0, 25, 100, 45]},
        {"text": "C", "bbox": [0, 50, 100, 70]},
    ]
    columns = LayoutAnalyzer.detect_columns(blocks)
    assert len(columns) == 1
    assert len(columns[0]) == 3

def test_detect_two_columns():
    blocks = [
        {"text": "Left 1", "bbox": [0, 0, 100, 20]},
        {"text": "Left 2", "bbox": [0, 25, 100, 45]},
        {"text": "Right 1", "bbox": [150, 0, 250, 20]},
        {"text": "Right 2", "bbox": [150, 25, 250, 45]},
    ]
    columns = LayoutAnalyzer.detect_columns(blocks)
    assert len(columns) == 2
    assert len(columns[0]) == 2
    assert columns[0][0]["text"] == "Left 1"
    assert len(columns[1]) == 2
    assert columns[1][0]["text"] == "Right 1"

def test_detect_overlapping_blocks():
    # Blocks that overlap horizontally should be grouped together
    blocks = [
        {"text": "A", "bbox": [0, 0, 100, 20]},
        {"text": "B", "bbox": [50, 25, 150, 45]}, # Overlaps A horizontally
        {"text": "C", "bbox": [200, 0, 300, 20]}, # Gutter of 50px (150 to 200)
    ]
    columns = LayoutAnalyzer.detect_columns(blocks)
    assert len(columns) == 2
    assert len(columns[0]) == 2
    assert columns[0][0]["text"] == "A"
    assert columns[0][1]["text"] == "B"
    assert len(columns[1]) == 1
    assert columns[1][0]["text"] == "C"
