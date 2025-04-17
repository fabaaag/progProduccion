import React, { useState, useEffect } from 'react';
import { Container, Card, Badge } from 'react-bootstrap';
import { FaCubes } from 'react-icons/fa';
import { getProductos, getProducto } from '../../../api/productos.api';
import { LoadingSpinner } from '../../UI/LoadingSpinner/LoadingSpinner';
import CompNavbar from '../../Navbar/CompNavbar';
import { Footer } from '../../Footer/Footer';
import FiltrosProductos from './ProductosSubcomps/FiltrosProductos';
import TablaProductos from './ProductosSubcomps/TablaProductos';
import PaginacionProductos from './ProductosSubcomps/PaginacionProductos';
import DetalleProductoModal from './ProductosSubcomps/DetalleProductoModal';
//import './css/ProductosList.css';

export const ProductosList = () => {
  const [productos, setProductos] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);
  const [totalItems, setTotalItems] = useState(0);
  const [loading, setLoading] = useState(false);

  //Estados para filtros
  const [filtros, setFiltros] = useState({
    search: '',
    codigo_producto: '',
    descripcion: '',
    familia_codigo: '',
    subfamilia_codigo: '',
    armado: ''
  });

  //Estado para mostrar/ocultar filtros avanzados
  const [mostrarFiltrosAvanzados, setMostrarFiltrosAvanzados] = useState(false);

  //Estados para el modal de ficha técnica
  const [showModal, setShowModal] = useState(false);
  const [productoSeleccionado, setProductoSeleccionado] = useState(null);
  const [loadingFicha, setLoadingFicha] = useState(false);

  const fetchProductos = async (page = 1, pageSize = 10, searchParams = {}) => {
    console.log("fetchProductos llamado con:", { page, pageSize, searchParams });
    setLoading(true);
    try {
      const params = {
        page,
        page_size: pageSize,
        ...searchParams
      };
      const queryString = new URLSearchParams(params).toString();
      console.log("URL que se construirá:", `/productos/productos?${queryString}`);
      
      const response = await getProductos(params);
      console.log("Respuesta completa del servidor:", response);
      setProductos(response.results);
      setTotalItems(response.count);
      setCurrentPage(page);
    } catch (error) {
      console.error("Error detallado:", error.response?.data || error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProductos(currentPage, itemsPerPage);
  }, []);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFiltros({
      ...filtros,
      [name]: value
    });
  };

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
  }


  const handleSearch = (e) => {
    e.preventDefault();
    console.log('Iniciando búsqueda con filtros:', filtros);
    
    const searchParams = procesarFiltros();
    console.log('Parámetros de búsqueda:', searchParams);
    
    // Recargar productos con los filtros
    fetchProductos(1, itemsPerPage, searchParams);
  };

  const handleReset = () => {
    setFiltros({
      search: '',
      codigo_producto: '',
      descripcion: '',
      familia_codigo: '',
      subfamilia_codigo: '',
      armado: ''
    });
    fetchProductos(1, itemsPerPage);
  };

  const handleVerDetalles = async (producto) => {
    if (!producto) {
      console.error("Producto no válido");
      return;
    }
    
    setLoadingFicha(true);
    try {
      console.log('Producto seleccionado:', producto);
      if(producto.id){
        const productoDetallado = await getProducto(producto.id);
        console.log("Detalles del producto:", productoDetallado);

        //El objeto piezaDetallada ya incluye las rutas en su propiedad 'rutas'
        // no es necesario hacer otra llamda a la API
        setProductoSeleccionado(productoDetallado);
      } else {
        setProductoSeleccionado(producto);
      }

      setShowModal(true);
    } catch (error) {
      console.error('Error al cargar detalles del producto:', error);
    } finally {
      setLoadingFicha(false);
    }
  };

  const handlePageChange = (pageNumber) => {
    const searchParams = procesarFiltros();
    fetchProductos(pageNumber, itemsPerPage, searchParams);
    window.scrollTo({top: 0, behavior: 'smooth'});
  };

  //Cálculos para la paginación
  const totalPages = Math.ceil(totalItems / itemsPerPage);

  return (
    <>
      <CompNavbar />
      <Container fluid className="py-4">
        {loading ? (
          <LoadingSpinner message="Cargando productos..." />
        ) : (
          <div className="productos-list-container">
            <Card className="productos-card">
              <Card.Header className="bg-primary text-white d-flex justify-content-between align-items-center">
                <h5 className="mb-0">
                  <FaCubes className="me-2" />
                  Listado de Productos
                </h5>
                <Badge bg="light" text="dark" pill>
                  Total: {totalItems}
                </Badge>
              </Card.Header>
              <Card.Body>
                <FiltrosProductos 
                  filtros={filtros}
                  mostrarFiltrosAvanzados={mostrarFiltrosAvanzados}
                  setMostrarFiltrosAvanzados={setMostrarFiltrosAvanzados}
                  handleInputChange={handleInputChange}
                  handleSearch={handleSearch}
                  handleReset={handleReset}
                  tipo="productos"
                />

                <TablaProductos 
                  productos={productos}
                  handleVerDetalles={handleVerDetalles}
                />

                <div className="mt-3">
                  {productos.length > 0 && (
                    <div className="d-flex justify-content-between align-items-center flex-wrap">
                      <div className="mb-2 mb-md-0">
                        Mostrando {Math.min((currentPage -1) * itemsPerPage + 1, totalItems)} - {Math.min(currentPage * itemsPerPage, totalItems)} de {totalItems} productos.
                      </div>
                      <PaginacionProductos 
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
        <DetalleProductoModal 
          showModal={showModal}
          setShowModal={setShowModal}
          productoSeleccionado={productoSeleccionado}
          loadingFicha={loadingFicha}
        />
      </Container>
      <Footer />
    </>
  );
};
