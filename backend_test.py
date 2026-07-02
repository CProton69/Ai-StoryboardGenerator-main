#!/usr/bin/env python3
"""
Backend API Testing for Storyboarder.ai Clone
Tests all backend endpoints following the review request order.
"""
import requests
import json
import time
import io
from pathlib import Path

# Backend URL from frontend/.env
BASE_URL = "https://visual-narrative-lab.preview.emergentagent.com/api"

# Test results tracking
test_results = {
    "passed": [],
    "failed": [],
    "warnings": []
}

def log_pass(test_name, details=""):
    """Log a passed test"""
    msg = f"✅ PASS: {test_name}"
    if details:
        msg += f" - {details}"
    print(msg)
    test_results["passed"].append(test_name)

def log_fail(test_name, details=""):
    """Log a failed test"""
    msg = f"❌ FAIL: {test_name}"
    if details:
        msg += f" - {details}"
    print(msg)
    test_results["failed"].append({"test": test_name, "details": details})

def log_warning(test_name, details=""):
    """Log a warning"""
    msg = f"⚠️  WARNING: {test_name}"
    if details:
        msg += f" - {details}"
    print(msg)
    test_results["warnings"].append({"test": test_name, "details": details})

def print_section(title):
    """Print a section header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

# Global variable to store project ID from seed-sample
sample_project_id = None
sample_screenplay_text = None

def test_1_seed_sample():
    """Test 1: POST /api/seed-sample - creates/returns sample project"""
    global sample_project_id
    print_section("TEST 1: POST /api/seed-sample")
    
    try:
        response = requests.post(f"{BASE_URL}/seed-sample", timeout=30)
        
        if response.status_code != 200:
            log_fail("seed-sample endpoint", f"Expected 200, got {response.status_code}")
            return False
        
        data = response.json()
        
        # Verify project structure
        if "id" not in data:
            log_fail("seed-sample response", "Missing 'id' field")
            return False
        
        sample_project_id = data["id"]
        log_pass("seed-sample project ID", f"ID: {sample_project_id}")
        
        # Verify title
        if data.get("title") != "The Last Transmission":
            log_fail("seed-sample title", f"Expected 'The Last Transmission', got '{data.get('title')}'")
            return False
        log_pass("seed-sample title")
        
        # Verify scenes (>=6)
        scenes = data.get("scenes", [])
        if len(scenes) < 6:
            log_fail("seed-sample scenes", f"Expected >=6 scenes, got {len(scenes)}")
            return False
        log_pass("seed-sample scenes", f"Found {len(scenes)} scenes")
        
        # Verify characters (Maya, Eli, Solenne)
        characters = data.get("characters", [])
        if not characters:
            log_fail("seed-sample characters", "No characters found")
            return False
        
        char_names = [c.get("name", "").lower() for c in characters]
        expected_chars = ["maya", "eli", "solenne"]
        found_chars = [name for name in expected_chars if any(name in cn for cn in char_names)]
        
        if len(found_chars) < 3:
            log_warning("seed-sample characters", f"Expected Maya/Eli/Solenne, found: {char_names}")
        else:
            log_pass("seed-sample characters", f"Found {len(characters)} characters including main cast")
        
        # Verify locations
        locations = data.get("locations", [])
        if not locations:
            log_fail("seed-sample locations", "No locations found")
            return False
        log_pass("seed-sample locations", f"Found {len(locations)} locations")
        
        # Verify objects
        objects = data.get("objects", [])
        if not objects:
            log_warning("seed-sample objects", "No objects found (may be expected)")
        else:
            log_pass("seed-sample objects", f"Found {len(objects)} objects")
        
        return True
        
    except Exception as e:
        log_fail("seed-sample endpoint", f"Exception: {str(e)}")
        return False

def test_2_list_projects():
    """Test 2: GET /api/projects - list includes sample project"""
    print_section("TEST 2: GET /api/projects")
    
    try:
        response = requests.get(f"{BASE_URL}/projects", timeout=30)
        
        if response.status_code != 200:
            log_fail("list projects", f"Expected 200, got {response.status_code}")
            return False
        
        data = response.json()
        
        if not isinstance(data, list):
            log_fail("list projects response", "Expected array response")
            return False
        
        log_pass("list projects endpoint", f"Found {len(data)} projects")
        
        # Verify sample project is in the list
        if sample_project_id:
            found = any(p.get("id") == sample_project_id for p in data)
            if found:
                log_pass("sample project in list")
            else:
                log_fail("sample project in list", f"Project {sample_project_id} not found")
                return False
        
        return True
        
    except Exception as e:
        log_fail("list projects", f"Exception: {str(e)}")
        return False

def test_3_get_project():
    """Test 3: GET /api/projects/{id} - returns full project"""
    print_section("TEST 3: GET /api/projects/{id}")
    
    if not sample_project_id:
        log_fail("get project", "No sample project ID available")
        return False
    
    try:
        response = requests.get(f"{BASE_URL}/projects/{sample_project_id}", timeout=30)
        
        if response.status_code != 200:
            log_fail("get project", f"Expected 200, got {response.status_code}")
            return False
        
        data = response.json()
        
        # Verify it's the correct project
        if data.get("id") != sample_project_id:
            log_fail("get project", f"ID mismatch: expected {sample_project_id}, got {data.get('id')}")
            return False
        
        log_pass("get project by ID", f"Retrieved project: {data.get('title')}")
        
        # Verify full structure
        required_fields = ["id", "title", "scenes", "characters", "locations", "objects"]
        for field in required_fields:
            if field not in data:
                log_fail("get project structure", f"Missing field: {field}")
                return False
        
        log_pass("get project structure", "All required fields present")
        return True
        
    except Exception as e:
        log_fail("get project", f"Exception: {str(e)}")
        return False

def test_4_create_project():
    """Test 4: POST /api/projects with screenplay text"""
    global sample_screenplay_text
    print_section("TEST 4: POST /api/projects")
    
    # First, get the sample screenplay
    try:
        response = requests.get(f"{BASE_URL}/sample-screenplay", timeout=30)
        if response.status_code != 200:
            log_fail("get sample screenplay", f"Expected 200, got {response.status_code}")
            return False
        
        screenplay_data = response.json()
        sample_screenplay_text = screenplay_data.get("screenplay", "")
        
        if not sample_screenplay_text:
            log_fail("get sample screenplay", "No screenplay text returned")
            return False
        
        log_pass("get sample screenplay", f"Retrieved {len(sample_screenplay_text)} characters")
        
    except Exception as e:
        log_fail("get sample screenplay", f"Exception: {str(e)}")
        return False
    
    # Test 4a: Create project with valid screenplay
    try:
        payload = {
            "title": "My Test Project",
            "format": "Short Film",
            "screenplay": sample_screenplay_text
        }
        
        response = requests.post(f"{BASE_URL}/projects", json=payload, timeout=30)
        
        if response.status_code != 200:
            log_fail("create project with valid screenplay", f"Expected 200, got {response.status_code}")
            return False
        
        data = response.json()
        
        # Verify parsing worked
        if not data.get("scenes"):
            log_fail("create project parsing", "No scenes parsed")
            return False
        
        if not data.get("characters"):
            log_fail("create project parsing", "No characters parsed")
            return False
        
        log_pass("create project with valid screenplay", f"Created project with {len(data['scenes'])} scenes, {len(data['characters'])} characters")
        
    except Exception as e:
        log_fail("create project with valid screenplay", f"Exception: {str(e)}")
        return False
    
    # Test 4b: Create project with too-short screenplay (should return 400)
    try:
        payload = {
            "title": "Invalid Project",
            "screenplay": "hi"
        }
        
        response = requests.post(f"{BASE_URL}/projects", json=payload, timeout=30)
        
        if response.status_code != 400:
            log_fail("create project with short screenplay", f"Expected 400, got {response.status_code}")
            return False
        
        log_pass("create project validation", "Correctly rejected too-short screenplay with 400")
        
    except Exception as e:
        log_fail("create project with short screenplay", f"Exception: {str(e)}")
        return False
    
    return True

def test_5_upload_project():
    """Test 5: POST /api/projects/upload with file"""
    print_section("TEST 5: POST /api/projects/upload")
    
    # Test 5a: Upload .txt file
    try:
        txt_content = """INT. COFFEE SHOP - DAY

