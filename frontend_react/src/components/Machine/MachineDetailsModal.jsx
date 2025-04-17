import React, { useState, useEffect } from 'react';
import { Modal, Nav, Tab, Row, Col, Badge, Form, Button } from 'react-bootstrap';
import { toast } from 'react-hot-toast';
import { getMachineTypes, updateMachineType } from '../../api/machines.api';
import { FaCog, FaTools, FaClipboardList, FaInfoCircle, FaEdit, FaHistory, FaWrench } from 'react-icons/fa';
import { motion } from 'framer-motion';
import './css/MachineDetailsModal.css';

export function MachineDetailsModal({ show, onHide, machine, onUpdate }) {
    const [activeTab, setActiveTab] = useState('info');
    const [machineTypes, setMachineTypes] = useState([]);
    const [selectedTypes, setSelectedTypes] = useState([]);
    const [isEditing, setIsEditing] = useState(false);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (show) {
            loadMachineTypes();
            setSelectedTypes(machine?.estado?.tipos_maquina?.map(t => t.id) || []);
        }
    }, [show, machine]);

    const loadMachineTypes = async () => {
        try {
            const types = await getMachineTypes();
            setMachineTypes(types);
        } catch (error) {
            console.error('Error al cargar tipos de máquina:', error);
            toast.error('Error al cargar tipos de máquina');
        }
    };

    const handleUpdateType = async () => {
        try {
            setLoading(true);
            await updateMachineType(machine.id, selectedTypes); // Actualizado para enviar array
            toast.success('Tipos de máquina actualizados correctamente');
            setIsEditing(false);
        } catch (error) {
            console.error('Error al actualizar tipos de máquina:', error);
            toast.error('Error al actualizar tipos de máquina');
        } finally {
            setLoading(false);
        }
    };

    const renderMachineTypeEdit = () => (
        <div className="mb-3">
            <Form.Group>
                <Form.Label>Tipos de Máquina</Form.Label>
                <Form.Select
                    multiple
                    value={selectedTypes}
                    onChange={(e) => {
                        const selected = Array.from(e.target.selectedOptions, option => option.value);
                        setSelectedTypes(selected);
                    }}
                    disabled={loading}
                >
                    {machineTypes.map(type => (
                        <option key={type.id} value={type.id}>
                            {type.codigo} - {type.descripcion}
                        </option>
                    ))}
                </Form.Select>
                <Form.Text className="text-muted">
                    Mantenga presionado Ctrl para seleccionar múltiples tipos
                </Form.Text>
            </Form.Group>
            <div className="mt-2">
                <Button
                    variant="primary"
                    onClick={handleUpdateType}
                    disabled={loading || selectedTypes.length === 0}
                    className="me-2"
                >
                    {loading ? 'Guardando...' : 'Guardar'}
                </Button>
                <Button
                    variant="secondary"
                    onClick={() => {
                        setIsEditing(false);
                        setSelectedTypes(machine?.estado?.tipos_maquina?.map(t => t.id) || []);
                    }}
                    disabled={loading}
                >
                    Cancelar
                </Button>
            </div>
        </div>
    );

    const renderMachineTypeDisplay = () => (
        <div className="types-container">
            {machine?.estado?.tipos_maquina?.map(tipo => (
                <Badge 
                    key={tipo.id} 
                    bg="info" 
                    className="machine-type-badge"
                >
                    <span className="type-code">{tipo.codigo}</span>
                    <span className="type-description">{tipo.descripcion}</span>
                </Badge>
            )) || 'Sin tipos asignados'}
        </div>
    );

    const renderProcessesTab = () => {
        const procesos = machine?.procesos_asociados || [];
        return (
            <div className="processes-section">
                <h6>Procesos Compatibles</h6>
                {procesos.length > 0 ? (
                    <div className="process-list">
                        {procesos.map(proceso => (
                            <Badge 
                                key={proceso.id} 
                                bg="info" 
                                className="process-badge"
                            >
                                <span className="process-code">{proceso.codigo_proceso}</span>
                                <span className="process-description">{proceso.descripcion}</span>
                            </Badge>
                        ))}
                    </div>
                ) : (
                    <p className="text-muted">No hay procesos compatibles con esta máquina</p>
                )}
            </div>
        );
    };

    const renderOrdersTab = () => {
        const ordenes = machine?.ordenes_trabajo || [];
        
        const getSituacionBadgeColor = (situacionCodigo) => {
            const colors = {
                'P': 'warning',    // Pendiente
                'S': 'info',       // Sin imprimir
                'T': 'success',    // Terminada
                'A': 'danger'      // Anulada
            };
            return colors[situacionCodigo] || 'secondary';
        };

        return (
            <div className="orders-section">
                <h6>Órdenes de Trabajo Asociadas</h6>
                {ordenes.length > 0 ? (
                    <div className="orders-list">
                        {ordenes.map(orden => (
                            <div key={orden.codigo_ot} className="order-card">
                                <div className="order-header">
                                    <h6>OT #{orden.codigo_ot}</h6>
                                    <Badge bg={getSituacionBadgeColor(orden.situacion_codigo)}>
                                        {orden.situacion}
                                    </Badge>
                                </div>
                                <p className="order-description">{orden.descripcion}</p>
                            </div>
                        ))}
                    </div>
                ) : (
                    <p className="text-muted">No hay órdenes de trabajo asociadas</p>
                )}
            </div>
        );
    };

    if (!machine) return null;

    const getStatusBadge = (estado) => {
        if (!estado?.estado) return <Badge bg="secondary">Sin Estado</Badge>;

        const badgeColors = {
            'OP': 'success',
            'MN': 'warning',
            'IN': 'danger'
        };

        return (
            <Badge bg={badgeColors[estado.estado] || 'secondary'}>
                {estado.descripcion || estado.estado}
            </Badge>
        );
    };

    const getStatusIconClass = (estado) => {
        if (!estado?.estado) return '';
        
        const statusClasses = {
            'OP': 'operativa',
            'MN': 'mantencion',
            'IN': 'inoperativa'
        };

        return statusClasses[estado.estado] || '';
    };

    return (
        <Modal show={show} onHide={onHide} size="lg" className="machine-details-modal">
            <Modal.Header closeButton className="border-0">
                <Modal.Title className="d-flex align-items-center gap-2">
                    <div className="machine-title">
                        <div className="d-flex align-items-center gap-2">
                            <FaCog className={`status-icon ${getStatusIconClass(machine?.estado?.estado_operatividad)}`} />
                            <div>
                                <h5 className="mb-0">{machine?.codigo_maquina}</h5>
                                <small className="text-muted">{machine?.descripcion}</small>
                            </div>
                        </div>
                        {machine?.estado?.disponible && (
                            <Badge bg="success" className="availability-badge">Disponible</Badge>
                        )}
                    </div>
                </Modal.Title>
            </Modal.Header>

            <Modal.Body className="p-0">
                <Tab.Container activeKey={activeTab} onSelect={(k) => setActiveTab(k)}>
                    <Row className="g-0">
                        <Col sm={3} className="border-end">
                            <Nav variant="pills" className="flex-column nav-custom">
                                <Nav.Item>
                                    <Nav.Link eventKey="info" className="d-flex align-items-center gap-2">
                                        <FaInfoCircle /> Información
                                    </Nav.Link>
                                </Nav.Item>
                                <Nav.Item>
                                    <Nav.Link eventKey="estado" className="d-flex align-items-center gap-2">
                                        <FaTools /> Estado y Tipos
                                    </Nav.Link>
                                </Nav.Item>
                                <Nav.Item>
                                    <Nav.Link eventKey="procesos" className="d-flex align-items-center gap-2">
                                        <FaWrench /> Procesos
                                    </Nav.Link>
                                </Nav.Item>
                                <Nav.Item>
                                    <Nav.Link eventKey="ordenes" className="d-flex align-items-center gap-2">
                                        <FaClipboardList /> Órdenes
                                    </Nav.Link>
                                </Nav.Item>
                                <Nav.Item>
                                    <Nav.Link eventKey="mantenimiento" className="d-flex align-items-center gap-2">
                                        <FaHistory /> Mantenimiento
                                    </Nav.Link>
                                </Nav.Item>
                            </Nav>
                        </Col>

                        <Col sm={9}>
                            <motion.div 
                                className="tab-content-wrapper p-4"
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                transition={{ duration: 0.3 }}
                            >
                                <Tab.Content>
                                    <Tab.Pane eventKey="info">
                                        <div className="info-grid">
                                            <InfoCard 
                                                label="Código"
                                                value={machine?.codigo_maquina || 'N/A'}
                                            />
                                            <InfoCard 
                                                label="Sigla"
                                                value={machine?.sigla || 'N/A'}
                                            />
                                            <InfoCard 
                                                label="Carga"
                                                value={machine?.carga ? `${machine.carga} kg` : 'N/A'}
                                            />
                                            <InfoCard 
                                                label="Golpes"
                                                value={machine?.golpes || '0'}
                                            />
                                            <InfoCard 
                                                label="Empresa"
                                                value={machine?.empresa?.nombre || 'No asignada'}
                                                fullWidth
                                            />
                                            <InfoCard 
                                                label="Estado"
                                                value={machine?.estado?.estado_operatividad?.descripcion || 'Sin estado'}
                                                badge={getStatusBadge(machine?.estado?.estado_operatividad)}
                                            />
                                            <InfoCard 
                                                label="Capacidad Máxima"
                                                value={machine?.estado?.capacidad_maxima || '0'}
                                            />
                                        </div>
                                    </Tab.Pane>

                                    <Tab.Pane eventKey="estado">
                                        <div className="status-section">
                                            <div className="status-header">
                                                <h6>Estado Actual</h6>
                                                {getStatusBadge(machine?.estado)}
                                            </div>
                                            
                                            <div className="types-section">
                                                <div className="d-flex justify-content-between align-items-center mb-3">
                                                    <h6 className="mb-0">Tipos de Máquina</h6>
                                                    {!isEditing && (
                                                        <Button 
                                                            variant="outline-primary" 
                                                            size="sm"
                                                            onClick={() => setIsEditing(true)}
                                                        >
                                                            <FaEdit /> Editar
                                                        </Button>
                                                    )}
                                                </div>
                                                {isEditing ? renderMachineTypeEdit() : renderMachineTypeDisplay()}
                                            </div>

                                            <div className="observation-section">
                                                <h6>Observaciones</h6>
                                                <p className="observation-text">
                                                    {machine?.estado?.observaciones || 'Sin observaciones'}
                                                </p>
                                            </div>
                                        </div>
                                    </Tab.Pane>

                                    <Tab.Pane eventKey="procesos">
                                        {renderProcessesTab()}
                                    </Tab.Pane>

                                    <Tab.Pane eventKey="ordenes">
                                        {renderOrdersTab()}
                                    </Tab.Pane>

                                    <Tab.Pane eventKey="mantenimiento">
                                        {/* Contenido de la pestaña de mantenimiento */}
                                    </Tab.Pane>
                                </Tab.Content>
                            </motion.div>
                        </Col>
                    </Row>
                </Tab.Container>
            </Modal.Body>
        </Modal>
    );
}

// Componente auxiliar para las tarjetas de información
const InfoCard = ({ label, value, badge, fullWidth = false }) => (
    <div className={`info-card ${fullWidth ? 'full-width' : ''}`}>
        <span className="info-label">{label}</span>
        <div className="info-value-container">
            <span className="info-value">{value}</span>
            {badge && <div className="info-badge">{badge}</div>}
        </div>
    </div>
);