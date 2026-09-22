const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
const TOKEN_KEY = 'second_brain_token';

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

async function request(path, options = {}) {
  const token = getToken();
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers
    }
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return response.json();
}

/** Parse a JSON response without throwing on a malformed body. */
export async function readJson(res, fallback = null) {
  try {
    return await res.json();
  } catch {
    return fallback;
  }
}

/**
 * Read an endpoint that should return an array.
 * Returns [] for anything unexpected so `.map()` / `.filter()` can never crash
 * a page. Accepts bare arrays and { items: [...] } / { results: [...] } envelopes.
 */
export async function readList(res) {
  const data = await readJson(res, []);
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.items)) return data.items;
  if (Array.isArray(data?.results)) return data.results;
  return [];
}

/**
 * Authenticated fetch.
 * ---------------------------------------------------------------------------
 * Several screens called the backend with a RAW `fetch()`, which does NOT
 * attach the JWT. Every one of those requests came back 401, so those panels
 * silently rendered empty while looking perfectly fine.
 *
 * Use this instead of `fetch()` for every call to our own backend. Accepts a
 * full URL (`${apiClient.baseUrl}/api/...`) or a bare path (`/api/...`), and
 * does NOT throw on non-2xx - callers keep using `res.ok`.
 */
export async function apiFetch(url, options = {}) {
  const token = getToken();
  const target = /^https?:\/\//i.test(url) ? url : `${API_BASE_URL}${url}`;

  const headers = { ...(options.headers || {}) };
  if (token && !headers.Authorization) {
    headers.Authorization = `Bearer ${token}`;
  }
  if (options.body && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  return fetch(target, { ...options, headers });
}

/**
 * Open a URL in the user's real browser.
 * Google blocks OAuth consent inside embedded webviews, so in Electron we hand
 * off to the system browser through the preload bridge. In a normal browser we
 * fall back to window.open.
 */
export async function openInBrowser(url) {
  const bridge = typeof window !== 'undefined' ? window.secondBrain : null;
  if (bridge?.openExternal) {
    const result = await bridge.openExternal(url);
    if (result?.ok) return { ok: true };
    // fall through to the browser path if the bridge refused
  }
  const opened = typeof window !== 'undefined' ? window.open(url, '_blank', 'noopener,noreferrer') : null;
  return opened ? { ok: true } : { ok: false, error: 'Popup blocked - allow popups for this app.' };
}

export const apiClient = {
  baseUrl: API_BASE_URL,
  tokenKey: TOKEN_KEY,
  getToken,
  setToken,
  clearToken,
  health: () => request('/api/health'),
  login: async (username = 'Immanuel', password = 'secondbrain') => {
    const data = await request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password, device_name: 'electron-desktop' })
    });
    setToken(data.access_token);
    return data;
  },
  logout: async () => {
    const data = await request('/api/auth/logout', { method: 'POST' });
    clearToken();
    return data;
  },
  createSession: (deviceName = 'electron-desktop') =>
    request('/api/sessions', {
      method: 'POST',
      body: JSON.stringify({ device_name: deviceName })
    }),
  saveActivity: (activity) =>
    request('/api/activities', {
      method: 'POST',
      body: JSON.stringify(activity)
    }),
  fetchActivities: () => request('/api/activities'),
  fetchTimeline: () => request('/api/timeline'),
  updateSetting: (key, value) =>
    request('/api/settings', {
      method: 'PUT',
      body: JSON.stringify({ key, value })
    }),
  fetchSettings: () => request('/api/settings'),
  startCapture: (options = {}) =>
    request('/api/capture/start', {
      method: 'POST',
      body: JSON.stringify({
        session_type: options.sessionType || 'study',
        screenshot_interval_seconds: options.screenshotIntervalSeconds || 5,
        watched_folders: options.watchedFolders || [],
        excluded_apps: options.excludedApps || ['password', '1password', 'bitwarden', 'keepass', 'authenticator']
      })
    }),
  stopCapture: () => request('/api/capture/stop', { method: 'POST' }),
  pauseCapture: () => request('/api/capture/pause', { method: 'POST' }),
  resumeCapture: () => request('/api/capture/resume', { method: 'POST' }),
  captureStatus: () => request('/api/capture/status'),
  captureActivity: () => request('/api/capture/activity'),
  captureScreenshots: () => request('/api/capture/screenshots'),
  captureSessions: () => request('/api/capture/sessions'),
  ocrStatus: () => request('/api/ocr/status'),
  queueUnprocessedOcr: () => request('/api/ocr/queue-unprocessed', { method: 'POST' }),
  processOcrSession: (sessionId) => request(`/api/ocr/sessions/${sessionId}/process`, { method: 'POST' }),
  fetchExtractedTexts: (query = '') => request(`/api/ocr/texts${query ? `?q=${encodeURIComponent(query)}` : ''}`),
  fetchSemanticChunks: (query = '', sourceType = '') => {
    const params = new URLSearchParams();
    if (query) params.set('q', query);
    if (sourceType) params.set('source_type', sourceType);
    const suffix = params.toString() ? `?${params.toString()}` : '';
    return request(`/api/ocr/chunks${suffix}`);
  },
  fetchDetectedTopics: () => request('/api/ocr/topics'),
  fetchProcessedSessions: () => request('/api/ocr/sessions'),
  rebuildMemoryArchive: () => request('/api/memory/rebuild', { method: 'POST' }),
  rebuildMemorySession: (sessionId) => request(`/api/memory/sessions/${sessionId}/rebuild`, { method: 'POST' }),
  searchMemories: (filters = {}) => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value) params.set(key, value);
    });
    return request(`/api/memory/search${params.toString() ? `?${params.toString()}` : ''}`);
  },
  fetchMemoryTimeline: (filters = {}) => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value) params.set(key, value);
    });
    return request(`/api/memory/timeline${params.toString() ? `?${params.toString()}` : ''}`);
  },
  fetchMemorySessions: () => request('/api/memory/sessions'),
  fetchSessionMemories: (sessionId) => request(`/api/memory/sessions/${sessionId}/memories`),
  fetchMemoryRelationships: (memoryId) => request(`/api/memory/memories/${memoryId}/relationships`),
  fetchRelatedMemories: (memoryId) => request(`/api/memory/memories/${memoryId}/related`),
  fetchMemoryStats: () => request('/api/memory/stats'),
  exportSessionUrl: (sessionId) => `${API_BASE_URL}/api/memory/export/session/${sessionId}?token=${encodeURIComponent(getToken())}`,
  semanticStatus: () => request('/api/semantic/status'),
  indexSemanticMemories: () => request('/api/semantic/index', { method: 'POST' }),
  reindexSemanticMemories: () => request('/api/semantic/reindex', { method: 'POST' }),
  hybridSemanticSearch: (payload) =>
    request('/api/semantic/hybrid-search', {
      method: 'POST',
      body: JSON.stringify(payload)
    }),
  semanticSearch: (payload) =>
    request('/api/semantic/search', {
      method: 'POST',
      body: JSON.stringify(payload)
    }),
  relatedSemanticMemories: (memoryId) => request(`/api/semantic/related/${memoryId}`),
  assembleSemanticContext: (payload) =>
    request('/api/semantic/context', {
      method: 'POST',
      body: JSON.stringify(payload)
    }),
  rebuildSemanticClusters: () => request('/api/semantic/clusters/rebuild', { method: 'POST' }),
  detectSemanticRelationships: () => request('/api/semantic/relationships/detect', { method: 'POST' }),
  fetchSemanticClusters: () => request('/api/semantic/clusters'),
  fetchEmbeddingJobs: () => request('/api/semantic/jobs'),
  fetchSearchHistory: () => request('/api/semantic/history'),
  fetchConversations: () => request('/api/chat/conversations'),
  fetchConversationMessages: (conversationId) => request(`/api/chat/conversations/${conversationId}/messages`),
  fetchConversationRetrieved: (conversationId) => request(`/api/chat/conversations/${conversationId}/retrieved`),
  askMemory: (payload) =>
    request('/api/chat/ask', {
      method: 'POST',
      body: JSON.stringify(payload)
    }),
  voiceStatus: () => request('/api/voice/status'),
  startVoiceSession: (payload) =>
    request('/api/voice/sessions', {
      method: 'POST',
      body: JSON.stringify(payload)
    }),
  stopVoiceSession: (sessionId) => request(`/api/voice/sessions/${sessionId}/stop`, { method: 'POST' }),
  fetchVoiceSessions: () => request('/api/voice/sessions'),
  fetchVoiceTranscripts: (sessionId) => request(`/api/voice/sessions/${sessionId}/transcripts`),
  fetchVoicePreferences: () => request('/api/voice/preferences'),
  updateVoicePreferences: (payload) =>
    request('/api/voice/preferences', {
      method: 'PUT',
      body: JSON.stringify(payload)
    }),
  voiceAudioUrl: (audioId) => `${API_BASE_URL}/api/voice/audio/${audioId}?token=${encodeURIComponent(getToken())}`,

  // ---- Google Workspace integration (Gmail + Calendar) -------------------
  googleStatus: () => request('/api/google/status'),
  googleAccounts: () => request('/api/google/accounts'),
  googleConnect: (email, services = ['gmail', 'calendar']) =>
    request('/api/google/connect', {
      method: 'POST',
      body: JSON.stringify({ email, services })
    }),
  googleDisconnect: (accountId) =>
    request(`/api/google/accounts/${accountId}`, { method: 'DELETE' }),
  gmailMessages: (accountId, q = '', limit = 25) => {
    const params = new URLSearchParams({ account_id: accountId, limit: String(limit) });
    if (q) params.set('q', q);
    return request(`/api/google/gmail/messages?${params.toString()}`);
  },
  gmailMessage: (accountId, messageId) =>
    request(`/api/google/gmail/message/${messageId}?account_id=${encodeURIComponent(accountId)}`),
  calendarEvents: (accountId, daysAhead = 7, daysBack = 1) =>
    request(`/api/google/calendar/events?account_id=${encodeURIComponent(accountId)}` +
            `&days_ahead=${daysAhead}&days_back=${daysBack}`),
  calendarList: (accountId) =>
    request(`/api/google/calendar/calendars?account_id=${encodeURIComponent(accountId)}`)
};
