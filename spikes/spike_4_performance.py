#!/usr/bin/env python3
"""
Spike 4: Performance Comparison
Goal: Compare Python vs Rust startup/execution time

Run: python spike_4_performance.py
Prerequisites: pip install ollama

This spike measures:
1. Python import time (cold start)
2. Ollama library initialization
3. Simple chat completion time
4. Comparison with Rust binary (if available)
"""

import sys
import time
import subprocess
from pathlib import Path


def measure_python_import():
    """Measure time to import ollama module."""
    cmd = [sys.executable, '-c', 'import time; start=time.time(); import ollama; print(f"{(time.time()-start)*1000:.0f}")']
    result = subprocess.run(cmd, capture_output=True, text=True)
    return int(result.stdout.strip()) if result.returncode == 0 else -1


def measure_python_startup():
    """Measure cold start of a minimal Python script."""
    script = '''
import time
start = time.time()
import ollama
loaded = time.time()
# Minimal operation - just check client exists
_ = ollama.Client()
ready = time.time()
print(f"import:{(loaded-start)*1000:.0f},ready:{(ready-start)*1000:.0f}")
'''
    cmd = [sys.executable, '-c', script]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        parts = result.stdout.strip().split(',')
        import_ms = int(parts[0].split(':')[1])
        ready_ms = int(parts[1].split(':')[1])
        return import_ms, ready_ms
    return -1, -1


def measure_simple_chat():
    """Measure time for a simple chat completion."""
    import ollama
    
    # Find an available model (prefer smaller/faster ones for benchmarking)
    models_to_try = ['llama3.2:1b', 'llama3.2:latest', 'qwen3:latest']
    model = None
    
    for m in models_to_try:
        try:
            ollama.show(m)
            model = m
            break
        except Exception:
            continue
    
    if not model:
        return -1, None
    
    start = time.time()
    response = ollama.chat(
        model=model,
        messages=[{'role': 'user', 'content': 'Say "hello" and nothing else.'}]
    )
    duration = (time.time() - start) * 1000
    return duration, model


def measure_rust_binary():
    """Measure Rust binary startup (dry-run mode)."""
    # Try to find local-brain binary
    binary_paths = [
        'target/release/local-brain',
        'target/debug/local-brain',
        Path.home() / '.local/bin/local-brain',
        '/usr/local/bin/local-brain'
    ]
    
    binary = None
    for p in binary_paths:
        p = Path(p)
        if p.exists():
            binary = p
            break
    
    if not binary:
        return -1, "Binary not found"
    
    # Measure dry-run startup
    start = time.time()
    result = subprocess.run(
        [str(binary), '--dry-run', '--files', 'Cargo.toml'],
        capture_output=True,
        text=True
    )
    duration = (time.time() - start) * 1000
    
    if result.returncode == 0:
        return duration, str(binary)
    return -1, f"Error: {result.stderr}"


def main():
    print("=" * 60)
    print("SPIKE 4: Performance Comparison")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Python import time
    print("\n📊 Test 1: Python import time (ollama module)")
    print("-" * 40)
    
    import_times = []
    for i in range(3):
        ms = measure_python_import()
        import_times.append(ms)
        print(f"   Run {i+1}: {ms}ms")
    
    avg_import = sum(import_times) / len(import_times) if all(t > 0 for t in import_times) else -1
    results['python_import'] = avg_import
    print(f"   Average: {avg_import:.0f}ms")
    
    # Test 2: Python startup (import + init)
    print("\n📊 Test 2: Python cold start")
    print("-" * 40)
    
    startup_times = []
    for i in range(3):
        import_ms, ready_ms = measure_python_startup()
        startup_times.append(ready_ms)
        print(f"   Run {i+1}: import={import_ms}ms, ready={ready_ms}ms")
    
    avg_startup = sum(startup_times) / len(startup_times) if all(t > 0 for t in startup_times) else -1
    results['python_startup'] = avg_startup
    print(f"   Average startup: {avg_startup:.0f}ms")
    
    # Test 3: Simple chat completion
    print("\n📊 Test 3: Simple chat completion")
    print("-" * 40)
    
    chat_times = []
    model_used = None
    for i in range(3):
        ms, model = measure_simple_chat()
        if ms > 0:
            chat_times.append(ms)
            model_used = model
            print(f"   Run {i+1}: {ms:.0f}ms (model: {model})")
        else:
            print(f"   Run {i+1}: Failed")
    
    avg_chat = sum(chat_times) / len(chat_times) if chat_times else -1
    results['python_chat'] = avg_chat
    results['model'] = model_used
    print(f"   Average: {avg_chat:.0f}ms")
    
    # Test 4: Rust binary comparison
    print("\n📊 Test 4: Rust binary (dry-run)")
    print("-" * 40)
    
    rust_times = []
    rust_path = None
    for i in range(3):
        ms, info = measure_rust_binary()
        if ms > 0:
            rust_times.append(ms)
            rust_path = info
            print(f"   Run {i+1}: {ms:.0f}ms")
        else:
            print(f"   Run {i+1}: {info}")
    
    avg_rust = sum(rust_times) / len(rust_times) if rust_times else -1
    results['rust_dryrun'] = avg_rust
    if rust_path:
        print(f"   Binary: {rust_path}")
        print(f"   Average: {avg_rust:.0f}ms")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    print(f"\n📈 Python Performance:")
    print(f"   Import time:    {results['python_import']:.0f}ms")
    print(f"   Cold start:     {results['python_startup']:.0f}ms")
    print(f"   Chat completion: {results['python_chat']:.0f}ms (with {results.get('model', 'unknown')})")
    
    if results['rust_dryrun'] > 0:
        print(f"\n📈 Rust Performance:")
        print(f"   Dry-run startup: {results['rust_dryrun']:.0f}ms")
        
        print(f"\n📊 Comparison:")
        startup_diff = results['python_startup'] - results['rust_dryrun']
        print(f"   Python startup vs Rust: +{startup_diff:.0f}ms ({results['python_startup']/results['rust_dryrun']:.1f}x)")
    
    # Evaluation
    print("\n" + "=" * 60)
    print("EVALUATION")
    print("=" * 60)
    
    startup_ok = results['python_startup'] < 1000  # < 1 second
    chat_reasonable = results['python_chat'] < 30000  # < 30 seconds
    
    if startup_ok:
        print(f"✅ Python startup < 1s ({results['python_startup']:.0f}ms)")
    else:
        print(f"❌ Python startup >= 1s ({results['python_startup']:.0f}ms)")
    
    if chat_reasonable:
        print(f"✅ Chat completion reasonable ({results['python_chat']:.0f}ms)")
    else:
        print(f"⚠️  Chat completion slow ({results['python_chat']:.0f}ms)")
    
    if startup_ok:
        print("\n✅ SPIKE SUCCESS: Performance is acceptable for CLI use")
        return 0
    else:
        print("\n⚠️  SPIKE WARNING: Python startup may feel slow, but still usable")
        return 0


if __name__ == "__main__":
    sys.exit(main())

