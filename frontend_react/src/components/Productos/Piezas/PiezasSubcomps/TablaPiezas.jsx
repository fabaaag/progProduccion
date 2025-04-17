import React from 'react';
import { Table, Badge, Button } from 'react-bootstrap';
import { FaFileAlt } from 'react-icons/fa';
import TablaBase from '../../Shared/Tables/TablaBase.jsx';

const TablaPiezas = ({ piezas, handleVerDetalles }) => {
    const columns = [
        { key: 'codigo_pieza', label: 'Código', style: {width: '15%'} },
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
        
    ];

    const renderActions = (pieza) => (
        <Button
            variant="primary"
            size="sm"
            onClick={() => handleVerDetalles(pieza)} 
        >
            <FaFileAlt className="me-1" /> Ficha Técnica
        </Button>
    )


    return (
        <TablaBase
            columns={columns}
            data={piezas}
            renderActions={renderActions}
            emptyMessage="No se encontraron piezas"
        />
    );
};

export default TablaPiezas;