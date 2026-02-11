FROM python:3.11-slim

# Diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema necessárias
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    libffi-dev \
    libssl-dev \
    python3-dev \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Atualizar pip e instalar pacotes
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

# Copiar todo o código
COPY . .

# Comando para rodar o bot
CMD ["python", "bot.py"]
