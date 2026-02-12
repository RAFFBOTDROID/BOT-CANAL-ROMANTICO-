# Usar imagem Python 3.11 completa
FROM python:3.11

# Diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema mínimas
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Atualizar pip e instalar pacotes só com binários pré-compilados
RUN pip install --upgrade pip setuptools wheel
RUN pip install --only-binary=:all: -r requirements.txt

# Copiar todo o código do bot
COPY . .

# Comando para rodar o bot
CMD ["python", "bot.py"]
