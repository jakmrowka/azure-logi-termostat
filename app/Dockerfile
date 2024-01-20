# Użyj oficjalnego obrazu Pythona jako obrazu bazowego
FROM python:3.9-slim

# Ustaw katalog roboczy w kontenerze
WORKDIR /app

# Skopiuj plik requirements.txt do katalogu roboczego
COPY requirements.txt requirements.txt

# Zainstaluj wymagane pakiety
RUN pip install --no-cache-dir -r requirements.txt

# Utwórz użytkownika bez uprawnień administracyjnych i ustaw odpowiednie uprawnienia dla katalogu /app
RUN useradd -m appuser && chown -R appuser:appuser /app
# Skopiuj skrypt do katalogu roboczego
COPY . .
RUN rm Dockerfile

# Ustaw użytkownika
USER appuser

# Uruchom skrypt Pythona przy starcie kontenera
CMD ["python", "app.py"]