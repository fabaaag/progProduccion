import React, { useState, useEffect } from 'react';
import { Modal, Card, Form, Button, Badge, InputGroup } from 'react-bootstrap';
import { FaSearch, FaExclamationTriangle } from 'react-icons/fa';
import { toast } from 'react-hot-toast';
import { addOrdersToProgram, getUnassignedOrders } from '../../api/programs.api';

export const AgregarOrdenModal = ({ show, onHide, programId, onOrdersAdded }) => {
    const [searchTerm, setSearchTerm] = useState('');
    const [ordenes, setOrdenes] = useState([]);
    const [ordenesFiltradas, setOrdenesFiltradas] = useState([]);
    const [ordenesSeleccionadas, setOrdenesSeleccionadas] = useState([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (show){
            cargarOrdenes();
        }
    }, [show]);

    useEffect(() => {
        filtrarOrdenes();
    }, [searchTerm, ordenes]);

    const cargarOrdenes = async () => {
        try {
            setLoading(true);
            const response = await getUnassignedOrders();
            setOrdenes(response);
            setOrdenesFiltradas(response);
        } catch (error) {
            toast.error('Error al cargar órdenes disponibles');
            console.error('Error cargando órdenes:', error);
        } finally {
            setLoading(false);
        }
    };

    const filtrarOrdenes = () => {
        if (!searchTerm.trim()){
            setOrdenesFiltradas(ordenes);
            return;
        }

        const termino = searchTerm.toLowerCase();
        const filtradas = ordenes.filter(orden => 
            orden.codigo_ot.toLowerCase().includes(termino) ||
            orden.descripcion_producto_ot.toLowerCase().includes(termino)
        );
        setOrdenesFiltradas(filtradas);
    };

    const toggleOrdenSeleccion = (orden) => {
        setOrdenesSeleccionadas(prev => {
            const isSelected = prev.some(o => o.id === orden.id);
            if(isSelected){
                return prev.filter(o => o.id !== orden.id);
            } else {
                return [...prev, orden];
            }
        });
    };

    const handleSubmit = async () => {
        try {
            if (ordenesSeleccionadas.length === 0) {
                toast.error('Selecciona al menos una orden');
                return;
            }

            const orderIds = ordenesSeleccionadas.map(orden => orden.id);
            await addOrdersToProgram(programId, orderIds);

            toast.success('Ordenes agregadas correctamente');
            onOrdersAdded && onOrdersAdded();
            onHide();
            setOrdenesSeleccionadas([]);
            setSearchTerm('');
        } catch (error) {
            toast.error('Error al agregar órdenes al programa');
            console.error('Error:', error);
        }
    };

    return (
        <Modal show={show} onHide={onHide} size='lg'>
            <Modal.Header closeButton>
                <Modal.Title>Agregar Órdenes al Programa</Modal.Title>
            </Modal.Header>
            <Modal.Body>
                <Form.Group className="mb-3">
                    <InputGroup>
                        <Form.Control 
                            type="text"
                            placeholder='Buscar por código o descripción...'
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                        <Button variant='outline-secondary'>
                            <FaSearch />
                        </Button>
                    </InputGroup>
                </Form.Group>

                {loading ? (
                    <div className="text-center">
                        <span>Cargando órdenes disponibles...</span>
                    </div>
                ) : (
                    <div style={{ maxHeight: '400px', overflowY: 'auto'}}>
                        {ordenesFiltradas.length === 0 ? (
                            <div className="text-center text-muted">
                                No se encontraron órdenes disponibles
                            </div>
                        ) : (
                            ordenesFiltradas.map(orden => (
                                <Card
                                    key={orden.id}
                                    className={`mb-2 ${ordenesSeleccionadas.some(o => o.id === orden.id)
                                        ? 'border-primary' : ''
                                    }`}
                                    onClick={() => toggleOrdenSeleccion(orden)}
                                    style={{ cursor: 'pointer' }}
                                >
                                    <Card.Body>
                                        <div className="d-flex justify-content-between align-items-center">
                                            <div>
                                                <h6>{orden.codigo_ot}</h6>
                                                <small>{orden.descripcion_producto_ot}</small>
                                            </div>
                                        </div>
                                    </Card.Body>
                                </Card>
                            ))
                        )}
                    </div>
                )}
            </Modal.Body>
            <Modal.Footer>
                <Button variant="secondary" onClick={onHide}>
                    Cancelar
                </Button>
                <Button
                    variant="primary"
                    onClick={handleSubmit}
                    disabled={ordenesSeleccionadas.length === 0}
                >
                    Agregar ({ordenesSeleccionadas.length})
                </Button>
            </Modal.Footer>
        </Modal>
    );
};