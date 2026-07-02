#!/usr/bin/env python3
"""
Backend API Testing for Dialogue Parsing and OpenAI Image Generation
Tests the newly added features as per review request.
"""
import requests
import json
import time

# Backend URL from frontend/.env
BASE_URL = "https://visual-narrative-lab.preview.emergentagent.com/api"

# Test results tracking
test_results = {
    "passed": [],
    "failed": [],
    "details": []
}

def log_pass(test_name, details=""):
    """Log a passed test"""
    msg = f"✅ PASS: {test_name}"
    if details:
        msg += f" - {details}"
    print(msg)
    test_results["passed"].append(test_name)
    test_results["details"].append({"test": test_name, "status": "PASS", "details": details})

def log_fail(test_name, details=""):
    """Log a failed test"""
    msg = f"❌ FAIL: {test_name}"
    if details:
        msg += f" - {details}"
    print(msg)
    test_results["failed"].append({"test": test_name, "details": details})
    test_results["details"].append({"test": test_name, "status": "FAIL", "details": details})

def print_section(title):
    """Print a section header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

# Global variable to store project ID
sample_project_id = None
first_scene_id = None

def test_1_dialogue_parsing():
    """Test 1: Dialogue parsing - verify scenes have dialogue arrays"""
    global sample_project_id, first_scene_id
    print_section("TEST 1: Dialogue Parsing")
    
    # Step 1: POST /api/seed-sample to get sample project
    try:
        print("Step 1: Creating sample project via POST /api/seed-sample...")
        response = requests.post(f"{BASE_URL}/seed-sample", timeout=30)
        
        if response.status_code != 200:
            log_fail("seed-sample endpoint", f"Expected 200, got {response.status_code}")
            return False
        
        data = response.json()
        sample_project_id = data.get("id")
        
        if not sample_project_id:
            log_fail("seed-sample response", "Missing 'id' field")
            return False
        
        log_pass("seed-sample created", f"Project ID: {sample_project_id}")
        
    except Exception as e:
        log_fail("seed-sample endpoint", f"Exception: {str(e)}")
        return False
    
    # Step 2: GET /api/projects/{id} and verify dialogue arrays
    try:
        print(f"\nStep 2: Fetching project via GET /api/projects/{sample_project_id}...")
        response = requests.get(f"{BASE_URL}/projects/{sample_project_id}", timeout=30)
        
        if response.status_code != 200:
            log_fail("get project", f"Expected 200, got {response.status_code}")
            return False
        
        project = response.json()
        scenes = project.get("scenes", [])
        
        if not scenes:
            log_fail("project scenes", "No scenes found in project")
            return False
        
        log_pass("project retrieved", f"Found {len(scenes)} scenes")
        
        # Step 3: Verify each scene has a 'dialogue' array
        print("\nStep 3: Verifying dialogue arrays in scenes...")
        scenes_with_dialogue = 0
        first_scene_dialogue = None
        
        for i, scene in enumerate(scenes):
            scene_num = i + 1
            
            # Check if dialogue field exists
            if "dialogue" not in scene:
                log_fail(f"scene {scene_num} dialogue field", "Missing 'dialogue' field")
                continue
            
            dialogue = scene.get("dialogue", [])
            
            # Verify it's an array
            if not isinstance(dialogue, list):
                log_fail(f"scene {scene_num} dialogue type", f"Expected array, got {type(dialogue)}")
                continue
            
            # Count scenes with non-empty dialogue
            if dialogue:
                scenes_with_dialogue += 1
                
                # Store first scene dialogue for detailed verification
                if first_scene_dialogue is None:
                    first_scene_dialogue = dialogue
                    first_scene_id = scene.get("id")
                
                # Verify dialogue structure
                for j, dlg in enumerate(dialogue):
                    if not isinstance(dlg, dict):
                        log_fail(f"scene {scene_num} dialogue[{j}]", f"Expected object, got {type(dlg)}")
                        continue
                    
                    if "character" not in dlg:
                        log_fail(f"scene {scene_num} dialogue[{j}]", "Missing 'character' field")
                        continue
                    
                    if "line" not in dlg:
                        log_fail(f"scene {scene_num} dialogue[{j}]", "Missing 'line' field")
                        continue
                
                print(f"  Scene {scene_num}: {len(dialogue)} dialogue entries")
        
        # Step 4: Verify first scene dialogue structure
        print("\nStep 4: Verifying first scene dialogue structure...")
        if not first_scene_dialogue:
            log_fail("first scene dialogue", "First scene has no dialogue")
            return False
        
        # Check for expected characters (Maya, Eli, etc.)
        characters_in_dialogue = [d.get("character", "").lower() for d in first_scene_dialogue]
        
        print(f"  First scene dialogue entries: {len(first_scene_dialogue)}")
        for dlg in first_scene_dialogue[:3]:  # Show first 3
            char = dlg.get("character", "")
            line = dlg.get("line", "")[:50]  # First 50 chars
            print(f"    {char}: {line}...")
        
        # Verify Maya is in the dialogue (expected from sample screenplay)
        if not any("maya" in char for char in characters_in_dialogue):
            log_fail("first scene dialogue content", f"Expected 'Maya' in dialogue, found: {characters_in_dialogue}")
        else:
            log_pass("first scene dialogue content", f"Found Maya in dialogue")
        
        # Step 5: Verify at least 3 scenes have non-empty dialogue
        print(f"\nStep 5: Verifying dialogue coverage...")
        if scenes_with_dialogue < 3:
            log_fail("dialogue coverage", f"Expected at least 3 scenes with dialogue, found {scenes_with_dialogue}")
            return False
        
        log_pass("dialogue coverage", f"{scenes_with_dialogue} scenes have non-empty dialogue (required: >=3)")
        
        # Overall success
        log_pass("dialogue parsing", f"All dialogue arrays properly structured with character/line objects")
        return True
        
    except Exception as e:
        log_fail("dialogue parsing", f"Exception: {str(e)}")
        return False

def test_2_openai_image_generation():
    """Test 2: OpenAI image generation with provider='openai'"""
    print_section("TEST 2: OpenAI Image Generation")
    
    if not sample_project_id or not first_scene_id:
        log_fail("OpenAI image generation", "No sample project or scene ID available")
        return False
    
    try:
        print(f"Testing OpenAI image generation for scene: {first_scene_id}")
        print("⏳ Generating image with OpenAI (gpt-image-2, fallback to gpt-image-1)...")
        print("   This may take up to 120 seconds...")
        
        gen_payload = {
            "target": "scene",
            "entityId": first_scene_id,
            "provider": "openai"
        }
        
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/projects/{sample_project_id}/generate-image",
            json=gen_payload,
            timeout=120
        )
        elapsed = time.time() - start_time
        
        print(f"   Response received in {elapsed:.1f} seconds")
        
        # Check response status
        if response.status_code == 502:
            # Backend error - capture and report detail
            error_detail = response.text
            try:
                error_json = response.json()
                error_detail = error_json.get("detail", error_detail)
            except:
                pass
            
            log_fail("OpenAI image generation", f"502 Bad Gateway - {error_detail}")
            print(f"\n📋 ERROR DETAIL (verbatim):")
            print(f"   Status: 502")
            print(f"   Detail: {error_detail}")
            return False
        
        if response.status_code != 200:
            error_msg = response.text
            try:
                error_json = response.json()
                error_msg = error_json.get("detail", error_msg)
            except:
                pass
            
            log_fail("OpenAI image generation", f"Expected 200, got {response.status_code} - {error_msg}")
            return False
        
        result = response.json()
        image_url = result.get("image")
        
        if not image_url:
            log_fail("OpenAI image generation response", "No 'image' field in response")
            return False
        
        # Verify URL format
        if not image_url.startswith("/api/images/"):
            log_fail("OpenAI image URL format", f"Expected /api/images/...png, got {image_url}")
            return False
        
        if not image_url.endswith(".png"):
            log_fail("OpenAI image URL format", f"Expected .png extension, got {image_url}")
            return False
        
        log_pass("OpenAI image generation", f"Generated image: {image_url} (took {elapsed:.1f}s)")
        
        # Test fetching the generated image
        print(f"\nFetching generated image from {image_url}...")
        try:
            full_image_url = f"{BASE_URL.replace('/api', '')}{image_url}"
            img_response = requests.get(full_image_url, timeout=30)
            
            if img_response.status_code != 200:
                log_fail("fetch OpenAI generated image", f"Expected 200, got {img_response.status_code}")
                return False
            
            content_type = img_response.headers.get("content-type", "")
            if "image" not in content_type:
                log_fail("OpenAI image content-type", f"Expected image/*, got {content_type}")
                return False
            
            if len(img_response.content) == 0:
                log_fail("OpenAI image content", "Empty image body")
                return False
            
            log_pass("fetch OpenAI generated image", f"Retrieved image ({len(img_response.content)} bytes, {content_type})")
            
            # Report which model path succeeded
            print(f"\n✅ SUCCESS PATH: OpenAI image generation completed successfully")
            print(f"   - Provider: openai")
            print(f"   - Model: gpt-image-2 (or fallback to gpt-image-1)")
            print(f"   - Image URL: {image_url}")
            print(f"   - Image size: {len(img_response.content)} bytes")
            print(f"   - Generation time: {elapsed:.1f}s")
            
            return True
            
        except Exception as e:
            log_fail("fetch OpenAI generated image", f"Exception: {str(e)}")
            return False
        
    except requests.exceptions.Timeout:
        log_fail("OpenAI image generation", "Request timed out after 120 seconds")
        return False
    except Exception as e:
        log_fail("OpenAI image generation", f"Exception: {str(e)}")
        return False

def test_3_nano_provider_routing():
    """Test 3: Optional - verify nano provider still works"""
    print_section("TEST 3: Nano Provider Routing (Optional)")
    
    if not sample_project_id:
        log_fail("Nano provider test", "No sample project ID available")
        return False
    
    # Get a different scene for testing
    try:
        response = requests.get(f"{BASE_URL}/projects/{sample_project_id}", timeout=30)
        if response.status_code != 200:
            log_fail("Nano provider test setup", "Could not fetch project")
            return False
        
        project = response.json()
        scenes = project.get("scenes", [])
        
        if len(scenes) < 2:
            print("⚠️  Skipping nano provider test - not enough scenes")
            return True
        
        second_scene_id = scenes[1].get("id")
        
    except Exception as e:
        log_fail("Nano provider test setup", f"Exception: {str(e)}")
        return False
    
    # Quick test with nano provider
    try:
        print(f"Testing nano provider for scene: {second_scene_id}")
        print("⏳ Generating image with Nano Banana (quick test)...")
        
        gen_payload = {
            "target": "scene",
            "entityId": second_scene_id,
            "provider": "nano"
        }
        
        response = requests.post(
            f"{BASE_URL}/projects/{sample_project_id}/generate-image",
            json=gen_payload,
            timeout=90
        )
        
        if response.status_code != 200:
            log_fail("Nano provider routing", f"Expected 200, got {response.status_code}")
            return False
        
        result = response.json()
        image_url = result.get("image")
        
        if not image_url or not image_url.startswith("/api/images/"):
            log_fail("Nano provider routing", f"Invalid image URL: {image_url}")
            return False
        
        log_pass("Nano provider routing", f"Nano provider still works: {image_url}")
        return True
        
    except Exception as e:
        log_fail("Nano provider routing", f"Exception: {str(e)}")
        return False

def print_summary():
    """Print test summary"""
    print_section("TEST SUMMARY")
    
    total_tests = len(test_results["passed"]) + len(test_results["failed"])
    
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {len(test_results['passed'])}")
    print(f"❌ Failed: {len(test_results['failed'])}")
    
    if test_results["failed"]:
        print("\n" + "="*80)
        print("FAILED TESTS:")
        print("="*80)
        for failure in test_results["failed"]:
            print(f"  ❌ {failure['test']}")
            if failure['details']:
                print(f"     {failure['details']}")
    
    print("\n" + "="*80)
    if len(test_results["failed"]) == 0:
        print("🎉 ALL TESTS PASSED!")
    else:
        print(f"⚠️  {len(test_results['failed'])} TEST(S) FAILED")
    print("="*80 + "\n")
    
    # Print detailed results for reporting
    print("\n" + "="*80)
    print("DETAILED TEST RESULTS:")
    print("="*80)
    for detail in test_results["details"]:
        status_icon = "✅" if detail["status"] == "PASS" else "❌"
        print(f"{status_icon} {detail['test']}")
        if detail['details']:
            print(f"   {detail['details']}")
    print("="*80 + "\n")

def main():
    """Run all tests in order"""
    print("\n" + "="*80)
    print("  DIALOGUE PARSING & OPENAI IMAGE GENERATION TESTS")
    print(f"  Base URL: {BASE_URL}")
    print("="*80)
    
    # Run tests in order
    test_1_dialogue_parsing()
    test_2_openai_image_generation()
    
    # Optional test (only if time permits)
    # Commenting out for now as per review request
    # test_3_nano_provider_routing()
    
    # Print summary
    print_summary()
    
    # Return exit code
    return 0 if len(test_results["failed"]) == 0 else 1

if __name__ == "__main__":
    exit(main())
