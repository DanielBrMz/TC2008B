import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import requests
import json
import tkinter as tk
from tkinter import ttk

class Grid:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.grid = np.zeros((rows, cols))
        self.camera_positions = []
        self.object_pos = None
        self.vision_radius = 85
        self.object_size = 3  # Tamaño del objeto (3x3)

        self.setup_grid()

    def setup_grid(self):
        # Define las columnas (obstáculos)
        columnas = [
            (10, 0, 90, 10),   # Columna 1 (desde arriba)
            (30, 10, 100, 10), # Columna 2 (desde abajo)
            (60, 10, 100, 10), # Columna 3 (desde abajo)
            (80, 0, 90, 10),   # Columna 4 (desde arriba)
        ]

        # Agregar las columnas al grid
        for col, start, end, width in columnas:
            self.grid[start:end, col:col+width] = 1

        # Agregar cámaras
        camara_size = 2
        for i, (col, start, end, width) in enumerate(columnas):
            if start == 0:  # Columna que comienza desde arriba
                camara_row = end - camara_size - 4  # Cámara en la parte inferior de la columna
            else:  # Columna que comienza desde abajo
                camara_row = start + 4  # Cámara en la parte superior de la columna
            
            if i < 2:  # Para las dos primeras columnas (izquierda)
                camara_col = col - camara_size  # Colocar la cámara a la izquierda de la columna
            else:  # Para las dos últimas columnas (derecha)
                camara_col = col + width  # Colocar la cámara a la derecha de la columna
            
            self.grid[camara_row:camara_row+camara_size, camara_col:camara_col+camara_size] = 3
            self.camera_positions.append((camara_row, camara_col))

        # Marcar el pasillo del medio como no válido para objetos
        self.grid[:, 49:51] = 4

    def is_valid_position(self, row, col):
        # Verificar si todas las celdas necesarias para el objeto están disponibles
        for i in range(self.object_size):
            for j in range(self.object_size):
                if row + i >= self.rows or col + j >= self.cols:
                    return False
                if self.grid[row + i, col + j] != 0:
                    return False
        return True

    def place_object(self, row, col, object_type):
        if self.is_valid_position(row, col):
            if self.object_pos:
                self.remove_object()
            self.object_pos = (row, col)
            for i in range(self.object_size):
                for j in range(self.object_size):
                    self.grid[row + i, col + j] = object_type

    def remove_object(self):
        if self.object_pos:
            row, col = self.object_pos
            for i in range(self.object_size):
                for j in range(self.object_size):
                    self.grid[row + i, col + j] = 0
            self.object_pos = None

    def detect_object(self):
        detections = []
        if self.object_pos is None:
            return [(0, None) for _ in self.camera_positions]

        object_row, object_col = self.object_pos
        for camera_pos in self.camera_positions:
            camera_row, camera_col = camera_pos
            if self.is_visible(camera_row, camera_col, object_row, object_col):
                relative_pos = (object_row - camera_row, object_col - camera_col)
                detections.append((1, relative_pos))
            else:
                detections.append((0, None))

        return detections

    def is_visible(self, camera_row, camera_col, object_row, object_col):
        distance = np.sqrt((camera_row - object_row)**2 + (camera_col - object_col)**2)
        if distance > self.vision_radius:
            return False

        # Comprobación de línea de visión
        x0, y0 = camera_row, camera_col
        x1, y1 = object_row, object_col
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        x, y = x0, y0
        n = 1 + dx + dy
        x_inc = 1 if x1 > x0 else -1
        y_inc = 1 if y1 > y0 else -1
        error = dx - dy
        dx *= 2
        dy *= 2

        for _ in range(n):
            if self.grid[int(x), int(y)] == 1:  # Solo consideramos las columnas como obstáculos
                return False
            if error > 0:
                x += x_inc
                error -= dy
            else:
                y += y_inc
                error += dx

        return True

    def get_vision_mask(self):
        mask = np.zeros((self.rows, self.cols))
        for camera_pos in self.camera_positions:
            for i in range(self.rows):
                for j in range(self.cols):
                    if self.is_visible(camera_pos[0], camera_pos[1], i, j):
                        mask[i, j] = 1
        return mask

