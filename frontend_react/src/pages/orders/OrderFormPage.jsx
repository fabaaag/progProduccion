import { useForm } from "react-hook-form";
import { createOrder, deleteOrder, updateOrder, getOrder } from "../../api/orders.api";
import { replace, useNavigate, useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { toast } from "react-hot-toast";
import CompNavbar from "../../components/Navbar/CompNavbar";
import TipoOTSelect from "../../components/Orders/TipoOTList";
import SituacionOTSelect from "../../components/Orders/SituacionOTList";

export function OrderFormPage(){
    const {register, handleSubmit,
        formState:{errors}, 
        setValue
    } = useForm();

    const navigate = useNavigate();
    const params  = useParams();

    const onSubmit = handleSubmit(async data =>{
        if(params.id){  
            console.log('actualizando');
            await updateOrder(params.id, data)
            toast.success('Orden actualizada', {
                position:"bottom-right",
                style:{
                    background:"#101010",
                    color:"#fff"
                }
            })
        }else{
            const res = await createOrder(data);
            toast.success('Orden creada', {
                position:"bottom-right",
                style:{
                    background:"#101010",
                    color:"#fff"
                }
            })
        }
        navigate("/orders");
    });
    
    useEffect(()=>{
        async function loadOrder(){
            if (params.id){
                const {data} = await getOrder(params.id);
                setValue('codigo_ot', data.codigo_ot)
                setValue('tipo_ot', data.tipo_ot.codigo_tipo_ot)
                setValue('situacion_ot', data.situacion_ot.codigo_situacion_ot)
                setValue('fecha_emision', data.fecha_emision)
                setValue('fecha_proc', data.fecha_proc)
                setValue('fecha_termino', data.fecha_termino)
                setValue('cliente', data.cliente.nombre)
                setValue('nro_nota_venta_ot', data.nro_nota_venta_ot)
                setValue('item_nota_venta', data.item_nota_venta)
                setValue('referencia_nota_venta', data.referencia_nota_venta)
                setValue('codigo_producto_inicial', data.codigo_producto_inicial)
                setValue('codigo_producto_salida', data.codigo_producto_salida)
                setValue('descripcion_producto_ot', data.descripcion_producto_ot)
                setValue('cantidad', data.cantidad)
                setValue('unidad_medida', data.unidad_medida_codigo_und_medida)
                setValue('cantidad_avance', data.cantidad_avance)
                setValue('peso_unitario', data.peso_unitario)
                setValue('materia_prima', data.materia_prima.nombre)
                setValue('cantidad_mprima', data.cantidad_mprima)
                setValue('unidad_medida_mprima', data.unidad_medida_mprima.codigo_und_medida)
                setValue('observacion_ot', data.observacion_ot)
                setValue('empresa', data.empresa.apodo)
                setValue('multa', data.multa)
            }
        }
        loadOrder();
    }, []);

    const[theme, setTheme] = useState('light');
    return (
        <div className={`container${theme}`}>
            <CompNavbar />
            <div className="">
                <h1 className="h1">Orden</h1>
                <hr />
                <form onSubmit={onSubmit}>
                    <div className="d-flex flex-column mx-5">
                        <label htmlFor="codigo_ot" className="form-label">Código OT</label>
                        <input type="text" name='codigo_ot' className="form-control" {...register ("codigo_ot", {required:true})} />
                        {errors.codigo_ot && <span>Este campo es requerido.</span>}
                        <br />

                        <label htmlFor="tipo_ot" className="form-label">Tipo OT</label>
                        <TipoOTSelect onchange={(value) => setValue('tipo_ot', value)} />

                        <label htmlFor="situacion_ot">Situacion OT</label>
                        <SituacionOTSelect onchange={(value) => setValue('situacion_ot', value)} />

                        <label htmlFor="fecha_inicio" className="form-label">Fecha Inicio</label>
                        <input type="date" name="fecha_inicio" className="form-control" />

                        <label htmlFor="fecha_proc" className="form-label"></label>
                    </div>
                </form>
            </div>
        </div>

    )
}
