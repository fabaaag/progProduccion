import React from 'react';
import { Col, Form } from 'react-bootstrap';
import FiltrosBase from '../../Shared/Filters/FiltrosBase';

const FiltrosProductos = ({
    filtros,
    mostrarFiltrosAvanzados,
    setMostrarFiltrosAvanzados,
    handleInputChange,
    handleSearch,
    handleReset
}) => {

    //Campos específicos para productos
    const camposEspecificos = (
        <>
            <Col md={6} lg={4}>
                <Form.Group className="mb-3">
                    <Form.Label>Código Producto</Form.Label>
                    <Form.Control
                        type="text"
                        placeholder="Código de producto"
                        name="codigo_producto"
                        value={filtros.codigo_producto || ''}
                        onChange={handleInputChange}
                    />
                </Form.Group>
            </Col>
            <Col md={6} lg={4}>
                <Form.Group className="mb-3">
                    <Form.Control 
                        type="text"
                        placeholder="Descripción"
                        name="descripcion"
                        value={filtros.descripcion || ''}
                        onChange={handleInputChange}
                    />
                </Form.Group>
            </Col>
            <Col md={6} lg={4}>
                <Form.Group className='mb-3'>
                    <Form.Label>Armado</Form.Label>
                    <Form.Select
                        name="armado"
                        value={filtros.armado || ''}
                        onChange={handleInputChange}
                    >
                        <option value="">Todos</option>
                        <option value="true">Sí</option>
                        <option value="false">No</option>

                    </Form.Select>

                </Form.Group>
            </Col>
        </>
    )
    return (
       <FiltrosBase 
        filtros={filtros}
        handleInputChange={handleInputChange}
        handleSearch={handleSearch}
        handleReset={handleReset}
        mostrarFiltrosAvanzados={mostrarFiltrosAvanzados}
        setMostrarFiltrosAvanzados={setMostrarFiltrosAvanzados}
        titulo='Filtros de Productos'
        tipo="productos"
       >
        {camposEspecificos}
       </FiltrosBase>
    );
};

export default FiltrosProductos;