import axios from './axiosConfig';

export const getAllEmpresas = async () => {
    try{
        const response = await axios.get(`/gestion/api/v1/empresas/`);
        return response.data;
    } catch (error){
        console.error("Error al obtener empresas:", error);
        throw error;
    }
}