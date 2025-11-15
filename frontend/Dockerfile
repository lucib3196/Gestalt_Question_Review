# syntax=docker/dockerfile:1
# ---- Build stage ----
FROM node:20-alpine AS front-end-build
WORKDIR /app

# Declare all Firebase-related args (build-time)
ARG VITE_FIREBASE_API_KEY
ARG VITE_FIREBASE_AUTH_DOMAIN
ARG VITE_FIREBASE_PROJECT_ID
ARG VITE_FIREBASE_STORAGE_BUCKET
ARG VITE_FIREBASE_MESSAGING_SENDER_ID
ARG VITE_FIREBASE_APP_ID
ARG VITE_FIREBASE_MEASUREMENT_ID
ARG VITE_API_URL

# Export them as runtime envs (so Vite can access them)
ENV VITE_FIREBASE_API_KEY=$VITE_FIREBASE_API_KEY
ENV VITE_FIREBASE_AUTH_DOMAIN=$VITE_FIREBASE_AUTH_DOMAIN
ENV VITE_FIREBASE_PROJECT_ID=$VITE_FIREBASE_PROJECT_ID
ENV VITE_FIREBASE_STORAGE_BUCKET=$VITE_FIREBASE_STORAGE_BUCKET
ENV VITE_FIREBASE_MESSAGING_SENDER_ID=$VITE_FIREBASE_MESSAGING_SENDER_ID
ENV VITE_FIREBASE_APP_ID=$VITE_FIREBASE_APP_ID
ENV VITE_FIREBASE_MEASUREMENT_ID=$VITE_FIREBASE_MEASUREMENT_ID
ENV VITE_API_URL=$VITE_API_URL

RUN rm -rf /app/*
COPY ./package*.json ./
RUN npm install
COPY . .
RUN echo "Building frontend with API URL: ${VITE_API_URL}"
RUN npm run build
FROM nginx:alpine

# Copy build output from previous stage to Nginx’s static directory
COPY --from=front-end-build /app/dist /usr/share/nginx/html

# Expose port 80 so you can access it in the browser
EXPOSE 80

# Nginx runs automatically when container starts
CMD ["nginx", "-g", "daemon off;"]
