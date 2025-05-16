import React from 'react';
import { Modal, Table } from 'react-bootstrap';

export const FullViewModal = ({ show, onHide, tasks}) => {
  if (!tasks || tasks.length === 0) return null;

  const cantidades = tasks[0].cantidades || {};
  const kilos = tasks[0].kilos || {};

  return (
    <Modal show={show} onHide={onHide} size="xl">
      <Modal.Header closeButton>
          <Modal.Title>Vista Completa de Tareas</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <Table striped bordered hover responsive>
          <thead>
            <tr>
              <th>OT</th>
              <th>Proceso</th>
              <th>Máquina</th>
              <th>Operador</th>
              <th>Cant. Prog.</th>
              <th>Kilos Prog.</th>
              <th>Estado</th>
              <th>Kilos Fab.</th>
              <th>% Cumpl.</th>
              <th>Observaciones</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map((task, index) => (
                <tr key={task.id} className={task.es_continuacion ? 'tarea-continuacion' : ''}>
                    <td>{task.codigo}</td>
                    <td>{task.proceso.descripcion}</td>
                    <td>{task.maquina?.descripcion || 'Sin máquina'}</td>
                    <td>{task.operador?.nombre || 'Sin asignar'}</td>
                    <td className="text-end">{task.cantidad_programada || 0}</td>
                    <td className="text-end">{(task.kilos_programados || 0).toFixed(2)}</td>
                    <td>{task.estado}</td>
                    <td className="text-end">{(task.kilos_fabricados || 0).toFixed(2)}</td>
                    <td className="text-center">{(task.porcentaje_cumplimiento || 0).toFixed(1)}%</td>
                    <td>{task.observaciones}</td>
                </tr>
            ))}
          </tbody>
        </Table>
      </Modal.Body>
    </Modal>
  );
};

