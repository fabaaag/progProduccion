import React, { useState, useEffect } from 'react';
import { Container, Card, Badge } from 'react-bootstrap';
import { FaCubes } from 'react-icons/fa';
import { getPiezas, getPieza } from '../../../api/productos.api';
import { LoadingSpinner } from '../../UI/LoadingSpinner/LoadingSpinner';
import CompNavbar from '../../Navbar/CompNavbar';
import { Footer } from '../../Footer/Footer';
import FiltrosPiezas from './PiezasSubcomps/FiltrosPiezas';
import TablaPiezas from './PiezasSubcomps/TablaPiezas';
import PaginacionPiezas from './PiezasSubcomps/PaginacionPiezas';
import DetallePiezaModal from './PiezasSubcomps/DetallePiezaModal';
//import './css/PiezasList.css';

export const PiezasList = () => {
  const [piezas, setPiezas] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);
  const [totalItems, setTotalItems] = useState(0);
  const [loading, setLoading] = useState(false);

  //Estado para filtros
  const [filtros, setFiltros] = useState({
    search: '',
    codigo_pieza: '',
    descripcion: '',
    familia: '',
    subfamilia: '',
  });

  //Estado para mostrar/ocultar filtros avanzados
  const [mostrarFIltrosAvanzados, setMostrarFiltrosAvanzados] = useState(false);

  //Estado para el modal de ficha técnica
  const [showModal, setShowModal] = useState(false);
  const [piezaSeleccionada, setPiezaSeleccionada] = useState(null);
  const [loadingFicha, setLoadingFicha] = useState(false);

  const fetchPiezas = async (page = 1, pageSize = 10, searchParams = {}) => {
    console.log('fetchPiezas llamado con: ', {page, pageSize, searchParams});
    setLoading(true);
    try{
      const params = {
        page,
        page_size: pageSize,
        ...searchParams,
      };
      //Log para ver exactamente qué parámetros se están enviando
      const queryString = new URLSearchParams(params).toString();
      console.log('URL que se construirá:', `/productos/piezas?${queryString}`);

      const response = await getPiezas(params);
      console.log('Respuesta completa del servidor:', response);
      setPiezas(response.results);
      setTotalItems(response.count);
      setCurrentPage(page);
    } catch(error){
      console.error('Error detallado:', error.response?.data || error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPiezas(currentPage, itemsPerPage);
  }, []);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFiltros({
      ...filtros,
      [name]: value,
    });
  };

  //Funcion auxiliar para procesar los filtros
  const procesarFiltros = () => {
    const searchParams = {};
    Object.entries(filtros).forEach(([key, value]) => {
      if(value !== '' &&  value !== null){
        if(key === 'familia'){
          searchParams['familia_codigo'] = value.trim();
        } else if (key === 'subfamilia'){
          searchParams['subfamilia_codigo'] = value.trim();
        }else if (key === 'descripcion'){
          searchParams['descripcion'] = value.trim();
        } else{
          searchParams[key] = value.trim();
        }
      }
    });
    return searchParams;
  };

  const handleSearch = (e) => {
    e.preventDefault();
    console.log('Iniciando búsqueda con filtros:', filtros);

    const searchParams = procesarFiltros();
    console.log('Parámetros de búsqueda:', searchParams);

    //Recargar piezas con los filtros
    fetchPiezas(1, itemsPerPage, searchParams);
  };

  const handleReset = () => {
    setFiltros({
      search: '',
      codigo_pieza: '',
      descripcion: '',
      familia: '',
      subfamilia: '',
    });
    fetchPiezas(1, itemsPerPage);
  };

  const handleVerDetalles = async (pieza) => {
    if (!pieza){
      console.error('Pieza no válida');
      return;
    }

    setLoadingFicha(true);
    try{
      console.log('Pieza seleccionada:', pieza);

      //Si tenemos un ID, obtener la pieza detallada que incluye las rutas
      if (pieza.id){
        const piezaDetallada = await getPieza(pieza.id);
        console.log("Detalles de la pieza:", piezaDetallada);

        //El objeto piezaDetallada ya incluye las rutas en su propiedad 'rutas'
        // no es necesario hacer otra llamda a la API
        setPiezaSeleccionada(piezaDetallada);
      }else{
        //Usar la pieza tal como está
        setPiezaSeleccionada(pieza);
      }

      setShowModal(true);
    } catch (error){
      console.error('Error al cargar detalles de la pieza:', error);
    } finally {
      setLoadingFicha(false);
    }
  };

  const handlePageChange = (pageNumber) => {
    const searchParams = procesarFiltros();
    fetchPiezas(pageNumber, itemsPerPage, searchParams);
    window.scrollTo({top: 0, behavior: 'smooth'});
  };

  //Cálculo para la paginación
  const totalPages = Math.ceil(totalItems / itemsPerPage);

  return (
    <>
      <CompNavbar />
      <Container fluid className="py-4">
        {loading ? (
          <LoadingSpinner message="Cargando piezas..." />
        ) : (
          <div className="piezas-list-container">
            <Card className="piezas-card">
              <Card.Header className="bg-primary text-white d-flex justify-content-between align-items-center">
                <h5 className="mb-0">
                  <FaCubes className="me-2" />
                  Listado de Piezas
                </h5>
                <Badge bg="light" text="dark" pill>
                  Total: {totalItems}
                </Badge>
              </Card.Header>
              <Card.Body>
                <FiltrosPiezas
                  filtros={filtros}
                  mostrarFiltrosAvanzados={mostrarFIltrosAvanzados}
                  setMostrarFiltrosAvanzados={setMostrarFiltrosAvanzados}
                  handleInputChange={handleInputChange}
                  handleSearch={handleSearch}
                  handleReset={handleReset}
                  tipo="piezas"
                />
                <TablaPiezas 
                  piezas={piezas}
                  handleVerDetalles={handleVerDetalles}
                />

                <div className="mt-3">
                  {piezas.length > 0 && (
                    <div className="d-flex justify-content-between align-items-center flex-wrap">
                      <div className="mb-2 mb-md-0">
                        Mostrando {Math.min((currentPage - 1) * itemsPerPage + 1, totalItems)} - {Math.min(currentPage * itemsPerPage, totalItems)} de {totalItems} piezas.|
                      </div>
                      <PaginacionPiezas 
                        currentPage={currentPage}
                        totalPages={totalPages}
                        handlePageChange={handlePageChange}
                      />
                    </div>
                  )}
                </div>
              </Card.Body>
            </Card>
          </div>
        )}
        <DetallePiezaModal 
          showModal={showModal}
          setShowModal={setShowModal}
          piezaSeleccionada={piezaSeleccionada}
          loadingFicha={loadingFicha}
        />
      </Container>
      <Footer />
    </>
  );
};