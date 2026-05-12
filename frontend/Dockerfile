FROM node:20-alpine
WORKDIR /app
# 1. Najpierw kopiujemy tylko pliki konfiguracyjne paczek
COPY package*.json ./
# 2. Instalujemy zależności WEWNĄTRZ obrazu
RUN npm install
# 3. Odpalamy serwer (reszta plików będzie zmapowana przez docker-compose)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]