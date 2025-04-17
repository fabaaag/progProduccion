import React from 'react';
import { Row, Col, Table, Badge, Alert } from 'react-bootstrap';
import { FaFileAlt, FaExclamationTriangle } from 'react-icons/fa';

export const InfoGeneralTab = ({ item, tipo = 'producto'}) =>{
    // Determinar el código según el tipo
    const codigo = tipo === 'producto' ? item.codigo_producto : item.codigo_pieza;

    return (
        <div className="info-container">
            <Row>
                <Col md={6}>
                    <div className="info-section">
                        <h5 className="border-bottom pb-2 mb">Datos Principales</h5>
                        <Table bordered striped hover size="sm">
                            <tbody>
                                <tr>
                                    <th width="40%">Código</th>
                                    <td>{codigo}</td>
                                </tr>
                                <tr>
                                    <th>Descripción</th>
                                    <td>{item.descripcion}</td>
                                </tr>
                                <tr>
                                    <th>Familia</th>
                                    <td>{item.familia_producto?.descripcion || '-'}</td>
                                </tr>
                                <tr>
                                    <th>Subfamilia</th>
                                    <td>{item.subfamilia_producto?.descripcion || '-'}</td>
                                </tr>
                                <tr>
                                    <th>Peso Unitario</th>
                                    <td>{parseFloat(item.peso_unitario).toFixed(4)} {item.und_medida?.nombre || ''}</td>
                                </tr>

                                {/* Campo específico para productos */}
                                {tipo === 'producto' && (
                                    <tr>
                                        <th>Armado</th>
                                        <td>
                                            <Badge bg={item.armado ? 'success' : 'secondary'}>
                                                {item.armado ? 'Sí' : 'No'}
                                            </Badge>
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </Table>
                    </div>
                </Col>
                <Col md={6}>
                {item.ficha_tecnica ? (
                    <div className="info-section">
                        <h5 className="border-bottom pb-2-mb-3">Ficha Técnica</h5>
                        <Table bordered striped hover size="sm">
                            <tbody>
                                <tr>
                                    <th width="40%">Tipo</th>
                                    <td>{item.ficha_tecnica.tipo_producto?.nombre || '-'}</td>
                                </tr>
                                <tr>
                                    <th>Largo Hilo</th>
                                    <td>{item.ficha_tecnica.largo_hilo}</td>
                                </tr>
                                <tr>
                                    <th>Hilos por Pulgada</th>
                                    <td>{item.ficha_tecnica.hilos_por_pulgada}</td>
                                </tr>
                                <tr>
                                    <th>Terminación</th>
                                    <td>{item.ficha_tecnica.terminacion_ficha?.nombre || '-'}</td>
                                </tr>
                                <tr>
                                    <th>Materia Prima</th>
                                    <td>{item.ficha_tecnica.materia_prima?.descripcion || '-'}</td>
                                </tr>
                                <tr>
                                    <th>Largo a Cortar</th>
                                    <td>{item.ficha_tecnica.largo_cortar || '-'}</td>
                                </tr>
                            </tbody>
                        </Table>

                        {item.ficha_tecnica.observacion_ficha && (
                            <div className="mt-3">
                                <h6>Observaciones</h6>
                                <Alert variant="light" className="p-2 observaciones-alert">
                                    {item.ficha_tecnica.observacion_ficha}
                                </Alert>
                            </div>
                        )}

                        {item.ficha_tecnica.plano_ficha && (
                            <div className="mt-3 text-center">
                                <a
                                    className="btn btn-outline-primary"
                                    href={item.ficha_tecnica.plano_ficha}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                >
                                    <FaFileAlt className="me-1" /> Ver Plano Técnico
                                </a>
                            </div>
                        )}
                    </div>
                ):(
                    <Alert variant="warning">
                        <FaExclamationTriangle className="me-2" />
                        {`${tipo === 'pieza' ? 'Esta' : 'Este'} ${tipo} no tiene ficha técnica asociada.`}
                    </Alert>
                )}
                </Col>
            </Row>
        </div>
    );
};

export default InfoGeneralTab;