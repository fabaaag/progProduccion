import React from 'react';
import { FaCubes, FaTools, FaChartLine } from 'react-icons/fa';
import ModalBase from '../../Shared/Details/ModalBase';

//Componentes internos para cada pestaña
import { InfoGeneralTab } from '../../Shared/Details/Tabs/InfoGeneralTab';
import { RutaFabricacionTab } from '../../Shared/Details/Tabs/RutaFabricacionTab';
//import { DatosProduccionTab } from './DetallePiezaTabs/DatosProduccionTab';


const DetallePiezaModal = ({ showModal, setShowModal, piezaSeleccionada, loadingFicha }) => {
    const tabs=[
        {
            id:'informacion',
            titulo: <><FaCubes className="me-1" /> Información General</>,
            contenido: <InfoGeneralTab item={piezaSeleccionada} tipo="pieza" />
        },
        {
            id: 'ruta',
            titulo: <><FaTools className="me-1" /> Ruta de Fabricación</>,
            contenido: <RutaFabricacionTab rutas={piezaSeleccionada?.rutas || []} tipo="pieza" />,
        },
        {
            id: 'produccion',
            titulo: <><FaChartLine className="me-1" /> Datos de Producción</>,
           //contenido: <DatosProduccionTab piezaId={piezaSeleccionada?.id} />
        }
    ];

    //Configurar el título del modal
    const titulo = piezaSeleccionada ? `${piezaSeleccionada.codigo_pieza} - ${piezaSeleccionada.descripcion}` : 'Detalle de la Pieza';

    return (
        <ModalBase
            showModal={showModal}
            setShowModal={setShowModal}
            itemSeleccionado={piezaSeleccionada}
            loadingItem={loadingFicha}
            titulo={titulo}
            icono={<FaCubes className="me-2" />}
            tabs={tabs}
            tamano="lg"
        />   
    );
};

export default DetallePiezaModal;