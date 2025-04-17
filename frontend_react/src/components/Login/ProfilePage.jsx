import { useState, useEffect } from 'react';
import { Form, Button, Card, Container, Row, Col } from 'react-bootstrap';
import CompNavbar from '../Navbar/CompNavbar.jsx';
import { updateProfile, getProfile } from '../../api/auth.api';
import { toast } from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';
import { LoadingSpinner } from '../UI/LoadingSpinner/LoadingSpinner.jsx';
import './css/ProfilePage.css';

export function ProfilePage() {
    const [userData, setUserData] = useState({
        first_name: '',
        last_name: '',
        email: '',
        telefono: '',
        cargo: ''
    });
    
    // Nuevo estado para las contraseñas
    const [passwordData, setPasswordData] = useState({
        current_password: '',
        new_password: '',
        confirm_password: ''
    });
    
    const [showPasswordForm, setShowPasswordForm] = useState(false);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        const loadProfile = async () => {
            try {
                const token = localStorage.getItem('token');
                console.log('Token actual:', token); // Debug

                if (!token) {
                    console.log('No hay token disponible'); // Debug
                    navigate('/login');
                    return;
                }

                console.log('Intentando obtener perfil...'); // Debug
                const profileData = await getProfile();
                console.log('Datos del perfil recibidos:', profileData); // Debug

                setUserData({
                    first_name: profileData.first_name || '',
                    last_name: profileData.last_name || '',
                    email: profileData.email || '',
                    telefono: profileData.telefono || '',
                    cargo: profileData.cargo || ''
                });
            } catch (error) {
                console.error('Error completo:', error);
                console.error('Respuesta del servidor:', error.response); // Debug
                
                if (error.response?.status === 401) {
                    toast.error('Sesión no válida');
                    localStorage.clear();
                    navigate('/login');
                } else {
                    toast.error('Error al cargar el perfil');
                }
            } finally {
                setLoading(false);
            }
        };

        loadProfile();
    }, [navigate]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            setLoading(true);
            const updatedUser = await updateProfile(userData);
            localStorage.setItem('user', JSON.stringify(updatedUser));
            toast.success('Perfil actualizado exitosamente');
        } catch (error) {
            console.error('Error al actualizar el perfil:', error);
            if (error.response?.status === 401) {
                localStorage.clear();
                navigate('/login');
            } else {
                toast.error('Error al actualizar el perfil');
            }
        } finally {
            setLoading(false);
        }
    };

    const handlePasswordSubmit = async (e) => {
        e.preventDefault();
        
        if (passwordData.new_password !== passwordData.confirm_password) {
            toast.error('Las contraseñas no coinciden');
            return;
        }

        if (passwordData.new_password.length < 8) {
            toast.error('La contraseña debe tener al menos 8 caracteres');
            return;
        }

        try {
            setLoading(true);
            await updateProfile({
                current_password: passwordData.current_password,
                new_password: passwordData.new_password
            });
            
            setPasswordData({
                current_password: '',
                new_password: '',
                confirm_password: ''
            });
            setShowPasswordForm(false);
            toast.success('Contraseña actualizada exitosamente');
        } catch (error) {
            console.error('Error al actualizar la contraseña:', error);
            if (error.response?.status === 401) {
                toast.error('Contraseña actual incorrecta');
            } else {
                toast.error('Error al actualizar la contraseña');
            }
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <>
                <CompNavbar />
                <Container className="d-flex justify-content-center align-items-center" style={{ minHeight: '80vh' }}>
                    <LoadingSpinner />
                </Container>
            </>
        );
    }

    return (
        <>
            <CompNavbar />
            <Container className='mt-4'>
                <Card className="profile-card mb-4">
                    <Card.Header className="profile-header">
                        <div className="profile-header-content">
                            <div className="profile-avatar">
                                {userData.first_name && userData.last_name ? 
                                    `${userData.first_name[0]}${userData.last_name[0]}`.toUpperCase() 
                                    : 'U'
                                }
                            </div>
                            <div className="profile-title">
                                <h3 className="mb-0">Mi Perfil</h3>
                                <small className="text-muted">{userData.cargo || 'Sin cargo asignado'}</small>
                            </div>
                        </div>
                    </Card.Header>
                    <Card.Body className="profile-body">
                        <Form onSubmit={handleSubmit}>
                            <div className="profile-section">
                                <h5 className="section-title">Información Personal</h5>
                                <Row>
                                    <Col md={6}>
                                        <Form.Group className='mb-3'>
                                            <Form.Label>Nombre</Form.Label>
                                            <Form.Control
                                                type='text'
                                                value={userData.first_name}
                                                onChange={(e) => setUserData({
                                                    ...userData,
                                                    first_name: e.target.value
                                                })}
                                                className="profile-input"
                                            />
                                        </Form.Group>
                                    </Col>
                                    <Col md={6}>
                                        <Form.Group className='mb-3'>
                                            <Form.Label>Apellido</Form.Label>
                                            <Form.Control
                                                type='text'
                                                value={userData.last_name}
                                                onChange={(e) => setUserData({
                                                    ...userData,
                                                    last_name: e.target.value
                                                })}
                                                className="profile-input"
                                            />
                                        </Form.Group>
                                    </Col>
                                </Row>

                                <Row>
                                    <Col md={6}>
                                        <Form.Group className='mb-3'>
                                            <Form.Label>Email</Form.Label>
                                            <Form.Control 
                                                type='email'
                                                value={userData.email}
                                                onChange={(e) => setUserData({
                                                    ...userData,
                                                    email: e.target.value
                                                })}
                                                className="profile-input"
                                            />
                                        </Form.Group>
                                    </Col>
                                    <Col md={6}>
                                        <Form.Group className='mb-3'>
                                            <Form.Label>Teléfono</Form.Label>
                                            <Form.Control 
                                                type='text'
                                                value={userData.telefono}
                                                onChange={(e) => setUserData({
                                                    ...userData,
                                                    telefono: e.target.value
                                                })}
                                                className="profile-input"
                                            />
                                        </Form.Group>
                                    </Col>
                                </Row>

                                <Form.Group className='mb-4'>
                                    <Form.Label>Cargo</Form.Label>
                                    <Form.Control 
                                        type='text'
                                        value={userData.cargo}
                                        onChange={(e) => setUserData({
                                            ...userData,
                                            cargo: e.target.value
                                        })}
                                        className="profile-input"
                                    />
                                </Form.Group>

                                <div className="profile-actions">
                                    <Button 
                                        variant="primary" 
                                        type="submit" 
                                        disabled={loading}
                                        className="action-button"
                                    >
                                        {loading ? (
                                            <>
                                                <span className="spinner-border spinner-border-sm me-2" />
                                                Actualizando...
                                            </>
                                        ) : 'Actualizar Perfil'}
                                    </Button>
                                    <Button
                                        variant={showPasswordForm ? "outline-danger" : "outline-primary"}
                                        onClick={() => setShowPasswordForm(!showPasswordForm)}
                                        className="action-button"
                                    >
                                        {showPasswordForm ? 'Cancelar' : 'Cambiar Contraseña'}
                                    </Button>
                                </div>
                            </div>
                        </Form>

                        {showPasswordForm && (
                            <div className="password-section">
                                <Form onSubmit={handlePasswordSubmit}>
                                    <h5 className="section-title">Cambiar Contraseña</h5>
                                    <Row>
                                        <Col md={12}>
                                            <Form.Group className='mb-3'>
                                                <Form.Label>Contraseña Actual</Form.Label>
                                                <Form.Control
                                                    type='password'
                                                    value={passwordData.current_password}
                                                    onChange={(e) => setPasswordData({
                                                        ...passwordData,
                                                        current_password: e.target.value
                                                    })}
                                                    required
                                                    className="profile-input"
                                                />
                                            </Form.Group>
                                        </Col>
                                    </Row>
                                    <Row>
                                        <Col md={6}>
                                            <Form.Group className='mb-3'>
                                                <Form.Label>Nueva Contraseña</Form.Label>
                                                <Form.Control
                                                    type='password'
                                                    value={passwordData.new_password}
                                                    onChange={(e) => setPasswordData({
                                                        ...passwordData,
                                                        new_password: e.target.value
                                                    })}
                                                    required
                                                    minLength={8}
                                                    className="profile-input"
                                                />
                                                <Form.Text className="text-muted">
                                                    Mínimo 8 caracteres
                                                </Form.Text>
                                            </Form.Group>
                                        </Col>
                                        <Col md={6}>
                                            <Form.Group className='mb-3'>
                                                <Form.Label>Confirmar Nueva Contraseña</Form.Label>
                                                <Form.Control
                                                    type='password'
                                                    value={passwordData.confirm_password}
                                                    onChange={(e) => setPasswordData({
                                                        ...passwordData,
                                                        confirm_password: e.target.value
                                                    })}
                                                    required
                                                    className="profile-input"
                                                />
                                            </Form.Group>
                                        </Col>
                                    </Row>
                                    <Button 
                                        variant="primary" 
                                        type="submit"
                                        disabled={loading}
                                        className="action-button"
                                    >
                                        {loading ? (
                                            <>
                                                <span className="spinner-border spinner-border-sm me-2" />
                                                Actualizando...
                                            </>
                                        ) : 'Cambiar Contraseña'}
                                    </Button>
                                </Form>
                            </div>
                        )}
                    </Card.Body>
                </Card>
            </Container>
        </>
    );
}