import React from 'react';
import { Alert, Badge } from 'react-bootstrap';
import { FaExclamationTriangle, FaClock, FaIndustry, FaTools } from 'react-icons/fa';
import { LoadingSpinner } from '../../../../UI/LoadingSpinner/LoadingSpinner';
import '../css/RutaFabricacion.css';

export const RutaFabricacionTab = ({
    rutas,
    tipo = 'producto',
    loadingRutas = false
}) => {
    if (!rutas || rutas.length === 0){
        return (
            <Alert variant="warning">
                <FaExclamationTriangle className="me-2" />
                {`Este ${tipo} no tiene rutas de fabricación definidas.`}
            </Alert>
        );
    }

    if (loadingRutas) {
        return (
            <div className="text-center py-4">
                <LoadingSpinner message="Cargando rutas de fabricación..." size="small" />
            </div>
        );
    }

    //Ordenar rutas por número de etapa
    const rutasOrdenadas = [...rutas].sort((a, b) => a.nro_etapa - b.nro_etapa);

    return (
        <div className="ruta-fabricacion-container">
            {/* Resumen de la ruta */}
            <div className="route-summary mb-4">
                <div className="summary-item">
                    <h5><FaClock className="icon" /> Tiempo Total</h5>
                    <div className="summary-value">
                        {rutasOrdenadas.reduce((total, ruta) => total + (ruta.estandar || 0), 0)} minutos
                    </div>
                </div>
                <div className="summary-item">
                    <h5><FaIndustry className="icon" /> Máquinas</h5>
                    <div className="summary-value">
                        {new Set(rutasOrdenadas.map(ruta => ruta.maquina?.id)).size}
                    </div>
                </div>
                <div className="summary-item">
                    <h5><FaTools className="icon" /> Etapas</h5>
                    <div className="summary-value">
                        {rutasOrdenadas.length}
                    </div>
                </div>
            </div>

            {/* Ruta de Procesos (estilo similar a Orders*/}
            <h5 className="section-title">Secuencia de Fabricación</h5>
            <div className="process-timeline">
                {rutasOrdenadas.map((ruta) => (
                    <div key={`ruta-${ruta.nro_etapa}`} className="process-item">
                        <div className="process-number">
                            {ruta.nro_etapa}
                            </div>
                        <div className="process-content">
                            <h6>
                            {ruta.proceso?.descripcion || 'Proceso'}
                            </h6>
                            <div className="process-detail">
                                <span className="machine">
                                    <FaIndustry className="icon" />
                                    {ruta.maquina?.descripcion || 'Máquina'}
                                </span>
                                <span className="standard">
                                    <FaClock className="icon" />
                                    {ruta.estandar || 0} min
                                </span>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};