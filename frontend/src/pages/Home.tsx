import React, { useState, useEffect } from 'react';
import UploadBox from '../components/UploadBox';
import ResultsGrid from '../components/ResultsGrid';
import { searchByImage, SearchResult, getPhotos, PhotoItem } from '../api/client';

type ViewMode = 'browse' | 'search';

const Home: React.FC = () => {
  const [viewMode, setViewMode] = useState<ViewMode>('browse');
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [allPhotos, setAllPhotos] = useState<PhotoItem[]>([]);
  const [totalPhotos, setTotalPhotos] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [queryTime, setQueryTime] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [faceDetected, setFaceDetected] = useState<boolean>(true);
  const [topK, setTopK] = useState(30);
  const [threshold, setThreshold] = useState(0.6);

  useEffect(() => {
    if (viewMode === 'browse') {
      loadPhotos(currentPage);
    }
  }, [viewMode, currentPage]);

  const loadPhotos = async (page: number) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await getPhotos(page, 20);
      setAllPhotos(response.photos);
      setTotalPhotos(response.total);
      setTotalPages(response.total_pages);
      setCurrentPage(response.page);
    } catch (err: any) {
      console.error('Failed to load photos:', err);
      setError('Failed to load photos. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleImageSelected = async (file: File) => {
    setIsLoading(true);
    setError(null);
    setMessage(null);
    setResults([]);

    try {
      const response = await searchByImage(file, topK, threshold);
      setResults(response.results);
      setQueryTime(response.query_time_ms);
      setFaceDetected(response.face_detected);
      setMessage(response.message || null);
      setViewMode('search');
    } catch (err: any) {
      console.error('Search failed:', err);
      setError(err.response?.data?.detail || 'Search failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleBackToBrowse = () => {
    setViewMode('browse');
    setResults([]);
    setMessage(null);
    setError(null);
    loadPhotos(currentPage);
  };

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1 style={styles.title}>PhotoMatch</h1>
        <p style={styles.subtitle}>Find similar faces using AI-powered search</p>
      </header>

      {viewMode === 'search' && (
        <div style={styles.backButton} onClick={handleBackToBrowse}>
          ← Back to Browse All Photos
        </div>
      )}

      <div style={styles.controls}>
        <div style={styles.controlGroup}>
          <label style={styles.label}>
            Max Results: {topK}
            <input
              type="range"
              min="10"
              max="100"
              step="10"
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              style={styles.slider}
            />
          </label>
        </div>
        <div style={styles.controlGroup}>
          <label style={styles.label}>
            Similarity Threshold: {(threshold * 100).toFixed(0)}%
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={threshold}
              onChange={(e) => setThreshold(Number(e.target.value))}
              style={styles.slider}
            />
          </label>
        </div>
      </div>

      <UploadBox onImageSelected={handleImageSelected} isLoading={isLoading} />

      {error && (
        <div style={styles.error}>
          <span style={styles.errorIcon}>⚠️</span>
          {error}
        </div>
      )}

      {message && !error && (
        <div style={styles.info}>
          <span style={styles.infoIcon}>{faceDetected ? 'ℹ️' : '👤'}</span>
          {message}
        </div>
      )}

      {!isLoading && viewMode === 'browse' && allPhotos.length > 0 && (
        <ResultsGrid 
          results={allPhotos.map(photo => ({
            photo_id: photo.photo_id,
            image_url: photo.image_url,
            similarity: 1.0,
            event_tag: photo.event_tag,
            width: photo.width,
            height: photo.height
          }))} 
          queryTime={0}
          currentPage={currentPage}
          totalPages={totalPages}
          totalResults={totalPhotos}
          onPageChange={setCurrentPage}
          showSimilarity={false}
        />
      )}

      {!isLoading && viewMode === 'browse' && allPhotos.length === 0 && !error && (
        <div style={styles.emptyState}>
          <div style={styles.emptyIcon}>📷</div>
          <p style={styles.emptyText}>No photos in database yet</p>
          <p style={styles.emptySubtext}>Upload some photos to get started</p>
        </div>
      )}

      {!isLoading && viewMode === 'search' && results.length > 0 && (
        <ResultsGrid 
          results={results} 
          queryTime={queryTime}
          showSimilarity={true}
        />
      )}
    </div>
  );
};

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    minHeight: '100vh',
    backgroundColor: '#f7fafc',
    padding: '40px 20px',
  },
  header: {
    textAlign: 'center',
    marginBottom: '40px',
  },
  title: {
    fontSize: '48px',
    fontWeight: '800',
    color: '#2d3748',
    margin: '0 0 12px 0',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
  },
  subtitle: {
    fontSize: '18px',
    color: '#718096',
    margin: 0,
  },
  controls: {
    maxWidth: '600px',
    margin: '0 auto 30px',
    display: 'flex',
    gap: '24px',
    flexWrap: 'wrap',
    justifyContent: 'center',
  },
  controlGroup: {
    flex: '1 1 250px',
    minWidth: '200px',
  },
  label: {
    display: 'block',
    fontSize: '14px',
    fontWeight: '600',
    color: '#4a5568',
    marginBottom: '8px',
  },
  slider: {
    width: '100%',
    marginTop: '8px',
    cursor: 'pointer',
  },
  error: {
    maxWidth: '600px',
    margin: '20px auto',
    padding: '16px 20px',
    backgroundColor: '#fff5f5',
    border: '2px solid #fc8181',
    borderRadius: '8px',
    color: '#c53030',
    fontSize: '14px',
    fontWeight: '500',
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  errorIcon: {
    fontSize: '20px',
  },
  info: {
    maxWidth: '600px',
    margin: '20px auto',
    padding: '16px 20px',
    backgroundColor: '#ebf8ff',
    border: '2px solid #4299e1',
    borderRadius: '8px',
    color: '#2c5282',
    fontSize: '14px',
    fontWeight: '500',
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  infoIcon: {
    fontSize: '20px',
  },
  backButton: {
    maxWidth: '600px',
    margin: '0 auto 20px',
    padding: '12px 20px',
    backgroundColor: '#4299e1',
    color: 'white',
    borderRadius: '8px',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: '600',
    textAlign: 'center',
    transition: 'background-color 0.2s',
  },
  emptyState: {
    textAlign: 'center',
    padding: '80px 20px',
  },
  emptyIcon: {
    fontSize: '64px',
    marginBottom: '16px',
  },
  emptyText: {
    fontSize: '20px',
    fontWeight: '600',
    color: '#2d3748',
    margin: '0 0 8px 0',
  },
  emptySubtext: {
    fontSize: '14px',
    color: '#718096',
    margin: 0,
  },
};

export default Home;
