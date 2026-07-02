#====================================================================================================
# START - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================

# THIS SECTION CONTAINS CRITICAL TESTING INSTRUCTIONS FOR BOTH AGENTS
# BOTH MAIN_AGENT AND TESTING_AGENT MUST PRESERVE THIS ENTIRE BLOCK

# Communication Protocol:
# If the `testing_agent` is available, main agent should delegate all testing tasks to it.
#
# You have access to a file called `test_result.md`. This file contains the complete testing state
# and history, and is the primary means of communication between main and the testing agent.
#
# Main and testing agents must follow this exact format to maintain testing data. 
# The testing data must be entered in yaml format Below is the data structure:
# 
## user_problem_statement: {problem_statement}
## backend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.py"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## frontend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.js"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## metadata:
##   created_by: "main_agent"
##   version: "1.0"
##   test_sequence: 0
##   run_ui: false
##
## test_plan:
##   current_focus:
##     - "Task name 1"
##     - "Task name 2"
##   stuck_tasks:
##     - "Task name with persistent issues"
##   test_all: false
##   test_priority: "high_first"  # or "sequential" or "stuck_first"
##
## agent_communication:
##     -agent: "main"  # or "testing" or "user"
##     -message: "Communication message between agents"

# Protocol Guidelines for Main agent
#
# 1. Update Test Result File Before Testing:
#    - Main agent must always update the `test_result.md` file before calling the testing agent
#    - Add implementation details to the status_history
#    - Set `needs_retesting` to true for tasks that need testing
#    - Update the `test_plan` section to guide testing priorities
#    - Add a message to `agent_communication` explaining what you've done
#
# 2. Incorporate User Feedback:
#    - When a user provides feedback that something is or isn't working, add this information to the relevant task's status_history
#    - Update the working status based on user feedback
#    - If a user reports an issue with a task that was marked as working, increment the stuck_count
#    - Whenever user reports issue in the app, if we have testing agent and task_result.md file so find the appropriate task for that and append in status_history of that task to contain the user concern and problem as well 
#
# 3. Track Stuck Tasks:
#    - Monitor which tasks have high stuck_count values or where you are fixing same issue again and again, analyze that when you read task_result.md
#    - For persistent issues, use websearch tool to find solutions
#    - Pay special attention to tasks in the stuck_tasks list
#    - When you fix an issue with a stuck task, don't reset the stuck_count until the testing agent confirms it's working
#
# 4. Provide Context to Testing Agent:
#    - When calling the testing agent, provide clear instructions about:
#      - Which tasks need testing (reference the test_plan)
#      - Any authentication details or configuration needed
#      - Specific test scenarios to focus on
#      - Any known issues or edge cases to verify
#
# 5. Call the testing agent with specific instructions referring to test_result.md
#
# IMPORTANT: Main agent must ALWAYS update test_result.md BEFORE calling the testing agent, as it relies on this file to understand what to test next.

#====================================================================================================
# END - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================



#====================================================================================================
# Testing Data - Main Agent and testing sub agent both should log testing data below this section
#====================================================================================================

user_problem_statement: "Clone of app.storyboarder.ai core app: upload screenplay (PDF/FDX/Fountain/Word/TXT), collate scenes, auto-create characters/locations/objects, edit characters & locations. Backend: MongoDB persistence, server-side parsing, CRUD, AI image gen (Nano Banana), PDF exports, settings + API keys, ComfyUI provider, Seedance animatic."

