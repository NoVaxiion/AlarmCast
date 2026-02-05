from listener import FireAlarmListener
import time

def test_background_listening():
    print("--- STEP 1: Initializing Listener ---")
    # This loads the model (might take a second)
    alarm_listener = FireAlarmListener(model_path='model/model.pt')
    
    print("\n--- STEP 2: Starting Background Thread ---")
    # This should return immediately and not block
    alarm_listener.start_listening()
    print("Listener started.")

    print("\n--- STEP 3: Simulating Main Program Work ---")
    print("This will count to 60 while the listener tries to detect for fire alarms.")

    try:
        for i in range(1, 61):
            print(f"Main Program: Working... {i}%")
            # Sleep creates a gap where the background thread can print its detection
            time.sleep(1) 
            
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")

if __name__ == "__main__":
    test_background_listening()