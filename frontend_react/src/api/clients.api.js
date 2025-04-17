import axios from './axiosConfig'

const clientsApi = axios.create({
    baseURL:'http://localhost:8000'
});

export const getAllClients = async () => await axios.get('/clientes/api/v1/clientes/');
export const createClient = async (client) => await axios.post('/clientes/api/v1/clientes/', client);
export const deleteClient = async (id) => await axios.delete(`/clientes/api/v1/clientes/${id}/`);
export const updateClient = async (id, client) => await axios.put(`/clientes/api/v1/clientes/${id}/`, client);
export const getClient = async (id) => await axios.get(`/clientes/api/v1/clientes/${id}/`);
