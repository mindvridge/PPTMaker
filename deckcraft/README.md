# DeckCraft

AI가 주제를 받아 디자인 품질 높은 PPT를 자동 생성하고, 웹 에디터에서 수정 후 PPTX/PDF로 내보내는 서비스.

## 구조

```
deckcraft/
├── frontend/          # Next.js 14 (App Router) + TypeScript + Tailwind CSS + Zustand
├── backend/           # FastAPI + Uvicorn + python-pptx
├── shared/            # 프론트/백엔드 공유 슬라이드 JSON 스키마
└── docker-compose.yml # frontend + backend + redis
```

## 실행

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

## 개발 (로컬)

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## 슬라이드 데이터 모델

`shared/slide-schema.json`이 프론트엔드(Fabric.js)와 백엔드(python-pptx)의 유일한 인터페이스입니다.

- **JSON Schema**: `shared/slide-schema.json`
- **TypeScript + Zod**: `frontend/src/lib/slide-model.ts`
- **Pydantic v2**: `backend/app/models/schemas.py`
