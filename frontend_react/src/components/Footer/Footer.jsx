import React from 'react';
import { Container, Row, Col } from 'react-bootstrap';
import logavsa from './img/logavsa.png';
import './Footer.css';

export function Footer() {
    return (
        <footer className="footer">
            <Container fluid>
                <Row className="footer-content align-items-center">
                    <Col xs={12} md={6} className="text-center text-md-start">
                        <img src={logavsa} alt='logo' className="footer-logo" />
                        <span className="company-name">Abasolo Vallejo</span>
                    </Col>
                    <Col xs={12} md={6} className="text-center text-md-end">
                        <p className="version-info">Versión 1.0.0</p>
                        <p className="copyright">
                            © {new Date().getFullYear()} Abasolo Vallejo - Uso Interno
                        </p>
                    </Col>
                </Row>
            </Container>
        </footer>
    );
}

