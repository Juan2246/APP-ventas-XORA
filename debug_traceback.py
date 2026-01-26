from app import app
import traceback

def test_api():
    try:
        with app.test_client() as client:
            response = client.get('/api/reports')
            print(f"Status Code: {response.status_code}")
            if response.status_code != 200:
                print("FAILED. Running with context to capture traceback...")
                with app.app_context():
                    try:
                        # Manually trigger the function to bypass Flask's error handler hiding the trace
                        from app import api_reports
                        api_reports()
                    except Exception:
                        traceback.print_exc()
            else:
                print("Success")
    except Exception as e:
        print(f"CRASH: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_api()
