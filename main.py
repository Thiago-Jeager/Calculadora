from flask import Flask, render_template, request, jsonify
from scipy.integrate import quad
from flask_cors import CORS

# Crear una instancia de la aplicación Flask
app = Flask(__name__)
CORS(app)  # Habilitar CORS para manejar solicitudes desde otros dominios

# Diccionario con los coeficientes de Joback para cada grupo funcional
coeficientes_joback = {
    '-CH3': (19.5, -0.00808, 0.000153, -0.0000000967),
    '>CH2': (-0.909, 0.095, -0.0000544, 0.0000000119),
    '>CH-': (-23.0, 0.204, -0.000265, 0.00000012),
    '>C<': (-66.2, 0.427, -0.000641, 0.000000301),
    '=CH2': (23.6, -0.0381, 0.000172, -0.000000103),
    '=CH-': ( -8.00, 0.105, -0.0000963, 0.0000000356),
    '=C<': (-28.1, 0.208, -0.000306, 0.000000146 ),
    '=C=': (27.4, -0.0557, 0.000101, -0.0000000502),
    '≡CH': ( 24.5,  -0.02716, 0.000111, -0.0000000678),
    '≡C-': (7.87, 0.0201, -0.00000833, 0.00000000139 ),
    '-CH2-': (-6.03, 0.0854, -0.00000800, -0.0000000180),
    '>CH-': (-20.5, 0.162, -0.00016, 0.0000000624),
    '>C<': (-90.9, 0.557, -0.0009, 0.000000469),
    '=CH-': (-2.14, 0.0574, -0.00000164, -0.0000000159),
    '-C<': (-8.25, 0.101, -0.000142, 0.000000678),
    '-F': (26.8, -0.0913, 0.000191, -0.000000103),
    '-CL': (33.3, -0.0963, 0.000187, -0.0000000996),
    '-BR': ( 28.6, -0.0649, 0.000136, -0.0000000745),
    '-I': (32.1, -0.0641, 0.000126, -0.0000000687),
    '-OH(alcohol)': (25.7, -0.0691, 0.000177, -0.0000000988),
    '-OH(phenol)': (-2.81, 0.111, -0.000116, 0.0000000494),
    '-O-(nonring)': (25.5, -0.0632, 0.000111, -0.0000000548),
    '-O-(ring)': (12.2, -0.0296, 0.0000603, -0.0000000356),
    '>C=O(nonring)': (6.45, -0.067, 0.0000357, -0.000000311),
    '>C=O(ring)': (30.4, -0.0327, 0.000236, -0.0000000195),
    'O=CH-(aldehyde)': (30.9, -0.0336, 0.000194, -0.0000000986),
    '-COOH(acid)': (24.5, 0.0472, 0.0000402, -0.0000000452),
    '-COO-(ester)': (24.5, 0.0196, 0.0000402, -0.0000000452),
    '=O(except as above)': (6.82, 0.0196, 0.0000127, -0.0000000178),
    '-NH2': (26.9, -0.0412, 0.000164, -0.0000000976),
    '>NH(nonring)': (-1.21, 0.0762, -0.0000486, 0.0000000105),
    '>NH(ring)': (-11.8, -0.023, 0.000107, -0.0000000628),
    '>N-(nonring)': (31.1, 0.227, -0.00032, 0.000000146),
    '-N=(nonring)': (0,0,0,0),
    '-N=(ring)': (8.83, -0.00384, 0.0000435, -0.000000026),
    '=NH': (5.69, -0.00412, 0.000128, -0.0000000888),
    '-CN': (35.6, -0.0332, 0.000184, -0.000000103),
    '-NO2': (25.9, -0.00374, 0.000129, -0.0000000888),
    '-SH': (35.3, -0.0758, 0.000185, -0.000000103),
    '-S-(nonring)': (19.6, -0.00561, 0.0000402, -0.0000000276),
    '-S-(ring)': (16.7, 0.00481, 0.0000277, -0.0000000211),
}

def calcular_cp_integral(grupos_funcionales, temperatura_min, temperatura_max):

    # Inicializar acumuladores para los coeficientes ajustados
    suma_a = suma_b = suma_c = suma_d = 0
    
    # Sumar los coeficientes para cada grupo funcional
    for grupo, cantidad in grupos_funcionales.items():
        if grupo in coeficientes_joback:
            a, b, c, d = coeficientes_joback[grupo]
            suma_a += cantidad * a
            suma_b += cantidad * b
            suma_c += cantidad * c
            suma_d += cantidad * d
        else:
            return None, "Grupo funcional no encontrado"

    # Definir la función a integrar
    def integrand(temperatura):
        return (suma_a - 37.93) + (suma_b + 0.210) * temperatura + (suma_c - 0.000391) * temperatura**2 + (suma_d + 0.000000206) * temperatura**3

    # Realizar la integración numérica
    cp_integral, _ = quad(integrand, temperatura_min, temperatura_max)
    
    # Crear la fórmula para mostrar
    formula = f"CP = ({suma_a}) + ({suma_b}) * T + ({suma_c}) * T^2 + ({suma_d}) * T^3"
    
    return cp_integral, formula

@app.route('/calcular', methods=['POST'])
def calcular():
    """
    Manejar la solicitud POST para calcular el calor específico.
    """
    # Extraer datos JSON de la solicitud
    data = request.json
    grupos_funcionales = data.get('grupos_funcionales', {})
    temperatura_min = data.get('temperatura_min', 298.15)
    temperatura_max = data.get('temperatura_max', 298.15)

    # Verificar que la temperatura mínima sea menor que la máxima
    if temperatura_min >= temperatura_max:
        return jsonify({'error': 'La temperatura mínima debe ser menor que la temperatura máxima.'})

    # Calcular el calor específico y obtener la fórmula
    resultado, formula = calcular_cp_integral(grupos_funcionales, temperatura_min, temperatura_max)
    
    if resultado is None:
        return jsonify({'error': formula})  # Devuelve el mensaje de error específico

    # Devolver el resultado y la fórmula en formato JSON
    return jsonify({
        'resultado': resultado,
        'formula': formula
    })
@app.route('/')
def index():
    return render_template('')

# Ejecutar la aplicación en modo de depuración
if __name__ == '__main__':
    app.run(debug=True)
