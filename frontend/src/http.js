export class ApiError extends Error {
  constructor(status, detail) {
    const text = Array.isArray(detail) ? detail.map(issue => issue.msg).join('；') : detail;
    super(text || '连接失败，请稍后重试。');
    this.status = status;
  }
}

export async function request(path, {token, method = 'GET', data, raw = false} = {}) {
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  if (data) headers['Content-Type'] = 'application/json';
  const response = await fetch(`/api${path}`, {method, headers, body: data ? JSON.stringify(data) : undefined});
  if (!response.ok) {
    const failure = await response.json().catch(() => ({}));
    throw new ApiError(response.status, failure.detail);
  }
  return raw ? response.blob() : response.json();
}
