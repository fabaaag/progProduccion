import React, { useState } from 'react';
import { loginUser } from '../../api/auth.api';
import { useNavigate } from 'react-router-dom';
import { Form, Button, Container, Card, Alert } from 'react-bootstrap';
import { toast } from 'react-hot-toast';
import { FaUser, FaLock } from 'react-icons/fa';
import { motion } from 'framer-motion';
import './css/Login.css';
import logo from '../../assets/logavsa.png'; // Ajusta la ruta según tu estructura de carpetas

export function Login() {
    const [credentials, setCredentials] = useState({
        username: '',
        password: ''
    });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const data = await loginUser(credentials);
            localStorage.setItem('token', data.token);
            localStorage.setItem('refreshToken', data.refresh);
            localStorage.setItem('user', JSON.stringify(data.user));

            toast.success('¡Bienvenido!', {
                icon: '👋',
                style: {
                    borderRadius: '10px',
                    background: '#333',
                    color: '#fff',
                }
            });
            
            if(data.user.rol === 'ADMIN' || data.user.rol === 'SUPERVISOR') {
                navigate('/home');
            } else {
                navigate('/login');
            }
        } catch (error) {
            console.error('Error:', error);
            setError('Usuario o contraseña incorrectos');
            toast.error('Error al iniciar sesión');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Container fluid className="login-container">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
            >
                <Card className="login-card">
                    <Card.Body className="p-4">
                        <div className="text-center mb-4">
                            <motion.div
                                initial={{ scale: 0 }}
                                animate={{ scale: 1 }}
                                transition={{ duration: 0.5 }}
                                className="logo-container"
                            >
                                <img 
                                    src={logo} 
                                    alt="Logo empresa" 
                                    className="company-logo"
                                />
                            </motion.div>
                            <h2 className="login-title">Iniciar Sesión</h2>
                            <p className="text-muted">Ingresa tus credenciales para continuar</p>
                        </div>

                        {error && (
                            <motion.div
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                            >
                                <Alert variant="danger" className="error-alert">
                                    {error}
                                </Alert>
                            </motion.div>
                        )}

                        <Form onSubmit={handleSubmit}>
                            <Form.Group className="mb-4">
                                <div className="input-group">
                                    <div className="input-group-prepend">
                                        <span className="input-group-text">
                                            <FaUser />
                                        </span>
                                    </div>
                                    <Form.Control 
                                        type="text"
                                        placeholder="Usuario"
                                        value={credentials.username}
                                        onChange={(e) => setCredentials({
                                            ...credentials,
                                            username: e.target.value.trimEnd()
                                        })}
                                        required
                                        className="login-input"
                                    />
                                </div>
                            </Form.Group>

                            <Form.Group className="mb-4">
                                <div className="input-group">
                                    <div className="input-group-prepend">
                                        <span className="input-group-text">
                                            <FaLock />
                                        </span>
                                    </div>
                                    <Form.Control 
                                        type="password"
                                        placeholder="Contraseña"
                                        value={credentials.password}
                                        onChange={(e) => setCredentials({
                                            ...credentials,
                                            password: e.target.value
                                        })}
                                        required
                                        className="login-input"
                                    />
                                </div>
                            </Form.Group>

                            <Button
                                type="submit"
                                className="login-button w-100"
                                disabled={loading}
                            >
                                {loading ? (
                                    <div className="spinner-container">
                                        <div className="spinner" />
                                        <span className="spinner-text">Iniciando sesión...</span>
                                    </div>
                                ) : (
                                    <span>Iniciar Sesión</span>
                                )}
                            </Button>
                        </Form>
                    </Card.Body>
                </Card>
            </motion.div>
        </Container>
    );
}