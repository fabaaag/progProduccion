import CompNavbar from '../components/Navbar/CompNavbar';
import { useNavigate } from 'react-router-dom';
import { Button, Card, Container, Row, Col } from "react-bootstrap";
import { Footer } from "../components/Footer/Footer";
import { FaIndustry, FaTools, FaUsers, FaCogs } from 'react-icons/fa';
import './HomePage.css';
import { motion } from 'framer-motion';
import { PageTransition } from '../components/UI/PageTransition';

export function HomePage() {
    const navigate = useNavigate();

    const menuItems = [
        {
            title: "Planificación",
            description: "Gestión de programas de producción",
            icon: <FaIndustry size={32} />,
            path: '/programs'
        },
        {
            title: "Mts / Diagnosticomaqs",
            description: "Sistema de diagnóstico de máquinas",
            icon: <FaTools size={32} />,
            path: '/machines-diagnostico'
        },
        {
            title: "Gestión",
            description: "Administración de personal",
            icon: <FaUsers size={32} />,
            path: '/operators'
        },
        {
            title: "Máquinas",
            description: "Control y gestión de máquinas",
            icon: <FaCogs size={32} />,
            path: '/machines'
        }
    ];

    const handleNavigation = (path) => {
        // Primero animamos la salida
        const container = document.querySelector('.homepage-content');
        container.style.opacity = '0';
        container.style.transform = 'translateY(-20px)';
        
        // Después de la animación, navegamos
        setTimeout(() => {
            navigate(path);
        }, 200);
    };

    const cardVariants = {
        hidden: { opacity: 0, y: 20 },
        visible: (index) => ({
            opacity: 1,
            y: 0,
            transition: {
                delay: index * 0.1,
                duration: 0.5,
                ease: "easeOut"
            }
        })
    };

    return (
        <div className="homepage">
            <CompNavbar />
            <PageTransition>
                <Container className="py-5 homepage-content">
                    <motion.div 
                        className="text-center mb-5"
                        initial={{ opacity: 0, y: -20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5 }}
                    >
                        <h1 className="company-title mb-3">AVSA</h1>
                        <p className="company-subtitle">Sistema de Gestión y Control de Producción</p>
                    </motion.div>

                    <Row className="g-4">
                        {menuItems.map((item, index) => (
                            <Col md={6} lg={3} key={index}>
                                <motion.div
                                    variants={cardVariants}
                                    initial="hidden"
                                    animate="visible"
                                    custom={index}
                                >
                                    <Card className="menu-card h-100">
                                        <Card.Body className="d-flex flex-column">
                                            <motion.div 
                                                className="icon-wrapper mb-4"
                                                whileHover={{ scale: 1.1 }}
                                                transition={{ type: "spring", stiffness: 400, damping: 10 }}
                                            >
                                                {item.icon}
                                            </motion.div>
                                            <Card.Title className="fw-bold mb-3">
                                                {item.title}
                                            </Card.Title>
                                            <Card.Text className="text-muted flex-grow-1">
                                                {item.description}
                                            </Card.Text>
                                            <motion.div
                                                whileHover={{ scale: 1.02 }}
                                                whileTap={{ scale: 0.98 }}
                                            >
                                                <Button 
                                                    variant="outline-primary" 
                                                    className="mt-3"
                                                    onClick={() => handleNavigation(item.path)}
                                                >
                                                    Acceder
                                                </Button>
                                            </motion.div>
                                        </Card.Body>
                                    </Card>
                                </motion.div>
                            </Col>
                        ))}
                    </Row>
                </Container>
            </PageTransition>
            <Footer />
        </div>
    );
}
