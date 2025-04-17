import axios from './axiosConfig';

export const getAllUsers = async () => {
    try {
        const response = await axios.get(`/users/api/v1/users/`);
        console.log('Headers de la petición:', response.config.headers);
        return response.data;
    } catch (error) {
        if(error.response?.status === 401){
            console.log('Token actual:', localStorage.getItem('token'));
            console.log('Headers enviados:', error.config.headers);
        }
        throw error;
    }
};

export const createUser = async (userData) => {
    try {
        console.log('Datos a enviar:', userData)
        const response = await axios.post(`/users/api/v1/users/create/`, userData);
        return response.data;
    } catch (error) {
        console.error('Error completo:', error.response?.data);
        throw error;
    }
};

export const updateUser = async(userId, userData) => {
    try {
        //Eliminamos campos que no queremos enviar en la actualización
        const { password, created_at, updated_at, ...dataToSend } = userData;

        console.log('Datos a enviar:', dataToSend);

        const response = await axios.put(`/users/api/v1/users/${userId}/`, dataToSend);
        return response.data;
    } catch (error) {
        console.error('Error completo: ', error.response?.data);
        throw error;
    }
};

export const toggleUserStatus = async(userId) => {
    try {
        const response = await axios.post(`/users/api/v1/users/${userId}/toggle-status/`);
        return response.data;
    } catch (error) {
        throw error;
    }
};

export const getUserById = async (id) => {
    try{
        const response = await axios.get(`/users/api/v1/users/${id}/`);
        return response.data;
    } catch (error) {
        throw error;
    }
}