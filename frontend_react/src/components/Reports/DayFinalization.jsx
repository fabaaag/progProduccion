import React from 'react';
import { Modal, Button, Alert } from 'react-bootstrap';
import { FaExclamationTriangle, FaCheckCircle, FaClock } from 'react-icons/fa';
import './css/DayFinalization.css'

export const DayFinalization = ({ show, onHide, date, tasks }) => {
    const pendingTasks = tasks.filter(t => t.estado !== 'Terminado');
    const hasUnfinishedTasks = pendingTasks.length > 0;

    const handleFinalize = () => {
        //Logica para finalizar el día
        console.log('Finalizando día...');
        onHide();
    };

    return (
        <Modal show={show} onHide={onHide} centered className="day-finalization-modal">
            <Modal.Header closeButton>
                <Modal.Title>
                    <FaClock className="me-2" />
                    Finalizar Día
                </Modal.Title>
            </Modal.Header>
            <Modal.Body>
                <div className="date-summary">
                    <h6>Fecha: {date?.toLocaleDateString('es-ES', {
                        weekday: 'long',
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric'
                    })}</h6>
                </div>

                {hasUnfinishedTasks ? (
                    <Alert variant="warning" className="mt-3">
                        <FaExclamationTriangle className="me-2" />
                        <strong>Atención:</strong> Hay tareas sin completar
                    </Alert>
                ) : (
                    <Alert variant="success" className="mt-3">
                        <FaCheckCircle className="me-2" />
                        Todas las tareas están completadas
                    </Alert>
                )}

                {hasUnfinishedTasks && (
                    <div className="pending-tasks mt-3">
                        <h6>Tareas pendientes:</h6>
                        <ul className="task-list">
                            {pendingTasks.map(task => (
                                <li key={task.id} className="task-item">
                                    <span className="ot-code">{task.ot_codigo}</span>
                                    <span className="process">{task.proceso?.descripcion}</span>
                                    <span className={`status ${task.estado.toLowerCase()}`}>
                                        {task.estado}
                                    </span>
                                </li>
                            ))}
                        </ul>
                    </div>
                )}
            </Modal.Body>
            <Modal.Footer>
                <Button variant="secondary" onClick={onHide}>
                    Cancelar
                </Button>
                <Button 
                    variant="primary" 
                    onClick={handleFinalize}
                    className={hasUnfinishedTasks ? 'btn-warning' : 'btn-success'}
                >
                    {hasUnfinishedTasks ? 'Finalizar con Pendientes' : 'Finalizar Día'}
                </Button>
            </Modal.Footer>
        </Modal>
    );
};