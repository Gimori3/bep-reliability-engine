"""
Core physical, thermodynamic, and conversion constants for the BEP Reliability Engine.
All quantities are declared in strict SI units or standard geotech conventions.
"""

# Hydro-Geotechnical Properties
GRAVITY: float = 9.81  # Acceleration due to gravity [m/s²]
GAMMA_W: float = 9.81  # Submerged unit weight of water [kN/m³]
RHO_W: float = 1000.0  # Density of water [kg/m³]

# Temporal Conversion Scaling
SECONDS_PER_MINUTE: int = 60
SECONDS_PER_HOUR: int = 3600
SECONDS_PER_DAY: int = 86400

# Spatial Dimension Conversion Scaling
MM_TO_M: float = 1e-3
CM_TO_M: float = 1e-2

# Numerical/Optimization Guard Bounds
EPSILON: float = 1e-9  # Prevention of division-by-zero errors in analytical expressions
