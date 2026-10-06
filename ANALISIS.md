# Análisis reproducible — Etapa 2

## Fuente y unidades

Se analizó `pavtch/GHAW-H` en la revisión inmutable de Hugging Face
`9ccc840bd7e96fd90db3a16548d5482c2833c47d`. Los cinco archivos tienen
sus SHA-256 registrados en `data/manifest.json`; el pipeline valida estos
hashes antes de leerlos. La documentación fuente se preserva en
`data/dataset_card.md` y `data/table_dictionary.md`.

La revisión tiene 262 repositorios, 604 historias, 2.820 snapshots de
Markdown, 2.820 registros de versión y 2.820 snapshots de lock files.
Las 604 historias son también 604 pares distintos de repositorio y ruta.
Los commits observados abarcan 2025-10-03 a 2026-06-27 (UTC). Esto es
el período cubierto por las versiones observadas, no la fecha de descarga
ni una ventana completa garantizada de actividad de cada repositorio.

Las especificaciones GH-AW son archivos Markdown con frontmatter YAML
(configuración) y cuerpo (instrucciones). GHAW-H no es un corpus de
AGENTS.md ni evalúa el rendimiento de los agentes. El estudio Agent
READMEs sirve como antecedente conceptual y metodológico; sus unidades
no se deben confundir con las de GHAW-H.

## Ejecución

Requiere Python 3.12. En una instalación normal:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/download_dataset.py --revision 9ccc840bd7e96fd90db3a16548d5482c2833c47d
.venv/bin/python scripts/analyze.py
```

No se requieren credenciales de Hugging Face o GitHub. El script descarga
directamente los mismos Parquet que los enlaces `hf://` indicados por el
profesor, pero fija la revisión para que posteriores cambios de `main` no
modifiquen los resultados. En la ejecución local se usó el runtime Python
3.12.14, pandas 2.2.3, NumPy 2.3.5 y pyarrow 23.0.1. El pyarrow instalado
localmente en `.deps/` se excluye de cualquier publicación.

## Operacionalización

- Versión: registro de `source_markdown_file_version` unido 1:1 a un
  snapshot y 1:1 a un lock file. Las versiones se agrupan por historia.
- Transición consecutiva: una versión no inicial y el registro señalado
  por su enlace `predecessor`; hay 2.820 − 604 = 2.216 transiciones.
  Se verifica misma historia, rango consecutivo y enlace recíproco. Las
  fechas no se usan para reordenar versiones. No hay intervalos negativos.
- LOC: número de líneas físicas con `str.splitlines()`, incluidas líneas
  vacías, sin excluir comentarios. El frontmatter se mide según el campo
  provisto por el dataset (sin sus delimitadores); el contenido total los
  incluye. Se entregan también LOC no vacías como sensibilidad.
- Añadidas/eliminadas: diff de listas de líneas con
  `difflib.SequenceMatcher(autojunk=False)`. Sustituciones cuentan como
  eliminación más adición. Churn = añadidas + eliminadas; crecimiento
  neto = añadidas − eliminadas = LOC nueva − LOC anterior.
- Cambio efectivo: churn > 0. Una diferencia de texto crudo limitada a
  terminadores de línea no cuenta; se detectaron dos transiciones de ese
  tipo. El método no demuestra cambio semántico y no mide horas de trabajo.
  Se registran estos conteos por componente: contenido total, cuerpo y
  frontmatter. Son diferencias entre strings de Python; no comparaciones
  de bytes de los archivos originales. En el cuerpo hay 29 transiciones
  con diferencia de texto crudo y sin cambio de líneas.
- Churn relativo: churn / max(1, LOC anterior), sin truncar; puede superar
  1 si el archivo crece o se reemplaza considerablemente.
- Intervalos entre cambios del cuerpo: desde el último evento de cambio
  efectivo del cuerpo hasta el siguiente, saltando versiones que solo
  cambian YAML. Hay 656 intervalos entre eventos; baseline de rango 1 a
  primer cambio se reporta aparte (298 intervalos). No se agregan períodos
  sin eventos posteriores ni se interpreta esto como tasa sin censura.
- Contexto: `main_language` informado por GitHub para el repositorio,
  no lenguaje del Markdown. Se conserva la categoría Unknown (1 repo) y
  las etiquetas del dataset, incluida Makefile.
