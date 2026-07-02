# Storyboarder.ai Clone — API Contracts

## Overview
Backend persists projects in MongoDB, parses screenplays server-side (PDF/DOCX/FDX/Fountain/TXT),
generates AI images (Gemini Nano Banana via EMERGENT_LLM_KEY), exports PDFs, manages settings &
user API keys, and generates animatics via Seedance 2.0 (using a user-supplied fal.ai/custom key
stored in Settings).

Base: `${REACT_APP_BACKEND_URL}/api`

## Data Models
- **Project**: id, title, format, fileName, cover, createdAt, screenplay, scenes[], characters[], locations[], objects[]
- **Scene**: id, number, heading, intExt, location, timeOfDay, synopsis, action, characters[], frameImage, videoUrl, pageEighths
- **Character**: id, name, role, age, gender, description, appearance, image, sceneCount
- **Location**: id, name, intExt, type, timeOfDay, description, image, sceneCount
- **Object**: id, name, category, mentions, description
- **Settings**: id="global", profile{name,email,studio}, defaultArtStyle, defaultFormat, exportPrefs{}, apiKeys[{id,provider,label,key}]

## Endpoints
- `GET /api/projects` → list
- `POST /api/projects` {title, screenplay, format} → parse + create
- `POST /api/projects/upload` (multipart: file, title, format) → extract text + parse + create
- `GET /api/projects/{id}`
- `PUT /api/projects/{id}` {title, format}
- `DELETE /api/projects/{id}`
- `PUT /api/projects/{id}/{kind}/{eid}` kind in [characters,locations,objects,scenes] → update entity
- `DELETE /api/projects/{id}/{kind}/{eid}` → delete entity
- `POST /api/projects/{id}/generate-image` {target:"scene|character|location", entityId, prompt, style} → Nano Banana → saves file, returns {image}
- `POST /api/projects/{id}/animatic` {sceneId, prompt} → Seedance via stored key → returns {videoUrl}  (requires fal/custom key in settings)
- `GET /api/projects/{id}/export?type=storyboard|shotlist|story` → PDF FileResponse
- `GET /api/settings` ; `PUT /api/settings`
- `POST /api/settings/keys` {provider,label,key} ; `DELETE /api/settings/keys/{kid}`
- `GET /api/images/{filename}` → serves generated image files
- `GET /api/videos/{filename}` → serves animatic files

## Frontend integration
- Replace `lib/store.js` localStorage calls with axios calls to above endpoints (keep same shape).
- mock.js parser stays only as fallback; primary parse is server-side.
- Images: generated images served from `${BACKEND_URL}/api/images/...`; stock images remain default until user generates.
- Settings page reads/writes `/api/settings`; API keys manager add/remove.
- Export buttons hit `/export`; Animatic button hits `/animatic`.

## Mocked / Notes
- AI images: REAL via Emergent key (Nano Banana).
- Animatic video: REAL via Seedance 2.0 ONLY if user adds fal.ai (or custom) key in Settings; otherwise returns 400 with guidance.
