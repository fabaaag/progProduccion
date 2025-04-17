import React, { useEffect, useState } from "react";
import axios from "axios";

const SituacionOTSelect = ({ onChange }) => {
    const[situaciones, setSituaciones] = useState();
    const[situacionSeleccionada, setSituacionSeleccionada] = useState("");

    useEffect(() => {
        axios
        .get("http://localhost:8000/gestion/api/v1/situaciones_ot/")
        .then((response) => setSituaciones(response.data))
        .catch((error) => console.error("Error al cargar las SituacionOT:", error));
    }, []);

    const handleSituacionOTChange = (event) => {
        const value = event.target.value;
        setSituacionSeleccionada(value);
        onChange && onChange(value);
    };

    return (
        <select value={situacionSeleccionada} onChange={handleSituacionOTChange}>
            <option value="" disabled>---Seleccionar SituacionOT---</option>
            {situaciones.map((situacion) => (
                <option key={situacion.id} value={situacion.id}>
                    {situacion.codigo_situacion_ot}-{situacion.descripcion}
                </option>
            ))}
        </select>
    );
};

export default SituacionOTSelect;