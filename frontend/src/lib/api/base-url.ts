const LOCAL_API_BASE = 'http://127.0.0.1:8000/api/v1';
const PROD_API_BASE = 'https://rural-ai-doctor.onrender.com/api/v1';

export function getApiBaseUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (configured) {
    return configured.replace(/\/$/, '');
  }

  if (typeof window !== 'undefined') {
    const host = window.location.hostname;
    if (host === 'localhost' || host === '127.0.0.1') {
      return LOCAL_API_BASE;
    }
  }

  return PROD_API_BASE;
}
