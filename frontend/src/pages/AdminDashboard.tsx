import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './AdminDashboard.css';

interface Photo {
  id: string;
  path: string;
  image_url: string;
  event_tag: string | null;
  width: number;
  height: number;
  created_at: string;
  face_count?: number;
}

interface Stats {
  total_photos: number;
  total_faces: number;
  event_tags: string[];
}

const AdminDashboard: React.FC = () => {
  const [photos, setPhotos] = useState<Photo[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [editingPhoto, setEditingPhoto] = useState<string | null>(null);
  const [editTag, setEditTag] = useState('');
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadEventTag, setUploadEventTag] = useState('');
  const [viewingImage, setViewingImage] = useState<Photo | null>(null);
  const navigate = useNavigate();

  const username = localStorage.getItem('adminUsername');
  const token = localStorage.getItem('adminToken');

  useEffect(() => {
    if (!token) {
      navigate('/admin/login');
      return;
    }
    loadData();
  }, [token, navigate]);

  const getAuthHeaders = () => {
    return {
      'Authorization': `Basic ${btoa('admin:admin')}`,
    };
  };

  const getImageUrl = (imageUrl: string): string => {
    if (imageUrl.startsWith('http')) {
      return imageUrl;
    }
    return `http://localhost:8001${imageUrl}`;
  };

  const handleDownloadImage = async (photo: Photo) => {
    try {
      const imageUrl = getImageUrl(photo.image_url);
      const response = await fetch(imageUrl);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = photo.path.split('/').pop() || 'image.jpg';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading image:', error);
      alert('Lỗi khi tải ảnh');
    }
  };

  const loadData = async () => {
    try {
      setLoading(true);

      // Load photos
      const photosResponse = await fetch('/api/admin/photos?limit=100&offset=0', {
        headers: getAuthHeaders(),
      });

      if (photosResponse.status === 401) {
        localStorage.removeItem('adminToken');
        localStorage.removeItem('adminUsername');
        navigate('/admin/login');
        return;
      }

      const photosData = await photosResponse.json();
      setPhotos(photosData.photos);

      // Load stats
      const statsResponse = await fetch('/api/admin/stats', {
        headers: getAuthHeaders(),
      });
      const statsData = await statsResponse.json();
      setStats(statsData);
    } catch (error) {
      console.error('Error loading data:', error);
      alert('Lỗi khi tải dữ liệu');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('adminToken');
    localStorage.removeItem('adminUsername');
    navigate('/admin/login');
  };

  const handleEditTag = (photo: Photo) => {
    setEditingPhoto(photo.id);
    setEditTag(photo.event_tag || '');
  };

  const handleSaveTag = async (photoId: string) => {
    try {
      const response = await fetch(`/api/admin/photos/${photoId}`, {
        method: 'PUT',
        headers: {
          ...getAuthHeaders(),
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ event_tag: editTag || null }),
      });

      if (response.ok) {
        await loadData();
        setEditingPhoto(null);
      } else {
        alert('Lỗi khi cập nhật tag');
      }
    } catch (error) {
      console.error('Error updating tag:', error);
      alert('Lỗi khi cập nhật tag');
    }
  };

  const handleCancelEdit = () => {
    setEditingPhoto(null);
    setEditTag('');
  };

  const handleDelete = async (photoId: string) => {
    if (deleteConfirm !== photoId) {
      setDeleteConfirm(photoId);
      return;
    }

    try {
      const response = await fetch(`/api/admin/photos/${photoId}`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
      });

      if (response.ok) {
        await loadData();
        setDeleteConfirm(null);
        alert('Đã xóa ảnh thành công');
      } else {
        alert('Lỗi khi xóa ảnh');
      }
    } catch (error) {
      console.error('Error deleting photo:', error);
      alert('Lỗi khi xóa ảnh');
    }
  };

  const handleUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    setUploading(true);

    try {
      for (const file of Array.from(files)) {
        const formData = new FormData();
        formData.append('file', file);
        if (uploadEventTag) {
          formData.append('event_tag', uploadEventTag);
        }

        const response = await fetch('/api/admin/upload', {
          method: 'POST',
          headers: getAuthHeaders(),
          body: formData,
        });

        if (!response.ok) {
          const error = await response.json();
          alert(`Lỗi upload ${file.name}: ${error.detail || 'Unknown error'}`);
        }
      }

      // Reload data after upload
      await loadData();
      setUploadEventTag('');
      alert('Upload thành công!');
    } catch (error) {
      console.error('Error uploading:', error);
      alert('Lỗi khi upload ảnh');
    } finally {
      setUploading(false);
      // Reset file input
      event.target.value = '';
    }
  };

  if (loading) {
    return (
      <div className="admin-container">
        <div className="loading">Đang tải...</div>
      </div>
    );
  }

  return (
    <div className="admin-container">
      <header className="admin-header">
        <div className="header-content">
          <h1>📸 PhotoMatch Admin</h1>
          <div className="header-actions">
            <span className="username">Xin chào, {username}</span>
            <button onClick={() => navigate('/')} className="btn-home">
              Về Trang Chủ
            </button>
            <button onClick={handleLogout} className="btn-logout">
              Đăng xuất
            </button>
          </div>
        </div>
      </header>

      <div className="admin-content">
        {stats && (
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-value">{stats.total_photos}</div>
              <div className="stat-label">Tổng số ảnh</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{stats.total_faces}</div>
              <div className="stat-label">Tổng số khuôn mặt</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{stats.event_tags.length}</div>
              <div className="stat-label">Số sự kiện</div>
            </div>
          </div>
        )}

        <div className="photos-section">
          <div className="section-header">
            <h2>Quản lý ảnh</h2>
            <div className="header-buttons">
              <div className="upload-section">
                <input
                  type="text"
                  placeholder="Event tag (optional)"
                  value={uploadEventTag}
                  onChange={(e) => setUploadEventTag(e.target.value)}
                  className="upload-tag-input"
                />
                <label className="btn-upload">
                  {uploading ? '⏳ Đang upload...' : '📤 Upload ảnh'}
                  <input
                    type="file"
                    multiple
                    accept="image/*"
                    onChange={handleUpload}
                    disabled={uploading}
                    style={{ display: 'none' }}
                  />
                </label>
              </div>
              <button onClick={loadData} className="btn-refresh">
                🔄 Làm mới
              </button>
            </div>
          </div>

          {photos.length === 0 ? (
            <div className="empty-state">Không có ảnh nào trong database</div>
          ) : (
            <div className="photos-grid">
              {photos.map((photo) => (
                <div key={photo.id} className="photo-card">
                  <div className="photo-image-container" onClick={() => setViewingImage(photo)}>
                    <img
                      src={getImageUrl(photo.image_url)}
                      alt={photo.path}
                      className="photo-image"
                      onError={(e) => {
                        (e.target as HTMLImageElement).src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="200" height="200"%3E%3Crect fill="%23ddd" width="200" height="200"/%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" dy=".3em" fill="%23999"%3ENo Image%3C/text%3E%3C/svg%3E';
                      }}
                    />
                    <div className="image-overlay">
                      <span className="zoom-icon">🔍</span>
                    </div>
                    {photo.face_count !== undefined && photo.face_count > 0 && (
                      <div className="face-badge">{photo.face_count} khuôn mặt</div>
                    )}
                  </div>

                  <div className="photo-info">
                    <div className="photo-path" title={photo.path}>
                      {photo.path.split('/').pop()}
                    </div>

                    {editingPhoto === photo.id ? (
                      <div className="edit-tag-form">
                        <input
                          type="text"
                          value={editTag}
                          onChange={(e) => setEditTag(e.target.value)}
                          placeholder="Event tag"
                          className="tag-input"
                        />
                        <div className="edit-actions">
                          <button
                            onClick={() => handleSaveTag(photo.id)}
                            className="btn-save"
                          >
                            ✓ Lưu
                          </button>
                          <button onClick={handleCancelEdit} className="btn-cancel">
                            ✕ Hủy
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="photo-tag">
                        <span className="tag-label">
                          {photo.event_tag || <em>Chưa có tag</em>}
                        </span>
                      </div>
                    )}

                    <div className="photo-meta">
                      <small>{photo.width} × {photo.height}</small>
                      <small>{new Date(photo.created_at).toLocaleDateString('vi-VN')}</small>
                    </div>

                    <div className="photo-actions">
                      {editingPhoto !== photo.id && (
                        <>
                          <button
                            onClick={() => handleEditTag(photo)}
                            className="btn-edit"
                          >
                            ✏️ Sửa tag
                          </button>
                          <button
                            onClick={() => handleDownloadImage(photo)}
                            className="btn-download"
                          >
                            📥 Tải về
                          </button>
                        </>
                      )}
                      <button
                        onClick={() => handleDelete(photo.id)}
                        className={`btn-delete ${deleteConfirm === photo.id ? 'confirm' : ''}`}
                      >
                        {deleteConfirm === photo.id ? '⚠️ Xác nhận xóa?' : '🗑️ Xóa'}
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Image Viewer Modal */}
      {viewingImage && (
        <div className="image-modal" onClick={() => setViewingImage(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{viewingImage.path.split('/').pop()}</h3>
              <div className="modal-actions">
                <button
                  onClick={() => handleDownloadImage(viewingImage)}
                  className="btn-modal-download"
                >
                  📥 Tải về
                </button>
                <button
                  onClick={() => setViewingImage(null)}
                  className="btn-modal-close"
                >
                  ✕
                </button>
              </div>
            </div>
            <div className="modal-body">
              <img
                src={getImageUrl(viewingImage.image_url)}
                alt={viewingImage.path}
                className="modal-image"
              />
            </div>
            <div className="modal-footer">
              <div className="modal-info">
                <span>📐 {viewingImage.width} × {viewingImage.height}</span>
                {viewingImage.event_tag && <span>🏷️ {viewingImage.event_tag}</span>}
                {viewingImage.face_count !== undefined && viewingImage.face_count > 0 && (
                  <span>👤 {viewingImage.face_count} khuôn mặt</span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;
