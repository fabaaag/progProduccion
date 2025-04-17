import React, { useState } from 'react';
import { Modal, Button, Tabs, Tab } from 'react-bootstrap';
import { LoadingSpinner } from '../../../UI/LoadingSpinner/LoadingSpinner';

const ModalBase = ({
    showModal,
    setShowModal,
    itemSeleccionado,
    loadingItem,
    titulo,
    icono,
    tabs,
    tamano = "lg",
}) => {
    const [activeTab, setActiveTab] = useState(tabs[0]?.id || 'informacion');

    return (
        <Modal
            show={showModal}
            onHide={() => setShowModal(false)}
            size={tamano}
            centered
            className="detalle-modal"
            dialogClassName="modal-90w"
        >
            <Modal.Header closeButton className="bg-primary text-white">
                <Modal.Title>
                    {icono}
                    {titulo}
                </Modal.Title>
            </Modal.Header>
            <Modal.Body>
                {loadingItem ? (
                    <div className="text-center py-4">
                        <LoadingSpinner message="Cargando información..." size="small" />
                    </div>
                ) : (
                    itemSeleccionado && (
                        <Tabs
                            activeKey={activeTab}
                            onSelect={(k) => setActiveTab(k)}
                            className="mb-4"
                        >
                            {tabs.map(tab => (
                                <Tab key={tab.id} eventKey={tab.id} title={tab.titulo}>
                                    {tab.contenido}
                                </Tab>
                            ))}
                        </Tabs>
                    )
                )}
            </Modal.Body>
            <Modal.Footer>
                <Button variant="secondary" onClick={() => setShowModal(false)}>
                    Cerrar
                </Button>
            </Modal.Footer>
        </Modal>
    );
};

export default ModalBase;