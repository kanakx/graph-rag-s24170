FROM python:3.12-slim

WORKDIR /app

RUN pip install --upgrade pip

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/

EXPOSE 8000

CMD ["streamlit", "run", "src/app.py"]
