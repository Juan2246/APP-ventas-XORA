from app import app
import json

def test_api():
    try:
        with app.test_client() as client:
            response = client.get('/api/reports')
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                print("Response JSON:")
                print(json.dumps(response.json, indent=2))
            else:
                print("Error Response:")
                print(response.data.decode('utf-8'))
    except Exception as e:
        print(f"CRASH: {e}")

if __name__ == "__main__":
    test_api()
