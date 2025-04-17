import axiosInstance from './axiosConfig';

// API para Productos
export const getProductos = async (params = {}) => {
    try {
        const response = await axiosInstance.get('/productos/productos/', { params });
        return response.data;
    } catch (error) {
        console.error('Error al obtener productos:', error);
        throw error;
    }
};

export const getProducto = async (id) => {
    try {
        const response = await axiosInstance.get(`/productos/productos/${id}/`);
        return response.data;
    } catch (error) {
        console.error(`Error al obtener producto con ID ${id}:`, error);
        throw error;
    }
};

// API para Piezas
export const getPiezas = async (params = {}) => {
    try {
        const response = await axiosInstance.get('/productos/piezas/', { params });
        return response.data;
    } catch (error) {
        console.error('Error al obtener piezas:', error);
        throw error;
    }
};

export const getPieza = async (id) => {
    try {
        const response = await axiosInstance.get(`/productos/piezas/${id}/`);
        return response.data;
    } catch (error) {
        console.error(`Error al obtener pieza con ID ${id}:`, error);
        throw error;
    }
};

// API para Familias y Subfamilias
export const getFamilias = async (params = {}) => {
    try {
        const response = await axiosInstance.get('/productos/familias/', { params });
        return response.data;
    } catch (error) {
        console.error('Error al obtener familias:', error);
        throw error;
    }
};

export const getSubfamilias = async (params = {}) => {
    try {
        const response = await axiosInstance.get('/productos/subfamilias/', { params });
        return response.data;
    } catch (error) {
        console.error('Error al obtener subfamilias:', error);
        throw error;
    }
};