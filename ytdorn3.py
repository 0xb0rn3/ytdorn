#!/usr/bin/env python3
"""
YtDorn3 - Enhanced YouTube Downloader
A feature-rich CLI tool for downloading YouTube videos and playlists with an elegant user interface.
"""

import sys
import platform
import subprocess
import os
from typing import Tuple, Dict, Any, Optional
import pkg_resources
import shutil
from datetime import datetime
import time
import threading
from math import ceil
import signal
import re
from pathlib import Path

class Colors:
    """
    Enhanced color and style management for terminal output.
    Supports RGB colors, gradients, and various text styles.
    """
    # Basic ANSI colors
    BLACK = '\033[30m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    
    # Text styles
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    REVERSE = '\033[7m'
    RESET = '\033[0m'
    
    # Background colors
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'

    @staticmethod
    def rgb(r: int, g: int, b: int) -> str:
        """Generate RGB color escape sequence."""
        return f'\033[38;2;{r};{g};{b}m'

    @staticmethod
    def gradient(text: str, start_color: Tuple[int, int, int], end_color: Tuple[int, int, int]) -> str:
        """
        Create a color gradient effect across text.
        
        Args:
            text: The text to apply the gradient to
            start_color: RGB tuple for starting color
            end_color: RGB tuple for ending color
            
        Returns:
            Text with applied color gradient
        """
        result = ""
        for i, char in enumerate(text):
            if char.strip():
                progress = i / (len(text) - 1) if len(text) > 1 else 0
                r = int(start_color[0] + (end_color[0] - start_color[0]) * progress)
                g = int(start_color[1] + (end_color[1] - start_color[1]) * progress)
                b = int(start_color[2] + (end_color[2] - start_color[2]) * progress)
                result += f"\033[38;2;{r};{g};{b}m{char}"
            else:
                result += char
        return result + Colors.RESET

class Spinner:
    """
    Animated spinner for showing progress during long operations.
    Uses threading to avoid blocking the main process.
    """
    def __init__(self):
        self.spinner_chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        self.stop_spinner = False
        self.spinner_thread = None
        self._current_message = ""

    def spin(self, message: str):
        """Animate the spinner with the given message."""
        i = 0
        while not self.stop_spinner:
            sys.stdout.write(f'\r{Colors.CYAN}{self.spinner_chars[i]}{Colors.RESET} {message}')
            sys.stdout.flush()
            time.sleep(0.1)
            i = (i + 1) % len(self.spinner_chars)

    def start(self, message: str):
        """Start the spinner animation."""
        self.stop_spinner = False
        self._current_message = message
        self.spinner_thread = threading.Thread(target=self.spin, args=(message,))
        self.spinner_thread.daemon = True
        self.spinner_thread.start()

    def stop(self):
        """Stop the spinner animation."""
        self.stop_spinner = True
        if self.spinner_thread:
            self.spinner_thread.join()
        sys.stdout.write('\r\033[K')
        sys.stdout.flush()

