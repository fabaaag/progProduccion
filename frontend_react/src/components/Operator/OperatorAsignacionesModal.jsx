import { useState, useEffect } from 'react';
import { Modal, Table, Alert, Spinner } from 'react-bootstrap';
import { getOperatorTasks } from '../../api/operator.api';
import { toast } from 'react-hot-toast';
import { FaUserClock, FaCalendarAlt, FaCog, FaIndustry, FaClipboardList } from 'react-icons/fa';
import { motion } from 'framer-motion';
import './css/OperatorAsignacionesModal.css';

export function OperatorAsignacionesModal({ show, handleClose, operator }) {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [tareas, setTareas] = useState([]);

    

    const loadAsignaciones = async (operator) => {
        if(!operator) return;

        setLoading(true);
        setError(null);

        try {
            console.log('Cargad')
            const taskData = await getOperatorTasks(operator);
            console.log("Datos de tareas recibidos:", taskData)
            setTareas(taskData || []);
        } catch (error) {
            console.error('Error al cargar asignaciones', error);
            toast.error('Error al cargar las asignaciones del operador');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (show && operator){
            loadAsignaciones(operator);
        }
    }, [show, operator]);

    const formatDate = (dateString) => {
        if(!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleDateString('es-CL');
    };

    return (
        <Modal show={show} onHide={handleClose} size="xl" className="asignaciones-modal">
            <Modal.Header closeButton>
                <Modal.Title className="modal-title">
                    <FaUserClock className="title-icon" />
                    Asignaciones de {operator?.nombre}
                </Modal.Title>
            </Modal.Header>
            <Modal.Body>
                {error && (
                    <Alert variant="danger" className="error-alert">
                        <FaExclamationCircle className="alert-icon" /> {error}
                    </Alert>
                )}

                {loading ? (
                    <motion.div 
                        className="loading-container"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                    >
                        <Spinner animation="border" variant="primary" />
                        <p>Cargando asignaciones...</p>
                    </motion.div>
                ) : tareas.length === 0 ? (
                    <motion.div 
                        className="no-data-container"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                    >
                        <FaClipboardList className="no-data-icon" />
                        <p>Este operador no tiene asignaciones actualmente.</p>
                    </motion.div>
                ) : (
                    <motion.div 
                        className="table-container"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                    >
                        <Table hover responsive className="asignaciones-table">
                            <thead>
                                <tr>
                                    <th>
                                        <FaClipboardList className="header-icon" />
                                        Programa
                                    </th>
                                    <th>
                                        <FaIndustry className="header-icon" />
                                        Orden de Trabajo
                                    </th>
                                    <th>
                                        <FaCog className="header-icon" />
                                        Proceso
                                    </th>
                                    <th>
                                        <FaCog className="header-icon" />
                                        Máquina
                                    </th>
                                    <th colSpan="2" className="dates-header">
                                        <FaCalendarAlt className="header-icon" />
                                        Fechas
                                    </th>
                                    <th colSpan="3" className="production-header">
                                        Producción
                                    </th>
                                </tr>
                                <tr className="subheader">
                                    <th colSpan="4"></th>
                                    <th>Inicio</th>
                                    <th>Fin</th>
                                    <th>Total</th>
                                    <th>Est. Hora</th>
                                    <th>Prod. Diaria</th>
                                </tr>
                            </thead>
                            <tbody>
                                {tareas.map((tarea, index) => (
                                    <motion.tr 
                                        key={index}
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ delay: index * 0.1 }}
                                        className="data-row"
                                    >
                                        <td className="programa-cell">
                                            {tarea.programa.nombre}
                                        </td>
                                        <td className="orden-cell">
                                            <span className="codigo">{tarea.orden_trabajo.codigo}</span>
                                            <span className="descripcion">{tarea.orden_trabajo.descripcion}</span>
                                        </td>
                                        <td className="proceso-cell">
                                            <span className="codigo">{tarea.proceso.codigo}</span>
                                            <span className="descripcion">{tarea.proceso.descripcion}</span>
                                        </td>
                                        <td className="maquina-cell">
                                            <span className="codigo">{tarea.maquina.codigo}</span>
                                            <span className="descripcion">{tarea.maquina.descripcion}</span>
                                        </td>
                                        <td className="fecha-cell">{formatDate(tarea.fechas.inicio)}</td>
                                        <td className="fecha-cell">{formatDate(tarea.fechas.fin)}</td>
                                        <td className="cantidad-cell">{tarea.produccion.cantidad_total}</td>
                                        <td className="estandar-cell">{tarea.produccion.estandar_diario}</td>
                                        <td className="produccion-cell">{tarea.produccion.cantidad_diaria}</td>
                                    </motion.tr>
                                ))}
                            </tbody>
                        </Table>
                    </motion.div>
                )}
            </Modal.Body>
        </Modal>
    );
}

