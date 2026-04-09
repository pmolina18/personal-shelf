# Documento de Requisitos — CI/CD Pipeline

## Introducción

Personal Shelf (shelfd.net) se despliega en una arquitectura mixta: Vercel (frontend Vue 3 SPA), Render (backend FastAPI) y Neon.dev (PostgreSQL). Actualmente, Render y Vercel redespliegan automáticamente al detectar un push a `main` vía webhook de GitHub, pero:

- No se ejecutan tests antes de desplegar — un push con código roto llega directamente a producción.
- Las migraciones de Alembic contra Neon.dev se ejecutan manualmente desde la máquina del desarrollador.
- No hay visibilidad del estado del pipeline (verde/rojo) en el repositorio.

Esta feature implementa un pipeline de CI/CD con GitHub Actions que ejecuta tests, aplica migraciones y garantiza que solo código validado llega a producción.

## Glosario

- **Pipeline_CI**: Workflow de GitHub Actions que se ejecuta en cada push a `main` y en cada pull request.
- **Job_Backend_Tests**: Job del pipeline que ejecuta los tests de backend (pytest) contra una base de datos SQLite en memoria.
- **Job_Frontend_Tests**: Job del pipeline que ejecuta los tests de frontend (vitest) en un entorno Node.js.
- **Job_Migrate**: Job del pipeline que ejecuta `alembic upgrade head` contra la base de datos de producción en Neon.dev.
- **GitHub_Secret**: Variable cifrada almacenada en GitHub → Settings → Secrets, accesible solo durante la ejecución del workflow.
- **Branch_Main**: Rama principal del repositorio desde la cual se despliega a producción.

## Requisitos

### Requisito 1: Ejecución automática de tests de backend

**User Story:** Como desarrollador, quiero que los tests de backend se ejecuten automáticamente en cada push, para detectar regresiones antes de que lleguen a producción.

#### Criterios de Aceptación

1. WHEN se hace push a Branch_Main o se abre un pull request contra Branch_Main, THEN el Pipeline_CI SHALL ejecutar Job_Backend_Tests.
2. THE Job_Backend_Tests SHALL instalar las dependencias de `backend/requirements.txt` en un entorno Python 3.11.
3. THE Job_Backend_Tests SHALL ejecutar `python -m pytest tests/ -x -q --ignore=tests/test_property_multitenancy.py --ignore=tests/test_property_media.py --ignore=tests/test_property_stats_export.py --ignore=tests/test_property_mcp.py` para los tests rápidos (unitarios + integración).
4. THE Job_Backend_Tests SHALL ejecutar los tests de propiedad (Hypothesis) con `HYPOTHESIS_MAX_EXAMPLES=10` para mantener el tiempo de ejecución razonable en CI.
5. IF algún test falla, THEN el Pipeline_CI SHALL marcar el job como fallido y no proceder con Job_Migrate.

### Requisito 2: Ejecución automática de tests de frontend

**User Story:** Como desarrollador, quiero que los tests de frontend se ejecuten automáticamente en cada push, para detectar regresiones en la interfaz.

#### Criterios de Aceptación

1. WHEN se hace push a Branch_Main o se abre un pull request contra Branch_Main, THEN el Pipeline_CI SHALL ejecutar Job_Frontend_Tests.
2. THE Job_Frontend_Tests SHALL instalar las dependencias de `frontend/package.json` en un entorno Node.js 20.
3. THE Job_Frontend_Tests SHALL ejecutar `npx vitest run` desde el directorio `frontend/`.
4. IF algún test falla, THEN el Pipeline_CI SHALL marcar el job como fallido.
5. THE Job_Backend_Tests y Job_Frontend_Tests SHALL ejecutarse en paralelo para minimizar el tiempo total del pipeline.

### Requisito 3: Ejecución automática de migraciones de base de datos

**User Story:** Como desarrollador, quiero que las migraciones de Alembic se apliquen automáticamente a Neon.dev tras un push exitoso a main, para no tener que ejecutarlas manualmente.

#### Criterios de Aceptación

1. THE Job_Migrate SHALL ejecutarse únicamente cuando el push es a Branch_Main (no en pull requests).
2. THE Job_Migrate SHALL ejecutarse solo si Job_Backend_Tests ha completado exitosamente.
3. THE Job_Migrate SHALL leer la variable `DATABASE_URL` desde GitHub_Secret para conectarse a Neon.dev.
4. THE Job_Migrate SHALL ejecutar `python -m alembic upgrade head` desde el directorio `backend/`.
5. IF la migración falla, THEN el Pipeline_CI SHALL marcar el job como fallido y notificar en el resumen del workflow.
6. THE Job_Migrate SHALL instalar las dependencias de `backend/requirements.txt` antes de ejecutar Alembic.

### Requisito 4: Gestión segura de secretos

**User Story:** Como desarrollador, quiero que las credenciales de producción estén protegidas, para que no se expongan en logs ni en el código fuente.

#### Criterios de Aceptación

1. THE Pipeline_CI SHALL leer `DATABASE_URL` exclusivamente desde GitHub_Secret, nunca desde el código fuente ni desde variables hardcodeadas en el workflow.
2. THE Pipeline_CI SHALL NO imprimir el valor de `DATABASE_URL` ni ningún otro secreto en los logs del workflow.
3. THE Pipeline_CI SHALL documentar en el workflow (como comentario) qué secretos deben configurarse en GitHub.

### Requisito 5: Visibilidad del estado del pipeline

**User Story:** Como desarrollador, quiero ver el estado del pipeline en GitHub, para saber de un vistazo si el último push está verde.

#### Criterios de Aceptación

1. THE Pipeline_CI SHALL generar un badge de estado que pueda incluirse en el README del repositorio.
2. WHEN todos los jobs completan exitosamente, THEN GitHub SHALL mostrar un check verde en el commit y en el pull request.
3. WHEN algún job falla, THEN GitHub SHALL mostrar un check rojo en el commit y en el pull request.

### Requisito 6: Compatibilidad con el flujo de desarrollo local

**User Story:** Como desarrollador, quiero que el pipeline de CI no interfiera con mi flujo de desarrollo local, para seguir trabajando como hasta ahora.

#### Criterios de Aceptación

1. THE Pipeline_CI SHALL NO modificar ningún archivo del proyecto que afecte al desarrollo local.
2. THE Pipeline_CI SHALL usar las mismas versiones de Python y Node.js que el entorno de desarrollo local (Python 3.11, Node.js 20).
3. THE Pipeline_CI SHALL NO requerir cambios en los scripts de test existentes (`pytest`, `vitest run`).
