import { API_CONFIG } from '../constants/config';
import type { User, LoginCredentials } from '../types';

/**
 * API Service for backend communication
 */
class APIService {
  private baseURL: string;
  private timeout: number;

  constructor() {
    this.baseURL = API_CONFIG.baseURL;
    this.timeout = API_CONFIG.timeout;
  }

  /**
   * Make HTTP request with timeout
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    // Auto-add Authorization header if token exists
    const token = localStorage.getItem('token');
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    };
    
    if (token && !headers['Authorization']) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(`${this.baseURL}${endpoint}`, {
        ...options,
        headers,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new Error('Request timeout');
        }
        throw error;
      }
      throw new Error('Unknown error occurred');
    }
  }

  /**
   * Register new user
   */
  async register(data: { email: string; password: string; name?: string }): Promise<{ user: User; token: string }> {
    // Truncate password to 72 characters (bcrypt limitation)
    const truncatedPassword = data.password.substring(0, 72);
    const registerData = {
      email: data.email,
      name: data.name || '',
      password: truncatedPassword
    };
    
    const response = await this.request<{ access_token: string; token_type: string; user: any }>
      ('/api/auth/register',
      {
        method: 'POST',
        body: JSON.stringify(registerData),
      }
    );
    
    // Store token
    localStorage.setItem('token', response.access_token);
    
    // Decode JWT for role (same as login)
    let jwtRole: string | undefined;
    let jwtIsAdmin: boolean = false;
    try {
      const tokenParts = response.access_token.split('.');
      const payload = JSON.parse(atob(tokenParts[1]));
      jwtRole = payload.role;
      jwtIsAdmin = payload.is_admin || false;
    } catch (e) {
      console.error('❌ Failed to decode token in register:', e);
    }
    
    // Map backend user object to frontend User type
    // Priority: JWT role > response.user role
    const user: User = {
      email: response.user.email,
      name: response.user.name || response.user.email.split('@')[0],
      role: (jwtRole?.toLowerCase() === 'admin' || jwtIsAdmin || response.user.role?.toLowerCase() === 'admin' || response.user.is_admin) ? 'admin' : 'user'
    };
    
    return {
      user,
      token: response.access_token,
    };
  }

  /**
   * Login user
   */
  async login(credentials: LoginCredentials): Promise<{ user: User; token: string }> {
    // Truncate password to 72 characters (bcrypt limitation)
    const truncatedPassword = credentials.password.substring(0, 72);
    const loginData = {
      email: credentials.email,
      password: truncatedPassword
    };
    
    const response = await this.request<{ access_token: string; token_type: string; user: any }>(
      '/api/auth/login',
      {
        method: 'POST',
        body: JSON.stringify(loginData),
      }
    );

    // Initialize JWT variables
    let jwtRole: string | undefined;
    let jwtIsAdmin: boolean = false;

    // Store token in localStorage
    if (response.access_token) {
      localStorage.setItem('token', response.access_token);
      
      // Debug: Decode and log JWT token payload
      try {
        const tokenParts = response.access_token.split('.');
        const payload = JSON.parse(atob(tokenParts[1]));
        jwtRole = payload.role;
        jwtIsAdmin = payload.is_admin || false;
        console.log('🔑 JWT Token Payload:', payload);
      } catch (e) {
        console.error('❌ Failed to decode token:', e);
      }
    }

    // Debug: Log response
    console.log('🔍 Login Response:', {
      user: response.user,
      has_role: response.user.role,
      has_is_admin: response.user.is_admin,
      jwt_role: jwtRole,
      jwt_is_admin: jwtIsAdmin,
      role_calculated: (jwtRole?.toLowerCase() === 'admin' || jwtIsAdmin || response.user.role?.toLowerCase() === 'admin' || response.user.is_admin) ? 'admin' : 'user'
    });

    // Map backend user object to frontend User type
    // Priority: JWT role > response.user role
    const user: User = {
      email: response.user.email,
      name: response.user.name || response.user.email.split('@')[0],
      role: (jwtRole?.toLowerCase() === 'admin' || jwtIsAdmin || response.user.role?.toLowerCase() === 'admin' || response.user.is_admin) ? 'admin' : 'user'
    };

    console.log('✅ Final User Object:', user);

    return {
      user,
      token: response.access_token,
    };
  }

  /**
   * Logout user
   */
  logout(): void {
    localStorage.removeItem('token');
  }

