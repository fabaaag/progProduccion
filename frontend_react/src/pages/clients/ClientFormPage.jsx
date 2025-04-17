import { useForm } from 'react-hook-form';
import { createClient, deleteClient, updateClient, getClient } from '../../api/clients.api.js';
import { replace, useNavigate, useParams } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { toast } from 'react-hot-toast';
import CompNavbar from '../../components/Navbar/compNavbar.jsx';


export function ClientFormPage() {
  const {register, handleSubmit,
    formState:{errors},
    setValue
  } = useForm();


  const navigate = useNavigate();
  const params = useParams();
  
  const onSubmit = handleSubmit(async data =>{
    if(params.id){
      console.log('actualizando');
      await updateClient(params.id, data)
      toast.success('Cliente actualizado',{
        position:"bottom-right",
        style:{
          background:"#101010",
          color:"#fff"
        }
      })
    }else{
      const res = await createClient(data);
      toast.success('Cliente creado', {
        position:"bottom-right",
        style:{
          background:"#101010",
          color:"#fff"
        }
      })
    }
    navigate("/clients");
  });

  useEffect(()=>{
    async function loadClient() {
      if(params.id){
        const {data} = await getClient(params.id);
        setValue('codigo_cliente', data.codigo_cliente)
        setValue('nombre', data.nombre)
        setValue('vip', data.vip)
        setValue('apodo', data.apodo)
      }
    }
    loadClient();
  }, []);

  const[theme, setTheme] = useState('light');
  return (
    <div className={`container${theme}`}>
      <CompNavbar />
      <div className=''>
      <h1 className='h1'>Cliente</h1>
      <hr />
      <form onSubmit={onSubmit} >
        <div className='d-flex flex-column mx-5'>
          <label className='form-label' htmlFor="codigo">Código Cliente</label>
          <input type="text" name='codigo' className='form-control' {...register("codigo_cliente", {required:true})} />
          {errors.codigo_cliente && <span>Este campo es requerido.</span>}
          <br />
          <label className='form-label' htmlFor="nombre">Nombre Cliente</label>
          <input type="text" name='nombre' className='form-control' {...register("nombre", {required:true})} />
          {errors.nombre && <span>Este campo es requerido.</span>}
          <br />
          <div className='d-flex gap-2'><label className='form-label' htmlFor="vip">¿VIP?</label>
          <input type="checkbox" className='form-check-input mt-1' name="vip" {...register("vip",{required:false}, {default:false})}/></div>
          <br />
          <label htmlFor="apodo">Apodo Cliente</label>
          <input type="text"  className='form-control' name='apodo' {...register("apodo", {required:true})} />
          {errors.apodo && <span>Este campo es requerido.</span>}
        </div>
      </form>
      <div className='btn-group mt-4 d-flex justify-content-center'>
      {params.id && (
        <div className='d-flex gap-3'>
          <button className='btn btn-primary' onClick={onSubmit}>Guardar</button>
          <button className='btn btn-danger' onClick={async ()=> {
            const accepted = window.confirm(`¿Estás seguro que deseas eliminar al cliente ${cliente.nombre}?`);
            if(accepted){
              await deleteClient(params.id);
              toast.success('Cliente eliminado.',{
                position:"bottom-right",
                style:{
                  background:"#101010",
                  color:"#fff"
                }
              })
              navigate("/clients");
            }
          }}>Eliminar</button>
        </div>
      )}
      </div>
    </div>
    </div>
  );
}