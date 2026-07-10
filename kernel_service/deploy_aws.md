# AWS Lambda Container Image — Deploy Kılavuzu

## Genel Akış
kernel_service/ → Docker image → ECR (AWS container registry) → Lambda function → Function URL (HTTPS endpoint)

---

## Adım 1: AWS CloudShell'i Aç

AWS konsolunda sağ üst köşede **CloudShell** ikonuna tıklayın (>_ şeklinde).
Açılan terminalde tüm komutları çalıştıracağız — hiçbir şey indirmeniz gerekmiyor.

---

## Adım 2: ECR Reposu Oluştur

```bash
aws ecr create-repository \
  --repository-name shapelid-kernel \
  --region eu-central-1
```

Çıktıda `repositoryUri` göreceksiniz:
```
123456789.dkr.ecr.eu-central-1.amazonaws.com/shapelid-kernel
```
Bu URI'yi kopyalayın — sonraki adımlarda kullanacaksınız.

---

## Adım 3: Kodu CloudShell'e Yükle

CloudShell'de **Actions → Upload file** ile şu dosyaları tek tek yükleyin:
- `main.py`
- `lambda_handler.py`
- `requirements.txt`
- `Dockerfile`
- `analyzers/` klasörü (önce zip'leyip yükleyin)
- `pricing/` klasörü (önce zip'leyip yükleyin)

Zip'leri açın:
```bash
unzip analyzers.zip -d analyzers/
unzip pricing.zip -d pricing/
```

---

## Adım 4: Docker Image Build Et ve ECR'a Push Et

```bash
# Değişkeni ayarla (kendi URI'nizi yazın)
REPO_URI="123456789.dkr.ecr.eu-central-1.amazonaws.com/shapelid-kernel"

# ECR'a login
aws ecr get-login-password --region eu-central-1 | \
  docker login --username AWS --password-stdin $REPO_URI

# Image build (ilk seferinde ~5-10 dk sürer)
docker build -t shapelid-kernel .

# Tag ve push
docker tag shapelid-kernel:latest $REPO_URI:latest
docker push $REPO_URI:latest
```

---

## Adım 5: Lambda Function Oluştur

### 5a — IAM Role (bir kez yapılır)
```bash
# Lambda execution role oluştur
aws iam create-role \
  --role-name shapelid-kernel-role \
  --assume-role-policy-document '{
    "Version":"2012-10-17",
    "Statement":[{
      "Effect":"Allow",
      "Principal":{"Service":"lambda.amazonaws.com"},
      "Action":"sts:AssumeRole"
    }]
  }'

# Temel log yetkisi ekle
aws iam attach-role-policy \
  --role-name shapelid-kernel-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

Role ARN'ı not edin: `arn:aws:iam::123456789:role/shapelid-kernel-role`

### 5b — Lambda Function Oluştur
```bash
ROLE_ARN="arn:aws:iam::HESAP_ID:role/shapelid-kernel-role"
REPO_URI="123456789.dkr.ecr.eu-central-1.amazonaws.com/shapelid-kernel:latest"

aws lambda create-function \
  --function-name shapelid-kernel \
  --package-type Image \
  --code ImageUri=$REPO_URI \
  --role $ROLE_ARN \
  --region eu-central-1 \
  --memory-size 2048 \
  --timeout 60 \
  --architectures x86_64
```

---

## Adım 6: Function URL Ekle (HTTPS endpoint)

```bash
aws lambda add-permission \
  --function-name shapelid-kernel \
  --statement-id FunctionURLAllowPublic \
  --action lambda:InvokeFunctionUrl \
  --principal "*" \
  --function-url-auth-type NONE \
  --region eu-central-1

aws lambda create-function-url-config \
  --function-name shapelid-kernel \
  --auth-type NONE \
  --region eu-central-1
```

Çıktıda `FunctionUrl` göreceksiniz:
```
https://XXXXXXXX.lambda-url.eu-central-1.on.aws/
```

**Bu URL'i kopyalayın — Base44'e eklenecek `KERNEL_SERVICE_URL` budur.**

---

## Adım 7: Test Et

```bash
curl https://XXXXXXXX.lambda-url.eu-central-1.on.aws/health
# {"status":"ok","version":"1.0.0","phase":"faz-1"}
```

---

## Tahmini Maliyet

| Kullanım | Maliyet |
|---|---|
| İlk 1M istek/ay | **Ücretsiz** (kalıcı free tier) |
| İlk 400.000 GB-saniye/ay | **Ücretsiz** |
| 2GB RAM × 30sn × 10K istek | ~$0.10 |
| **Tipik MVP maliyeti** | **$0 - $2/ay** |

---

## Güncelleme (yeni kod deploy)

```bash
docker build -t shapelid-kernel .
docker tag shapelid-kernel:latest $REPO_URI:latest
docker push $REPO_URI:latest

aws lambda update-function-code \
  --function-name shapelid-kernel \
  --image-uri $REPO_URI:latest \
  --region eu-central-1
```
