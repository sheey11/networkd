FROM python:3.8.12-alpine3.15
WORKDIR /usr/src/app
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "./networkd.py" ]
