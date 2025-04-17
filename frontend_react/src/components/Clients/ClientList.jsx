import { useEffect, useState } from "react"
import {getAllClients} from '../../api/clients.api'
import CompNavbar from '../Navbar/CompNavbar.jsx'
import { useNavigate } from "react-router-dom"

export function ClientList() {

    const[clients, setClients] = useState([]);

    useEffect(()=>{
        
        async function loadClients(){
            const res = await getAllClients();
            setClients(res.data);
        }
        loadClients();
    }, []);
    const[theme, setTheme] = useState('light');
    const navigate = useNavigate()
    return (
    <div className={`container${theme}`}>
        <compNavbar />
        <br />
        <div className="client-list">
        <table className="table table-hover">
            <thead>
            <tr className={theme == 'light' ? "table-dark" : "table-primary"}>
                <th>Código Cliente</th>
                <th>Nombre</th>
                <th>¿VIP?</th>
                <th>Apodo</th>
                <th>-</th>
            </tr>
            </thead>
            <tbody>
            {clients.map(client=>(
                <tr key={client.id}>
                    <td>{client.codigo_cliente}</td>
                    <td>{client.nombre}</td>
                    <td>{client.vip}</td>
                    <td>{client.apodo}</td>
                    <td>
                        <button className="btn btn-primary"
                        onClick={()=>{
                            navigate(`/clients/${client.id}`)
                        }}
                        >Ver</button>
                    </td>
                </tr>
            ))}
            </tbody>
        </table>
    </div>
    </div>
  );
  
}
