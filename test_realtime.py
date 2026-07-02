"""
Quick test for real-time system
"""
import asyncio
import json
import base64
import numpy as np

async def test_websocket():
    """Test WebSocket connection and audio processing"""
    import websockets
    
    print("Testing WebSocket connection...")
    
    try:
        async with websockets.connect("ws://localhost:8000/ws") as websocket:
            print("✓ Connected to WebSocket")
            
            # Send session start
            await websocket.send(json.dumps({
                "type": "session_start",
                "session_id": "test_session"
            }))
            
            response = await websocket.recv()
            data = json.loads(response)
            print(f"✓ Session started: {data}")
            
            # Create test audio (2 seconds of silence)
            sample_rate = 16000
            duration = 2
            audio = np.zeros(sample_rate * duration, dtype=np.float32)
            
            # Convert to int16 PCM
            audio_int16 = (audio * 32768).astype(np.int16)
            audio_bytes = audio_int16.tobytes()
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
            
            # Send audio chunk
            print("Sending test audio chunk...")
            await websocket.send(json.dumps({
                "type": "audio",
                "audio_data": audio_b64,
                "session_id": "test_session"
            }))
            
            print("✓ Audio sent successfully")
            
            # Wait for response (with timeout)
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                data = json.loads(response)
                print(f"✓ Received response: {data.get('type')}")
                
                if data.get('type') == 'transcription':
                    print(f"  Transcript: {data.get('text', 'N/A')}")
                    print(f"  Analysis: {data.get('analysis', {}).get('lead_qualification', {})}")
                
            except asyncio.TimeoutError:
                print("⚠ No response received (this is normal for silence)")
            
            # Send session stop
            await websocket.send(json.dumps({
                "type": "session_stop",
                "session_id": "test_session"
            }))
            
            print("\n✅ WebSocket test completed successfully!")
            return True
            
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("="*60)
    print("Real-Time System Quick Test")
    print("="*60)
    print("\nMake sure the server is running:")
    print("  python server.py")
    print("\nPress Enter to continue...")
    input()
    
    success = await test_websocket()
    
    if success:
        print("\n✅ System is working correctly!")
    else:
        print("\n❌ System test failed. Check the errors above.")

if __name__ == "__main__":
    asyncio.run(main())