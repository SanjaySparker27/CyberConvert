# CyberConvert 🚀

A modern, privacy-focused 3D model converter with built-in preview capabilities. Convert between 20+ 3D formats locally without uploading files to any server.

![CyberConvert Banner](https://raw.githubusercontent.com/SanjaySparker27/CyberConvert/main/docs/banner.png)

## ✨ Features

- **🔒 100% Private** - All processing happens locally on your machine. Your files never leave your computer.
- **⚡ Fast Conversion** - Direct conversion without internet latency. Optimized algorithms for quick processing.
- **👁️ Built-in 3D Viewer** - Preview your models before and after conversion with our integrated WebGL viewer powered by Three.js.
- **📱 Responsive Design** - Works seamlessly on desktop, tablet, and mobile devices.
- **🌐 Offline Capable** - Once loaded, the app works without internet connection.
- **🎨 Modern UI** - Clean, cyberpunk-inspired interface with dark mode.

## 🎯 Supported Formats

### Mesh Formats
| Format | Read | Write |
|--------|------|-------|
| STL    | ✅   | ✅    |
| OBJ    | ✅   | ✅    |
| PLY    | ✅   | ✅    |
| OFF    | ✅   | ✅    |
| 3MF    | ✅   | ✅    |

### Scene Formats
| Format | Read | Write |
|--------|------|-------|
| glTF   | ✅   | ✅    |
| GLB    | ✅   | ✅    |
| FBX    | ✅   | ⚠️    |
| DAE    | ✅   | ⚠️    |
| 3DS    | ✅   | ⚠️    |

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/SanjaySparker27/CyberConvert.git
cd CyberConvert

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

### Usage

1. Open your browser and navigate to `http://localhost:5000`
2. Drag and drop your 3D file or click to browse
3. Preview your model in the 3D viewer
4. Select your desired output format
5. Click "Convert File"
6. Download your converted file!

## 🏗️ Architecture

```
CyberConvert/
├── frontend/          # Frontend HTML/CSS/JS
│   └── index.html     # Main application interface
├── converter3d/       # Backend conversion engine
│   ├── converter.py   # Core conversion logic
│   ├── format_registry.py
│   └── batch.py       # Batch processing
├── tests/             # Test suite
│   └── test_ui.py
├── app.py             # Flask web server
├── main.py            # CLI entry point
├── requirements.txt   # Python dependencies
├── README.md          # This file
└── LICENSE            # MIT License
```

## 🧪 Testing

Run the test suite:

```bash
python -m pytest tests/
```

Or use the included test runner:

```bash
python tests/test_ui.py
```

## 🛠️ Development

### Frontend Development
The frontend is built with vanilla HTML, CSS, and JavaScript:
- **Tailwind CSS** - Utility-first CSS framework
- **Three.js** - 3D graphics library
- **Modern ES6+** JavaScript

### Backend Development
The backend uses Flask with the following structure:
```python
# Key endpoints
GET  /api/status         # Check API status
GET  /api/formats        # List supported formats
POST /api/upload         # Upload file for conversion
POST /api/convert        # Convert file to new format
GET  /api/download/:id   # Download converted file
```

### Adding New Formats

To add a new format converter, modify `converter3d/converter.py`:

```python
def convert_to_newformat(self, mesh, filepath):
    # Implementation
    pass
```

## 📝 API Documentation

### Status Endpoint
```http
GET /api/status
```

Response:
```json
{
  "status": "online",
  "version": "1.0.0",
  "supported_formats": {...}
}
```

### Convert Endpoint
```http
POST /api/convert
Content-Type: multipart/form-data
```

Parameters:
- `file`: The 3D file to convert
- `output_format`: Target format (e.g., "stl", "obj")

Response:
```json
{
  "success": true,
  "download_url": "/api/download/converted.stl",
  "output_filename": "converted.stl",
  "vertices": 1234,
  "faces": 567
}
```

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run linting
flake8 .

# Run tests
pytest tests/ -v

# Run with hot reload
FLASK_DEBUG=1 python app.py
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Three.js](https://threejs.org/) - 3D library
- [Tailwind CSS](https://tailwindcss.com/) - CSS framework
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [Trimesh](https://trimsh.org/) - Mesh processing

## 🔗 Links

- 🌐 **Live Demo**: https://cyberconvert-demo.herokuapp.com
- 📖 **Documentation**: https://github.com/SanjaySparker27/CyberConvert/wiki
- 🐛 **Issue Tracker**: https://github.com/SanjaySparker27/CyberConvert/issues
- 💬 **Discussions**: https://github.com/SanjaySparker27/CyberConvert/discussions

## 👨‍💻 Author

**Sanjay Aradya** - [@SanjaySparker27](https://github.com/SanjaySparker27)

[![GitHub](https://img.shields.io/badge/GitHub-SanjaySparker27-181717?style=flat&logo=github)](https://github.com/SanjaySparker27)

---

Made with ❤️ by [Sanjay Aradya](https://github.com/SanjaySparker27)

Star ⭐ this repo if you find it helpful!
