# Stage 1: Build
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

# Default backend URL — override with -e BACKEND_URL=http://your-backend:8000
ENV BACKEND_URL=http://host.docker.internal:8000

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
