import urllib.request, json, urllib.error
req = urllib.request.Request('http://localhost:8000/auth/register', data=json.dumps({'username': 'testuser2', 'email': 'test2@example.com', 'password': 'password123'}).encode('utf-8'), headers={'Content-Type': 'application/json'})
try:
  print(urllib.request.urlopen(req).read().decode('utf-8'))
except urllib.error.HTTPError as e:
  print("ERROR:")
  print(e.read().decode('utf-8'))
