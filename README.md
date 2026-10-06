# Mantenimiento de archivos Markdown en GitHub Agentic Workflows

Paquete de réplica de la Etapa 2 de **Francisco Barrozo y Antonia Paredes**, Universidad de La Frontera.

Estudio observacional longitudinal del mantenimiento textual de workflows Markdown de GH-AW. Se distinguen el cuerpo de instrucciones, la configuración YAML y el archivo completo; se comparan resúmenes por repositorio según su lenguaje principal.

## Replicar el análisis

Requisitos: Python 3.12, conexión para descargar inicialmente los cinco Parquet y aproximadamente 100 MB para los datos. Desde la raíz del repositorio:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/download_dataset.py --revision 9ccc840bd7e96fd90db3a16548d5482c2833c47d
python scripts/analyze.py
```

El dataset es [`pavtch/GHAW-H`](https://huggingface.co/datasets/pavtch/GHAW-H), fijado en la revisión indicada. `data/manifest.json` preserva las URLs, tamaños y SHA-256 de los cinco archivos. Los scripts verifican hashes, claves, relaciones entre tablas, secuencias y enlaces de versiones. No se necesitan credenciales para descargar el dataset público.

Para regenerar las imágenes PNG a 600 dpi:

```bash
python -m pip install -r requirements-plots.txt
python scripts/plot_results.py --output-dir paper/figuras
```

Los boxplots utilizan cuartiles de pandas con interpolación lineal y bigotes de Tukey a 1,5 IQR. Los círculos vacíos conservan los atípicos y sus repeticiones; el desplazamiento perpendicular al eje de valores es determinista y no altera las líneas. La figura de cambios incluye detalle de 0–80 líneas y rango completo. Las cajas con IQR cero se muestran como líneas.

## Contenido

- `scripts/`: descarga, análisis y figuras reproducibles.
- `data/`: manifiesto y documentación atribuida del dataset; los Parquet crudos se descargan localmente y están excluidos de Git.
- `results/`: métricas por versión, transición, historia y repositorio; resúmenes, sensibilidad sin Pulumi y evidencia de importaciones.
- `ANALISIS.md`: definiciones, procedimiento, controles y limitaciones.
- `paper/`: LaTeX, PDF y dos figuras del manuscrito vigente. El PDF aportado fue compilado con pdfTeX y tiene cuatro páginas de contenido y una de referencias.
- `CITATION.cff` y `.zenodo.json`: autores y metadatos de citación y archivo.

Para importar el documento en Overleaf, cargue el `.tex` y la carpeta `paper/figuras/` conservando la ruta `figuras/` junto al fuente, y seleccione pdfLaTeX. Solo las correcciones respecto de la Etapa 1 están en azul; las incorporaciones están en negro.

## Resultados principales

La revisión analizada contiene 262 repositorios, 604 historias, 2.820 versiones y 2.216 transiciones. Se observaron 954 transiciones con cambios efectivos del cuerpo, en 298 historias y 151 repositorios. La mediana de churn efectivo del cuerpo es 11 líneas; los 656 intervalos entre cambios sucesivos tienen mediana de 2,444 días. Las cifras completas y los controles están en `results/summary.json`.

La incorporación inicial no se considera mantenimiento. Un cambio efectivo modifica listas de líneas físicas de `splitlines()`. Los repositorios sin cambios del cuerpo no se agregan como churn cero a la distribución de cambios efectivos; sus denominadores se informan por separado.

Los resultados son descriptivos. No estiman esfuerzo humano, calidad de ejecución ni efectos causales del lenguaje. La selección de adoptantes tempranos, ventanas temporales desiguales, dependencia organizacional, plantillas e importaciones limitan las comparaciones.

## Licencias y atribución

El código tiene licencia [MIT](LICENSE). El manuscrito, las figuras y los resultados propios tienen licencia [CC BY 4.0](LICENSE-DOCUMENTS.md). La documentación de GHAW-H y los contenidos originales conservan sus licencias y atribuciones; el paquete no los relicencia ni redistribuye los Parquet crudos.

Dataset original: P. Valenzuela-Toledo, T. Kehrer y S. Panichella, *GHAW-H: A Dataset of GitHub Agentic Workflow Histories*, v0.1.2, [DOI 10.5281/zenodo.22084012](https://doi.org/10.5281/zenodo.22084012). Ese DOI identifica el dataset original, no este paquete.

## Citar y archivar este paquete

Repositorio: [https://github.com/franciscoo30/ghaw-h-maintenance-barrozo-paredes](https://github.com/franciscoo30/ghaw-h-maintenance-barrozo-paredes).

Utilice los autores y la versión de `CITATION.cff`. La primera release prevista es `v0.1.0`; su DOI propio se incorporará cuando Zenodo termine de archivarla. Los enlaces del paquete en el manuscrito se completarán al obtener el DOI propio; el PDF incluido corresponde al manuscrito previo a la publicación del paquete.
