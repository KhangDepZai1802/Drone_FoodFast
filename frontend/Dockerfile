# ✅ DEVELOPMENT MODE - Hot reload enabled
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy all source code
COPY . .

# Expose port
EXPOSE 3000

# ✅ FIX: Run Vite dev server (NOT serve)
CMD ["npm", "run", "dev", "--", "--host"]