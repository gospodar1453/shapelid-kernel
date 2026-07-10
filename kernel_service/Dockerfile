FROM public.ecr.aws/lambda/python:3.11

# Sistem bağımlılıkları
RUN dnf install -y mesa-libGL glib2 && dnf clean all

# Bağımlılıkları kopyala ve yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama kodunu kopyala
COPY main.py .
COPY analyzers/ analyzers/
COPY pricing/ pricing/

# Lambda handler wrapper
COPY lambda_handler.py .

CMD ["lambda_handler.handler"]
