# TC2008B Modelación de Sistemas Multiagentes con gráficas computacionales
# Python server to interact with Unity via POST
# Sergio Ruiz-Loza, Ph.D. March 2021
#Actualizado por Axel Dounce, PhD

from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import json
import threading
import agentpy as ap
from matplotlib import pyplot as plt
import IPython
import random
from owlready2 import *

class Server(BaseHTTPRequestHandler):
    
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html') #Preguntar si en lugar de este tipo de formato no debe de ser formato json para dar respuestas al ciente(Unity)
        self.end_headers()
        
    def do_GET(self):
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        response_data = get_response()
        self._set_response()
        #self.wfile.write("GET request for {}".format(self.path).encode('utf-8'))
        self.wfile.write(str(response_data).encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        #post_data = self.rfile.read(content_length)
        post_data = json.loads(self.rfile.read(content_length))
        #logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                     #str(self.path), str(self.headers), post_data.decode('utf-8'))
        logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                     str(self.path), str(self.headers), json.dumps(post_data))
      
      
        # Aquí se procesa lo el cliente ha enviado, y se construye una respuesta.
        response_data = post_response(post_data)
        
        
        self._set_response()
        #self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))
        self.wfile.write(str(response_data).encode('utf-8'))


    def run(server_class=HTTPServer, handler_class=Server, port=8585):
        logging.basicConfig(level=logging.INFO)
        server_address = ('', port)
        httpd = server_class(server_address, handler_class)
        logging.info("Starting httpd...\n") # HTTPD is HTTP Daemon!
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:   # CTRL+C stops the server
            pass
        httpd.server_close()
        logging.info("Stopping httpd...\n")
    
    #==========================================Procesamiento de datos de cliente=========================
    
def post_response(data):
    
        #Tuple: (norte, sur, izquierda, derecha)
        #Tuple: (0,0,1,0)
        #havebox: 1/0
        #Id: 1-5
        #0-no hay nada
        #1-colision con un robot, pared
        #CON UNA CAJA TENIENDO OTRA CAJA
        #CON UN PUNTO DE RECOLECCION Y NO TRAIGO UNA CAJA
        #UN PUNTO DE RECOLECCION LLENO.
        #2.-
        #COLISION CON UNA CAJA Y NO TRAIGO OTRA CAJA.
        #ACCIONES DE SALIDA: 
        #1.- AVANZAR HACIA LA DIRECCION DE LA CAJA.
        #2.- SETEAR VARIABLE DE HAVEBOX COMO 1.
        #3.-
        #COLISION CON UN PUNTO DE RECOLECCION, TRAIGO UNA CAJA Y HAY ESPACIO.
        #ACCIONES DE SALIDA:
        #MOVIMIENTO EN CUALQUIER DIRECCION A EXCEPCION DE LA DIRECCION EN LA QUE FUE LA COLISION.
        #SETEAR LA VARIABLE HAVEBOX COMO 0.
        
    
    model.environment = data
    model.post_flag = 1
    
    #NOTA: PREGUNTAR SI EL PASAR EL JSON AL STEP DEL MODEL SE PUEDE HACER DE ESTA FORMA Y POR SU PARTE SI ES LO CORRECTO PARA HACER.
    return model.step(data)


"""
Función para procesar los datos que vienen del cliente (mediante POST) en forma de JSON.
Se construye un JSON para la respuesta al cliente.
Se retorna la respuesta.

Ejemplo:

    x = data['x'] * 2
    y = data['y'] * 2
    z = data['z'] * 2
    
    new_position = {
        "x" : x+1,
        "y" : y-1,
        "z" : z
    }
    
    return new_position
"""

#return None
  
#def get_response():
#    """
#    Función construir un JSON para la respuesta al cliente (GET).
#    Se retorna la respuesta.
#        
#    Ejemplo:
#        
#        act = wealth_transfer
#            
#            
#        return act
#    """
#    return None





