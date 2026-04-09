"""
Core conversion logic for 3D file formats.
Uses multiple libraries to achieve comprehensive format support.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
import numpy as np
import warnings

# Suppress library warnings
warnings.filterwarnings('ignore')

class ConversionError(Exception):
    """Raised when conversion fails."""
    pass

class Converter3D:
    """Main converter class handling all format conversions."""
    
    def __init__(self):
        self.temp_dir = None
        self._load_converters()
    
    def _load_converters(self):
        """Initialize converter modules."""
        self.mesh_available = False
        self.cad_available = False
        self.bim_available = False
        self.scene_available = False
        
        # Try to import mesh libraries
        try:
            import trimesh
            self.trimesh = trimesh
            self.mesh_available = True
        except ImportError:
            pass
        
        try:
            import meshio
            self.meshio = meshio
        except ImportError:
            pass
        
        # Try to import CAD libraries
        try:
            import cadquery as cq
            self.cadquery = cq
            self.cad_available = True
        except ImportError:
            pass
        
        try:
            import OCP
            self.ocp_available = True
        except ImportError:
            self.ocp_available = False
        
        try:
            import rhino3dm
            self.rhino3dm = rhino3dm
            self.rhino_available = True
        except ImportError:
            self.rhino_available = False
        
        # Try to import BIM libraries
        try:
            import ifcopenshell
            self.ifcopenshell = ifcopenshell
            self.bim_available = True
        except ImportError:
            pass
        
        # Try to import scene formats
        try:
            import pygltflib
            self.pygltflib = pygltflib
            self.gltf_available = True
        except ImportError:
            self.gltf_available = False
        
        try:
            import collada
            self.collada = collada
            self.dae_available = True
        except ImportError:
            self.dae_available = False
    
    def convert(self, 
                input_path: str, 
                output_path: str,
                input_format: Optional[str] = None,
                output_format: Optional[str] = None,
                **options) -> Dict[str, Any]:
        """
        Convert a 3D file from one format to another.
        
        Args:
            input_path: Path to input file
            output_path: Path to output file
            input_format: Override input format detection
            output_format: Override output format detection
            **options: Format-specific options
            
        Returns:
            Dictionary with conversion results
        """
        from .format_registry import FormatDetector, FORMAT_REGISTRY
        
        # Detect or use provided formats
        if input_format is None:
            input_format, detection_method = FormatDetector.detect(input_path)
            if input_format is None:
                raise ConversionError(f"Could not detect format for: {input_path}")
        else:
            detection_method = "provided"
        
        if output_format is None:
            output_format = FormatDetector.get_format_by_extension(output_path)
            if output_format is None:
                raise ConversionError(f"Could not detect output format from: {output_path}")
        
        input_format = input_format.lower()
        output_format = output_format.lower()
        
        # Validate formats
        if input_format not in FORMAT_REGISTRY:
            raise ConversionError(f"Unsupported input format: {input_format}")
        if output_format not in FORMAT_REGISTRY:
            raise ConversionError(f"Unsupported output format: {output_format}")
        
        # Check if same format (just copy)
        if input_format == output_format:
            shutil.copy2(input_path, output_path)
            return {
                "success": True,
                "input_format": input_format,
                "output_format": output_format,
                "method": "copy"
            }
        
        # Route to appropriate converter
        result = self._route_conversion(
            input_path, output_path,
            input_format, output_format,
            **options
        )
        
        result["input_format"] = input_format
        result["output_format"] = output_format
        result["input_detected_by"] = detection_method
        
        return result
    
    def _route_conversion(self, input_path: str, output_path: str,
                          input_fmt: str, output_fmt: str, **options) -> Dict[str, Any]:
        """Route conversion to appropriate handler."""
        
        # Define conversion strategies
        category_routes = {
            # Mesh to mesh - use trimesh
            ("mesh", "mesh"): self._convert_mesh_to_mesh,
            ("scene", "mesh"): self._convert_scene_to_mesh,
            ("mesh", "scene"): self._convert_mesh_to_scene,
            ("cad", "mesh"): self._convert_cad_to_mesh,
            ("cad", "cad"): self._convert_cad_to_cad,
            ("bim", "mesh"): self._convert_bim_to_mesh,
            ("scene", "scene"): self._convert_scene_to_scene,
        }
        
        from .format_registry import FORMAT_REGISTRY
        
        input_cat = FORMAT_REGISTRY[input_fmt].category.value
        output_cat = FORMAT_REGISTRY[output_fmt].category.value
        
        route_key = (input_cat, output_cat)
        
        if route_key in category_routes:
            return category_routes[route_key](input_path, output_path, input_fmt, output_fmt, **options)
        else:
            # Try mesh as intermediate format
            return self._convert_via_mesh(input_path, output_path, input_fmt, output_fmt, **options)
    
    def _convert_mesh_to_mesh(self, input_path: str, output_path: str,
                              input_fmt: str, output_fmt: str, **options) -> Dict[str, Any]:
        """Convert between mesh formats using trimesh."""
        if not self.mesh_available:
            raise ConversionError("trimesh library required for mesh conversion")
        
        try:
            # Load mesh
            mesh = self.trimesh.load(input_path, force='mesh')
            
            # Export to target format
            file_type = output_fmt
            if output_fmt == "gltf":
                file_type = "glb"  # trimesh uses glb for binary glTF
            
            mesh.export(output_path, file_type=file_type)
            
            return {
                "success": True,
                "vertices": len(mesh.vertices),
                "faces": len(mesh.faces),
                "method": "trimesh"
            }
        except Exception as e:
            raise ConversionError(f"Mesh conversion failed: {str(e)}")
    
    def _convert_scene_to_mesh(self, input_path: str, output_path: str,
                               input_fmt: str, output_fmt: str, **options) -> Dict[str, Any]:
        """Convert scene format to mesh."""
        if not self.mesh_available:
            raise ConversionError("trimesh required for scene conversion")
        
        try:
            # Load as scene, then extract mesh
            scene = self.trimesh.load(input_path)
            
            if isinstance(scene, self.trimesh.Scene):
                # Concatenate all meshes in scene
                meshes = []
                for geom in scene.geometry.values():
                    if isinstance(geom, self.trimesh.Trimesh):
                        meshes.append(geom)
                
                if meshes:
                    mesh = self.trimesh.util.concatenate(meshes)
                else:
                    raise ConversionError("No meshes found in scene")
            else:
                mesh = scene
            
            file_type = output_fmt
            if output_fmt == "gltf":
                file_type = "glb"
            
            mesh.export(output_path, file_type=file_type)
            
            return {
                "success": True,
                "vertices": len(mesh.vertices),
                "faces": len(mesh.faces),
                "method": "trimesh_scene"
            }
        except Exception as e:
            raise ConversionError(f"Scene to mesh conversion failed: {str(e)}")
    
    def _convert_mesh_to_scene(self, input_path: str, output_path: str,
                               input_fmt: str, output_fmt: str, **options) -> Dict[str, Any]:
        """Convert mesh to scene format."""
        # For now, treat as mesh to mesh
        return self._convert_mesh_to_mesh(input_path, output_path, input_fmt, output_fmt, **options)
    
    def _convert_cad_to_mesh(self, input_path: str, output_path: str,
                             input_fmt: str, output_fmt: str, **options) -> Dict[str, Any]:
        """Convert CAD formats to mesh."""
        
        # Try CADQuery first
        if self.cad_available and input_fmt in ["step", "stp", "iges", "igs"]:
            try:
                return self._convert_step_iges_to_mesh(input_path, output_path, output_fmt, **options)
            except Exception as e:
                pass
        
        # Try Rhino3dm for 3DM files
        if input_fmt == "3dm" and self.rhino_available:
            try:
                return self._convert_3dm_to_mesh(input_path, output_path, output_fmt, **options)
            except Exception as e:
                pass
        
        # Fallback: try trimesh (some formats supported)
        if self.mesh_available:
            try:
                mesh = self.trimesh.load(input_path)
                file_type = output_fmt if output_fmt != "gltf" else "glb"
                mesh.export(output_path, file_type=file_type)
                return {
                    "success": True,
                    "vertices": len(mesh.vertices),
                    "faces": len(mesh.faces),
                    "method": "trimesh_cad_fallback"
                }
            except Exception as e:
                raise ConversionError(f"CAD to mesh conversion failed: {str(e)}")
        
        raise ConversionError(f"No converter available for {input_fmt} to {output_fmt}")
    
    def _convert_step_iges_to_mesh(self, input_path: str, output_path: str,
                                   output_fmt: str, **options) -> Dict[str, Any]:
        """Convert STEP/IGES to mesh using CADQuery."""
        import cadquery as cq
        
        # Load CAD file
        if input_path.lower().endswith(('.step', '.stp')):
            shape = cq.importers.importStep(input_path)
        else:
            shape = cq.importers.importIges(input_path)
        
        # Tessellate to mesh
        tolerance = options.get('tolerance', 0.1)
        angular_tolerance = options.get('angular_tolerance', 0.1)
        
        mesh = shape.val().tessellate(tolerance)
        
        # Create trimesh object
        vertices = mesh[0]
        faces = mesh[1]
        
        tri_mesh = self.trimesh.Trimesh(vertices=vertices, faces=faces)
        
        # Export
        file_type = output_fmt if output_fmt != "gltf" else "glb"
        tri_mesh.export(output_path, file_type=file_type)
        
        return {
            "success": True,
            "vertices": len(vertices),
            "faces": len(faces),
            "method": "cadquery_tessellation"
        }
    
    def _convert_3dm_to_mesh(self, input_path: str, output_path: str,
                             output_fmt: str, **options) -> Dict[str, Any]:
        """Convert Rhino 3DM to mesh."""
        import rhino3dm
        
        model = rhino3dm.File3dm.Read(input_path)
        
        all_vertices = []
        all_faces = []
        vertex_offset = 0
        
        for obj in model.Objects:
            geometry = obj.Geometry
            
            # Convert different geometry types to mesh
            if isinstance(geometry, rhino3dm.Mesh):
                mesh = geometry
            elif isinstance(geometry, rhino3dm.Brep):
                mesh = geometry.GetMesh(rhino3dm.MeshType.Any)
            elif hasattr(geometry, 'GetMesh'):
                mesh = geometry.GetMesh(rhino3dm.MeshType.Any)
            else:
                continue
            
            if mesh:
                # Get vertices
                verts = [[v.X, v.Y, v.Z] for v in mesh.Vertices]
                all_vertices.extend(verts)
                
                # Get faces
                for i in range(mesh.Faces.Count):
                    face = mesh.Faces[i]
                    if face.IsTriangle:
                        all_faces.append([face.A + vertex_offset, 
                                         face.B + vertex_offset, 
                                         face.C + vertex_offset])
                    else:  # Quad
                        all_faces.append([face.A + vertex_offset, 
                                         face.B + vertex_offset, 
                                         face.C + vertex_offset])
                        all_faces.append([face.A + vertex_offset, 
                                         face.C + vertex_offset, 
                                         face.D + vertex_offset])
                
                vertex_offset += len(verts)
        
        if not all_vertices:
            raise ConversionError("No meshable geometry found in 3DM file")
        
        tri_mesh = self.trimesh.Trimesh(vertices=all_vertices, faces=all_faces)
        
        file_type = output_fmt if output_fmt != "gltf" else "glb"
        tri_mesh.export(output_path, file_type=file_type)
        
        return {
            "success": True,
            "vertices": len(all_vertices),
            "faces": len(all_faces),
            "method": "rhino3dm"
        }
    
    def _convert_cad_to_cad(self, input_path: str, output_path: str,
                            input_fmt: str, output_fmt: str, **options) -> Dict[str, Any]:
        """Convert between CAD formats."""
        # Often requires going through an intermediate representation
        # For now, use OpenCASCADE where possible
        
        if self.cad_available:
            try:
                return self._convert_cad_cad_cadquery(input_path, output_path, 
                                                       input_fmt, output_fmt, **options)
            except Exception as e:
                pass
        
        raise ConversionError(f"CAD to CAD conversion not yet supported for {input_fmt} -> {output_fmt}")
    
    def _convert_cad_cad_cadquery(self, input_path: str, output_path: str,
                                   input_fmt: str, output_fmt: str, **options) -> Dict[str, Any]:
        """Convert CAD using CADQuery."""
        import cadquery as cq
        
        # Import
        if input_fmt in ["step", "stp"]:
            shape = cq.importers.importStep(input_path)
        elif input_fmt in ["iges", "igs"]:
            shape = cq.importers.importIges(input_path)
        else:
            raise ConversionError(f"CADQuery cannot import {input_fmt}")
        
        # Export
        if output_fmt in ["step", "stp"]:
            cq.exporters.export(shape, output_path, exportType='STEP')
        elif output_fmt == "brep":
            cq.exporters.export(shape, output_path, exportType='BREP')
        elif output_fmt in ["stl", "obj", "ply"]:
            cq.exporters.export(shape, output_path)
        else:
            raise ConversionError(f"CADQuery cannot export to {output_fmt}")
        
        return {
            "success": True,
            "method": "cadquery"
        }
    
    def _convert_bim_to_mesh(self, input_path: str, output_path: str,
                             input_fmt: str, output_fmt: str, **options) -> Dict[str, Any]:
        """Convert BIM/IFC to mesh."""
        if not self.bim_available:
            raise ConversionError("ifcopenshell required for IFC conversion")
        
        if input_fmt == "ifc":
            return self._convert_ifc_to_mesh(input_path, output_path, output_fmt, **options)
        
        raise ConversionError(f"BIM conversion not supported for {input_fmt}")
    
    def _convert_ifc_to_mesh(self, input_path: str, output_path: str,
                             output_fmt: str, **options) -> Dict[str, Any]:
        """Convert IFC to mesh."""
        import ifcopenshell
        import ifcopenshell.geom
        
        ifc_file = ifcopenshell.open(input_path)
        
        settings = ifcopenshell.geom.settings()
        settings.set(settings.USE_WORLD_COORDS, True)
        
        all_vertices = []
        all_faces = []
        vertex_offset = 0
        
        # Process all products with geometry
        for product in ifc_file.by_type('IfcProduct'):
            if product.is_a('IfcOpeningElement'):
                continue
            
            try:
                shape = ifcopenshell.geom.create_shape(settings, product)
                
                # Get geometry data
                vertices = shape.geometry.verts
                faces = shape.geometry.faces
                
                # Reshape vertices (x,y,z triplets)
                verts_reshaped = [(vertices[i], vertices[i+1], vertices[i+2]) 
                                 for i in range(0, len(vertices), 3)]
                
                # Reshape faces (triangles)
                faces_reshaped = [(faces[i] + vertex_offset, 
                                  faces[i+1] + vertex_offset, 
                                  faces[i+2] + vertex_offset)
                                 for i in range(0, len(faces), 3)]
                
                all_vertices.extend(verts_reshaped)
                all_faces.extend(faces_reshaped)
                vertex_offset += len(verts_reshaped)
                
            except:
                continue
        
        if not all_vertices:
            raise ConversionError("No geometry found in IFC file")
        
        tri_mesh = self.trimesh.Trimesh(vertices=all_vertices, faces=all_faces)
        
        file_type = output_fmt if output_fmt != "gltf" else "glb"
        tri_mesh.export(output_path, file_type=file_type)
        
        return {
            "success": True,
            "vertices": len(all_vertices),
            "faces": len(all_faces),
            "method": "ifcopenshell"
        }
    
    def _convert_scene_to_scene(self, input_path: str, output_path: str,
                                input_fmt: str, output_fmt: str, **options) -> Dict[str, Any]:
        """Convert between scene formats."""
        # Use trimesh for basic conversions
        if self.mesh_available:
            try:
                return self._convert_mesh_to_mesh(input_path, output_path, input_fmt, output_fmt, **options)
            except Exception as e:
                pass
        
        raise ConversionError(f"Scene to scene conversion not yet supported for {input_fmt} -> {output_fmt}")
    
    def _convert_via_mesh(self, input_path: str, output_path: str,
                          input_fmt: str, output_fmt: str, **options) -> Dict[str, Any]:
        """Convert via intermediate mesh format."""
        # Use STL as intermediate
        if not self.mesh_available:
            raise ConversionError("trimesh required for conversion")
        
        with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as tmp:
            temp_stl = tmp.name
        
        try:
            # Convert to STL first
            self._route_conversion(input_path, temp_stl, input_fmt, "stl", **options)
            
            # Then to target format
            result = self._convert_mesh_to_mesh(temp_stl, output_path, "stl", output_fmt, **options)
            result["method"] = f"via_stl -> {result['method']}"
            return result
            
        finally:
            if os.path.exists(temp_stl):
                os.unlink(temp_stl)
    
    def get_info(self, filepath: str, format_id: Optional[str] = None) -> Dict[str, Any]:
        """Get information about a 3D file."""
        from .format_registry import FormatDetector
        
        if format_id is None:
            format_id, _ = FormatDetector.detect(filepath)
        
        info = {
            "format": format_id,
            "file_size": os.path.getsize(filepath),
            "path": filepath
        }
        
        if not self.mesh_available:
            return info
        
        try:
            mesh = self.trimesh.load(filepath, force='mesh')
            
            if isinstance(mesh, self.trimesh.Scene):
                info["type"] = "scene"
                info["object_count"] = len(mesh.geometry)
            else:
                info["type"] = "mesh"
                info["vertices"] = len(mesh.vertices)
                info["faces"] = len(mesh.faces)
                info["bounds"] = mesh.bounds.tolist()
                info["volume"] = float(mesh.volume) if mesh.is_watertight else None
                info["surface_area"] = float(mesh.area)
                info["watertight"] = mesh.is_watertight
                
        except Exception as e:
            info["error"] = str(e)
        
        return info

def convert_file(input_path: str, output_path: str, **options) -> Dict[str, Any]:
    """Convenience function for one-off conversions."""
    converter = Converter3D()
    return converter.convert(input_path, output_path, **options)