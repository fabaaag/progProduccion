import { useEffect, useState, useMemo, useCallback } from "react";
import { getAllOrders, searchOrders } from "../../api/orders.api.js";
import CompNavbar from "../Navbar/CompNavbar.jsx";
import { useNavigate } from "react-router-dom";
import { OrderDetailModal} from './OrderDetailModal.jsx'
import { Form, Card, Badge, InputGroup, Button } from 'react-bootstrap';
import { FaSearch, FaFilter } from 'react-icons/fa';
import { LoadingSpinner } from '../UI/LoadingSpinner/LoadingSpinner';
import './css/OrdersList.css'

export function OrdersList(){
    const [orders, setOrders] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [selectedOrder, setSelectedOrder] = useState(null);
    const [searchTerm, setSearchTerm] = useState("");
    const [filterStatus, setFilterStatus] = useState("all");
    const [isSearching, setIsSearching] = useState(false);
    const navigate = useNavigate()

    // Usar useCallback para funciones
    const handleShowModal = useCallback((order) => {
        setSelectedOrder(order);
        setShowModal(true);
    }, []);

    const handleCloseModal = useCallback(() => {
        setShowModal(false);
        setSelectedOrder(null);
    }, []);

    const loadOrders = useCallback(async () => {
        try {
            setLoading(true);
            const res = await getAllOrders();
            setOrders(res.data);
        } catch (error) {
            console.error("Error al cargar las órdenes:", error);
        } finally {
            setLoading(false);
        }
    }, []);

    // Cargar órdenes solo una vez
    useEffect(() => {
        loadOrders();
    }, [loadOrders]);

    // Función para buscar con debounce
    useEffect(() => {
        const searchTimeout = setTimeout(async () => {
            try {
                setIsSearching(true);
                const res = await searchOrders(searchTerm, filterStatus);
                setOrders(res.data);
            } catch (error) {
                console.error("Error al buscar órdenes:", error);
            } finally {
                setIsSearching(false);
            }
        }, 500); // Esperar 500ms después de la última tecla

        return () => clearTimeout(searchTimeout);
    }, [searchTerm, filterStatus]);

    // Usar useMemo para filtrar las órdenes
    const filteredOrders = useMemo(() => {
        const searchLower = searchTerm.toLowerCase();
        
        return orders.filter(order => {
            const matchesSearch = 
                order.codigo_ot?.toString().toLowerCase().includes(searchLower) ||
                order.descripcion_producto_ot?.toLowerCase().includes(searchLower) ||
                order.cliente?.nombre?.toLowerCase().includes(searchLower);

            const matchesStatus = 
                filterStatus === 'all' || 
                order.situacion_ot?.codigo_situacion_ot === filterStatus;

            return matchesSearch && matchesStatus;
        });
    }, [orders, searchTerm, filterStatus]);

    // Handlers con debounce para los filtros
    const handleSearch = useCallback((e) => {
        const { value } = e.target;
        setSearchTerm(value);
    }, []);

    const handleStatusFilter = useCallback((e) => {
        const { value } = e.target;
        setFilterStatus(value);
    }, []);

    
    const getStatusBadgeColor = (status) => {
        switch(status) {
            case 'Pendiente': return 'warning';
            case 'Stock': return 'info';
            case 'Completado': return 'success';
            default: return 'secondary';
        }
    };

    return(
        <div className="bg-light min-vh-100">
            <CompNavbar />
            <div className="container py-4">
                {/* Header Section */}
                <div className="d-flex justify-content-between align-items-center mb-4">
                    <h1 className="h3">Órdenes de Trabajo</h1>
                    <Button variant="primary" onClick={() => navigate('/')}>
                        Volver al Inicio
                    </Button>
                </div>

                {/* Filters Section - Siempre visible */}
                <Card className="mb-4 shadow-sm">
                    <Card.Body>
                        <div className="row g-3">
                            <div className="col-md-4">
                                <InputGroup className="search-input-group">
                                    <div className="search-icon">
                                        <FaSearch />
                                    </div>
                                    <Form.Control
                                        className="search-input"
                                        placeholder="Buscar orden..."
                                        onChange={handleSearch}
                                        value={searchTerm}
                                    />
                                </InputGroup>
                            </div>
                            <div className="col-md-4">
                                <Form.Select
                                    onChange={handleStatusFilter}
                                    value={filterStatus}
                                >
                                    <option value="all">Todos los estados</option>
                                    <option value="P">Pendiente</option>
                                    <option value="S">Sin Imprimir</option>
                                    <option value="T">Terminado</option>
                                </Form.Select>
                            </div>
                        </div>
                    </Card.Body>
                </Card>

                {/* Content Section with Loading */}
                <div className="position-relative">
                    {(loading || isSearching) && (
                        <LoadingSpinner 
                            message={isSearching ? "Buscando órdenes..." : "Cargando órdenes..."}
                            containerStyle="content"
                        />
                    )}
                    
                    <div className="row g-4" style={{ 
                        opacity: loading || isSearching ? 0.5 : 1,
                        transition: 'opacity 0.3s ease'
                    }}>
                        {filteredOrders.length === 0 ? (
                            <div className="col-12 text-center">
                                <p>No se encontraron órdenes que coincidan con la búsqueda</p>
                            </div>
                        ) : (
                            filteredOrders.map(order => (
                                <div key={order.id} className="col-md-6 col-lg-4">
                                    <Card 
                                        className="h-100 shadow-sm hover-card" 
                                        onClick={() => handleShowModal(order)}
                                        style={{ cursor: 'pointer' }}
                                    >
                                        <Card.Body>
                                            <div className="d-flex justify-content-between align-items-start mb-3">
                                                <div>
                                                    <h5 className="mb-1">OT #{order.codigo_ot}</h5>
                                                    <p className="text-muted small mb-0">{order.descripcion_producto_ot}</p>
                                                </div>
                                                <Badge bg={getStatusBadgeColor(order.tipo_ot?.descripcion)}>
                                                    {order.tipo_ot?.descripcion}
                                                </Badge>
                                            </div>
                                            
                                            <div className="small mb-2">
                                                <strong>Cliente:</strong> {order.cliente?.nombre}
                                            </div>
                                            
                                            <div className="progress mb-2" style={{height: "8px"}}>
                                                <div 
                                                    className="progress-bar" 
                                                    role="progressbar"
                                                    style={{
                                                        width: `${(order.cantidad_avance / order.cantidad) * 100}%`
                                                    }}
                                                />
                                            </div>
                                            
                                            <div className="d-flex justify-content-between text-muted small">
                                                <span>Avance: {order.cantidad_avance} / {order.cantidad}</span>
                                                <span>Término: {order.fecha_termino}</span>
                                            </div>
                                        </Card.Body>
                                    </Card>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>

            <OrderDetailModal
                show={showModal}
                onHide={handleCloseModal}
                orderData={selectedOrder}
            />
        </div>
    );
}