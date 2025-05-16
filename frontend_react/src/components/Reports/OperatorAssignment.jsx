import React, { useState, useEffect } from 'react';
import { Modal, Button, Form, ListGroup } from 'react-bootstrap';
import { FaSearch, FaUserPlus } from 'react-icons/fa';
import './css/OperatorAssignment.css';

export const OperatorAssignment = ({ show, onHide, task }) => {
    const [searchTerm, setSearchTerm] = useState('');
    const [operators, setOperators] = useState([
        //Data de ejemplo, luego lo traemos de la api
        { id: 1, nombre: 'Juan Pérez', disponible: true },
        { id: 2, nombre: 'María García', disponible: false },
        { id: 3, nombre: 'Carlos López', disponible: true },
        //... más operadores
    ]);
    const [selectedOperator, setSelectedOperator] = useState(null);

    useEffect(() => {
        if (show) {
            //loadOperators();
            setSearchTerm('');
            setSelectedOperator(null);
        }
    }, [show]);

    const filteredOperators = operators.filter(op => 
        op.nombre.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const handleAssign = () => {
        if (selectedOperator) {
            //Aqui iría la logica para asignar el operador
            console.log(`Asignando operador ${selectedOperator.nombre} a la tarea ${task?.id}`);
            onHide();
            
        }
    };

    return (
        <Modal show={show} onHide={onHide} centered className="operator-assignment-modal">
            <Modal.Header closeButton>
                <Modal.Title>
                    <FaUserPlus className="me-2" />
                    Asignar Operador
                </Modal.Title>
            </Modal.Header>
            <Modal.Body>
                <div className="task-info mb-3">
                    <h6>Información de la Tarea:</h6>
                    <p className="mb-1"><strong>OT:</strong> {task?.ot_codigo}</p>
                    <p className="mb-1"><strong>Proceso:</strong> {task?.proceso?.descripcion}</p>
                    <p className="mb-0"><strong>Máquina:</strong> {task?.maquina?.descripcion}</p>
                </div>

                <Form.Group className="mb-3 search-container">
                    <Form.Control
                        type="text"
                        placeholder="Buscar operador..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                    <FaSearch className="search-icon" />
                </Form.Group>

                <ListGroup className="operators-list">
                    {filteredOperators.map(operator => (
                        <ListGroup.Item
                            key={operator.id}
                            action
                            active={selectedOperator?.id === operator.id}
                            onClick={() => setSelectedOperator(operator)}
                            disabled={!operator.disponible}
                            className={`operator-item ${!operator.disponible ? 'unavailable' : ''}`}
                        >
                            <div className="operator-info">
                                <span className="operator-name">{operator.nombre}</span>
                                <span className={`operator-status ${operator.disponible ? 'available' : 'busy'}`}>
                                    {operator.disponible ? 'Disponible' : 'Ocupado'}
                                </span>
                            </div>
                        </ListGroup.Item>
                    ))}
                </ListGroup>
            </Modal.Body>
            <Modal.Footer>
                <Button variant="secondary" onClick={onHide}>
                    Cancelar
                </Button>
                <Button 
                    variant="primary" 
                    onClick={handleAssign}
                    disabled={!selectedOperator}
                >
                    Asignar Operador
                </Button>
            </Modal.Footer>
        </Modal>
    );
};