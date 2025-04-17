import { useNavigate } from "react-router-dom";


export function ProgramaCard({ program }){
    const navigate = useNavigate();
    return (
        <div className=""
        onClick={()=>{
            navigate(`/programs/${program.id}`)
        }}
        >
            <h1 className="">Programa - {`${program.nombre}`}</h1>
            <h4>{`${program.fecha_inicio}`}</h4>

        </div>
        
    )
}