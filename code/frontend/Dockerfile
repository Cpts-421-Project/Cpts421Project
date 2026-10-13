# ---- Build Stage ----
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .

# Vite inlines env vars at build time; Railway passes service variables as build args
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# ---- Production Stage ----
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf.template /etc/nginx/nginx.conf.template

# Remove the default server block so ours is the only one
RUN rm /etc/nginx/conf.d/default.conf

EXPOSE 3000

# Substitute $PORT, $BACKEND_HOST, and $BACKEND_PORT in the template
CMD ["/bin/sh", "-c", "export PORT=${PORT:-3000} BACKEND_HOST=${BACKEND_HOST:-backend.railway.internal} BACKEND_PORT=${BACKEND_PORT:-8000} && envsubst '$PORT $BACKEND_HOST $BACKEND_PORT' < /etc/nginx/nginx.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]
