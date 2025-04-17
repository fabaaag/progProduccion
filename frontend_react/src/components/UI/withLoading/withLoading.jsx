import React from 'react';
import { LoadingSpinner } from '../LoadingSpinner/LoadingSpinner';

export const withLoading = (WrappedComponent) => {
    return function WithLoadingComponent({ isLoading, loadingMessage, ...props }) {
        return (
            <div className="position-relative">
                {isLoading && (
                    <LoadingSpinner 
                        message={loadingMessage} 
                        containerStyle="content"
                    />
                )}
                <div style={{ opacity: isLoading ? 0.5 : 1 }}>
                    <WrappedComponent {...props} />
                </div>
            </div>
        );
    };
};