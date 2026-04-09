# Guía de Despliegue — shelfd.net

Arquitectura: Vercel (frontend) + Render (backend) + Neon.dev (PostgreSQL) + Cloudflare (DNS)

---

## 1. Base de datos — Neon.dev

1. Crear cuenta en [neon.tech](https://neon.tech) (free tier permanente, 0.5 GB)
2. Crear un nuevo proyecto (nombre: `shelfd` o similar)
3. Copiar la connection string. Tendrá este formato:
   ```
   postgresql://user:password@ep-xxx-yyy.region.neon.tech/neondb?sslmode=require
   ```
4. Convertirla al formato asyncpg que usa el backend (cambiar `postgresql://` por `postgresql+asyncpg://`):
   ```
   postgresql+asyncpg://user:password@ep-xxx-yyy.region.neon.tech/neondb?ssl=require
   ```
5. Ejecutar las migraciones contra Neon.dev desde tu máquina local:
   ```bash
   cd personal-shelf/backend
   DATABASE_URL="postgresql+asyncpg://user:password@ep-xxx-yyy.region.neon.tech/neondb?ssl=require" \
     python -m alembic upgrade head
   ```
   Esto crea todas las tablas (media_items, users, tags, friendships, etc.)

---

## 2. Backend — Render

1. Crear cuenta en [render.com](https://render.com)
2. Nuevo → Web Service → conectar tu repo de GitHub (`personal-shelf`)
3. Configuración del servicio:
   - Name: `shelfd-api`
   - Runtime: Python
   - Build Command: `pip install -r backend/requirements.txt`
   - Start Command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - Health Check Path: `/api/health`

4. Variables de entorno en Render (Environment → Add Environment Variable):

   | Variable | Valor |
   |---|---|
   | `DATABASE_URL` | `postgresql+asyncpg://user:password@ep-xxx.neon.tech/neondb?ssl=require` |
   | `ALLOWED_ORIGINS` | `https://shelfd.net,https://www.shelfd.net` |
   | `JWT_SECRET_KEY` | (generar un string aleatorio largo, ej: `openssl rand -hex 32`) |
   | `TMDB_API_KEY` | (tu API key de themoviedb.org, opcional) |

5. Deploy. Render arrancará el backend y verificará el health check en `/api/health`
6. Anotar la URL del servicio (ej: `https://shelfd-api.onrender.com`)

> Nota: el free tier de Render duerme el servicio tras 15 min de inactividad. La primera petición tras dormir tarda ~30s (cold start).

---

## 3. Frontend — Vercel

1. Crear cuenta en [vercel.com](https://vercel.com)
2. Importar proyecto → seleccionar tu repo de GitHub
3. Configuración:
   - Framework Preset: Vite
   - Root Directory: `frontend`
   - Build Command: `npm run build` (ya está en vercel.json)
   - Output Directory: `dist` (ya está en vercel.json)

4. Variables de entorno en Vercel (Settings → Environment Variables):

   | Variable | Valor |
   |---|---|
   | `VITE_API_BASE_URL` | `https://shelfd-api.onrender.com/api` |
   | `VITE_IMAGES_BASE_URL` | `https://shelfd-api.onrender.com` |

   > Importante: estas variables se inyectan en build time, no en runtime. Cada vez que las cambies, necesitas re-deployar.

5. Deploy. Vercel generará una URL temporal (ej: `shelfd-frontend.vercel.app`)

---

## 4. DNS — Cloudflare

Ya tienes `shelfd.net` en Cloudflare. Ahora hay que apuntar el dominio a Vercel.

### 4.1 Conectar shelfd.net a Vercel

1. En Vercel → tu proyecto → Settings → Domains → Add Domain → `shelfd.net`
2. Vercel te pedirá que añadas registros DNS. Ve a Cloudflare:

   | Tipo | Nombre | Contenido | Proxy |
   |---|---|---|---|
   | CNAME | `@` | `cname.vercel-dns.com` | DNS only (nube gris) |
   | CNAME | `www` | `cname.vercel-dns.com` | DNS only (nube gris) |

   > Importante: desactiva el proxy de Cloudflare (nube gris, no naranja) para que Vercel pueda emitir el certificado SSL. Una vez verificado, puedes activar el proxy si quieres.

3. En Vercel, verifica el dominio. Puede tardar unos minutos en propagar.
4. Vercel emitirá automáticamente un certificado SSL para `shelfd.net` y `www.shelfd.net`.

### 4.2 (Opcional) Subdominio para el backend

Si prefieres `api.shelfd.net` en vez de `shelfd-api.onrender.com`:

1. En Render → tu servicio → Settings → Custom Domains → Add `api.shelfd.net`
2. En Cloudflare, añadir:

   | Tipo | Nombre | Contenido | Proxy |
   |---|---|---|---|
   | CNAME | `api` | `shelfd-api.onrender.com` | DNS only (nube gris) |

3. Si usas `api.shelfd.net`, actualiza las variables de Vercel:
   - `VITE_API_BASE_URL` → `https://api.shelfd.net/api`
   - `VITE_IMAGES_BASE_URL` → `https://api.shelfd.net`
4. Y en Render, actualiza `ALLOWED_ORIGINS` si es necesario.

---

## 5. Verificación post-despliegue

Ejecuta estas comprobaciones en orden:

```bash
# 1. Health check del backend
curl https://shelfd-api.onrender.com/api/health
# Esperado: {"status":"ok"}

# 2. CORS — verificar que el frontend puede hablar con el backend
curl -I -X OPTIONS https://shelfd-api.onrender.com/api/auth/login \
  -H "Origin: https://shelfd.net" \
  -H "Access-Control-Request-Method: POST"
# Esperado: access-control-allow-origin: https://shelfd.net

# 3. Frontend carga
curl -s https://shelfd.net | head -5
# Esperado: HTML con el <div id="app">

# 4. Registro de usuario (prueba end-to-end)
# Abre https://shelfd.net en el navegador y registra un usuario
```

---

## 6. Checklist rápido

- [ ] Neon.dev: proyecto creado, connection string copiada
- [ ] Migraciones ejecutadas contra Neon.dev (`alembic upgrade head`)
- [ ] Render: servicio creado con las 4 env vars
- [ ] Render: health check responde 200
- [ ] Vercel: proyecto importado con root `frontend`
- [ ] Vercel: 2 env vars configuradas (VITE_API_BASE_URL, VITE_IMAGES_BASE_URL)
- [ ] Cloudflare: CNAME `@` y `www` apuntando a `cname.vercel-dns.com`
- [ ] shelfd.net carga el frontend
- [ ] Registro/login funciona end-to-end
- [ ] (Opcional) CNAME `api` para subdominio custom del backend

---

## Notas importantes

- Las imágenes en Render son efímeras (se pierden en cada redeploy). Si tienes `TMDB_API_KEY` configurada, se re-descargan bajo demanda cuando un usuario accede a un item.
- El free tier de Render duerme tras 15 min. Considera un servicio de ping (UptimeRobot, cron-job.org) para mantenerlo despierto.
- Neon.dev free tier: 0.5 GB, sin expiración. Suficiente para uso personal.
- Vercel free tier: sin cold starts, CDN global, ideal para SPAs.
