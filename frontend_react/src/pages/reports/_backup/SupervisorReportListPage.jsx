// frontend_react/src/pages/reports/SupervisorReportListPage.jsx
import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Badge, Button, Form, InputGroup } from 'react-bootstrap';
import { Link, useNavigate } from 'react-router-dom';
import { getAllSupervisorReports } from '../../../api/reports.api';
import CompNavbar from "../../../components/Navbar/CompNavbar";
import { Footer } from "../../../components/Footer/Footer";
import { LoadingSpinner } from "../../../components/UI/LoadingSpinner/LoadingSpinner";
import { toast } from "react-hot-toast";
import { FaCalendarAlt, FaUserCog, FaSearch, FaEye, FaFilter, FaTimes, FaLock } from 'react-icons/fa';
import './css/SupervisorReportListPage.css';

export function SupervisorReportListPage() {
    const [reports, setReports] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [filters, setFilters] = useState({
        estado: '',
        supervisor_id: ''
    });
    const navigate = useNavigate();
    
    useEffect(() => {
        fetchReports();
    }, [filters]);
    
    const fetchReports = async () => {
        try {
            setLoading(true);
            const data = await getAllSupervisorReports(filters);
            setReports(data);
        } catch (error) {
            setError(error.message);
            toast.error(`Error al cargar reportes: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };
    
    const handleFilterChange = (field, value) => {
        setFilters(prev => ({
            ...prev,
            [field]: value
        }));
    };
    
    const clearFilters = () => {
        setFilters({
            estado: '',
            supervisor_id: ''
        });
        setSearchTerm('');
    };
    
    // Filtrar por búsqueda de texto (local)
    const filteredReports = reports.filter(report => 
        report.programa_nombre.toLowerCase().includes(searchTerm.toLowerCase()) ||
        report.supervisor_nombre.toLowerCase().includes(searchTerm.toLowerCase())
    );
    
    if (loading) return <LoadingSpinner message="Cargando reportes..." />;
    
    return (
        <div className="supervisor-reports-page">
            <CompNavbar />
            <Container className="mt-4 mb-5">
                <div className="d-flex justify-content-between align-items-center mb-4">
                    <h2 className="page-title">Reportes de Supervisor</h2>
                    <Button 
                        variant="outline-secondary"
                        onClick={() => navigate('/programs')}
                    >
                        Volver a Programas
                    </Button>
                </div>
                
                <div className="filters-section mb-4">
                    <Card>
                        <Card.Body>
                            <Row>
                                <Col md={6}>
                                    <InputGroup className="mb-3">
                                        <InputGroup.Text><FaSearch /></InputGroup.Text>
                                        <Form.Control
                                            placeholder="Buscar por programa o supervisor..." 
                                            value={searchTerm}
                                            onChange={(e) => setSearchTerm(e.target.value)}
                                        />
                                        {searchTerm && (
                                            <Button 
                                                variant="outline-secondary"
                                                onClick={() => setSearchTerm('')}
                                            >
                                                <FaTimes />
                                            </Button>
                                        )}
                                    </InputGroup>
                                </Col>
                                <Col md={3}>
                                    <Form.Group>
                                        <Form.Label><FaFilter className="me-1" /> Estado</Form.Label>
                                        <Form.Select 
                                            value={filters.estado}
                                            onChange={(e) => handleFilterChange('estado', e.target.value)}
                                        >
                                            <option value="">Todos</option>
                                            <option value="ACTIVO">Activo</option>
                                            <option value="FINALIZADO">Finalizado</option>
                                            <option value="PAUSADO">Pausado</option>
                                        </Form.Select>
                                    </Form.Group>
                                </Col>
                                <Col md={3} className="d-flex align-items-end">
                                    <Button 
                                        variant="secondary" 
                                        onClick={clearFilters}
                                        className="w-100"
                                    >
                                        Limpiar Filtros
                                    </Button>
                                </Col>
                            </Row>
                        </Card.Body>
                    </Card>
                </div>
                
                {error && <div className="alert alert-danger">{error}</div>}
                
                <Row xs={1} md={2} lg={3} className="g-4">
                    {filteredReports.map(report => (
                        <Col key={report.id}>
                            <Card className={`report-card h-100 ${report.bloqueado ? 'report-card-locked' : ''}`}>
                                {report.bloqueado && (
                                    <div className="locked-badge">
                                        <FaLock /> Bloqueado
                                    </div>
                                )}
                                <Card.Body>
                                    <Card.Title>{report.programa_nombre}</Card.Title>
                                    <div className="report-meta">
                                        <div className="meta-item">
                                            <FaCalendarAlt className="meta-icon" />
                                            <span>{report.fecha_inicio} - {report.fecha_fin}</span>
                                        </div>
                                        <div className="meta-item">
                                            <FaUserCog className="meta-icon" />
                                            <span>{report.supervisor_nombre}</span>
                                        </div>
                                        <div className="meta-item">
                                            <Badge bg={
                                                report.estado === 'ACTIVO' ? 'primary' :
                                                report.estado === 'FINALIZADO' ? 'success' : 'warning'
                                            }>
                                                {report.estado}
                                            </Badge>
                                        </div>
                                    </div>
                                    
                                    <div className="completion-info mt-3">
                                        <div className="d-flex justify-content-between">
                                            <span>Progreso:</span>
                                            <Badge bg={
                                                report.porcentaje_completado >= 90 ? 'success' : 
                                                report.porcentaje_completado >= 70 ? 'primary' : 
                                                report.porcentaje_completado >= 50 ? 'info' : 
                                                report.porcentaje_completado >= 30 ? 'warning' : 'danger'
                                            }>
                                                {report.porcentaje_completado}%
                                            </Badge>
                                        </div>
                                        <div className="progress mt-2">
                                            <div 
                                                className={`progress-bar bg-${
                                                    report.porcentaje_completado >= 90 ? 'success' : 
                                                    report.porcentaje_completado >= 70 ? 'primary' : 
                                                    report.porcentaje_completado >= 50 ? 'info' : 
                                                    report.porcentaje_completado >= 30 ? 'warning' : 'danger'
                                                }`}
                                                style={{ width: `${report.porcentaje_completado}%` }}
                                            ></div>
                                        </div>
                                    </div>
                                </Card.Body>
                                <Card.Footer>
                                    <Link to={`/supervisor-reports/${report.id}`} className="btn btn-primary w-100">
                                        <FaEye className="me-2" />
                                        Ver Reporte
                                    </Link>
                                </Card.Footer>
                            </Card>
                        </Col>
                    ))}
                </Row>
                
                {filteredReports.length === 0 && (
                    <div className="text-center p-5">
                        <h4>No se encontraron reportes</h4>
                        <p>Intenta con otra búsqueda o crea un nuevo reporte</p>
                    </div>
                )}
            </Container>
            <Footer />
        </div>
    );
}