import {BrowserRouter, Routes, Route, Navigate} from 'react-router-dom';
import { ClientPage } from './pages/clients/ClientPage';
import { ClientFormPage } from './pages/clients/ClientFormPage';
import { HomePage } from './pages/HomePage';
import { OrderPage } from './pages/orders/OrderPage';
import { OrderFormPage } from './pages/orders/OrderFormPage';
import { ProgramPage } from './pages/programs/ProgramPage';
import { ProgramFormPage } from './pages/programs/ProgramFormPage';
import { ProgramDetail } from './pages/programs/ProgramDetail';
import { Toaster } from 'react-hot-toast';
import { ProtectedRoute } from './components/ProtectedRoute/ProtectedRoute';
import { Login } from './components/Login/Login';
import { ProfilePage } from './components/Login/ProfilePage';
import { UserManagementPage  } from './components/Admin/UserManagementPage';
import { UserFormPage } from './components/Admin/UserFormPage';
import { OperatorManagementPage } from './components/Operator/OperatorManagementPage';
import { ProgramaOperadores } from './components/Operator/ProgramaOperadores';
import { MachineList } from './components/Machine/MachineList';
import { DiagnosticoMaquinas } from './components/Machine/DiagnosticoMaquinas';
import { ReporteSupervisor } from './pages/programs/ReporteSupervisor';
import { ProductosList } from './components/Productos/Productos/ProductosList';
import { PiezasList } from './components/Productos/Piezas/PiezasList';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Rutas públicas */}
        <Route path='login/' element={<Login/>} />

        {/*Ruta por defecto -  redirige a login si no está autenticado */}      
        <Route path='/' element={<Navigate to="/home"/>}/>

        {/* Rutas protegidas */}
        <Route path='/profile' element={
          <ProtectedRoute>
            <ProfilePage/>
          </ProtectedRoute>
        }/>
        <Route path='/home' element={
          <ProtectedRoute>
            <HomePage/>
          </ProtectedRoute>}
        />
        <Route path='/clients' element={
          <ProtectedRoute allowedRoles={['ADMIN', 'SUPERVISOR']}>
            <ClientPage/>
          </ProtectedRoute>}
        />
        <Route path='clients-create' element={
          <ProtectedRoute allowedRoles={['ADMIN', 'SUPERVISOR']}>
            <ClientFormPage/>
          </ProtectedRoute>
        }
        />
        <Route path='/clients/:id' element={
          <ProtectedRoute allowedRoles={['ADMIN', 'SUPERVISOR']}>
            <ClientFormPage/>
          </ProtectedRoute>
        }/>
        <Route path='/orders' element={
          <ProtectedRoute allowedRoles={['ADMIN', 'SUPERVISOR']}>
            <OrderPage/>
          </ProtectedRoute>
        }/>
        <Route path='/orders/:id/orders-detail' element={
          <ProtectedRoute allowedRoles={['ADMIN', 'SUPERVISOR']}>
            <OrderFormPage/>
          </ProtectedRoute>
        }
        />
        <Route path='/orders/:id' element={
          <ProtectedRoute allowedRoles={['ADMIN', 'SUPERVISOR']}>
            <OrderFormPage/>
          </ProtectedRoute>
        }/>
        <Route path='/programs' element={
          <ProtectedRoute allowedRoles={['ADMIN', 'SUPERVISOR']}>
            <ProgramPage/>
          </ProtectedRoute>
        }/>
        <Route path='/programs-create' element={
          <ProtectedRoute allowedRoles={['ADMIN', 'SUPERVISOR']}>
            <ProgramFormPage/>
          </ProtectedRoute>
        }/>
        <Route path='/programs/:programId' element={
          <ProtectedRoute allowedRoles={['ADMIN', 'SUPERVISOR']}>
            <ProgramDetail/>
          </ProtectedRoute>
        }/>
        <Route path='/programs/:programId/operadores' element={
          <ProtectedRoute allowedRoles={['ADMIN', 'SUPERVISOR']}>
            <ProgramaOperadores/>
          </ProtectedRoute>
        }/>
        <Route path="/operators" element={
          <ProtectedRoute allowedRoles={['ADMIN', 'SUPERVISOR']}>
            <OperatorManagementPage/>
          </ProtectedRoute>
        }/>
        <Route path="/users/manage" element={
          <ProtectedRoute allowedRoles={['ADMIN', ]}>
            <UserManagementPage />
          </ProtectedRoute>
        }/>
        <Route path="/users/create" element={
          <ProtectedRoute allowedRoles={['ADMIN', ]}>
            <UserFormPage />
          </ProtectedRoute>
        }/>
        <Route path="/users/edit/:id" element={
          <ProtectedRoute allowedRoles={['ADMIN', ]}>
            <UserFormPage />
          </ProtectedRoute>
        }/>
        <Route path="/machines" element={
          <ProtectedRoute allowedRoles={['ADMIN', 'SUPERVISOR']}>
            <MachineList/>
          </ProtectedRoute>
        }/>
        <Route path="/machines-diagnostico" element={
          <ProtectedRoute allowedRoles={['ADMIN', 'SUPERVISOR']}>
            <DiagnosticoMaquinas/>
          </ProtectedRoute>
        }/>
        <Route path="/programs/:programId/supervisor-report" element={
          <ProtectedRoute allowedRoles={['ADMIN', 'SUPERVISOR']}>
            <ReporteSupervisor/>
          </ProtectedRoute>
        }/>
        <Route path="/productos" element={
          <ProtectedRoute allowedRoles={['ADMIN', 'SUPERVISOR']}>
            <ProductosList/>
          </ProtectedRoute>
        }/>
        <Route path="/piezas" element={
          <ProtectedRoute allowedRoles={['ADMIN', 'SUPERVISOR']}>
            <PiezasList/>
          </ProtectedRoute>
        }/>
      </Routes>
      <Toaster/>
    </BrowserRouter>
  )
}

export default App;

/*//<Route path="*" element={<Navigate to="/login"/>}/>*/