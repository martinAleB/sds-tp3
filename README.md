# TP3 - Simulación de Sistemas

El presente trabajo implementa una dinámica molecular dirigida por eventos (EDMD) para estudiar la difusión y la efusión de un gas de discos duros en un recinto doble con un cuello de apertura variable. El objetivo es caracterizar cómo evoluciona la distribución de partículas entre recintos, estimar el coeficiente de difusión a partir del MSD y cuantificar la presión ejercida sobre las paredes en función del área efectiva del canal.

Las funcionalidades incluidas son las siguientes:

- <b>Motor EDMD</b>: Simula choques elásticos partícula–partícula y partícula–pared dentro de dos recintos cuadrados conectados por un canal de ancho configurable `L`, incorporando obstáculos fijos en el cuello.
- <b>Geometría Parametrizable</b>: Permite variar la apertura del canal y capturar el impacto sobre efusión, caudal y equilibrio de presiones entre recintos.
- <b>Persistencia de Corridas</b>: Guarda cada simulación bajo `data/simulations/<nombre>/` con archivos `static.txt` y `dynamic.txt`, incluyendo el historial de partículas que impactan bordes.
- <b>Análisis Estadístico</b>: Scripts en Python para reconstruir tiempos de choque, estimar presiones medias por recinto, obtener regresiones `P` vs `A^{-1}` y calcular el coeficiente de difusión vía MSD.
- <b>Visualización</b>: Animaciones en tiempo real de las trayectorias y velocidades que reproducen la dinámica en el recinto y canal.
- <b>Informe Técnico</b>: Carpeta `report/` con la presentación del trabajo práctico y figuras claves generadas a partir de las simulaciones.

<details>
  <summary>Contenidos</summary>
  <ol>
    <li><a href="#instalación">Instalación</a></li>
    <li><a href="#instrucciones">Instrucciones</a></li>
    <li><a href="#manual-de-usuario">Manual de Usuario</a></li>
    <li><a href="#integrantes">Integrantes</a></li>
  </ol>
</details>

## Instalación

Clonar el repositorio:

- HTTPS:
  ```sh
  git clone https://github.com/martinAleB/sds-tp3.git
  ```
- SSH:
  ```sh
  git clone git@github.com:martinAleB/sds-tp3.git
  ```

Motor de simulación (Java + Maven):

```sh
cd simulations
mvn clean package
```

Scripts de post-procesamiento (Python >= 3.10):

```sh
python3 -m venv .venv
source .venv/bin/activate          # Linux / macOS
# .venv\Scripts\activate           # Windows PowerShell
pip install numpy matplotlib
```

> **Requisitos**: JDK 21 (o compatible con Maven), Python 3.10+ con `pip`.

<p align="right">(<a href="#tp3---simulación-de-sistemas">Volver</a>)</p>

## Instrucciones

Todos los comandos deben ejecutarse desde la raíz del repositorio (o la carpeta indicada) con el entorno correspondiente activado.

- Compilación rápida del motor:
  ```sh
  ./compile-sims-engine.sh
  ```
- Ejecución de simulaciones:
  ```sh
  cd simulations
  java -jar target/simulations-1.0-SNAPSHOT.jar <nombre> <N> <L> <T>
  ```
  Los resultados quedan en `data/simulations/<nombre>/`.
- Post-procesamiento:
  ```sh
  python post-processing/pressure_analysis.py data/simulations/L003
  python post-processing/diffusion-coefficient.py data/simulations/L003 --t0 51 --tmin 1 --tmax 20
  ```
- Animaciones:
  ```sh
  python post-processing/animate_sim_realtime.py data/simulations/L003 --out anim.mp4 --fps 60
  ```

<p align="right">(<a href="#tp3---simulación-de-sistemas">Volver</a>)</p>

## Manual de Usuario

### Motor de Dinámica Molecular (Java)

