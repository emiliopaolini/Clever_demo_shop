
FROM python:3.9

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt


ENV PYTHONUNBUFFERED=1
ENV API_ENDPOINT=http://10.109.226.4:5000/clusters/cluster1/pods/resources
ENV INTERVAL_SEC=2
ENV WINDOW_SIZE=15
ENV FORECAST_HORIZON=10
ENV POD_FILTER=recommendationservice
ENV MODEL_PATH=LSTM_model
ENV SCALER_PATH=scaler.pkl


CMD ["python", "real_time.py"]