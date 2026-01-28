import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001/api';

export interface SearchResult {
  photo_id: string;
  image_url: string;
  similarity: number;
  event_tag?: string;
  width: number;
  height: number;
}

export interface SearchResponse {
  results: SearchResult[];
  query_time_ms: number;
  face_detected: boolean;
  message?: string;
}

export interface PhotoItem {
  photo_id: string;
  image_url: string;
  event_tag?: string;
  width: number;
  height: number;
  created_at: string;
}

export interface PhotoListResponse {
  photos: PhotoItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  database: string;
  face_model: string;
}

export const searchByImage = async (
  file: File,
  topK: number = 30,
  threshold: number = 0.6,
  eventTag?: string
): Promise<SearchResponse> => {
  const formData = new FormData();
  formData.append('file', file);

  const params = new URLSearchParams();
  params.append('top_k', topK.toString());
  params.append('threshold', threshold.toString());
  if (eventTag) {
    params.append('event_tag', eventTag);
  }

  const response = await axios.post<SearchResponse>(
    `${API_BASE_URL}/search?${params.toString()}`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );

  return response.data;
};

export const getPhotos = async (
  page: number = 1,
  pageSize: number = 20,
  eventTag?: string
): Promise<PhotoListResponse> => {
  const params = new URLSearchParams();
  params.append('page', page.toString());
  params.append('page_size', pageSize.toString());
  if (eventTag) {
    params.append('event_tag', eventTag);
  }

  const response = await axios.get<PhotoListResponse>(
    `${API_BASE_URL}/photos?${params.toString()}`
  );

  return response.data;
};

export const checkHealth = async (): Promise<HealthResponse> => {
  const response = await axios.get<HealthResponse>(`${API_BASE_URL}/health`);
  return response.data;
};

// Helper to get full image URL
export const getImageUrl = (imageUrl: string): string => {
  // If already an absolute URL, return as-is
  if (imageUrl.startsWith('http')) {
    return imageUrl;
  }
  // If it's a relative path (e.g., /static/...), return as-is
  // The browser will handle it relative to the current origin
  return imageUrl;
};
