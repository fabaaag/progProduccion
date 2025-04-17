import React from 'react';
import { Col, Form } from 'react-bootstrap';
import FiltrosBase from '../../Shared/Filters/FiltrosBase';

const FiltrosPiezas = ({
    filtros,
    mostrarFiltrosAvanzados,
    setMostrarFiltrosAvanzados,
    handleInputChange,
    handleSearch,
    handleReset
}) => {
    return (
        <FiltrosBase
            filtros={filtros}
            handleInputChange={handleInputChange}
            handleSearch={handleSearch}
            handleReset={handleReset}
            mostrarFiltrosAvanzados={mostrarFiltrosAvanzados}
            setMostrarFiltrosAvanzados={setMostrarFiltrosAvanzados}
            titulo="Filtros de Piezas"
        >
            {/* Campos específicos para piezas */}
            <Col md={6} lg={4}>
                <Form.Group className="mb-3">
                    <Form.Label>Código</Form.Label>
                    <Form.Control
                        type="text"
                        name="codigo_pieza"
                        value={filtros.codigo_pieza}
                        onChange={handleInputChange}
                        placeholder="Filtrar por código"
                    />
                </Form.Group>
            </Col>

            <Col md={6} lg={4}>
                <Form.Group className="mb-3">
                    <Form.Label>Descripción</Form.Label>
                    <Form.Control
                        type="text"
                        name="descripcion"
                        value={filtros.descripcion}
                        onChange={handleInputChange}
                        placeholder="Filtrar por descripción"
                    />
                </Form.Group>
            </Col>
        </FiltrosBase>
    );
};

export default FiltrosPiezas;