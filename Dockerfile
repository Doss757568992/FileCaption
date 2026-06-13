FROM python:3.11-slim

WORKDIR /workspace

# Dependencies-ai install seiya
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bot files-ai copy seiya
COPY . .

# Expose port for flask
EXPOSE 8080

# Run the bot
CMD ["python", "bot.py"]
