"""
Format registry and detection for all supported 3D file formats.
"""

import os
from enum import Enum
from typing import Dict, List, Optional, Tuple
import struct

class FormatCategory(Enum):
    MESH = "mesh"           # Polygon mesh formats (STL, OBJ, PLY, etc.)
    CAD = "cad"             # CAD formats (STEP, IGES, BREP, 3DM)
    BIM = "bim"             # Architecture/BIM formats (IFC, BIM)
    SCENE = "scene"         # Scene formats (GLTF, FBX, DAE, 3DS)
    FREECAD = "freecad"     # FreeCAD formats (FCStd)

class FormatInfo:
    def __init__(self, 
                 name: str, 
                 extensions: List[str],
                 category: FormatCategory,
                 can_read: bool = True,
                 can_write: bool = True,
                 description: str = ""):
        self.name = name
        self.extensions = [ext.lower() for ext in extensions]
        self.category = category
        self.can_read = can_read
        self.can_write = can_write
        self.description = description

# Registry of all supported formats
FORMAT_REGISTRY: Dict[str, FormatInfo] = {
    # Mesh formats
    "stl": FormatInfo("STL", [".stl"], FormatCategory.MESH, 
                      description="STereoLithography format"),
    "obj": FormatInfo("OBJ", [".obj"], FormatCategory.MESH,
                      description="Wavefront OBJ format"),
    "ply": FormatInfo("PLY", [".ply"], FormatCategory.MESH,
                      description="Polygon File Format (Stanford)"),
    "off": FormatInfo("OFF", [".off"], FormatCategory.MESH,
                      description="Object File Format"),
    
    # Scene formats
    "gltf": FormatInfo("glTF", [".gltf", ".glb"], FormatCategory.SCENE,
                       description="GL Transmission Format"),
    "dae": FormatInfo("COLLADA", [".dae"], FormatCategory.SCENE,
                      description="COLLADA Digital Asset Exchange"),
    "fbx": FormatInfo("FBX", [".fbx"], FormatCategory.SCENE,
                      description="Filmbox format (Autodesk)"),
    "3ds": FormatInfo("3DS", [".3ds"], FormatCategory.SCENE,
                      description="3D Studio format"),
    "wrl": FormatInfo("VRML", [".wrl", ".vrml"], FormatCategory.SCENE,
                      description="Virtual Reality Modeling Language"),
    
    # 3D printing formats
    "3mf": FormatInfo("3MF", [".3mf"], FormatCategory.MESH,
                      description="3D Manufacturing Format"),
    "amf": FormatInfo("AMF", [".amf"], FormatCategory.MESH,
                      description="Additive Manufacturing File Format"),
    
    # CAD formats
    "step": FormatInfo("STEP", [".step", ".stp"], FormatCategory.CAD,
                       description="Standard for the Exchange of Product data"),
    "iges": FormatInfo("IGES", [".iges", ".igs"], FormatCategory.CAD,
                       description="Initial Graphics Exchange Specification"),
    "brep": FormatInfo("BREP", [".brep"], FormatCategory.CAD,
                       description="Boundary Representation (OpenCASCADE)"),
    "3dm": FormatInfo("Rhino", [".3dm"], FormatCategory.CAD,
                      description="Rhinoceros 3D format"),
    
    # BIM formats
    "ifc": FormatInfo("IFC", [".ifc"], FormatCategory.BIM,
                      description="Industry Foundation Classes"),
    "bim": FormatInfo("BIM", [".bim"], FormatCategory.BIM,
                      description="Building Information Modeling"),
    
    # FreeCAD
    "fcstd": FormatInfo("FreeCAD", [".fcstd"], FormatCategory.FREECAD,
                        description="FreeCAD document format"),
}

