const BASE_URL = import.meta.env.VITE_API_URL || '';

export class ApiClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string = BASE_URL) {
    this.baseUrl = baseUrl;
  }

  setToken(token: string): void {
    this.token = token;
    console.log('[ApiClient] Token set');
  }

  clearToken(): void {
    this.token = null;
    console.log('[ApiClient] Token cleared');
  }

  private getHeaders(contentType?: string): Record<string, string> {
    const headers: Record<string, string> = {};
    if (contentType) {
      headers['Content-Type'] = contentType;
    }
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    return headers;
  }

  async get<T>(path: string): Promise<T> {
    console.log(`[ApiClient] GET ${path}`);
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: 'GET',
      headers: this.getHeaders('application/json'),
      credentials: 'include',
    });

    if (!response.ok) {
      console.error(`[ApiClient] GET ${path} failed with status ${response.status}`);
      throw new Error(`API error: ${response.status}`);
    }

    console.log(`[ApiClient] GET ${path} succeeded`);
    return response.json();
  }

  async post<T>(path: string, body: unknown): Promise<T> {
    console.log(`[ApiClient] POST ${path}`);
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: 'POST',
      headers: this.getHeaders('application/json'),
      credentials: 'include',
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      console.error(`[ApiClient] POST ${path} failed with status ${response.status}`);
      throw new Error(`API error: ${response.status}`);
    }

    console.log(`[ApiClient] POST ${path} succeeded`);
    return response.json();
  }

  async postForm<T>(path: string, data: Record<string, string>): Promise<T> {
    console.log(`[ApiClient] POST (form) ${path}`);
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: 'POST',
      headers: this.getHeaders('application/x-www-form-urlencoded'),
      credentials: 'include',
      body: new URLSearchParams(data).toString(),
    });

    if (!response.ok) {
      console.error(`[ApiClient] POST (form) ${path} failed with status ${response.status}`);
      throw new Error(`API error: ${response.status}`);
    }

    console.log(`[ApiClient] POST (form) ${path} succeeded`);
    return response.json();
  }

  async postEmpty(path: string): Promise<void> {
    console.log(`[ApiClient] POST (empty) ${path}`);
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: 'POST',
      headers: this.getHeaders(),
      credentials: 'include',
    });

    if (!response.ok) {
      console.error(`[ApiClient] POST (empty) ${path} failed with status ${response.status}`);
      throw new Error(`API error: ${response.status}`);
    }

    console.log(`[ApiClient] POST (empty) ${path} succeeded`);
  }

  getLoginUrl(name: string): string {
    return `${this.baseUrl}/login/${encodeURIComponent(name)}`;
  }
}

export const apiClient = new ApiClient();
