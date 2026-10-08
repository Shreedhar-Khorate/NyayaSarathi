from app.services.reading_order import ReadingOrder

def test_reading_order_two_columns():
    # Blocks are passed in completely random order
    blocks = [
        {"text": "Right 2", "bbox": [150, 25, 250, 45]},
        {"text": "Left 1", "bbox": [0, 0, 100, 20]},
        {"text": "Right 1", "bbox": [150, 0, 250, 20]},
        {"text": "Left 2", "bbox": [0, 25, 100, 45]},
    ]
    
    sorted_blocks = ReadingOrder.sort_blocks(blocks)
    assert len(sorted_blocks) == 4
    
    # Expected order: Left 1, Left 2, Right 1, Right 2
    assert sorted_blocks[0]["text"] == "Left 1"
    assert sorted_blocks[1]["text"] == "Left 2"
    assert sorted_blocks[2]["text"] == "Right 1"
    assert sorted_blocks[3]["text"] == "Right 2"

def test_reading_order_same_line():
    # Two blocks on the exact same line within a column
    blocks = [
        {"text": "Word2", "bbox": [50, 0, 100, 20]},
        {"text": "Word1", "bbox": [0, 0, 40, 20]},
    ]
    sorted_blocks = ReadingOrder.sort_blocks(blocks)
    assert sorted_blocks[0]["text"] == "Word1"
    assert sorted_blocks[1]["text"] == "Word2"
