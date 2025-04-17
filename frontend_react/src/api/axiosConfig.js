import axios from 'axios';
import config from './api';


const axiosInstance = axios.create({
    baseURL: config.apiUrl,
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
});

//Variable para controlar si estamos en proceso de refresh
let isRefreshing = false;
//Cola de solicitudes fallidas
let failedQueue = [];

const processQueue = (error, token = null) => {
    failedQueue.forEach(prom => {
        if(error){
            prom.reject(error);
        }else{
            prom.resolve(token);
        }
    });
    failedQueue = [];
};

// Interceptor para agregar el token a todas las peticiones
axiosInstance.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            // Asegurarse de que el token se envía con el formato correcto
            config.headers = {
                ...config.headers,
                'Authorization': `Bearer ${token}`.trim()
            };
            // Debug para ver los headers
            console.log('Request headers:', config.headers);
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

axiosInstance.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;
        if (error.response?.status === 401 && !originalRequest._retry && !originalRequest.url.includes('token/refresh')) {
            originalRequest._retry = true;

            //Si ya estamos refrescando, añadir a la cola
            if (isRefreshing){
                return new Promise((resolve, reject) => {
                    failedQueue.push({ resolve, reject });
                })
                .then(token => {
                    originalRequest.headers['Authorization'] = `Bearer ${token}`;
                    return axiosInstance(originalRequest);
                })
                .catch(err => {
                    return Promise.reject(err);
                });
            }

            isRefreshing = true;
            const refreshToken = localStorage.getItem('refreshToken');
            console.log('401 error detected, attempting token refresh');


            if (!refreshToken) {
                isRefreshing = false;
                // Solo limpiar tokens, no todo localStorage
                localStorage.removeItem('token');
                localStorage.removeItem('refreshToken');
                window.location.href = '/login';
                return Promise.reject(error)
            }
            try {
                const response = await axios.create({
                    baseURL: config.apiUrl,
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    }
                }).post('/users/api/v1/token/refresh/', {
                    refresh: refreshToken
                });
                
                const newToken = response.data.access;
                localStorage.setItem('token', newToken);

                //Procesar la cola con el nuevo token
                processQueue(null, newToken);
                
                // Actualizar el token en la petición original
                originalRequest.headers['Authorization'] = `Bearer ${newToken}`;

                isRefreshing = false;
                
                // Reintentar la petición original
                return axiosInstance(originalRequest);
            } catch (refreshError) {
                console.log('Token refresh failed:', refreshError);

                //Procesar la cola con error
                processQueue(refreshError, null)

                //Solo limpiar tokens, no todo localStorage
                localStorage.removeItem('token');
                localStorage.removeItem('refreshToken');

                isRefreshing = false

               //Redireccionar solo si no estamos ya en la página de login
               if(!window.location.pathname.includes('/login')){
                window.location.href = '/login';
               }
                return Promise.reject(refreshError);
            }
            
        }
        return Promise.reject(error);
    }
);

export default axiosInstance;
