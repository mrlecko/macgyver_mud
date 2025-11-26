import sys
import os
import time
import subprocess
import random

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from environments.labyrinth import LabyrinthEnvironment

def get_memory_usage():
    # Native Linux memory check (RSS in MB)
    try:
        pid = os.getpid()
        output = subprocess.check_output(['ps', '-p', str(pid), '-o', 'rss='])
        return int(output.strip()) / 1024  # KB -> MB
    except Exception:
        return 0.0

def run_stress_test(steps=10000):
    print(f"Starting Long-Run Stress Test ({steps} steps)...")
    
    env = LabyrinthEnvironment(mode='infinite', max_steps=steps)
    state = env.reset()
    
    start_time = time.time()
    start_mem = get_memory_usage()
    
    print(f"Initial Memory: {start_mem:.2f} MB")
    
    for i in range(steps):
        action = random.choice(['move', 'scan', 'rest'])
        state, reward, done, info = env.step(action)
        
        if i % 1000 == 0:
            current_mem = get_memory_usage()
            print(f"Step {i}: Entropy={state['entropy']:.2f}, Stress={state['stress']:.2f}, Mem={current_mem:.2f} MB")
            
        if done:
            print(f"Environment terminated early at step {i}")
            break
            
    end_time = time.time()
    end_mem = get_memory_usage()
    
    print("-" * 40)
    print(f"Test Complete in {end_time - start_time:.2f} seconds")
    print(f"Final Memory: {end_mem:.2f} MB (Delta: {end_mem - start_mem:.2f} MB)")
    print("-" * 40)
    
    if end_mem - start_mem > 50: # Fail if leaks > 50MB
        print("FAILURE: Significant memory leak detected!")
        sys.exit(1)
    else:
        print("SUCCESS: Memory usage stable.")
        sys.exit(0)

if __name__ == "__main__":
    run_stress_test()
