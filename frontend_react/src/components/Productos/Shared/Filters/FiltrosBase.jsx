import React, { useState, useEffect } from 'react';
import { Form, Button, Row, Col, Card } from 'react-bootstrap';
import { FaSearch, FaFilter, FaTimes } from 'react-icons/fa';
import { 
    getFamilias,
    getSubfamilias    
} from '../../../../api/productos.api';

const FiltrosBase = ({
    filtros,
    handleInputChange,
    handleSearch,
    handleReset,
    mostrarFiltrosAvanzados,
    setMostrarFiltrosAvanzados,
    children, // Contenido adicional específico para cada tipo
    titulo = "Filtros de búsqueda",
    tipo = "productos"
}) => {

    const [familias, setFamilias] = useState([]);
    const [subfamilias, setSubfamilias] = useState([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        cargarFamilias();
    }, [tipo]);

    useEffect(() => {
        if (filtros.familia_codigo){
            cargarSubfamilias(filtros.familia_codigo);
        }else {
            setSubfamilias([]);
        }
    }, [filtros.familia_codigo]);

    const cargarFamilias = async () => {
        try {
            setLoading(true);
            const response = await getFamilias({ tipo });
            setFamilias(response);
        } catch (error) {
            console.error('Error al cargar familias:' , error);
        } finally {
            setLoading(false);
        }
    };

    const cargarSubfamilias = async (familiaCodigo) => {
        try {
            setLoading(true);
            const response = await getSubfamilias({
                familia_codigo: familiaCodigo,
                tipo
            });
            setSubfamilias(response);
        } catch (error) {
            console.error('Error al cargar subfamilias:', error);
        } finally {
            setLoading(false);
        }
    }


    return (
        <Card className="mb-4 filtros-card">
            <Card.Header className="d-flex justify-content-between align-items-center">
                <h6 className="mb-0">
                    <FaFilter className="me-2" />
                    {titulo}
                </h6>
                <Button 
                    variant="link"
                    className="p-0 text-decoration-none"
                    onClick={() => setMostrarFiltrosAvanzados(!mostrarFiltrosAvanzados)}
                >
                    {mostrarFiltrosAvanzados ? 'Ocultar filtros avanzados': ' Mostrar filtros avanzados'}
                </Button>
            </Card.Header>
            <Card.Body>
                <Form onSubmit={handleSearch}>
                    {/*Búsqueda rápida*/}
                    <Row className="mb-3">
                        <Col>
                            <Form.Group className="mb-0">
                                <Form.Control 
                                    type="text"
                                    placeholder="Buscar..."
                                    name="search"
                                    value={filtros.search}
                                    onChange={handleInputChange}
                                />
                            </Form.Group>
                        </Col>
                        <Col xs="auto">
                            <div className="d-flex gap-2">
                                <Button type="submit" variant="primary">
                                    <FaSearch className="me-1" /> Buscar
                                </Button>
                                <Button
                                    type="button"
                                    variant="outline-secondary"
                                    onClick={handleReset}
                                >
                                    <FaTimes className="me-1" /> Limpiar
                                </Button>
                            </div>
                        </Col>
                    </Row>
                    {/* Filtros avanzados */}
                    {mostrarFiltrosAvanzados && (
                        <div className="filtros-avanzados mt-3">
                            <hr className="my-3" />
                            <h6 className="mb-3">Filtros Avanzados</h6>
                            <Row className="mb-3">
                                <Col md={6} lg={4}>
                                    <Form.Group className="mb-3">
                                        <Form.Label>Familia</Form.Label>
                                        <Form.Select
                                            name="familia_codigo"
                                            value={filtros.familia_codigo || ''}
                                            onChange={handleInputChange}
                                            disabled={loading} 
                                        >
                                            <option value="">Seleccione una familia</option>
                                            {familias.map(familia => (
                                                <option key={familia.id} value={familia.codigo_familia}>
                                                    {familia.descripcion}
                                                </option>
                                            ))}
                                        </Form.Select>
                                    </Form.Group>
                                </Col>
                                <Col md={6} lg={4}>
                                    <Form.Group className="mb-3">
                                        <Form.Label>Subfamilia</Form.Label>
                                        <Form.Select
                                            name="subfamilia_codigo"
                                            value={filtros.subfamilia_codigo || ''}
                                            onChange={handleInputChange}
                                            disabled={!filtros.familia_codigo || loading} 
                                        >
                                            <option value="">Seleccione una subfamilia</option>
                                            {subfamilias.map(subfamilia => (
                                                <option key={subfamilia.id} value={subfamilia.codigo_subfamilia}>
                                                    {subfamilia.descripcion}
                                                </option>
                                            ))}
                                        </Form.Select>
                                    </Form.Group>
                                </Col>
                                {/* Contenido específico para cada tipo */}
                                {children}
                            </Row>
                        </div>
                    )}
                </Form>
            </Card.Body>
        </Card>
    );
};

export default FiltrosBase;