class FormatDetector:
    """Detects file formats by extension and content."""
    
    @staticmethod
    def get_format_by_extension(filepath: str) -> Optional[str]:
        """Get format ID from file extension."""
        ext = os.path.splitext(filepath)[1].lower()
        for fmt_id, fmt_info in FORMAT_REGISTRY.items():
            if ext in fmt_info.extensions:
                return fmt_id
        return None
    
    @staticmethod
    def detect_by_content(filepath: str) -> Optional[str]:
        """Attempt to detect format by file content."""
        try:
            with open(filepath, 'rb') as f:
                header = f.read(4096)
            
            # Check for ASCII formats
            try:
                text_header = header.decode('utf-8', errors='ignore').upper()
                
                # STL (ASCII)
                if "SOLID" in text_header[:100]:
                    return "stl"
                
                # OBJ
                if any(prefix in text_header[:500] for prefix in ["V ", "VT ", "VN ", "F ", "# OBJ"]):
                    return "obj"
                
                # PLY
                if "PLY" in text_header[:10]:
                    return "ply"
                
                # OFF
                if text_header.startswith("OFF") or "N POINTS" in text_header[:100]:
                    return "off"
                
                # STEP
                if "ISO-10303-21" in text_header[:200]:
                    return "step"
                
                # IGES
                if text_header.startswith("S") and len(text_header) > 80 and "1H" in text_header[:80]:
                    return "iges"
                
                # VRML
                if "#VRML" in text_header[:100]:
                    return "wrl"
                
                # glTF (JSON)
                if text_header.strip().startswith("{") and '"asset"' in text_header[:500]:
                    return "gltf"
                
                # COLLADA
                if "<COLLADA" in text_header[:500]:
                    return "dae"
                
                # 3MF (ZIP based)
                if header[:4] == b'PK\x03\x04':
                    return "3mf"
                
                # AMF
                if "<AMF" in text_header[:500]:
                    return "amf"
                
                # IFC
                if "ISO-10303-21" in text_header[:200] and "IFC" in text_header[:500]:
                    return "ifc"
                
                # BREP
                if "CASCADE Topology V" in text_header[:200] or "DBRep_DrawableShape" in text_header:
                    return "brep"
                    
            except:
                pass
            
            # Binary format checks
            # Binary STL
            if len(header) >= 80 and struct.unpack('<I', header[80:84])[0] < 10000000:
                # Check if triangle count is reasonable
                return "stl"
            
            # FBX
            if b"Kaydara FBX Binary" in header[:100] or b"FBX" in header[:100]:
                return "fbx"
            
            # glTF Binary
            if header[:4] == b'glTF':
                return "gltf"
            
            # 3DS
            if struct.unpack('<H', header[:2])[0] == 0x4D4D:  # "MM" magic
                return "3ds"
            
            # 3DM (Rhino)
            if header[:4] in [b'3DM ' + bytes([i]) for i in range(256)]:
                return "3dm"
            
            # FreeCAD
            if header[:4] == b'FCStd':
                return "fcstd"
            
        except Exception as e:
            pass
        
        return None
    
    @staticmethod
    def detect(filepath: str) -> Tuple[Optional[str], str]:
        """
        Detect format of a file.
        Returns: (format_id, detection_method)
        """
        # Try extension first
        ext_fmt = FormatDetector.get_format_by_extension(filepath)
        if ext_fmt:
            return ext_fmt, "extension"
        
        # Try content detection
        content_fmt = FormatDetector.detect_by_content(filepath)
        if content_fmt:
            return content_fmt, "content"
        
        return None, "unknown"

def get_supported_formats() -> Dict[str, List[str]]:
    """Get lists of supported formats by category."""
    result = {
        "all_read": [],
        "all_write": [],
        "mesh": [],
        "cad": [],
        "bim": [],
        "scene": [],
    }
    
    for fmt_id, fmt_info in FORMAT_REGISTRY.items():
        if fmt_info.can_read:
            result["all_read"].append(fmt_id)
        if fmt_info.can_write:
            result["all_write"].append(fmt_id)
        
        cat_key = fmt_info.category.value
        if cat_key not in result:
            result[cat_key] = []
        result[cat_key].append(fmt_id)
    
    return result

def get_format_extensions(format_id: str) -> List[str]:
    """Get file extensions for a format."""
    fmt = FORMAT_REGISTRY.get(format_id.lower())
    return fmt.extensions if fmt else []

def format_exists(format_id: str) -> bool:
    """Check if a format is supported."""
    return format_id.lower() in FORMAT_REGISTRY