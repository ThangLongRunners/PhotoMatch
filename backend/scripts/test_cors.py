import requests

# Test API endpoint
print("Testing API endpoint CORS...")
response = requests.get("http://localhost:8000/health")
print(f"Status: {response.status_code}")
print("Headers:")
for key, value in response.headers.items():
    if 'access-control' in key.lower() or 'cors' in key.lower():
        print(f"  {key}: {value}")

print("\n" + "="*60)

# Test static file endpoint
print("Testing static file CORS...")
test_url = "http://localhost:8000/static/uploads/c0bf9053-ed29-4db8-931e-6fe0c847e1be_Oidoioi%20Multimedia%20(151).JPG"
try:
    response = requests.get(test_url, timeout=5)
    print(f"Status: {response.status_code}")
    print("Headers:")
    for key, value in response.headers.items():
        if 'access-control' in key.lower() or 'cors' in key.lower():
            print(f"  {key}: {value}")
    if not any('access-control' in k.lower() for k in response.headers.keys()):
        print("  ⚠️  NO CORS HEADERS FOUND!")
except Exception as e:
    print(f"Error: {e}")
