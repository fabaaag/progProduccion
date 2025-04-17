import { useState, useEffect } from 'react';
import { Modal, Table, Spinner, Tooltip, OverlayTrigger } from 'react-bootstrap';
import { FaCog, FaExclamationCircle, FaTools, FaEllipsisH } from 'react-icons/fa';
import { motion } from 'framer-motion';
import { getOperatorMachines } from '../../api/machines.api';
import './css/OperatorMachinesModal.css';

export function OperatorMachinesModal({ show, handleClose, operator }) {
    const [machinesDetails, setMachinesDetails] = useState([]);
    const [loading, setLoading] = useState(false);
    const [expandedTypes, setExpandedTypes] = useState(new Set());

    useEffect(() => {
        if (show && operator?.id) {
            loadMachinesDetails();
        }
    }, [show, operator]);

    const loadMachinesDetails = async () => {
        setLoading(true);
        try {
            const data = await getOperatorMachines(operator.id);
            setMachinesDetails(data);
        } catch (error) {
            console.error('Error al cargar detalles de máquinas:', error);
        } finally {
            setLoading(false);
        }
    };

    const toggleExpandTypes = (machineId) => {
        setExpandedTypes(prev => {
            const newSet = new Set(prev);
            if (newSet.has(machineId)) {
                newSet.delete(machineId);
            } else {
                newSet.add(machineId);
            }
            return newSet;
        });
    };

    const renderMachineTypes = (maquina) => {
        if (!maquina.tipos_maquina || maquina.tipos_maquina.length === 0) {
            return <span className="no-type">Sin tipos asignados</span>;
        }

        const isExpanded = expandedTypes.has(maquina.id);
        const tipos = maquina.tipos_maquina;

        if (tipos.length === 1) {
            return (
                <span className="machine-type">
                    {tipos[0].descripcion}
                </span>
            );
        }

        return (
            <div className="types-container">
                <span className="machine-type">
                    {tipos[0].descripcion}
                </span>
                {!isExpanded && tipos.length > 1 && (
                    <OverlayTrigger
                        placement="top"
                        overlay={
                            <Tooltip>
                                {tipos.slice(1).map(tipo => tipo.descripcion).join(', ')}
                            </Tooltip>
                        }
                    >
                        <button 
                            className="expand-types-btn"
                            onClick={() => toggleExpandTypes(maquina.id)}
                        >
                            <FaEllipsisH /> +{tipos.length - 1}
                        </button>
                    </OverlayTrigger>
                )}
                {isExpanded && (
                    <>
                        {tipos.slice(1).map((tipo, idx) => (
                            <span key={idx} className="machine-type">
                                {tipo.descripcion}
                            </span>
                        ))}
                        <button 
                            className="collapse-types-btn"
                            onClick={() => toggleExpandTypes(maquina.id)}
                        >
                            Ver menos
                        </button>
                    </>
                )}
            </div>
        );
    };

    return (
        <Modal show={show} onHide={handleClose} size='lg' className="operator-machines-modal">
            <Modal.Header closeButton>
                <Modal.Title className="modal-title">
                    <FaTools className="title-icon" />
                    Máquinas asignadas a {operator?.nombre}
                </Modal.Title>
            </Modal.Header>
            <Modal.Body>
                {loading ? (
                    <motion.div 
                        className="loading-container"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                    >
                        <Spinner animation="border" variant="primary" />
                        <p>Cargando información de máquinas...</p>
                    </motion.div>
                ) : machinesDetails.length > 0 ? (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ duration: 0.3 }}
                    >
                        <div className="table-responsive">
                            <Table hover className="machines-table">
                                <thead>
                                    <tr>
                                        <th>
                                            <FaCog className="header-icon" />
                                            Código
                                        </th>
                                        <th>Descripción</th>
                                        <th>Tipos</th>
                                        <th>Estado</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {machinesDetails.map((maquina, index) => (
                                        <motion.tr 
                                            key={maquina.id}
                                            initial={{ opacity: 0, y: 20 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            transition={{ delay: index * 0.1 }}
                                            className="machine-row"
                                        >
                                            <td className="code-cell">
                                                {maquina.codigo_maquina}
                                            </td>
                                            <td className="desc-cell">
                                                {maquina.descripcion}
                                            </td>
                                            <td className="types-cell">
                                                {renderMachineTypes(maquina)}
                                            </td>
                                            <td className="status-cell">
                                                <span className={`status-badge ${
                                                    maquina.estado_operatividad === 'Operativa' ? 'operational' : 'non-operational'
                                                }`}>
                                                    {maquina.estado_operatividad}
                                                </span>
                                            </td>
                                        </motion.tr>
                                    ))}
                                </tbody>
                            </Table>
                        </div>
                    </motion.div>
                ) : (
                    <motion.div 
                        className="no-machines-message"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                    >
                        <FaExclamationCircle className="warning-icon" />
                        <p>Este operador no tiene máquinas asignadas</p>
                    </motion.div>
                )}
            </Modal.Body>
        </Modal>
    );
}