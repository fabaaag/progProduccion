import React from 'react';
import { Badge, Button } from 'react-bootstrap';
import { FaFileAlt } from 'react-icons/fa';
import TablaBase from '../../Shared/Tables/TablaBase';

const TablaProductos = ({ productos, handleVerDetalles }) => {
    const columns = [
        { key: 'codigo_producto', label: 'Código', style: {width: '15%'} },
        { key: 'descripcion', label: 'Descripcion', style: {width: '25%'}},
        {
            key: 'familia_producto',
            label: 'Familia',
            style: { width: '15%' },
            render: (val) => val?.descripcion || '-'
        },
        {
            key: 'subfamilia_producto',
            label: 'Subfamilia',
            style: { width: '15%' },
            render: (val) => val?.descripcion || '-'
        },
        {
            key: 'peso_unitario',
            label: 'Peso',
            style: { width: '10%' },
            render: (val) => parseFloat(val).toFixed(4)
        },
        {
            key: 'und_medida',
            label: 'Unidad Medida',
            style: { width: '10%' },
            render: (val) => val?.nombre || '-'
        },
        {
            key: 'armado',
            label: 'Armado',
            style: { width: '10%' },
            render: (val) => (
                <Badge bg={val ? 'success' : 'secondary'} pill>
                    {val ? 'Si' : 'No'}
                </Badge>
            )
        },
    ];

    const renderActions = (producto) => (
        <Button
            variant="primary"
            size="sm"
            onClick={() => handleVerDetalles(producto)} 
        >
            <FaFileAlt className="me-1" /> Ficha Técnica
        </Button>
    )


    return (
        <TablaBase
            columns={columns}
            data={productos}
            renderActions={renderActions}
            emptyMessage="No se encontraron productos"
        />
    );
};

export default TablaProductos;