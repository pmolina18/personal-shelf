# Plan de Implementación: CI/CD Pipeline

## Visión General

Crear un pipeline de GitHub Actions que ejecute tests de backend y frontend en paralelo, aplique migraciones de Alembic contra Neon.dev en pushes a main, y proporcione visibilidad del estado del pipeline en el repositorio.

## Tareas

- [ ] 1. Crear el workflow de GitHub Actions
  - [ ] 1.1 Crear `.github/workflows/ci.yml` con la estructura base
    - Definir `name: CI`
    - Definir trigger: `on: push: branches: [main]` y `on: pull_request: branches: [main]`
    - Definir los tres jobs: `backend-tests`, `frontend-tests`, `migrate`
    - _Requisitos: 1.1, 2.1, 3.1_

  - [ ] 1.2 Implementar job `backend-tests`
    - Runner: `ubuntu-latest`
    - Setup Python 3.11 con `actions/setup-python@v5`
    - Cache de pip para acelerar instalaciones
    - Instalar dependencias: `pip install -r backend/requirements.txt`
    - Ejecutar tests rápidos: `python -m pytest tests/ -x -q --ignore=tests/test_property_multitenancy.py --ignore=tests/test_property_media.py --ignore=tests/test_property_stats_export.py --ignore=tests/test_property_mcp.py`
    - Ejecutar property tests con `HYPOTHESIS_MAX_EXAMPLES=10`
    - _Requisitos: 1.2, 1.3, 1.4, 1.5_

  - [ ] 1.3 Implementar job `frontend-tests`
    - Runner: `ubuntu-latest`
    - Setup Node.js 20 con `actions/setup-node@v4`
    - Cache de node_modules para acelerar instalaciones
    - `npm ci` en directorio `frontend/`
    - `npx vitest run` en directorio `frontend/`
    - _Requisitos: 2.2, 2.3, 2.4, 2.5_

  - [ ] 1.4 Implementar job `migrate`
    - Runner: `ubuntu-latest`
    - Condición: `if: github.event_name == 'push' && github.ref == 'refs/heads/main'`
    - Dependencia: `needs: [backend-tests]`
    - Setup Python 3.11
    - Instalar dependencias de backend
    - Ejecutar `python -m alembic upgrade head` en directorio `backend/`
    - Variable de entorno `DATABASE_URL` desde `secrets.DATABASE_URL`
    - Añadir comentario en el workflow documentando qué secrets se necesitan
    - _Requisitos: 3.2, 3.3, 3.4, 3.5, 3.6, 4.1, 4.2, 4.3_

- [ ] 2. Documentación y visibilidad
  - [ ] 2.1 Añadir badge de CI al WIKI.md
    - Insertar badge de GitHub Actions al inicio del WIKI.md
    - Formato: `![CI](https://github.com/USUARIO/personal-shelf/actions/workflows/ci.yml/badge.svg)`
    - Pedir al usuario su nombre de usuario de GitHub para construir la URL correcta
    - _Requisitos: 5.1, 5.2, 5.3_

  - [ ] 2.2 Actualizar DEPLOY.md con instrucciones de CI/CD
    - Añadir sección sobre configuración del secret `DATABASE_URL` en GitHub
    - Añadir nota sobre branch protection recomendada
    - _Requisitos: 4.3_

- [ ] 3. Checkpoint — Verificar pipeline
  - Hacer push del workflow a main y verificar que los tres jobs se ejecutan correctamente
  - Verificar que el badge muestra el estado correcto
  - Preguntar al usuario si ha configurado el secret `DATABASE_URL` en GitHub
  - _Requisitos: 5.2, 5.3, 6.1, 6.2, 6.3_

## Notas

- Este spec no incluye tests de propiedad (Hypothesis) porque es configuración de infraestructura, no lógica de negocio
- El pipeline no orquesta los deploys de Render/Vercel — estos son automáticos vía webhook de GitHub
- Los 44 tests de frontend que fallan actualmente (pre-existentes, relacionados con auth) seguirán fallando en CI. Hay que decidir si se arreglan antes o se marcan como skip temporalmente
- El secret `DATABASE_URL` debe configurarse manualmente en GitHub → Settings → Secrets → Actions → New repository secret
