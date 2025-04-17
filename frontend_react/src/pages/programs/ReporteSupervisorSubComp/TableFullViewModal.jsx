import React from 'react';
import { Modal, Button, Table } from 'react-bootstrap';
import { FaTimes } from 'react-icons/fa';
import moment from 'moment';
import './css/TableFullViewModal.css';

const TableFullViewModal = ({
    show,
    onHide,
    tasks,
    currentDate,
    taskStates,
    kilosFabricados,
    porcentajeCumplimiento
}) => {
    return (
        <Modal
            show={show}
            onHide={onHide}
            dialogClassName="modal-xl"
            contentClassName="table-modal-content"
        >
            <Modal.Header closeButton>
                <Modal.Title>Reporte completo - {currentDate && moment(currentDate).format('DD/MM/YYYY')}</Modal.Title>
            </Modal.Header>
            <Modal.Body className="p-0">
                <div className="table-responsive">
                    <Table>
                        <thead>
                            <tr>
                                <th>Prioridad</th>
                                <th>OT</th>
                                <th>Proceso</th>
                                <th>Máquina</th>
                                <th>Operador</th>
                                <th>Cant. Prog</th>
                                <th>Kilos Prog</th>
                                <th>Horario</th>
                                <th>Estado</th>
                                <th>Kilos Fab.</th>
                                <th>% Cumpl.</th>
                                <th>Observaciones</th>
                            </tr>
                        </thead>
                        <tbody>
                            {tasks.map((task, index) => (
                                <tr key={task.id}>
                                    <td><strong>{index + 1}</strong></td>
                                    <td>{task.ot_codigo}</td>
                                    <td>{task.proceso}</td>
                                    <td>{task.maquina ? task.maquina.descripcion : "Sin máquina"}</td>
                                    <td>
                                        <div>
                                            <span>{task.operador_nombre || "Sin asignar"}</span>
                                            {task.asignado_por_nombre && (
                                                <small className="d-block text-muted">
                                                    Asignado por: {task.asignado_por_nombre} <br />
                                                    {task.fecha_asignacion && new Date(task.fecha_asignacion).toLocaleString()}
                                                </small>
                                            )}
                                        </div>
                                    </td>
                                    <td>{task.cantidad_programada}</td>
                                    <td>{task.kilos_programados.toFixed(2)}</td>
                                    <td>{`${task.hora_inicio} - ${task.hora_fin}`}</td>
                                    <td>{taskStates[task.id] || task.estado}</td>
                                    <td>{kilosFabricados[task.id] || task.kilos_fabricados || '0'}</td>
                                    <td>
                                        {porcentajeCumplimiento[task.id] ? 
                                        `${porcentajeCumplimiento[task.id].toFixed(1)}%`:
                                        '0%'}
                                    </td>
                                    <td>{task.observaciones || ''}</td>
                                </tr>
                            ))}
                        </tbody>
                    </Table>
                </div>
            </Modal.Body>
            <Modal.Footer>
                <Button variant="secondary" onClick={onHide}>
                    <FaTimes className="me-2" />
                    Cerrar
                </Button>
            </Modal.Footer>
        </Modal>
    );
};

export default TableFullViewModal;