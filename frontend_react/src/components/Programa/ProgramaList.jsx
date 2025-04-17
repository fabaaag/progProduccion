import { useEffect, useState, useMemo } from "react";
import { getAllPrograms, deleteProgram } from "../../api/programs.api.js";
import CompNavbar from "../Navbar/CompNavbar.jsx";
import { useNavigate } from "react-router-dom";
import { Link } from "react-router-dom";
import { Button, Modal, Card, Badge, Form, InputGroup } from "react-bootstrap";
import { toast } from "react-hot-toast";
import { FaSearch, FaCalendarAlt, FaClock, FaTrash, FaEye, FaPlus } from 'react-icons/fa';
import './css/ProgramaList.css';

export function ProgramaList(){
    const [programs, setPrograms] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const [programToDelete, setProgramToDelete] = useState(null);
    const [searchTerm, setSearchTerm] = useState("");
    const navigate = useNavigate();

    // Cargar programas
    useEffect(() => {
        loadPrograms();
    }, []);

    const loadPrograms = async () => {
        try {
            setLoading(true);
            const res = await getAllPrograms();
            setPrograms(res.data);
        } catch (error) {
            toast.error(`Error al cargar los programas: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    // Filtrar programas
    const filteredPrograms = useMemo(() => {
        return programs.filter(program => 
            program.nombre.toLowerCase().includes(searchTerm.toLowerCase())
        );
    }, [programs, searchTerm]);

    // Calcular estado del programa
    const getProgramStatus = (fechaInicio, fechaFin) => {
        const now = new Date();
        const start = new Date(fechaInicio);
        const end = new Date(fechaFin);

        if (now < start) return { text: 'Pendiente', color: 'warning' };
        if (now > end) return { text: 'Finalizado', color: 'secondary' };
        return { text: 'En Proceso', color: 'success' };
    };

    // Calcular días restantes
    const getDaysRemaining = (fechaFin) => {
        const now = new Date();
        const end = new Date(fechaFin);
        const diff = end - now;
        const days = Math.ceil(diff / (1000 * 60 * 60 * 24));
        return days;
    };

    const handleDelete = async (programId) => {
        try{
            await deleteProgram(programId);
            setPrograms(programs.filter(program => program.id !== programId));
            toast.success('Programa eliminado correctamente');
        }catch(error){
            console.error('Error al eliminar el programa:', error);
            toast.error('Error al eliminar el programa');
        }
        setShowDeleteModal(false);
    };

    if (loading) {
        return (
            <div className="loading-container">
                <div className="spinner-border text-primary" role="status">
                    <span className="visually-hidden">Cargando...</span>
                </div>
                <p>Cargando Programas de Producción</p>
            </div>
        );
    }

    return(
        <div className="bg-light min-vh-100">
            <CompNavbar />
            <div className="container py-4">
                {/* Header Section */}
                <div className="d-flex justify-content-between align-items-center mb-4">
                    <div>
                        <h1 className="h3 mb-0">Programas de Producción</h1>
                        <p className="text-muted">Total: {programs.length} programas</p>
                    </div>
                    <div className="d-flex gap-2">
                        <Button 
                            variant="outline-primary" 
                            onClick={() => navigate('/')}
                        >
                            Volver al inicio
                        </Button>
                        <Link 
                            to='/programs-create' 
                            className="btn btn-success d-flex align-items-center gap-2"
                        >
                            <FaPlus /> Crear Programa
                        </Link>
                    </div>
                </div>

                {/* Search Section */}
                <Card className="mb-4 shadow-sm">
                    <Card.Body>
                        <InputGroup className="search-input-group">
                            <div className="search-icon">
                                <FaSearch />
                            </div>
                            <Form.Control
                                className="search-input"
                                placeholder="Buscar programa..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                            />
                        </InputGroup>
                    </Card.Body>
                </Card>

                {/* Programs Grid */}
                <div className="row g-4">
                    {filteredPrograms.map(program => {
                        const status = getProgramStatus(program.fecha_inicio, program.fecha_fin);
                        const daysRemaining = getDaysRemaining(program.fecha_fin);
                        
                        return (
                            <div key={program.id} className="col-md-6 col-lg-4">
                                <Card className="h-100 shadow-sm program-card">
                                    <Card.Body>
                                        <div className="d-flex justify-content-between align-items-start mb-3">
                                            <div>
                                                <h5 className="mb-1">{program.nombre}</h5>
                                                <Badge bg={status.color}>{status.text}</Badge>
                                            </div>
                                            <div className="program-actions">
                                                <Button 
                                                    variant="light"
                                                    size="sm"
                                                    onClick={() => navigate(`/programs/${program.id}`)}
                                                    className="me-2"
                                                >
                                                    <FaEye />
                                                </Button>
                                                <Button 
                                                    variant="danger"
                                                    size="sm"
                                                    onClick={() => {
                                                        setProgramToDelete(program);
                                                        setShowDeleteModal(true);
                                                    }}
                                                >
                                                    <FaTrash />
                                                </Button>
                                            </div>
                                        </div>
                                        
                                        <div className="program-dates mb-3">
                                            <div className="date-item">
                                                <FaCalendarAlt className="icon" />
                                                <div>
                                                    <small className="text-muted">Inicio</small>
                                                    <p className="mb-0">{program.fecha_inicio}</p>
                                                </div>
                                            </div>
                                            <div className="date-item">
                                                <FaClock className="icon" />
                                                <div>
                                                    <small className="text-muted">Término</small>
                                                    <p className="mb-0">{program.fecha_fin}</p>
                                                </div>
                                            </div>
                                        </div>

                                        <div className="program-footer">
                                            <small className="text-muted">
                                                {daysRemaining > 0 
                                                    ? `${daysRemaining} días restantes`
                                                    : 'Programa finalizado'}
                                            </small>
                                            <div className="progress" style={{height: "4px"}}>
                                                <div 
                                                    className="progress-bar" 
                                                    style={{
                                                        width: `${Math.max(0, Math.min(100, 100 - (daysRemaining * 100 / 30)))}%`
                                                    }}
                                                />
                                            </div>
                                        </div>
                                    </Card.Body>
                                </Card>
                            </div>
                        );
                    })}
                </div>

                {/* Delete Modal */}
                <Modal show={showDeleteModal} onHide={() => setShowDeleteModal(false)}>
                    <Modal.Header closeButton>
                        <Modal.Title>Confirmar Eliminación</Modal.Title>
                    </Modal.Header>
                    <Modal.Body>
                        ¿Estás seguro de que deseas eliminar el programa "{programToDelete?.nombre}"?
                        <br />
                        <small className="text-danger">Esta acción no se puede deshacer.</small>
                    </Modal.Body>
                    <Modal.Footer>
                        <Button variant="secondary" onClick={() => setShowDeleteModal(false)}>
                            Cancelar
                        </Button>
                        <Button 
                            variant="danger" 
                            onClick={() => {
                                handleDelete(programToDelete.id);
                                setShowDeleteModal(false);
                            }}
                        >
                            Eliminar
                        </Button>
                    </Modal.Footer>
                </Modal>
            </div>
        </div>
    );
}