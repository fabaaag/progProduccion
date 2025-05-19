import React, { useEffect, useState } from "react";
import { useParams, Link, redirect, useNavigate } from "react-router-dom";
import { Button, Dropdown, Form, Badge, Card, Collapse, Table, Modal, Alert } from "react-bootstrap";
import { ReactSortable } from "react-sortablejs";
import CompNavbar from "../../components/Navbar/CompNavbar";
import { Footer } from "../../components/Footer/Footer";
import { getProgram, updatePriorities, deleteOrder, getMaquinas, generateProgramPDF, getProcesoTimeline, verificarReajustesPrograma, aplicarReajustesPrograma } from "../../api/programs.api";
import Timeline from "react-calendar-timeline";
import "react-calendar-timeline/dist/Timeline.scss";
import { toast } from "react-hot-toast";
import moment from "moment";
import { LoadingSpinner } from "../../components/UI/LoadingSpinner/LoadingSpinner";
import "./ProgramDetail.css";
import { FaArrowLeft, FaCalendarAlt, FaFlag, FaFilePdf, FaClipboardList, FaExclamationTriangle, FaSave, FaChevronDown, FaPlus } from "react-icons/fa";
import { ProgramMonitoring } from "../../components/Programa/ProgramMonitoring";
import { AgregarOrdenModal } from '../../components/Programa/AgregarOrdenModal';
// En ProgramDetail.jsx, al inicio donde están los imports
import { supervisorReportAPI } from "../../api/supervisorReport.api";

const AlertMessage = ({ type, icon, message }) => (
    <div className={`alert alert-${type} d-flex align-items-center`} role="alert">
        <div className="alert-icon me-3">
            {icon}
        </div>
        <div>{message}</div>
    </div>
);

