import React from 'react';
import PaginacionBase from '../../Shared/Tables/PaginacionBase';

const PaginacionPiezas = ({ currentPage, totalPages, handlePageChange }) => {
    return (
        <PaginacionBase
            currentPage={currentPage}
            totalPages={totalPages}
            handlePageChange={handlePageChange}
            maxVisiblePages={5}
        />
    );
};

export default PaginacionPiezas;