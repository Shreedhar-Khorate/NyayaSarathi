import React, { useState } from 'react';
import { uploadDocument } from '../api';

const FileUpload = () => {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e) => {
    if (e.target.files) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    
    setLoading(true);
    try {
      const data = await uploadDocument(file);
      setResult(data);
    } catch (error) {
      console.error('Error uploading file:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2>Upload Document</h2>
      <input type="file" onChange={handleFileChange} />
      <button onClick={handleUpload} disabled={!file || loading}>
        {loading ? 'Uploading...' : 'Upload'}
      </button>
      
      {result && (
        <div>
          <h3>Result</h3>
          <p><strong>Filename:</strong> {result.filename}</p>
          <p><strong>Status:</strong> {result.status}</p>
          <p><strong>Document Type:</strong> {result.document_type}</p>
          <p><strong>Pages:</strong> {result.pages}</p>
          <p><strong>Method:</strong> {result.extraction_method}</p>
          
          <h4>Extracted Text:</h4>
          <pre style={{ 
            background: '#f4f4f4', 
            padding: '10px', 
            maxHeight: '400px', 
            overflowY: 'auto',
            whiteSpace: 'pre-wrap'
          }}>
            {result.text}
          </pre>
        </div>
      )}
    </div>
  );
};

export default FileUpload;
