import React, { useState, useEffect } from 'react';
import { SearchResult, getImageUrl } from '../api/client';

interface ResultsGridProps {
  results: SearchResult[];
  queryTime: number;
  currentPage?: number;
  totalPages?: number;
  totalResults?: number;
  onPageChange?: (page: number) => void;
  showSimilarity?: boolean;
}

const ITEMS_PER_PAGE = 20;

const ResultsGrid: React.FC<ResultsGridProps> = ({ 
  results, 
  queryTime, 
  currentPage: externalPage,
  totalPages: externalTotalPages,
  totalResults: externalTotal,
  onPageChange,
  showSimilarity = true
}) => {
  const [internalPage, setInternalPage] = useState(1);

  useEffect(() => {
    if (externalPage) {
      setInternalPage(externalPage);
    }
  }, [externalPage]);

  if (results.length === 0) {
    return (
      <div style={styles.emptyState}>
        <div style={styles.emptyIcon}>🔍</div>
        <p style={styles.emptyText}>No matching faces found</p>
        <p style={styles.emptySubtext}>Try uploading a different image or adjusting the similarity threshold</p>
      </div>
    );
  }

  // Use external pagination if provided, otherwise use internal
  const usePagination = onPageChange !== undefined;
  const currentPage = usePagination ? (externalPage || 1) : internalPage;
  const totalPages = usePagination ? (externalTotalPages || 1) : Math.ceil(results.length / ITEMS_PER_PAGE);
  const totalCount = usePagination ? (externalTotal || results.length) : results.length;
  
  const startIndex = usePagination ? 0 : (internalPage - 1) * ITEMS_PER_PAGE;
  const endIndex = usePagination ? results.length : startIndex + ITEMS_PER_PAGE;
  const currentResults = usePagination ? results : results.slice(startIndex, endIndex);

  const handlePageChange = (page: number) => {
    if (usePagination && onPageChange) {
      onPageChange(page);
    } else {
      setInternalPage(page);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2 style={styles.title}>
          {showSimilarity ? `Found ${totalCount} matching ${totalCount === 1 ? 'face' : 'faces'}` : `All Photos (${totalCount})`}
        </h2>
        {queryTime > 0 && <p style={styles.queryTime}>Query time: {queryTime.toFixed(2)}ms</p>}
        {totalPages > 1 && (
          <p style={styles.pageInfo}>
            Showing {usePagination ? ((currentPage - 1) * 20 + 1) : (startIndex + 1)}-{usePagination ? Math.min(currentPage * 20, totalCount) : Math.min(endIndex, totalCount)} of {totalCount}
          </p>
        )}
      </div>

      <div style={styles.grid}>
        {currentResults.map((result) => (
          <div key={result.photo_id} style={styles.card}>
            <div style={styles.imageContainer}>
              <img
                src={getImageUrl(result.image_url)}
                alt={`Match ${result.photo_id}`}
                style={styles.image}
                loading="lazy"
              />
              {showSimilarity && (
                <div style={styles.overlay}>
                  <div style={styles.similarityBadge}>
                    {(result.similarity * 100).toFixed(1)}% match
                  </div>
                </div>
              )}
            </div>
            <div style={styles.cardInfo}>
              {result.event_tag && (
                <span style={styles.eventTag}>{result.event_tag}</span>
              )}
              <div style={styles.dimensions}>
                {result.width} × {result.height}
              </div>
            </div>
          </div>
        ))}
      </div>

      {totalPages > 1 && (
        <div style={styles.pagination}>
          <button
            onClick={() => handlePageChange(currentPage - 1)}
            disabled={currentPage === 1}
            style={{
              ...styles.pageButton,
              ...(currentPage === 1 ? styles.pageButtonDisabled : {}),
            }}
          >
            ← Previous
          </button>

          <div style={styles.pageNumbers}>
            {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
              <button
                key={page}
                onClick={() => handlePageChange(page)}
                style={{
                  ...styles.pageNumber,
                  ...(page === currentPage ? styles.pageNumberActive : {}),
                }}
              >
                {page}
              </button>
            ))}
          </div>

          <button
            onClick={() => handlePageChange(currentPage + 1)}
            disabled={currentPage === totalPages}
            style={{
              ...styles.pageButton,
              ...(currentPage === totalPages ? styles.pageButtonDisabled : {}),
            }}
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
};

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    width: '100%',
    marginTop: '40px',
  },
  header: {
    marginBottom: '24px',
    textAlign: 'center',
  },
  title: {
    fontSize: '24px',
    fontWeight: '700',
    color: '#2d3748',
    margin: '0 0 8px 0',
  },
  queryTime: {
    fontSize: '14px',
    color: '#718096',
    margin: 0,
  },
  pageInfo: {
    fontSize: '14px',
    color: '#a0aec0',
    margin: '4px 0 0 0',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
    gap: '24px',
    padding: '0',
  },
  card: {
    backgroundColor: 'white',
    borderRadius: '12px',
    overflow: 'hidden',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
    transition: 'transform 0.2s, box-shadow 0.2s',
    cursor: 'pointer',
  },
  imageContainer: {
    position: 'relative',
    width: '100%',
    paddingBottom: '100%',
    backgroundColor: '#f7fafc',
    overflow: 'hidden',
  },
  image: {
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    objectFit: 'cover',
  },
  overlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: 'linear-gradient(to bottom, rgba(0,0,0,0.6) 0%, transparent 30%)',
    opacity: 0,
    transition: 'opacity 0.2s',
    display: 'flex',
    alignItems: 'flex-start',
    justifyContent: 'center',
    padding: '12px',
  },
  similarityBadge: {
    backgroundColor: '#48bb78',
    color: 'white',
    padding: '6px 12px',
    borderRadius: '20px',
    fontSize: '13px',
    fontWeight: '600',
  },
  cardInfo: {
    padding: '12px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  eventTag: {
    fontSize: '13px',
    color: '#4299e1',
    fontWeight: '500',
  },
  dimensions: {
    fontSize: '12px',
    color: '#a0aec0',
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
  pagination: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    gap: '16px',
    marginTop: '40px',
    paddingBottom: '40px',
  },
  pageButton: {
    padding: '10px 20px',
    fontSize: '14px',
    fontWeight: '600',
    color: '#4299e1',
    backgroundColor: 'white',
    border: '2px solid #4299e1',
    borderRadius: '8px',
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
  pageButtonDisabled: {
    color: '#cbd5e0',
    borderColor: '#cbd5e0',
    cursor: 'not-allowed',
    opacity: 0.5,
  },
  pageNumbers: {
    display: 'flex',
    gap: '8px',
  },
  pageNumber: {
    padding: '8px 14px',
    fontSize: '14px',
    fontWeight: '500',
    color: '#4a5568',
    backgroundColor: 'white',
    border: '2px solid #e2e8f0',
    borderRadius: '6px',
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
  pageNumberActive: {
    color: 'white',
    backgroundColor: '#4299e1',
    borderColor: '#4299e1',
  },
};

// Add hover effect via CSS-in-JS workaround
const styleSheet = document.createElement('style');
styleSheet.textContent = `
  div[style*="cursor: pointer"]:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15) !important;
  }
  div[style*="cursor: pointer"]:hover div[style*="opacity: 0"] {
    opacity: 1 !important;
  }
`;
document.head.appendChild(styleSheet);

export default ResultsGrid;
