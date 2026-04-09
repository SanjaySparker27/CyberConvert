"""
Batch conversion functionality for processing multiple files.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Callable
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
import time

from .converter import Converter3D, ConversionError
from .format_registry import FormatDetector

class BatchConverter:
    """Handles batch conversion of multiple files."""
    
    def __init__(self, output_format: str, tolerance: float = 0.1, 
                 angular_tolerance: float = 0.1, workers: int = 1,
                 verbose: bool = False):
        self.output_format = output_format.lower()
        self.tolerance = tolerance
        self.angular_tolerance = angular_tolerance
        self.workers = workers
        self.verbose = verbose
    
    def convert_batch(self, files: List[Path], input_base: Path, 
                      output_base: Path) -> List[Dict[str, Any]]:
        """
        Convert a batch of files.
        
        Args:
            files: List of input file paths
            input_base: Base input directory
            output_base: Base output directory
            
        Returns:
            List of conversion results
        """
        results = []
        
        if self.workers > 1:
            # Parallel processing
            with ProcessPoolExecutor(max_workers=self.workers) as executor:
                futures = {}
                
                for file_path in files:
                    future = executor.submit(
                        self._convert_single,
                        file_path, input_base, output_base
                    )
                    futures[future] = file_path
                
                # Progress bar
                with tqdm(total=len(files), desc="Converting") as pbar:
                    for future in as_completed(futures):
                        file_path = futures[future]
                        try:
                            result = future.result()
                        except Exception as e:
                            result = {
                                'success': False,
                                'input': str(file_path),
                                'error': str(e)
                            }
                        
                        results.append(result)
                        pbar.update(1)
                        
                        if self.verbose and result.get('success'):
                            pbar.write(f"✓ {file_path.name}")
                        elif not result.get('success'):
                            pbar.write(f"✗ {file_path.name}: {result.get('error', 'Failed')}")
        else:
            # Sequential processing with progress bar
            for file_path in tqdm(files, desc="Converting"):
                result = self._convert_single(file_path, input_base, output_base)
                results.append(result)
        
        return results
    
    def _convert_single(self, input_path: Path, input_base: Path, 
                        output_base: Path) -> Dict[str, Any]:
        """Convert a single file."""
        # Determine relative path to maintain directory structure
        rel_path = input_path.relative_to(input_base)
        output_path = output_base / rel_path
        
        # Change extension to output format
        output_path = output_path.with_suffix(f".{self.output_format}")
        
        # Create output directory
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            converter = Converter3D()
            
            result = converter.convert(
                str(input_path),
                str(output_path),
                output_format=self.output_format,
                tolerance=self.tolerance,
                angular_tolerance=self.angular_tolerance
            )
            
            result['input'] = str(input_path)
            result['output'] = str(output_path)
            return result
            
        except Exception as e:
            return {
                'success': False,
                'input': str(input_path),
                'error': str(e)
            }
    
    def convert_with_callback(self, files: List[Path], input_base: Path,
                              output_base: Path, 
                              progress_callback: Callable[[int, int, str], None],
                              complete_callback: Callable[[Dict[str, Any]], None]):
        """
        Batch convert with callbacks for UI integration.
        
        Args:
            files: List of input files
            input_base: Base input directory
            output_base: Base output directory
            progress_callback: Called with (current, total, message)
            complete_callback: Called with result dict for each file
        """
        total = len(files)
        
        for i, file_path in enumerate(files):
            progress_callback(i, total, f"Converting {file_path.name}...")
            
            result = self._convert_single(file_path, input_base, output_base)
            complete_callback(result)
        
        progress_callback(total, total, "Complete")

def convert_directory(input_dir: str, output_dir: str, output_format: str,
                     recursive: bool = True, pattern: str = '*',
                     tolerance: float = 0.1, workers: int = 1) -> Dict[str, Any]:
    """
    Convenience function to convert an entire directory.
    
    Returns summary statistics.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Find files
    if recursive:
        if pattern == '*':
            # All supported formats
            from .format_registry import FORMAT_REGISTRY
            files = []
            for fmt_info in FORMAT_REGISTRY.values():
                for ext in fmt_info.extensions:
                    files.extend(input_path.rglob(f'*{ext}'))
        else:
            files = list(input_path.rglob(pattern))
    else:
        if pattern == '*':
            from .format_registry import FORMAT_REGISTRY
            files = []
            for fmt_info in FORMAT_REGISTRY.values():
                for ext in fmt_info.extensions:
                    files.extend(input_path.glob(f'*{ext}'))
        else:
            files = list(input_path.glob(pattern))
    
    files = sorted(set(files))
    
    if not files:
        return {
            'success': False,
            'error': 'No files found',
            'total': 0,
            'converted': 0,
            'failed': 0
        }
    
    batch_converter = BatchConverter(
        output_format=output_format,
        tolerance=tolerance,
        workers=workers
    )
    
    results = batch_converter.convert_batch(files, input_path, output_path)
    
    successful = sum(1 for r in results if r.get('success'))
    failed = len(results) - successful
    
    return {
        'success': failed == 0,
        'total': len(files),
        'converted': successful,
        'failed': failed,
        'results': results
    }