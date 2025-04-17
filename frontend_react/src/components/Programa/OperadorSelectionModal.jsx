import React, { useState, useEffect } from 'react';
import { Modal, Button, Form, Spinner } from 'react-bootstrap';
import { getOperadoresPorMaquina } from '../../api/operator.api.js'
import { toast } from 'react-hot-toast';

export function OperadorSelectionModal({
    show, 
    onHide,
    maquinaId,
    procesoId,
    currentOperadorId,
    onSelect
}) {
    const [operadores, setOperadores] = useState([]);
    const [selectedOperadorId, setSelectedOperadorId] = useState('');
    const [loading, setLoading] = useState(false);

    //Cargar operadores cuando se abre el modal
    useEffect(() => {
        if (show && maquinaId){
            loadOperadores();
        }

        //Establecer el operador actual como seleccionado si existe
        if(currentOperadorId){
            setSelectedOperadorId(currentOperadorId);

        } else {
            setSelectedOperadorId('');
        }
    }, [show, maquinaId, currentOperadorId]);

    const loadOperadores = async () => {
        setLoading(true);
        try{
            const data= await getOperadoresPorMaquina(maquinaId);
            setOperadores(data);
            console.log(`[Modal] Operadores cargados para máquina ${maquinaId}: `, data);

        } catch (error){
            console.error('Error al cargar operadores:', error);
            toast.error('No se pudieron cargar los operadores disponibles');
        } finally {
            setLoading(false);
        }
    };

    const handleSelectOperador = () => {
        onSelect(selectedOperadorId);
        onHide();
    };

    const handleRemoveOperador = () => {
        onSelect(null);
        onHide();
    };

    return (
        <Modal show={show} onHide={onHide} centered>
            <Modal.Header closeButton>
                <Modal.Title>Seleccionar Operador</Modal.Title>
            </Modal.Header>
            <Modal.Body>
                {loading ? (
                    <div className='text-center'>
                        <Spinner animation="border" role="status">
                            <span className="visually-hidden">Cargando...</span>
                        </Spinner>
                    </div>
                ) : operadores.length > 0 ? (
                    <Form>
                        <Form.Group>
                            <Form.Label>Operadores disponibles para esta máquina</Form.Label>
                            <Form.Control
                                as="select"
                                value={selectedOperadorId}
                                onChange={(e) => setSelectedOperadorId(e.target.value)}
                            >
                                <option value="">Seleccione un operador</option>
                                {operadores.map(operador => (
                                    <option key={operador.id} value={operador.id}>
                                        {operador.nombre}
                                    </option>
                                ))}
                            </Form.Control>
                        </Form.Group>
                    </Form>
                ) : (
                    <p className='text-danger'>No hay operadores habilitados para esta máquina</p>
                )}
            </Modal.Body>
            <Modal.Footer>
                {currentOperadorId && (
                    <Button 
                        variant="outline-danger"
                        onClick={handleRemoveOperador}
                    >Desasignar</Button>
                )}
                <Button variant="secondary" onClick={onHide}>Cancelar</Button>
                <Button
                    variant="primary"
                    onClick={handleSelectOperador}
                    disabled={!selectedOperadorId || loading}
                >Asignar</Button>
            </Modal.Footer>
        </Modal>
    );
}