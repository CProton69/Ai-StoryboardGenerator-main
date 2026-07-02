#!/usr/bin/env python3
"""
Test ONLY the newly added image upload endpoint
"""
import requests
import io
from PIL import Image

BASE_URL = "https://visual-narrative-lab.preview.emergentagent.com/api"

def create_test_image(format='PNG', size=(100, 100), color=(255, 0, 0)):
    """Create a small test image in memory"""
    img = Image.new('RGB', size, color)
    buf = io.BytesIO()
    img.save(buf, format=format)
    buf.seek(0)
    return buf

def test_1_upload_png():
    """Test 1: POST /api/upload-image with PNG"""
    print("\n" + "="*80)
    print("TEST 1: POST /api/upload-image with PNG")
    print("="*80)
    
    try:
        # Create a small PNG image
        png_data = create_test_image(format='PNG', size=(50, 50), color=(0, 255, 0))
        
        files = {
            'file': ('test_image.png', png_data, 'image/png')
        }
        
        response = requests.post(f"{BASE_URL}/upload-image", files=files, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ FAIL: Expected 200, got {response.status_code}")
            print(f"   Response: {response.text}")
            return None
        
        data = response.json()
        
        if "image" not in data:
            print(f"❌ FAIL: No 'image' field in response")
            print(f"   Response: {data}")
            return None
        
        image_path = data["image"]
        
        if not image_path.startswith("/api/images/up-"):
            print(f"❌ FAIL: Image path doesn't start with /api/images/up-")
            print(f"   Got: {image_path}")
            return None
        
        if not image_path.endswith(".png"):
            print(f"❌ FAIL: Image path doesn't end with .png")
            print(f"   Got: {image_path}")
            return None
        
        print(f"✅ PASS: PNG uploaded successfully")
        print(f"   Image path: {image_path}")
        return image_path
        
    except Exception as e:
        print(f"❌ FAIL: Exception: {str(e)}")
        return None

def test_2_get_uploaded_png(image_path):
    """Test 2: GET the uploaded PNG image"""
    print("\n" + "="*80)
    print("TEST 2: GET uploaded PNG image")
    print("="*80)
    
    if not image_path:
        print("❌ SKIP: No image path from previous test")
        return False
    
    try:
        # Construct full URL
        full_url = f"{BASE_URL.replace('/api', '')}{image_path}"
        
        response = requests.get(full_url, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ FAIL: Expected 200, got {response.status_code}")
            return False
        
        content_type = response.headers.get("content-type", "")
        
        if "image/png" not in content_type and "image/" not in content_type:
            print(f"❌ FAIL: Expected image/png or image/*, got {content_type}")
            return False
        
        if len(response.content) == 0:
            print(f"❌ FAIL: Empty image content")
            return False
        
        print(f"✅ PASS: PNG image retrieved successfully")
        print(f"   Content-Type: {content_type}")
        print(f"   Size: {len(response.content)} bytes")
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Exception: {str(e)}")
        return False

def test_3_upload_jpg():
    """Test 3: POST /api/upload-image with JPG"""
    print("\n" + "="*80)
    print("TEST 3: POST /api/upload-image with JPG")
    print("="*80)
    
    try:
        # Create a small JPEG image
        jpg_data = create_test_image(format='JPEG', size=(50, 50), color=(0, 0, 255))
        
        files = {
            'file': ('test_image.jpg', jpg_data, 'image/jpeg')
        }
        
        response = requests.post(f"{BASE_URL}/upload-image", files=files, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ FAIL: Expected 200, got {response.status_code}")
            print(f"   Response: {response.text}")
            return None
        
        data = response.json()
        
        if "image" not in data:
            print(f"❌ FAIL: No 'image' field in response")
            return None
        
        image_path = data["image"]
        
        if not image_path.endswith(".jpg") and not image_path.endswith(".jpeg"):
            print(f"❌ FAIL: Image path doesn't end with .jpg or .jpeg")
            print(f"   Got: {image_path}")
            return None
        
        print(f"✅ PASS: JPG uploaded successfully")
        print(f"   Image path: {image_path}")
        
        # Also test GET for JPG
        full_url = f"{BASE_URL.replace('/api', '')}{image_path}"
        get_response = requests.get(full_url, timeout=30)
        
        if get_response.status_code != 200:
            print(f"❌ FAIL: GET request failed with {get_response.status_code}")
            return None
        
        content_type = get_response.headers.get("content-type", "")
        
        if "image/jpeg" not in content_type and "image/" not in content_type:
            print(f"⚠️  WARNING: Expected image/jpeg, got {content_type}")
        else:
            print(f"✅ PASS: JPG image retrieved with correct content-type: {content_type}")
        
        return image_path
        
    except Exception as e:
        print(f"❌ FAIL: Exception: {str(e)}")
        return None

def test_4_upload_unsupported():
    """Test 4: POST /api/upload-image with unsupported file type (.txt)"""
    print("\n" + "="*80)
    print("TEST 4: POST /api/upload-image with unsupported file type (.txt)")
    print("="*80)
    
    try:
        # Create a text file
        txt_data = io.BytesIO(b"This is a text file, not an image")
        
        files = {
            'file': ('test_file.txt', txt_data, 'text/plain')
        }
        
        response = requests.post(f"{BASE_URL}/upload-image", files=files, timeout=30)
        
        if response.status_code != 400:
            print(f"❌ FAIL: Expected 400, got {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        data = response.json()
        error_msg = data.get("detail", "")
        
        if "unsupported" not in error_msg.lower() and "image type" not in error_msg.lower():
            print(f"⚠️  WARNING: Error message may not be clear: {error_msg}")
        
        print(f"✅ PASS: Unsupported file type correctly rejected with 400")
        print(f"   Error message: {error_msg}")
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Exception: {str(e)}")
        return False

def test_5_scene_update_with_frameimage(uploaded_image_path):
    """Test 5: Verify entity update works with frameImage for scenes"""
    print("\n" + "="*80)
    print("TEST 5: Update scene with frameImage field")
    print("="*80)
    
    if not uploaded_image_path:
        print("❌ SKIP: No uploaded image path from previous test")
        return False
    
    try:
        # First, create a sample project
        response = requests.post(f"{BASE_URL}/seed-sample", timeout=30)
        
        if response.status_code != 200:
            print(f"❌ FAIL: Could not create sample project: {response.status_code}")
            return False
        
        project = response.json()
        project_id = project["id"]
        scenes = project.get("scenes", [])
        
        if not scenes:
            print(f"❌ FAIL: No scenes in sample project")
            return False
        
        first_scene_id = scenes[0]["id"]
        
        print(f"   Project ID: {project_id}")
        print(f"   First scene ID: {first_scene_id}")
        
        # Update the scene with the uploaded image
        update_payload = {
            "frameImage": uploaded_image_path
        }
        
        response = requests.put(
            f"{BASE_URL}/projects/{project_id}/scenes/{first_scene_id}",
            json=update_payload,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ FAIL: Scene update failed with {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        updated_project = response.json()
        updated_scenes = updated_project.get("scenes", [])
        updated_scene = next((s for s in updated_scenes if s["id"] == first_scene_id), None)
        
        if not updated_scene:
            print(f"❌ FAIL: Scene not found after update")
            return False
        
        if updated_scene.get("frameImage") != uploaded_image_path:
            print(f"❌ FAIL: frameImage not updated correctly")
            print(f"   Expected: {uploaded_image_path}")
            print(f"   Got: {updated_scene.get('frameImage')}")
            return False
        
        print(f"✅ PASS: Scene frameImage updated successfully")
        print(f"   Scene ID: {first_scene_id}")
        print(f"   frameImage: {updated_scene.get('frameImage')}")
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Exception: {str(e)}")
        return False

def main():
    """Run all image upload tests"""
    print("\n" + "="*80)
    print("  IMAGE UPLOAD ENDPOINT TESTS")
    print(f"  Base URL: {BASE_URL}")
    print("="*80)
    
    results = {
        "passed": 0,
        "failed": 0
    }
    
    # Test 1: Upload PNG
    png_path = test_1_upload_png()
    if png_path:
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    # Test 2: GET uploaded PNG
    if test_2_get_uploaded_png(png_path):
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    # Test 3: Upload JPG
    jpg_path = test_3_upload_jpg()
    if jpg_path:
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    # Test 4: Upload unsupported file
    if test_4_upload_unsupported():
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    # Test 5: Scene update with frameImage
    if test_5_scene_update_with_frameimage(png_path):
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    # Print summary
    print("\n" + "="*80)
    print("  TEST SUMMARY")
    print("="*80)
    print(f"Total Tests: {results['passed'] + results['failed']}")
    print(f"✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['failed']}")
    print("="*80 + "\n")
    
    return 0 if results["failed"] == 0 else 1

if __name__ == "__main__":
    exit(main())
