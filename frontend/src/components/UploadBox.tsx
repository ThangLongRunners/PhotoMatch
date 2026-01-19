import React, { useState } from 'react';

interface UploadBoxProps {
  onImageSelected: (file: File) => void;
  isLoading: boolean;
}

const UploadBox: React.FC<UploadBoxProps> = ({ onImageSelected, isLoading }) => {
  const [preview, setPreview] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);

  const handleFile = (file: File) => {
    if (!file.type.startsWith('image/')) {
      alert('Please upload an image file');
      return;
    }

    // Create preview
    const reader = new FileReader();
    reader.onloadend = () => {
      setPreview(reader.result as string);
    };
    reader.readAsDataURL(file);

    // Pass to parent
    onImageSelected(file);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  return (
    <div style={styles.container}>
      <div
        style={{
          ...styles.uploadBox,
          ...(dragActive ? styles.dragActive : {}),
        }}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        {preview ? (
          <div style={styles.previewContainer}>
            <img src={preview} alt="Preview" style={styles.preview} />
            <label style={styles.changeButton}>
              Change Image
              <input
                type="file"
                accept="image/*"
                onChange={handleChange}
                style={styles.hiddenInput}
                disabled={isLoading}
              />
            </label>
          </div>
        ) : (
          <label style={styles.uploadLabel}>
            <div style={styles.uploadContent}>
              <div style={styles.uploadIcon}>📷</div>
              <p style={styles.uploadText}>
                Drop an image here or click to upload
              </p>
              <p style={styles.uploadSubtext}>
                Upload a photo containing a face to search
              </p>
            </div>
            <input
              type="file"
              accept="image/*"
              onChange={handleChange}
              style={styles.hiddenInput}
              disabled={isLoading}
            />
          </label>
        )}
      </div>
      {isLoading && <div style={styles.loadingText}>Searching...</div>}
    </div>
  );
};

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    width: '100%',
    maxWidth: '600px',
    margin: '0 auto',
  },
  uploadBox: {
    border: '3px dashed #cbd5e0',
    borderRadius: '12px',
    padding: '40px',
    textAlign: 'center',
    backgroundColor: '#f7fafc',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
  },
  dragActive: {
    borderColor: '#4299e1',
    backgroundColor: '#ebf8ff',
  },
  uploadLabel: {
    display: 'block',
    cursor: 'pointer',
  },
  uploadContent: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '12px',
  },
  uploadIcon: {
    fontSize: '64px',
  },
  uploadText: {
    fontSize: '18px',
    fontWeight: '600',
    color: '#2d3748',
    margin: 0,
  },
  uploadSubtext: {
    fontSize: '14px',
    color: '#718096',
    margin: 0,
  },
  hiddenInput: {
    display: 'none',
  },
  previewContainer: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '20px',
  },
  preview: {
    maxWidth: '100%',
    maxHeight: '300px',
    borderRadius: '8px',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
  },
  changeButton: {
    padding: '10px 24px',
    backgroundColor: '#4299e1',
    color: 'white',
    borderRadius: '6px',
    cursor: 'pointer',
    fontWeight: '500',
    transition: 'background-color 0.2s',
  },
  loadingText: {
    textAlign: 'center',
    marginTop: '20px',
    fontSize: '16px',
    color: '#4299e1',
    fontWeight: '500',
  },
};

export default UploadBox;
