"""
Configuration settings for the FastAPI backend.
"""

# CORS Configuration
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173",  # Vite default port
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:5173",
]

CORS_SETTINGS = {
    "allow_origins": CORS_ORIGINS,
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}

# Server Configuration
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8000
DEBUG_MODE = True

# API Configuration
API_PREFIX = "/api"
API_VERSION = "v1"

# Simulation metadata (names only for now)
SIMULATION_LIST = [
    {"id": 1, "name": "Convolution Simulation", "description": "Visualize convolution operations"},
    {"id": 2, "name": "Fourier Series Visualization", "description": "Explore Fourier series decomposition"},
    {"id": 3, "name": "Fourier Analysis: Phase Vs Magnitude", "description": "Analyze magnitude and phase spectra"},
    {"id": 4, "name": "RC Lowpass Filter", "description": "Interactive RC filter simulation"},
    {"id": 5, "name": "Second-Order System Response", "description": "Explore second-order system dynamics and frequency response"},
    {"id": 6, "name": "Aliasing & Quantization", "description": "Demonstrate sampling effects"},
    {"id": 7, "name": "Amplifier Topologies", "description": "Simulate amplifier circuits"},
    {"id": 8, "name": "Feedback System Analysis", "description": "Explore feedback in amplifiers"},
    {"id": 9, "name": "DC Motor Simulation", "description": "Model DC motor dynamics"},
    {"id": 10, "name": "Furuta Pendulum", "description": "Control system for inverted pendulum"},
    {"id": 11, "name": "CT/DT Poles Conversion", "description": "Convert between continuous and discrete poles"},
    {"id": 12, "name": "Lens Convolution", "description": "Optical system convolution"},
    {"id": 13, "name": "Modulation Techniques", "description": "AM, FM, and digital modulation"},
]