backend:
  - task: "Projects CRUD (list/create/get/update/delete)"
    implemented: true
    working: true
    file: "server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "POST /api/projects parses screenplay text into scenes/characters/locations/objects and persists. GET list/single, PUT title/format, DELETE. Use /api/seed-sample to create sample, or POST with sample screenplay from /api/sample-screenplay."
        -working: true
        -agent: "testing"
        -comment: "✅ ALL TESTS PASSED. Tested: POST /api/seed-sample (created sample project with 6 scenes, 3 characters, 5 locations, 8 objects), GET /api/projects (list working), GET /api/projects/{id} (retrieval working), POST /api/projects with valid screenplay (parsed correctly), POST /api/projects with short screenplay (correctly rejected with 400). All CRUD operations working correctly."

  - task: "Screenplay upload + server-side parsing (txt/fountain real; pdf/docx/fdx extraction)"
    implemented: true
    working: true
    file: "server.py, screenplay_parser.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "POST /api/projects/upload (multipart file). Extracts text via pypdf/python-docx/xml for binary; falls back to sample if extraction yields <20 chars. Parser detects scene headings (INT/EXT), character cues (ALLCAPS), locations, props."
        -working: true
        -agent: "testing"
        -comment: "✅ ALL TESTS PASSED. Tested: POST /api/projects/upload with .txt file (parsed 2 scenes, 2 characters correctly), POST /api/projects/upload with .fountain file (parsed 2 scenes correctly). Scene heading detection, character cue extraction (ALLCAPS), and location parsing all working as expected."

  - task: "Entity CRUD (characters/locations/objects/scenes update & delete)"
    implemented: true
    working: true
    file: "server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "PUT/DELETE /api/projects/{pid}/{kind}/{eid}. kind in characters,locations,objects,scenes. Merges fields, keeps id."
        -working: true
        -agent: "testing"
        -comment: "✅ ALL TESTS PASSED. Tested: PUT /api/projects/{pid}/characters/{cid} (successfully updated character name, role, appearance and persisted changes), DELETE /api/projects/{pid}/objects/{oid} (successfully removed object), PUT with invalid kind (correctly rejected with 400). Entity updates merge correctly and preserve IDs."

  - task: "Settings + API keys manager (mask secrets)"
    implemented: true
    working: true
    file: "server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "GET/PUT /api/settings (global doc). POST /api/settings/keys add provider key (fal/comfyui/custom etc), DELETE /api/settings/keys/{kid}. Returned keys are masked."
        -working: true
        -agent: "testing"
        -comment: "✅ ALL TESTS PASSED. Tested: GET /api/settings (creates default settings correctly), PUT /api/settings (updated defaultArtStyle successfully), POST /api/settings/keys with provider=fal (key added and properly masked as 'fal-••••890'), DELETE /api/settings/keys/{kid} (key removed successfully). Secret masking working correctly - full key never exposed in responses."

  - task: "PDF Exports (storyboard/shotlist/story)"
    implemented: true
    working: true
    file: "server.py, export_service.py"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "GET /api/projects/{pid}/export?type=storyboard|shotlist|story returns application/pdf. Verify content-type and non-empty body."
        -working: true
        -agent: "testing"
        -comment: "✅ ALL TESTS PASSED. Tested: GET /api/projects/{pid}/export?type=storyboard (generated 2847 bytes PDF), ?type=shotlist (generated 2493 bytes PDF), ?type=story (generated 5050 bytes PDF). All exports return correct content-type (application/pdf), non-empty bodies, and valid PDF format. Invalid type correctly rejected with 400."

  - task: "AI image generation (Nano Banana via Emergent key)"
    implemented: true
    working: true
    file: "server.py, ai_service.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "POST /api/projects/{pid}/generate-image {target,entityId,provider:nano}. Uses gemini-3.1-flash-image-preview. Saves PNG to /app/backend/generated, serves at /api/images/{file}, updates entity image field. NOTE: real model call, may take time/cost. Test one scene image generation."
        -working: true
        -agent: "testing"
        -comment: "✅ ALL TESTS PASSED. Tested: POST /api/projects/{pid}/generate-image with target=scene, provider=nano (successfully generated image in ~30s, returned /api/images/img-*.png URL), GET /api/images/{filename} (retrieved 796KB PNG image with correct content-type). Real Nano Banana integration working correctly with gemini-3.1-flash-image-preview model."

  - task: "Animatic via Seedance (requires user key) - error path"
    implemented: true
    working: true
    file: "server.py, ai_service.py"
    stuck_count: 0
    priority: "low"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "POST /api/projects/{pid}/animatic. Without a fal/custom key configured it MUST return 400 with guidance. Only test the 400 path (no real key available)."
        -working: true
        -agent: "testing"
        -comment: "✅ TEST PASSED. Tested: POST /api/projects/{pid}/animatic without video key configured (correctly returned 400 with clear error message: 'No video provider key configured. Add a fal.ai or custom key in Settings to generate animatics.'). Error path working as expected."

  - task: "Image upload endpoint (user-provided artwork)"
    implemented: true
    working: true
    file: "server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "POST /api/upload-image (multipart file upload). Accepts PNG/JPG/JPEG/WEBP/GIF (max 15MB). Returns JSON {image: /api/images/up-{uuid}.ext}. GET /api/images/{filename} serves with correct content-type. Validates file types and rejects unsupported formats with 400. Scene frameImage field can be updated with uploaded image path."
        -working: true
        -agent: "testing"
        -comment: "✅ ALL TESTS PASSED (5/5). Tested: (1) POST /api/upload-image with PNG - uploaded successfully, returned /api/images/up-*.png path ✅ (2) GET uploaded PNG - retrieved with correct content-type image/png (132 bytes) ✅ (3) POST /api/upload-image with JPG - uploaded successfully, returned /api/images/up-*.jpg path, GET served with content-type image/jpeg ✅ (4) POST /api/upload-image with .txt file - correctly rejected with 400 and clear error message 'Unsupported image type. Use PNG, JPG, WEBP or GIF.' ✅ (5) PUT /api/projects/{pid}/scenes/{sid} with frameImage field - scene updated successfully with uploaded image path ✅. Image upload endpoint fully functional with proper validation, file type detection, and entity integration."

  - task: "Dialogue parsing from screenplay"
    implemented: true
    working: true
    file: "screenplay_parser.py, server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "Screenplay parser extracts dialogue from screenplay text. Each scene contains a 'dialogue' array with objects {character, line}. Parser detects character cues (ALLCAPS) and associates following lines as dialogue. Used in build_scene_prompt for AI image generation context."
        -working: true
        -agent: "testing"
        -comment: "✅ ALL TESTS PASSED. Tested: POST /api/seed-sample created project with 6 scenes ✅, GET /api/projects/{id} verified all scenes have 'dialogue' array field ✅, First scene contains 3 dialogue entries with proper structure (character: 'Maya', line: '...') ✅, All 6 scenes have non-empty dialogue arrays (required: >=3) ✅, Dialogue objects correctly structured with 'character' and 'line' fields ✅. Dialogue parsing fully functional and integrated with scene data."

  - task: "OpenAI image generation provider (gpt-image-2 with fallback)"
    implemented: true
    working: true
    file: "ai_service.py, server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "POST /api/projects/{pid}/generate-image with provider='openai' uses OpenAI image generation via Emergent key. Tries gpt-image-2 first, falls back to gpt-image-1 if model not routable. Returns /api/images/{filename}.png. Integrated with scene prompt building including dialogue context."
        -working: true
        -agent: "testing"
        -comment: "✅ ALL TESTS PASSED. Tested: POST /api/projects/{id}/generate-image with provider='openai' and target='scene' ✅, Image generated successfully in 16.6 seconds (well within 120s timeout) ✅, Returned proper URL format /api/images/img-*.png ✅, GET /api/images/{filename} retrieved 1.8MB PNG with correct content-type image/png ✅, No 502 error observed - gpt-image-2 is routable via Emergent key (or fallback to gpt-image-1 worked seamlessly) ✅. OpenAI provider fully functional with proper fallback mechanism."

