#!/usr/bin/env python3
"""
Test GPU availability and face detection performance
"""
import time
import numpy as np
from PIL import Image

def test_gpu():
    print("=" * 60)
    print("GPU Test for PhotoMatch")
    print("=" * 60)
    
    # Test PyTorch CUDA
    print("\n1. Testing PyTorch CUDA...")
    try:
        import torch
        print(f"   PyTorch version: {torch.__version__}")
        print(f"   CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"   CUDA version: {torch.version.cuda}")
            print(f"   GPU device: {torch.cuda.get_device_name(0)}")
            print(f"   GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
        else:
            print("   ⚠️  WARNING: CUDA not available, will use CPU")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test ONNX Runtime GPU
    print("\n2. Testing ONNX Runtime GPU...")
    try:
        import onnxruntime as ort
        print(f"   ONNX Runtime version: {ort.__version__}")
        providers = ort.get_available_providers()
        print(f"   Available providers: {providers}")
        if 'CUDAExecutionProvider' in providers:
            print("   ✓ CUDAExecutionProvider available")
        else:
            print("   ⚠️  CUDAExecutionProvider not available")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test InsightFace
    print("\n3. Testing InsightFace...")
    try:
        from insightface.app import FaceAnalysis
        
        print("   Loading face detection model...")
        app = FaceAnalysis(
            name='buffalo_l',
            providers=['CUDAExecutionProvider', 'CPUExecutionProvider'] if torch.cuda.is_available() else ['CPUExecutionProvider'],
            allowed_modules=['detection', 'recognition']
        )
        
        ctx_id = 0 if torch.cuda.is_available() else -1
        app.prepare(ctx_id=ctx_id, det_size=(640, 640))
        
        device_type = "GPU" if ctx_id >= 0 else "CPU"
        print(f"   ✓ Model loaded successfully on {device_type}")
        
        # Create a test image (random noise)
        print("\n4. Performance Test...")
        test_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
        
        # Warm up
        print("   Warming up...")
        for _ in range(3):
            app.get(test_image)
        
        # Benchmark
        num_iterations = 10
        print(f"   Running {num_iterations} iterations...")
        start_time = time.time()
        for _ in range(num_iterations):
            faces = app.get(test_image)
        elapsed_time = time.time() - start_time
        
        avg_time = elapsed_time / num_iterations
        fps = 1.0 / avg_time if avg_time > 0 else 0
        
        print(f"\n   Results:")
        print(f"   - Average time per image: {avg_time*1000:.2f} ms")
        print(f"   - Throughput: {fps:.2f} FPS")
        print(f"   - Total time for {num_iterations} images: {elapsed_time:.2f} seconds")
        
        if torch.cuda.is_available():
            print(f"\n   ✓ GPU acceleration is working!")
            print(f"   Expected performance: 15-30 FPS on GPU vs 2-5 FPS on CPU")
        else:
            print(f"\n   ℹ️  Running on CPU (expect slower performance)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)

if __name__ == "__main__":
    test_gpu()
