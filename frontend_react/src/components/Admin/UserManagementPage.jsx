import { useState, useEffect } from 'react';
import { Container, Card, Button, Badge, Table } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import CompNavbar from '../Navbar/CompNavbar';
import { getAllUsers, toggleUserStatus } from '../../api/users.api';
import { toast } from 'react-hot-toast';
import { FaUserPlus, FaEdit, FaPowerOff, FaSearch } from 'react-icons/fa';
import { motion } from 'framer-motion';
import './css/UserManagementPage.css';

export function UserManagementPage() {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const navigate = useNavigate();

    useEffect(() => {
        loadUsers();
    }, []);

    const loadUsers = async () => {
        try {
            const data = await getAllUsers();
            setUsers(data);
        } catch (error) {
            toast.error('Error al cargar usuarios');
        } finally {
            setLoading(false);
        }
    };

    const handleToggleStatus = async (userId) => {
        try {
            await toggleUserStatus(userId);
            loadUsers();
            toast.success('Estado del usuario actualizado');
        } catch (error) {
            toast.error('Error al actualizar el estado del usuario');
        }
    };

    const filteredUsers = users.filter(user => 
        user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
        `${user.first_name} ${user.last_name}`.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const getRoleBadgeVariant = (rol) => {
        const variants = {
            'ADMIN': 'primary',
            'SUPERVISOR': 'success',
            'OPERADOR': 'info'
        };
        return variants[rol] || 'secondary';
    };

    return (
        <>
            <CompNavbar />
            <Container className="mt-4">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5 }}
                >
                    <Card className="user-manage-card">
                        <Card.Header className="d-flex justify-content-between align-items-center">
                            <h3 className="mb-0">Gestión de Usuarios</h3>
                            <Button 
                                variant="primary"
                                onClick={() => navigate('/users/create')}
                                className="create-user-btn"
                            >
                                <FaUserPlus className="me-2" />
                                Crear Usuario
                            </Button>
                        </Card.Header>

                        <Card.Body>
                            <div className="search-container mb-4">
                                <div className="search-input-wrapper">
                                    <FaSearch className="search-icon" />
                                    <input
                                        type="text"
                                        placeholder="Buscar usuarios..."
                                        value={searchTerm}
                                        onChange={(e) => setSearchTerm(e.target.value)}
                                        className="search-input"
                                    />
                                </div>
                            </div>

                            <div className="table-responsive">
                                <Table hover className="user-table">
                                    <thead>
                                        <tr>
                                            <th>Usuario</th>
                                            <th>Nombre</th>
                                            <th>Email</th>
                                            <th>Rol</th>
                                            <th>Estado</th>
                                            <th>Acciones</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {filteredUsers.map(user => (
                                            <motion.tr
                                                key={user.id}
                                                initial={{ opacity: 0 }}
                                                animate={{ opacity: 1 }}
                                                transition={{ duration: 0.3 }}
                                            >
                                                <td>{user.username}</td>
                                                <td>{`${user.first_name} ${user.last_name}`}</td>
                                                <td>{user.email}</td>
                                                <td>
                                                    <Badge bg={getRoleBadgeVariant(user.rol)}>
                                                        {user.rol}
                                                    </Badge>
                                                </td>
                                                <td>
                                                    <Badge bg={user.activo ? 'success' : 'danger'}>
                                                        {user.activo ? 'Activo' : 'Inactivo'}
                                                    </Badge>
                                                </td>
                                                <td>
                                                    <div className="action-buttons">
                                                        <Button
                                                            variant="info"
                                                            size="sm"
                                                            onClick={() => navigate(`/users/edit/${user.id}`)}
                                                            className="action-button edit-button"
                                                        >
                                                            <FaEdit /> Editar
                                                        </Button>
                                                        <Button
                                                            variant={user.activo ? "danger" : "success"}
                                                            size="sm"
                                                            onClick={() => handleToggleStatus(user.id)}
                                                            className="action-button toggle-button"
                                                        >
                                                            <FaPowerOff />
                                                            {user.activo ? ' Desactivar' : ' Activar'}
                                                        </Button>
                                                    </div>
                                                </td>
                                            </motion.tr>
                                        ))}
                                    </tbody>
                                </Table>
                            </div>
                        </Card.Body>
                    </Card>
                </motion.div>
            </Container>
        </>
    );
}