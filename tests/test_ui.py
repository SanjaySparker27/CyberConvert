"""UI Test Suite for CyberConvert 3D Model Converter"""
import unittest
import requests
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

class TestUIComponents(unittest.TestCase):
    def setUp(self):
        self.base_url = "http://localhost:5000"
        
    def test_page_loads(self):
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            self.assertEqual(response.status_code, 200)
            self.assertIn("CyberConvert", response.text)
        except requests.exceptions.ConnectionError:
            self.skipTest("Server not running")
    
    def test_html_structure(self):
        frontend_dir = Path(__file__).parent.parent / "frontend"
        html_content = (frontend_dir / "index.html").read_text()
        required_elements = [
            '<!DOCTYPE html>',
            '<meta name="viewport"',
            'id="upload-zone"',
            'id="file-input"',
            'id="viewer-canvas"',
            'id="convert-btn"',
        ]
        for element in required_elements:
            self.assertIn(element, html_content)

class TestAPIEndpoints(unittest.TestCase):
    def setUp(self):
        self.base_url = "http://localhost:5000"
        
    def test_status_endpoint(self):
        try:
            response = requests.get(f"{self.base_url}/api/status", timeout=5)
            self.assertEqual(response.status_code, 200)
        except requests.exceptions.ConnectionError:
            self.skipTest("Server not running")

if __name__ == '__main__':
    unittest.main()
