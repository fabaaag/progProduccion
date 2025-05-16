import React, { useState, useEffect } from 'react';
import { Modal, Button, Table, Alert, Spinner } from 'react-bootstrap' ;
import { FaCheck, FaTimes, FaExclamationTriangle, FaArrowRight } from 'react-icons/fa';
import { previewFinalizarDia, finalizarDia } from '../../../api/programs.api';
import './css/FinalizarDiaModal.css';

const FinalizarDiaModal = ({
    show,
    onHide,
    programId,
    fecha,
    onFinalizacionExitosa
}) => {
    const [paso, setPaso] = useState('preview'); // preview, confirm, success
    const [cargando, setCargando] = useState(true);
    const [error, setError] = useState(null);
    const [datosPreview, setDatosPreview] = useState(null);
    const [resultado, setResultado] = useState(null);

    //Cargar previsualización al abrir
    useEffect(() => {
        if(show) {
            cargarPreview();
        }
    }, [show, programId, fecha]);

    const cargarPreview = async () => {
        try{
            setCargando(true);
            setError(null);
    
            // Convertir programId a número antes de enviarlo
            const datos = await previewFinalizarDia(parseInt(programId, 10), fecha);
            
            // Normalizar los IDs en la respuesta
            if (datos && datos.tareas_incompletas) {
                datos.tareas_incompletas = datos.tareas_incompletas.map(tarea => ({
                    ...tarea,
                    id: typeof tarea.id === 'string' && tarea.id.startsWith('item_') 
                        ? parseInt(tarea.id.split('_')[1]) 
                        : tarea.id
                }));
            }
            
            setDatosPreview(datos);
            setPaso('preview');
        } catch (error){
            console.error('Error obteniendo previsualización:', error);
            setError('No se pudo cargar la previsualización. Intente nuevamente.');
        } finally {
            setCargando(false);
        }
    };

    const confirmarFinalizacion = async () => {
        try {
            setCargando(true);
            setError(null);
            
            // Asegurarse de que las tareas no tengan IDs con formato "item_X_Y"
            if (datosPreview && datosPreview.tareas_incompletas) {
                // Normalizar los IDs de las tareas antes de enviarlas
                datosPreview.tareas_incompletas = datosPreview.tareas_incompletas.map(tarea => ({
                    ...tarea,
                    id: typeof tarea.id === 'string' && tarea.id.startsWith('item_') 
                        ? parseInt(tarea.id.split('_')[1]) 
                        : tarea.id
                }));
            }
            
            // Convertir programId a número antes de enviarlo}
            console.log(programId, 'id del programa que va hacia el comunicador api')
            const resultado = await finalizarDia(parseInt(programId, 10), fecha);
            console.log(resultado, 'er resultaou');
            setResultado(resultado);
            setPaso('success');
            
            // Notificar al componente padre que se finalizó exitosamente
            if (onFinalizacionExitosa) {
                onFinalizacionExitosa(resultado);
            }
        } catch (err) {
            console.error('Error finalizando día:', err);
            
            // Mostrar mensaje de error más detallado si está disponible
            const errorMsg = err.response?.data?.error || 'No se pudo finalizar el día. Por favor, inténtelo de nuevo.';
            setError(errorMsg);
            setPaso('preview'); // Volver a previsualización en caso de error
        } finally {
            setCargando(false);
        }
    };
    
    const resetearModal = () => {
        setPaso('preview');
        setDatosPreview(null);
        setResultado(null);
        setError(null);
        onHide();
    };
    
    const renderTablaPreview = () => {
        if (!datosPreview || !datosPreview.tareas_incompletas || datosPreview.tareas_incompletas.length === 0) {
            return (
                <Alert variant="success">
                    <FaCheck className="me-2" />
                    Todas las tareas del día están completadas. No es necesario crear continuaciones.
                </Alert>
            );
        }
        
        return (
            <>
                <Alert variant="warning">
                    <FaExclamationTriangle className="me-2" />
                    Las siguientes tareas no se han completado y se trasladarán al día siguiente:
                </Alert>
                <Table striped bordered hover responsive>
                    <thead>
                        <tr>
                            <th>OT</th>
                            <th>Proceso</th>
                            <th>% Completado</th>
                            <th>Unidades Programadas</th>
                            <th>Kg Programados</th>
                            <th>Kg Fabricados</th>
                            <th>Kg Pendientes</th>
                        </tr>
                    </thead>
                    <tbody>
                        {datosPreview.tareas_incompletas.map(tarea => (
                            <tr key={tarea.id}>
                                <td>{tarea.ot_codigo}</td>
                                <td>{tarea.proceso}</td>
                                <td>{tarea.porcentaje_completado.toFixed(1)}%</td>
                                <td>{tarea.cantidad_programada.toFixed(2)}</td>
                                <td>{tarea.kilos_programados.toFixed(2)}</td>
                                <td>{tarea.kilos_fabricados.toFixed(2)}</td>
                                <td>{tarea.kilos_restantes.toFixed(2)}</td>
                            </tr>
                        ))}
                    </tbody>
                </Table>
            </>
        );
    };
    
    const renderTablaResultado = () => {
        if (!resultado || !resultado.tareas_procesadas || resultado.tareas_procesadas.length === 0) {
            return (
                <Alert variant="info">
                    No se procesaron tareas para continuar al día siguiente.
                </Alert>
            );
        }
        
        return (
            <>
                <Alert variant="success">
                    <FaCheck className="me-2" />
                    Se han creado continuaciones para las siguientes tareas:
                </Alert>
                <Table striped bordered hover responsive>
                    <thead>
                        <tr>
                            <th>OT</th>
                            <th>Proceso</th>
                            <th>% Completado</th>
                            <th>Cant. Pendiente</th>
                            <th>Kg Pendientes</th>
                            <th>Fecha Continuación</th>
                        </tr>
                    </thead>
                    <tbody>
                        {resultado.tareas_procesadas.map(tarea => (
                            <tr key={tarea.id}>
                                <td>{tarea.ot_codigo}</td>
                                <td>{tarea.proceso}</td>
                                <td>{tarea.porcentaje_completado.toFixed(1)}%</td>
                                <td>{tarea.cantidad_restante}</td>
                                <td>{tarea.kilos_restantes.toFixed(2)}</td>
                                <td>{tarea.fecha_continuacion}</td>
                            </tr>
                        ))}
                    </tbody>
                </Table>
            </>
        );
    };
    
    const renderContenido = () => {
        if (cargando) {
            return (
                <div className="text-center my-4">
                    <Spinner animation="border" variant="primary" />
                    <p className="mt-2">Procesando datos...</p>
                </div>
            );
        }
        
        if (error) {
            return (
                <Alert variant="danger">
                    <FaTimes className="me-2" />
                    {error}
                </Alert>
            );
        }
        
        switch (paso) {
            case 'preview':
                return (
                    <>
                        <Modal.Body>
                            {renderTablaPreview()}
                        </Modal.Body>
                        <Modal.Footer>
                            <Button variant="secondary" onClick={resetearModal}>
                                Cancelar
                            </Button>
                            <Button 
                                variant="primary" 
                                onClick={() => setPaso('confirm')}
                                disabled={!datosPreview || datosPreview.tareas_incompletas.length === 0}
                            >
                                Continuar <FaArrowRight className="ms-1" />
                            </Button>
                        </Modal.Footer>
                    </>
                );
                
            case 'confirm':
                return (
                    <>
                        <Modal.Body>
                            <Alert variant="warning">
                                <h5><FaExclamationTriangle className="me-2" /> Confirmar finalización del día</h5>
                                <p>
                                    Está a punto de finalizar el día {fecha}. 
                                    Este proceso creará continuaciones para {datosPreview.tareas_incompletas.length} tareas incompletas 
                                    para el día {datosPreview.siguiente_dia}.
                                </p>
                                <p className="mb-0">
                                    <strong>Esta acción no se puede deshacer.</strong>
                                </p>
                            </Alert>
                        </Modal.Body>
                        <Modal.Footer>
                            <Button variant="secondary" onClick={() => setPaso('preview')}>
                                Volver
                            </Button>
                            <Button variant="danger" onClick={confirmarFinalizacion}>
                                <FaCheck className="me-1" /> Confirmar finalización
                            </Button>
                        </Modal.Footer>
                    </>
                );
                
            case 'success':
                return (
                    <>
                        <Modal.Body>
                            <Alert variant="success" className="mb-3">
                                <h5><FaCheck className="me-2" /> Día finalizado con éxito</h5>
                                <p className="mb-0">
                                    El día {fecha} ha sido finalizado correctamente. Se han creado continuaciones 
                                    para {resultado.total_tareas} tareas para el día {resultado.siguiente_dia}.
                                </p>
                            </Alert>
                            {renderTablaResultado()}
                        </Modal.Body>
                        <Modal.Footer>
                            <Button variant="primary" onClick={resetearModal}>
                                Cerrar
                            </Button>
                        </Modal.Footer>
                    </>
                );
                
            default:
                return null;
        }
    };
    
    return (
        <Modal
            show={show}
            onHide={resetearModal}
            backdrop="static"
            keyboard={!cargando}
            size="lg"
            centered
        >
            <Modal.Header closeButton={!cargando}>
                <Modal.Title>
                    {paso === 'preview' && `Finalizar día: ${fecha}`}
                    {paso === 'confirm' && `Confirmar finalización: ${fecha}`}
                    {paso === 'success' && `Día finalizado: ${fecha}`}
                </Modal.Title>
            </Modal.Header>
            {renderContenido()}
        </Modal>
    );
};

export default FinalizarDiaModal;