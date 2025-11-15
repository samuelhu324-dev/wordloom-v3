/**
 * Application Configuration
 * Reads from environment variables (.env.local, .env.production)
 */

export const config = {
  api: {
    baseUrl: process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000/api',
    timeout: parseInt(process.env.NEXT_PUBLIC_API_TIMEOUT || '10000', 10),
  },
  theme: {
    default: (process.env.NEXT_PUBLIC_DEFAULT_THEME as 'Light' | 'Dark' | 'Loom') || 'Light',
  },
};
