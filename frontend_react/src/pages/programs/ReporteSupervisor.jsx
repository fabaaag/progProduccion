import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Container, Table, Form, Button, ButtonGroup } from 'react-bootstrap';
import { ReactSortable } from "react-sortablejs";
import CompNavbar from "../../components/Navbar/CompNavbar";
import { Footer } from "../../components/Footer/Footer";
import { LoadingSpinner } from "../../components/UI/LoadingSpinner/LoadingSpinner";
import { toast } from "react-hot-toast";
import moment from 'moment';
import { getSupervisorReport, updateSupervisorReport, getProcesoTimeline } from '../../api/programs.api';
import { crearAsignacion } from '../../api/asignaciones.api';
import { FaArrowLeft, FaSave, FaUser, FaUserPlus, FaExpand } from 'react-icons/fa';
import './ReporteSupervisor.css';
import DatePicker from 'react-datepicker';
import "react-datepicker/dist/react-datepicker.css";
import { OperadorSelectionModal } from '../../components/Programa/OperadorSelectionModal';
import TableFullViewModal from './ReporteSupervisorSubComp/TableFullViewModal';

export function ReporteSupervisor() {
    const { programId } = useParams();
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

    //Estados para la asignación de operadores
    const [showOperadorModal, setShowOperadorModal] = useState(false);
    const [currentProceso, setCurrentProceso] = useState(null);
    const [operadores, setOperadores] = useState([]);
    const [showTableModal, setShowTableModal] = useState(false);

    const fetchTasksForDate = async () => {
        try {
            setLoading(true);
            setError(null);
            
            if (!programId || !currentDate) {
                console.log("Faltan datos:", { programId, currentDate });
                return; // En lugar de lanzar error, simplemente retornamos
            }

            const response = await getSupervisorReport(programId);
            console.log('Respuesta del servidor:', response);
            
            if (!response.tareas || !Array.isArray(response.tareas)) {
                throw new Error('Formato de respuesta inválido');
            }

            // Filtrar tareas para la fecha actual
            const tareasDelDia = response.tareas.filter(tarea => 
                tarea.fecha === currentDate
            );

            console.log(`Tareas para ${currentDate}:`, tareasDelDia);

            // Actualizar el estado con las tareas filtradas
            setDisplayedTasks(tareasDelDia);

            // Cargar los kilos fabricados y porcentajes existentes
            const kilosFab = {};
            const porcentajes = {};
            tareasDelDia.forEach(tarea => {
                if (tarea.kilos_fabricados) {
                    kilosFab[tarea.id] = tarea.kilos_fabricados;
                    porcentajes[tarea.id] = (tarea.kilos_fabricados / tarea.kilos_programados) * 100;
                }
            });
            setKilosFabricados(kilosFab);
            setPorcentajeCumplimiento(porcentajes);

        } catch (error) {
            console.error('Error al cargar tareas:', error);
            setError(error.message);
            toast.error(`Error: ${error.message}`);
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
        console.log("ProgramId recibido:", programId);
        const initializeData = async () => {
            if (!programId) {
                console.error("No se recibió programId");
                toast.error("Error: No se pudo identificar el programa");
                return;
            }
            try {
                setLoading(true);
                const response = await getSupervisorReport(programId);
                const programa = response.programa;
                
                console.log('Datos del programa recibidos:', programa);
                
                if (!programa || !programa.fecha_inicio || !programa.fecha_fin) {
                    throw new Error('El programa no tiene fechas definidas');
                }

                let startDate = moment(programa.fecha_inicio).isValid() 
                    ? moment(programa.fecha_inicio) 
                    : moment(programa.fecha_inicio, ['YYYY-MM-DD', 'DD/MM/YYYY', 'YYYY/MM/DD']);
                    
                let endDate = moment(programa.fecha_fin).isValid() 
                    ? moment(programa.fecha_fin) 
                    : moment(programa.fecha_fin, ['YYYY-MM-DD', 'DD/MM/YYYY', 'YYYY/MM/DD']);

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
                setCurrentDate(firstDate);
                setSelectedDateIndex(0);
                
            } catch (error) {
                console.error("Error al inicializar datos:", error);
                setError(error.message);
                toast.error(`Error al cargar los datos iniciales: ${error.message}`);
            } finally {
                setLoading(false);
            }
        };

        initializeData();
    }, [programId]);

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
        const kilosNum = parseFloat(kilos) || 0;
        setKilosFabricados(prev => ({...prev, [taskId]: kilosNum}));
        
        // Calcular porcentaje localmente
        const porcentaje = (kilosNum / task.kilos_programados) * 100;
        setPorcentajeCumplimiento(prev => ({...prev, [taskId]: porcentaje}));
        
        // Guardar cambio pendiente
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
            
            // Crear un array de promesas para todas las actualizaciones
            const updatePromises = displayedTasks.map((task, index) => {
                const taskData = {
                    id: task.id,
                    priority: index + 1, // La prioridad basada en la posición actual
                    proceso_id: task.proceso_id,
                    kilos_fabricados: kilosFabricados[task.id] || task.kilos_fabricados || 0,
                    cantidad_programada: task.cantidad_programada,
                    fecha: task.fecha,
                    estado: taskStates[task.id] || task.estado || 'Pendiente',
                    observaciones: task.observaciones || ''
                };
                return updateSupervisorReport(programId, taskData);
            });

            // Esperar a que todas las actualizaciones se completen
            await Promise.all(updatePromises);
            
            // Limpiar cambios pendientes
            setPendingChanges({});
            
            // Recargar datos
            await fetchTasksForDate();
            
            toast.success('Reporte guardado correctamente');
        } catch (error) {
            console.error('Error al guardar el reporte:', error);
            toast.error('Error al guardar el reporte');
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
        if(!programId){
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
                const timelineData = await getProcesoTimeline(programId, proceso.id);
                console.log('Datos del timeline recibidos:', timelineData);

                fechaInicio = timelineData.fecha_inicio;
                fechaFin = timelineData.fecha_fin;
            } catch (error){
                console.warn('Error al obtener fechas del timeline:', error);

                //Si hay error usar la fecha actual y una duración predeterminada
                fechaInicio = new Date();
                fechaFin = newDate(fechaInicio);
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
                programa_id: parseInt(programId),
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

    if (loading) return <LoadingSpinner message="Cargando reporte..." />;
    if (error) return (
        <div className="supervisor-report">
            <CompNavbar />
            <Container className="mt-4">
                <div className="alert alert-danger">
                    Error al cargar el reporte: {error}
                </div>
                <Link to={`/programs/${programId}`} className="btn btn-secondary">
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
                    <Link to={`/programs/${programId}`} className="btn btn-outline-secondary">
                        <FaArrowLeft className="me-2" />
                        Volver al Programa
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
                    <div className="total-kilos-alert grow-1">
                    <strong>Total Kilos Programados para el día:</strong> {displayedTasks.reduce((sum, task) => sum + task.kilos_programados, 0).toFixed(2)} kg
                    </div>
                    <Button
                        variant="primary" 
                        onClick={() => setShowTableModal(true)}
                        className="ms-3 view-full-table-btn"
                    >
                        <FaExpand className="me-2" />
                        Ver Tabla Completa
                        </Button>
                </div>

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
                                    animation={200}
                                    handle=".drag-handle"
                                    ghostClass="sortable-ghost"
                                    dragClass="sortable-drag"
                                    chosenClass="sortable-chosen"
                                    forceFallback={true}
                                    fallbackOnBody={true}
                                    scroll={true}
                                    bubbleScroll={true}
                                    scrollSensitivity={30}
                                    scrollSpeed={10}
                                    delayOnTouchOnly={true}
                                    delay={2}
                                    swapThreshold={0.5}
                                    dataIdAttr="data-id"
                                >
                                    {displayedTasks.map((task, index) => (
                                        <tr key={task.id} data-id={task.id}>
                                            <td className="col-drag">
                                                <div className="drag-handle">
                                                    ≡
                                                </div>
                                            </td>
                                            <td className="col-priority">
                                                <strong>{index + 1}</strong>
                                            </td>
                                            <td className="col-ot">{task.ot_codigo}</td>
                                            <td className="col-process">{task.proceso}</td>
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
                                                    value={kilosFabricados[task.id] || task.kilos_fabricados || ''}
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

                <div className="d-flex justify-content-end mt-4">
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
        </div>
    );
}