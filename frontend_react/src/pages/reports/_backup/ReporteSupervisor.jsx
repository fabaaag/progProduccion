import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Container, Table, Form, Button, ButtonGroup, Modal } from 'react-bootstrap';
import { ReactSortable } from "react-sortablejs";
import CompNavbar from "../../../components/Navbar/CompNavbar";
import { Footer } from "../../../components/Footer/Footer";
import { LoadingSpinner } from "../../../components/UI/LoadingSpinner/LoadingSpinner";
import { toast } from "react-hot-toast";
import moment from 'moment';
import { getSupervisorReport, updateSupervisorReport, getProcesoTimeline, getProgramTimelineEjecucion } from '../../../api/programs.api';
import { getSupervisorReportDetail } from '../../../api/reports.api';
import { crearAsignacion } from '../../../api/asignaciones.api';
import { FaArrowLeft, FaSave, FaUser, FaUserPlus, FaExpand, FaCalendarCheck, FaCodeBranch } from 'react-icons/fa';
import './ReporteSupervisor.css';
import DatePicker from 'react-datepicker';
import "react-datepicker/dist/react-datepicker.css";
import { OperadorSelectionModal } from '../../../components/Programa/OperadorSelectionModal';
import TableFullViewModal from './TableFullViewModal';
import FinalizarDiaModal from './FinalizarDiaModal';
import TareaGenealogiaView from './TareaGenealogiaView';
import Timeline from "react-calendar-timeline";
import "react-calendar-timeline/dist/Timeline.scss";

