import { useState, useEffect } from 'react';
import { Container, Card, Table, Form, Row, Col, Button } from 'react-bootstrap';
import CompNavbar from '../Navbar/CompNavbar';
import { getAllOperators } from '../../api/operator.api';
import { getAllMachines } from '../../api/machines.api';
import { toast } from 'react-hot-toast';
import { OperatorForm } from './OperatorForm';
import { OperatorMachinesModal } from './OperatorMachinesModal';
import { OperatorAsignacionesModal } from './OperatorAsignacionesModal';
import { FaUserPlus, FaEdit, FaCog, FaSearch, FaClipboardList } from 'react-icons/fa';
import { motion } from 'framer-motion';
import './css/OperatorManagement.css';

export function OperatorManagementPage() {
    const [operators, setOperators] = useState([]);
    const [machines, setMachines] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [editingOperator, setEditingOperator] = useState(null);
    const [filters, setFilters] = useState({
        searchTerm: '',
        machine: ''
    });
    const [showMachinesModal, setShowMachinesModal] = useState(false);
    const [selectedOperator, setSelectedOperator] = useState(null);

    const [showAsignacionesModal, setShowAsignacionesModal] = useState(false);
    const [selectedOperatorForAsignaciones, setSelectedOperatorForAsignaciones] = useState(null);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try{
            setLoading(false);
            const operatorsData = await getAllOperators();
            setOperators(operatorsData);

            const machinesData = await getAllMachines();
            setMachines(machinesData);
        }catch (error){
            console.error('Error al cargar operadores:', error);
            toast.error('Error al cargar los operadores');  
            console.error('Error al cargar las máquinas:', error);
            toast.error('Error al cargar las máquinas');
        } finally {
            setLoading(false);
        }
    };

    const handleEdit = (operator) => {
        setEditingOperator(operator);
        setShowModal(true);
    };

    const handleCloseModal = () => {
        setShowModal(false);
        setEditingOperator(null);
    };

    const handleShowMachines = (operator) => {
        // Asegurarse de que operator.maquinas exista
        if(!operator.maquinas){
            console.warn(`El operador ${operator.nombre} no tiene máquinas definidas`);
            operator.maquinas = []; // Asignar un array vacío para evitar errores
        }
        setSelectedOperator(operator);
        setShowMachinesModal(true);        
    }
    
    const filteredOperators = operators.filter(operator => {
        const searchTerm = filters.searchTerm.toLowerCase();
        return operator.nombre.toLowerCase().includes(searchTerm) ||
                operator.rut.toLowerCase().includes(searchTerm);
    });

    const handleShowAsignaciones = (operator) => {
        setSelectedOperatorForAsignaciones(operator);
        setShowAsignacionesModal(true);
    }

    return (
        <>
            <CompNavbar />
            <Container className="mt-4">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5 }}
                >
                    <Card className="operator-manage-card">
                        <Card.Header className="d-flex justify-content-between align-items-center">
                            <h3 className="mb-0">Gestión de Operarios</h3>
                            <Button 
                                variant="primary" 
                                onClick={() => setShowModal(true)}
                                className="create-operator-btn"
                            >
                                <FaUserPlus className="me-2" />
                                Nuevo Operador
                            </Button>
                        </Card.Header>
                        <Card.Body>
                            <Row className="mb-4">
                                <Col md={6}>
                                    <div className="search-input-wrapper">
                                        <FaSearch className="search-icon" />
                                        <Form.Control
                                            type="text"
                                            placeholder="Buscar por nombre o RUT..."
                                            value={filters.searchTerm}
                                            onChange={(e) => setFilters({
                                                ...filters,
                                                searchTerm: e.target.value
                                            })}
                                            className="search-input"
                                        />
                                    </div>
                                </Col>
                                <Col md={6}>
                                    <Form.Select
                                        value={filters.machine}
                                        onChange={(e) => setFilters({
                                            ...filters,
                                            machine: e.target.value
                                        })}
                                        className="filter-select"
                                    >
                                        <option value="">Filtrar por máquina</option>
                                        {machines.map(machine => (
                                            <option key={machine.id} value={machine.id}>
                                                {machine.descripcion}
                                            </option>
                                        ))}
                                    </Form.Select>
                                </Col>
                            </Row>

                            {loading ? (
                                <div className="text-center py-4">
                                    <div className="spinner-border text-primary" role="status">
                                        <span className="visually-hidden">Cargando...</span>
                                    </div>
                                </div>
                            ) : (
                                <div className="table-responsive">
                                    <Table hover className="operator-table">
                                        <thead>
                                            <tr>
                                                <th>Nombre</th>
                                                <th>RUT</th>
                                                <th>Empresa</th>
                                                <th>Máquinas</th>
                                                <th>Estado</th>
                                                <th>Acciones</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {filteredOperators.map(operator => (
                                                <motion.tr 
                                                    key={operator.id}
                                                    initial={{ opacity: 0 }}
                                                    animate={{ opacity: 1 }}
                                                    transition={{ duration: 0.3 }}
                                                >
                                                    <td>{operator.nombre}</td>
                                                    <td>{operator.rut}</td>
                                                    <td>{operator.empresa.nombre}</td>
                                                    <td>
                                                        <Button 
                                                            variant="info" 
                                                            size="sm"
                                                            onClick={() => handleShowMachines(operator)}
                                                            className="machines-btn"
                                                        >
                                                            <FaCog className="me-2" />
                                                            Ver Máquinas ({operator.maquinas_habilitadas ? operator.maquinas_habilitadas.length : 0})
                                                        </Button>
                                                    </td>
                                                    <td>
                                                        <span className={`status-badge ${operator.activo ? 'active' : 'inactive'}`}>
                                                            {operator.activo ? 'Activo' : 'Inactivo'}
                                                        </span>
                                                    </td>
                                                    <td>
                                                        <div className="action-buttons">
                                                            <Button 
                                                                variant="primary" 
                                                                size="sm" 
                                                                onClick={() => handleEdit(operator)}
                                                                className="action-button edit-button"
                                                            >
                                                                <FaEdit className="me-1" /> Editar
                                                            </Button>
                                                            <Button 
                                                                variant="success" 
                                                                size="sm" 
                                                                onClick={() => handleShowAsignaciones(operator)}
                                                                className="action-button assign-button"
                                                            >
                                                                <FaClipboardList className="me-1" /> Ver Asignaciones
                                                            </Button>
                                                        </div>
                                                    </td>
                                                </motion.tr>
                                            ))}
                                        </tbody>
                                    </Table>
                                </div>
                            )}
                        </Card.Body>
                    </Card>
                </motion.div>
            </Container>

            <OperatorForm 
                show={showModal}
                handleClose={handleCloseModal}
                operatorToEdit={editingOperator}
                onOperatorSaved={loadData}
            />

            <OperatorMachinesModal 
                show={showMachinesModal}
                handleClose={() => setShowMachinesModal(false)}
                operator={selectedOperator}
            />

            <OperatorAsignacionesModal 
                show={showAsignacionesModal}
                handleClose={() => setShowAsignacionesModal(false)}
                operator={selectedOperatorForAsignaciones}
            />
        </>
    );
}