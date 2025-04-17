import { useNavigate } from "react-router-dom"

export function ClientCard({ client }) {
    const navigate = useNavigate()
    return (
    <div className=""
        onClick={()=>{
            navigate(`/clients/${client.codigo_cliente}`)
        }}
    >
        <h1 className="">Cliente - {`${client.codigo_cliente}`}</h1>
        <h3>{`${client.nombre}`}</h3>
    </div>
  )
}
