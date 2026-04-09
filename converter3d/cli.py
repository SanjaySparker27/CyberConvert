#!/usr/bin/env python3
"""
Command-line interface for 3D File Format Converter
"""

import os
import sys
import click
from pathlib import Path
from typing import List
from tqdm import tqdm
import colorama
from colorama import Fore, Style

from .converter import Converter3D, ConversionError
from .format_registry import FormatDetector, FORMAT_REGISTRY, get_supported_formats
from .batch import BatchConverter

colorama.init()

# Get version from package
from . import __version__

@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="converter3d")
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx, verbose):
    """
    3D File Format Converter
    
    Convert between 3dm, 3ds, 3mf, amf, bim, brep, dae, fbx, fcstd,
    gltf, ifc, iges, step, stl, obj, off, ply, wrl and more.
    
    Examples:
        converter3d convert input.stl output.obj
        converter3d convert input.step output.stl --tolerance 0.01
        converter3d batch ./input_dir ./output_dir --output-format gltf
        converter3d info model.stl
    """
    ctx.ensure_object(dict)
    ctx.obj['VERBOSE'] = verbose
    
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())

@cli.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.argument('output_path', type=click.Path())
@click.option('--input-format', '-i', help='Input format (auto-detect if not specified)')
@click.option('--output-format', '-o', help='Output format (from extension if not specified)')
@click.option('--tolerance', '-t', type=float, default=0.1, help='Mesh tessellation tolerance (for CAD formats)')
@click.option('--angular-tolerance', '-a', type=float, default=0.1, help='Angular tolerance in radians (for CAD formats)')
@click.option('--merge-meshes', is_flag=True, help='Merge multiple meshes into one')
@click.pass_context
def convert(ctx, input_path, output_path, input_format, output_format, 
            tolerance, angular_tolerance, merge_meshes):
    """Convert a single 3D file."""
    verbose = ctx.obj.get('VERBOSE', False)
    
    converter = Converter3D()
    
    # Detect formats
    detected_input, detect_method = FormatDetector.detect(input_path)
    
    if input_format:
        actual_input = input_format.lower()
    else:
        actual_input = detected_input
        if verbose and detected_input:
            click.echo(f"{Fore.BLUE}Detected input format: {detected_input} ({detect_method}){Style.RESET_ALL}")
    
    if output_format:
        actual_output = output_format.lower()
    else:
        actual_output = FormatDetector.get_format_by_extension(output_path)
    
    if not actual_input:
        click.echo(f"{Fore.RED}Error: Could not detect input format. Use --input-format to specify.{Style.RESET_ALL}")
        sys.exit(1)
    
    if not actual_output:
        click.echo(f"{Fore.RED}Error: Could not detect output format. Use --output-format to specify.{Style.RESET_ALL}")
        sys.exit(1)
    
    # Show conversion info
    click.echo(f"Converting: {Fore.CYAN}{input_path}{Style.RESET_ALL}")
    click.echo(f"Format: {Fore.GREEN}{actual_input.upper()}{Style.RESET_ALL} -> {Fore.GREEN}{actual_output.upper()}{Style.RESET_ALL}")
    click.echo(f"Output: {Fore.CYAN}{output_path}{Style.RESET_ALL}")
    
    # Perform conversion
    try:
        options = {
            'tolerance': tolerance,
            'angular_tolerance': angular_tolerance,
            'merge_meshes': merge_meshes
        }
        
        result = converter.convert(input_path, output_path, **options)
        
        if result['success']:
            click.echo(f"\n{Fore.GREEN}✓ Conversion successful!{Style.RESET_ALL}")
            
            if 'vertices' in result:
                click.echo(f"  Vertices: {result['vertices']:,}")
                click.echo(f"  Faces: {result['faces']:,}")
            
            if 'method' in result:
                click.echo(f"  Method: {result['method']}")
            
            # Show output file size
            output_size = os.path.getsize(output_path)
            click.echo(f"  Output size: {format_file_size(output_size)}")
        else:
            click.echo(f"\n{Fore.RED}✗ Conversion failed{Style.RESET_ALL}")
            sys.exit(1)
            
    except ConversionError as e:
        click.echo(f"\n{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        click.echo(f"\n{Fore.RED}Unexpected error: {str(e)}{Style.RESET_ALL}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

@cli.command()
@click.argument('input_dir', type=click.Path(exists=True, file_okay=False))
@click.argument('output_dir', type=click.Path())
@click.option('--output-format', '-f', required=True, help='Output format for all files')
@click.option('--recursive', '-r', is_flag=True, help='Process subdirectories recursively')
@click.option('--pattern', '-p', default='*', help='File pattern to match (e.g., "*.stl")')
@click.option('--tolerance', '-t', type=float, default=0.1)
@click.option('--workers', '-w', type=int, default=1, help='Number of parallel workers')
@click.pass_context
def batch(ctx, input_dir, output_dir, output_format, recursive, pattern, tolerance, workers):
    """Convert multiple files in batch mode."""
    verbose = ctx.obj.get('VERBOSE', False)
    
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find files
    if recursive:
        if pattern == '*':
            # Match all supported extensions
            files = []
            for fmt_info in FORMAT_REGISTRY.values():
                for ext in fmt_info.extensions:
                    files.extend(input_dir.rglob(f'*{ext}'))
        else:
            files = list(input_dir.rglob(pattern))
    else:
        if pattern == '*':
            files = []
            for fmt_info in FORMAT_REGISTRY.values():
                for ext in fmt_info.extensions:
                    files.extend(input_dir.glob(f'*{ext}'))
        else:
            files = list(input_dir.glob(pattern))
    
    files = sorted(set(files))  # Remove duplicates and sort
    
    if not files:
        click.echo(f"{Fore.YELLOW}No matching files found.{Style.RESET_ALL}")
        return
    
    click.echo(f"Found {len(files)} file(s) to convert")
    click.echo(f"Output format: {output_format}")
    click.echo(f"Output directory: {output_dir}\n")
    
    batch_converter = BatchConverter(
        output_format=output_format,
        tolerance=tolerance,
        workers=workers,
        verbose=verbose
    )
    
    results = batch_converter.convert_batch(files, input_dir, output_dir)
    
    # Summary
    successful = sum(1 for r in results if r.get('success'))
    failed = len(results) - successful
    
    click.echo(f"\n{Fore.GREEN if failed == 0 else Fore.YELLOW}Batch conversion complete:{Style.RESET_ALL}")
    click.echo(f"  Successful: {Fore.GREEN}{successful}{Style.RESET_ALL}")
    click.echo(f"  Failed: {Fore.RED if failed > 0 else Fore.GREEN}{failed}{Style.RESET_ALL}")
    
    if failed > 0 and verbose:
        click.echo(f"\n{Fore.RED}Failed conversions:{Style.RESET_ALL}")
        for r in results:
            if not r.get('success'):
                click.echo(f"  - {r.get('input', 'unknown')}: {r.get('error', 'unknown error')}")

@cli.command()
@click.argument('filepath', type=click.Path(exists=True))
@click.option('--format', '-f', help='Specify format (auto-detect if not provided)')
@click.pass_context
def info(ctx, filepath, format):
    """Display information about a 3D file."""
    verbose = ctx.obj.get('VERBOSE', False)
    converter = Converter3D()
    
    try:
        file_info = converter.get_info(filepath, format)
        
        # Format info
        click.echo(f"\n{Fore.CYAN}File Information{Style.RESET_ALL}")
        click.echo(f"  Path: {filepath}")
        click.echo(f"  Size: {format_file_size(file_info['file_size'])}")
        
        if file_info.get('format'):
            fmt_name = FORMAT_REGISTRY.get(file_info['format'], {}).name or file_info['format'].upper()
            click.echo(f"  Format: {fmt_name}")
        
        if 'type' in file_info:
            click.echo(f"  Type: {file_info['type'].capitalize()}")
        
        if 'vertices' in file_info:
            click.echo(f"\n{Fore.CYAN}Mesh Statistics{Style.RESET_ALL}")
            click.echo(f"  Vertices: {file_info['vertices']:,}")
            click.echo(f"  Faces: {file_info['faces']:,}")
            
            if 'bounds' in file_info and file_info['bounds']:
                bounds = file_info['bounds']
                dims = [b[1] - b[0] for b in bounds]
                click.echo(f"  Dimensions: {dims[0]:.3f} x {dims[1]:.3f} x {dims[2]:.3f}")
            
            if 'volume' in file_info and file_info['volume']:
                click.echo(f"  Volume: {file_info['volume']:.3f}")
            
            if 'surface_area' in file_info:
                click.echo(f"  Surface Area: {file_info['surface_area']:.3f}")
            
            if 'watertight' in file_info:
                status = f"{Fore.GREEN}Yes" if file_info['watertight'] else f"{Fore.RED}No"
                click.echo(f"  Watertight: {status}{Style.RESET_ALL}")
        
        if 'object_count' in file_info:
            click.echo(f"  Objects: {file_info['object_count']}")
        
        if 'error' in file_info:
            click.echo(f"\n{Fore.RED}Error reading file: {file_info['error']}{Style.RESET_ALL}")
            
    except Exception as e:
        click.echo(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)

@cli.command()
def formats():
    """List all supported file formats."""
    supported = get_supported_formats()
    
    click.echo(f"\n{Fore.CYAN}Supported File Formats{Style.RESET_ALL}\n")
    
    categories = {
        'mesh': f"{Fore.GREEN}Mesh Formats{Style.RESET_ALL}",
        'cad': f"{Fore.BLUE}CAD Formats{Style.RESET_ALL}",
        'bim': f"{Fore.MAGENTA}BIM/Architecture{Style.RESET_ALL}",
        'scene': f"{Fore.YELLOW}Scene Formats{Style.RESET_ALL}",
        'freecad': f"{Fore.CYAN}FreeCAD{Style.RESET_ALL}",
    }
    
    for cat_key, cat_name in categories.items():
        formats = supported.get(cat_key, [])
        if formats:
            click.echo(f"\n{cat_name}")
            for fmt_id in sorted(formats):
                fmt_info = FORMAT_REGISTRY[fmt_id]
                ext_str = ', '.join(fmt_info.extensions)
                rw_status = "R/W" if fmt_info.can_read and fmt_info.can_write else "R" if fmt_info.can_read else "W"
                click.echo(f"  {fmt_id.upper():8} ({ext_str:20}) [{rw_status}] - {fmt_info.description}")
    
    click.echo(f"\n{Fore.GREEN}Legend:{Style.RESET_ALL} [R/W] = Read & Write, [R] = Read only, [W] = Write only")

def format_file_size(size_bytes):
    """Format file size in human-readable form."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def main():
    """Entry point for the CLI."""
    cli()

if __name__ == '__main__':
    main()