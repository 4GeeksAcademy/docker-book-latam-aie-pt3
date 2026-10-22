# Plan detallado para dockerizar la aplicación de biblioteca

> **Estado:** implementado; se construyeron las imágenes de desarrollo y producción y se inició el stack de producción. La validación del proxy entre contenedores queda pendiente por un timeout de red en el entorno actual.  
> **Decisiones confirmadas:** incluir desarrollo y producción, usar Docker Compose, conservar SQLite con persistencia, parametrizar la ruta de la base de datos con `DATABASE_URL` y enrutar la API mediante Vite en desarrollo y Nginx en producción.

## 1. Objetivo y arquitectura propuesta

La aplicación está formada por:

- **Backend:** FastAPI + SQLModel + SQLite, ubicado en `backend/`. El proceso ASGI se ejecutará con Uvicorn en el puerto `8001`.
- **Frontend:** React + Vite + TypeScript, ubicado en `frontend/`. En desarrollo correrá Vite en el puerto `3001`; en producción se compilará y Nginx servirá los archivos estáticos.
- **Persistencia:** un volumen Docker nombrado se montará en `/data`, y SQLite guardará allí `/data/books.db`.
- **Red interna:** Compose conectará los servicios. Dentro de los contenedores se usa el nombre de servicio `backend`, no `localhost`, para llamar al backend.

Flujo de peticiones:

```text
Desarrollo: navegador :3001 -> Vite -> backend:8001 -> SQLite en volumen
Producción: navegador :8080 -> Nginx -> backend:8001 -> SQLite en volumen
```

La API actual usa las rutas `/books` y `/books/{book_id}`. El backend inicializa las tablas y corre el seed al arrancar; el seed actual inserta libros solamente si la base está vacía.

## 2. Archivos que se propone añadir o modificar

```text
raíz/
├── compose.yaml                    # Compose de producción (configuración por defecto)
├── compose.dev.yaml                # Ajustes para desarrollo con hot reload
├── .env.example                    # Plantilla de variables, sin secretos reales
├── backend/
│   ├── Dockerfile                  # Imagen/backend: etapas de desarrollo y producción
│   ├── .dockerignore               # Excluye archivos innecesarios y .env
│   └── database.py                 # Modificar para tomar DATABASE_URL del entorno
└── frontend/
    ├── Dockerfile                  # Etapas Vite desarrollo, build y Nginx producción
    ├── .dockerignore               # Excluye dependencias/build local y .env
    └── nginx.conf                  # Archivos estáticos + proxy de rutas API
```

> No se propone usar `server.py`: es un servidor Flask de la plantilla anterior, no el frontend React actual. Tampoco se necesita Dockerfile para la raíz si Compose construye cada servicio desde su propia carpeta.

## 3. Preparación del backend

### 3.1 Hacer configurable la ubicación de SQLite

Modificar `backend/database.py` para que `DATABASE_URL` provenga del entorno y tenga un valor local por defecto compatible con la ejecución actual. La imagen Docker establecerá, por ejemplo, `DATABASE_URL=sqlite:////data/books.db`.

- **Qué resuelve:** hoy la URL se fija junto a `database.py` (`backend/books.db`); en un contenedor esa ruta pertenece al sistema de archivos efímero de la imagen.
- **Resultado esperado:** ejecuciones locales pueden seguir usando `backend/books.db`; Compose coloca la base persistente en `/data/books.db`.
- **Cuidado:** preservar la configuración SQLite `check_same_thread=False` y comprobar que el directorio destino exista. En el diseño propuesto `/data` se crea/monta antes de arrancar.

### 3.2 `backend/Dockerfile`

El Dockerfile del backend tendrá como contexto la carpeta `backend/` y contendrá dos etapas identificables:

```dockerfile
# Etapa base: usa una imagen oficial pequeña de Python 3; evita escribir .pyc
# y mantiene stdout/stderr sin buffer para que los logs aparezcan en Docker.
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

# Instala primero requisitos para aprovechar la caché si solo cambia el código.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código de la API, modelos, acceso a datos y seed.
COPY . .

# Etapa de desarrollo: inicia Uvicorn con recarga al modificar archivos montados.
FROM base AS development
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]

# Etapa de producción: no activa autoreload.
FROM base AS production
EXPOSE 8001
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
```

Comentarios de diseño:

