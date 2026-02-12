# Usar imagem Python 3.11 completa (não slim) para evitar problemas de build com Groq
FROM python:3.11

# Diretório de trabalho
WORKDIR /app

# Atualizar pip e instalar dependências do sistema necessárias
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Atualizar pip e instalar pacotes Python
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

# Copiar todo o código do bot
COPY . .

# Comando para rodar o bot
CMD ["python", "bot.py"]
