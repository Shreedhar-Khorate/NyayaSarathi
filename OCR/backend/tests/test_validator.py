import pytest
from fastapi import HTTPException
from app.services.validator import validate_file

class MockFile:
    def __init__(self, filename, content_type, size):
        self.filename = filename
        self.content_type = content_type
        self.size = size
        self.content = b"x" * size

    async def read(self):
        return self.content
        
    async def seek(self, pos):
        pass

@pytest.mark.asyncio
async def test_validate_valid_pdf():
    file = MockFile("test.pdf", "application/pdf", 1024)
    await validate_file(file)

@pytest.mark.asyncio
async def test_validate_valid_image():
    file = MockFile("test.png", "image/png", 1024)
    await validate_file(file)

@pytest.mark.asyncio
async def test_validate_invalid_extension():
    file = MockFile("test.txt", "text/plain", 1024)
    with pytest.raises(HTTPException) as excinfo:
        await validate_file(file)
    assert excinfo.value.status_code == 400
    assert "Unsupported file format" in str(excinfo.value.detail)

@pytest.mark.asyncio
async def test_validate_invalid_mime():
    file = MockFile("test.pdf", "text/plain", 1024)
    with pytest.raises(HTTPException) as excinfo:
        await validate_file(file)
    assert excinfo.value.status_code == 400
    assert "Unsupported file format" in str(excinfo.value.detail)
