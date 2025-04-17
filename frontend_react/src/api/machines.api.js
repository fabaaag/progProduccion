import axios from './axiosConfig';

export const getAllMachines = async () => {
    try{
        const response = await axios.get(`/gestion/api/v1/maquinas/`);
        return response.data;
    } catch (error){
        console.error('Error al obtener máquinas:', error);
        throw error;
    }
};

export const getAllMachinesFromApp = async () => {
    try{
        const response = await axios.get(`/machine/api/v1/machines/`);
        return response.data;
    } catch (error) {
        console.error('Error al obtener las máquinas:', error);
        throw error;
    }
};

export const getMachineTypes = async () => {
    try{
        const response = await axios.get('/machine/api/v1/machine-types/');
        return response.data;
    } catch (error){
        console.error('Error al obtener tipos de máquina:', error);
        throw error;
    }
};

export const getMachineDetails = async (machineId) => {
    try{
        const response = await axios.get(`/machine/api/v1/machines/${machineId}/`);
        return response.data;
    } catch (error){
        console.error('Error al obtener detalles de la máquina:', error);
        throw error;
    }
};

export const updateMachineType = async (machineId, typeIds) => {
    try {
        const response = await axios.put(`/machine/api/v1/machines/${machineId}/`, {
            tipos_maquina_ids: typeIds // Cambiado para enviar array de IDs
        });
        return response.data;
    } catch (error) {
        console.error('Error al actualizar tipos de máquina:', error);
        throw error;
    }
};

export const getOperatorMachines = async (operatorId) => {
    try {
        const response = await axios.get(`/machine/api/v1/operator-machines/${operatorId}/`);
        return response.data;
    } catch (error) {
        console.error('Error al obtener máquinas del operador:', error);
        throw error;
    }
};

export const getOperatorFormMachines = async () => {
    try {
        const response = await axios.get('/machine/api/v1/operator-form-machines/');
        return response.data;
    } catch (error) {
        console.error('Error al obtener máquinas para el formulario:', error);
        throw error;
    }
};
