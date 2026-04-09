#!/usr/bin/env python3
"""
Entry point for 3D File Format Converter
Can run as CLI or GUI
"""

import sys
import argparse

def main():
    parser = argparse.ArgumentParser(
        description='3D File Format Converter - Universal converter for 3D files',
        usage='''%(prog)s [command] [options]

Commands:
    convert     Convert a single file
    batch       Convert multiple files
    info        Get file information
    formats     List supported formats
    gui         Launch graphical interface
    
Examples:
    %(prog)s convert input.stl output.obj
    %(prog)s batch ./models ./converted --output-format gltf
    %(prog)s info model.step
    %(prog)s gui
''')
    
    parser.add_argument('command', nargs='?', 
                       help='Command to run (convert, batch, info, formats, gui)')
    
    # Check if GUI requested or no command
    if len(sys.argv) == 1:
        # No arguments - launch GUI
        try:
            from converter3d.gui import main as gui_main
            gui_main()
        except ImportError:
            print("GUI mode requires tkinter. Please install python3-tk.")
            print("\nOr use CLI mode:")
            print("  python main.py convert input.stl output.obj")
            sys.exit(1)
    elif len(sys.argv) > 1 and sys.argv[1] == 'gui':
        # GUI explicitly requested
        try:
            from converter3d.gui import main as gui_main
            gui_main()
        except ImportError:
            print("GUI mode requires tkinter. Please install python3-tk.")
            sys.exit(1)
    else:
        # CLI mode - pass to click CLI
        from converter3d.cli import cli
        cli()

if __name__ == '__main__':
    main()
