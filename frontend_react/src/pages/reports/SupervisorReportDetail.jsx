import React, { useState, useEffect } from 'react';
import { Container, Alert, Spinner, Button } from 'react-bootstrap';
import { useParams } from 'react-router-dom';
import { supervisorReportAPI } from '../../api/supervisorReport.api';
import { FaStream } from 'react-icons/fa';
import moment from 'moment';
import 'moment/locale/es';

// Componentes
import { TaskTable } from '../../components/Reports/TaskTable';
import { DateNavigation } from '../../components/Reports/DateNavigation';
import { TaskStatusBar } from '../../components/Reports/TaskStatusBar';
import { DayFinalization } from '../../components/Reports/DayFinalization';
import { OperatorAssignment } from '../../components/Reports/OperatorAssignment';
import CompNavbar from '../../components/Navbar/CompNavbar';
import { Footer } from '../../components/Footer/Footer';

//Modales
import { FullViewModal } from './modals/FullViewModal';
import { TimelineModal } from './modals/TimelineModal';
import { GenealogiaModal } from './modals/GenealogiaModal';

//Estilos
import './css/SupervisorReport.css'

export const SupervisorReportDetail = () => {
    const { programId } = useParams();
    const [currentDate, setCurrentDate] = useState(null);
    const [tasks, setTasks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    
    //Estados para modales
    const [showFullView, setShowFullView] = useState(false);
    const [showTimeline, setShowTimeline] = useState(false);
    const [showGenealogia, setShowGenealogia] = useState(false);
    const [selectedTask, setSelectedTask] = useState(null);

    //Estados para TaskTable
    const [kilosFabricados, setKilosFabricados] = useState({});
    const [taskStates, setTaskStates] = useState({});
    const [showOperatorAssign, setShowOperatorAssign] = useState(false);
    const [unidadesFabricadas, setUnidadesFabricadas] = useState({});

    const [programDates, setProgramDates] = useState({
        startDate: null,
        endDate: null
    });

    //Estado para detalles de la tarea
    const [selectedTaskDetails, setSelectedTaskDetails] = useState(null);

    const loadTaskDetails = async (taskId) => {
        try {
            const details = await supervisorReportAPI.getTaskProductionDetails(taskId);
            setSelectedTaskDetails(details);
        } catch (error) {
            console.error('Error al cargar detalles de la tarea:', error);
            // Manejar el error según necesites
        }
    };

    // Función auxiliar para parsear fechas correctamente
    const parseDate = (dateString) => {
        if (!dateString) return null;
        const [year, month, day] = dateString.split('-').map(Number);
        return new Date(year, month - 1, day); // month - 1 porque en JS los meses van de 0-11
    };

    useEffect(() => {
        const init = async () => {
            try {
                // Obtener el reporte inicial sin especificar fecha - dejemos que el backend decida
                const response = await supervisorReportAPI.getReportDetail(programId);
                
                if (response.programa) {
                    setProgramDates({
                        startDate: moment(response.programa.fecha_inicio).toDate(),
                        endDate: moment(response.programa.fecha_fin).toDate()
                    });
                    
                    // Usar moment para evitar el ajuste de zona horaria
                    const fechaActual = moment(response.programa.fecha_actual).format('YYYY-MM-DD');
                    setCurrentDate(moment(fechaActual, 'YYYY-MM-DD').toDate());
                    setTasks(response.tareas || []);
                }
                
                setLoading(false);
            } catch (error) {
                console.error('Error en init:', error);
                setError('Error al cargar los datos del programa');
                setLoading(false);
            }
        };

        init();
    }, [programId]);

    const handleDateChange = async (newDate) => {
        try {
            // Agregar logs de depuración
            console.log("Fecha seleccionada (objeto Date):", newDate);
            const formattedDate = moment(newDate).format('YYYY-MM-DD');
            console.log("Fecha formateada para API:", formattedDate);
            
            const response = await supervisorReportAPI.getReportDetail(programId, formattedDate);
            console.log("Respuesta del API:", response);
            
            setCurrentDate(newDate);
            setTasks(response.tareas || []);
        } catch (error) {
            console.error('Error al cambiar fecha:', error);
            setError('Error al cargar las tareas del día');
        }
    };

    const handleTasksUpdate = async (updatedTasks) => {
        setTasks(updatedTasks);
    };

    const handleOperatorAssign = (task) => {
        setSelectedTask(task);
        setShowOperatorAssign(true);
    };

    const handleShowGenealogia = (task) => {
        setSelectedTask(task);
        setShowGenealogia(true);
    };

    const handleKilosChange = (taskId, value, task) => {
        // Convertir el valor a número
        const kilos = parseFloat(value) || 0;
        
        // Actualizar el estado de kilos
        setKilosFabricados(prev => ({
            ...prev,
            [taskId]: kilos
        }));
        
        // Calcular unidades basado en peso unitario
        if (task.orden_trabajo && task.orden_trabajo.peso_unitario) {
            const pesoUnitario = parseFloat(task.orden_trabajo.peso_unitario);
            if (pesoUnitario > 0) {
                const unidades = Math.round(kilos / pesoUnitario);
                
                // Actualizar el estado de unidades
                setUnidadesFabricadas(prev => ({
                    ...prev,
                    [taskId]: unidades
                }));
                
                // Calcular nuevo porcentaje de cumplimiento
                const porcentajeCumplimiento = (unidades / task.cantidades.total_dia) * 100;
                
                // Actualizar la tarea con unidades y porcentaje
                const updatedTasks = tasks.map(t => 
                    t.id === taskId 
                        ? { 
                            ...t, 
                            cantidades: {
                                ...t.cantidades,
                                completada: unidades
                            },
                            porcentaje_cumplimiento: porcentajeCumplimiento
                        } 
                        : t
                );
                setTasks(updatedTasks);
            }
        }
    };

    const handleStateChange = (taskId, value, task) => {
        // Solo actualizamos el estado local, sin llamada a API
        setTaskStates(prev => ({
            ...prev,
            [taskId]: value
        }));
    };

    const handleObservacionesChange = (taskId, value, task) => {
        // Actualizar localmente sin llamar a la API
        const updatedTasks = tasks.map(t => 
            t.id === taskId ? { ...t, observaciones: value} : t
        );
        setTasks(updatedTasks);
    };

    // Añadir un nuevo handler para guardar los cambios
    const handleSaveTask = async (taskId, task) => {
        try {
            // Obtener kilos y unidades
            const kilos = kilosFabricados[taskId] || task.kilos.fabricados || 0;
            const unidades = unidadesFabricadas[taskId] || task.cantidades.completada || 0;
            
            // Guardar en el servidor
            await supervisorReportAPI.updateTask(programId, {
                tarea_id: taskId,
                kilos_fabricados: kilos,
                unidades_fabricadas: unidades,
                estado: taskStates[taskId] || task.estado,
                observaciones: task.observaciones || ''
            });
            
            // Recargar los datos para reflejar los cambios guardados
            handleDateChange(new Date(currentDate));
        } catch (error) {
            console.error('Error al guardar los cambios de la tarea:', error);
        }
    };

    const handleFinishDay = async () => {
        try {
            const formattedDate = currentDate.toISOString().split('T')[0];
            const preview = await supervisorReportAPI.getDayFinalizationPreview(programId, formattedDate);
            
            // Aquí podrías mostrar un modal con la preview antes de finalizar
            const confirmed = window.confirm('¿Desea finalizar el día?');
            
            if (confirmed) {
                await supervisorReportAPI.finishDay(programId, formattedDate);
                handleDateChange(new Date(currentDate));
            }
        } catch (error) {
            console.error('Error al finalizar el día:', error);
        }
    };

    return (
        <>
            <CompNavbar />
            <Container>
                {!programId ? (
                    <Alert variant="danger" className="my-3">
                        No se encontró el ID del programa
                    </Alert>
                ) : loading ? (
                    <div className="text-center my-5">
                        <Spinner animation="border" role="status">
                            <span className="visually-hidden">Cargando...</span>
                        </Spinner>
                    </div>
                ) : error ? (
                    <Alert variant="danger" className="my-3">
                        {error}
                    </Alert>
                ) : (
                    <>
                        <div className="d-flex justify-content-between align-items-center mb-3">
                            {currentDate && (
                                <DateNavigation 
                                    currentDate={currentDate}
                                    onDateChange={handleDateChange}
                                    programStartDate={programDates.startDate}
                                    programEndDate={programDates.endDate}
                                />
                            )}
                            <Button 
                                variant="outline-primary"
                                onClick={() => setShowTimeline(true)}
                                className="ms-2"
                            >
                                <FaStream className="me-2" />
                                Ver Timeline
                            </Button>
                        </div>

                        {selectedTaskDetails && (
                            <ProductionDetailsForm 
                                orderDetails={selectedTaskDetails}
                                disabled={false}
                            />
                        )}

                        <TaskStatusBar tasks={tasks} />

                        <TaskTable 
                            tasks={tasks}
                            onTasksUpdate={handleTasksUpdate}
                            onOperatorAssign={handleOperatorAssign}
                            onShowGenealogia={handleShowGenealogia}
                            kilosFabricados={kilosFabricados}
                            onKilosChange={handleKilosChange}
                            taskStates={taskStates}
                            onStateChange={handleStateChange}
                            onObservacionesChange={handleObservacionesChange}
                            onTaskSelect={(task) => loadTaskDetails(task.id)}
                            onSaveTask={handleSaveTask}
                            unidadesFabricadas={unidadesFabricadas}
                        />
                        {/* Modales */}
                        <FullViewModal 
                            show={showFullView}
                            onHide={() => setShowFullView(false)}
                            tasks={tasks}
                        />

                        <TimelineModal 
                            show={showTimeline}
                            onHide={() => setShowTimeline(false)}
                            programId={programId}
                            currentDate={currentDate}  
                        />
                        
                        <GenealogiaModal 
                            show={showGenealogia}
                            onHide= {() => setShowGenealogia(false)}
                            task={selectedTask}
                        />
                        <OperatorAssignment 
                            show={showOperatorAssign}
                            onHide={() => setShowOperatorAssign(false)}
                            task={selectedTask}
                        />
                    </>
                )}
            </Container>
            <Footer />        
        </>
    );
};
