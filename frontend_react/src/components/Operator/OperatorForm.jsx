import { useState, useEffect } from 'react';
import { Form, Button, Modal, Alert, Row, Col } from 'react-bootstrap';
import { createOperator, updateOperator, deleteOperator } from '../../api/operator.api.js';
import { getOperatorFormMachines } from '../../api/machines.api.js';
import { getAllEmpresas } from '../../api/empresas.api.js';
import { toast } from 'react-hot-toast';
import { FaUser, FaIdCard, FaBuilding, FaCog, FaTrash, FaSave, FaTimes } from 'react-icons/fa';
import './css/OperatorForm.css';

export function OperatorForm({ show, handleClose, operatorToEdit, onOperatorSaved }) {
    const [formData, setFormData] = useState({
        nombre: '',
        rut: '',
        empresa: '',
        maquinas: [],
        activo: true
    });

    const [machines, setMachines] = useState([]);
    const [empresas, setEmpresas] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

    useEffect(() => {
        loadInitialData();
    }, []);

    useEffect(() => {
        if(operatorToEdit){
            setFormData({
                nombre: operatorToEdit.nombre,
                rut: operatorToEdit.rut,
                empresa: operatorToEdit.empresa || 1,
                maquinas: operatorToEdit.maquinas_habilitadas || [],
                activo: operatorToEdit.activo
            });
        } else {
            resetForm();
        }
    }, [operatorToEdit]);

    const loadInitialData = async () => {
        try{
            const [machinesData, empresasData] = await Promise.all([
                getOperatorFormMachines(),
                getAllEmpresas()
            ]);
            setMachines(machinesData);
            setEmpresas(empresasData)
        } catch(error){
            console.error('Error al cargar datos iniciales:', error);
            setError('Error al cargar datos necesarios');
        }
    };

    const resetForm = () => {
        setFormData({
            nombre: '',
            rut: '',
            empresa: 1,
            maquinas: [],
            activo: true
        });
        setError('');
    };

    const validateRut = (rut) => {
        //Expresión regultar para validar formato RUT (XX.XXX.XXX-X)
        const rutRegex = /^\d{1,2}\.\d{3}\.\d{3}[-][0-9kK]{1}$/;
        return rutRegex.test(rut);
    }

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        //Validaciones
        if(!formData.nombre.trim()){
            setError('El nombre es requerido');
            return;
        }

        if(!validateRut(formData.rut)){
            setError('El formato del RUT no es válido (XX.XXX.XXX-X)');
            return;
        }

        if(formData.maquinas.length === 0){
            setError('Debe seleccionar al menos una máquina');
            return
        }

        setLoading(true);
        try{
            console.log('maqs operatorform:', formData.maquinas )
            const dataToSend = {
                nombre: formData.nombre,
                rut: formData.rut,
                empresa: parseInt(formData.empresa),
                maquinas_habilitadas: formData.maquinas,
                activo: formData.activo
            };

            console.log('Datos a enviar:', dataToSend);

            if(operatorToEdit) {
                await updateOperator(operatorToEdit.id, dataToSend);
            }else{
                onOperatorSaved();
                handleClose()
                await createOperator(dataToSend);

            }

            
            if(operatorToEdit){
                await updateOperator(operatorToEdit.id, formData);
                toast.success('Operador actualizado exitosamente');
            }else{
                await createOperator(formData);
                toast.success('Operador creado exitosamente');
            }
            onOperatorSaved();
            handleClose();
            resetForm();
        } catch (error) {
            console.error('Error:', error);
            const errorMessage = error.response?.data?.detail || error.response?.data?.message || 'Error al guardar el operador';
            setError(errorMessage);
        } finally {
            setLoading(false);
        }
    };

    const handleChange = (e) => {
        const {name, value, type, checked} = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value
        }));
    };

    const handleMachineSelect = (e) => {
        const selectedOptions = Array.from(e.target.selectedOptions, option => parseInt(option.value));
        setFormData(prev => ({
            ...prev,
            maquinas: selectedOptions
        }));
    };

    const handleDelete = async () => {
        setLoading(true);
        try{
            await deleteOperator(operatorToEdit.id);
            toast.success('Operador eliminado exitosamente');
            onOperatorSaved();
            handleClose();
        } catch(error) {
            console.error('Error al eliminar operador:', error);
            const errorMessage = error.response?.data?.detail || 'Error al eliminar el operador';
            setError(errorMessage);
        } finally {
            setLoading(false);
            setShowDeleteConfirm(false);
        }
    }
    return (
        <Modal show={show} onHide={handleClose} backdrop="static" keyboard={false} className="operator-form-modal">
            <Form onSubmit={handleSubmit}>
                <Modal.Header closeButton>
                    <Modal.Title className="modal-title">
                        <FaUser className="title-icon" />
                        {operatorToEdit ? 'Editar Operador' : 'Nuevo Operador'}
                    </Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    {error && (
                        <Alert variant="danger" className="error-alert">
                            <i className="fas fa-exclamation-circle me-2"></i>
                            {error}
                        </Alert>
                    )}

                    <div className="form-section">
                        <Form.Group className="form-group">
                            <Form.Label>
                                <FaUser className="field-icon" /> Nombre
                            </Form.Label>
                            <Form.Control
                                type="text"
                                name="nombre"
                                value={formData.nombre}
                                onChange={handleChange}
                                placeholder="Ingrese el nombre completo"
                                className="form-input"
                                required
                            />
                        </Form.Group>

                        <Form.Group className="form-group">
                            <Form.Label>
                                <FaIdCard className="field-icon" /> RUT
                            </Form.Label>
                            <Form.Control
                                type="text"
                                name="rut"
                                value={formData.rut}
                                onChange={handleChange}
                                placeholder="XX.XXX.XXX-X"
                                className="form-input"
                                required
                            />
                            <Form.Text className="text-muted">
                                Formato: XX.XXX.XXX-X
                            </Form.Text>
                        </Form.Group>

                        <Form.Group className="form-group">
                            <Form.Label>
                                <FaBuilding className="field-icon" /> Empresa
                            </Form.Label>
                            <Form.Select
                                name="empresa"
                                value={formData.empresa}
                                onChange={handleChange}
                                className="form-select"
                                required
                            >
                                <option value="">Seleccione una empresa...</option>
                                {empresas.map(empresa => (
                                    <option key={empresa.id} value={empresa.id}>
                                        {empresa.nombre}
                                    </option>
                                ))}
                            </Form.Select>
                        </Form.Group>
                    </div>

                    <div className="machines-section">
                        <Form.Label className="machines-title">
                            <FaCog className="field-icon" /> Máquinas Asignadas
                        </Form.Label>
                        <div className="machines-container">
                            {machines.map(machine => (
                                <div
                                    key={machine.id}
                                    className={`machine-item ${formData.maquinas.includes(machine.id) ? 'selected' : ''}`}
                                    onClick={() => {
                                        const newMachines = formData.maquinas.includes(machine.id)
                                            ? formData.maquinas.filter(id => id !== machine.id)
                                            : [...formData.maquinas, machine.id];
                                        setFormData(prev => ({ ...prev, maquinas: newMachines }));
                                    }}
                                >
                                    <div className="machine-header">
                                        <div className="machine-code">{machine.codigo_maquina}</div>
                                        {formData.maquinas.includes(machine.id) && (
                                            <div className="selected-indicator">✓</div>
                                        )}
                                    </div>
                                    <div className="machine-desc">{machine.descripcion}</div>
                                    <div className={`machine-status ${machine.estado_operatividad?.estado === 'OP' ? 'active' : 'inactive'}`}>
                                        {machine.estado_operatividad?.descripcion || 'No especificado'}
                                    </div>
                                </div>
                            ))}
                        </div>
                        <Form.Text className="text-muted machines-help">
                            Haga clic en las máquinas para seleccionar/deseleccionar
                        </Form.Text>
                    </div>

                    <Form.Group className="form-group status-group">
                        <Form.Check
                            type="switch"
                            id="operator-status"
                            name="activo"
                            label="Operador Activo"
                            checked={formData.activo}
                            onChange={handleChange}
                            className="status-switch"
                        />
                    </Form.Group>

                    {showDeleteConfirm && operatorToEdit && (
                        <Alert variant="danger" className="delete-alert">
                            <p>¿Está seguro que desea eliminar al operador {operatorToEdit.nombre}?</p>
                            <div className="alert-actions">
                                <Button
                                    variant="outline-secondary"
                                    size="sm"
                                    onClick={() => setShowDeleteConfirm(false)}
                                    className="me-2"
                                >
                                    <FaTimes className="button-icon" /> Cancelar
                                </Button>
                                <Button
                                    variant="danger"
                                    size="sm"
                                    onClick={handleDelete}
                                >
                                    <FaTrash className="button-icon" /> Confirmar
                                </Button>
                            </div>
                        </Alert>
                    )}
                </Modal.Body>
                <Modal.Footer>
                    <div className="button-container">
                        <Button 
                            variant="danger" 
                            onClick={() => setShowDeleteConfirm(true)}
                            disabled={loading || showDeleteConfirm}
                            className="action-button delete-button"
                        >
                            <FaTrash className="button-icon" /> Eliminar
                        </Button>
                        <div className="button-group">
                            <Button 
                                variant="secondary" 
                                onClick={handleClose} 
                                disabled={loading} 
                                className="action-button cancel-button"
                            >
                                <FaTimes className="button-icon" /> Cancelar
                            </Button>
                            <Button 
                                variant="primary" 
                                type="submit" 
                                disabled={loading}
                                className="action-button save-button"
                            >
                                <FaSave className="button-icon" />
                                {loading ? 'Guardando...' : (operatorToEdit ? 'Actualizar' : 'Crear')}
                            </Button>
                        </div>
                    </div>
                </Modal.Footer>
            </Form>
        </Modal>
    );
}