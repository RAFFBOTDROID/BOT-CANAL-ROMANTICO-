# Usar Python 3.11 slim
FROM python:3.11-slim

# Diretório de trabalho
WORKDIR /app

# Copiar requirements
COPY requirements.txt .

# Atualizar pip e instalar pacotes
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

# Copiar todo o código
COPY . .

# Rodar o bot
CMD ["python", "bot.py"]