export function ProgramDetail() {

    const HIDE_TEXT = true; // Cambiar f o t
     

    const { programId } = useParams();
    const navigate = useNavigate();
    const [programData, setProgramData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [overlayLoading, setOverlayLoading] = useState(false);
    const [otList, setOtList] = useState([]);
    const [timelineItems, setTimelineItems] = useState([]);
    const [showTimeline, setShowTimeline] = useState(false); // Control para mostrar el timeline
    const [timelineLoading, setTimelineLoading] = useState(false);
    const [timelineGroups, setTimelineGroups] = useState([]);
    const [timelineMode, setTimelineMode] = useState('planning'); // 'planning' o 'execution'

    const [expandedOTs, setExpandedOTs] = useState({});
    const [maquinas, setMaquinas] = useState([]);

    const [pendingChanges, setPendingChanges] = useState({});
    const [savingChanges, setSavingChanges] = useState(false);
    const [maquinasPorProceso, setMaquinasPorProceso] = useState({});


    // Para controlar la visibiidad de la alerta de cambios pendientes
    const [showPendingChangesAlert, setShowPendingChangesAlert] = useState(false);

    const [showAgregarOrden, setShowAgregarOrden] = useState(false);

    const [showReajustesModal, setShowReajustesModal] = useState(false);
    const [ajustes, setAjustes] = useState(null);

    //Agregar función para cargar máquinas por proceso
    const cargarMaquinasPorProceso = async (itemRuta) => {
        try{
            console.log("[Frontend] itemRuta completo:", itemRuta);

            //Verificar si el objecto tiene la propiedad codigo_proceso
            if(!itemRuta || !itemRuta.codigo_proceso){
                console.error("[Frontend] Error: itemRuta no tiene codigo_proceso", itemRuta);
                return [];
            }
            const codigoProceso = itemRuta.codigo_proceso;
            console.log(`[Frontend] Código de proceso extraído: ${codigoProceso}`);

            //Verificar que el código de proceso no sea null o undefined
            if(!codigoProceso){
                console.error('[Frontend] No se encontró código de proceso para el item:', itemRuta);
                return [];
            }
            console.log(`[Frontend] Llamando a getMáquinas con programId=${programId}, procesoCodigo=${codigoProceso} `);
            const maquinasData = await getMaquinas(programId, codigoProceso);

            console.log(`[Frontend] Máquinas recibidas para proceso ${codigoProceso}:`, maquinasData);
            setMaquinasPorProceso(prev => ({
                ...prev,
                [itemRuta.id]: maquinasData
            }));
            return maquinasData;
        } catch(error) {
            console.error('Error al cargar máquinas para el proceso:', error);
            toast.error("Error al cargar máquinas disponibles");
            return [];
        }
    };

    const handleProcessChange = (otId, procesoId, field, value) => {
        if(!otList){
            console.error('otList no está inicializado.');
            return;
        }
    
        console.log(`Cambio pendiente en OT: ${otId}, Proceso: ${procesoId}, Campo: ${field}, Valor: ${value}`);
    
        setOtList(prevOtList => {
            if(!prevOtList) return [];  // Retornamos array vacío si es undefined
    
            const newList = prevOtList.map(ot => {
                if(ot.orden_trabajo === otId && ot.procesos){
                return{
                    ...ot,
                    procesos: ot.procesos.map(proceso => {
                            if(proceso.id === procesoId){
                            return {
                                ...proceso,
                                [field]: value
                            };
                        }
                        return proceso;
                    })
                    };
                }
                return ot;
            });
            return newList;
        });

        setPendingChanges(prev => {
            const newChanges = {
                ...prev,
                [`${otId}-${procesoId}-${field}`]: {
                    otId,
                    procesoId,
                    field,
                    value
                }
            };
            console.log('Cambios pendientes:', newChanges);
            //Mostrar la alerta si hay cambios pendientes
            setShowPendingChangesAlert(true);

            return newChanges;
        });
    };

    const handleSaveChanges = async () => {
        try {
            setSavingChanges(true);
            setOverlayLoading(true);
            console.log("Guardando cambios:", pendingChanges);

            //Procesar cambios en procesos (estandar, cantidad, maquina)
            const procesosConCambios = {};

            //Agrupar cambios por ot y proceso
            Object.keys(pendingChanges).forEach(key => {
                if (!key.includes('_asignacion')){
                    const [otId, procesoId, field] = key.split('-');

                    if (!procesosConCambios[otId]){
                        procesosConCambios[otId] = {};
                    }

                    if (!procesosConCambios[otId][procesoId]) {
                        procesosConCambios[otId][procesoId] = {};
                    }

                    procesosConCambios[otId][procesoId][field] = pendingChanges[key].value;
                }
            });

            
            // Procesar cambios de prioridad
            const orderIds = otList.map((ot, index) => {
                const procesos = [];

                if (procesosConCambios[ot.orden_trabajo]){
                    Object.keys(procesosConCambios[ot.orden_trabajo]).forEach(procesoId => {
                        procesos.push({
                            id: parseInt(procesoId),
                            ...procesosConCambios[ot.orden_trabajo][procesoId]
                        });
                    });
                }

                return {
                    id: ot.orden_trabajo,
                    priority: index + 1 ,
                    procesos: procesos.length > 0 ? procesos: undefined
                }
            });
            
            if (orderIds.length > 0) {
                console.log("Actualizando prioridades:", orderIds);
                await updatePriorities(programId, orderIds, true);
            }
            
            // Limpiar cambios pendientes
            setPendingChanges({});

            //Ocultar la alerta después de guardar
            setShowPendingChangesAlert(false);
            
            // Recargar datos
            await fetchProgramData();
            
            toast.success("Cambios guardados correctamente");
        } catch (error) {
            console.error("Error al guardar los cambios:", error);
            toast.error(`Error al guardar los cambios: ${error.message}`);
        } finally {
            setSavingChanges(false);
        }
    };

    const handleToggleExpand = async(otId) => {
        const expandiendo = !expandedOTs[otId];
        setExpandedOTs((prevExpanded) => ({
            ...prevExpanded,
            [otId]: expandiendo
        }));

        //Si estamos expandiendo, cargar las máquinas para cada proceso
        if(expandiendo){
            const ot = otList.find(ot => ot.orden_trabajo === otId);
            if (ot && ot.procesos){ 
                for (const proceso of ot.procesos) { 
                    if(!maquinasPorProceso[proceso.id]){
                        await cargarMaquinasPorProceso(proceso);
                    }
                }
            }
        }
    };

    const toggleTimeline = () => {
        if (hayProcesosConEstandarCero()) {
            const procesosConEstandarCero = getProcesosConEstandarCero();

            toast.error(
                <div>
                    <p>No se puede proyectar: Hay procesos con estándar en 0</p>
                    <ul style={{ maxHeight: '200px', overflowY: 'auto', padding: '0 0 0 20px'}}>
                        {procesosConEstandarCero.map((p, idx) => (
                            <li key={idx}>{p.ot_codigo} - {p.proceso_descripcion}</li>
                        ))}
                    </ul>
                    <p>Por favor, corrija los valores antes de proyectar.</p>
                </div>,
                { duration: 5000 }
            );
            return; //Salimos de la función sin cambiar el estado del timeline
        }

        //Solo llegamos aquí si no hay procesos con estándar en 0
        if (!showTimeline) {
            setTimelineLoading(true);
            setTimeout(() => setTimelineLoading(false), 1000); // Simula carga
        }
        setShowTimeline(!showTimeline);
    };


    const fetchData = async () => {
        if(!programId){
            console.error("No hay programId disponible");
            return;
        }
        try{
            const maquinasData = await getMaquinas(programId);
            setMaquinas(maquinasData);    
        }catch(error){
            console.error("Error al cargar datos:", error);
            toast.error("Error al cargar las maquinas");
        }
    };

    const fetchProgramData = async () => {
        setLoading(true);
        try {
            const response = await getProgram(programId);
            console.log("Datos recibidos del backend:", response.data);
            
            setProgramData(response.program || {});
            
            // Procesar las órdenes de trabajo y sus asignaciones
            const ordenesTrabajo = response.ordenes_trabajo || [];
            setOtList(ordenesTrabajo);

            // Validar y procesar los datos del timeline
            if (response.routes_data && typeof response.routes_data === "object") {
                const { groups, items } = response.routes_data;

                // Procesar grupos y subgrupos
                if (Array.isArray(groups)) {
                    const flatGroups = groups.flatMap(ot => {
                        // Grupo principal (OT)
                        const mainGroup = {
                            id: ot.id,
                            title: ot.orden_trabajo_codigo_ot || "OT Sin código",
                            stackItems: true,
                            height: 70
                        };

                        // Subgrupos (procesos)
                        const processGroups = ot.procesos?.map(proceso => ({
                            id: `${ot.id}-${proceso.id}`,
                            title: proceso.descripcion || "Sin descripción",
                            height: 50,
                            parent: ot.id
                        })) || [];

                        return [mainGroup, ...processGroups];
                    });

                    setTimelineGroups(flatGroups);
                }

                // Procesar items del timeline
                if (Array.isArray(items)) {
                    const timelineItems = items.map((item) => {
                        // Determinar el color basado en el estado y asignación
                        let backgroundColor;
                        if (item.asignado) {
                            backgroundColor = "#4CAF50"; // Verde si tiene asignación
                        } else if (new Date(item.end_time) < new Date()) {
                            backgroundColor = "#ff4444"; // Rojo si está vencido
                        } else {
                            backgroundColor = "#FFA726"; // Naranja por defecto
                        }

                        return {
                            id: item.id,
                            group: `${item.ot_id}-${item.proceso_id}`,
                            title: `${item.name}${item.operador_nombre ? ` - Op: ${item.operador_nombre}` : ''}`,
                            start_time: new Date(item.start_time),
                            end_time: new Date(item.end_time),
                            itemProps: {
                                style: {
                                    backgroundColor,
                                    color: 'white',
                                    borderRadius: '4px',
                                    padding: '2px 6px',
                                    fontSize: '12px'
                                },
                                'data-tooltip': `
                                    ${item.name}
                                    Cantidad: ${item.cantidad_intervalo} de ${item.cantidad_total}
                                    ${item.operador_nombre ? `Operador: ${item.operador_nombre}` : 'Sin operador asignado'}
                                    Estándar: ${item.estandar} u/hr
                                    Inicio: ${new Date(item.start_time).toLocaleString()}
                                    Fin: ${new Date(item.end_time).toLocaleString()}
                                `
                            },
                            canMove: false,
                            canResize: false
                        };
                    });
                    setTimelineItems(timelineItems);
                }
            }
        } catch (error) {
            console.error("Error al cargar detalles del programa:", error);
            toast.error("Error al cargar los datos");
        } finally {
            setLoading(false);
        }
    };

    const loadTimelineData = async () => {
        if (!showTimeline || !programId) return;
        
        try {
            setTimelineLoading(true);
            let timelineData;

            if (timelineMode === 'execution') {
                console.log("Cargando datos de ejecución...");
                // Obtener la fecha actual del programa
                const programResponse = await getProgram(programId);
                const programDate = programResponse.program.fecha_inicio;
                
                const response = await supervisorReportAPI.getExecutionTimeline(
                    programId, 
                    { fecha: programDate }
                );
                console.log("Datos de ejecución recibidos:", response);
                timelineData = response;
            } else {
                console.log("Cargando datos de planificación...");
                const response = await getProgram(programId);
                console.log("Datos de planificación recibidos:", response);
                timelineData = response.routes_data || { groups: [], items: [] };
            }

            processTimelineData(timelineData);
        } catch (error) {
            console.error('Error cargando datos del timeline:', error);
            toast.error('Error al cargar la proyección');
        } finally {
            setTimelineLoading(false);
        }
    };

    useEffect(() => {
        if (showTimeline) {
            console.log("Modo timeline cambiado a:", timelineMode);
            loadTimelineData();
        }
    }, [showTimeline, timelineMode, programId]);

    const processTimelineData = (timelineData) => {
        console.log("Datos recibidos en processTimelineData:", timelineData);

        if (timelineMode === 'execution') {
            // Verificar si hay datos de ejecución
            if (HIDE_TEXT || !timelineData.timeline || timelineData.timeline.length === 0) {
                setTimelineGroups([]);
                setTimelineItems([]);
                return;
            }

            // Procesar datos de ejecución
            const groups = [];
            const items = [];
            
            // Agrupar por OT
            const otGroups = {};
            timelineData.timeline.forEach(ejecucion => {
                const otId = `ot_${ejecucion.orden_trabajo.codigo}`;
                
                // Crear grupo de OT si no existe
                if (!otGroups[otId]) {
                    otGroups[otId] = {
                        id: otId,
                        title: ejecucion.orden_trabajo.codigo,
                        stackItems: true,
                        height: 70
                    };
                    groups.push(otGroups[otId]);
                }

                // Crear subgrupo de proceso
                const procesoGroupId = `proc_${ejecucion.tarea_id}`;
                if (!groups.find(g => g.id === procesoGroupId)) {
                    groups.push({
                        id: procesoGroupId,
                        title: ejecucion.proceso.descripcion,
                        parent: otId,
                        height: 50
                    });
                }

                // Ajustar las horas de inicio y fin al horario laboral
                const fecha = moment(ejecucion.tiempo.inicio).format('YYYY-MM-DD');
                const start_time = moment(`${fecha} 08:00`).toDate();
                const end_time = moment(`${fecha} 18:00`).toDate();

                // Crear item de timeline
                items.push({
                    id: `item_${ejecucion.id}`,
                    group: procesoGroupId,
                    title: `${ejecucion.proceso.descripcion} - ${ejecucion.cantidad_producida} de ${ejecucion.cantidad_total} unidades`,
                    start_time: start_time,
                    end_time: end_time,
                    className: 'execution-timeline-item',
                    porcentaje_avance: (ejecucion.cantidad_producida / ejecucion.cantidad_total) * 100,
                    itemProps: {
                        style: {
                            backgroundColor: getEstadoColor(ejecucion.estado),
                            color: 'white',
                            borderRadius: '4px',
                            padding: '2px 6px',
                            fontSize: '12px'
                        },
                        'data-tooltip': `
                            ${ejecucion.proceso.descripcion}
                            Cantidad: ${ejecucion.cantidad_producida} de ${ejecucion.cantidad_total} unidades
                            Avance: ${((ejecucion.cantidad_producida / ejecucion.cantidad_total) * 100).toFixed(1)}%
                            Pendiente: ${ejecucion.cantidad_pendiente} unidades
                            Estado: ${ejecucion.estado}
                            Operador: ${ejecucion.operador?.nombre || 'No asignado'}
                            Inicio real: ${moment(ejecucion.tiempo.inicio).format('HH:mm')}
                            Fin real: ${moment(ejecucion.tiempo.fin).format('HH:mm')}
                        `
                    }
                });
            });

            setTimelineGroups(groups);
            setTimelineItems(items);

        } else {
            // Modo planificación - Mantener el código existente para planificación
            if (!timelineData.groups || !timelineData.items) {
                console.error("Datos de timeline inválidos:", timelineData);
                return;
            }

            // Procesar grupos y subgrupos
            const groups = timelineData.groups.flatMap(ot => {
                const mainGroup = {
                    id: `ot_${ot.id}`,
                    title: ot.orden_trabajo_codigo_ot,
                    stackItems: true,
                    height: 70
                };

                const processGroups = ot.procesos?.map(proceso => ({
                    id: `proc_${proceso.id}`,
                    title: proceso.descripcion,
                    parent: `ot_${ot.id}`,
                    height: 50
                })) || [];

                return [mainGroup, ...processGroups];
            });

            // Procesar items
            const items = timelineData.items.map(item => ({
                id: `item_${item.id}`,
                group: `proc_${item.proceso_id}`,
                title: item.name,
                start_time: moment(item.start_time).toDate(),
                end_time: moment(item.end_time).toDate(),
                itemProps: {
                    style: {
                        backgroundColor: '#FFA726',
                        color: 'white',
                        borderRadius: '4px',
                        padding: '2px 6px',
                        fontSize: '12px'
                    },
                    'data-tooltip': `
                        ${item.name}
                        Inicio: ${moment(item.start_time).format('DD/MM/YYYY HH:mm')}
                        Fin: ${moment(item.end_time).format('DD/MM/YYYY HH:mm')}
                    `
                }
            }));

            setTimelineGroups(groups);
            setTimelineItems(items);
        }
    };

    // Función auxiliar para determinar el color según el estado
    const getEstadoColor = (estado) => {
        switch (estado?.toUpperCase()) {
            case 'COMPLETADO': return '#4CAF50';
            case 'EN_PROCESO': return '#2196F3';
            case 'DETENIDO': return '#f44336';
            default: return '#FFA726';
        }
    };

    useEffect(()=> {  
        fetchData();
    }, [programId])

    useEffect(() => {
        if (!programId) {
            console.error("No se proporcionó un programId");
            return;
        }
        fetchProgramData();
    }, [programId]);
    
    const handleDeleteOrder = async (orderId) => {
        console.log(orderId, programId);
        if(window.confirm("¿Estás seguro que deseas eliminar esta orden de trabajo?")){
            setLoading(true);
            try{
                const result = await deleteOrder(programId, orderId);
                if(result && result.deleted > 0){
                setOtList(otList.filter((ot) => ot.orden_trabajo !== orderId));
                console.log("Orden de trabajo eliminada exitósamente.");
                }else{
                    console.error("Error al eliminar la orden de trabajo:", result);
                    alert("No se pudo eliminar la orden de trabajo");
                }
            }catch(error){
                console.error("Error al eliminar la orden de trabajo:", error);
                alert(error.message ||"Error al eliminar la orden de trabajo");
            }finally{
                setLoading(false);
            }
        }
    };

    const handleOtReorder = (newOtList) => {
        console.log("Nueva lista recibida: ", newOtList);
        setOtList(newOtList);

        const updatedGroups = newOtList.flatMap(ot => {
            const mainGroup = {
                id: `ot_${ot.orden_trabajo}`,
                title: ot.orden_trabajo_codigo_ot,
                height: 50,
                stackItems: true
            };

            const processGroups = ot.procesos.map(proceso => ({
                id: `${mainGroup.id}-${proceso.id}`,
                title: proceso.descripcion,
                parent: mainGroup.id,
                height: 30
            }));

            return [mainGroup, ...processGroups];
        });

        setTimelineGroups(updatedGroups);

        const orderIds = newOtList.map((ot, index) => ({
                id: ot.orden_trabajo,
                priority: index + 1
        })).filter(item => item !== null);

        console.log("Actualizando prioridades: ", orderIds);
        setLoading(true);

        updatePriorities(programId, orderIds)
            .then((response) => {
                console.log("Prioridades actualizadas:", response);

                if (response.routes_data?.items) {
                    const serverItems = response.routes_data.items.map(item => ({
                        id: item.id,
                        group: `${item.ot_id}-${item.proceso_id}`,
                        title: `${item.name} (Restantes: ${item.unidades_restantes})`,
                        start_time: new Date(item.start_time + 'Z'),  // Añadimos Z para asegurar que se interprete en UTC
                        end_time: new Date(item.end_time + 'Z'),      // Añadimos Z para asegurar que se interprete en UTC
                        itemProps: {
                            style: {
                                backgroundColor: '#4CAF50',
                                color: 'white',
                                borderRadius: '4px',
                                padding: '2px 6px',
                                opacity: 1 - (item.unidades_restantes / item.cantidad_total)
                            }
                        }
                    }));
                    setTimelineItems(serverItems);
                }
            })
            .catch((error) => {
                console.error("Error al actualizar prioridades", error);
                alert("Error al actualizar el orden de las OTs");
            })
            .finally(() => {
                setLoading(false);
            });
    };

    const hayProcesosConEstandarCero =() => {
        if (!otList || otList.length === 0) return false;

        return otList.some(ot => 
            ot.procesos && ot.procesos.some(proceso => 
                !proceso.estandar || parseFloat( proceso.estandar) === 0
            )
        );
    };

    const getProcesosConEstandarCero = () => {
        const procesosConEstandarCero = [];

        otList?.forEach( ot => {
            ot.procesos?.forEach(proceso => {
                if (!proceso.estandar || parseFloat(proceso.estandar) === 0) {
                    procesosConEstandarCero.push({
                        ot_codigo: ot.orden_trabajo_codigo_ot,
                        proceso_descripcion: proceso.descripcion,
                        id: proceso.id
                    });
                }
            });
        });

        return procesosConEstandarCero;
    };

    const renderOt = (ot) => {
        const hasPendingChanges = Object.keys(pendingChanges).some(key => 
            key.startsWith(`${ot.orden_trabajo}-`)
        );

        return (
            <Card 
                key={ot.orden_trabajo}
                className={`ot-card mb-3 ${expandedOTs[ot.orden_trabajo] ? 'expanded' : ''}`}
            >
                <Card.Header className="d-flex justify-content-between align-items-center">
                    <div className="d-flex align-items-center">
                        <div className="ot-number me-3">
                            #{ot.orden_trabajo_codigo_ot}
                        </div>
                        <div className="ot-info">
                            <h6 className="mb-0">{ot.orden_trabajo_descripcion_producto_ot}</h6>
                            <small className="text-muted">
                                <FaCalendarAlt className="me-1" />
                                {ot.orden_trabajo_fecha_termino}
                            </small>
                        </div>
                    </div>
                    <div className="d-flex align-items-center">
                        {hasPendingChanges && (
                            <Button
                                variant="success"
                                size="sm"
                                onClick={handleSaveChanges}
                                disabled={savingChanges}
                                className="me-2"
                            >
                                <FaSave className="me-1" />
                                {savingChanges ? "Guardando..." : "Guardar"}
                            </Button>
                        )}
                        <Button
                            variant={expandedOTs[ot.orden_trabajo] ? "primary" : "outline-primary"}
                            size="sm"
                            onClick={() => handleToggleExpand(ot.orden_trabajo)}
                        >
                            <FaChevronDown 
                                className={`transition-transform ${
                                    expandedOTs[ot.orden_trabajo] ? 'rotate-180' : ''
                                }`}
                            />
                        </Button>
                    </div>
                </Card.Header>

                <Collapse in={expandedOTs[ot.orden_trabajo]}>
                    <Card.Body className="p-0">
                        <div className="table-responsive">
                            <Table className="process-table mb-0">
                                <thead>
                                    <tr>
                                        <th>#</th>
                                        <th>Proceso</th>
                                        <th>Máquina</th>
                                        <th>Operador</th>
                                        <th>Cantidad</th>
                                        <th>Estandar</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {ot.procesos?.map((item_ruta) => (
                                        <tr 
                                            key={item_ruta.id}
                                            className={!item_ruta.estandar || parseFloat(item_ruta.estandar) === 0 ? "table-danger" : ""}
                                        >
                                            <td>{item_ruta.item}</td>
                                            <td>
                                                <input 
                                                type="text" 
                                                className="form-control" 
                                                value={`${item_ruta.codigo_proceso} - ${item_ruta.descripcion}`}
                                                disabled
                                                />
                                            </td>
                                            <td>
                                                <select 
                                                className="form-control" 
                                                value={item_ruta.maquina_id || ''}
                                                onChange={(e) => handleProcessChange(
                                                    ot.orden_trabajo,
                                                    item_ruta.id,
                                                    "maquina_id",
                                                    e.target.value
                                                    
                                                )}
                                                onFocus={() => {
                                                    console.log("[Frontend] onFocus del selector de máquinas");
                                                    console.log("[Frontend] item_ruta:", item_ruta);
                                                    console.log("[Frontend] ¿Tiene código de proceso?", !!item_ruta.codigo_proceso);

                                                    //Cargar máquinas cuando el select recibe el foco
                                                    if(!maquinasPorProceso[item_ruta.id]){
                                                        cargarMaquinasPorProceso(item_ruta);
                                                    }
                                                }}
                                                >
                                                    <option value="">Seleccione una máquina</option>
                                                    {(maquinasPorProceso[item_ruta.id] || maquinas).map(maquina => (
                                                        <option
                                                            value={maquina.id}
                                                            key={maquina.id}
                                                        >
                                                            {maquina.codigo_maquina} - {maquina.descripcion}
                                                        </option>
                                                    ))}
                                                </select>
                                            </td>
                                            <td>
                                                <input 
                                                    type="text" 
                                                    className="form-control"
                                                    value={item_ruta.operador_nombre || 'Sin asignar'}    
                                                    disabled
                                                    title="La asignación de operadores se realiza desde el Reporte."
                                                />/
                                            </td>
                                            <td>
                                                <input 
                                                type="number" 
                                                className="form-control"
                                                value={item_ruta.cantidad} 
                                                onChange={(e) => handleProcessChange(
                                                    ot.orden_trabajo,
                                                    item_ruta.id,
                                                    'cantidad',
                                                    parseInt(e.target.value, 10)
                                                )}
                                                />
                                            </td>
                                            <td>
                                                <Form.Control 
                                                type="number" 
                                                    value={item_ruta.estandar || 0}
                                                    onChange={(e) => {
                                                        const newValue = parseFloat(e.target.value);
                                                        handleProcessChange(
                                                            ot.orden_trabajo,
                                                            item_ruta.id,
                                                            'estandar',
                                                            parseFloat(e.target.value)
                                                        );
                                                    }}
                                                    min="0"
                                                    step="1"
                                                    className={!item_ruta.estandar || parseFloat(item_ruta.estandar) === 0 ? "border-danger" : ""}
                                                />
                                                {(!item_ruta.estandar || parseFloat(item_ruta.estandar) === 0) && 
                                                    <small className="text-danger">Ingrese un estándar mayor a 0</small>
                                                }
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </Table>
                        </div>
                    </Card.Body>
                </Collapse>
            </Card>
        )
    };
        

    if (loading) return <LoadingSpinner message="Cargando detalles del programa..."/>;
    if (!programData) return <p>No se encontró el programa.</p>;

    const handleOrdenesAgregadas = (data) => {
        // Recargar los datos del programa
        fetchProgramData();
    };

    const verificarReajustes = async () => {
        try {
            console.log('Verificando reajustes para programa:', programId);
            const response = await verificarReajustesPrograma(programId);
            console.log('Respuesta completa:', JSON.stringify(response, null, 2));
            
            if (response.requiere_ajustes) {
                // Veamos la estructura de cada ajuste
                response.ajustes_sugeridos.forEach((ajuste, index) => {
                    console.log(`Ajuste ${index}:`, {
                        key: `${ajuste.orden_trabajo}-${ajuste.proceso.id}`,
                        orden_trabajo: ajuste.orden_trabajo,
                        proceso_id: ajuste.proceso.id,
                        fecha_propuesta: ajuste.fecha_propuesta
                    });
                });

                // Intentemos el agrupamiento de otra manera
                const ajustesUnicos = Array.from(new Set(
                    response.ajustes_sugeridos.map(ajuste => 
                        `${ajuste.orden_trabajo}-${ajuste.proceso.id}`
                    )
                )).map(key => {
                    const [ot, procesoId] = key.split('-');
                    const ajustesDeEstePar = response.ajustes_sugeridos.filter(
                        ajuste => ajuste.orden_trabajo === ot && ajuste.proceso.id === parseInt(procesoId)
                    );
                    // Tomar el último ajuste (más reciente)
                    return ajustesDeEstePar[ajustesDeEstePar.length - 1];
                });

                console.log('Ajustes únicos:', ajustesUnicos);

                setAjustes({
                    ...response,
                    ajustes_sugeridos: ajustesUnicos
                });
                setShowReajustesModal(true);
            } else {
                toast.success(response.mensaje);
            }
        } catch (error) {
            console.error('Error completo:', error);
            toast.error("Error al verificar reajustes");
        }
    };

    const aplicarReajustes = async () => {
        try {
            if (!ajustes || !ajustes.ajustes_sugeridos) {
                console.log('Estado de ajustes:', ajustes); // Agregar este log
                toast.error("No hay ajustes para aplicar");
                return;
            }
            
            console.log('Enviando ajustes:', ajustes.ajustes_sugeridos); // Agregar este log
            await aplicarReajustesPrograma(programId, ajustes.ajustes_sugeridos);
            setShowReajustesModal(false);
            toast.success("Ajustes aplicados correctamente");
            // Recargar datos del programa
            fetchProgramData();
        } catch (error) {
            console.log('Error completo:', error.response?.data); // Agregar este log
            toast.error("Error al aplicar reajustes");
            console.error(error);
        }
    };

    return (
        <div className="page-container">
            <CompNavbar />
            
            <div className="content-wrapper">
                <div className="container">
                    <div className="program-header">
                        <div className="d-flex justify-content-between align-items-center mb-4">
                            <div>
                                <Link to="/programs" className="btn btn-outline-primary">
                                    <FaArrowLeft className="me-2" />
                                    Volver a Programas
                                </Link>
                            </div>
                            <div className="text-center">
                                <h1 className="h3 mb-2">{programData?.nombre}</h1>
                                <div className="program-dates">
                                    <Badge bg="info" className="me-3">
                                        <FaCalendarAlt className="me-2" />
                                        Inicio: {programData?.fecha_inicio}
                                    </Badge>
                                    <Badge bg="info">
                                        <FaFlag className="me-2" />
                                        Término: {programData?.fecha_fin}
                                    </Badge>
                                </div>
                            </div>
                            <div className="action-buttons">
                                <Button 
                                    variant="outline-primary" 
                                    className="me-2"
                                    onClick={() => setShowAgregarOrden(true)}
                                >
                                    <FaPlus className="me-2" />
                                    Agregar Órdenes
                                </Button>
                                <Button 
                                    variant="outline-success" 
                                    className="me-2"
                                    onClick={() => generateProgramPDF(programId)}
                                >
                                    <FaFilePdf className="me-2" />
                                    PDF
                                </Button>
                                <Button 
                                    variant="outline-info"
                                    onClick={() => navigate(`/programs/${programId}/supervisor-report`)}
                                >
                                    <FaClipboardList className="me-2" />
                                    Reporte
                                </Button>
                                {/*<Button 
                                    variant="warning" 
                                    onClick={verificarReajustes}
                                    className="ms-2"
                                >
                                    Verificar Disponibilidad
                                </Button>*/}
                            </div>
                        </div>
                    </div>
                    <ProgramMonitoring programId={programId}/>

                    <section
                        className="container-section container-fluid border py-2 mb-2"
                        style={{ borderRadius: "5px" }}
                    >
                        <h2>Órdenes de Trabajo:</h2>
                        {hayProcesosConEstandarCero() && (
                            <AlertMessage
                                type="warning"
                                icon={<FaExclamationTriangle size={20} />}
                                message="Hay procesos con estándar en 0. Por favor, ingrese un valor válido para poder proyectar en la carta."
                            />
                        )}

                        {showPendingChangesAlert && Object.keys(pendingChanges).length > 0 && (
                            <div className="alert alert-info" role="alert">
                                <i className="bi bi-info-circle-fill me-2"></i>
                                Hay cambios pendientes por guardar. Por favor, guarde los cambios antes de salir de la página.
                            </div>
                        )}
                        
                        <div>
                            {otList && otList.length > 0 ? (
                                <ReactSortable
                                    list={otList}
                                    setList={setOtList}
                                    onEnd={(evt) => {
                                        const newOtList = [...otList];
                                        const movedItem = newOtList.splice(evt.oldIndex, 1)[0];
                                        newOtList.splice(evt.newIndex, 0, movedItem);
                                        handleOtReorder(newOtList);
                                    }}
                                >
                                    {otList.map((ot) => renderOt(ot))}
                                </ReactSortable>
                            ) : (
                                <p>No hay OTs asignadas a este programa.</p>
                            )}
                        </div>
                        <div className="d-flex align-items-center">
                            <Button 
                                variant="success" 
                                onClick={toggleTimeline} 
                                className="mt-3 me-2" 
                                disabled={timelineLoading || hayProcesosConEstandarCero()}
                                title={hayProcesosConEstandarCero() ? "No se puede proyectar: Hay procesos con estándar en 0" : ""}
                            >
                                {timelineLoading ? (
                                    <span>
                                        <LoadingSpinner message="" size="small"/> Cargando Proyección
                                    </span>
                                ) : showTimeline ? "Ocultar Proyección" : "Mostrar Proyección"}
                            </Button>
                            {showTimeline && (
                                <div className="btn-group mt-3">
                                    <Button
                                        variant={timelineMode === 'planning' ? 'primary' : 'outline-primary'}
                                        onClick={() => setTimelineMode('planning')}
                                    >
                                        Planificación
                                    </Button>
                                    <Button
                                        variant={timelineMode === 'execution' ? 'primary' : 'outline-primary'}
                                        onClick={() => setTimelineMode('execution')}
                                    >
                                        Ejecución
                                    </Button>
                                </div>
                            )}
                        </div>
                    </section>

                    {showTimeline && (
                        <div className="timeline-container mt-4 mb-4" style={{ width: "100%" }}>
                            <Timeline
                                groups={timelineGroups}
                                items={timelineItems}
                                defaultTimeStart={moment().startOf('day').toDate()}
                                defaultTimeEnd={moment().add(14, 'days').toDate()}
                                lineHeight={50}
                                sidebarWidth={200}
                                canMove={false}
                                canResize={false}
                                stackItems
                                timeSteps={{
                                    second: 1,
                                    minute: 30,
                                    hour: 1,
                                    day: 1,
                                    month: 1,
                                    year: 1
                                }}
                                traditionalZoom
                                itemRenderer={({ item, itemContext, getItemProps }) => (
                                    <div
                                        {...getItemProps({
                                            className: `${timelineMode === 'execution' ? 'execution-timeline-item' : ''}`,
                                            style: {
                                                ...item.itemProps.style,
                                                borderRadius: '4px',
                                                padding: '2px 6px'
                                            }
                                        })}
                                        title={item.itemProps['data-tooltip']}
                                    >
                                        <div className="timeline-item-content">
                                            <div className="item-title">{item.title}</div>
                                            {timelineMode === 'execution' && (
                                                <div className="progress">
                                                    <div 
                                                        className="progress-bar" 
                                                        style={{ 
                                                            width: `${item.porcentaje_avance}%`
                                                        }}
                                                    />
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                )}
                            />
                        </div>
                    )}
                </div>
            </div>
            <Footer />
            <AgregarOrdenModal 
                show={showAgregarOrden}
                onHide={() => setShowAgregarOrden(false)}
                programId={programId}
                onOrdenesAgregadas={handleOrdenesAgregadas}
            />
            <Modal show={showReajustesModal} onHide={() => setShowReajustesModal(false)} size="lg">
                <Modal.Header closeButton>
                    <Modal.Title>Ajustes Necesarios</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    {ajustes && (
                        <>
                            <Alert variant="info">
                                <strong>Fecha actual de fin:</strong> {ajustes.fecha_actual}<br/>
                                <strong>Nueva fecha de fin propuesta:</strong> {ajustes.nueva_fecha_fin}
                            </Alert>
                            
                            <div className="mb-3">
                                <strong>Total de ajustes necesarios: </strong> 
                                {ajustes.ajustes_sugeridos.length}
                            </div>
                            
                            {ajustes.ajustes_sugeridos.map((ajuste, index) => (
                                <Card key={`${ajuste.orden_trabajo}-${ajuste.proceso.id}`} className="mb-3">
                                    <Card.Header className="d-flex justify-content-between align-items-center">
                                        <span className="fw-bold">OT: {ajuste.orden_trabajo}</span>
                                        <Badge bg={index === 0 ? "warning" : "info"}>
                                            {index === 0 ? "Primer ajuste necesario" : `Ajuste #${index + 1}`}
                                        </Badge>
                                    </Card.Header>
                                    <Card.Body>
                                        <div className="row">
                                            <div className="col-md-6">
                                                <h6>Proceso</h6>
                                                <p>{ajuste.proceso.descripcion}</p>
                                                <h6>Máquina</h6>
                                                <p>{ajuste.maquina.codigo} - {ajuste.maquina.descripcion}</p>
                                            </div>
                                            <div className="col-md-6">
                                                <h6>Fechas</h6>
                                                <div className="text-danger">
                                                    <small>Original: {new Date(ajuste.fecha_original).toLocaleString()}</small>
                                                </div>
                                                <div className="text-success">
                                                    <small>Propuesta: {new Date(ajuste.fecha_propuesta).toLocaleString()}</small>
                                                </div>
                                            </div>
                                        </div>
                                    </Card.Body>
                                </Card>
                            ))}
                        </>
                    )}
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="secondary" onClick={() => setShowReajustesModal(false)}>
                        Cancelar
                    </Button>
                    <Button 
                        variant="primary" 
                        onClick={aplicarReajustes}
                        disabled={!ajustes || ajustes.ajustes_sugeridos.length === 0}
                    >
                        Aplicar Ajustes
                    </Button>
                </Modal.Footer>
            </Modal>
        </div>
    );
}
