FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성: LibreOffice(PDF 변환), poppler-utils(PNG 변환), 폰트 관련
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-noto-cjk \
    libreoffice-impress \
    poppler-utils \
    wget \
    unzip \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

# Pretendard 폰트 설치
RUN wget -q https://github.com/orioncactus/pretendard/releases/download/v1.3.9/Pretendard-1.3.9.zip \
    && unzip -q Pretendard-1.3.9.zip -d /usr/share/fonts/pretendard \
    && rm Pretendard-1.3.9.zip \
    && fc-cache -fv

# Python 의존성
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 임시 디렉토리
RUN mkdir -p /tmp/deckcraft/exports

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
