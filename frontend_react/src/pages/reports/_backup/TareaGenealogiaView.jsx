// Crear archivo: frontend_react/src/components/Tarea/TareaGenealogiaView.jsx

import React, { useState, useEffect } from 'react';
import { Card, Table, Badge, ProgressBar, Spinner, Alert } from 'react-bootstrap';
import { FaCodeBranch, FaExclamationCircle } from 'react-icons/fa';
import { obtenerGenealogiaTask } from '../../../api/programs.api';
import './css/TareaGenealogiaView.css'; // Crearemos este archivo después

const TareaGenealogiaView = ({ tareaSeleccionada }) => {
    const [cargando, setCargando] = useState(true);
    const [error, setError] = useState(null);
    const [genealogia, setGenealogia] = useState(null);
    
    useEffect(() => {
        if (tareaSeleccionada) {
            cargarGenealogia();
        }
    }, [tareaSeleccionada]);
    
    const cargarGenealogia = async () => {
        try {
            setCargando(true);
            setError(null);
            
            // Determinar qué ID usar:
            let idConsulta = tareaSeleccionada.id;
            
            console.log("ID original de la tarea:", idConsulta);
            
            // Si es una continuación, usar el ID de la tarea original
            if (tareaSeleccionada.es_continuacion && tareaSeleccionada.tarea_original_id) {
                idConsulta = tareaSeleccionada.tarea_original_id;
                console.log("Usando ID de tarea original:", idConsulta);
            } else if (tareaSeleccionada.tiene_fragmentos) {
                // Es una tarea original, usar el proceso_id como ID real
                // Ya que el ID actual puede ser un ID generado por ReactSortable
                if (tareaSeleccionada.proceso_id) {
                    idConsulta = tareaSeleccionada.proceso_id;
                    console.log("Usando proceso_id como ID real:", idConsulta);
                }
            }
            
            // Extraer el número real en caso de IDs con formato item_X_Y
            let idNumerico;
            if (typeof idConsulta === 'string' && idConsulta.startsWith('item_')) {
                // Extraer el primer número después de 'item_'
                const match = idConsulta.match(/item_(\d+)/);
                if (match && match[1]) {
                    idNumerico = parseInt(match[1], 10);
                    console.log("ID extraído del formato item_X_Y:", idNumerico);
                } else {
                    throw new Error(`No se pudo extraer el ID numérico de: ${idConsulta}`);
                }
            } else {
                idNumerico = parseInt(idConsulta, 10);
            }
            
            if (isNaN(idNumerico)) {
                throw new Error(`ID de tarea inválido: ${idConsulta}`);
            }
            
            console.log("ID numérico final para consulta:", idNumerico);
            const datos = await obtenerGenealogiaTask(idNumerico);
            setGenealogia(datos);
        } catch (err) {
            console.error('Error cargando genealogía:', err);
            setError(`No se pudo cargar la genealogía: ${err.message}`);
        } finally {
            setCargando(false);
        }
    };
    
    const obtenerColorEstado = (porcentaje) => {
        if (porcentaje >= 100) return 'success';
        if (porcentaje >= 70) return 'info';
        if (porcentaje >= 30) return 'warning';
        return 'danger';
    };
    
    const renderFragmentoRecursivo = (fragmento, nivel = 0) => {
        // Calcular indentación para visualizar jerarquía
        const indentacion = nivel * 20;
        
        return (
            <React.Fragment key={fragmento.id}>
                <tr className={fragmento.es_continuacion ? 'continuacion-row' : 'original-row'}>
                    <td style={{ paddingLeft: `${indentacion}px` }}>
                        {fragmento.es_continuacion ? '↳' : ''} {fragmento.fecha}
                    </td>
                    <td>
                        <Badge bg={fragmento.es_continuacion ? 'secondary' : 'primary'}>
                            {fragmento.es_continuacion ? 'Continuación' : 'Original'}
                        </Badge>
                    </td>
                    <td>{parseFloat(fragmento.cantidad_asignada || 0).toFixed(2)} kg</td>
                    <td>{parseFloat(fragmento.cantidad_completada || 0).toFixed(2)} kg</td>
                    <td>
                        <ProgressBar 
                            now={parseFloat(fragmento.porcentaje_completado || 0)} 
                            variant={obtenerColorEstado(parseFloat(fragmento.porcentaje_completado || 0))}
                            label={`${(parseFloat(fragmento.porcentaje_completado || 0)).toFixed(1)}%`}
                        />
                    </td>
                </tr>
                
                {/* Renderizar continuaciones de forma recursiva */}
                {fragmento.continuaciones && fragmento.continuaciones.map(cont => 
                    renderFragmentoRecursivo(cont, nivel + 1)
                )}
            </React.Fragment>
        );
    };
    
    if (cargando) {
        return (
            <div className="text-center my-4">
                <Spinner animation="border" variant="primary" />
                <p className="mt-2">Cargando genealogía de la tarea...</p>
            </div>
        );
    }
    
    if (error) {
        return (
            <Alert variant="danger">
                <FaExclamationCircle className="me-2" />
                {error}
            </Alert>
        );
    }
    
    if (!genealogia || !genealogia.genealogia) {
        return (
            <Alert variant="info">
                Esta tarea no tiene historial de fragmentación.
            </Alert>
        );
    }
    
    return (
        <div className="tarea-genealogia">
            <Card className="mb-3">
                <Card.Header>
                    <div className="d-flex justify-content-between align-items-center">
                        <h5 className="mb-0">
                            <FaCodeBranch className="me-2" />
                            Historial de Tarea
                        </h5>
                        <Badge bg="primary" pill>
                            Progreso Global: {genealogia.progreso_global.toFixed(1)}%
                        </Badge>
                    </div>
                </Card.Header>
                <Card.Body>
                    <div className="tarea-info mb-3">
                        <h6>Tarea Original:</h6>
                        <p>
                            <strong>Proceso:</strong> {genealogia.tarea_original.proceso}<br />
                            <strong>Máquina:</strong> {genealogia.tarea_original.maquina}<br />
                            <strong>Cantidad Total:</strong> {genealogia.tarea_original.cantidad_total.toFixed(2)} kg
                        </p>
                    </div>
                    
                    <div className="table-responsive">
                        <Table striped hover>
                            <thead>
                                <tr>
                                    <th>Fecha</th>
                                    <th>Tipo</th>
                                    <th>Asignado</th>
                                    <th>Completado</th>
                                    <th>Progreso</th>
                                </tr>
                            </thead>
                            <tbody>
                                {renderFragmentoRecursivo(genealogia.genealogia)}
                            </tbody>
                        </Table>
                    </div>
                </Card.Body>
            </Card>
        </div>
    );
};

export default TareaGenealogiaView;