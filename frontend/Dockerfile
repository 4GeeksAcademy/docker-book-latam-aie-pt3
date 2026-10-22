# Dependencias comunes: npm ci usa el lockfile para una instalación reproducible.
FROM node:20-alpine AS dependencies
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# Build de producción: compila TypeScript y crea los archivos estáticos.
FROM dependencies AS build
COPY . .
RUN npm run build

# Desarrollo: Vite con hot reload. Se declara antes de production para que
# production sea el target predeterminado al construir esta imagen.
FROM dependencies AS development
COPY . .
EXPOSE 3001
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3001"]

# Producción: Nginx sirve el bundle y reenvía las rutas API al backend.
FROM nginx:alpine AS production
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
