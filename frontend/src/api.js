import axios from 'axios';

// ==========================================
// CẤU HÌNH API - DÙNG API GATEWAY
// ==========================================
const API_GATEWAY = 'http://localhost:8000';

const SERVICE_PATHS = {
    USER: '/api/users',
    PRODUCT: '/api/products',
    ORDER: '/api/orders',
    PAYMENT: '/api/payments'
};

// Helper lấy URL ảnh
export const getImageUrl = (path) => {
    if (!path) return 'https://placehold.co/400x300?text=No+Image';
    if (path.startsWith('http')) return path;
    return `${API_GATEWAY}/api/products${path}`;
};

// ==========================================
// TẠO AXIOS CLIENTS
// ==========================================
const createClient = (servicePath) => {
    const client = axios.create({ 
        baseURL: `${API_GATEWAY}${servicePath}`,
        timeout: 10000,
        headers: {
            'Content-Type': 'application/json'
        }
    });
    
    // Interceptor tự động thêm token
    client.interceptors.request.use((config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    }, (error) => {
        return Promise.reject(error);
    });
    
    // Interceptor xử lý lỗi
    client.interceptors.response.use(
        (response) => response,
        (error) => {
            if (error.response?.status === 401) {
                localStorage.removeItem('token');
                localStorage.removeItem('user');
                window.location.href = '/login';
            }
            return Promise.reject(error);
        }
    );
    
    return client;
};

// Export các API clients
export const userApi = createClient(SERVICE_PATHS.USER);
export const productApi = createClient(SERVICE_PATHS.PRODUCT);
export const orderApi = createClient(SERVICE_PATHS.ORDER);
export const paymentApi = createClient(SERVICE_PATHS.PAYMENT);

// ==========================================
// [FIX CRITICAL] AUTH API - Special Endpoints
// ==========================================
export const authApi = {
    // [FIX] Login với form-urlencoded
    login: async (username, password) => {
        // CRITICAL: Backend expects OAuth2PasswordRequestForm
        // Content-Type PHẢI là application/x-www-form-urlencoded
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);
        
        const response = await axios.post(
            `${API_GATEWAY}/token`,  // Không có /api/users prefix
            formData.toString(),      // Convert to string
            {
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            }
        );
        return response;
    },
    
    // Register với JSON
    register: (userData) => 
        axios.post(`${API_GATEWAY}/register`, userData, {
            headers: {
                'Content-Type': 'application/json'
            }
        }),
    
    // Verify token
    verifyToken: (token) =>
        axios.get(`${API_GATEWAY}/verify-token`, {
            headers: { 
                Authorization: `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        })
};

export const API_BASE = API_GATEWAY;