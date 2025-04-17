import React from 'react';
import './LoadingSpinner.css';
import { motion } from 'framer-motion';
import { FaCog } from 'react-icons/fa';

export function LoadingSpinner({ 
    message = "Cargando...", 
    overlay = false, 
    size = "normal",
    containerStyle = "content"
}) {
    const getContainerClass = () => {
        let className = "loader-container";
        if (overlay) className += " overlay";
        if (containerStyle === "content") className += " content-loader";
        if (size === "small") className += " small-loader";
        return className;
    };

    return (
        <motion.div 
            className={getContainerClass()}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
        >
            <div className="loader-content">
                <div className="spinner-container">
                    <svg className="progress-ring" width="80" height="80">
                        <circle
                            className="progress-ring__circle-bg"
                            stroke="#e6e6e6"
                            strokeWidth="4"
                            fill="transparent"
                            r="34"
                            cx="40"
                            cy="40"
                        />
                        <circle
                            className="progress-ring__circle"
                            stroke="#004b93"
                            strokeWidth="4"
                            fill="transparent"
                            r="34"
                            cx="40"
                            cy="40"
                        />
                    </svg>
                    
                    <motion.div 
                        className="icon-container"
                        animate={{ 
                            rotate: 360
                        }}
                        transition={{
                            duration: 2,
                            repeat: Infinity,
                            ease: "linear"
                        }}
                    >
                        <FaCog className="spinning-icon" />
                    </motion.div>
                </div>
                
                <motion.p 
                    className="loading-text"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5 }}
                >
                    {message}
                </motion.p>
            </div>
        </motion.div>
    );
}

export default LoadingSpinner;