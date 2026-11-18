# Stage 1: Build React/Vite app
FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# Vite environment variables at build time
ARG VITE_FORKLIFT_ID=1
ARG VITE_WAREHOUSE_ID=1
ENV VITE_FORKLIFT_ID=$VITE_FORKLIFT_ID
ENV VITE_WAREHOUSE_ID=$VITE_WAREHOUSE_ID

RUN npm run build

# Stage 2: Serve with Nginx and reverse-proxy API requests
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
