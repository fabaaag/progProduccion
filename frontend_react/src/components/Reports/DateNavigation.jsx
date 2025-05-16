import React from 'react';
import { ButtonGroup, Button } from 'react-bootstrap';
import { FaChevronLeft, FaChevronRight, FaCalendarAlt } from 'react-icons/fa';
import DatePicker, { registerLocale } from 'react-datepicker';
import es from 'date-fns/locale/es';
import "react-datepicker/dist/react-datepicker.css";
import './css/DateNavigation.css';

// Registramos el locale español
registerLocale('es', es);

export const DateNavigation = ({ currentDate, onDateChange, programStartDate, programEndDate }) => {
    // Función para verificar si es día laborable (no sábado ni domingo)
    const isWorkingDay = (date) => {
        const day = date.getDay();
        return day !== 0 && day !== 6; // 0 es domingo, 6 es sábado
    };

    // Función para obtener el siguiente día laborable
    const getNextWorkingDay = (date) => {
        const nextDate = new Date(date);
        nextDate.setDate(nextDate.getDate() + 1);
        while (!isWorkingDay(nextDate)) {
            nextDate.setDate(nextDate.getDate() + 1);
        }
        return nextDate;
    };

    // Función para obtener el día laborable anterior
    const getPreviousWorkingDay = (date) => {
        const prevDate = new Date(date);
        prevDate.setDate(prevDate.getDate() - 1);
        while (!isWorkingDay(prevDate)) {
            prevDate.setDate(prevDate.getDate() - 1);
        }
        return prevDate;
    };

    // Función para verificar si una fecha está dentro del rango del programa
    const isWithinProgramDates = (date) => {
        return date >= new Date(programStartDate) && date <= new Date(programEndDate);
    };

    const handlePreviousDay = () => {
        const prevDate = getPreviousWorkingDay(currentDate);
        if (isWithinProgramDates(prevDate)) {
            onDateChange(prevDate);
        }
    };

    const handleNextDay = () => {
        const nextDate = getNextWorkingDay(currentDate);
        if (isWithinProgramDates(nextDate)) {
            onDateChange(nextDate);
        }
    };

    const handleDateChange = (date) => {
        if (!date) return;
        
        // Si el día seleccionado no es laborable, encontrar el siguiente día laborable
        let targetDate = date;
        if (!isWorkingDay(targetDate)) {
            targetDate = getNextWorkingDay(date);
        }

        // Verificar que la fecha esté dentro del rango del programa
        if (isWithinProgramDates(targetDate)) {
            onDateChange(targetDate);
        }
    };

    // Función para filtrar las fechas disponibles en el DatePicker
    const filterDate = (date) => {
        return isWorkingDay(date) && isWithinProgramDates(date);
    };

    const formatDate = (date) => {
        if (!date) return '';
        
        // Crear una copia para evitar modificar la fecha original
        const displayDate = new Date(date);
        
        // Log para depuración
        console.log("Fecha recibida:", date);
        console.log("Fecha que se va a mostrar:", displayDate);
        console.log("Fecha formateada:", displayDate.toLocaleDateString('es-ES', { 
            weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' 
        }));
        
        // Formatear la fecha
        return displayDate.toLocaleDateString('es-ES', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    };

    return (
        <div className="date-navigation">
            <div className="navigation-container">
                <h2 className="page-title">Reporte Supervisor</h2>
                <div className="date-controls">
                    <ButtonGroup>
                        <Button 
                            variant="outline-primary" 
                            onClick={handlePreviousDay}
                            disabled={!currentDate || new Date(currentDate) <= new Date(programStartDate)}
                            className="nav-button"
                        >
                            <FaChevronLeft />
                        </Button>
                        <DatePicker
                            selected={currentDate}
                            onChange={handleDateChange}
                            locale="es"
                            dateFormat="dd/MM/yyyy"
                            minDate={new Date(programStartDate)}
                            maxDate={new Date(programEndDate)}
                            filterDate={filterDate}
                            className="date-picker-input"
                            customInput={
                                <Button variant="light" className="date-button">
                                    <FaCalendarAlt className="calendar-icon" />
                                    <span className="date-text">
                                        {formatDate(currentDate)}
                                    </span>
                                </Button>
                            }
                        />
                        <Button 
                            variant="outline-primary" 
                            onClick={handleNextDay}
                            disabled={!currentDate || new Date(currentDate) >= new Date(programEndDate)}
                            className="nav-button"
                        >
                            <FaChevronRight />
                        </Button>
                    </ButtonGroup>
                </div>
            </div>
        </div>
    );
};