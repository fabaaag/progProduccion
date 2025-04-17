import React, { useState, useEffect } from "react";
import './Navbar.css'

const ThemeToggleButton = () => {
    const[isDarkMode, setIsDarkMode] = useState(false);

    //cargar la preferencia desde local storage
    useEffect(() => {
        const savedTheme = localStorage.getItem("theme");
        if (savedTheme === 'dark'){
            setIsDarkMode(true);
            document.body.classList.add("dark-mode");
        }
    }, []);

    const toggleTheme = () => {
        setIsDarkMode((prev) => !prev);

        if(!isDarkMode){
            document.body.classList.add("dark-mode");
            localStorage.setItem("theme", "dark")
        }else{
            document.body.classList.remove("dark-mode");
            localStorage.setItem("theme", "light");
        }
    };

    return (
        <button 
        onClick={toggleTheme} 
        style={{
            padding: "10px 20px",
            backgroundColor: isDarkMode ? "#333" : "#ddd",
            color: isDarkMode ? "#fff" : "#000",
            border: "none",
            cursor: "pointer",
        }}
        >
        {isDarkMode ? "☀️" : "🌙"}    
        </button>
    )
}

export default ThemeToggleButton;