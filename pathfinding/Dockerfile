FROM python:3
RUN apt-get update && apt-get install -y software-properties-common \
    postgresql-client
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD [ "sh", "entrypoint.sh" ]