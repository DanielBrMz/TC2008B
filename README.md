# Equipo TC2008B

> [!WARNING]
> 2/9/2024
> Los avancecs de Unity para la entrega intermedia pueden observarse en la escena `BaseModels` en la carpeta `Assets\Scenes`

### Integrantes
1. Yair Salvador Beltran Rios A01254673
2. Daniel Alfredo Barreras Meraz A01254805
3. Angela Estefania Aguilar Medina A01637703
4. Gael Venegas Gomez A01642913
5. Julian Enrique Espinoza Valenzuela A01254679

## Actividad Integradora 1

En esta actividad se desarrolló una simulación basada en agentes que consiste en robots dentro de un almacén que deben de recoger cajas en su ambiente y llevarlas a sus estaciones de carga siguiendo algunas condiciones como si la estación está llena y cuál es la estación más cercana.

## Actividad Integradora Entrega Intermedia
En esta entrega se realizó un avance significativo hacia la evidencia final. El progreso se centró en el desarrollo de una simulación orientada a la vigilancia de un entorno específico. En esta simulación se incluyeron agentes como cámaras, drones y personal de seguridad, cuyo objetivo es interactuar entre sí para mantener vigilado el entorno en cuestión. Para esta entrega, se integraron en la rama principal del repositorio los avances correspondientes a Unity, así como las mejoras relacionadas con el servidor desarrollado en Python y AgentPy. Finalmente, se añadió la documentación requerida para el entregable intermedio.

## Instalacion (WIP)
- Dirigite a la seccion de [releases](#)
- Descarga el archivo .zip de la version mas reciente
- Descomprime el archivo y corre el ejecutable

## Keybinds
- `V` - Visualizar/Ocultar los sensores de los agentes
- `T` - Visualizar tiles 

## Build
- Clona el repositorio en tu dispositivo
```bash
git clone https://github.com/DanielBrMz/TC2008B.git
```

### Servidor
Se requiere correr el servidor de Python para que la simulación funcione

> [!TIP]
> Se recomienda crear un ambiente virtual para instalar las dependencias correctamente y para asegurarse de que el programa corra sin conflictos

- Navega a ```Evidencia1/Server```

- Instala las dependencias del proyecto
> [!WARNING]
> Solo incluimos las dependencias indispensables, puede que necesite instalar otros paquetes que suponemos ya deberian estar instalados en su ambiente
```bash
pip install -r requirements.txt
````

- Corre el server y copia la URL (en la ruta `/gmes`) al componente de Unity `EnviromentManager`

```bash
python Evidencia1/Server/Server.py
```
> [!NOTE]
> Si estas corriendo el server en la misma computadora que el proyecto de Unity, la url por defecto sera la correcta

### Unity
- Abre Unity Hub, da click en agregar y selecciona la carpeta **Unity**

- En caso de no tener instalada la version correcta de Unity, se debe de instalar la version **2020.3.42f1**

- Una vez que se haya cargado el proyecto, se debe de abrir la escena llamada **Warehouse**

> [!WARNING]
> El proyecto fallara instantaneamente si no encuentra respuesta del servidor de python
