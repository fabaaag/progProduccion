import axios from './axiosConfig';


export const loginUser = async (credentials) => {
    try {
        const response = await axios.post(`/users/api/v1/login/`, credentials);
        
        // Guardar tokens inmediatamente después de recibirlos
        if (response.data.token) {
            localStorage.setItem('token', response.data.token);
            localStorage.setItem('refreshToken', response.data.refresh);
            
            // Configurar el token en axios para futuras peticiones
            axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.token}`;
        }
        
        return response.data;
    } catch (error) {
        console.error('Error en login:', error);
        throw error;
    }
};

export const checkAuthStatus = () => {
    const token = localStorage.getItem('token');
    const user = JSON.parse(localStorage.getItem('user'));
    return { isAuthenticated: !!token, user};
};

export const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
};

export const updateProfile = async (userData) => {
    try {
        const response = await axios.put('/users/api/v1/profile/', userData);
        
        // Si la respuesta incluye un nuevo token (caso de cambio de contraseña)
        if (response.data.token) {
            localStorage.setItem('token', response.data.token);
            localStorage.setItem('refreshToken', response.data.refresh);
            axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.token}`;
        }
        
        return response.data;
    } catch (error) {
        if (error.response?.data) {
            // Manejar errores específicos del backend
            const errorMessage = Object.values(error.response.data)[0];
            throw new Error(Array.isArray(errorMessage) ? errorMessage[0] : errorMessage);
        }
        throw error;
    }
};

export const getProfile = async () => {
    try {
        const response = await axios.get('/users/api/v1/profile/');
        console.log('Respuesta del perfil:', response.data);
        return response.data;
    } catch (error) {
        console.error('Error en getProfile:', error.response?.data || error.message);
        throw error;
    }
};

// Nueva función para refrescar el token
export const refreshAccessToken = async () => {
    try {
        const refreshToken = localStorage.getItem('refreshToken');
        if (!refreshToken) {
            throw new Error('No refresh token available');
        }

        const response = await axios.post(`/users/api/v1/token/refresh/`, {
            refresh: refreshToken
        });

        const newToken = response.data.access;
        localStorage.setItem('token', newToken);
        axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;

        return newToken;
    } catch (error) {
        console.error('Error refreshing token:', error);
        localStorage.clear();
        window.location.href = '/login';
        throw error;
    }
};