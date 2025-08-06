INSTANCES = 8
base_port = 8090

print("8Knot Multi-Instance Port Mapping (localhost -> container):\n")
for i in range(1, INSTANCES + 1):
    print(f"Instance {i}:")
    print(f"  Web UI:       http://localhost:{base_port + i} -> instance{i}:8080")
    print()