- `requirements.txt` ya declara FastAPI, Uvicorn y SQLModel; no hace falta instalar Flask para este backend.
- `EXPOSE` documenta el puerto del contenedor; Compose define si se publica al host.
- La variable `DATABASE_URL` se inyecta desde Compose, no se codifica en el Dockerfile.
- Como mejora de seguridad posterior, se puede ejecutar como usuario no-root. Antes debe verificarse que pueda escribir en el volumen SQLite.

### 3.3 `backend/.dockerignore`

Crear el archivo en el contexto del backend, incluyendo como mínimo:

```dockerignore
# No enviar configuración local ni variables de entorno al contexto de build.
.env
.env.*
!.env.example

# No copiar el entorno virtual ni cachés del equipo anfitrión.
.venv/
__pycache__/
*.py[cod]

# No incorporar la base local a la imagen; la base se monta desde un volumen.
books.db
*.db

# Excluir metadatos Git.
.git/
```

Aunque `.env` se excluye del contexto de imagen, Compose puede leer el `.env` de la raíz para interpolar variables. No se debe incluir un archivo `.env` con secretos en una imagen.

## 4. Preparación del frontend

### 4.1 Proxy Vite para desarrollo

Modificar `frontend/vite.config.ts` para que la URL del proxy no quede fija a `http://localhost:8001`. Se recomienda usar una variable de entorno de Vite, con `http://localhost:8001` como valor predeterminado local y `http://backend:8001` en el contenedor de desarrollo.

- **Por qué:** en el contenedor frontend, `localhost` es el propio frontend, no el servicio backend.
- **Importante:** las variables que Vite incorpora al cliente deben llevar el prefijo `VITE_`; esta URL es configuración de red, no un secreto.
- Vite debe seguir escuchando en `0.0.0.0:3001` para ser accesible fuera del contenedor.

### 4.2 `frontend/Dockerfile`

El Dockerfile del frontend tendrá etapas de desarrollo y producción. La etapa de producción construye el bundle con Node y lo copia a una imagen Nginx:

```dockerfile
# Etapa común Node: instalar las dependencias usando el lockfile reproducible.
FROM node:20-alpine AS dependencies
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# Etapa de compilación: genera frontend/dist con TypeScript y Vite.
FROM dependencies AS build
COPY . .
RUN npm run build

# Etapa de desarrollo: conserva Vite y dependencias para hot reload.
# Va antes de production para que el target de producción sea el último.
FROM dependencies AS development
COPY . .
EXPOSE 3001
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3001"]

# Etapa de producción: Nginx publica el contenido estático y aplica el proxy API.
FROM nginx:alpine AS production
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
```

Comentarios de diseño:

- `npm ci` requiere y respeta `package-lock.json`, que ya existe en el repositorio.
- No se copia `node_modules/` del anfitrión; se instala dentro de la imagen.
- `dist/` se genera al construir la imagen y no se necesita enviar el `dist/` local.
- La etapa final contiene Nginx y los archivos compilados, no necesita ejecutar Node/Vite.

### 4.3 `frontend/nginx.conf`

Crear una configuración Nginx que:

1. Sirva los archivos compilados desde `/usr/share/nginx/html`.
2. Use fallback de SPA (`try_files ... /index.html`) para rutas propias de React.
3. Envíe las rutas de API al servicio `backend:8001` por la red de Compose.
4. Permita que las rutas de documentación OpenAPI también lleguen al backend.

Esquema orientativo:

```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # Sin URI en proxy_pass se conserva el path, por ejemplo /books/1.
    location /books {
        proxy_pass http://backend:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Rutas de documentación y esquema OpenAPI de FastAPI.
    location /docs {
        proxy_pass http://backend:8001;
        proxy_set_header Host $host;
    }
    location /openapi.json {
        proxy_pass http://backend:8001;
        proxy_set_header Host $host;
    }

    # Fallback para navegación del frontend React.
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

Antes de implementar, validar que la sintaxis y el comportamiento de `proxy_pass` preserven las rutas `/books` y `/books/{id}`. La raíz `/` se reservaría para el frontend; la API sigue accesible a través de `/books` y `/docs`.

### 4.4 `frontend/.dockerignore`

Crear el archivo en el contexto del frontend, incluyendo:

```dockerignore
# No enviar archivos de entorno al build de Docker.
.env
.env.*
!.env.example

# Las dependencias se instalan en la imagen mediante npm ci.
node_modules/