class ProgressBar:
    """
    Enhanced progress bar with ETA calculation and adaptive formatting.
    """
    def __init__(self, total: int, prefix: str = '', width: int = 30):
        self.total = total
        self.prefix = prefix
        self.width = width
        self.start_time = time.time()
        self.current = 0

    def update(self, current: int) -> str:
        """
        Update the progress bar with current progress.
        
        Args:
            current: Current progress value
            
        Returns:
            Formatted progress bar string
        """
        self.current = current
        percentage = (current / self.total) * 100 if self.total else 0
        filled_width = int(self.width * current / self.total) if self.total else 0
        
        # Create gradient progress bar
        bar = self._create_gradient_bar(filled_width)
        
        # Calculate ETA
        eta = self._calculate_eta(current)
        
        # Format the complete progress line
        return (f"\r{self.prefix} [{bar}] {percentage:5.1f}% "
                f"({self._format_size(current)}/{self._format_size(self.total)}) {eta}")

    def _create_gradient_bar(self, filled_width: int) -> str:
        """Create a gradient-colored progress bar."""
        gradient_bar = ''
        for i in range(filled_width):
            color_val = int(255 * (i / self.width))
            gradient_bar += Colors.rgb(100, 200-color_val, 255) + '█'
        
        return gradient_bar + Colors.DIM + '░' * (self.width - filled_width) + Colors.RESET

    def _calculate_eta(self, current: int) -> str:
        """Calculate and format the estimated time remaining."""
        if current <= 0:
            return "ETA: --:--"
            
        elapsed = time.time() - self.start_time
        rate = current / elapsed if elapsed > 0 else 0
        remaining = (self.total - current) / rate if rate > 0 else 0
        
        return f"ETA: {self._format_time(remaining)}"

    @staticmethod
    def _format_size(bytes: int) -> str:
        """Format byte size to human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes < 1024:
                return f"{bytes:.1f}{unit}"
            bytes /= 1024
        return f"{bytes:.1f}PB"

    @staticmethod
    def _format_time(seconds: float) -> str:
        """Format seconds into human readable time."""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.0f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"

class Console:
    """
    Console UI management class handling menus and user interaction.
    """
    @staticmethod
    def print_banner():
        """Display the application banner with ASCII art."""
        banner = """
        ╭──────────────────────────────────────╮
        │   __   _____ ____                    │
        │   \ \ / /_  /_  /  ___  ____  ____  │
        │    \ V / / / / / / _ \/ __ \/ __ \  │
        │    / . \/ /_/ /_/  __/ /_/ / / / /  │
        │   /_/ \_\___/___/\___/\____/_/ /_/  │
        │                                      │
        ╰──────────────────────────────────────╯
        """
        print(Colors.gradient(banner, (100, 200, 255), (150, 100, 255)))
        print(f"{Colors.CYAN}{Colors.BOLD}YtDorn3 {Colors.RESET}"
              f"{Colors.CYAN}v1.3 by Q4n0{Colors.RESET}")
        print(f"{Colors.DIM}https://github.com/Q4n0{Colors.RESET}")
        print(Colors.gradient('═' * 50, (100, 200, 255), (150, 100, 255)) + "\n")

    @staticmethod
    def create_menu(title: str, options: list, previous_selection: Optional[str] = None) -> str:
        """
        Create an interactive menu with the given options.
        
        Args:
            title: Menu title
            options: List of (key, label) tuples for menu options
            previous_selection: Previously selected option (for highlighting)
            
        Returns:
            Selected option key
        """
        print(f"\n{Colors.CYAN}{Colors.BOLD}{title}{Colors.RESET}")
        print(f"{Colors.DIM}{'─' * 40}{Colors.RESET}")
        
        for idx, (key, label) in enumerate(options, 1):
            prefix = '├──' if idx < len(options) else '└──'
            if previous_selection and str(idx) == previous_selection:
                print(f"{Colors.DIM}{prefix}{Colors.RESET} "
                      f"{Colors.GREEN}✓{Colors.RESET} {label}")
            else:
                print(f"{Colors.DIM}{prefix}{Colors.RESET} {label}")
        
        while True:
            choice = input(f"\n{Colors.CYAN}Select option (1-{len(options)}): "
                         f"{Colors.RESET}").strip()
            if choice in [str(i) for i in range(1, len(options) + 1)]:
                return choice
            print(f"{Colors.RED}Invalid selection. Please try again.{Colors.RESET}")

class SystemManager:
    """
    Handles system-related operations like dependency management.
    """
    @staticmethod
    def check_dependencies() -> Tuple[bool, bool]:
        """Check if required dependencies are installed."""
        yt_dlp_installed = shutil.which('yt-dlp') is not None
        try:
            pkg_resources.get_distribution('yt-dlp')
            yt_dlp_installed = True
        except pkg_resources.DistributionNotFound:
            pass
        
        ffmpeg_installed = shutil.which('ffmpeg') is not None
        return yt_dlp_installed, ffmpeg_installed

    @staticmethod
    def install_dependencies(spinner: Spinner):
        """Install required system dependencies."""
        os_type = platform.system().lower()
        yt_dlp_installed, ffmpeg_installed = SystemManager.check_dependencies()
        
        spinner.start("Checking dependencies...")
        time.sleep(1)  # Give visual feedback
        spinner.stop()
        
        if not yt_dlp_installed:
            print(f"\n{Colors.YELLOW}Installing yt-dlp...{Colors.RESET}")
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "yt-dlp", 
                     "--break-system-packages"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                print(f"{Colors.GREEN}✓ yt-dlp installed successfully!{Colors.RESET}")
            except subprocess.CalledProcessError:
                try:
                    subprocess.check_call(
                        [sys.executable, "-m", "pip", "install", "yt-dlp"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    print(f"{Colors.GREEN}✓ yt-dlp installed successfully!{Colors.RESET}")
                except subprocess.CalledProcessError:
                    print(f"{Colors.RED}✗ Error installing yt-dlp.{Colors.RESET}")
                    SystemManager._show_manual_install_instructions()
                    sys.exit(1)
        
        if not ffmpeg_installed:
            print(f"\n{Colors.YELLOW}Installing ffmpeg...{Colors.RESET}")
            try:
                SystemManager._install_ffmpeg_for_os(os_type)
                print(f"{Colors.GREEN}✓ ffmpeg installed successfully!{Colors.RESET}")
            except Exception as e:
                print(f"{Colors.RED}✗ Error installing ffmpeg: {str(e)}{Colors.RESET}")
                print("Please install ffmpeg manually from: "
                      "https://ffmpeg.org/download.html")
                sys.exit(1)

    @staticmethod
    def _install_ffmpeg_for_os(os_type: str):
        """Install ffmpeg for the specific operating system."""
        if os_type == "windows":
            if shutil.which('choco'):
                subprocess.check_call(['choco', 'install', 'ffmpeg', '-y'])
            else:
                raise Exception("Chocolatey package manager not found")
        elif os_type == "darwin":
            if shutil.which('brew'):
                subprocess.check_call(['brew', 'install', 'ffmpeg'])
            else:
                raise Exception("Homebrew package manager not found")
        elif os_type == "linux":
            package_managers = {
                'apt-get': ['sudo', 'apt-get', 'update', '&&', 
                           'sudo', 'apt-get', 'install', '-y', 'ffmpeg'],
                'dnf': ['sudo', 'dnf', 'install', '-y', 'ffmpeg'],
                'pacman': ['sudo', 'pacman', '-S', '--noconfirm', 'ffmpeg'],
                'zypper': ['sudo', 'zypper', 'install', '-y', 'ffmpeg']
            }
            
            for pm, cmd in package_managers.items():
                if shutil.which(pm):
                    subprocess.check_call(cmd)
                    return
                    
            raise Exception("No supported package manager found")

    @staticmethod
    def _show_manual_install_instructions():
        """Show instructions for manual installation."""
        print("\nTry installing manually with either:")
        print("1. pip install yt-dlp --break-system-packages")
        print("2. pip install yt-dlp --user")
        print("3. Create and use a virtual environment first")

class Downloader:
    """
    Handles video and playlist downloads with progress tracking.
    """
    def __init__(self):
        self.progress_bars = {}
        self.start_times = {}

    def download_hook(self, d: Dict[str, Any]):
        """
        Progress hook for yt-dlp downloads.
        Handles both download progress and completion status.
        """
        if d['status'] == 'downloading':
            filename = os.path.basename(d.get('filename', ''))
            if filename:
                # Initialize progress tracking for new downloads
                if filename not in self.progress_bars:
                    self.start_times[filename] = time.time()
                    total_bytes = d.get('total_bytes', 0)
                self.progress_bars[filename] = ProgressBar(
                    total_bytes,
                    prefix=f"{Colors.CYAN}↓{Colors.RESET} {filename[:40]}..."
                )

                downloaded_bytes = d.get('downloaded_bytes', 0)
                speed = d.get('speed', 0)
                
                # Update progress bar
                progress_str = self.progress_bars[filename].update(downloaded_bytes)
                speed_str = f" @ {ProgressBar._format_size(speed)}/s" if speed else ""
                sys.stdout.write(f"{progress_str}{speed_str}")
                sys.stdout.flush()

        elif d['status'] == 'finished':
            filename = os.path.basename(d.get('filename', ''))
            if filename in self.start_times:
                duration = time.time() - self.start_times[filename]
                sys.stdout.write('\r\033[K')
                print(f"\r{Colors.GREEN}✓ {filename} downloaded in "
                      f"{ProgressBar._format_time(duration)}{Colors.RESET}")
                del self.progress_bars[filename]
                del self.start_times[filename]
                sys.stdout.flush()

    def download_playlist(self, playlist_url: str, output_dir: str = 'downloads',
                         format_choice: str = '1'):
        """
        Download a complete YouTube playlist.
        
        Args:
            playlist_url: URL of the playlist
            output_dir: Directory to save downloaded files
            format_choice: Quality/format selection for download
        """
        from yt_dlp import YoutubeDL
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        format_options = self._get_format_options(format_choice)
        ydl_opts = {
            'outtmpl': os.path.join(output_dir, '%(playlist)s', '%(title)s.%(ext)s'),
            'ignoreerrors': True,
            'noplaylist': False,
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [self.download_hook],
            'no_color': True,
            'extract_flat': True,
            'logger': self._get_quiet_logger()
        }
        ydl_opts.update(format_options)

        try:
            print(f"\n{Colors.CYAN}📥 Initializing playlist download...{Colors.RESET}")
            with YoutubeDL(ydl_opts) as ydl:
                # First pass: get playlist info
                info = ydl.extract_info(playlist_url, download=False)
                playlist_title = info.get('title', 'Playlist')
                video_count = len(info['entries'])
                
                print(f"\n{Colors.CYAN}📑 Playlist: {Colors.RESET}{playlist_title}")
                print(f"{Colors.CYAN}📊 Total videos: {Colors.RESET}{video_count}\n")
                
                # Second pass: actual download
                ydl_opts['extract_flat'] = False
                with YoutubeDL(ydl_opts) as ydl_download:
                    ydl_download.download([playlist_url])

            print(f"\n{Colors.GREEN}✨ Playlist download completed successfully!{Colors.RESET}")
            print(f"{Colors.CYAN}📂 Files saved in: {Colors.RESET}"
                  f"{os.path.abspath(output_dir)}\n")

        except Exception as e:
            print(f'\n{Colors.RED}❌ Error downloading playlist: {str(e)}{Colors.RESET}')
            raise

    def download_single_video(self, video_url: str, output_dir: str = 'downloads',
                            format_choice: str = '1'):
        """
        Download a single YouTube video.
        
        Args:
            video_url: URL of the video
            output_dir: Directory to save downloaded file
            format_choice: Quality/format selection for download
        """
        from yt_dlp import YoutubeDL
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        format_options = self._get_format_options(format_choice)
        ydl_opts = {
            'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
            'ignoreerrors': True,
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [self.download_hook],
            'no_color': True,
            'logger': self._get_quiet_logger()
        }
        ydl_opts.update(format_options)

        try:
            print(f"\n{Colors.CYAN}📥 Initializing video download...{Colors.RESET}")
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                video_title = info.get('title', 'Video')
                print(f"\n{Colors.CYAN}🎬 Video: {Colors.RESET}{video_title}")
                ydl.download([video_url])

            print(f"\n{Colors.GREEN}✨ Video download completed successfully!{Colors.RESET}")
            print(f"{Colors.CYAN}📂 File saved in: {Colors.RESET}"
                  f"{os.path.abspath(output_dir)}\n")

        except Exception as e:
            print(f'\n{Colors.RED}❌ Error downloading video: {str(e)}{Colors.RESET}')
            raise

    @staticmethod
    def _get_format_options(choice: str) -> Dict[str, Any]:
        """Get format options based on user selection."""
        formats = {
            '1': {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'format_note': 'Best Quality Video'
            },
            '2': {
                'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/'
                         'best[height<=720][ext=mp4]/best',
                'format_note': '720p Video'
            },
            '3': {
                'format': 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/'
                         'best[height<=480][ext=mp4]/best',
                'format_note': '480p Video'
            },
            '4': {
                'format': 'bestaudio[ext=m4a]/bestaudio/best',
                'format_note': 'Best Quality Audio',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'm4a',
                    'preferredquality': '192',
                }]
            },
            '5': {
                'format': 'worstaudio/worst',
                'format_note': 'Medium Quality Audio',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'm4a',
                    'preferredquality': '128',
                }]
            }
        }
        return formats.get(choice, formats['1'])

    @staticmethod
    def _get_quiet_logger():
        """Create a quiet logger for yt-dlp."""
        return type('QuietLogger', (), {
            'debug': lambda *args, **kw: None,
            'warning': lambda *args, **kw: None,
            'error': lambda *args, **kw: None,
        })()

def main():
    """Main program entry point."""
    # Initialize components
    spinner = Spinner()
    console = Console()
    downloader = Downloader()
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        print(f"\n\n{Colors.YELLOW}👋 Download canceled. Goodbye!{Colors.RESET}\n")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Show banner and check dependencies
    console.print_banner()
    SystemManager.install_dependencies(spinner)
    print(f"\n{Colors.GREEN}✓ System ready!{Colors.RESET}")
    
    while True:
        print(f"\n{Colors.gradient('═' * 50, (100, 200, 255), (150, 100, 255))}")
        
        # Main menu options
        download_options = [
            ('playlist', '📋 Playlist Download'),
            ('single', '🎥 Single Video Download'),
            ('exit', '🚪 Exit')
        ]
        
        choice = console.create_menu("Download Type", download_options)
        
        if choice == '3':  # Exit option
            print(f"\n{Colors.GREEN}👋 Thanks for using YtDorn3!{Colors.RESET}\n")
            break
            
        # Get URL and validate
        url = input(f"\n{Colors.CYAN}🔗 Enter URL: {Colors.RESET}").strip()
        if not url:
            print(f"{Colors.RED}Please enter a valid URL.{Colors.RESET}")
            continue
            
        # Validate URL format
        is_playlist = 'playlist' in url or 'list=' in url
        if choice == '1' and not is_playlist:
            print(f"\n{Colors.YELLOW}⚠️  This appears to be a single video URL. "
                  f"Would you like to:{Colors.RESET}")
            options = [
                ('single', 'Download as single video'),
                ('new', 'Enter a different URL')
            ]
            subchoice = console.create_menu("URL Type", options)
            if subchoice == '2':
                continue
            choice = '2'
        elif choice == '2' and is_playlist:
            print(f"\n{Colors.YELLOW}⚠️  This appears to be a playlist URL. "
                  f"Would you like to:{Colors.RESET}")
            options = [
                ('playlist', 'Download entire playlist'),
                ('new', 'Enter a different URL')
            ]
            subchoice = console.create_menu("URL Type", options)
            if subchoice == '2':
                continue
            choice = '1'
        
        # Get output directory
        output_dir = input(f"{Colors.CYAN}📁 Enter output directory "
                         f"(press Enter for 'downloads'): {Colors.RESET}").strip()
        if not output_dir:
            output_dir = 'downloads'
        
        # Quality options menu
        quality_options = [
            ('best', '🎥 Best Quality Video (1080p or best available)'),
            ('720p', '🎥 Medium Quality Video (720p)'),
            ('480p', '🎥 Low Quality Video (480p)'),
            ('audio-high', '🎵 Audio Only (Best Quality)'),
            ('audio-medium', '🎵 Audio Only (Medium Quality)')
        ]
        format_choice = console.create_menu("Quality Options", quality_options)
        
        try:
            if choice == '1':
                downloader.download_playlist(url, output_dir, format_choice)
            else:
                downloader.download_single_video(url, output_dir, format_choice)
        except Exception as e:
            print(f"{Colors.RED}An error occurred: {str(e)}{Colors.RESET}")
            continue
        
        # Ask to download another
        again = input(f"\n{Colors.CYAN}🔄 Download another video/playlist? (y/n): "
                     f"{Colors.RESET}").strip().lower()
        if again != 'y':
            print(f"\n{Colors.GREEN}👋 Thanks for using YtDorn3!{Colors.RESET}\n")
            break

if __name__ == "__main__":
    main()