export function ReporteSupervisor() {
    // Obtener parámetros - ahora detectamos ambos posibles
    const params = useParams();
    const programId = params.programId;
    const reportId = params.reportId;
    
    // Estado para manejar el ID del programa (ya sea directo o derivado del reporte)
    const [effectiveProgramId, setEffectiveProgramId] = useState(programId);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [displayedTasks, setDisplayedTasks] = useState([]);
    const [currentDate, setCurrentDate] = useState(null);
    const [availableDates, setAvailableDates] = useState([]);
    const [selectedDateIndex, setSelectedDateIndex] = useState(0);
    const [kilosFabricados, setKilosFabricados] = useState({});
    const [porcentajeCumplimiento, setPorcentajeCumplimiento] = useState({});
    const [programDateRange, setProgramDateRange] = useState({ start: null, end: null });
    const [tareasPorFecha, setTareasPorFecha] = useState({});
    const [taskStates, setTaskStates] = useState({});
    const [editableStates, setEditableStates] = useState({});
    const [pendingChanges, setPendingChanges] = useState({});
    const [programData, setProgramData] = useState(null);
    const [supervisionData, setSupervisionData] = useState(null);
    const [tasksForDate, setTasksForDate] = useState([]);

    //Estados para la asignación de operadores
    const [showOperadorModal, setShowOperadorModal] = useState(false);
    const [currentProceso, setCurrentProceso] = useState(null);
    const [operadores, setOperadores] = useState([]);
    const [showTableModal, setShowTableModal] = useState(false);

    // 2. Añadir estados para controlar los modales
    const [showFinalizarDiaModal, setShowFinalizarDiaModal] = useState(false);
    const [showGenealogiaModal, setShowGenealogiaModal] = useState(false);
    const [tareaSeleccionada, setTareaSeleccionada] = useState(null);

    // Añadir estados para la timeline
    const [showTimeline, setShowTimeline] = useState(false);
    const [timelineData, setTimelineData] = useState({ groups: [], items: [] });
    const [timelineLoading, setTimelineLoading] = useState(false);

    // Efecto para resolver el programId si viene de un reportId
    useEffect(() => {
        const resolveIds = async () => {
            // Si ya tenemos programId directo, usamos ese
            if (programId) {
                return;
            }
            
            // Si tenemos reportId, necesitamos obtener el programId asociado
            if (reportId) {
                try {
                    // Usar la función de la API que ya tenemos
                    const reporteData = await getSupervisorReportDetail(reportId);
                    console.log("Datos del reporte:", reporteData);
                    
                    // Obtener el ID del programa desde la respuesta
                    const programIdFromReport = reporteData.programa_data.id;
                    console.log("ProgramId obtenido del reporte:", programIdFromReport);
                    
                    if (programIdFromReport) {
                        setEffectiveProgramId(programIdFromReport);
                    } else {
                        toast.error("No se pudo identificar el programa asociado al reporte");
                    }
                } catch (error) {
                    console.error("Error al obtener el programa desde el reporte:", error);
                    toast.error("Error al cargar datos del reporte");
                }
            }
        };
        
        resolveIds();
    }, [programId, reportId]);

    const fetchTasksForDate = async () => {
        try {
            setLoading(true);
            setError(null);
            
            const response = await getSupervisorReport(effectiveProgramId);
            console.log("Respuesta del backend:", response);
            
            if (!response || !response.programa) {
                throw new Error("No se recibieron datos válidos del servidor");
            }
    
            setProgramData(response.programa);
    
            const tasksForCurrentDate = response.tareas || [];
            console.log("Tareas para la fecha actual:", tasksForCurrentDate);
    
            // Mapear las tareas con la información de fragmentación
            const processedTasks = tasksForCurrentDate.map(task => ({
                id: task.id,
                orden: task.orden,
                item_ruta_id: task.item_ruta_id,
                ot_codigo: task.ot_codigo,
                orden_trabajo: task.orden_trabajo,
                proceso: {
                    id: task.proceso.id,
                    codigo: task.proceso.codigo,
                    descripcion: task.proceso.descripcion
                },
                maquina: {
                    id: task.maquina.id,
                    codigo: task.maquina.codigo,
                    descripcion: task.maquina.descripcion
                },
                cantidad_programada: task.cantidad_programada,
                kilos_programados: task.kilos_programados,
                kilos_fabricados: task.kilos_fabricados || 0,
                unidades_fabricadas: task.unidades_fabricadas || 0,
                estado: task.estado || 'Pendiente',
                observaciones: task.observaciones || '',
                porcentaje_cumplimiento: task.porcentaje_cumplimiento || 0,
                
                // Campos nuevos para fragmentación
                es_continuacion: task.es_continuacion || false,
                tarea_padre_fecha: task.tarea_padre_fecha,
                tarea_padre_porcentaje: task.tarea_padre_porcentaje || 0,
                tarea_padre_kilos: task.tarea_padre_kilos || 0,
                
                // Campos para operador
                operador_id: task.operador_id,
                operador_nombre: task.operador_nombre || 'Sin asignar'
            }));
    
            setDisplayedTasks(processedTasks);
    
            // Inicializar estados para las tareas
            const initialKilosFabricados = {};
            const initialTaskStates = {};
            const initialEditableStates = {};
            const initialPorcentajeCumplimiento = {};
    
            processedTasks.forEach(task => {
                initialKilosFabricados[task.id] = task.kilos_fabricados;
                initialTaskStates[task.id] = task.estado;
                initialEditableStates[task.id] = task.estado !== 'Terminado';
                initialPorcentajeCumplimiento[task.id] = task.porcentaje_cumplimiento;
            });
    
            setKilosFabricados(initialKilosFabricados);
            setTaskStates(initialTaskStates);
            setEditableStates(initialEditableStates);
            setPorcentajeCumplimiento(initialPorcentajeCumplimiento);
    
        } catch (error) {
            console.error("Error al cargar las tareas:", error);
            setError(error.message || "Error al cargar las tareas");
            toast.error(`Error: ${error.message || "No se pudieron cargar las tareas"}`);
        } finally {
            setLoading(false);
        }
    };

    // Simplificar isWorkingDay
    const isWorkingDay = (date) => {
        const day = moment(date).day();
        return day !== 0 && day !== 6; // 0 es domingo, 6 es sábado
    };

    // Efecto para inicialización
    useEffect(() => {
        console.log("ProgramId efectivo:", effectiveProgramId);
        
        const initializeData = async () => {
            if (!effectiveProgramId) {
                console.error("No se pudo identificar el programa");
                toast.error("Error: No se pudo identificar el programa");
                return;
            }
            try {
                setLoading(true);
                const response = await getSupervisorReport(effectiveProgramId);
                console.log("Datos del programa recibidos: ", response.programa);
                
                if (!response.programa.fecha_inicio || !response.programa.fecha_fin) {
                    throw new Error("El programa no tiene fechas definidas");
                }

                setProgramData(response.programa);
                setCurrentDate(new Date(response.programa.fecha));
                
                let startDate = moment(response.programa.fecha_inicio).isValid() 
                    ? moment(response.programa.fecha_inicio) 
                    : moment(response.programa.fecha_inicio, ['YYYY-MM-DD', 'DD/MM/YYYY', 'YYYY/MM/DD']);
                    
                let endDate = moment(response.programa.fecha_fin).isValid() 
                    ? moment(response.programa.fecha_fin) 
                    : moment(response.programa.fecha_fin, ['YYYY-MM-DD', 'DD/MM/YYYY', 'YYYY/MM/DD']);

                if (!startDate.isValid() || !endDate.isValid()) {
                    throw new Error('Fechas del programa inválidas');
                }

                console.log('Fechas parseadas:', {
                    inicio: startDate.format('YYYY-MM-DD'),
                    fin: endDate.format('YYYY-MM-DD')
                });
                
                setProgramDateRange({ 
                    start: startDate.toDate(), 
                    end: endDate.toDate() 
                });
                
                const dates = [];
                let currentDateTemp = startDate.clone();
                
                while (currentDateTemp.isSameOrBefore(endDate)) {
                    if (isWorkingDay(currentDateTemp)) {
                        dates.push(currentDateTemp.format('YYYY-MM-DD'));
                    }
                    currentDateTemp.add(1, 'days');
                }
                
                console.log('Fechas disponibles generadas:', dates);
                
                if (dates.length === 0) {
                    throw new Error('No hay fechas laborables disponibles en el rango del programa');
                }

                setAvailableDates(dates);
                
                // Iniciar con la primera fecha del programa
                const firstDate = dates[0];
                console.log('Estableciendo fecha inicial:', firstDate);
                setSelectedDateIndex(0);
                
            } catch (error) {
                console.error("Error al inicializar datos:", error);
                setError(error.message);
                toast.error(`Error al cargar los datos iniciales: ${error.message}`);
            } finally {
                setLoading(false);
            }
        };

        // Solo ejecutar si tenemos un ID válido
        if (effectiveProgramId) {
            initializeData();
        }
    }, [effectiveProgramId]);

    // Efecto separado para cargar tareas cuando cambia la fecha
    useEffect(() => {
        if (currentDate && !loading) {
            fetchTasksForDate();
        }
    }, [currentDate]);

    // Modificar handleDateNavigation para asegurar que se actualicen las tareas
    const handleDateNavigation = (direction) => {
        const newIndex = direction === 'next' 
            ? selectedDateIndex + 1 
            : selectedDateIndex - 1;

        if (newIndex >= 0 && newIndex < availableDates.length) {
            const newDate = availableDates[newIndex];
            console.log(`Navegando a nueva fecha: ${newDate} (índice: ${newIndex})`);
            setSelectedDateIndex(newIndex);
            setCurrentDate(newDate);
            // No es necesario llamar a fetchTasksForDate aquí porque el useEffect lo hará
        }
    };

    const handlePriorityUpdate = (newList) => {
        console.log("Lista anterior:", displayedTasks);
        console.log("Nueva lista:", newList);
        
        // Crear un nuevo array con las prioridades actualizadas
        const updatedTasks = newList.map((task, newIndex) => {
            // Encontrar el índice anterior de esta tarea
            const oldIndex = displayedTasks.findIndex(t => t.id === task.id);
            console.log(`Tarea ${task.id} movida de posición ${oldIndex} a ${newIndex}`);
            
            return {
                ...task,
                priority: newIndex + 1 // La nueva prioridad basada en la posición
            };
        });

        // Actualizar los cambios pendientes con las nuevas prioridades
        const changes = {};
        updatedTasks.forEach((task, index) => {
            changes[task.id] = {
                id: task.id,
                priority: index + 1,
                proceso_id: task.proceso_id,
                kilos_fabricados: kilosFabricados[task.id] || task.kilos_fabricados || 0,
                cantidad_programada: task.cantidad_programada,
                fecha: task.fecha,
                estado: taskStates[task.id] || task.estado || 'Pendiente',
                observaciones: task.observaciones || ''
            };
        });

        // Actualizar el estado
        setDisplayedTasks(updatedTasks);
        setPendingChanges(prev => ({...prev, ...changes}));
    };

    const handleKilosChange = (taskId, kilos, task) => {
        // Preservar el valor de entrada tal cual (vacío o texto) en la interfaz
        // pero usar un valor numérico para cálculos
        setKilosFabricados(prev => ({...prev, [taskId]: kilos}));
        
        // Para cálculos, convertir a número, pero permitiendo 0 explícitamente
        const kilosNum = kilos === "" ? 0 : 
                       (isNaN(parseFloat(kilos)) ? 0 : parseFloat(kilos));
        
        // Calcular porcentaje localmente
        const porcentaje = (kilosNum / task.kilos_programados) * 100;
        setPorcentajeCumplimiento(prev => ({...prev, [taskId]: porcentaje}));
        
        // Guardar cambio pendiente con el valor numérico
        setPendingChanges(prev => ({
            ...prev,
            [taskId]: {
                ...prev[taskId],
                kilos_fabricados: kilosNum,
                proceso_id: task.proceso_id,
                cantidad_programada: task.cantidad_programada,
                fecha: task.fecha,
                estado: taskStates[taskId] || task.estado || 'Pendiente',
                observaciones: task.observaciones || ''
            }
        }));
    };

    const handleStateChange = (taskId, newState, task) => {
        setTaskStates(prev => ({...prev, [taskId]: newState}));
        
        // Si cambiamos a "Terminado", verificar los kilos fabricados
        if (newState === 'Terminado') {
            const kilosFab = kilosFabricados[taskId] || 0;
            if (kilosFab < task.kilos_programados) {
                if (!window.confirm('Los kilos fabricados son menores a los programados. ¿Desea marcar como terminado de todas formas?')) {
                    return;
                }
            }
            setEditableStates(prev => ({...prev, [taskId]: false}));
        } else {
            setEditableStates(prev => ({...prev, [taskId]: true}));
        }

        // Guardar cambio pendiente
        setPendingChanges(prev => ({
            ...prev,
            [taskId]: {
                ...prev[taskId],
                estado: newState,
                proceso_id: task.proceso_id,
                kilos_fabricados: kilosFabricados[taskId] || 0,
                cantidad_programada: task.cantidad_programada,
                fecha: task.fecha,
                observaciones: task.observaciones || ''
            }
        }));
    };

    const handleObservacionesChange = (taskId, observaciones, task) => {
        const newTasks = [...displayedTasks];
        const index = newTasks.findIndex(t => t.id === taskId);
        newTasks[index].observaciones = observaciones;
        setDisplayedTasks(newTasks);

        // Guardar cambio pendiente
        setPendingChanges(prev => ({
            ...prev,
            [taskId]: {
                ...prev[taskId],
                observaciones,
                proceso_id: task.proceso_id,
                kilos_fabricados: kilosFabricados[taskId] || 0,
                cantidad_programada: task.cantidad_programada,
                fecha: task.fecha,
                estado: taskStates[taskId] || task.estado || 'Pendiente'
            }
        }));
    };

    const handleSaveReport = async () => {
        try {
            setLoading(true);
            
            // Añadir console.log para depurar la entrada
            console.log('Estado de kilosFabricados:', kilosFabricados);
            console.log('Tareas originales:', displayedTasks);
            
            // Crear un único objeto con todas las tareas en lugar de múltiples peticiones
            const tasksData = displayedTasks.map((task, index) => {
                // Asegurarnos de que valores cero se manejen correctamente
                const kilosValue = kilosFabricados[task.id];
                let kilosFab;
                
                // Validar que sea un número o convertirlo a 0
                if (kilosValue !== undefined && kilosValue !== null && kilosValue !== "") {
                    kilosFab = parseFloat(kilosValue);
                    if (isNaN(kilosFab)) kilosFab = 0;
                } else if (task.kilos_fabricados !== undefined && task.kilos_fabricados !== null) {
                    kilosFab = parseFloat(task.kilos_fabricados);
                    if (isNaN(kilosFab)) kilosFab = 0;
                } else {
                    kilosFab = 0;
                }
                
                return {
                    id: task.id,
                    priority: index + 1,
                    proceso_id: task.proceso_id,
                    kilos_fabricados: kilosFab,
                    cantidad_programada: parseFloat(task.cantidad_programada || 0),
                    fecha: task.fecha,
                    estado: taskStates[task.id] || task.estado || 'Pendiente',
                    observaciones: task.observaciones || ''
                };
            });
    
            // Añadir console.log para depurar
            console.log('Enviando tareas al backend:', tasksData);
            
            // Enviar una única petición con todas las tareas
            await updateSupervisorReport(effectiveProgramId, {
                tasks: tasksData
            });
            
            // Limpiar cambios pendientes
            setPendingChanges({});
            
            // Recargar datos
            await fetchTasksForDate();
            
            toast.success('Reporte guardado correctamente');
        } catch (error) {
            console.error('Error al guardar el reporte:', error);
            // Mostrar más información del error si está disponible
            if (error.response) {
                console.error('Respuesta del servidor:', error.response.data);
                toast.error(`Error al guardar el reporte: ${error.response.data.error || error.message || 'Error desconocido'}`);
            } else {
                toast.error(`Error al guardar el reporte: ${error.message || 'Error desconocido'}`);
            }
        } finally {
            setLoading(false);
        }
    };

    //Funcion para abrir el modal de selección de operador
    const openOperadorModal = (task) => {
        setCurrentProceso(task);
        setShowOperadorModal(true);
    };

    //Función para manejar el cambio de operador
    const handleOperadorChange =  async (proceso, operadorId) => {
        if(!effectiveProgramId){
            console.error("No hay programId disponible");
            return;
        }

        console.log(`Asignando operador ${operadorId} al proceso ${proceso.id}`);

        //si operadorId es null, estamos desasignando
        const isRemoving = operadorId === null;

        try {
            //Actualizar el estado local primero para UI responsivo
            const updatedTasks = displayedTasks.map(task => {
                if (task.id === proceso.id){
                    return {
                        ...task,
                        operador_id: operadorId,
                        operador_nombre: isRemoving ? null : operadores.find(op => op.id.toString() === operadorId.toString())?.nombre || 'Operador asignado'
                    };
                }
                return task;
            });

            setDisplayedTasks(updatedTasks);

            let fechaInicio, fechaFin;

            try{
                //Obtener las fechas del timeline desde el backend
                const timelineData = await getProcesoTimeline(effectiveProgramId, proceso.id);
                console.log('Datos del timeline recibidos:', timelineData);

                fechaInicio = timelineData.fecha_inicio;
                fechaFin = timelineData.fecha_fin;
            } catch (error){
                console.warn('Error al obtener fechas del timeline:', error);

                //Si hay error usar la fecha actual y una duración predeterminada
                fechaInicio = new Date();
                fechaFin = new Date(fechaInicio);
                fechaFin.setHours(fechaFin.getHours() + 8);
            }

            //Convertir fechas a formato ISO pero con la zona horaria de Chile
            const formatearFechaChile = (fecha) => {
                if (!(fecha instanceof Date)){
                    fecha = new Date(fecha);
                }

                //Obtener el offset de Chile(UTC-3 o UTC-4 dependiendo del horario de verano)
                const offsetChile = -3;

                //Crear una nueva fecha con el offset de Chile
                const fechaChile = new Date(fecha.getTime());
                const offsetActual = fecha.getTimezoneOffset() / 60;
                const diferenciaOffset = offsetActual - offsetChile;

                //Ajustar la fecha según la diferencia de offset
                fechaChile.setHours(fecha.getHours() + diferenciaOffset);

                //Formatear la fecha en formato ISO sin la Z al final (que indica UTC)
                const fechaISO = fechaChile.toISOString().slice(0, 10);

                //Agregar el offset de Chile manualmente
                return `${fechaISO}-03:00`;
            };
            const asignacionData = {
                programa_id: parseInt(effectiveProgramId),
                item_ruta_id: proceso.id,
                operador_id: operadorId,
                fecha_inicio: formatearFechaChile(fechaInicio),
                fecha_fin: formatearFechaChile(fechaFin),
                is_removing: isRemoving
            };

            console.log("Datos de asignación formateados:", asignacionData);
            
            //Llamar al endpoint para asignar/desasignar operador
            const resp_asignacion = await crearAsignacion(asignacionData);
            console.log("Respuesta de la asginación:", resp_asignacion);

            toast.success(isRemoving ? 'Operador desasignado correctamente' : 'Operador asignado correctamente');

            //Recargar las tareas para la fecha actual
            await fetchTasksForDate();
        } catch (error){
            console.error("Error al asignar / desasignar operador:", error);
            toast.error(isRemoving ? 'Error al desasignar operador' : 'Error al asignar operador');

            await fetchTasksForDate();
        }
    }

    // 3. Añadir función para manejar la finalización exitosa
    const handleFinalizacionExitosa = (resultado) => {
        toast.success('Día finalizado correctamente');
        
        // Si el siguiente día está en las fechas disponibles, navegar a él
        if (resultado && resultado.siguiente_dia) {
            const siguienteDiaIndex = availableDates.indexOf(resultado.siguiente_dia);
            if (siguienteDiaIndex >= 0) {
                setSelectedDateIndex(siguienteDiaIndex);
                setCurrentDate(resultado.siguiente_dia);
            }
        }
        
        // Recargar datos
        fetchTasksForDate();
    };

    // 4. Añadir función para mostrar genealogía
    const handleVerGenealogia = (tarea) => {
        console.log("Tarea seleccionada para genealogía:", tarea);
        
        // Una tarea original debe tener tiene_fragmentos=true
        // O una continuación debe tener tarea_original_id
        if (!tarea.tiene_fragmentos && !tarea.tarea_original_id) {
            toast.error('Esta tarea no tiene información de fragmentación');
            return;
        }
        
        setTareaSeleccionada(tarea);
        setShowGenealogiaModal(true);
    };

    // Función para cargar la timeline
    const loadTimelineData = async () => {
        if (!effectiveProgramId) return;
        
        try {
            setTimelineLoading(true);
            const data = await getProgramTimelineEjecucion(effectiveProgramId);
            
            // Convertir datos para la timeline
            const processedGroups = data.groups;
            const processedItems = data.items.map(item => ({
                ...item,
                start_time: moment(item.start_time).toDate(),
                end_time: moment(item.end_time).toDate(),
                itemProps: {
                    style: {
                        backgroundColor: item.estado === 'Terminado' ? '#4CAF50' : 
                                        item.estado === 'En Proceso' ? '#2196F3' : 
                                        item.estado === 'Detenido' ? '#FF9800' : '#9E9E9E',
                        color: 'white',
                        borderRadius: '4px',
                        padding: '2px 6px'
                    },
                    onDoubleClick: () => {
                        // Navegar a la fecha correspondiente
                        const dateIndex = availableDates.indexOf(item.fecha);
                        if (dateIndex >= 0) {
                            setSelectedDateIndex(dateIndex);
                            setCurrentDate(item.fecha);
                        }
                    }
                }
            }));
            
            setTimelineData({
                groups: processedGroups,
                items: processedItems
            });
        } catch (error) {
            toast.error("Error al cargar la timeline de ejecución");
            console.error(error);
        } finally {
            setTimelineLoading(false);
        }
    };

    // Efecto para cargar la timeline cuando cambia el programa
    useEffect(() => {
        if (showTimeline && effectiveProgramId) {
            loadTimelineData();
        }
    }, [showTimeline, effectiveProgramId]);

    if (loading) return <LoadingSpinner message="Cargando reporte..." />;
    if (error) return (
        <div className="supervisor-report">
            <CompNavbar />
            <Container className="mt-4">
                <div className="alert alert-danger">
                    Error al cargar el reporte: {error}
                </div>
                <Link to={`/programs/${effectiveProgramId}`} className="btn btn-secondary">
                    Volver al Programa
                </Link>
            </Container>
            <Footer />
        </div>
    );

    return (
        <div className="supervisor-report">
            <CompNavbar />
            <Container className="mt-4">
                <div className="report-header d-flex justify-content-between align-items-center">
                    <Link to={`/programs/${effectiveProgramId}`} className="btn btn-outline-secondary">
                        <FaArrowLeft className="me-2" />
                        Volver al Programa
                    </Link>
                    <Link to={`/supervisor-reports`} className="btn btn-outline-secondary">
                        <FaArrowLeft className="me-2" />
                        Volver a Reportes
                    </Link>
                    <h2 className="report-title">Reporte de Supervisor</h2>
                </div>

                <div className="date-navigation">
                    <ButtonGroup className="w-100 justify-content-center align-items-center">
                        <Button 
                            variant="outline-primary"
                            onClick={() => handleDateNavigation('prev')}
                            disabled={selectedDateIndex === 0}
                        >
                            &lt; Día Anterior
                        </Button>
                        
                        <DatePicker
                            selected={currentDate ? moment(currentDate).toDate() : null}
                            onChange={date => {
                                const formattedDate = moment(date).format('YYYY-MM-DD');
                                console.log('Fecha seleccionada:', formattedDate);
                                const newIndex = availableDates.indexOf(formattedDate);
                                if (newIndex !== -1) {
                                    setSelectedDateIndex(newIndex);
                                    setCurrentDate(formattedDate);
                                }
                            }}
                            minDate={programDateRange.start}
                            maxDate={programDateRange.end}
                            dateFormat="dd/MM/yyyy"
                            filterDate={date => {
                                const dateStr = moment(date).format('YYYY-MM-DD');
                                return availableDates.includes(dateStr);
                            }}
                            className="form-control text-center"
                            customInput={
                                <Button variant="light" className="date-display">
                                    {currentDate ? moment(currentDate).format('DD/MM/YYYY') : 'Seleccione fecha'}
                                </Button>
                            }
                            showMonthDropdown
                            showYearDropdown
                            dropdownMode="select"
                            includeDates={availableDates.map(date => moment(date).toDate())}
                        />
                        
                        <Button 
                            variant="outline-primary"
                            onClick={() => handleDateNavigation('next')}
                            disabled={selectedDateIndex === availableDates.length - 1}
                        >
                            Siguiente Día &gt;
                        </Button>
                    </ButtonGroup>
                </div>
                <div className="action-toolbar d-flex justify-content-between align-items-center mb-3">
                    <div className="total-kilos-alert flex-grow-1">
                        <strong>Total Kilos Programados para el día:</strong> {displayedTasks.reduce((sum, task) => sum + task.kilos_programados, 0).toFixed(2)} kg
                    </div>
                    <Button 
                        variant="primary" 
                        onClick={() => setShowTableModal(true)}
                        className="ms-2"
                    >
                        <FaExpand className="me-2" />
                        Ver Tabla Completa
                    </Button>
                    <Button 
                        variant="success" 
                        onClick={() => {
                            if(effectiveProgramId){
                                setShowFinalizarDiaModal(true)
                            } else {
                                toast.error('No se pudo identificar el programa');
                            }
                        }}
                        className="ms-2"
                        disabled={!effectiveProgramId}
                    >
                        <FaCalendarCheck className="me-2" />
                        Finalizar Día
                    </Button>
                </div>

                <div className="timeline-controls mt-3 mb-3">
                    <Button 
                        variant={showTimeline ? "primary" : "outline-primary"} 
                        onClick={() => setShowTimeline(!showTimeline)}
                    >
                        {showTimeline ? "Ocultar Timeline de Ejecución" : "Mostrar Timeline de Ejecución"}
                    </Button>
                </div>

                {showTimeline && (
                    <div className="timeline-container mt-3 mb-4">
                        {timelineLoading ? (
                            <div className="text-center p-4">
                                <LoadingSpinner message="Cargando timeline..." />
                            </div>
                        ) : timelineData.items.length === 0 ? (
                            <div className="alert alert-info">
                                No hay datos de ejecución para mostrar en la timeline.
                            </div>
                        ) : (
                            <Timeline
                                groups={timelineData.groups}
                                items={timelineData.items}
                                defaultTimeStart={moment().subtract(7, 'day').startOf('day')}
                                defaultTimeEnd={moment().add(7, 'day').endOf('day')}
                                canMove={false}
                                canResize={false}
                                canChangeGroup={false}
                                itemHeightRatio={0.7}
                                lineHeight={40}
                                itemTouchSendsClick={false}
                                stackItems
                                sidebarWidth={150}
                                traditionalZoom
                                horizontalLineClassNamesForGroup={(group) => []}
                            />
                        )}
                    </div>
                )}

                {displayedTasks.length > 0 ? (
                    <>
                        <div className="report-table">
                            <Table>
                                <thead>
                                    <tr>
                                        <th className="col-drag"></th>
                                        <th className="col-priority">Prioridad</th>
                                        <th className="col-ot">OT</th>
                                        <th className="col-process">Proceso</th>
                                        <th className="col-machine">Máquina</th>
                                        <th className="col-operator">Operador</th>
                                        <th className="col-quantity">Cant. Prog.</th>
                                        <th className="col-kilos">Kilos Prog.</th>
                                        <th className="col-schedule">Horario</th>
                                        <th className="col-status">Estado</th>
                                        <th className="col-produced">Kilos Fab.</th>
                                        <th className="col-compliance">% Cumpl.</th>
                                        <th className="col-observations">Observaciones</th>
                                    </tr>
                                </thead>
                                <ReactSortable
                                    tag="tbody"
                                    list={displayedTasks}
                                    setList={newState => {
                                        if (newState.length === displayedTasks.length) {
                                            handlePriorityUpdate(newState);
                                        }
                                    }}
                                    // Asegurarse de que los IDs sean numéricos
                                    setData={(dataSet) => {
                                        return dataSet.map(item => ({
                                            ...item,
                                            id: typeof item.id === 'string' && item.id.startsWith('item_') 
                                                ? parseInt(item.id.split('_')[1]) 
                                                : item.id
                                        }));
                                    }}
                                    animation={150}
                                    handle=".drag-handle"
                                    ghostClass="sortable-ghost"
                                    dragClass="sortable-drag"
                                    chosenClass="sortable-chosen"
                                    forceFallback={false}
                                    fallbackOnBody={false}
                                    scroll={true}
                                    bubbleScroll={true}
                                    scrollSensitivity={30}
                                    scrollSpeed={10}
                                    delayOnTouchOnly={true}
                                    delay={0}
                                    swapThreshold={0.65}
                                    dataIdAttr="data-id"
                                >
                                    {displayedTasks.map((task, index) => (
                                        <tr key={task.id} data-id={task.id} className={task.es_continuacion ? 'tarea-continuacion' : ''}>
                                            <td className="col-drag">
                                                <div className="drag-handle">
                                                    <span>≡</span>
                                                </div>
                                            </td>
                                            <td className="col-priority">
                                                <strong>{index + 1}</strong>
                                            </td>
                                            <td className="col-ot">{task.ot_codigo}</td>
                                            <td className="col-process">
                                                {task.proceso.descripcion}
                                                {task.es_continuacion && (
                                                    <div className="continuacion-badge ms-2" 
                                                        title={`Continuación de tarea del ${task.tarea_padre_fecha}. 
                                                                Avance previo: ${task.tarea_padre_porcentaje.toFixed(1)}% 
                                                                (${task.tarea_padre_kilos.toFixed(2)} kg)`}>
                                                        <FaArrowLeft className="me-1" style={{color: '#ff7700'}} />
                                                        <small>Continuación</small>
                                                    </div>
                                                )}
                                                {task.tiene_fragmentos && (
                                                    <Button 
                                                        variant="link" 
                                                        size="sm" 
                                                        className="p-0 ms-1"
                                                        onClick={() => handleVerGenealogia(task)}
                                                        title="Ver historial de fragmentación"
                                                    >
                                                        <FaCodeBranch />
                                                    </Button>
                                                )}
                                            </td>
                                            <td className="col-machine">{task.maquina ? task.maquina.descripcion : 'Sin máquina'}</td>
                                            <td className="col-operator">
                                                <span>{task.operador_nombre || 'Sin asignar'}</span>
                                                {task.asignado_por_nombre && (
                                                    <small className="text-muted">
                                                        Asignado por: {task.asignado_por_nombre} <br />
                                                        {task.fecha_asignacion && new Date(task.fecha_asignacion).toLocaleString()}
                                                    </small>
                                                )}
                                                <Button
                                                    variant="outline-primary"
                                                    size="sm"
                                                    onClick={() => openOperadorModal(task)}
                                                    title="Asignar operador"
                                                    className="mt-1"
                                                >
                                                    <FaUserPlus />
                                                </Button>
                                            </td>
                                            <td className="col-quantity">{task.cantidad_programada}</td>
                                            <td className="col-kilos">{task.kilos_programados.toFixed(2)}</td>
                                            <td className="col-schedule">{`${task.hora_inicio} - ${task.hora_fin}`}</td>
                                            <td className="col-status">
                                                <Form.Select
                                                    size="sm"
                                                    value={taskStates[task.id] || task.estado}
                                                    onChange={(e) => handleStateChange(task.id, e.target.value, task)}
                                                >
                                                    <option value="Pendiente">Pendiente</option>
                                                    <option value="En Proceso">En Proceso</option>
                                                    <option value="Terminado">Terminado</option>
                                                    <option value="Detenido">Detenido</option>
                                                </Form.Select>
                                            </td>
                                            <td className="col-produced">
                                                <Form.Control
                                                    type="number"
                                                    step="0.01"
                                                    value={kilosFabricados[task.id] !== undefined ? kilosFabricados[task.id] : (task.kilos_fabricados || '')}
                                                    onChange={(e) => handleKilosChange(task.id, e.target.value, task)}
                                                    disabled={!editableStates[task.id] && taskStates[task.id] === 'Terminado'}
                                                />
                                            </td>
                                            <td className="col-compliance">
                                                {porcentajeCumplimiento[task.id] ? 
                                                    `${porcentajeCumplimiento[task.id].toFixed(1)}%` : 
                                                    '0%'}
                                            </td>
                                            <td className="col-observations">
                                                <Form.Control
                                                    size="sm"
                                                    type="text"
                                                    value={task.observaciones || ''}
                                                    onChange={(e) => handleObservacionesChange(task.id, e.target.value, task)}
                                                    placeholder="Agregar observación"
                                                />
                                            </td>
                                        </tr>
                                    ))}
                                </ReactSortable>
                            </Table>

                            <OperadorSelectionModal
                                show={showOperadorModal}
                                onHide={() => setShowOperadorModal(false)}
                                maquinaId={currentProceso?.maquina.id}
                                procesoId={currentProceso?.id}
                                currentOperadorId={currentProceso?.operador_id}
                                onSelect={(operadorId) => handleOperadorChange(currentProceso, operadorId)}
                            />
                        </div>
                        <TableFullViewModal
                            show={showTableModal}
                            onHide={() => setShowTableModal(false)}
                            tasks={displayedTasks}
                            currentDate={currentDate}
                            taskStates={taskStates}
                            kilosFabricados={kilosFabricados}
                            porcentajeCumplimiento={porcentajeCumplimiento}
                        /> 
                    </>
                ) : (
                    <div className="no-tasks-message">
                        No hay tareas programadas para este día
                    </div>
                )}

                <div className="d-flex justify-content-end mt-4 mb-2">
                    <Button 
                        className="save-button" 
                        onClick={handleSaveReport}
                        disabled={Object.keys(pendingChanges).length === 0}
                    >
                        <FaSave className="me-2" />
                        Guardar Reporte
                        {Object.keys(pendingChanges).length > 0 && 
                            ` (${Object.keys(pendingChanges).length} cambios pendientes)`
                        }
                    </Button>
                </div>
            </Container>
            <Footer />

            <FinalizarDiaModal
                show={showFinalizarDiaModal}
                onHide={() => setShowFinalizarDiaModal(false)}
                programId={effectiveProgramId}
                fecha={currentDate}
                onFinalizacionExitosa={handleFinalizacionExitosa}
            />

            <Modal
                show={showGenealogiaModal}
                onHide={() => setShowGenealogiaModal(false)}
                size="lg"
                centered
            >
                <Modal.Header closeButton>
                    <Modal.Title>
                        Historial de Tarea
                        {tareaSeleccionada && (
                            <span className="ms-2 text-muted">
                                {tareaSeleccionada.proceso.descripcion} (OT: {tareaSeleccionada.ot_codigo})
                            </span>
                        )}
                    </Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    {tareaSeleccionada && (
                        <TareaGenealogiaView 
                            tareaSeleccionada={tareaSeleccionada} 
                        />
                    )}
                </Modal.Body>
            </Modal>
        </div>
    );
}