FROM python:3.12-slim

WORKDIR /app

# mysqlclient needs the MySQL client headers + a C compiler to build.
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Runs migrations + seeds the demo admin on every container start, then
# serves. Fine for this project's scope; a production image would split
# migrate/seed into a separate init step ahead of a WSGI server.
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py create_demo_admin && python manage.py runserver 0.0.0.0:8000"]