A cozy coffee shop filled with the aroma of fresh brew.

SARAH (30s), a writer, sits at a corner table typing furiously on her laptop.

SARAH
(to herself)
This deadline is killing me.

BARISTA (20s) approaches with a fresh cup.

BARISTA
Another espresso?

SARAH
You're a lifesaver.

EXT. CITY STREET - NIGHT

Sarah walks home under streetlights, clutching her laptop bag.
"""
        
        files = {
            'file': ('test_screenplay.txt', io.BytesIO(txt_content.encode('utf-8')), 'text/plain')
        }
        data = {
            'title': 'Test Upload TXT',
            'format': 'Short Film'
        }
        
        response = requests.post(f"{BASE_URL}/projects/upload", files=files, data=data, timeout=30)
        
        if response.status_code != 200:
            log_fail("upload .txt file", f"Expected 200, got {response.status_code}")
            return False
        
        result = response.json()
        
        # Verify parsing
        scenes = result.get("scenes", [])
        if len(scenes) < 2:
            log_fail("upload .txt parsing", f"Expected at least 2 scenes, got {len(scenes)}")
            return False
        
        # Check for SARAH character
        characters = result.get("characters", [])
        char_names = [c.get("name", "").lower() for c in characters]
        if not any("sarah" in name for name in char_names):
            log_warning("upload .txt character detection", f"SARAH not detected in characters: {char_names}")
        
        log_pass("upload .txt file", f"Parsed {len(scenes)} scenes, {len(characters)} characters")
        
    except Exception as e:
        log_fail("upload .txt file", f"Exception: {str(e)}")
        return False
    
    # Test 5b: Upload .fountain file
    try:
        fountain_content = """Title: Test Fountain
