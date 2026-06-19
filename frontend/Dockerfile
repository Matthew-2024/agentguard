FROM node:20-alpine AS build

WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
ENV VITE_AGENTGUARD_API_URL=/api
RUN npm run build

FROM nginx:1.27-alpine

ENV AGENTGUARD_API_KEY=agentguard-local-dev
COPY frontend/nginx.conf /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
