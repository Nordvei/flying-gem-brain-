# Contributing to Flying GEM Brain

Thank you for your interest in contributing! We welcome contributions from the defense tech and autonomous systems community.

## How to Contribute

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/flying-gem-brain.git
cd flying-gem-brain
```

### 2. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 3. Make Your Changes

- Follow the existing code style
- Add tests for new features
- Update documentation as needed
- Keep commits focused and descriptive

### 4. Test Your Changes

```bash
# Run tests
pytest

# Run simulation (if applicable)
python simulation/swarm_sim.py
```

### 5. Submit a Pull Request

- Push your branch to your fork
- Open a Pull Request against `main`
- Describe your changes clearly
- Reference any related issues

## Areas for Contribution

### High Priority

- **MAVLink Integration** - Improve Pixhawk communication
- **Hailo AI Optimization** - YOLOv8n performance tuning
- **Simulation** - Swarm behavior simulation
- **Documentation** - Setup guides, tutorials

### Medium Priority

- **Additional Sensors** - Thermal, LiDAR integration
- **Formation Control** - Advanced swarm patterns
- **Object Tracking** - Multi-frame object persistence
- **Mesh Resilience** - Network partition handling

### Nice to Have

- **Web UI** - Browser-based operator interface
- **Log Analysis** - Post-flight telemetry analysis
- **3D Visualization** - Real-time swarm visualization
- **Hardware Guides** - Assembly and setup tutorials

## Code Style

### Python

- Follow PEP 8
- Use type hints where appropriate
- Document functions with docstrings
- Keep functions focused (single responsibility)

Example:
```python
def detect_objects(frame: np.ndarray, confidence: float = 0.5) -> List[Detection]:
    """
    Detect objects in a camera frame using YOLOv8n.

    Args:
        frame: Input image (BGR format)
        confidence: Minimum detection confidence (0.0-1.0)

    Returns:
        List of Detection objects with bounding boxes and labels
    """
    # Implementation
    pass
```

### Commit Messages

Use conventional commits format:

```
feat: add thermal camera support
fix: resolve mesh reconnection issue
docs: update hardware setup guide
test: add edge node unit tests
```

## Testing

### Unit Tests

```bash
pytest tests/
```

### Integration Tests

```bash
pytest tests/integration/
```

### Hardware-in-Loop (if available)

```bash
# Requires physical drone setup
pytest tests/hardware/
```

## Documentation

- Update README.md if adding new features
- Add docstrings to all functions
- Create guides in `docs/` for new capabilities
- Include examples in code comments

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.

## Questions?

- Open an issue for discussion
- Email: info@infinity-folder.no
- Check existing issues and PRs first

## Code of Conduct

- Be respectful and professional
- Focus on technical merit
- Welcome newcomers
- Assume good intentions

---

**Thank you for helping make Flying GEM Brain better!**
