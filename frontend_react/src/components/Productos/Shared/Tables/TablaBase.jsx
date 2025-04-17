import React from 'react';
import { Table, Badge } from 'react-bootstrap';
import '../css/TablaBase.css';

const TablaBase = ({
    columns, 
    data,
    renderActions,
    emptyMessage = "No se encontraron registros"
}) => {
    return (
        <div className="table-responsive">
            <Table hover responsive className="tabla-base">
                <thead className="table-primary">
                    <tr>
                        {columns.map(col => (
                            <th key={col.key} style={col.style}>{col.label}</th>
                        ))}
                        {renderActions && <th>Acciones</th>}
                    </tr>
                </thead>
                <tbody>
                    {data.length > 0 ? (
                        data.map((item, index) => (
                            <tr key={item.id || item.codigo_producto || item.codigo_pieza || item.codigo_pieza || index}>
                                {columns.map(col => (
                                    <td key={`${index}-${col.key}`} style={col.cellStyle}>
                                        {col.render ? col.render(item[col.key], item) : item[col.key]}
                                    </td>
                                ))}
                                {renderActions && (
                                    <td className="text-center">{renderActions(item)}</td>
                                )}
                            </tr>
                        ))
                    ) :(
                        <tr>
                            <td colSpan={columns.length + (renderActions ? 1 : 0)} className="text-center">
                                {emptyMessage}
                            </td>
                        </tr>
                    )}
                </tbody>
            </Table>
        </div>
    );
};

export default TablaBase;