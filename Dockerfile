# Stage 1: Build Tailwind (optional if you want a multi-stage build)
FROM node:18 AS tailwind
WORKDIR /app
COPY package.json tailwind.config.js ./
RUN npm install
COPY static/css/styles.css ./
RUN npx tailwindcss -i ./styles.css -o ../static/css/app.css

# Stage 2: Python app
FROM python:3.10-slim
WORKDIR /app
# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy app code and built CSS
COPY . .
# Expose port
EXPOSE 8080
CMD ["uvicorn", "word_search:app", "--host", "0.0.0.0", "--port", "8080"]
