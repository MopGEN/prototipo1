Calculadora Graficadora y “Derivando con Borre” (8–12 años)

**Autor:** Víctor Manuel Ortiz Pérez  
**Repositorio:** `prototipo1`

**Especialización del proyecto:** calculadora **graficadora** + **minijuego de derivadas** para niñ@s de **8–12** años.  
**Objetivo:** aprender a **interpretar y estimar** derivadas (pendiente en un punto) fomentando pensamiento lógico-matemático, con **inclusión, usabilidad y accesibilidad** como ejes.

## ✨ Módulos
- **Graficadora**: traza `y=f(x)`, marca `x₀`, muestra **tangente** y estimación de `f’(x₀)`.
- **Derivando con Borre (juego)**:
  - Modo **Signo**: ¿sube / baja / plano?
  - Modo **Valor**: estima `f’(x₀)` (opciones cercanas).
  - Gamificación breve: rachas, vidas, “huesitos” y mini-jefe.
- **Calculadora básica** (apoyo; sin ampliar fuera del foco).

## 🖥️ Instalación y ejecución
```bash
git clone https://github.com/<tu-usuario>/prototipo1.git
cd prototipo1
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python src/cerebrino_hd_plus.py
