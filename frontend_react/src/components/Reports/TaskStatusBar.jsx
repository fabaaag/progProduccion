import React, { useMemo } from 'react';
import { ProgressBar } from 'react-bootstrap';
import { FaTasks, FaCheck, FaSpinner, FaPause } from 'react-icons/fa';
import './css/TaskStatusBar.css';

export const TaskStatusBar = ({ tasks }) => {
    
    const statusCounts = useMemo(() => {
        return tasks.reduce((acc, task) => {
            const estado = task.estado || 'Pendiente';
            acc[estado] = (acc[estado] || 0) + 1;
            return acc;
        }, {});
    }, [tasks]);

    const totalTareas = tasks.length;
    const completadas = statusCounts['Terminado'] || 0;
    const enProgreso = statusCounts['En Proceso'] || 0;
    const detenidas = statusCounts['Detenido'] || 0;
    const pendientes = statusCounts['Pendiente'] || 0;

    const calcularPorcentaje = (cantidad) => {
        return totalTareas > 0 ? (cantidad / totalTareas) * 100 : 0;
    };

    return (
        <div className="task-status-bar">
            <div className="status-summary">
                <div className="status-item">
                    <FaTasks className="status-icon total" />
                    <span className="status-label">Total Tareas:</span>
                    <span className="status-value">{totalTareas}</span>
                </div>
                <div className="status-item">
                    <FaCheck className="status-icon completed" />
                    <span className="status-label">Completadas:</span>
                    <span className="status-value">{completadas}</span>
                </div>
                <div className="status-item">
                    <FaSpinner className="status-icon in-progress" />
                    <span className="status-label">En Progreso:</span>
                    <span className="status-value">{enProgreso}</span>
                </div>
                <div className="status-item">
                    <FaPause className="status-icon stopped" />
                    <span className="status-label">Detenidas:</span>
                    <span className="status-value">{detenidas}</span>
                </div>
            </div>
            <ProgressBar className="mt-2">
                <ProgressBar 
                    variant="success"
                    now={calcularPorcentaje(completadas)}
                    key={1}
                    label={completadas > 0 ? `${completadas}` : ''}
                />
                <ProgressBar 
                    variant="primary"
                    now={calcularPorcentaje(enProgreso)}
                    key={2}
                    label={enProgreso > 0 ? `${enProgreso}` : ''}
                />
                <ProgressBar 
                    variant="danger"
                    now={calcularPorcentaje(detenidas)}
                    key={3}
                    label={detenidas > 0 ? `${detenidas}` : ''}
                />
                <ProgressBar 
                    variant="warning"
                    now={calcularPorcentaje(pendientes)}
                    key={4}
                    label={pendientes > 0 ? `${pendientes}` : ''}
                />
            </ProgressBar>
        </div>
    );
};