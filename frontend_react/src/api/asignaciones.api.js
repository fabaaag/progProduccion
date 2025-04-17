import axios from './axiosConfig';



export const crearAsignacion = async (asignacionData) => {
    try {
        // Verificar que programa sea válido
        if (!asignacionData.programa_id || asignacionData.programa_id === 'undefined') {
            throw new Error("ID de programa inválido");
        }
        
        console.log("Datos de asignación a enviar:", asignacionData);
        
        const response = await axios.post(
            `/operator/api/v1/asignaciones/`, 
            asignacionData
        );
        console.log("Respuesta del servidor:", response.data);
        return response.data;
    } catch (error) {
        console.error("Error al crear asignación:", error);
        console.error('Error detallado:', error.response?.data);
        throw error;
    }
};

export const obtenerAsignacionesPrograma = async (programaId) => {
    try {
        const response = await axios.get(`/operator/api/v1/asignaciones/programa/${programaId}/`);
    } catch (error) {
        console.error('Error al obtener asignaciones:', error);
        throw error;
    }
}