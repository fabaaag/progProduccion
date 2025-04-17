import React from 'react';
import { FaCubes, FaTools, FaChartLine } from 'react-icons/fa';
import ModalBase from '../../Shared/Details/ModalBase';

//Componentes internos para cada pestaña
import { InfoGeneralTab } from '../../Shared/Details/Tabs/InfoGeneralTab';
import { RutaFabricacionTab } from '../../Shared/Details/Tabs/RutaFabricacionTab';
//import { DatosProduccionTab } from './DetalleProductoTabs/DatosProduccionTab';

const DetalleProductoModal = ({ showModal, setShowModal, productoSeleccionado, loadingFicha }) => {
  const tabs = [
    {
      id:'informacion',
      titulo: <><FaCubes className="me-1" /> Información General</>,
      contenido: <InfoGeneralTab item={productoSeleccionado} tipo="producto"/>
    },
    {
      id: 'ruta',
      titulo: <><FaTools className="me-1" /> Ruta de Fabricación</>,
      contenido: <RutaFabricacionTab rutas={productoSeleccionado?.rutas || []} tipo="producto"/>
    },
    {
      id: 'produccion',
      titulo: <><FaChartLine className="me-1" /> Datos de Producción</>,
      //contenido: <DatosProduccionTab piezaId={piezaSeleccionada?.id} />
    }
  ]

  const titulo = productoSeleccionado ? `${productoSeleccionado.codigo_producto} - ${productoSeleccionado.descripcion}` : 'Detalle del Producto';

  return (
    <ModalBase
      showModal={showModal}
      setShowModal={setShowModal}
      itemSeleccionado={productoSeleccionado}
      loadingItem={loadingFicha}
      titulo={titulo}
      icono={<FaCubes className="me-2" />}
      tabs={tabs}
      tamano="lg"
    />
  );
};

export default DetalleProductoModal;