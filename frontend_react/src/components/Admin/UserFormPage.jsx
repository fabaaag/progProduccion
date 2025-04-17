import { useState, useEffect } from 'react';
import { Form, Button, Container, Card } from 'react-bootstrap';
import CompNavbar from '../../components/Navbar/CompNavbar';
import { createUser, updateUser, getUserById } from '../../api/users.api';
import { toast } from 'react-hot-toast';
import { useParams, useNavigate } from 'react-router-dom';

export function UserFormPage() {
    const { id } = useParams();
    const navigate = useNavigate();
    const isEditing = !!id;

    const [userData, setUserData] = useState({
        username: '',
        password: '',
        first_name: '',
        last_name: '',
        email: '',
        rut: '',
        telefono:'',
        cargo:'',
        rol: 'OPERADOR',
        activo: true
    });

    useEffect(() => {
        if (isEditing){
            loadUser();
        }
    }, [id]);

    const loadUser = async () => {
        try{
            const data = await getUserById(id);
            const { password, ...userWithoutPassword } = data;
            setUserData(userWithoutPassword);
            setOriginalData(userWithoutPassword);
        } catch (error) {
            toast.error('Error al cargar el usuario');
            navigate('/users/manage');
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const dataToSubmit = { ...userData };
            
            //Si estamos editando y el RUT no ha cambiado, lo eliminamos
            if (isEditing && originalData && originalData.rut === userData.rut) {
                delete dataToSubmit.rut;
            }

            console.log('Datos a enviar:', dataToSubmit);

            if (isEditing) {
                console.log('Actualizando usuario:', dataToSubmit);
                await updateUser(id, dataToSubmit);
                toast.success('Usuario actualizado correctamente');
            } else {
                console.log('Creando usuario:', dataToSubmit);
                await createUser(dataToSubmit);
                toast.success('Usuario creado exitósamente');
            }
            navigate('/users/manage');
        
        } catch (error){
            console.error('Error completo:', error.response?.data);;
            const errorMessage = error.response?.data?.rut?.[0] || error.response?.data?.error || 'Error al procesar la solicitud';
            toast.error(errorMessage);
        }
    };

    const [originalData, setOriginalData] = useState(null);

    return (
        <>
            <CompNavbar />
            <Container className='mt-4'>
                <Card>
                    <Card.Header>
                        <h3>{isEditing ? 'Editar Usuario' : 'Crear Usuario'}</h3>
                    </Card.Header>
                    <Card.Body>
                        <Form onSubmit={handleSubmit}>
                            <Form.Group className='mb-3'>
                                <Form.Label>Nombre de Usuario</Form.Label>
                                <Form.Control
                                type="text"
                                value={userData.username}
                                onChange={(e) => setUserData({...userData, username: e.target.value})}
                                disabled= {isEditing}
                                required
                                />
                            </Form.Group>

                            {!isEditing && (
                                <Form.Group className='mb-3'>
                                    <Form.Label>Contraseña</Form.Label>
                                    <Form.Control
                                        type="password"
                                        value={userData.password}
                                        onChange={(e) => setUserData({...userData, password: e.target.value})}
                                        required={!isEditing}
                                    />
                                </Form.Group>
                            )}
                            
                            <Form.Group className='mb-3'>
                                <Form.Label>Nombre</Form.Label>
                                <Form.Control
                                    type='text'
                                    value={userData.first_name}
                                    onChange={(e) => setUserData({...userData, first_name: e.target.value})}
                                />
                            </Form.Group>
                            <Form.Group className='mb-3'>
                                <Form.Label>Apellido</Form.Label>
                                <Form.Control
                                    type='text'
                                    value={userData.last_name}
                                    onChange={(e) => setUserData({...userData, last_name: e.target.value})}
                                />
                            </Form.Group>
                            <Form.Group className='mb-3'>
                                <Form.Label>Email</Form.Label>
                                <Form.Control
                                    type='email'
                                    value={userData.email}
                                    onChange={(e) => setUserData({...userData, email: e.target.value})}
                                />
                            </Form.Group>
                            <Form.Group className='mb-3'>
                                <Form.Label>RUT</Form.Label>
                                <Form.Control
                                    type='text'
                                    value={userData.rut}
                                    onChange={(e) => {
                                        // Opcional: Añadir validación de formato RUT aquí
                                        setUserData({...userData, rut: e.target.value});
                                    }}
                                    placeholder="12.345.678-9"
                                    disabled={isEditing} //Deshabilitamos la edición del RUT en modo edición
                                />
                            </Form.Group>
                            <Form.Group className='mb-3'>
                                <Form.Label>Teléfono</Form.Label>
                                <Form.Control
                                    type='text'
                                    value={userData.telefono}
                                    onChange={(e) => setUserData({...userData, telefono: e.target.value})}
                                />
                            </Form.Group>
                            <Form.Group className="mb-3">
                                <Form.Label>Cargo</Form.Label>
                                <Form.Select
                                    value={userData.rol}
                                    onChange={(e) => setUserData({...userData, rol: e.target.value})}
                                >
                                    <option value="ADMIN">Administrador</option>
                                    <option value="SUPERVISOR">Supervisor</option>
                                    <option value="OPERADOR">Operador</option>
                                </Form.Select>
                            </Form.Group>
                            <Form.Group className='mb-3'>
                                <Form.Check
                                    type='checkbox'
                                    label='Usuario Activo'
                                    checked={userData.activo}
                                    onChange={(e) => setUserData({...userData, activo: e.target.checked})}
                                />
                            </Form.Group>
                            <div className='d-flex gap-2'>
                                <Button variant="primary" type='submit'>
                                    {isEditing ? 'Actualizar' : 'Crear'} Usuario
                                </Button>

                                <Button 
                                variant="secondary"
                                onClick={() => navigate('/users/manage')}
                                >
                                    Cancelar
                                </Button>      
                            </div>
                        </Form>
                    </Card.Body>
                </Card>
            </Container>
        </>
    )
}
