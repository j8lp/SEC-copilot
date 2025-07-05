FROM python:3.10

LABEL maintainer "Triumph"

COPY ../ /app

WORKDIR /app

RUN pip install --no-cache-dir -r requirements.txt

ARG OPENAI_API_KEY
ARG SEC_API_KEY

ENV OPENAI_API_KEY=$OPENAI_API_KEY
ENV SEC_API_KEY=$SEC_API_KEY

CMD ["streamlit", "run", "app.py"]