class Application(tk.Tk):
    def __init__(self, grid):
        super().__init__()

        self.grid = grid
        self.title("Grid Visualization")
        self.geometry("1000x800")

        self.figure, self.ax = plt.subplots(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(expand=True, fill=tk.BOTH)

        self.status_frame = ttk.Frame(self)
        self.status_frame.pack(pady=10)

        self.status_labels = []
        for i in range(4):  # Asumiendo que hay 4 cámaras
            label = ttk.Label(self.status_frame, text=f"Camera {i}: Running", font=("Arial", 12))
            label.pack(pady=2)
            self.status_labels.append(label)

        self.setup_plot()
        self.update_visualization()

    def setup_plot(self):
        # Crear un nuevo colormap personalizado
        cmap = plt.cm.colors.ListedColormap(['white', 'gray', 'green', 'red', 'yellow'])
        bounds = [0, 0.5, 1.5, 2.5, 3.5, 4.5]
        norm = plt.cm.colors.BoundaryNorm(bounds, cmap.N)

        self.im = self.ax.imshow(self.grid.grid, cmap=cmap, norm=norm)
        self.ax.set_title('Unity en Python', fontsize=16)
        self.colorbar = self.figure.colorbar(self.im, boundaries=bounds, ticks=[0, 1, 2, 3, 4])
        self.colorbar.set_ticklabels(['Empty', 'Wall', 'Fugitive', 'Camera', 'Central'])

        # Create text objects for each cell
        self.cell_texts = [[self.ax.text(j, i, '', ha='center', va='center', fontweight='bold', fontsize=6) 
                            for j in range(self.grid.cols)] 
                           for i in range(self.grid.rows)]

        # Create vision mask
        self.vision_mask = self.ax.imshow(self.grid.get_vision_mask(), alpha=0.3, cmap='gray')

    def update_visualization(self):
        # Update the grid data
        self.im.set_data(self.grid.grid)
        
        # Update the vision mask
        self.vision_mask.set_data(self.grid.get_vision_mask())
        
        # Update cell texts
        for i in range(self.grid.rows):
            for j in range(self.grid.cols):
                cell_type = self.grid.grid[i, j]
                if cell_type == 1:
                    self.cell_texts[i][j].set_text('W')
                    self.cell_texts[i][j].set_color('black')
                elif cell_type == 2:
                    self.cell_texts[i][j].set_text('F')
                    self.cell_texts[i][j].set_color('white')
                elif cell_type == 3:
                    self.cell_texts[i][j].set_text('C')
                    self.cell_texts[i][j].set_color('white')
                elif cell_type == 4:
                    self.cell_texts[i][j].set_text('')
                    self.cell_texts[i][j].set_color('black')
                else:
                    self.cell_texts[i][j].set_text('')

        self.canvas.draw()

        detections = self.grid.detect_object()
        
        data = {
            "Camera": [
                {
                    "id": i,
                    "position": list(pos),
                    "Detect": detection[0],
                    "DetectPosition": list(detection[1]) if detection[1] else None
                } for i, (pos, detection) in enumerate(zip(self.grid.camera_positions, detections))
            ]
        }
        
        print(f"Sending data to server: {json.dumps(data, indent=2)}")
        
        try:
            response = requests.post('http://localhost:5000/detect', json=data, timeout=0.1)
            actions = response.json()['Camera']
            for i, cam in enumerate(actions):
                status_text = f"Camera {cam['id']}: {cam['action']}"
                self.status_labels[i].config(text=status_text)
                if cam['action'] == "alarm":
                    self.status_labels[i].config(foreground="red")
                else:
                    self.status_labels[i].config(foreground="black")
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to server: {e}")
            for label in self.status_labels:
                label.config(text="Status: Server connection error", foreground="orange")

            # Lógica para colocar o remover objeto
        if self.grid.object_pos is None:
            # Intentar colocar un nuevo objeto
            object_type = 2  # Fugitivo
            attempts = 0
            while attempts < 100:  # Limitar intentos para evitar bucle infinito
                object_row = np.random.randint(0, self.grid.rows - self.grid.object_size + 1)
                object_col = np.random.randint(0, self.grid.cols - self.grid.object_size + 1)
                if object_col < 40 or object_col >= 60:  # Evitar columnas 40-60
                    if self.grid.is_valid_position(object_row, object_col):
                        self.grid.place_object(object_row, object_col, object_type)
                        break
                attempts += 1
        else:
            # Posibilidad de remover el objeto existente
            if np.random.random() < 0.1:  # 10% de probabilidad de remover
                self.grid.remove_object()

        self.after(200, self.update_visualization)  # Actualizar cada 0.2 segundos

def main():
    grid = Grid(100, 100)
    app = Application(grid)
    app.mainloop()

if __name__ == "__main__":
    main()