const BASE_URL = import.meta.env.VITE_API_URL || '';

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async get<T>(path: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return response.json();
  }

  getLoginUrl(name: string): string {
    return `${this.baseUrl}/login/${encodeURIComponent(name)}`;
  }
}

export const apiClient = new ApiClient();