  /**
   * Get current user profile
   */
  async getCurrentUser(): Promise<User> {
    const token = localStorage.getItem('token');
    if (!token) {
      throw new Error('No authentication token found');
    }

    const backendUser = await this.request<any>('/api/auth/me', {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    // Decode JWT token to get role
    let jwtRole: string | undefined;
    let jwtIsAdmin: boolean = false;
    try {
      const tokenParts = token.split('.');
      const payload = JSON.parse(atob(tokenParts[1]));
      jwtRole = payload.role;
      jwtIsAdmin = payload.is_admin || false;
      console.log('🔑 JWT in getCurrentUser:', { role: jwtRole, is_admin: jwtIsAdmin });
    } catch (e) {
      console.error('❌ Failed to decode token in getCurrentUser:', e);
    }

    console.log('👤 Backend user in getCurrentUser:', {
      ...backendUser,
      jwt_role: jwtRole,
      jwt_is_admin: jwtIsAdmin
    });

    // Map backend user object to frontend User type
    // Priority: JWT role > backendUser.role > backendUser.is_admin
    const user: User = {
      email: backendUser.email,
      name: backendUser.name || backendUser.email.split('@')[0],
      role: (jwtRole?.toLowerCase() === 'admin' || jwtIsAdmin || backendUser.role?.toLowerCase() === 'admin' || backendUser.is_admin) ? 'admin' : 'user'
    };

    console.log('✅ Final user in getCurrentUser:', user);
    return user;
  }

  /**
   * Update user profile
   */
  async updateProfile(name: string, email: string): Promise<User> {
    const token = localStorage.getItem('token');
    if (!token) {
      throw new Error('No authentication token found');
    }

    const backendUser = await this.request<any>('/api/auth/profile', {
      method: 'PUT',
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ name, email }),
    });

    // Map backend user object to frontend User type
    return {
      email: backendUser.email,
      name: backendUser.name || backendUser.email.split('@')[0],
      role: backendUser.is_admin ? 'admin' : 'user'
    };

    // Map backend user object to frontend User type
    return {
      email: backendUser.email,
      name: backendUser.name || backendUser.email.split('@')[0],
      role: backendUser.is_admin ? 'admin' : 'user'
    };
  }

  /**
   * Upload invoice image for OCR processing
   */
  async uploadInvoice(file: File): Promise<{ job_id: string; status: string }> {
    const token = localStorage.getItem('token');
    const formData = new FormData();
    formData.append('file', file);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(`${this.baseURL}/api/upload`, {
        method: 'POST',
        headers: {
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: formData,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
        throw new Error(error.detail || 'Upload failed');
      }

      return await response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new Error('Upload timeout');
        }
        throw error;
      }
      throw new Error('Upload failed');
    }
  }

  /**
   * Get invoices list
   */
  async getInvoices(params?: {
    skip?: number;
    limit?: number;
    status?: string;
  }): Promise<{ invoices: any[]; total: number }> {
    const token = localStorage.getItem('token');
    const queryParams = new URLSearchParams();
    
    if (params?.skip) queryParams.append('skip', params.skip.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.status) queryParams.append('status', params.status);

    const endpoint = `/api/invoices${queryParams.toString() ? `?${queryParams}` : ''}`;

    return await this.request(endpoint, {
      headers: {
        ...(token && { Authorization: `Bearer ${token}` }),
      },
    });
  }

  /**
   * Get invoice statistics
   */
  async getInvoiceStats(): Promise<{
    total: number;
    processed: number;
    pending: number;
    failed: number;
  }> {
    const token = localStorage.getItem('token');
    
    return await this.request('/api/invoices/stats', {
      headers: {
        ...(token && { Authorization: `Bearer ${token}` }),
      },
    });
  }

  /**
   * Send chat message
   */
  async sendChatMessage(message: string): Promise<{ response: string }> {
    const token = localStorage.getItem('token');
    
    return await this.request('/api/chat/', {
      method: 'POST',
      headers: {
        ...(token && { Authorization: `Bearer ${token}` }),
      },
      body: JSON.stringify({ message }),
    });
  }

  /**
   * Get all users (Admin only)
   */
  async getAllUsers(): Promise<any[]> {
    const token = localStorage.getItem('token');
    if (!token) {
      throw new Error('No authentication token');
    }
    
    console.log('🔑 Sending request with token:', token.substring(0, 20) + '...');
    
    return await this.request('/api/admin/users', {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  }

  /**
   * Get user statistics (Admin only)
   */
  async getUserStatistics(): Promise<any> {
    const token = localStorage.getItem('token');
    if (!token) {
      throw new Error('No authentication token');
    }
    
    return await this.request('/api/admin/users/statistics', {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  }

  /**
   * Get invoice statistics (Admin only)
   */
  async getInvoiceStatistics(): Promise<any> {
    const token = localStorage.getItem('token');
    if (!token) {
      throw new Error('No authentication token');
    }
    
    return await this.request('/api/admin/invoices/statistics', {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  }

  /**
   * Create a new invoice (Admin only)
   */
  async createInvoice(invoiceData: any): Promise<any> {
    const token = localStorage.getItem('token');
    if (!token) {
      throw new Error('No authentication token');
    }
    
    return await this.request('/api/invoices/create', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(invoiceData),
    });
  }

  /**
   * Get recent activities (Admin only)
   */
  async getRecentActivities(): Promise<any> {
    const token = localStorage.getItem('token');
    if (!token) {
      throw new Error('No authentication token');
    }
    
    return await this.request('/api/admin/activities/recent', {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  }

  /**
   * Get top users (Admin only)
   */
  async getTopUsers(): Promise<any> {
    const token = localStorage.getItem('token');
    if (!token) {
      throw new Error('No authentication token');
    }
    
    return await this.request('/api/admin/users/top', {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  }

  /**
   * Get monthly statistics (Admin only)
   */
  async getMonthlyStatistics(): Promise<any> {
    const token = localStorage.getItem('token');
    if (!token) {
      throw new Error('No authentication token');
    }
    
    return await this.request('/api/admin/statistics/monthly', {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  }

  /**
   * Check backend health
   */
  async healthCheck(): Promise<{ status: string; version: string }> {
    return await this.request('/health');
  }
}

export const apiService = new APIService();
export default apiService;