# El build Docker genera su propio directorio dist.
dist/

# Excluir metadatos y configuración local del editor.
.git/
.vscode/
```

## 5. Compose de producción: `compose.yaml`

La configuración por defecto debe levantar el frontend compilado y el backend:

```yaml
services:
  backend:
    # Construir usando backend/Dockerfile y su etapa sin autoreload.
    build:
      context: ./backend
      target: production
    environment:
      # Guardar SQLite fuera del filesystem efímero del contenedor.
      DATABASE_URL: ${DATABASE_URL:-sqlite:////data/books.db}
    volumes:
      # Volumen nombrado: sobrevive a recreación/actualización del contenedor.
      - books_data:/data
    expose:
      # Solo visible para otros servicios de Compose, no publicado al host.
      - "8001"
    restart: unless-stopped

  frontend:
    # Compilar React y servirlo con Nginx.
    build:
      context: ./frontend
      target: production
    ports:
      # Acceso desde el navegador en http://localhost:8080.
      - "8080:80"
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  # Docker administra este almacenamiento persistente.
  books_data:
```

Puntos a revisar:

- `depends_on` ordena el inicio, pero por sí solo no garantiza que el backend ya esté listo para recibir tráfico. Se puede añadir healthcheck si el arranque coordinado lo requiere.
- En producción, el backend queda sin puerto publicado en el host; Nginx es el punto de entrada. Si se requiere consultar directamente `http://localhost:8001/docs`, se puede agregar un mapeo de puerto de forma explícita.
- El contenedor backend debe poder escribir en `/data` para crear SQLite.

## 6. Compose de desarrollo: `compose.dev.yaml`

Este archivo será **independiente** del de producción. Así no se heredan por accidente los puertos de Nginx ni la configuración productiva; se monta el código local para hot reload:

```yaml
services:
  backend:
    build:
      context: ./backend
      target: development
    ports:
      # API/documentación directa para facilitar pruebas locales.
      - "8001:8001"
    volumes:
      # Refleja cambios de Python dentro del contenedor.
      - ./backend:/app
      # Conserva SQLite independientemente del bind mount del código.
      - books_data:/data

  frontend:
    build:
      context: ./frontend
      target: development
    environment:
      # Nombre DNS del servicio Compose, no localhost.
      VITE_API_PROXY_TARGET: http://backend:8001
    ports:
      - "3001:3001"
    volumes:
      # Refleja cambios de React/TypeScript en tiempo real.
      - ./frontend:/app
      # Evita que node_modules del anfitrión reemplace el de la imagen.
      - /app/node_modules
    depends_on:
      - backend

volumes:
  # Comparte persistencia con las ejecuciones de producción del mismo proyecto Compose.
  books_data:
```

Desarrollo se ejecuta solo con `-f compose.dev.yaml`; producción se ejecuta solo con `compose.yaml`. Si se usa el mismo nombre de proyecto Compose, ambos archivos refieren al mismo volumen `books_data`.

## 7. Variables de entorno y `.env`

Crear `.env.example` como plantilla documentativa, sin credenciales:

```dotenv
# Puerto HTTP de la interfaz publicada por Compose (si se parametriza).
FRONTEND_PORT=8080

# Ruta SQLite dentro del contenedor backend.
DATABASE_URL=sqlite:////data/books.db
```

Si se decide usar `.env`, copiar la plantilla y mantener el archivo real fuera del control de versiones:

```bash
# Crear configuración local a partir de la plantilla; revisar antes de usar.
cp .env.example .env
```

- El `.env` se utiliza para configuración/interpolación de Compose, no para copiarse dentro de las imágenes.
- Confirmar que `.env` está ignorado por Git. Los `.dockerignore` de **ambos contextos** deben incluir `.env` y `.env.*`.
- No almacenar secretos en variables `VITE_*`: el código del frontend se entrega al navegador.

## 8. Secuencia de implementación y comandos principales

Los siguientes comandos son parte del plan; **no se han ejecutado**.

### Paso 1 — verificar herramientas

```bash
# Comprobar que Docker responde y que Compose v2 está instalado.
docker --version
docker compose version
```

### Paso 2 — construir y arrancar en desarrollo

```bash
# Construir las etapas development y arrancar backend + Vite en primer plano.
docker compose -f compose.dev.yaml up --build
```

```bash
# Variante en segundo plano; útil para recuperar el prompt de la terminal.
docker compose -f compose.dev.yaml up --build -d
```

URLs de prueba en desarrollo:

- Frontend: `http://localhost:3001`
- Backend: `http://localhost:8001`
- Documentación API: `http://localhost:8001/docs`

### Paso 3 — validar endpoints y logs

```bash
# Consultar libros a través del proxy de Vite.
curl http://localhost:3001/books

# Consultar directamente el backend y OpenAPI.
curl http://localhost:8001/books
curl -I http://localhost:8001/docs

# Ver estado y logs de todos los servicios.
docker compose -f compose.dev.yaml ps
docker compose -f compose.dev.yaml logs -f
```

### Paso 4 — construir y arrancar producción

```bash
# Construye etapas production y publica Nginx en el puerto 8080.
docker compose up --build -d
```

URLs de prueba en producción:

- Aplicación: `http://localhost:8080`
- API proxificada: `http://localhost:8080/books`
- Documentación proxificada: `http://localhost:8080/docs`

```bash
# Comprobar respuesta API y servicios activos en producción.
curl http://localhost:8080/books
docker compose ps
docker compose logs -f backend frontend
```

### Paso 5 — detener, limpiar o reconstruir

```bash
# Detener y retirar contenedores/red, conservando el volumen de datos.
docker compose down

# Detener el stack de desarrollo, conservando el volumen de datos.
docker compose -f compose.dev.yaml down

# Reconstruir imágenes si cambiaron dependencias o Dockerfiles.
docker compose build --no-cache
```

> **Peligro:** `docker compose down -v` elimina también el volumen `books_data` y, por tanto, la base SQLite persistente. Solo usarlo si se desea borrar los datos deliberadamente.

## 9. Criterios de aceptación

- `docker compose -f compose.dev.yaml up --build` levanta los servicios de desarrollo.
- Vite sirve React en el puerto `3001`, y `/books` se enruta al backend usando `backend:8001`.
- `docker compose up --build -d` sirve el frontend desde Nginx en `8080` y enruta `/books` al backend.
- La API responde con una lista JSON en `/books`; `/docs` muestra Swagger UI del backend.
- El backend crea la base y realiza el seed solo si la base está vacía.
- Los datos permanecen después de `docker compose down` y volver a iniciar, siempre que no se use `-v`.
- Ni `.env` ni `.env.*`, `node_modules`, `.venv`, `dist` local, cachés o la SQLite local forman parte de los contextos de build.

## 10. Orden recomendado de trabajo

1. Cambiar `database.py` para admitir `DATABASE_URL` y conservar un default de desarrollo local.
2. Actualizar `vite.config.ts` para permitir el destino de proxy configurable.
3. Crear `backend/Dockerfile` y `backend/.dockerignore`.
4. Crear `frontend/Dockerfile`, `frontend/.dockerignore` y `frontend/nginx.conf`.
5. Crear `compose.yaml`, `compose.dev.yaml` y `.env.example`; confirmar que `.env` está en `.gitignore`.
6. Seguir los comandos de desarrollo y comprobar API, proxy y persistencia.
7. Construir y validar el modo de producción.
8. Documentar cualquier decisión adicional, como healthchecks o publicación directa del puerto backend.

## 11. Resultado de la ejecución inicial

- Compose de desarrollo y producción pasan la validación de configuración.
- Las imágenes de desarrollo y producción construyen correctamente; también pasa `npm run build` en `frontend/`.
- El stack de producción se inició. Nginx responde en `http://localhost:8080/` y el backend arranca, crea SQLite en el volumen y carga los 10 libros de ejemplo.
- En esta sesión el backend responde dentro de su propio contenedor, pero desde el contenedor frontend la conexión a `backend:8001` expira y las rutas `/books` y `/docs` devuelven `504`. Se comprobó que ambos servicios comparten la red Compose; esto apunta a una limitación/regla de red del entorno Docker actual, no a una respuesta HTTP de FastAPI. No dar por validado el proxy hasta repetir la prueba en un entorno donde haya conectividad entre contenedores.
- Para repetir las pruebas cuando la red esté disponible:

```bash
# Confirmar resolución del nombre del servicio desde el frontend.
docker compose exec frontend getent hosts backend

# Probar conexión al backend directamente desde Nginx.
docker compose exec frontend wget -qO- http://backend:8001/books

# Probar la API a través del proxy Nginx.
curl -i http://localhost:8080/books
```