Author: Test

FADE IN:

INT. LABORATORY - DAY

DR. JONES examines a mysterious artifact under bright lights.

DR. JONES
This changes everything.

ASSISTANT
Should we call the university?

DR. JONES
Not yet. We need more data.

EXT. DESERT - SUNSET

The sun sets over endless sand dunes.

FADE OUT.
"""
        
        files = {
            'file': ('test_screenplay.fountain', io.BytesIO(fountain_content.encode('utf-8')), 'text/plain')
        }
        data = {
            'title': 'Test Upload Fountain',
            'format': 'Short Film'
        }
        
        response = requests.post(f"{BASE_URL}/projects/upload", files=files, data=data, timeout=30)
        
        if response.status_code != 200:
            log_fail("upload .fountain file", f"Expected 200, got {response.status_code}")
            return False
        
        result = response.json()
        
        scenes = result.get("scenes", [])
        if len(scenes) < 2:
            log_fail("upload .fountain parsing", f"Expected at least 2 scenes, got {len(scenes)}")
            return False
        
        log_pass("upload .fountain file", f"Parsed {len(scenes)} scenes")
        
    except Exception as e:
        log_fail("upload .fountain file", f"Exception: {str(e)}")
        return False
    
    return True

def test_6_entity_crud():
    """Test 6: Entity CRUD operations"""
    print_section("TEST 6: Entity CRUD (PUT/DELETE)")
    
    if not sample_project_id:
        log_fail("entity CRUD", "No sample project ID available")
        return False
    
    # Get the project to find entity IDs
    try:
        response = requests.get(f"{BASE_URL}/projects/{sample_project_id}", timeout=30)
        if response.status_code != 200:
            log_fail("entity CRUD setup", "Could not fetch project")
            return False
        
        project = response.json()
        
    except Exception as e:
        log_fail("entity CRUD setup", f"Exception: {str(e)}")
        return False
    
    # Test 6a: PUT /api/projects/{pid}/characters/{characterId}
    try:
        characters = project.get("characters", [])
        if not characters:
            log_fail("entity CRUD characters", "No characters to update")
            return False
        
        char_id = characters[0]["id"]
        update_payload = {
            "name": "Updated Character Name",
            "role": "Lead",
            "appearance": "Tall with dark hair and piercing eyes"
        }
        
        response = requests.put(
            f"{BASE_URL}/projects/{sample_project_id}/characters/{char_id}",
            json=update_payload,
            timeout=30
        )
        
        if response.status_code != 200:
            log_fail("update character", f"Expected 200, got {response.status_code}")
            return False
        
        updated_project = response.json()
        updated_char = next((c for c in updated_project["characters"] if c["id"] == char_id), None)
        
        if not updated_char:
            log_fail("update character", "Character not found after update")
            return False
        
        if updated_char["name"] != "Updated Character Name":
            log_fail("update character", f"Name not updated: {updated_char['name']}")
            return False
        
        if updated_char["appearance"] != "Tall with dark hair and piercing eyes":
            log_fail("update character", "Appearance not updated")
            return False
        
        log_pass("update character", f"Successfully updated character {char_id}")
        
    except Exception as e:
        log_fail("update character", f"Exception: {str(e)}")
        return False
    
    # Test 6b: DELETE /api/projects/{pid}/objects/{objectId}
    try:
        objects = project.get("objects", [])
        if not objects:
            log_warning("delete object", "No objects to delete (may be expected)")
        else:
            obj_id = objects[0]["id"]
            
            response = requests.delete(
                f"{BASE_URL}/projects/{sample_project_id}/objects/{obj_id}",
                timeout=30
            )
            
            if response.status_code != 200:
                log_fail("delete object", f"Expected 200, got {response.status_code}")
                return False
            
            updated_project = response.json()
            remaining_objects = updated_project.get("objects", [])
            
            if any(o["id"] == obj_id for o in remaining_objects):
                log_fail("delete object", "Object still exists after deletion")
                return False
            
            log_pass("delete object", f"Successfully deleted object {obj_id}")
        
    except Exception as e:
        log_fail("delete object", f"Exception: {str(e)}")
        return False
    
    # Test 6c: Invalid kind should return 400
    try:
        response = requests.put(
            f"{BASE_URL}/projects/{sample_project_id}/invalid_kind/some-id",
            json={"name": "test"},
            timeout=30
        )
        
        if response.status_code != 400:
            log_fail("invalid entity kind", f"Expected 400, got {response.status_code}")
            return False
        
        log_pass("invalid entity kind", "Correctly rejected invalid kind with 400")
        
    except Exception as e:
        log_fail("invalid entity kind", f"Exception: {str(e)}")
        return False
    
    return True

def test_7_settings():
    """Test 7: Settings and API keys management"""
    print_section("TEST 7: Settings & API Keys")
    
    # Test 7a: GET /api/settings (creates default if not exists)
    try:
        response = requests.get(f"{BASE_URL}/settings", timeout=30)
        
        if response.status_code != 200:
            log_fail("get settings", f"Expected 200, got {response.status_code}")
            return False
        
        settings = response.json()
        
        # Verify default structure
        required_fields = ["id", "defaultArtStyle", "defaultFormat", "apiKeys"]
        for field in required_fields:
            if field not in settings:
                log_fail("settings structure", f"Missing field: {field}")
                return False
        
        log_pass("get settings", "Retrieved settings with correct structure")
        
    except Exception as e:
        log_fail("get settings", f"Exception: {str(e)}")
        return False
    
    # Test 7b: PUT /api/settings to change defaultArtStyle
    try:
        update_payload = {
            "defaultArtStyle": "noir black and white"
        }
        
        response = requests.put(f"{BASE_URL}/settings", json=update_payload, timeout=30)
        
        if response.status_code != 200:
            log_fail("update settings", f"Expected 200, got {response.status_code}")
            return False
        
        updated_settings = response.json()
        
        if updated_settings.get("defaultArtStyle") != "noir black and white":
            log_fail("update settings", f"Art style not updated: {updated_settings.get('defaultArtStyle')}")
            return False
        
        log_pass("update settings", "Successfully updated defaultArtStyle")
        
    except Exception as e:
        log_fail("update settings", f"Exception: {str(e)}")
        return False
    
    # Test 7c: POST /api/settings/keys - add API key and verify masking
    try:
        key_payload = {
            "provider": "fal",
            "label": "my fal key",
            "key": "fal-secret-1234567890"
        }
        
        response = requests.post(f"{BASE_URL}/settings/keys", json=key_payload, timeout=30)
        
        if response.status_code != 200:
            log_fail("add API key", f"Expected 200, got {response.status_code}")
            return False
        
        settings_with_key = response.json()
        api_keys = settings_with_key.get("apiKeys", [])
        
        if not api_keys:
            log_fail("add API key", "No API keys in response")
            return False
        
        # Find the key we just added
        added_key = next((k for k in api_keys if k.get("provider") == "fal"), None)
        
        if not added_key:
            log_fail("add API key", "Added key not found in response")
            return False
        
        # Verify key is MASKED
        returned_key = added_key.get("key", "")
        if "fal-secret-1234567890" in returned_key:
            log_fail("API key masking", f"Key not masked: {returned_key}")
            return False
        
        if "•" not in returned_key and "*" not in returned_key:
            log_fail("API key masking", f"Key doesn't appear masked: {returned_key}")
            return False
        
        log_pass("add API key", f"Key added and masked: {returned_key}")
        
        # Store key ID for deletion test
        key_id = added_key.get("id")
        
    except Exception as e:
        log_fail("add API key", f"Exception: {str(e)}")
        return False
    
    # Test 7d: DELETE /api/settings/keys/{kid}
    try:
        if not key_id:
            log_fail("delete API key", "No key ID available")
            return False
        
        response = requests.delete(f"{BASE_URL}/settings/keys/{key_id}", timeout=30)
        
        if response.status_code != 200:
            log_fail("delete API key", f"Expected 200, got {response.status_code}")
            return False
        
        settings_after_delete = response.json()
        remaining_keys = settings_after_delete.get("apiKeys", [])
        
        if any(k.get("id") == key_id for k in remaining_keys):
            log_fail("delete API key", "Key still exists after deletion")
            return False
        
        log_pass("delete API key", f"Successfully deleted key {key_id}")
        
    except Exception as e:
        log_fail("delete API key", f"Exception: {str(e)}")
        return False
    
    return True

def test_8_exports():
    """Test 8: PDF Exports (storyboard, shotlist, story)"""
    print_section("TEST 8: PDF Exports")
    
    if not sample_project_id:
        log_fail("exports", "No sample project ID available")
        return False
    
    export_types = ["storyboard", "shotlist", "story"]
    
    for export_type in export_types:
        try:
            response = requests.get(
                f"{BASE_URL}/projects/{sample_project_id}/export",
                params={"type": export_type},
                timeout=30
            )
            
            if response.status_code != 200:
                log_fail(f"export {export_type}", f"Expected 200, got {response.status_code}")
                continue
            
            # Verify content-type
            content_type = response.headers.get("content-type", "")
            if "application/pdf" not in content_type:
                log_fail(f"export {export_type} content-type", f"Expected application/pdf, got {content_type}")
                continue
            
            # Verify non-empty body
            if len(response.content) == 0:
                log_fail(f"export {export_type} content", "Empty PDF body")
                continue
            
            # Basic PDF validation (starts with %PDF)
            if not response.content.startswith(b'%PDF'):
                log_fail(f"export {export_type} format", "Response doesn't appear to be a PDF")
                continue
            
            log_pass(f"export {export_type}", f"Generated PDF ({len(response.content)} bytes)")
            
        except Exception as e:
            log_fail(f"export {export_type}", f"Exception: {str(e)}")
    
    # Test invalid export type (should return 400)
    try:
        response = requests.get(
            f"{BASE_URL}/projects/{sample_project_id}/export",
            params={"type": "invalid_type"},
            timeout=30
        )
        
        if response.status_code != 400:
            log_fail("export invalid type", f"Expected 400, got {response.status_code}")
            return False
        
        log_pass("export invalid type", "Correctly rejected invalid type with 400")
        
    except Exception as e:
        log_fail("export invalid type", f"Exception: {str(e)}")
        return False
    
    return True

def test_9_ai_image_generation():
    """Test 9: AI image generation (REAL Nano Banana call)"""
    print_section("TEST 9: AI Image Generation (Nano Banana)")
    
    if not sample_project_id:
        log_fail("AI image generation", "No sample project ID available")
        return False
    
    # Get the project to find first scene ID
    try:
        response = requests.get(f"{BASE_URL}/projects/{sample_project_id}", timeout=30)
        if response.status_code != 200:
            log_fail("AI image generation setup", "Could not fetch project")
            return False
        
        project = response.json()
        scenes = project.get("scenes", [])
        
        if not scenes:
            log_fail("AI image generation setup", "No scenes available")
            return False
        
        first_scene_id = scenes[0]["id"]
        
    except Exception as e:
        log_fail("AI image generation setup", f"Exception: {str(e)}")
        return False
    
    # Test AI image generation (allow up to 90s)
    try:
        print("⏳ Generating image with Nano Banana (this may take up to 90 seconds)...")
        
        gen_payload = {
            "target": "scene",
            "entityId": first_scene_id,
            "provider": "nano"
        }
        
        response = requests.post(
            f"{BASE_URL}/projects/{sample_project_id}/generate-image",
            json=gen_payload,
            timeout=90
        )
        
        if response.status_code != 200:
            error_msg = response.text
            log_fail("AI image generation", f"Expected 200, got {response.status_code}. Error: {error_msg}")
            log_warning("AI image generation", "This may be due to model/key issues. Check backend logs for details.")
            return False
        
        result = response.json()
        image_url = result.get("image")
        
        if not image_url:
            log_fail("AI image generation response", "No image URL in response")
            return False
        
        if not image_url.startswith("/api/images/"):
            log_fail("AI image generation URL format", f"Unexpected URL format: {image_url}")
            return False
        
        log_pass("AI image generation", f"Generated image: {image_url}")
        
        # Test fetching the generated image
        try:
            full_image_url = f"{BASE_URL.replace('/api', '')}{image_url}"
            img_response = requests.get(full_image_url, timeout=30)
            
            if img_response.status_code != 200:
                log_fail("fetch generated image", f"Expected 200, got {img_response.status_code}")
                return False
            
            content_type = img_response.headers.get("content-type", "")
            if "image/png" not in content_type:
                log_fail("generated image content-type", f"Expected image/png, got {content_type}")
                return False
            
            if len(img_response.content) == 0:
                log_fail("generated image content", "Empty image body")
                return False
            
            log_pass("fetch generated image", f"Retrieved image ({len(img_response.content)} bytes)")
            
        except Exception as e:
            log_fail("fetch generated image", f"Exception: {str(e)}")
            return False
        
    except requests.exceptions.Timeout:
        log_fail("AI image generation", "Request timed out after 90 seconds")
        return False
    except Exception as e:
        log_fail("AI image generation", f"Exception: {str(e)}")
        return False
    
    return True

def test_10_animatic_error_path():
    """Test 10: Animatic error path (no video key configured)"""
    print_section("TEST 10: Animatic Error Path")
    
    if not sample_project_id:
        log_fail("animatic error path", "No sample project ID available")
        return False
    
    # Get the project to find first scene ID
    try:
        response = requests.get(f"{BASE_URL}/projects/{sample_project_id}", timeout=30)
        if response.status_code != 200:
            log_fail("animatic error path setup", "Could not fetch project")
            return False
        
        project = response.json()
        scenes = project.get("scenes", [])
        
        if not scenes:
            log_fail("animatic error path setup", "No scenes available")
            return False
        
        first_scene_id = scenes[0]["id"]
        
    except Exception as e:
        log_fail("animatic error path setup", f"Exception: {str(e)}")
        return False
    
    # Test animatic without video key (should return 400)
    try:
        animatic_payload = {
            "sceneId": first_scene_id
        }
        
        response = requests.post(
            f"{BASE_URL}/projects/{sample_project_id}/animatic",
            json=animatic_payload,
            timeout=30
        )
        
        if response.status_code != 400:
            log_fail("animatic error path", f"Expected 400, got {response.status_code}")
            return False
        
        error_data = response.json()
        error_msg = error_data.get("detail", "")
        
        # Verify error message mentions configuring a video provider key
        if "video provider key" not in error_msg.lower() and "key configured" not in error_msg.lower():
            log_warning("animatic error message", f"Error message may not be clear: {error_msg}")
        
        log_pass("animatic error path", f"Correctly returned 400 with message: {error_msg}")
        
    except Exception as e:
        log_fail("animatic error path", f"Exception: {str(e)}")
        return False
    
    return True

def print_summary():
    """Print test summary"""
    print_section("TEST SUMMARY")
    
    total_tests = len(test_results["passed"]) + len(test_results["failed"])
    
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {len(test_results['passed'])}")
    print(f"❌ Failed: {len(test_results['failed'])}")
    print(f"⚠️  Warnings: {len(test_results['warnings'])}")
    
    if test_results["failed"]:
        print("\n" + "="*80)
        print("FAILED TESTS:")
        print("="*80)
        for failure in test_results["failed"]:
            print(f"  ❌ {failure['test']}")
            if failure['details']:
                print(f"     {failure['details']}")
    
    if test_results["warnings"]:
        print("\n" + "="*80)
        print("WARNINGS:")
        print("="*80)
        for warning in test_results["warnings"]:
            print(f"  ⚠️  {warning['test']}")
            if warning['details']:
                print(f"     {warning['details']}")
    
    print("\n" + "="*80)
    if len(test_results["failed"]) == 0:
        print("🎉 ALL TESTS PASSED!")
    else:
        print(f"⚠️  {len(test_results['failed'])} TEST(S) FAILED")
    print("="*80 + "\n")

def main():
    """Run all tests in order"""
    print("\n" + "="*80)
    print("  STORYBOARDER.AI BACKEND API TESTS")
    print(f"  Base URL: {BASE_URL}")
    print("="*80)
    
    # Run tests in order
    test_1_seed_sample()
    test_2_list_projects()
    test_3_get_project()
    test_4_create_project()
    test_5_upload_project()
    test_6_entity_crud()
    test_7_settings()
    test_8_exports()
    test_9_ai_image_generation()
    test_10_animatic_error_path()
    
    # Print summary
    print_summary()
    
    # Return exit code
    return 0 if len(test_results["failed"]) == 0 else 1

if __name__ == "__main__":
    exit(main())
