import axios from "./axiosConfig";



export const createProgram = (program) => axios.post(`/gestion/api/v1/programas/crear_programa/`, program);

export const getAllPrograms = () => axios.get(`/gestion/api/v1/programas/`);

export const deleteProgram = async (id) => {
  try {
      const response = await axios.delete(`/gestion/api/v1/programas/${id}/delete/`);
      return response.data
  } catch (error) {
      console.log("Error eliminando programas:", error)
      throw error
  }
};

export const updateProgram = async (programId, updates) => {
  try{
    const response = await axios.put(`/gestion/api/v1/programas/${programId}/update-prio/`,
      {
        order_ids: updates.map(orden => ({
          id: orden.orden_trabajo,
          priority: orden.priority,
          procesos: orden.procesos.map(proceso => ({
            id: proceso.id,
            maquina_id: proceso.maquina_id,
            estandar: proceso.estandar
          }))
        })),
        recalculate_dates: true
      },
      {
        headers: {
          'Content-Type': 'application/json'
        }
      }
    );
    return response.data;
  } catch (error) {
    console.error("Error actualizando programa:", error);
    throw error;
  }
};

export const getProgram = async (programId) => {
  try {
    if (!programId) {
      console.error('programId is undefined');
      throw new Error('programId is required');
    }

    let programResponse, asignacionesResponse;
    
    try {
      programResponse = await axios.get(`/gestion/api/v1/programas/${programId}/`);
    } catch (error) {
      console.error('Error obteniendo datos del programa:', error);
      throw error;
    }

    const program = programResponse.data;
    
    return program;
  } catch (error) {
    console.error('Error fetching program:', error);
    throw error;
  }
};
  
export const updatePriorities = async (programId, orderIds) => {
  try {
    const response = await axios.put(
      `/gestion/api/v1/programas/${programId}/update-prio/`,
      { 
        order_ids: orderIds,
        recalculate_dates: true
      },
      {
        headers: {
          'Content-Type':'application/json',
        }
      }
    );
    return response.data;
  } catch (error) {
    console.error("Error actualizando prioridades", error);
    throw error;
  }
};
  
export const deleteOrder = async (programId, orderId) => {
  try{
    console.log(orderId);
    const response = await axios.delete(`/machine/api/v1/programas/${programId}/delete-orders/`, {
      data: { order_ids:[orderId] },
      headers: {
        'Content-Type': 'application/json',
      },
      validateStatus: function (status) {
        return status >= 200 && status < 300;
      }
    });
    return response.data.result;
  }catch(error){
    if (error.response){
      throw error.response.data;
    }
    throw error;
  }
};

export const getMaquinas = async (programId, procesoCodigo = null) => {
  if(!programId){
    throw new Error("Se requiere un ID de programa");
  }

  console.log(`[Frontend] getMaquinas llamada con programId=${programId}, procesoCodigo=${procesoCodigo}`);
  
  const url = procesoCodigo
      ? `/gestion/api/v1/programas/${programId}/maquinas/?proceso_codigo=${procesoCodigo}`
      : `/gestion/api/v1/programas/${programId}/maquinas/`;
      console.log(`[API] Solicitando máquinas con URL: ${url}`);
      console.log(`[API] Parámetros: programId=${programId}, procesoCodigo=${procesoCodigo}`);

  try{
    const response = await axios.get(url);
    console.log(`[API] Respuesta recibida para máquinas:`, response);
    return response.data;
  }catch(error){
    console.error(`[API] Error fetching maquinas:`, error);
    console.error(`[API] URL que falló: ${url}`);
    
    if (error.response) {
      console.error(`[API] Datos de respuesta de error:`, error.response.data);
      console.error(`[API] Estado de respuesta de error:`, error.response.status);
    }
    
    throw error;
  }
};

export const generateProgramPDF = async (programId) => {
  try{
    const response = await axios.get(`/gestion/api/v1/programas/${programId}/generar_pdf/`, {
      responseType: 'blob',
      timeout: 30000 //Aumentar el timeout a 30 segundos
    });

    console.log("Respuesta recibida, creando blob...");

    //Verificar que la respuesta sea un PDF válido
    if(response.headers['content-type'] !== 'application/pdf'){
      console.error("La respuesta no es un PDF:", response.headers['content-type']);

      //Si no es un PDF, intentar leer el contenido como texto
      const text =  await response.data.text();
      try {
        const errorData = JSON.parse(text);
        throw new Error(errorData.detail || errorData.message || "La respuesta no es un PDF válido");
      } catch (e) {
        throw new Error("La respuesta no es un PDF válido");
      }
    }

    const blob = new Blob([response.data], { type: 'application/pdf' });
    const url = window.URL.createObjectURL(blob);

    console.log("Blob creado, descargando PDF...");

    const a = document.createElement('a');
    a.href = url;
    a.download = `programa_${programId}.pdf`;
    document.body.appendChild(a);
    a.click();


    setTimeout(() => {
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
    }, 100);

    console.log("PDF descargado exitosamente");
    return true;
  } catch(error){
    console.error('Error generando PDF:', error);
    throw error;
  }
};

export const getProcesoTimeline = async (programaId, procesoId) => {
  try{
    const response = await axios.get(`/gestion/api/v1/programas/${programaId}/procesos/${procesoId}/timeline/`);
    return response.data;
  } catch (error){
    console.error(`[API] Error obteniendo timeline para proceso:`, error);
    throw error;
  }
}

export const getSupervisorReport = async (programId) => {
  try {
      const response = await axios.get(`/gestion/api/v1/programas/${programId}/supervisor-report/`);
      return response.data;
  } catch (error) {
      console.error('Error en getSupervisorReport:', error);
      throw error;
  }
};

export const updateSupervisorReport = async (programId, taskData) => {
  try {
      const response = await axios.post(
          `/gestion/api/v1/programas/${programId}/supervisor-report/update-priority/`,
          taskData
      );
      return response.data;
  } catch (error) {
      console.error('Error en updateSupervisorReport:', error);
      throw error;
  }
};