FROM python:3.8

WORKDIR /app

COPY . /app

RUN pip install pymongo

EXPOSE 3000 5050

CMD ["python", "main.py"]