import axios from './axiosConfig';

const API_URL = 'http://localhost:8000/operator/api/v1';

export const getAllOperators = async () => {
    try {
        const response = await axios.get(`/operator/api/v1/operadores/`);
        return response.data;
    } catch(error){
        console.error('Error al obtener operadores:', error);
        throw error;
    }
};

export const getRoles = async () => {
    try{
        const response = await axios.get(`/operator/api/v1/roles/`);
        return response.data;
    } catch (error){
        console.error('Error al obtener roles:', error);
        throw error;
    }
}

export const getOperatorTasks = async (operator) => {
    if(!operator || !operator.id){
        throw new Error("Se requiere un operador válido con ID");
    }
    try {
        const response = await axios.get(`/operator/api/v1/operadores/${operator.id}/tareas/`);
        console.log('Respuesta de tareas:', response.data);
        return response.data.tareas || [];
    } catch (error) {
        console.error('Error al cargar asignaciones:', error);
        throw error;
    }
};

//Crear un nuevo operador 
export const createOperator = async (operatorData) => {
    try{
        // Extraer las máquinas habilitadas del objeto datos
        const { maquinas_habilitadas, ...operatorInfo } = operatorData;
        console.log('Datos básicos del operador enviados al backend:', operatorInfo);
        const response = await axios.post(`/operator/api/v1/operadores/`, operatorInfo);
        const newOperator = response.data;

        // Si hay máquinas habilitadas, actualizarlas en un segundo paso
        if (maquinas_habilitadas && maquinas_habilitadas.length > 0){
            try {
                console.log('Actualizando máquinas habilitadas:', maquinas_habilitadas);
                await updateOperatorMachines(newOperator.id, maquinas_habilitadas);
            } catch (machineError) {
                console.error('Error al asignar máquinas al operador:', machineError);
                //Notificar pero no interrumpir el flijo, ya que el operador se creó correctamente
                throw new Error(`Operador creado pero hubo un error al asignar máquinas: ${machineError.message}`)
            }
        }
        return newOperator;
    } catch (error) {
        console.error('Error al crear operador:', error);
        throw error;
    }
};

//Actualizar un operador existente
export const updateOperator = async (operatorId, operatorData) => {
    try{
        // Extraer las máquinas habilitadas del objeto de datos
        const { maquinas_habilitadas, ...operatorInfo } = operatorData;

        console.log('Datos básicos del operador a actualizar:', operatorInfo);
        //Primero actualizar la información básica del operador
        const response = await axios.put(`/operator/api/v1/operadores/${operatorId}/`, operatorInfo);
        console.log ('maqs', maquinas_habilitadas);
        // Luego actualizar las máquinas habilitadas
        if(maquinas_habilitadas !== undefined) {
            try {
                console.log('Actualizando máquinas habilitadas:', maquinas_habilitadas);
                const response_maqs = await updateOperatorMachines(operatorId, maquinas_habilitadas);
                console.log('Respuesta de máquinas habilitadas:', response_maqs);
            } catch (machineError) {
                console.error('Error al actualizar máquinas del operador:', maquinas_habilitadas)
                //Notificar pero no interrumpir el flujo, ya que el operador se actualizó correctamente
                throw new Error(`Operador actualizado pero hubo un error al actualizar máquinas: ${machineError.message}`);
            }
        }

        return response.data;
    } catch (error){
        console.error("Error al actualizar operador:", error);
        throw error;
    }
};

// Nueva función para actualizar las máquinas habilitadas
export const updateOperatorMachines = async (operatorId, machineIds) => {
    try {
        console.log('maquinas:', machineIds);
        const response = await axios.post(`/operator/api/v1/operadores/${operatorId}/maquinas/`, {
            maquinas: machineIds
        });
        return response.data;
    } catch (error){
        console.error('Error al actualizar máquinas del operador:', error);
        throw error;
    }
};

//Eliminar operador (soft delete)
export const deleteOperator = async (operatorId) => {
    try{
        await axios.delete(`/operator/api/v1/operadores/${operatorId}/`);
    } catch (error){
        console.error('Error al eliminar operador:', error);
        throw error;
    }
}

export const getAsignacionesPrograma = async (programId) => {
    try{
        const response = await axios.get(`/operator/api/v1/operadores/${programId}/asignaciones/`);
        return response.data;
    } catch (error) {
        console.error('Error al obtener asignaciones del programa:', error);
        throw error;
    }
}

// Asignar operador a un programa
export const assignOperatorToProgram = async(programId, assignmentData) => {
    try{
        const response = await axios.post(`/operator/api/v1/operadores/${programId}/asignaciones/`, assignmentData);
        return response.data;
    } catch (error){
        console.error('Error al asignar operador al programa:', error);
        throw error;
    }
};

//Eliminar asignación de operador
export const removeOperatorAssignment = async(programId, assignmentId) => {
    try{
        await axios.delete(`/operator/api/v1/operadores/${programId}/asignaciones/${assignmentId}`);
    } catch (error) {
        console.error('Eror al eliminar asignación:', error);
        throw error;
    }
};

export const getOperatorById = async (id) => {
    try{
        const response = await axios.get(`/operator/api/v1/disponibilidad/`, {
            params: {
                operador_id: operatorId,
                fecha_inicio: startDate,
                fecha_fin: endDate

            }
        });
        return response.data;
    } catch (error){
        console.error('Error al obtener disponibilidad:', error);
        throw error;
    }
};

export const getOperadoresPorMaquina = async (maquinaId) => {
    if (!maquinaId){
        throw new Error("Se requiere un ID de máquina");
    }
    try{
        const response = await axios.get(`/operator/api/v1/operadores/por-maquina/${maquinaId}/`);
        return response.data;
    } catch (error){
        console.error("Error obteniendo operadores por máquina:", error);
        throw error;
    }
};