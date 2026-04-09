"""
Simple GUI for the 3D file converter using tkinter.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import threading
from pathlib import Path

from .converter import Converter3D, ConversionError
from .format_registry import FORMAT_REGISTRY, get_supported_formats
from .batch import BatchConverter

class ConverterGUI:
    """Tkinter-based GUI for the 3D converter."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("3D File Format Converter")
        self.root.geometry("700x600")
        self.root.minsize(600, 500)
        
        self.converter = Converter3D()
        self.current_task = None
        
        self._create_ui()
        self._load_formats()
    
    def _create_ui(self):
        """Create the user interface."""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title = ttk.Label(main_frame, text="3D File Format Converter", 
                         font=('Helvetica', 16, 'bold'))
        title.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Mode selection
        mode_frame = ttk.LabelFrame(main_frame, text="Conversion Mode", padding="10")
        mode_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.mode_var = tk.StringVar(value="single")
        ttk.Radiobutton(mode_frame, text="Single File", variable=self.mode_var,
                       value="single", command=self._on_mode_change).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(mode_frame, text="Batch (Directory)", variable=self.mode_var,
                       value="batch", command=self._on_mode_change).pack(side=tk.LEFT, padx=10)
        
        # Input section
        input_frame = ttk.LabelFrame(main_frame, text="Input", padding="10")
        input_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        input_frame.columnconfigure(0, weight=1)
        
        self.input_path_var = tk.StringVar()
        self.input_entry = ttk.Entry(input_frame, textvariable=self.input_path_var)
        self.input_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        self.input_btn = ttk.Button(input_frame, text="Browse...", command=self._browse_input)
        self.input_btn.grid(row=0, column=1)
        
        # Output section
        output_frame = ttk.LabelFrame(main_frame, text="Output", padding="10")
        output_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        output_frame.columnconfigure(0, weight=1)
        
        self.output_path_var = tk.StringVar()
        self.output_entry = ttk.Entry(output_frame, textvariable=self.output_path_var)
        self.output_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        self.output_btn = ttk.Button(output_frame, text="Browse...", command=self._browse_output)
        self.output_btn.grid(row=0, column=1)
        
        # Format selection
        format_frame = ttk.LabelFrame(main_frame, text="Output Format", padding="10")
        format_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(format_frame, text="Format:").pack(side=tk.LEFT, padx=(0, 5))
        self.format_var = tk.StringVar()
        self.format_combo = ttk.Combobox(format_frame, textvariable=self.format_var, 
                                         state="readonly", width=20)
        self.format_combo.pack(side=tk.LEFT)
        
        # Options
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        options_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Tolerance
        ttk.Label(options_frame, text="Tolerance:").grid(row=0, column=0, sticky=tk.W)
        self.tolerance_var = tk.DoubleVar(value=0.1)
        ttk.Spinbox(options_frame, from_=0.001, to=1.0, increment=0.001,
                   textvariable=self.tolerance_var, width=10).grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Recursive
        self.recursive_var = tk.BooleanVar(value=False)
        self.recursive_check = ttk.Checkbutton(options_frame, text="Recursive (batch mode)",
                                               variable=self.recursive_var)
        self.recursive_check.grid(row=0, column=2, padx=20)
        
        # Convert button
        self.convert_btn = ttk.Button(main_frame, text="Convert", command=self._start_conversion)
        self.convert_btn.grid(row=6, column=0, columnspan=3, pady=20)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Status
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.grid(row=8, column=0, columnspan=3, sticky=tk.W)
        
        # Log area
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="5")
        log_frame.grid(row=9, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(9, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, state=tk.DISABLED)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    def _load_formats(self):
        """Load supported formats into the combobox."""
        formats = get_supported_formats()
        all_formats = sorted(formats['all_write'])
        self.format_combo['values'] = [f.upper() for f in all_formats]
        if all_formats:
            self.format_combo.current(0)
    
    def _on_mode_change(self):
        """Handle mode change between single file and batch."""
        mode = self.mode_var.get()
        if mode == "single":
            self.input_path_var.set("")
            self.output_path_var.set("")
        else:
            self.input_path_var.set("")
            self.output_path_var.set("")
    
    def _browse_input(self):
        """Browse for input file or directory."""
        mode = self.mode_var.get()
        if mode == "single":
            # File dialog
            filetypes = [("All 3D files", "*.stl;*.obj;*.ply;*.gltf;*.glb;*.dae;*.fbx;*.3ds;*.wrl;*.step;*.stp;*.iges;*.igs;*.3dm;*.ifc;*.brep"),
                        ("STL files", "*.stl"),
                        ("OBJ files", "*.obj"),
                        ("PLY files", "*.ply"),
                        ("glTF files", "*.gltf;*.glb"),
                        ("STEP files", "*.step;*.stp"),
                        ("All files", "*.*")]
            path = filedialog.askopenfilename(filetypes=filetypes)
        else:
            # Directory dialog
            path = filedialog.askdirectory()
        
        if path:
            self.input_path_var.set(path)
            # Auto-suggest output path
            self._auto_suggest_output(path)
    
    def _browse_output(self):
        """Browse for output file or directory."""
        mode = self.mode_var.get()
        if mode == "single":
            path = filedialog.asksaveasfilename(
                defaultextension=f".{self.format_var.get().lower()}"
            )
        else:
            path = filedialog.askdirectory()
        
        if path:
            self.output_path_var.set(path)
    
    def _auto_suggest_output(self, input_path):
        """Auto-suggest output path based on input."""
        input_path = Path(input_path)
        output_format = self.format_var.get().lower()
        
        if self.mode_var.get() == "single":
            output_name = input_path.stem + f"_converted.{output_format}"
            self.output_path_var.set(str(input_path.parent / output_name))
        else:
            self.output_path_var.set(str(input_path.parent / f"{input_path.name}_converted"))
    
    def _start_conversion(self):
        """Start the conversion process."""
        input_path = self.input_path_var.get()
        output_path = self.output_path_var.get()
        output_format = self.format_var.get().lower()
        
        if not input_path or not output_path:
            messagebox.showerror("Error", "Please specify input and output paths")
            return
        
        if not os.path.exists(input_path):
            messagebox.showerror("Error", "Input path does not exist")
            return
        
        # Start conversion in separate thread
        self.convert_btn.config(state=tk.DISABLED)
        self.progress.start()
        self.status_var.set("Converting...")
        self._log("Starting conversion...")
        
        thread = threading.Thread(target=self._convert_worker,
                                 args=(input_path, output_path, output_format))
        thread.daemon = True
        thread.start()
    
    def _convert_worker(self, input_path, output_path, output_format):
        """Worker thread for conversion."""
        try:
            if self.mode_var.get() == "single":
                self._convert_single(input_path, output_path, output_format)
            else:
                self._convert_batch(input_path, output_path, output_format)
        except Exception as e:
            self.root.after(0, lambda: self._conversion_error(str(e)))
    
    def _convert_single(self, input_path, output_path, output_format):
        """Convert a single file."""
        try:
            result = self.converter.convert(
                input_path, output_path,
                output_format=output_format,
                tolerance=self.tolerance_var.get()
            )
            
            if result['success']:
                msg = f"✓ Conversion successful!\n"
                if 'vertices' in result:
                    msg += f"Vertices: {result['vertices']:,}\n"
                    msg += f"Faces: {result['faces']:,}\n"
                msg += f"Method: {result.get('method', 'unknown')}"
                
                self.root.after(0, lambda: self._conversion_success(msg))
            else:
                self.root.after(0, lambda: self._conversion_error("Conversion failed"))
                
        except ConversionError as e:
            self.root.after(0, lambda: self._conversion_error(str(e)))
    
    def _convert_batch(self, input_path, output_path, output_format):
        """Convert a batch of files."""
        from .batch import convert_directory
        
        result = convert_directory(
            input_path, output_path, output_format,
            recursive=self.recursive_var.get(),
            tolerance=self.tolerance_var.get()
        )
        
        if result['success']:
            msg = f"✓ Batch conversion complete!\n"
            msg += f"Total: {result['total']}\n"
            msg += f"Successful: {result['converted']}\n"
            msg += f"Failed: {result['failed']}"
            self.root.after(0, lambda: self._conversion_success(msg))
        else:
            msg = f"Batch completed with errors:\n"
            msg += f"Successful: {result['converted']}\n"
            msg += f"Failed: {result['failed']}"
            self.root.after(0, lambda: self._conversion_error(msg))
    
    def _conversion_success(self, message):
        """Handle successful conversion."""
        self.progress.stop()
        self.convert_btn.config(state=tk.NORMAL)
        self.status_var.set("Conversion complete")
        self._log(message)
        messagebox.showinfo("Success", message)
    
    def _conversion_error(self, message):
        """Handle conversion error."""
        self.progress.stop()
        self.convert_btn.config(state=tk.NORMAL)
        self.status_var.set("Conversion failed")
        self._log(f"Error: {message}")
        messagebox.showerror("Error", message)
    
    def _log(self, message):
        """Add a message to the log."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

def main():
    """Run the GUI application."""
    root = tk.Tk()
    app = ConverterGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()