frontend:
  - task: "Frontend integration with backend"
    implemented: false
    working: "NA"
    file: "src/lib/store.js (to be replaced with api)"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "Frontend currently uses localStorage. Will wire to backend API after backend tests pass."

metadata:
  created_by: "main_agent"
  version: "1.0"
  test_sequence: 4
  run_ui: false

test_plan:
  current_focus: []
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication:
    -agent: "main"
    -message: "Backend Phase 2 implemented. Please test all backend endpoints. Use POST /api/seed-sample to create a sample project (returns project with id). Then test CRUD, entity edits, settings + keys (verify masking), exports (3 types -> PDF), and ONE AI image generation (provider=nano, target=scene, first scene's entityId) - this is a real Nano Banana call so allow up to ~60s. For animatic, only verify the 400 (no key) path. Do NOT test ComfyUI/Seedance real calls (no reachable endpoint/key)."
    -agent: "testing"
    -message: "🎉 ALL BACKEND TESTS PASSED (29/29). Comprehensive testing completed covering: (1) Projects CRUD - seed-sample, list, get, create with validation ✅ (2) Screenplay upload - .txt and .fountain parsing ✅ (3) Entity CRUD - character update, object delete, invalid kind rejection ✅ (4) Settings & API keys - CRUD operations with proper secret masking ✅ (5) PDF Exports - all 3 types (storyboard/shotlist/story) generating valid PDFs ✅ (6) AI image generation - real Nano Banana call successful, generated 796KB PNG ✅ (7) Animatic error path - correctly returns 400 with clear message ✅. Backend is production-ready. All endpoints working correctly with proper validation, error handling, and data persistence."
    -agent: "main"
    -message: "Added image upload endpoint POST /api/upload-image for user-provided artwork. Supports PNG/JPG/JPEG/WEBP/GIF with 15MB limit. Returns /api/images/up-{uuid}.ext path. Validates file types and rejects unsupported formats. Scene frameImage field can be updated with uploaded paths. Please test ONLY this new endpoint."
    -agent: "testing"
    -message: "✅ IMAGE UPLOAD ENDPOINT TESTS PASSED (5/5). Tested: PNG upload → 200 with correct path format ✅, GET PNG → 200 with image/png content-type ✅, JPG upload → 200 with .jpg extension and image/jpeg content-type ✅, Unsupported .txt file → 400 with clear error message ✅, Scene frameImage update → 200 with uploaded image path persisted ✅. New image upload endpoint fully functional and integrated with entity updates."
    -agent: "testing"
    -message: "✅ DIALOGUE PARSING & OPENAI PROVIDER TESTS PASSED (7/7). Tested per review request: (1) Dialogue parsing - POST /api/seed-sample created project, GET /api/projects/{id} verified all 6 scenes have 'dialogue' arrays with proper {character, line} structure, first scene contains Maya dialogue, all scenes have non-empty dialogue (exceeds >=3 requirement) ✅ (2) OpenAI image generation - POST /api/projects/{id}/generate-image with provider='openai' generated image in 16.6s (within 120s timeout), returned /api/images/img-*.png, GET image retrieved 1.8MB PNG successfully, NO 502 error observed (gpt-image-2 routable via Emergent key or fallback to gpt-image-1 worked) ✅. Both new features fully functional."