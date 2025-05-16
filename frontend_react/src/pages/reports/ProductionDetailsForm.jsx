import React from 'react';
import { Form, Row, Col, Card } from 'react-bootstrap';

export const ProductionDetailsForm = ({ 
  orderDetails,
  disabled = false 
}) => {
  return (
    <Card className="mb-3">
      <Card.Body>
        {/* Sección OT */}
        <Row className="mb-3">
          <Col md={4}>
            <Form.Group>
              <Form.Label>Orden de Trabajo</Form.Label>
              <Row>
                <Col>
                  <Form.Control
                    type="text"
                    value={orderDetails?.numero_ot || ''}
                    disabled={true}
                    placeholder="Número"
                  />
                </Col>
                <Col>
                  <Form.Control
                    type="text"
                    value={orderDetails?.etapa || ''}
                    disabled={true}
                    placeholder="Etapa"
                  />
                </Col>
              </Row>
            </Form.Group>
          </Col>
          <Col md={4}>
            <Form.Group>
              <Form.Label>Cantidad Unidades</Form.Label>
              <Form.Control
                type="text"
                value={orderDetails?.cantidad_unidades || ''}
                disabled={true}
              />
            </Form.Group>
          </Col>
          <Col md={4}>
            <Form.Group>
              <Form.Label>Saldo Pendiente</Form.Label>
              <Form.Control
                type="text"
                value={orderDetails?.saldo_pendiente || ''}
                disabled={true}
              />
            </Form.Group>
          </Col>
        </Row>

        {/* Sección Producto */}
        <Row className="mb-3">
          <Col md={8}>
            <Form.Group>
              <Form.Label>Producto</Form.Label>
              <Row>
                <Col md={4}>
                  <Form.Control
                    type="text"
                    value={orderDetails?.codigo_producto || ''}
                    disabled={true}
                    placeholder="Código"
                  />
                </Col>
                <Col md={8}>
                  <Form.Control
                    type="text"
                    value={orderDetails?.nombre_producto || ''}
                    disabled={true}
                    placeholder="Nombre"
                  />
                </Col>
              </Row>
            </Form.Group>
          </Col>
          <Col md={4}>
            <Form.Group>
              <Form.Label>Materia Prima</Form.Label>
              <Form.Control
                type="text"
                value={orderDetails?.materia_prima || ''}
                disabled={true}
              />
            </Form.Group>
          </Col>
        </Row>

        {/* Sección Proceso */}
        <Row className="mb-3">
          <Col md={4}>
            <Form.Group>
              <Form.Label>Proceso</Form.Label>
              <Form.Control
                type="text"
                value={orderDetails?.proceso || ''}
                disabled={true}
              />
            </Form.Group>
          </Col>
          <Col md={4}>
            <Form.Group>
              <Form.Label>Unidad o Máquina</Form.Label>
              <Form.Control
                type="text"
                value={orderDetails?.maquina || ''}
                disabled={true}
              />
            </Form.Group>
          </Col>
          <Col md={4}>
            <Form.Group>
              <Form.Label>Estándar por Hora</Form.Label>
              <Form.Control
                type="text"
                value={orderDetails?.estandar_hora || ''}
                disabled={true}
              />
            </Form.Group>
          </Col>
        </Row>

        {/* Sección Trabajadores */}
        <Row>
          <Col md={4}>
            <Form.Group>
              <Form.Label>RUT Trabajador</Form.Label>
              <Form.Control
                type="text"
                value={orderDetails?.rut_trabajador || ''}
                disabled={disabled}
              />
            </Form.Group>
          </Col>
          <Col md={4}>
            <Form.Group>
              <Form.Label>Horas Trabajadas</Form.Label>
              <Form.Control
                type="number"
                value={orderDetails?.horas_trabajadas || ''}
                disabled={disabled}
                onChange={(e) => {
                  // Aquí iría la lógica para actualizar las horas trabajadas
                }}
              />
            </Form.Group>
          </Col>
          <Col md={4}>
            <Form.Group>
              <Form.Label>Sobretiempo</Form.Label>
              <Form.Control
                type="number"
                value={orderDetails?.sobretiempo || ''}
                disabled={disabled}
                onChange={(e) => {
                  // Aquí iría la lógica para actualizar el sobretiempo
                }}
              />
            </Form.Group>
          </Col>
        </Row>
      </Card.Body>
    </Card>
  );
};