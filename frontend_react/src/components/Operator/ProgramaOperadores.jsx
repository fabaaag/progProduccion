import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Table, Card, Button, Toast } from 'react-bootstrap';
import { getAsignacionesPrograma } from '../../api/operator.api.js';
import { toast } from 'react-hot-toast';

export function ProgramaOperadores(){
    const { programaId } = useParams();
    const [asignaciones, setAsignaciones] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadAsignaciones();
    }, [programaId]);

    const loadAsignaciones = async () => {
        try{
            const data = await getAsignacionesPrograma(programaId);
            setAsignaciones(data);
        } catch (error) {
            toast.error('Error al cargar las asignaciones');
        } finally {
            setLoading(false);
        }
    };

    return(
        <Card>
            <Card.Header><h5>Asignación de Operadores</h5></Card.Header>
            <Card.Body>
                <Table responsive>
                    <thead>
                        <tr>
                            <th>Operador</th>
                            <th>Máquina</th>
                            <th>Proceso</th>
                            <th>Fecha</th>
                        </tr>
                    </thead>
                    <tbody>
                        {asignaciones.map(asignacion => (
                            <tr key={asignacion.id}>
                                <td>{asignacion.operador.nombre}</td>
                                <td>{asignaciones.maquina.descripcion}</td>
                                <td>{asignacion.proceso.descripcion}</td>
                                <td>{asignacion.fecha_asignacion}</td>
                            </tr>
                        ))}
                    </tbody>
                </Table>
            </Card.Body>
        </Card>
    )
}