#==============================================================================
#===================Definición de Agentes y simulación (Model)=================
#==============================================================================
#   ONTOLOGY SECTION:
#==============================================================================
onto = get_ontology("file://onto.owl")
with onto:
#==============================================================================
#==============================================================================
#   AGENT DESIGN SECTION:
#==============================================================================
    class RobotAgent(ap.Agent):
       
        #NOTA: EN ESTE CASO LAS ACCIONES NO SON LAS QUE DETERMINARAN QUE REGLA SE USARA, SI NO, QUE LAS REGLAS SE EVALUARAN CON LOS 
        #CAMBIOS EN EL AMBIENTE Y PRODUCIRAN ACCIONES QUE SERAN DEVUELTAS COMO UN JSON AL CLIENTE EN ESTE CASO UNITY. JUNTO CON LOS ATRIBUTOS DE ID Y HAVEBOX.
        #DUDAS: EN DONDE Y COMO PROCESAR EL JSON RECIBIDO. Y POR SU PARTE, COMO MANEJAR ACCIONES PARA DEVOLVERLAS COMO PARTE DEL JSON DE RESPUESTA JUNTO CON LAS VARIABLES ID Y HAVEBOX.
        #SE ESTA PENSANDO MANEJAR LA MISMA TUPLA RECIBIDA, COMO TUPLA DE RESPUESTA. SIENDO 1 QUE A ESA DIRECCION DEBE IR EL ROBOT Y 0 QUE A ESA DIRECCON NO DEBE DE IR. TUPLA: (NORTE, SUR, IZQUIERDA, DERECHA).
        #HAVEBOX DE IGUAL FORMA MANEJARA O Y 1. 1 COMO QUE TIENE UNA CAJA Y 0 COMO QUE NO.
        #ID MANEJARA NUMEROS DEL 1 AL 5. ID'S DISTINTOS PARA CADA ROBOT.
        
        _id_counter = 0
        
        def setup(self):
            """
            Inicialization function.
            """
            #Initial colission tuple. This tuple describes the colisions that each robot has with the things that are in his surroundings(The 4 adyacent squares).
            self.colisiontuple = (0,0,0,0) 
            #Status variable. This variable act as a flag for indicate if the robot has a box with him or not. 
            self.havebox = 0 
            #Identificator variable.
            RobotAgent._id_counter += 1
            self.id = RobotAgent._id_counter
            
            # Acciones del agente
            self.actions = (
                self.move_N,
                self.move_S,
                self.move_E,
                self.move_W,
                self.move_random
            )
            # Reglas del agente
            self.rules = (
                self.rule_1,
                self.rule_2,
                self.rule_3
            )
        
        def see(self,e):
            """
            Función de percepción
            @param e: entorno grid
            """
            data = e
            self.colisiontuple = data["Tuple"]
            self.havebox = data["boxes"]
            #POSIBLE FUNCION PARA RECIBIR EL JSON DE CAMBIO DE AMBIENTE Y POSTERIORMENTE MANIPULARLO PARA PRODUCIR RESPUESTA AL POST MANDADO POR EL CLIENTE.
            pass
        
        def next(self):
            """
            Función de razonamiento Deductivo
            """
            
            
        pass
    
        def step(self):
            """
            Función paso a paso
            """
            self.see(self.model.environment)
            self.next() #Razonamiento y acción
        pass

        def update(self):
            pass

        def end(self):
            pass
        
        def rule_1(self):
            #COLISION CON:
            #UNA PARED
            #OTRO ROBOT
            #CON UNA CAJA TENIENDO OTRA CAJA
            #CON UN PUNTO DE RECOLECCION Y NO TRAIGO UNA CAJA
            #UN PUNTO DE RECOLECCION LLENO.
            #ACCIONES DE SALIDA:
            #MOVIMIENTO EN CUALQUIER DIRECCION A EXCEPCION DE LA DIRECCION EN LA QUE FUE LA COLISION.
            #PREGUNTAR COMO SE PUEDE HACER PARA MULTIPLES COLISIONES EN EL MISMO POST.
            pass
        
        def rule_2(self):
            #COLISION CON UNA CAJA Y NO TRAIGO OTRA CAJA.
            #ACCIONES DE SALIDA: 
            #1.- AVANZAR HACIA LA DIRECCION DE LA CAJA.
            #2.- SETEAR VARIABLE DE HAVEBOX COMO 1.
            
            pass
        
        def rule_3(self):
            #COLISION CON UN PUNTO DE RECOLECCION, TRAIGO UNA CAJA Y HAY ESPACIO.
            #ACCIONES DE SALIDA:
            #MOVIMIENTO EN CUALQUIER DIRECCION A EXCEPCION DE LA DIRECCION EN LA QUE FUE LA COLISION.
            #SETEAR LA VARIABLE HAVEBOX COMO 0.
            pass
        
        

#==============================================================================
#==============================================================================
#   AGENT MODEL SECTION:
#==============================================================================
    class RobotModel(ap.Model):

        def setup(self):
            """
            Función de inicialización
            """
            self.environment = {}
            self.post_flag = 0
            
            self.robots = ap.AgentList(self, self.p.robots, RobotAgent)

            pass

        def step(self, data):
            """
            Función paso a paso
            """
            
            #Recibir aqui el json y guardarlo en una variable, para manipularlo en las funciones que manda a llamar step por step el modelo. 
            if self.post_flag == 1:
                self.robots.step() 
                self.post_flag = 0
            
            pass

        def update(self):
            pass

        def end(self):
            pass

#==============================================================================
#==============================================================================
#   PARAMETERS SECTION:
#==============================================================================
parameters = {
    'robots': 5,
}

# 


#==============================================================================
#==================================Main========================================
#==============================================================================
#==============================================================================

if _name_ == '_main_':
    from sys import argv
    
    #Iniciar hilo del servidor    
    p = threading.Thread(target=run, args = tuple(),daemon=True)
    p.start()
    
    #Correr simulación (de preferencia no especifiquen los steps)
    model = RobotModel(parameters)
    results = model.run()