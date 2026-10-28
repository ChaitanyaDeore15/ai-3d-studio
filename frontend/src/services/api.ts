import {
  GenerationCreateRequest,
  GenerationJob,
  Asset,
  Project,
  SystemCapabilities,
  RefineRequest,
  User
} from '../types';

const RAW_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');
export const API_BASE = RAW_BASE ? `${RAW_BASE}/api` : '/api';

export function resolveAssetUrl(url: string | null | undefined): string {
  if (!url) return '';
  if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('blob:')) {
    return url;
  }
  return RAW_BASE ? `${RAW_BASE}${url}` : url;
}

export function getAuthToken(): string | null {
  return localStorage.getItem('ai3d_token');
}

export function setAuthToken(token: string | null) {
  if (token) {
    localStorage.setItem('ai3d_token', token);
  } else {
    localStorage.removeItem('ai3d_token');
  }
}

function getAuthHeaders(): HeadersInit {
  const token = getAuthToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json'
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

// --- Auth API ---
export async function registerUser(email: string, username: string, password: string): Promise<{ access_token: string; user: User }> {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, username, password })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Registration failed');
  }
  const data = await res.json();
  setAuthToken(data.access_token);
  return data;
}

export async function loginUser(email_or_username: string, password: string): Promise<{ access_token: string; user: User }> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email_or_username, password })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Login failed');
  }
  const data = await res.json();
  setAuthToken(data.access_token);
  return data;
}

export async function fetchCurrentUser(): Promise<User | null> {
  const token = getAuthToken();
  if (!token) return null;
  const res = await fetch(`${API_BASE}/auth/me`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) {
    setAuthToken(null);
    return null;
  }
  return res.json();
}

// --- System & Capabilities API ---
export async function fetchHealth(): Promise<{ status: string; blender_available: boolean; blender_version?: string }> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
  return res.json();
}

export async function fetchCapabilities(): Promise<SystemCapabilities> {
  const res = await fetch(`${API_BASE}/capabilities`);
  if (!res.ok) throw new Error(`Capabilities check failed: ${res.statusText}`);
  return res.json();
}

// --- Generation API ---
export async function submitGeneration(payload: GenerationCreateRequest): Promise<GenerationJob> {
  const res = await fetch(`${API_BASE}/generations`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorData.detail || 'Generation request failed');
  }
  return res.json();
}

export async function getGenerationJob(jobId: string): Promise<GenerationJob> {
  const res = await fetch(`${API_BASE}/generations/${jobId}`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error(`Failed to query job ${jobId}`);
  return res.json();
}

export async function cancelGenerationJob(jobId: string): Promise<void> {
  await fetch(`${API_BASE}/generations/${jobId}/cancel`, {
    method: 'POST',
    headers: getAuthHeaders()
  });
}

// --- Assets API ---
export async function fetchAssets(projectId?: string): Promise<Asset[]> {
  const url = projectId ? `${API_BASE}/assets?project_id=${projectId}` : `${API_BASE}/assets`;
  const res = await fetch(url, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error('Failed to load assets');
  const data: Asset[] = await res.json();
  return data.map((a) => ({ ...a, download_url: resolveAssetUrl(a.download_url) }));
}

export async function fetchAsset(assetId: string): Promise<Asset> {
  const res = await fetch(`${API_BASE}/assets/${assetId}`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error(`Asset not found: ${assetId}`);
  const data: Asset = await res.json();
  data.download_url = resolveAssetUrl(data.download_url);
  return data;
}

export async function updateAsset(assetId: string, projectId: string | null): Promise<Asset> {
  const res = await fetch(`${API_BASE}/assets/${assetId}`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
    body: JSON.stringify({ project_id: projectId })
  });
  if (!res.ok) throw new Error('Failed to update asset');
  return res.json();
}

export async function deleteAsset(assetId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/assets/${assetId}`, {
    method: 'DELETE',
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error('Failed to delete asset');
}

export async function requestExport(assetId: string, requestedFormat: 'glb' | 'gltf_zip'): Promise<{ id: string; status: string }> {
  const res = await fetch(`${API_BASE}/assets/${assetId}/exports`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ requested_format: requestedFormat })
  });
  if (!res.ok) throw new Error('Export request failed');
  return res.json();
}

export async function getExportJob(exportId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/exports/${exportId}`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error('Failed to check export job');
  return res.json();
}

export async function submitRefinement(assetId: string, payload: RefineRequest): Promise<GenerationJob> {
  const res = await fetch(`${API_BASE}/refine/${assetId}`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorData.detail || 'Refinement request failed');
  }
  return res.json();
}

export async function uploadReferenceImage(file: File): Promise<{ upload_id: string; filename: string }> {
  const formData = new FormData();
  formData.append('file', file);
  const token = getAuthToken();
  const headers: Record<string, string> = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}/uploads`, {
    method: 'POST',
    headers,
    body: formData
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Failed to upload reference image');
  }
  return res.json();
}

// --- Projects API ---
export async function fetchProjects(): Promise<Project[]> {
  const res = await fetch(`${API_BASE}/projects`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error('Failed to fetch projects');
  return res.json();
}

export async function createProject(name: string, description?: string): Promise<Project> {
  const res = await fetch(`${API_BASE}/projects`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ name, description })
  });
  if (!res.ok) throw new Error('Failed to create project');
  return res.json();
}

export async function deleteProject(projectId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/projects/${projectId}`, {
    method: 'DELETE',
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error('Failed to delete project');
}
