import React from 'react';
import { Pagination } from 'react-bootstrap';
import '../css/PaginacionBase.css';

const PaginacionBase = ({
    currentPage,
    totalPages,
    handlePageChange,
    maxVisiblePages = 5,
}) => {
    if (totalPages <=1) return null;

    let items = [];
    let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

    //Ajustar el rango si no tenemos suficientes páginas al final
    if (endPage - startPage + 1 < maxVisiblePages) {
        startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }

    // Primera página y elipsis si es necesario
    if (startPage > 1){
        items.push(
            <Pagination.Item
                key="first-page"
                onClick={() => handlePageChange(1)}
            >
                1
            </Pagination.Item>
        );
        if (startPage > 2){
            items.push(<Pagination.Ellipsis key="ellipsis-start" disables />);
        }
    }

    // Páginas numeradas
    for (let number = startPage; number <= endPage; number++){
        items.push(
            <Pagination.Item
                key={`page-${number}`}
                active={number === currentPage}
                onClick={() => handlePageChange(number)}
            >
                {number}
            </Pagination.Item>
        );
    }

    // Última página y elipsis si es necesario
    if (endPage < totalPages) {
        if (endPage < totalPages - 1){
            items.push(<Pagination.Ellipsis key="ellipsis-end" disabled />);
        }
        items.push(
            <Pagination.Item
                key="last-page"
                onClick={() => handlePageChange(totalPages)}
            >
                {totalPages}
            </Pagination.Item>
        );
    }

    return (
        <div className="paginacion-container">
            <Pagination>
                <Pagination.Prev
                    onClick={() => handlePageChange(currentPage + 1)}
                    disabled={currentPage === totalPages}
                />
                {items}
                <Pagination.Next
                    onClick={() => handlePageChange(currentPage + 1)}
                    disabled={currentPage === totalPages}
                />
            </Pagination>
        </div>
    );
};

export default PaginacionBase;