import React, { useEffect, useState } from 'react';
import { Card, Badge, Button, Container, InputGroup, Form, Pagination, OverlayTrigger, Tooltip } from 'react-bootstrap';
import CompNavbar from '../Navbar/CompNavbar';
import { Footer } from '../../components/Footer/Footer';
import { getAllMachinesFromApp, getMachineDetails, getMachineTypes } from '../../api/machines.api';
import { toast } from 'react-hot-toast';
import { MachineDetailsModal } from './MachineDetailsModal';
import { FaSearch, FaPlus, FaCog, FaTools } from 'react-icons/fa';
import { LoadingSpinner } from '../UI/LoadingSpinner/LoadingSpinner';
import './css/MachineList.css';

export function MachineList() {
    const [machines, setMachines] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [selectedMachine, setSelectedMachine] = useState(null);
    const [loadingDetails, setLoadingDetails] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [filterStatus, setFilterStatus] = useState('all');
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage] = useState(9); // 9 máquinas por página (3x3 grid)
    const [machineTypes, setMachineTypes] = useState([]);
    const [selectedMachineType, setSelectedMachineType] = useState('all');

    useEffect(() => {
        loadMachines();
        loadMachineTypes();
    }, []);

    const loadMachines = async () => {
        try {
            setLoading(true);
            const data = await getAllMachinesFromApp();
            setMachines(data);
        } catch (error) {
            console.error('Error al cargar máquinas:', error);
            toast.error('Error al cargar la lista de máquinas');
        } finally {
            setLoading(false);
        }
    };

    const loadMachineTypes = async () => {
        try {
            const types = await getMachineTypes();
            setMachineTypes(types);
        } catch (error) {
            console.error('Error al cargar tipos de máquina:', error);
            toast.error('Error al cargar los tipos de máquina');
        }
    };

    const handleMachineUpdate = async () => {
        //Recargar los detalles de la máquina después de una actualización
        if (selectedMachine) {
            await handleShowDetails(selectedMachine.id);
        }
        //Recargar la lista de máquinas
        await loadMachines();

    }

    const handleShowDetails = async (machineId) => {
        try{
            setLoadingDetails(true);
            const details = await getMachineDetails(machineId);
            setSelectedMachine(details);
            setShowModal(true);
        } catch (error){
            console.error('Error al cargar detalles:', error);
            toast.error('Error al cargar los detalles de la máquina');
        } finally {
            setLoadingDetails(false);
        }
    };

    const getStatusBadge = (estado) => {
        if (!estado) return <Badge bg="secondary">Sin Estado</Badge>;

        const badgeColors = {
            'Operativa': 'success',
            'En Mantención': 'warning',
            'Inoperativa': 'danger'
        };

        return (
            <Badge bg={badgeColors[estado.estado] || 'secondary'}>
                {estado.estado}
            </Badge>
        );
    };

    const filteredMachines = machines.filter(machine => {
        const matchesSearch = 
            machine.codigo.toLowerCase().includes(searchTerm.toLowerCase()) ||
            machine.descripcion.toLowerCase().includes(searchTerm.toLowerCase());
        
        const matchesStatus = filterStatus === 'all' || 
            (machine.estado && machine.estado.estado === filterStatus);

        const matchesType = selectedMachineType === 'all' || 
            (machine.tipos_maquina && 
             machine.tipos_maquina.some(tipo => tipo.id === parseInt(selectedMachineType)));

        return matchesSearch && matchesStatus && matchesType;
    });

    const getStatusIcon = (estado) => {
        if (!estado) return <FaCog />;
        switch (estado.estado) {
            case 'Operativa': return <FaCog className="text-success" />;
            case 'En Mantención': return <FaTools className="text-warning" />;
            case 'Inoperativa': return <FaCog className="text-danger" />;
            default: return <FaCog />;
        }
    };

    // Cálculos para la paginación
    const indexOfLastMachine = currentPage * itemsPerPage;
    const indexOfFirstMachine = indexOfLastMachine - itemsPerPage;
    const currentMachines = filteredMachines.slice(indexOfFirstMachine, indexOfLastMachine);
    const totalPages = Math.ceil(filteredMachines.length / itemsPerPage);

    // Función para cambiar de página
    const handlePageChange = (pageNumber) => {
        setCurrentPage(pageNumber);
        // Scroll suave hacia arriba
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    // Componente de paginación
    const PaginationComponent = () => {
        if (totalPages <= 1) return null;

        let items = [];
        const maxVisiblePages = 5; // Número máximo de páginas visibles
        let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
        let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

        // Ajustar startPage si estamos cerca del final
        if (endPage - startPage + 1 < maxVisiblePages) {
            startPage = Math.max(1, endPage - maxVisiblePages + 1);
        }

        // Agregar primera página y ellipsis si es necesario
        if (startPage > 1) {
            items.push(
                <Pagination.Item key={1} onClick={() => handlePageChange(1)}>
                    1
                </Pagination.Item>
            );
            if (startPage > 2) {
                items.push(<Pagination.Ellipsis key="ellipsis1" />);
            }
        }

        // Agregar páginas numeradas
        for (let number = startPage; number <= endPage; number++) {
            items.push(
                <Pagination.Item
                    key={number}
                    active={number === currentPage}
                    onClick={() => handlePageChange(number)}
                >
                    {number}
                </Pagination.Item>
            );
        }

        // Agregar última página y ellipsis si es necesario
        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                items.push(<Pagination.Ellipsis key="ellipsis2" />);
            }
            items.push(
                <Pagination.Item
                    key={totalPages}
                    onClick={() => handlePageChange(totalPages)}
                >
                    {totalPages}
                </Pagination.Item>
            );
        }

        return (
            <Pagination className="justify-content-center mt-4">
                <Pagination.Prev
                    onClick={() => handlePageChange(currentPage - 1)}
                    disabled={currentPage === 1}
                />
                {items}
                <Pagination.Next
                    onClick={() => handlePageChange(currentPage + 1)}
                    disabled={currentPage === totalPages}
                />
            </Pagination>
        );
    };

    const MachineTypesBadge = ({ tipos }) => {
        if (!tipos || tipos.length === 0) return <span className="text-muted">No asignado</span>;

        const visibleTypes = tipos.slice(0, 2);
        const remainingCount = tipos.length - 2;

        return (
            <div className="machine-types">
                {visibleTypes.map((tipo, index) => (
                    <Badge 
                        key={tipo.id} 
                        bg="info" 
                        className="me-1"
                    >
                        {tipo.codigo}
                    </Badge>
                ))}
                {remainingCount > 0 && (
                    <OverlayTrigger
                        placement="top"
                        overlay={
                            <Tooltip>
                                {tipos.slice(2).map(tipo => tipo.codigo).join(', ')}
                            </Tooltip>
                        }
                    >
                        <Badge bg="secondary" className="remaining-types">
                            +{remainingCount}
                        </Badge>
                    </OverlayTrigger>
                )}
            </div>
        );
    };

    if (loading) return <LoadingSpinner message="Cargando máquinas..." />;

    return (
        <div className="bg-light min-vh-100">
            <CompNavbar />
            <Container className="py-4">
                {/* Header Section */}
                <div className="d-flex justify-content-between align-items-center mb-4">
                    <h1 className="h3">Gestión de Máquinas</h1>
                    <Button variant="primary" className="d-flex align-items-center gap-2">
                        <FaPlus /> Nueva Máquina
                    </Button>
                </div>

                {/* Filters Section */}
                <Card className="mb-4 shadow-sm">
                    <Card.Body>
                        <div className="row g-3">
                            <div className="col-md-4">
                                <InputGroup className="search-input-group">
                                    <div className="search-icon">
                                        <FaSearch />
                                    </div>
                                    <Form.Control
                                        className="search-input"
                                        placeholder="Buscar máquina..."
                                        value={searchTerm}
                                        onChange={(e) => setSearchTerm(e.target.value)}
                                    />
                                </InputGroup>
                            </div>
                            <div className="col-md-4">
                                <Form.Select
                                    value={filterStatus}
                                    onChange={(e) => setFilterStatus(e.target.value)}
                                >
                                    <option value="all">Todos los estados</option>
                                    <option value="Operativa">Operativa</option>
                                    <option value="En Mantención">En Mantención</option>
                                    <option value="Inoperativa">Inoperativa</option>
                                </Form.Select>
                            </div>
                            <div className="col-md-4">
                                <Form.Select
                                    value={selectedMachineType}
                                    onChange={(e) => setSelectedMachineType(e.target.value)}
                                >
                                    <option value="all">Todos los tipos</option>
                                    {machineTypes.map(type => (
                                        <option key={type.id} value={type.id}>
                                            {type.codigo} - {type.descripcion}
                                        </option>
                                    ))}
                                </Form.Select>
                            </div>
                        </div>
                    </Card.Body>
                </Card>

                {/* Información de resultados */}
                <div className="d-flex justify-content-between align-items-center mb-3">
                    <small className="text-muted">
                        Mostrando {currentMachines.length} de {filteredMachines.length} máquinas
                    </small>
                    <div className="d-flex align-items-center gap-2">
                        <small className="text-muted">Máquinas por página:</small>
                        <span className="badge bg-secondary">{itemsPerPage}</span>
                    </div>
                </div>

                {/* Grid de máquinas */}
                <div className="row g-4">
                    {currentMachines.length === 0 ? (
                        <div className="col-12 text-center py-5">
                            <h5 className="text-muted">No se encontraron máquinas</h5>
                            <p className="text-muted">Intenta ajustar los filtros de búsqueda</p>
                        </div>
                    ) : (
                        currentMachines.map(machine => (
                            <div key={machine.id} className="col-md-6 col-lg-4">
                                <Card 
                                    className="h-100 shadow-sm machine-card" 
                                    onClick={() => handleShowDetails(machine.id)}
                                >
                                    <Card.Body>
                                        <div className="d-flex justify-content-between align-items-start mb-3">
                                            <div>
                                                <div className="d-flex align-items-center gap-2">
                                                    {getStatusIcon(machine.estado_operatividad)}
                                                    <h5 className="mb-0">{machine.codigo}</h5>
                                                </div>
                                                <p className="text-muted small mb-0">{machine.descripcion}</p>
                                            </div>
                                            <Badge 
                                                bg={
                                                    machine.estado_operatividad?.estado === 'OP' ? 'success' :
                                                    machine.estado_operatividad?.estado === 'MA' ? 'warning' :
                                                    'danger'
                                                }
                                            >
                                                {machine.estado_operatividad?.descripcion || 'Sin Estado'}
                                            </Badge>
                                        </div>
                                        
                                        <div className="machine-info">
                                            <div className="info-item">
                                                <span className="label">Tipos:</span>
                                                <MachineTypesBadge tipos={machine.tipos_maquina} />
                                            </div>
                                            <div className="info-item">
                                                <span className="label">Capacidad:</span>
                                                <span>{machine.capacidad_maxima || '0'}</span>
                                            </div>
                                            <div className="info-item">
                                                <span className="label">Disponible:</span>
                                                <Badge bg={machine.disponible ? 'success' : 'danger'}>
                                                    {machine.disponible ? 'Sí' : 'No'}
                                                </Badge>
                                            </div>
                                        </div>
                                    </Card.Body>
                                </Card>
                            </div>
                        ))
                    )}
                </div>

                {/* Componente de paginación */}
                <PaginationComponent />
            </Container>

            <MachineDetailsModal 
                show={showModal}
                onHide={() => setShowModal(false)}
                machine={selectedMachine}
                onUpdate={handleMachineUpdate}
            />
            <Footer />
        </div>
    );
}