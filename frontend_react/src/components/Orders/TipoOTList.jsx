import React, { useEffect, useState } from "react";
import axios from "axios";

const TipoOTSelect = ({ onChange }) =>{
    const [tipos, setTipos] = useState();
    const [tipoSeleccionado, setTipoSeleccionado] = useState("");

    useEffect(() => {
        axios
            .get("http://localhost:8000/gestion/api/v1/tipos_ot/")
            .then((response) => setTipos(response.data))
            .catch((error) => console.error("Error al cargar los TipoOT: ", error));
    }, []);

    const handleTipoOTChange = (event) => {
        const value = event.target.value;
        setTipoSeleccionado(value);
        onChange && onChange(value);
    };

    return (
        <select value={tipoSeleccionado} onChange={handleTipoOTChange} className="form-control">
                <option value="" disabled>---Seleccionar TipoOT---</option>
                {tipos.map((tipo) => (
                    <option key={tipo.id} value={tipo.id}>
                        {tipo.codigo_tipo_ot}-{tipo.descripcion}
                    </option>
                ))}
        </select>
    );
};

export default TipoOTSelect;