```sh
cd simulations
java -jar target/simulations-1.0-SNAPSHOT.jar L005 300 0.05 60000
```

Parámetros:

- `simulation_name`: carpeta de salida en `data/simulations/<name>/`.
- `N`: cantidad de partículas móviles (todas de radio `R = 1.5 mm` por defecto).
- `L`: ancho del canal central (en metros) que conecta los recintos.
- `T`: cantidad de eventos registrados (pasos del algoritmo EDMD).

Archivos generados:

- `static.txt`: valores de `N`, `L`, radio `R`, masa `M`, velocidad inicial `V` y `T`.
- `dynamic.txt`: para cada evento, una línea encabezado con el tiempo acumulado y los IDs de partículas que impactaron el borde, seguida por `N` líneas con `(x, y, vx, vy)` de cada partícula móvil.

Las dos partículas fijas que definen el cuello se agregan automáticamente (no aparecen en `dynamic.txt`). El archivo dinámico es apto para reconstruir choques con paredes y estimar flujos entre recintos.

<p align="right">(<a href="#tp3---simulación-de-sistemas">Volver</a>)</p>

### Animación de Simulaciones

```sh
python post-processing/animate_sim_realtime.py data/simulations/L003 --out animation_rt.mp4 --fps 60 --speed 1.0
```

- Reproduce en “tiempo real” la simulación interpolando posiciones entre eventos EDMD.
- El vector campo muestra velocidades instantáneas y los discos se colorean con opacidad para resaltar densidad local.
- `--speed` permite acelerar o desacelerar la reproducción.

<p align="right">(<a href="#tp3---simulación-de-sistemas">Volver</a>)</p>

### Análisis de Presiones

```sh
python post-processing/pressure_analysis.py data/simulations/L003
```

- Reconstruye los choques contra paredes a partir de los IDs listados en `dynamic.txt`.
- Binea los impulsos transferidos y calcula `P_left` y `P_right` como fuerza promedio por longitud de pared.
- Exporta `pressures.csv` con columnas `t`, `P_left`, `P_right` y grafica ambas curvas resaltando la transición de régimen.

Para comparar distintas aperturas:

```sh
python post-processing/pressure_area.py \
  data/simulations/L003 data/simulations/L005 data/simulations/L007 data/simulations/L009
```

- Calcula el área efectiva `A` del recinto + canal (restando el radio de las paredes) y grafica la presión promedio en régimen vs `A^{-1}`.

```sh
python post-processing/pressure_regression.py \
  data/simulations/L003 data/simulations/L005 data/simulations/L007 data/simulations/L009 \
  --tmin 60 --ngrid 400
```

- Ajuste lineal `P = c · A^{-1}` por mínimos cuadrados desde origen.
- Entrega curva de error `E(c)`, valor óptimo `c*`, desviación estándar y coeficiente de determinación `R²`.

<p align="right">(<a href="#tp3---simulación-de-sistemas">Volver</a>)</p>

### Coeficiente de Difusión

```sh
python post-processing/diffusion-coefficient.py data/simulations/L003 --t0 51 --tmin 1 --tmax 20 --dim 2
```

- Reconstruye la trayectoria completa y computa el Mean Squared Displacement usando un frame de referencia `t0`.
- Ajusta la recta `MSD(t) = a · t` sobre la ventana `[tmin, tmax]` y reporta `D = a / (2 · dim)`.
- Grafica la curva de error del ajuste y el MSD con su recta óptima.

<p align="right">(<a href="#tp3---simulación-de-sistemas">Volver</a>)</p>

## Integrantes

Martín Alejandro Barnatán (64463) - mbarnatan@itba.edu.ar  
Ignacio Martín Maruottolo Quiroga (64611) - imaruottoloquiroga@itba.edu.ar  
Ignacio Pedemonte Berthoud (64908) - ipedemonteberthoud@itba.edu.ar

<p align="right">(<a href="#tp3---simulación-de-sistemas">Volver</a>)</p>
