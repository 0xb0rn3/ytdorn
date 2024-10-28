#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import sys
import threading
import queue
import os
from datetime import datetime
from yt_dlp import YoutubeDL
import platform
import subprocess
import pkg_resources
import shutil
from typing import Tuple

class Colors:
    BLUE = '#3498db'
    CYAN = '#00bcd4'
    GREEN = '#2ecc71'
    YELLOW = '#f1c40f'
    RED = '#e74c3c'
    BG_DARK = '#2c3e50'
    BG_LIGHT = '#ffffff'
    TEXT_DARK = '#2c3e50'
    TEXT_LIGHT = '#ecf0f1'

class YtDornGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YtDorn3 GUI")
        self.root.geometry("800x600")
        self.root.configure(bg=Colors.BG_LIGHT)
        self.output_queue = queue.Queue()
        self.create_widgets()
        self.check_dependencies()

    def create_widgets(self):
        # URL Frame
        url_frame = ttk.Frame(self.root)
        url_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(url_frame, text="URL:").pack(side='left')
        self.url_entry = ttk.Entry(url_frame)
        self.url_entry.pack(side='left', fill='x', expand=True, padx=5)

        # Type Selection
        type_frame = ttk.Frame(self.root)
        type_frame.pack(fill='x', padx=10, pady=5)
        
        self.download_type = tk.StringVar(value="single")
        ttk.Radiobutton(type_frame, text="Single Video", 
                       variable=self.download_type, value="single").pack(side='left')
        ttk.Radiobutton(type_frame, text="Playlist", 
                       variable=self.download_type, value="playlist").pack(side='left')

        # Quality Selection
        quality_frame = ttk.Frame(self.root)
        quality_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(quality_frame, text="Quality:").pack(side='left')
        self.quality_var = tk.StringVar(value="1")
        qualities = [
            "Best Quality Video (1080p+)",
            "Medium Quality Video (720p)",
            "Low Quality Video (480p)",
            "Audio Only (Best Quality)",
            "Audio Only (Medium Quality)"
        ]
        quality_menu = ttk.Combobox(quality_frame, textvariable=self.quality_var, 
                                  values=qualities, state='readonly')
        quality_menu.pack(side='left', fill='x', expand=True, padx=5)
        quality_menu.set(qualities[0])

        # Output Directory
        dir_frame = ttk.Frame(self.root)
        dir_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(dir_frame, text="Save to:").pack(side='left')
        self.dir_entry = ttk.Entry(dir_frame)
        self.dir_entry.pack(side='left', fill='x', expand=True, padx=5)
        self.dir_entry.insert(0, os.path.join(os.path.expanduser("~"), "Downloads"))
        
        ttk.Button(dir_frame, text="Browse", 
                  command=self.browse_directory).pack(side='right')

        # Progress Frame
        progress_frame = ttk.Frame(self.root)
        progress_frame.pack(fill='x', padx=10, pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, 
                                          variable=self.progress_var, 
                                          maximum=100)
        self.progress_bar.pack(fill='x', pady=5)
        
        self.status_label = ttk.Label(progress_frame, text="Ready")
        self.status_label.pack(fill='x')

        # Log Area
        self.log_area = scrolledtext.ScrolledText(self.root, height=15)
        self.log_area.pack(fill='both', expand=True, padx=10, pady=5)

        # Control Buttons
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill='x', padx=10, pady=5)
        
        self.download_btn = ttk.Button(button_frame, text="Download", 
                                     command=self.start_download)
        self.download_btn.pack(side='left', padx=5)
        
        ttk.Button(button_frame, text="Cancel", 
                  command=self.cancel_download).pack(side='left', padx=5)
        
        ttk.Button(button_frame, text="Clear Log", 
                  command=self.clear_log).pack(side='right', padx=5)

    def browse_directory(self):
        directory = filedialog.askdirectory(initialdir=self.dir_entry.get())
        if directory:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, directory)

    def log(self, message, level="info"):
        color_map = {
            "info": Colors.TEXT_DARK,
            "success": Colors.GREEN,
            "error": Colors.RED,
            "warning": Colors.YELLOW
        }
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_area.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_area.see(tk.END)
        
        # Color the last line
        last_line_start = self.log_area.get("end-2c linestart", "end-1c")
        self.log_area.tag_add(level, f"end-{len(last_line_start)+2}c linestart", "end-1c")
        self.log_area.tag_config(level, foreground=color_map.get(level, Colors.TEXT_DARK))

    def download_progress_hook(self, d):
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes', 0)
            downloaded_bytes = d.get('downloaded_bytes', 0)
            if total_bytes > 0:
                progress = (downloaded_bytes / total_bytes) * 100
                self.output_queue.put(('progress', progress))
                
            filename = os.path.basename(d.get('filename', ''))
            speed = d.get('speed', 0)
            if speed:
                speed_str = self.format_size(speed) + '/s'
                status = f"Downloading {filename}... @ {speed_str}"
                self.output_queue.put(('status', status))

        elif d['status'] == 'finished':
            self.output_queue.put(('status', "Download complete, processing..."))
            self.log("Download complete, processing file...", "success")

    def format_size(self, bytes):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes < 1024:
                return f"{bytes:.1f}{unit}"
            bytes /= 1024
        return f"{bytes:.1f}TB"

    def start_download(self):
        url = self.url_entry.get().strip()
        if not url:
            self.log("Please enter a URL", "error")
            return

        self.download_btn.state(['disabled'])
        self.progress_var.set(0)
        threading.Thread(target=self.download_thread, daemon=True).start()
        self.check_queue()

    def download_thread(self):
        try:
            url = self.url_entry.get().strip()
            output_dir = self.dir_entry.get()
            is_playlist = self.download_type.get() == "playlist"
            quality = self.quality_var.get()[0]  # Get first character (1-5)

            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            format_options = self.get_format_options(quality)
            ydl_opts = {
                'outtmpl': os.path.join(output_dir, 
                                      '%(playlist)s/%(title)s.%(ext)s' if is_playlist 
                                      else '%(title)s.%(ext)s'),
                'progress_hooks': [self.download_progress_hook],
                'quiet': True,
                'no_warnings': True,
                'extract_flat': is_playlist
            }
            ydl_opts.update(format_options)

            with YoutubeDL(ydl_opts) as ydl:
                self.log(f"Starting download for: {url}")
                ydl.download([url])

            self.output_queue.put(('done', None))
        except Exception as e:
            self.output_queue.put(('error', str(e)))

    def check_queue(self):
        try:
            while True:
                msg_type, msg = self.output_queue.get_nowait()
                if msg_type == 'progress':
                    self.progress_var.set(msg)
                elif msg_type == 'status':
                    self.status_label.config(text=msg)
                elif msg_type == 'error':
                    self.log(f"Error: {msg}", "error")
                    self.download_btn.state(['!disabled'])
                elif msg_type == 'done':
                    self.log("Download completed successfully!", "success")
                    self.download_btn.state(['!disabled'])
                    return
        except queue.Empty:
            pass
        self.root.after(100, self.check_queue)

    def cancel_download(self):
        self.log("Download cancelled", "warning")
        self.download_btn.state(['!disabled'])
        self.progress_var.set(0)
        self.status_label.config(text="Ready")

    def clear_log(self):
        self.log_area.delete(1.0, tk.END)

    def get_format_options(self, choice):
        if choice == '1':
            return {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            }
        elif choice == '2':
            return {
                'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best'
            }
        elif choice == '3':
            return {
                'format': 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best'
            }
        elif choice == '4':
            return {
                'format': 'bestaudio[ext=m4a]/bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'm4a',
                    'preferredquality': '192',
                }]
            }
        else:
            return {
                'format': 'worstaudio/worst',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'm4a',
                    'preferredquality': '128',
                }]
            }

    def check_dependencies(self):
        try:
            import yt_dlp
        except ImportError:
            self.log("Installing yt-dlp...", "warning")
            try:
                subprocess.check_call([
                    sys.executable, 
                    "-m", 
                    "pip", 
                    "install", 
                    "yt-dlp",
                    "--break-system-packages"
                ])
                self.log("yt-dlp installed successfully!", "success")
            except:
                self.log("Error installing yt-dlp. Please install manually.", "error")

def main():
    root = tk.Tk()
    app = YtDornGUI(root)
    
    # Set style
    style = ttk.Style()
    if platform.system() == 'Darwin':  # macOS
        style.theme_use('aqua')
    else:
        style.theme_use('clam')

    root.mainloop()

if __name__ == "__main__":
    main()
