import { useNavigate } from "react-router-dom";

export function OrderCard({ order }) {
    const navigate = useNavigate()
    return (
        <div className=""
        onClick={()=>{
            navigate(`/orders/${order.codigo_ot}`)
        }}
        >
            <h1 className="">Orden - {`${order.codigo_ot}`}</h1>
            <h3>{`${order.descripcion_producto_ot}`}</h3>
        </div>
    )
}