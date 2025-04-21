import requests

try:
    response = requests.get('http://127.0.0.1:5000/')
    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        print("Server is running and accessible!")
    else:
        print(f"Server returned status: {response.status_code}")
        print(response.text[:200])  # Print first 200 chars of response
except Exception as e:
    print(f"Error connecting to server: {str(e)}") 