- Comparación por lenguaje: primero mediana por repositorio de LOC de las
  últimas versiones de sus historias, y de churn de sus transiciones con
  cambio del cuerpo; luego mediana entre repositorios de cada lenguaje.
  El denominador de churn es solo repositorios con cambio del cuerpo y
  se entrega explícitamente. No se aplican pruebas causales ni se tratan
  transiciones del mismo repositorio como observaciones independientes.

## Resultados principales

- 406/604 historias tienen más de una versión (67,22%); 405/604 cambian
  líneas del archivo completo (67,05%).
- El cuerpo cambia en 298/604 historias (49,34%), o 298/406 historias
  multiversión (73,40%), y en 151/262 repositorios (57,63%).
- 2.214/2.216 transiciones cambian líneas. De esas 2.214, 1.260 cambian
  exclusivamente frontmatter (56,91%), 384 exclusivamente cuerpo (17,34%)
  y 570 ambos componentes (25,75%).
- Hay 954 transiciones con cambio del cuerpo, 1.830 con cambio del YAML.
  La mediana de churn entre cambios efectivos del cuerpo es 11 líneas
  [Q1=4; Q3=31,75]. El mediano churn efectivo del YAML es 3 [2;9].
- Las 604 últimas versiones por historia tienen mediana de 143,5 líneas
  totales [58;235], 85,5 de cuerpo [23;173] y 35 de YAML [22;62].
- Los 656 intervalos entre cambios efectivos del cuerpo tienen mediana
  de 2,444 días [0,169;11,105]. Los 298 intervalos baseline→primer cambio
  tienen mediana de 2,130 días [0,109;12,970].
- Churn efectivo total: mediana 5 [2;21]; añadidas 3 [1;13] y eliminadas
  1 [0;5]. Se añaden en total 37.264 y eliminan 31.345 líneas. Entre
  transiciones efectivas, 1.356 crecen, 340 decrecen y 518 conservan LOC.

Todas las cifras provienen de `results/summary.json` y CSV, no de
estimaciones o ejemplos simulados. Las medianas de cantidades no se
suman entre sí; son resúmenes marginales distintos.

## Comprobaciones y amenazas observadas

Se validaron PK únicas, FK completas, correspondencia 1:1 de
snapshot/versión/lock, conteo por historia, rangos contiguos, enlaces
recíprocos, una ruta y repositorio por historia y la identidad del delta de
LOC con añadidas−eliminadas.

La muestra de adoptantes tempranos no representa todo GitHub. Los
períodos observados varían y los archivos con una versión no permiten
inferir falta de mantención. No hay medidas de calidad de salida,
autores del cambio, costo laboral, ni motivo del mantenimiento.

En las últimas versiones, 218/604 tienen un campo `imports:` y las
96/604 con cuerpo de una línea importan instrucciones. LOC local no
incluye los archivos importados y puede subestimar el tamaño de las
instrucciones ejecutadas. 497/604 contenidos finales son distintos;
hay reutilización de plantillas. Pulumi concentra 52/262 repositorios
(28 Go, 20 Makefile, 3 TypeScript y 1 Shell). Por ello las diferencias
descriptivas entre lenguajes también reflejan organizaciones, adopción,
plantillas e importaciones. Una sensibilidad que excluye Pulumi se
entrega en `results/language_sensitivity_without_pulumi.csv`.

## Archivos resultantes

`summary.json`: resultados y auditoría; `version_features.csv`: métricas
por versión; `transitions.csv`: diff consecutivo y tiempos; `history_metrics.csv`:
conteos por historia; `body_change_events.csv`: tiempos por evento del cuerpo;
`repository_metrics.csv`: agregaciones por repo; `language_summary.csv`:
contextos y denominadores; `latest_version_features.csv`: últimos estados;
`language_imports_audit.csv`: evidencia de importaciones por lenguaje;
`dataset_evidence_example.csv`: ejemplo real de claves/rutas/fechas/LOC
de Apache CloudStack, sin redistribuir su contenido.

## Licencias y publicación

La documentación del dataset declara CC BY 4.0 para metadatos del
release y aclara que cada contenido fuente conserva su licencia original.
Los Parquet crudos se descargan para análisis local, se excluyen con
`.gitignore` y no deben añadirse automáticamente a GitHub o Zenodo.
Los resultados agregados y el código permiten reproducción desde los
enlaces públicos. El DOI `10.5281/zenodo.22084012` identifica el dataset
original, no este paquete de réplica. El repositorio de este paquete es https://github.com/franciscoo30/ghaw-h-maintenance-barrozo-paredes.
La release v0.1.0 está archivada con DOI propio: https://doi.org/10.5281/zenodo.23176470.
