// frontend_react/src/api/reports.api.js
import axios from "../../../api/axiosConfig";

// Obtener lista de reportes
export const getAllSupervisorReports = async (filters = {}) => {
    try {
        // Construir query params para filtros
        const params = new URLSearchParams();
        Object.entries(filters).forEach(([key, value]) => {
            if (value) params.append(key, value);
        });
        
        const queryString = params.toString() ? `?${params.toString()}` : '';
        const response = await axios.get(`/gestion/api/v1/reportes-supervisor/${queryString}`);
        return response.data;
    } catch (error) {
        console.error('Error obteniendo reportes:', error);
        throw error;
    }
};

// Obtener detalle de un reporte
export const getSupervisorReportDetail = async (reportId) => {
    try {
        const response = await axios.get(`/gestion/api/v1/reportes-supervisor/${reportId}/`);
        return response.data;
    } catch (error) {
        console.error('Error obteniendo detalle del reporte:', error);
        throw error;
    }
};

// Crear nuevo reporte
export const createSupervisorReport = async (programId) => {
    try {
        const response = await axios.post('/gestion/api/v1/reportes-supervisor/', {
            programa_id: programId
        });
        return response.data;
    } catch (error) {
        console.error('Error creando reporte:', error);
        throw error;
    }
};

// Actualizar reporte
export const updateSupervisorReport = async (reportId, data) => {
    try {
        const response = await axios.put(`/gestion/api/v1/reportes-supervisor/${reportId}/`, data);
        return response.data;
    } catch (error) {
        console.error('Error actualizando reporte:', error);
        throw error;
    }
};

// Liberar bloqueo
export const releaseReportLock = async (reportId) => {
    try {
        const response = await axios.delete(`/gestion/api/v1/reportes-supervisor/${reportId}/`);
        return response.data;
    } catch (error) {
        console.error('Error liberando bloqueo:', error);
        throw error;
    }
};

// Reutilizar funciones existentes para obtener datos diarios
export const getDailyReport = async (reportId, date) => {
    try {
        // Aquí usaríamos el endpoint existente
        const response = await axios.get(`/gestion/api/v1/programas/${reportId}/supervisor-report/`);
        
        // Filtrar por fecha si se proporciona
        if (date && response.data.tareas) {
            response.data.tareas = response.data.tareas.filter(tarea => tarea.fecha === date);
        }
        
        return response.data;
    } catch (error) {
        console.error('Error obteniendo reporte diario:', error);
        throw error;
    }
};