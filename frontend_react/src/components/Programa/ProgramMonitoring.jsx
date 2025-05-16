import React, { useState, useEffect } from 'react';
import { Alert, Card, Row, Col, ListGroup, Modal, Button, Badge } from 'react-bootstrap';
import { checkProgramStatus } from '../../api/programs.api';
import { FaExclamationTriangle, FaClock, FaTools } from 'react-icons/fa';

export const ProgramMonitoring = ({ programId }) => {
    const [statusInfo, setStatusInfo] = useState(null);
    const [alertas, setAlertas] = useState([]);
    const [showRetrasosModal, setShowRetrasosModal] = useState(false);
    const [showCuellosModal, setShowCuellosModal] = useState(false);

    const verificarEstado = async () => {
        try {
            const data = await checkProgramStatus(programId);
            setStatusInfo(data);

            const nuevasAlertas = [];

            if (data.tareas_retrasadas > 0) {
                nuevasAlertas.push({
                    variant: 'danger',
                    mensaje: `${data.tareas_retrasadas} tareas presentan retrasos`
                });
            }

            if (data.cuellos_botella > 0) {
                nuevasAlertas.push({
                    variant: 'warning',
                    mensaje: `Se detectaron ${data.cuellos_botella} cuellos de botella`
                });
            }

            setAlertas(nuevasAlertas);
        } catch (error) {
            console.error('Error al verificar estado:', error);
        }
    };

    useEffect(() => {
        verificarEstado()
        const interval = setInterval(verificarEstado, 300000);
        return () => clearInterval(interval);
    }, [programId]);

    return (
        <div className="program-monitoring">
            {alertas.map((alerta, index) => (
                <Alert key={index} variant={alerta.variant} className="mb-3">
                    {alerta.mensaje}
                </Alert>
            ))}

            {statusInfo && (
                <Row className="mb-4">
                    <Col md={4}>
                        <Card 
                            className="cursor-pointer" 
                            onClick={() => statusInfo.tareas_retrasadas > 0 && setShowRetrasosModal(true)}
                            style={{ cursor: statusInfo.tareas_retrasadas > 0 ? 'pointer' : 'default' }}
                        >
                            <Card.Body className="text-center">
                                <FaClock className="mb-2" size={24} color="#dc3545"/>
                                <Card.Title>Tareas Retrasadas</Card.Title>
                                <Card.Text className='text-danger h2'>
                                    {statusInfo.tareas_retrasadas}
                                </Card.Text>
                                {statusInfo.tareas_retrasadas > 0 && (
                                    <small className="text-muted">Click para ver detalles</small>
                                )}
                            </Card.Body>
                        </Card>
                    </Col>
                    <Col md={4}>
                        <Card 
                            className="cursor-pointer"
                            onClick={() => statusInfo.cuellos_botella > 0 && setShowCuellosModal(true)}
                            style={{ cursor: statusInfo.cuellos_botella > 0 ? 'pointer' : 'default' }}
                        >
                            <Card.Body className="text-center">
                                <FaExclamationTriangle className="mb-2" size={24} color="#ffc107"/>
                                <Card.Title>Cuellos de Botella</Card.Title>
                                <Card.Text className='text-warning h2'>
                                    {statusInfo.cuellos_botella}
                                </Card.Text>
                                {statusInfo.cuellos_botella > 0 && (
                                    <small className="text-muted">Click para ver detalles</small>
                                )}
                            </Card.Body>
                        </Card>
                    </Col>
                    <Col md={4}>
                        <Card>
                            <Card.Body className="text-center">
                                <FaTools className="mb-2" size={24} color="#0dcaf0"/>
                                <Card.Title>Acciones Tomadas</Card.Title>
                                <Card.Text className='text-info h2'>
                                    {statusInfo.acciones_tomadas?.length || 0}
                                </Card.Text>
                            </Card.Body>
                        </Card>
                    </Col>
                </Row>
            )}

            {/* Modal de Tareas Retrasadas */}
            <Modal 
                show={showRetrasosModal} 
                onHide={() => setShowRetrasosModal(false)}
                size="lg"
            >
                <Modal.Header closeButton>
                    <Modal.Title>
                        <FaClock className="me-2 text-danger"/>
                        Detalle de Tareas Retrasadas
                    </Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <ListGroup variant='flush'>
                        {statusInfo?.tareas_retrasadas_detalle?.map((tarea, index) => (
                            <ListGroup.Item key={index} className="border-bottom">
                                <div className="d-flex justify-content-between align-items-start">
                                    <div>
                                        <h6 className="mb-1">OT {tarea.ot_codigo}</h6>
                                        <p className="mb-1">{tarea.proceso}</p>
                                        <small className="text-muted">Operador: {tarea.operador}</small>
                                    </div>
                                    <Badge bg="danger" pill>
                                        {tarea.retraso.toFixed(2)}%
                                    </Badge>
                                </div>
                            </ListGroup.Item>
                        ))}
                    </ListGroup>
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="secondary" onClick={() => setShowRetrasosModal(false)}>
                        Cerrar
                    </Button>
                </Modal.Footer>
            </Modal>

            {/* Modal de Cuellos de Botella */}
            <Modal 
                show={showCuellosModal} 
                onHide={() => setShowCuellosModal(false)}
                size="lg"
            >
                <Modal.Header closeButton>
                    <Modal.Title>
                        <FaExclamationTriangle className="me-2 text-warning"/>
                        Detalle de Cuellos de Botella
                    </Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <ListGroup variant='flush'>
                        {statusInfo?.cuellos_botella_detalle?.map((cuello, index) => (
                            <ListGroup.Item key={index} className="border-bottom">
                                <h6 className="d-flex justify-content-between align-items-center">
                                    <span>
                                        {cuello.maquina_codigo} - {cuello.maquina_descripcion}
                                    </span>
                                    <Badge bg="warning" text="dark">
                                        {cuello.tiempo_total.toFixed(2)} hrs
                                    </Badge>
                                </h6>
                                <ListGroup variant="flush" className="mt-2">
                                    {cuello.tareas_afectadas.map((tarea, idx) => (
                                        <ListGroup.Item key={idx} className="py-2">
                                            <div className="d-flex justify-content-between align-items-center">
                                                <span>OT {tarea.ot_codigo} - {tarea.proceso}</span>
                                                <small className="text-muted">
                                                    {tarea.tiempo_estimado.toFixed(2)} hrs
                                                </small>
                                            </div>
                                        </ListGroup.Item>
                                    ))}
                                </ListGroup>
                            </ListGroup.Item>
                        ))}
                    </ListGroup>
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="secondary" onClick={() => setShowCuellosModal(false)}>
                        Cerrar
                    </Button>
                </Modal.Footer>
            </Modal>
        </div>
    );
};