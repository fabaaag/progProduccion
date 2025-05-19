// src/api/supervisorReport.api.js
import axiosInstance from './axiosConfig';

export const supervisorReportAPI = {
    // Obtener lista de reportes de supervisor
    getReportList: async () => {
        try {
            const response = await axiosInstance.get('/gestion/api/v1/reportes-supervisor/');
            return response.data;
        } catch (error) {
            throw error;
        }
    },

    // Obtener detalle del reporte para una fecha específica
    getReportDetail: async (programId, date) => {
        try {
            if (!programId) {
                throw new Error('programId is required');
            }

            // Asegurarnos que programId sea numérico
            const numericProgramId = parseInt(programId, 10);
            
            const response = await axiosInstance.get(`/gestion/api/v1/programas/${numericProgramId}/supervisor-report/`, {
                params: { fecha: date }
            });
            return response.data;
        } catch (error) {
            console.error('Error en getReportDetail:', error);
            throw error;
        }
    },

    // Obtener resumen diario
    getDailySummary: async (programId, date) => {
        try {
            if (!programId) {
                throw new Error('programId is required');
            }

            const numericProgramId = parseInt(programId, 10);
            
            const response = await axiosInstance.get(`/gestion/api/v1/programas/${numericProgramId}/resumen-diario/${date}/`);
            return response.data;
        } catch (error) {
            console.error('Error en getDailySummary:', error);
            throw error;
        }
    },

    // Actualizar tarea (kilos fabricados, estado, observaciones)
    updateTask: async (programId, taskData) => {
        try {
            const response = await axiosInstance.put(`/gestion/api/v1/programas/${programId}/supervisor-report/`, taskData);
            return response.data;
        } catch (error) {
            throw error;
        }
    },

    // Finalizar día - Obtener preview
    getDayFinalizationPreview: async (programId, date) => {
        try {
            const response = await axiosInstance.get(`/gestion/api/v1/programas/${programId}/finalizar-dia/${date}/`);
            return response.data;
        } catch (error) {
            throw error;
        }
    },

    // Finalizar día - Confirmar
    finishDay: async (programId, date) => {
        try {
            const response = await axiosInstance.post(`/gestion/api/v1/programas/${programId}/finalizar-dia/${date}/`);
            return response.data;
        } catch (error) {
            throw error;
        }
    },

    // Timeline de ejecución
    getExecutionTimeline: async (programId, params = {}) => {
        try {
            const queryParams = new URLSearchParams(params).toString();
            const url = `/gestion/api/v1/programas/${programId}/timeline-ejecucion/${queryParams ? `?${queryParams}` : ''}`;
            const response = await axiosInstance.get(url);
            return response.data;
        } catch (error) {
            throw error;
        }
    },

    // Agregar este método dentro del objeto supervisorReportAPI
    getTaskProductionDetails: async (taskId) => {
        try {
            if (!taskId) {
                throw new Error('taskId is required');
            }
            const response = await axiosInstance.get(`/gestion/api/supervisor/task/${taskId}/details/`);
            return response.data;
        } catch (error) {
            console.error('Error en getTaskProductionDetails:', error);
            throw error;
        }
    },
};