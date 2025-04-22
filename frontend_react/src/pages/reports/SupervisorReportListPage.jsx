import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Badge, Button } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import { getAllSupervisorReports } from '../../api/reports.api';
import CompNavbar from '../../components/Navbar/CompNavbar';
import { Footer } from '../../components/Footer/Footer';
import { LoadingSpinner } from '../../components/UI/LoadingSpinner/LoadingSpinner';
import { FaCalendarAlt, FaUserCog, FaSearch, FaEye } from 'react-icons/fa';
import './css/SupervisorReportListPage.css';

export function SupervisorReportListPage() {
    const [reports, setReports] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        fetchReports();
    }, []);

    const fetchReports = async () => {
        try {
            setLoading(true);
            const data = await getAllSupervisorReports();
            setReports(data);
        } catch (error) {
            setError(error.message);
        } finally {
            setLoading(false);
        }
    };

    const filteredReports = reports.filter(report => 
        report.programa_nombre.toLowerCase().includes(searchTerm.toLowerCase()) ||
        report.supervisor_nombre.toLowerCase().includes(searchTerm.toLowerCase())
    );
    
    if (loading) return <LoadingSpinner message="Cargando reportes..." />;

    return (
        <div className="supervisor-reports-page">
            <CompNavbar />
            <Container className="mt-4 mb-5">
                <h2 className="page-title mb-4">Reportes de Supervisor</h2>

                <div className="search-bar mb-4">
                    <div className="input-group">
                        <span className="input-group-text"><FaSearch /></span>
                        <input 
                            type="text" 
                            className="form-control" 
                            placeholder="Buscar por programa o supervisor"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                </div>

                {error && <div className="alert alert-danger">{error}</div>}

                <Row xs={1} md={2} lg={3} className="g-4">
                    {filteredReports.map(report => (
                        <Col key={report.id}>
                            <Card className="report-card h-100">
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
                                    </div>
                                    <div className="completion-info mt-3">
                                        <div className="d-flex justify-content-betweem">
                                            <span>Progreso: </span>
                                            <Badge bg={
                                                report.porcentaje_completado >= 90 ? 'success':
                                                report.porcentaje_completado >= 70 ? 'warning':
                                                report.porcentaje_completado >= 50 ? 'info':
                                                report.porcentaje_completado >= 30 ? 'warning': 'danger'
                                            }>
                                                {report.porcentaje_completado}%
                                            </Badge>
                                        </div>
                                        <div className="progress mt-2">
                                            <div className={`progress-bar bg-${
                                                report.porcentaje_completado >= 90 ? 'success':
                                                report.porcentaje_completado >= 70 ? 'warning':
                                                report.porcentaje_completado >= 50 ? 'info':
                                                report.porcentaje_completado >= 30 ? 'warning': 'danger'
                                            }`}
                                            style={{ width: `${report.porcentaje_completado}%`}}
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
};