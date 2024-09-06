import matplotlib.pyplot as plt
import numpy as np

# Crear la matriz inicial de 100x100 con valores en 0 (representando pasillos vacíos)
grid = np.zeros((100, 100))

# Definir las columnas
columnas = [
    (10, 0, 90, 10),   # Columna 1 (desde arriba)
    (30, 10, 100, 10), # Columna 2 (desde abajo)
    (60, 10, 100, 10), # Columna 3 (desde abajo)
    (80, 0, 90, 10),   # Columna 4 (desde arriba)
]

# Agregar las columnas al grid
for col, start, end, width in columnas:
    grid[start:end, col:col+width] = 1

# Agregar "cámaras" (cuadrados) al final de cada columna
camara_size = 2
for col, start, end, width in columnas:
    if start == 0:  # Columna que comienza desde arriba
        camara_row = end - camara_size - 4  # Cámara en la parte inferior de la columna
    else:  # Columna que comienza desde abajo
        camara_row = start + 4  # Cámara en la parte superior de la columna
    
    camara_col = col + width  # Colocar la cámara a la derecha de la columna
    grid[camara_row:camara_row+camara_size, camara_col:camara_col+camara_size] = 1

# Visualizar el grid usando imshow
plt.figure(figsize=(10, 10))
plt.imshow(grid, cmap='Greys', origin='upper')
plt.title("Psh Carcel con Cámaras")
plt.show()
