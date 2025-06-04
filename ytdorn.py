#!/usr/bin/env python3
"""
YtDorn v0.1.2 - Super Powerful YouTube Downloader
Created by: 0xb0rn3
Advanced CLI tool for comprehensive YouTube content downloading with modern UI
"""

import sys
import platform
import subprocess
import os
import json
import asyncio
import concurrent.futures
from typing import Dict, Any, Optional, List, Tuple
import shutil
from datetime import datetime
import time
import threading
from pathlib import Path
import signal
import re
import argparse
from urllib.parse import urlparse, parse_qs
import logging

class Colors:
    """Enhanced color management with modern terminal styling"""
    # Core colors
    PRIMARY = '\033[38;2;64;224;255m'      # Bright cyan
    SECONDARY = '\033[38;2;255;100;255m'   # Bright magenta
    SUCCESS = '\033[38;2;0;255;127m'       # Bright green
    WARNING = '\033[38;2;255;191;0m'       # Bright yellow
    ERROR = '\033[38;2;255;69;58m'         # Bright red
    INFO = '\033[38;2;175;175;255m'        # Light blue
    MUTED = '\033[38;2;128;128;128m'       # Gray

    # Text styles
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'

    # Special effects
    GLOW = '\033[5m'
    REVERSE = '\033[7m'

    @staticmethod
    def rgb(r: int, g: int, b: int) -> str:
        return f'\033[38;2;{r};{g};{b}m'

    @staticmethod
    def gradient_text(text: str, color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> str:
        """Create smooth color gradient across text"""
        if not text.strip():
            return text

        result = ""
        text_length = len([c for c in text if c.strip('\r\n\t ')]) # More robust stripping for length
        char_index = 0

        for char in text:
            if char.strip('\r\n\t '):
                progress = char_index / max(text_length - 1, 1)
                r = int(color1[0] + (color2[0] - color1[0]) * progress)
                g = int(color1[1] + (color2[1] - color1[1]) * progress)
                b = int(color1[2] + (color2[2] - color1[2]) * progress)
                result += Colors.rgb(r, g, b) + char
                char_index += 1
            else:
                result += char
        return result + Colors.RESET

class ModernSpinner:
    """Advanced spinner with multiple animation styles"""

    STYLES = {
        'dots': ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'],
        'pulse': ['●', '○', '◍', '◌'],
        'wave': [' ', '▃', '▄', '▅', '▆', '▇', '█', '▇', '▆', '▅', '▄', '▃'],
        'arrow': ['←', '↖', '↑', '↗', '→', '↘', '↓', '↙'],
    }

    def __init__(self, style='dots'):
        self.frames = self.STYLES.get(style, self.STYLES['dots'])
        self.stop_event = threading.Event()
        self.thread = None
        self.message = ""

    def animate(self):
        """Run the spinner animation"""
        frame_index = 0
        while not self.stop_event.is_set():
            frame = self.frames[frame_index % len(self.frames)]
            sys.stdout.write(f'\r{Colors.PRIMARY}{frame}{Colors.RESET} {self.message}')
            sys.stdout.flush()
            time.sleep(0.1)
            frame_index += 1

    def start(self, message: str):
        """Start spinner with message"""
        self.message = message
        self.stop_event.clear()
        self.thread = threading.Thread(target=self.animate, daemon=True)
        self.thread.start()

    def stop(self, final_message: str = None):
        """Stop spinner and optionally show final message"""
        self.stop_event.set()
        if self.thread:
            self.thread.join()
        sys.stdout.write('\r\033[K') # Clear the spinner line
        if final_message:
            print(final_message)

class AdvancedProgressBar:
    """Modern progress bar with detailed statistics"""

    def __init__(self, total: int, description: str = "", width: int = 40):
        self.total = total
        self.description = description
        self.width = width
        self.start_time = time.time()
        self.current = 0
        self.speed_samples: List[Tuple[float, int]] = [] # time, bytes
        self.last_update = time.time()

    def update(self, current: int, extra_info: str = "") -> str:
        """Update progress with enhanced statistics"""
        self.current = current
        now = time.time()

        # Calculate speed with smoothing
        if now - self.last_update > 0.5:  # Update speed every 0.5 seconds
            if self.speed_samples: # Ensure there's a previous sample to compare against
                # Speed = (change in bytes) / (change in time)
                # Only add if current > previous sample bytes to avoid negative speed on retries/corrections
                if current > self.speed_samples[-1][1] and now > self.speed_samples[-1][0]:
                     speed = (current - self.speed_samples[-1][1]) / (now - self.speed_samples[-1][0])
                     self.speed_samples.append((now, current, speed)) # Store time, current_bytes, speed
                elif now > self.start_time: # Fallback if something is odd with samples
                     speed = current / (now - self.start_time)
                     self.speed_samples.append((now, current, speed))
            elif now > self.start_time: # First sample or restart
                speed = current / (now - self.start_time)
                self.speed_samples.append((now, current, speed)) # Store time, current_bytes, speed
            
            if len(self.speed_samples) > 10:  # Keep last 10 samples
                self.speed_samples.pop(0)
            self.last_update = now


        # Calculate percentage and bar
        percentage = (current / self.total * 100) if self.total > 0 else 0
        filled = int(self.width * current / self.total) if self.total > 0 else 0

        # Create modern progress bar with gradient
        bar = ''
        for i in range(filled):
            intensity = min(255, 50 + (i * 205 // self.width))
            bar += Colors.rgb(intensity, 100, 255) + '█'

        if filled < self.width:
            bar += Colors.MUTED + '░' * (self.width - filled)
        bar += Colors.RESET

        # Calculate ETA
        elapsed = now - self.start_time
        eta_seconds = 0
        if self.speed_samples and self.total > 0 and current > 0:
            # Use average speed from recent samples for ETA
            recent_speeds = [s[2] for s in self.speed_samples if len(s) > 2 and s[2] > 0]
            if recent_speeds:
                avg_speed = sum(recent_speeds) / len(recent_speeds)
                if avg_speed > 0:
                    eta_seconds = (self.total - current) / avg_speed
        elif current > 0 and elapsed > 0 and self.total > 0: # Fallback if no speed samples
             rate = current / elapsed
             if rate > 0:
                 eta_seconds = (self.total - current) / rate

        eta = self._format_duration(eta_seconds) if eta_seconds > 0 else "--:--"


        # Format sizes
        current_size = self._format_bytes(float(current))
        total_size = self._format_bytes(float(self.total))

        # Get current speed
        current_speed_str = ""
        if self.speed_samples and len(self.speed_samples[-1]) > 2:
            # Use the latest calculated speed
            speed_val = self.speed_samples[-1][2]
            if speed_val > 0:
                 current_speed_str = f" @ {self._format_bytes(speed_val)}/s"
        elif extra_info: # Fallback to yt-dlp provided speed if available
            current_speed_str = extra_info


        return (f"\r{Colors.PRIMARY}▶{Colors.RESET} {self.description[:30]:<30} "
                f"[{bar}] {percentage:5.1f}% "
                f"({current_size}/{total_size}){current_speed_str} "
                f"ETA: {eta} ") # Removed extra_info from here as it's part of current_speed_str

    @staticmethod
    def _format_bytes(bytes_val: float) -> str:
        """Format bytes with appropriate units"""
        if bytes_val < 0: bytes_val = 0.0
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024:
                return f"{bytes_val:.1f}{unit}"
            bytes_val /= 1024
        return f"{bytes_val:.1f}PB"

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """Format duration in human readable format"""
        if seconds < 0: seconds = 0
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds // 60)}m {int(seconds % 60)}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"

class ModernUI:
    """Advanced terminal UI with modern design elements"""

    @staticmethod
    def print_banner():
        """Display enhanced banner with version info"""
        banner_text = """
╭─────────────────────────────────────────────╮
│  ██╗   ██╗████████╗██████╗  ██████╗ ██████╗ │
│  ╚██╗ ██╔╝╚══██╔══╝██╔══██╗██╔═══██╗██╔══██╗│
│   ╚████╔╝    ██║   ██║  ██║██║   ██║██████╔╝│
│    ╚██╔╝     ██║   ██║  ██║██║   ██║██╔══██╗│
│     ██║      ██║   ██████╔╝╚██████╔╝██║  ██║│
│     ╚═╝      ╚═╝   ╚═════╝  ╚═════╝ ╚═╝  ╚═╝│
╰─────────────────────────────────────────────╯"""

        print(Colors.gradient_text(banner_text, (64, 224, 255), (255, 100, 255)))
        print(f"\n{Colors.PRIMARY}{Colors.BOLD}YtDorn v0.1.2{Colors.RESET} {Colors.MUTED}by 0xb0rn3{Colors.RESET}")
        print(f"{Colors.INFO}Super Powerful YouTube Downloader{Colors.RESET}")
        print(f"{Colors.MUTED}https://github.com/0xb0rn3/YtDorn {Colors.RESET}") # Example URL
        print(Colors.gradient_text('═' * 50, (64, 224, 255), (255, 100, 255)))

    @staticmethod
    def create_interactive_menu(title: str, options: List[Tuple[str, str, str]],
                                show_shortcuts: bool = True) -> str:
        """Create modern interactive menu with shortcuts and descriptions"""
        print(f"\n{Colors.PRIMARY}{Colors.BOLD}┌─ {title} ─┐{Colors.RESET}")

        for i, (key, title_text, description) in enumerate(options, 1):
            icon = key if len(key) == 1 else str(i)
            shortcut = f"[{icon}]" if show_shortcuts else f"[{i}]"
            print(f"{Colors.INFO}{shortcut:<4}{Colors.RESET} {title_text}")
            if description:
                print(f"      {Colors.MUTED}{description}{Colors.RESET}")

        print(f"{Colors.PRIMARY}└{'─' * (len(title) + 4)}┘{Colors.RESET}")

        while True:
            prompt = f"\n{Colors.PRIMARY}❯{Colors.RESET} Select option: "
            choice = input(prompt).strip().lower()

            # Check for direct key match or number
            for i, (key, _, _) in enumerate(options, 1):
                if choice == key.lower() or choice == str(i):
                    return str(i) # Return the numeric index as string

            print(f"{Colors.ERROR}Invalid selection. Please try again.{Colors.RESET}")

    @staticmethod
    def get_user_input(prompt: str, default: Optional[str] = None, validator=None) -> str:
        """Enhanced input with validation and defaults"""
        display_default = f" ({default})" if default else ""
        full_prompt = f"{Colors.PRIMARY}❯{Colors.RESET} {prompt}{Colors.MUTED}{display_default}{Colors.RESET}: "

        while True:
            value = input(full_prompt).strip()
            if not value and default is not None: # Check if default is not None explicitly
                return default
            if not value: # If no default and no input
                print(f"{Colors.ERROR}This field is required.{Colors.RESET}")
                continue
            if validator and not validator(value):
                # Validator should print its own error message for specificity
                # print(f"{Colors.ERROR}Invalid input. Please try again.{Colors.RESET}")
                continue
            return value

    @staticmethod
    def show_info_panel(title: str, items: Dict[str, str]):
        """Display information in a modern panel format"""
        if not items: return # Don't print empty panel

        max_key_length = max(len(key) for key in items.keys()) if items else 0
        
        title_bar_length = max(max_key_length + 20, len(title) + 4)


        print(f"\n{Colors.INFO}┌─ {title} {'─' * (title_bar_length - len(title) - 3)}┐")
        for key, value in items.items():
            print(f"{Colors.INFO}│{Colors.RESET} {key:<{max_key_length}} : {Colors.PRIMARY}{value}{Colors.RESET}")
        print(f"{Colors.INFO}└{'─' * title_bar_length}┘{Colors.RESET}")


class DependencyManager:
    """Advanced dependency management with better error handling"""

    @staticmethod
    def check_system_dependencies() -> Dict[str, bool]:
        """Comprehensive dependency check"""
        deps = {}
        deps['yt-dlp'] = shutil.which('yt-dlp') is not None
        if not deps['yt-dlp']:
            try:
                import yt_dlp
                deps['yt-dlp'] = True
            except ImportError:
                deps['yt-dlp'] = False # Explicitly set to False if both fail

        deps['ffmpeg'] = shutil.which('ffmpeg') is not None
        return deps

    @staticmethod
    def get_installation_instructions(missing_deps: List[str]) -> Dict[str, str]:
        """Provide installation instructions for missing dependencies"""
        instructions = {}
        for dep in missing_deps:
            if dep == 'yt-dlp':
                instructions[dep] = (
                    "Install yt-dlp using one of these methods:\n"
                    "  pip install yt-dlp\n"
                    "  Or visit: https://github.com/yt-dlp/yt-dlp#installation"
                )
            elif dep == 'ffmpeg':
                instructions[dep] = (
                    "FFmpeg is recommended for full functionality (e.g., audio extraction, format conversion).\n"
                    "  Windows: winget install ffmpeg OR choco install ffmpeg\n"
                    "  MacOS: brew install ffmpeg\n"
                    "  Linux: sudo apt install ffmpeg OR sudo dnf install ffmpeg OR sudo pacman -S ffmpeg\n"
                    "  Or download from: https://ffmpeg.org/download.html"
                )
        return instructions

    @staticmethod
    def install_missing_dependencies(spinner: ModernSpinner) -> bool:
        """Install missing dependencies with progress feedback"""
        spinner.start("Checking system dependencies...")
        deps_status = DependencyManager.check_system_dependencies()
        time.sleep(0.5) # Simulate check time
        
        missing_deps = [dep for dep, found in deps_status.items() if not found]

        if not missing_deps:
            spinner.stop(f"{Colors.SUCCESS}✓ System dependencies are satisfied.{Colors.RESET}")
            return True
        
        spinner.stop(f"{Colors.WARNING}⚠ Some dependencies are missing: {', '.join(missing_deps)}{Colors.RESET}")

        instructions = DependencyManager.get_installation_instructions(missing_deps)
        if instructions:
            print(f"{Colors.INFO}Installation instructions:{Colors.RESET}")
            for dep, instruction in instructions.items():
                print(f"{Colors.PRIMARY}{dep}:{Colors.RESET}\n{Colors.MUTED}{instruction}{Colors.RESET}")

        if 'yt-dlp' in missing_deps:
            print(f"{Colors.WARNING}Yt-dlp is essential. Attempting to install...{Colors.RESET}")
            spinner.start("Installing yt-dlp via pip...")
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", "yt-dlp", "--upgrade"
                    # Consider adding --break-system-packages if appropriate for the target environment
                    # but it's generally better if the user manages their Python environment.
                ], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE) # Use PIPE for stderr to check output
                # Verify after install attempt
                if shutil.which('yt-dlp') or hasattr(__import__('yt_dlp'), '__version__'):
                    spinner.stop(f"{Colors.SUCCESS}✓ yt-dlp installed successfully.{Colors.RESET}")
                    deps_status['yt-dlp'] = True
                else:
                    raise subprocess.CalledProcessError(1, "pip install yt-dlp (verification failed)")
            except subprocess.CalledProcessError as e:
                spinner.stop(f"{Colors.ERROR}✗ Failed to install yt-dlp automatically. Error: {e.stderr.decode() if e.stderr else str(e)}{Colors.RESET}\n"
                             f"{Colors.WARNING}Please install it manually.{Colors.RESET}")
                return False # yt-dlp is critical
            except FileNotFoundError: # sys.executable or pip not found
                 spinner.stop(f"{Colors.ERROR}✗ Python/pip not found correctly. Cannot auto-install yt-dlp.{Colors.RESET}")
                 return False


        if not deps_status.get('ffmpeg', False): # If ffmpeg was initially missing
            # We don't attempt to auto-install ffmpeg due to complexity and permissions.
            # The instructions are already printed.
            print(f"{Colors.WARNING}⚠ FFmpeg not found. Some features like audio extraction/conversion might be limited.{Colors.RESET}")

        # Final check if critical yt-dlp is now available
        return deps_status.get('yt-dlp', False)


class SuperDownloader:
    """Advanced downloader with comprehensive YouTube support"""

    def __init__(self):
        self.progress_bars: Dict[str, AdvancedProgressBar] = {}
        self.download_stats: Dict[str, Dict[str, Any]] = {}
        # self.concurrent_downloads = 3 # Not directly used by yt-dlp in this script structure

    def download_hook(self, d: Dict[str, Any]):
        """Enhanced progress hook with detailed tracking"""
        # filename in hook can be temp filename, use info_dict for final name if needed
        if d['status'] == 'error':
            filename = d.get('filename', 'Unknown file')
            base_filename = os.path.basename(filename).replace('.temp', '') # Clean temp extension
            sys.stdout.write('\r\033[K') # Clear line
            print(f"{Colors.ERROR}✗ Error downloading {base_filename}: {d.get('error', 'Unknown error')}{Colors.RESET}")
            if base_filename in self.progress_bars:
                del self.progress_bars[base_filename]
            if base_filename in self.download_stats:
                del self.download_stats[base_filename]
            return


        # Try to get a more stable filename from info_dict if available
        info_dict_filename = d.get('info_dict', {}).get('filename')
        if info_dict_filename:
            filename = info_dict_filename
        else:
            filename = d.get('filename', 'Unknown')

        base_filename = os.path.basename(filename).replace('.temp', '') # Clean .temp extension

        if d['status'] == 'downloading':
            if base_filename not in self.progress_bars:
                total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                if total_bytes == 0: # Handle cases where total_bytes is missing (e.g. live streams, some formats)
                    total_bytes = d.get('downloaded_bytes', 0) # Set total to current if unknown, bar will be full
                
                self.progress_bars[base_filename] = AdvancedProgressBar(
                    int(total_bytes), # Ensure it's an int
                    base_filename[:25] # Truncate description
                )
                self.download_stats[base_filename] = {'start_time': time.time(), 'total_bytes': int(total_bytes)}

            downloaded_bytes = d.get('downloaded_bytes', 0)
            speed = d.get('speed', 0) # yt-dlp provides speed in bytes/sec

            extra_info_speed = ""
            if speed: # yt-dlp speed
                extra_info_speed = f"{AdvancedProgressBar._format_bytes(speed)}" # No "/s" needed, handled by progress bar

            progress_line = self.progress_bars[base_filename].update(int(downloaded_bytes), extra_info_speed)
            sys.stdout.write(progress_line)
            sys.stdout.flush()

        elif d['status'] == 'finished':
            if base_filename in self.progress_bars:
                total_bytes = self.download_stats[base_filename]['total_bytes']
                # Ensure final update shows 100%
                final_progress = self.progress_bars[base_filename].update(total_bytes, "")
                sys.stdout.write(final_progress + "\n") # Move to next line after completion
                sys.stdout.flush()

                duration = time.time() - self.download_stats[base_filename]['start_time']
                # print(f"{Colors.SUCCESS}✓ {base_filename} completed in " # Replaced by bar's final print
                #       f"{AdvancedProgressBar._format_duration(duration)}{Colors.RESET}")
                del self.progress_bars[base_filename]
                del self.download_stats[base_filename]
            else: # If no progress bar (e.g. very small file or already downloaded)
                sys.stdout.write('\r\033[K') # Clear any partial line
                print(f"{Colors.SUCCESS}✓ {base_filename} processed.{Colors.RESET}")


    def get_video_info(self, url: str) -> Dict[str, Any]:
        """Extract comprehensive video information"""
        from yt_dlp import YoutubeDL

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': 'in_playlist', # Extract flat for playlists, full for single videos
            'skip_download': True, # Ensure no download happens here
        }

        with YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                if not info: # Should not happen if no exception, but as safeguard
                    raise Exception("No information extracted.")
                return self._process_video_info(info)
            except Exception as e:
                # More specific error from yt-dlp often in e.exc_info[1] or e.args
                error_message = str(e)
                if hasattr(e, 'exc_info') and e.exc_info and len(e.exc_info) > 1:
                    # Try to get a more specific yt-dlp error message
                    yt_dlp_error = str(e.exc_info[1])
                    if 'Unsupported URL' in yt_dlp_error or 'valid URL' in yt_dlp_error:
                         error_message = f"Invalid or unsupported URL: {url}"
                    elif 'Unable to extract' in yt_dlp_error:
                         error_message = f"Could not extract info from URL (may be private or unavailable): {yt_dlp_error}"
                    else:
                         error_message = f"yt-dlp error: {yt_dlp_error}"

                raise Exception(f"Could not extract video info: {error_message}")


    def _process_video_info(self, info: Dict[str, Any]) -> Dict[str, Any]:
        """Process and clean video information"""
        processed = {}
        is_playlist_or_channel = info.get('_type') == 'playlist' or info.get('_type') == 'multi_video' \
                                 or 'entries' in info and info.get('entries') is not None


        if is_playlist_or_channel:
            processed['is_playlist'] = True
            processed['playlist_title'] = info.get('title', 'Unknown Playlist/Channel')
            processed['playlist_count'] = info.get('playlist_count') or len(info.get('entries', []))
            # For playlists, other details might be for the playlist itself, not a single video
            processed['title'] = processed['playlist_title'] # Use playlist title as main title
            processed['uploader'] = info.get('uploader', 'Various Artists') # Or channel name
            processed['duration'] = sum(e.get('duration', 0) for e in info.get('entries', []) if e) if info.get('entries') else 0
            processed['view_count'] = info.get('view_count', 0) # Playlist views if available
            processed['upload_date'] = info.get('upload_date', '') # Playlist creation date if available
            processed['description'] = info.get('description', '')[:200] + '...' if info.get('description') else ''
            processed['formats'] = 'N/A for playlists (per video)' # Formats are per video
            processed['is_live'] = False # Typically playlists aren't "live" in the same way
        else: # Single video
            processed['is_playlist'] = False
            processed['title'] = info.get('title', 'Unknown Video')
            processed['uploader'] = info.get('uploader', 'Unknown Uploader')
            processed['duration'] = info.get('duration', 0)
            processed['view_count'] = info.get('view_count', 0)
            processed['upload_date'] = info.get('upload_date', '')
            if processed['upload_date']:
                try:
                    processed['upload_date'] = datetime.strptime(processed['upload_date'], '%Y%m%d').strftime('%Y-%m-%d')
                except ValueError:
                    pass # Keep original if format is unexpected
            processed['description'] = info.get('description', '')[:200] + '...' if info.get('description') else ''
            processed['formats'] = len(info.get('formats', [])) if info.get('formats') else 'Unknown'
            processed['is_live'] = info.get('is_live', False)
        
        processed['original_info'] = info # Keep original for potential advanced use

        return processed

    def download_with_options(self, url: str, options: Dict[str, Any]):
        """Download with comprehensive options"""
        from yt_dlp import YoutubeDL

        # Build yt-dlp options
        ydl_opts: Dict[str, Any] = {
            'outtmpl': options.get('output_template', '%(title)s.%(ext)s'),
            'format': options.get('format', 'best'),
            'writesubtitles': options.get('subtitles', False),
            'writeautomaticsub': options.get('auto_subtitles', False) and options.get('subtitles', False), # only if writesubtitles is true
            'subtitleslangs': options.get('subtitle_langs', ['en']) if options.get('subtitles') else [],
            'writethumbnail': options.get('thumbnail', False),
            'writedescription': options.get('description_file', False), # Renamed for clarity
            'writeinfojson': options.get('metadata_json', False), # Renamed for clarity
            'ignoreerrors': options.get('ignore_errors', True), # True to continue playlist on error
            'no_warnings': True,
            'progress_hooks': [self.download_hook],
            'quiet': True, # Suppress direct yt-dlp console output, rely on hooks
            'noprogress': True, # Suppress yt-dlp's own progress bar, use ours
            'noplaylist': options.get('no_playlist', False), # If user explicitly wants to download only video from playlist URL
        }
        
        # Conditional options
        if options.get('playlist_items'):
            ydl_opts['playlist_items'] = str(options['playlist_items'])
        if options.get('date_after'):
            ydl_opts['dateafter'] = options['date_after'] # YYYYMMDD
        if options.get('match_title'):
            ydl_opts['match_filter'] = f"title ~= '(?i){options['match_title']}'" # Case-insensitive regex match

        # Add post-processors based on options
        postprocessors = []
        if options.get('extract_audio'):
            postprocessors.append({
                'key': 'FFmpegExtractAudio',
                'preferredcodec': options.get('audio_format', 'mp3'),
                'preferredquality': options.get('audio_quality', '192'), # e.g., 192 for 192k
            })

        if options.get('embed_subs') and options.get('subtitles'):
            postprocessors.append({'key': 'FFmpegEmbedSubtitle'})
        
        if options.get('embed_thumbnail') and options.get('thumbnail'):
            postprocessors.append({
                'key': 'FFmpegMetadata',
                'add_metadata': True, # Generic, but used by yt-dlp to embed thumbnail if downloaded
            })
            postprocessors.append({'key': 'EmbedThumbnail'}) # yt-dlp's dedicated thumbnail embedder


        if postprocessors:
            ydl_opts['postprocessors'] = postprocessors

        try:
            with YoutubeDL(ydl_opts) as ydl:
                return_code = ydl.download([url])
                if return_code != 0 and not options.get('ignore_errors', True):
                    # This path might not be hit often if ignoreerrors is True and hook handles errors
                    print(f"{Colors.ERROR}Download failed with yt-dlp error code: {return_code}{Colors.RESET}")
                    return False
            return True # Assume success if no exceptions raised and ignoreerrors is on
        except Exception as e:
            # This catches broader issues, hook handles per-file errors
            print(f"{Colors.ERROR}Download execution failed: {str(e)}{Colors.RESET}")
            return False

    @staticmethod
    def get_format_options() -> List[Tuple[str, str, str]]:
        """Get available format options with descriptions"""
        return [
            ('best', '🎬 Best Overall', 'Highest available video & audio (MP4 preferred)'),
            ('bestvideo', '🏆 Best Video Only', 'Highest quality video stream (no audio)'),
            ('bestaudio', '🎧 Best Audio Only', 'Highest quality audio stream'),
            ('mp4_1080p', '📺 1080p HD (MP4)', 'Full HD quality (H.264, AAC)'),
            ('mp4_720p', '📹 720p HD (MP4)', 'HD quality (H.264, AAC)'),
            ('mp3', '🎶 MP3 Audio', 'Extract audio and convert to MP3 (192kbps)'),
            ('m4a', '🎵 M4A Audio (AAC)', 'Extract audio in M4A format (best quality AAC)'),
            ('custom', '⚙ Custom yt-dlp format', 'Specify custom format string'),
        ]

    @staticmethod
    def create_advanced_options_menu(ui: ModernUI, video_info: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive options selection menu."""
        options: Dict[str, Any] = {}
        is_playlist = video_info.get('is_playlist', False)
        config = ConfigManager.load_config() # Load defaults

        if is_playlist:
            count = video_info.get('playlist_count', 'multiple')
            print(f"{Colors.INFO}ℹ️ This is a playlist/channel with {count} videos. "
                  f"Options will apply to all items.{Colors.RESET}")
            # Ask if user wants to download the playlist as a whole or select a single video from it (if applicable)
            # yt-dlp's default is to download all if a playlist URL is given without --no-playlist
            # options['no_playlist'] = False # Default to download all

        # --- Output Directory ---
        current_dir_display = os.getcwd()
        default_output_val = config.get('default_output_dir', str(Path("downloads").resolve()))
        
        user_path_input = ui.get_user_input(
            f"Output directory (current: {current_dir_display})",
            default=default_output_val,
            validator=lambda x: Path(x).parent.exists() or Path(x).parent.is_dir() if not Path(x).exists() and Path(x).is_absolute() 
                                else True # Basic check for parent existence for new dirs
        )
        resolved_path = Path(user_path_input).resolve()
        options['output_dir'] = str(resolved_path)
        # Directory creation is handled in main() before download starts
        print(f"{Colors.MUTED}Files will be saved into: {options['output_dir']}{Colors.RESET}")


        # --- Format Selection ---
        format_menu_options = SuperDownloader.get_format_options()
        format_choice_idx_str = ui.create_interactive_menu("Format Selection", format_menu_options)
        # format_choice_key = format_menu_options[int(format_choice_idx_str) - 1][0]
        
        # Map choice index back to the key ('best', 'mp3', etc.)
        # Ensure format_choice_idx_str is valid before indexing
        try:
            selected_format_option_idx = int(format_choice_idx_str) -1
            if 0 <= selected_format_option_idx < len(format_menu_options):
                 format_choice_key = format_menu_options[selected_format_option_idx][0]
            else: # Should not happen with create_interactive_menu validation
                format_choice_key = 'best' # Fallback
        except ValueError:
            format_choice_key = 'best' # Fallback


        format_map = {
            'best': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best', # Prioritize MP4 container
            'bestvideo': 'bestvideo',
            'bestaudio': 'bestaudio/best',
            'mp4_1080p': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]',
            'mp4_720p': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]',
            'mp3': 'bestaudio/best', # Actual conversion handled by postprocessor
            'm4a': 'bestaudio[ext=m4a]/bestaudio', # Prefer m4a directly
        }

        if format_choice_key == 'custom':
            options['format'] = ui.get_user_input("Enter custom yt-dlp format string", default="best")
        else:
            options['format'] = format_map.get(format_choice_key, 'best')

        # Audio specific options if an audio format was chosen
        if format_choice_key in ['mp3', 'm4a', 'bestaudio']:
            options['extract_audio'] = True
            if format_choice_key == 'mp3':
                options['audio_format'] = 'mp3'
                options['audio_quality'] = ui.get_user_input("MP3 Quality (e.g., 128, 192, 320)", default="192", validator=lambda x: x.isdigit())
            elif format_choice_key == 'm4a':
                options['audio_format'] = 'm4a' # yt-dlp will pick best quality m4a by default for bestaudio[ext=m4a]
            # For 'bestaudio', audio_format can be other types like opus, vorbis. We don't force codec here.
        else: # Video format or best overall
            options['extract_audio'] = False


        # --- Additional Options ---
        # Subtitles
        sub_choice = ui.create_interactive_menu("Subtitle Options", [
            ('y', 'Yes, download subtitles', 'If available, .srt or .vtt'),
            ('n', 'No subtitles', ''),
        ])
        options['subtitles'] = (sub_choice == '1') # '1' corresponds to 'y'
        if options['subtitles']:
            options['auto_subtitles'] = ui.create_interactive_menu("Auto-generated Subtitles?", [
                ('y', 'Yes, include auto-generated if manual are missing', ''),
                ('n', 'No, only manual subtitles', ''),
            ]) == '1'
            options['subtitle_langs'] = [ui.get_user_input("Subtitle language(s) (comma-separated, e.g., en,es)", default="en")]
            options['embed_subs'] = ui.create_interactive_menu("Embed Subtitles?", [
                 ('y', 'Yes, embed into video file (if supported)', 'Requires FFmpeg'),
                 ('n', 'No, save as separate file', ''),
            ]) == '1'


        # Thumbnail
        thumb_choice = ui.create_interactive_menu("Thumbnail Options", [
            ('y', 'Yes, download thumbnail', 'Saves as .jpg or .webp'),
            ('n', 'No thumbnail', '')
        ])
        options['thumbnail'] = (thumb_choice == '1')
        if options['thumbnail'] and not options.get('extract_audio', False): # Embedding usually for video/audio files
            options['embed_thumbnail'] = ui.create_interactive_menu("Embed Thumbnail?", [
                 ('y', 'Yes, embed into media file (if supported)', 'Requires FFmpeg'),
                 ('n', 'No, save as separate file', ''),
            ]) == '1'


        # Metadata and Description files
        meta_choice = ui.create_interactive_menu("Extra Files Options", [
            ('j', 'JSON Info', 'Save full video metadata to a .json file'),
            ('d', 'Description File', 'Save video description to a .description file'),
            ('n', 'None', 'Skip these extra files')
        ])
        if meta_choice == '1': options['metadata_json'] = True
        if meta_choice == '2': options['description_file'] = True
        # If 'n' (index '3'), defaults (False) are kept.

        if is_playlist:
            playlist_opts_choice = ui.create_interactive_menu("Playlist Specific Options", [
                ('all', "Download all items", "Default behavior for playlists."),
                ('items', "Specify item numbers/range", "e.g., 1,3,5-7"),
                ('skip', "Skip playlist options", "Use defaults")
            ])
            if playlist_opts_choice == '2': # 'items'
                options['playlist_items'] = ui.get_user_input("Playlist items (e.g., 1-5,8,10)", default="all")
            # 'all' or 'skip' implies default yt-dlp behavior (download all if not 'no_playlist')

        # --- Output Template ---
        # Default template: title.ext. Can be customized further.
        # Using a more robust title, limited in length. %(title).100s truncates title to 100 chars.
        # %(playlist_index)s- %(title)s for playlists is common.
        # yt-dlp default outtmpl is `%(title)s [%(id)s].%(ext)s`
        # We'll use a simpler one, but easily customizable if we expose this later.
        filename_pattern = "%(title).150s.%(ext)s"
        if is_playlist and options.get('playlist_items', 'all') == 'all' and not options.get('no_playlist'):
             # Add playlist index if it's a playlist and we are downloading items from it
             filename_pattern = "%(playlist_index)s - %(title).150s.%(ext)s"
        
        options['output_template'] = str(Path(options['output_dir']) / filename_pattern)

        return options

def validate_url(url: str) -> bool:
    """Basic validation for YouTube URLs or common video URLs"""
    if not url or not isinstance(url, str):
        return False
    try:
        parsed = urlparse(url)
        if not all([parsed.scheme, parsed.netloc]):
            print(f"{Colors.WARNING}URL seems malformed (missing scheme or domain).{Colors.RESET}")
            return False # Basic structural check

        # Common YouTube domains
        youtube_domains = ['youtube.com', 'youtu.be', 'm.youtube.com']
        if any(domain in parsed.netloc.lower() for domain in youtube_domains):
            # More specific checks for YouTube (optional, yt-dlp is the ultimate validator)
            if 'youtube.com' in parsed.netloc.lower():
                query_params = parse_qs(parsed.query)
                if parsed.path.startswith('/watch') and 'v' in query_params: return True
                if parsed.path.startswith('/playlist') and 'list' in query_params: return True
                if parsed.path.startswith(('/channel/', '/c/', '/user/')): return True
            elif 'youtu.be' in parsed.netloc.lower() and parsed.path != '/': return True # youtu.be/VIDEOID
            # If it's a YouTube domain but doesn't match specific patterns, still let yt-dlp try
            print(f"{Colors.MUTED}URL is a YouTube domain, attempting anyway...{Colors.RESET}")
            return True

        # Generic check for other potential video platform URLs (very broad)
        # This is mostly to allow yt-dlp to try and handle it.
        if '.' in parsed.netloc and len(parsed.netloc) > 3: # Basic check for a valid-looking domain
             print(f"{Colors.MUTED}URL is not a standard YouTube URL, but attempting with yt-dlp...{Colors.RESET}")
             return True
        
        print(f"{Colors.ERROR}Invalid URL structure: {url}{Colors.RESET}")
        return False

    except Exception as e: # Catches parsing errors for completely invalid strings
        print(f"{Colors.ERROR}URL validation error: {e}{Colors.RESET}")
        return False


def main():
    """Enhanced main function with comprehensive features"""
    ui = ModernUI()
    spinner = ModernSpinner(style='dots')
    downloader = SuperDownloader() # Instance of SuperDownloader

    # Signal handler for graceful exit
    def signal_handler(signum, frame):
        print(f"\n\n{Colors.WARNING}🛑 Download interrupted by user (Ctrl+C). Exiting gracefully...{Colors.RESET}\n")
        spinner.stop() # Ensure spinner is stopped
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


    ui.print_banner()

    if not DependencyManager.install_missing_dependencies(spinner):
        # Error messages are printed by install_missing_dependencies
        sys.exit(1)

    print(f"\n{Colors.SUCCESS}🚀 System ready!{Colors.RESET}")

    while True:
        try:
            print(f"\n{Colors.gradient_text('═' * 60, (64, 224, 255), (255, 100, 255))}")

            main_options = [
                ('d', '📥 Download Content', 'Video, Playlist, or Channel URL'),
                ('i', '📊 Get Media Info', 'Fetch detailed information without downloading'),
                ('q', '🚪 Quit', 'Exit the application'),
            ]
            choice_idx_str = ui.create_interactive_menu("Main Menu", main_options)
            
            # Map choice index back to key
            user_choice = main_options[int(choice_idx_str)-1][0]


            if user_choice == 'q':  # Quit
                print(f"\n{Colors.SUCCESS}👋 Thank you for using YtDorn! Goodbye!{Colors.RESET}\n")
                break

            url_prompt = "Enter YouTube or compatible Video/Playlist/Channel URL"
            url = ""
            while not url: # Loop until a valid URL is entered or user cancels (implicitly via Ctrl+C)
                url_input = ui.get_user_input(url_prompt) # No default, validator inside loop
                if validate_url(url_input): # Basic pre-validation
                    url = url_input
                else:
                    # validate_url prints its own error if it fails strictly
                    # If it returns False without printing, means it's just a warning state.
                    # Ask user if they want to proceed with a potentially problematic URL.
                    if not any(err_kw in url_input.lower() for err_kw in ["invalid", "malformed"]): # Avoid re-prompt if truly bad
                        proceed = ui.create_interactive_menu(f"URL Validation Warning", [
                            ('y', "Proceed with this URL anyway", url_input),
                            ('n', "Re-enter URL", "")
                        ])
                        if proceed == '1': # Yes, proceed
                            url = url_input
                        # Else, loop will continue to ask for URL
                    # If validate_url printed a hard error, it won't reach here or url remains ""
            
            if not url: # Should not happen if loop is exited correctly, but as safeguard
                print(f"{Colors.WARNING}No URL provided. Returning to main menu.{Colors.RESET}")
                continue


            spinner.start("Fetching media information...")
            try:
                video_info = downloader.get_video_info(url)
                spinner.stop() # Stop before printing info
            except Exception as e:
                spinner.stop(f"{Colors.ERROR}Failed to get media info: {str(e)}{Colors.RESET}")
                continue

            # Display common info for both 'info' and 'download' paths
            info_items = {
                'Title': video_info['title'],
                'Type': 'Playlist/Channel' if video_info['is_playlist'] else 'Single Video',
            }
            if video_info['is_playlist']:
                info_items['Item Count'] = str(video_info['playlist_count'])
            else: # Single video
                info_items['Uploader'] = video_info['uploader']
                info_items['Duration'] = AdvancedProgressBar._format_duration(video_info['duration'])
            
            if not video_info['is_playlist']: # More details for single items
                info_items['Views'] = f"{video_info.get('view_count', 0):,}" if video_info.get('view_count') else 'N/A'
                info_items['Uploaded'] = video_info.get('upload_date', 'N/A')
                info_items['Formats (approx.)'] = str(video_info.get('formats', 'N/A'))
                info_items['Live?'] = 'Yes' if video_info.get('is_live', False) else 'No'

            ui.show_info_panel("Media Preview", info_items)


            if user_choice == 'i':  # Get Info only
                if video_info.get('description'):
                    print(f"{Colors.INFO}Description Preview:{Colors.RESET}\n{Colors.MUTED}{video_info['description']}{Colors.RESET}")
                # Detailed format listing could be added here if desired
                continue # Back to main menu

            # --- Download Path (user_choice == 'd') ---
            # Get advanced download options from user
            # Pass ui instance and video_info to the static method
            download_options = SuperDownloader.create_advanced_options_menu(ui, video_info)

            # Confirm download
            confirm_options_list = [
                ('s', '✅ Start Download', 'Begin downloading with selected options'),
                ('m', '⚙️ Modify Options', 'Change download settings'),
                ('c', '❌ Cancel & Main Menu', 'Return to main menu'),
            ]
            confirm_choice_idx_str = ui.create_interactive_menu("Confirm Download", confirm_options_list)
            confirm_action = confirm_options_list[int(confirm_choice_idx_str)-1][0]


            if confirm_action == 'c':  # Cancel
                continue
            elif confirm_action == 'm':  # Modify options
                download_options = SuperDownloader.create_advanced_options_menu(ui, video_info)
                # After modifying, assume they want to start download
                confirm_action = 's' 

            if confirm_action == 's':  # Start download
                print(f"\n{Colors.PRIMARY}🚀 Starting download(s)...{Colors.RESET}")
                
                # Ensure output directory exists (resolved path is in download_options['output_dir'])
                try:
                    output_dir_path = Path(download_options['output_dir'])
                    output_dir_path.mkdir(parents=True, exist_ok=True)
                except OSError as e:
                    print(f"{Colors.ERROR}Error creating output directory {download_options['output_dir']}: {e}{Colors.RESET}")
                    continue # Or handle more gracefully

                success = downloader.download_with_options(url, download_options)

                if success: # yt-dlp handles individual file successes/failures with ignoreerrors
                    print(f"\n{Colors.SUCCESS}✨ Download process completed!{Colors.RESET}")
                    print(f"{Colors.INFO}📁 Files saved to (or attempted in): {os.path.abspath(download_options['output_dir'])}{Colors.RESET}")
                else:
                    # download_with_options or download_hook would have printed specific errors
                    print(f"\n{Colors.WARNING}⚠️ Download process finished with some issues. Check messages above.{Colors.RESET}")


        except KeyboardInterrupt: # Should be caught by signal_handler, but as a fallback
            print(f"\n\n{Colors.WARNING}🛑 Operation cancelled by user.{Colors.RESET}")
            spinner.stop()
            # No 'continue' here, KeyboardInterrupt usually means exit intent for the current operation
            # Ask if user wants to exit YtDorn or go to main menu
            exit_choice = ui.create_interactive_menu("Interrupted", [
                ('m', "Return to Main Menu", ""),
                ('q', "Quit YtDorn", "")
            ], show_shortcuts=False)
            if exit_choice == '2': # Quit
                print(f"\n{Colors.SUCCESS}👋 Exiting YtDorn. Goodbye!{Colors.RESET}\n")
                sys.exit(0)
            # Else, loop continues (back to main menu)
            
        except Exception as e:
            spinner.stop() # Ensure spinner is stopped on any unexpected error
            print(f"\n{Colors.ERROR}❌ An unexpected error occurred in the main loop: {str(e)}{Colors.RESET}")
            # Log detailed traceback for debugging if needed
            # import traceback
            # print(f"{Colors.MUTED}{traceback.format_exc()}{Colors.RESET}")
            # Ask to continue or quit
            error_choice = ui.create_interactive_menu("Unexpected Error", [
                ('m', "Try returning to Main Menu", ""),
                ('q', "Quit YtDorn", "")
            ], show_shortcuts=False)
            if error_choice == '2': # Quit
                print(f"\n{Colors.SUCCESS}👋 Exiting YtDorn. Goodbye!{Colors.RESET}\n")
                sys.exit(1) # Exit with error code
            # Else, loop continues (back to main menu)

        # Ask if user wants to perform another operation or exit
        # This is now effectively handled by the main loop always showing menu,
        # unless an unrecoverable error or explicit quit occurs.
        # No need for explicit "continue?" question after each operation.

class BatchDownloader: # Retained, but not integrated into interactive main menu in this pass
    """Handle batch downloads from file or multiple URLs"""

    @staticmethod
    def download_from_file(file_path: str, base_options: Dict[str, Any], ui: ModernUI, downloader: SuperDownloader) -> bool:
        """Download multiple URLs from a text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip() and not line.startswith('#')] # Ignore empty lines and comments

            valid_urls = [url for url in urls if validate_url(url)]

            if not valid_urls:
                print(f"{Colors.ERROR}No valid URLs found in file: {file_path}{Colors.RESET}")
                return False

            print(f"{Colors.INFO}Found {len(valid_urls)} valid URLs in {file_path} (out of {len(urls)} lines).{Colors.RESET}")
            
            # Confirm batch download
            confirm_batch = ui.create_interactive_menu(f"Batch Download ({len(valid_urls)} URLs)", [
                ('s', "Start Batch Download", "Use provided options for all URLs"),
                ('c', "Cancel Batch", "")
            ])
            if confirm_batch != '1':
                print(f"{Colors.WARNING}Batch download cancelled.{Colors.RESET}")
                return False

            successful_downloads = 0
            total_urls = len(valid_urls)

            for i, url in enumerate(valid_urls, 1):
                print(f"\n{Colors.gradient_text(f'═ Batch Item {i}/{total_urls} ═', (64,224,255), (175,175,255))}")
                print(f"{Colors.PRIMARY}Processing URL: {url}{Colors.RESET}")
                
                # Fetch info for this specific URL to customize options if needed, or just use base_options
                # For simplicity, we'll use the base_options provided via CLI for all batch items.
                # A more advanced batch mode might re-prompt or use per-URL configs.
                current_options = base_options.copy() # Start with base CLI options

                # Ensure output directory exists for this item, potentially using a subfolder structure
                # Example: base_output_dir / playlist_title_or_url_hash / video_title.ext
                # For now, all batch items go to the same specified output dir.
                output_dir_path = Path(current_options['output_dir'])
                try:
                    output_dir_path.mkdir(parents=True, exist_ok=True)
                except OSError as e:
                    print(f"{Colors.ERROR}Error creating output directory {output_dir_path} for {url}: {e}{Colors.RESET}")
                    print(f"{Colors.WARNING}⚠ Skipping URL due to directory error: {url}{Colors.RESET}")
                    continue
                
                # Update output template to ensure it's in the resolved directory
                filename_pattern = "%(title).150s.%(ext)s" # Default pattern for batch items
                # Potentially add %(playlist_index)s if URL is a playlist, but yt-dlp handles this if URL itself is a playlist.
                current_options['output_template'] = str(output_dir_path / filename_pattern)


                if downloader.download_with_options(url, current_options):
                    successful_downloads += 1 # Counts if the download call succeeded, not individual files in a playlist
                else:
                    print(f"{Colors.WARNING}⚠ Issues encountered with URL: {url}. Check logs.{Colors.RESET}")
            
            print(f"\n{Colors.gradient_text('═ Batch Complete ═', (0,255,127), (64,224,255))}")
            if successful_downloads == total_urls:
                 print(f"{Colors.SUCCESS}✅ Batch download fully completed: {successful_downloads}/{total_urls} URLs processed successfully.{Colors.RESET}")
            else:
                 print(f"{Colors.WARNING}⚠️ Batch download completed with some issues: {successful_downloads}/{total_urls} URLs processed without fatal errors.{Colors.RESET}")
            return True

        except FileNotFoundError:
            print(f"{Colors.ERROR}Batch file not found: {file_path}{Colors.RESET}")
            return False
        except Exception as e:
            print(f"{Colors.ERROR}Error processing batch file: {str(e)}{Colors.RESET}")
            # import traceback; print(traceback.format_exc()) # For debugging
            return False

class ConfigManager:
    """Manage user configurations and presets"""

    CONFIG_FILE = str(Path.home() / ".ytdorn_config.json")

    @staticmethod
    def load_config() -> Dict[str, Any]:
        """Load user configuration"""
        try:
            if Path(ConfigManager.CONFIG_FILE).exists():
                with open(ConfigManager.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            # print(f"{Colors.WARNING}Could not load config file: {e}{Colors.RESET}")
            pass # Silently ignore load errors, use defaults
        return ConfigManager._get_default_config()

    @staticmethod
    def save_config(config: Dict[str, Any]) -> bool:
        """Save user configuration"""
        try:
            with open(ConfigManager.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            print(f"{Colors.ERROR}Could not save config file: {e}{Colors.RESET}")
            return False

    @staticmethod
    def _get_default_config() -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'default_output_dir': str(Path.home() / "Downloads" / "YtDorn"),
            'default_format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'default_audio_format': 'mp3', # For audio extraction
            'default_audio_quality': '192',
            'default_subtitles': False,
            'default_auto_subtitles': False,
            'default_subtitle_langs': ['en'],
            'default_thumbnail': False,
            'ignore_errors': True, # For playlists primarily
            'presets': {
                'default_video': {
                    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                    'subtitles': False,
                    'thumbnail': True,
                    'embed_thumbnail': True,
                },
                'high_quality_video': {
                    'format': 'bestvideo[height>=1080][ext=mp4]+bestaudio[ext=m4a]/best[height>=1080][ext=mp4]/bestvideo+bestaudio/best',
                    'subtitles': True,
                    'subtitle_langs': ['en', 'und'], # und for unknown/original if 'en' not found
                    'embed_subs': True,
                    'thumbnail': True,
                    'embed_thumbnail': True,
                    'metadata_json': True,
                    'description_file': True,
                },
                'audio_mp3_good': {
                    'format': 'bestaudio/best', # yt-dlp selects best audio
                    'extract_audio': True,
                    'audio_format': 'mp3',
                    'audio_quality': '192', # kbps
                    'thumbnail': True, # Download thumbnail
                    'embed_thumbnail': True, # Embed into audio file
                    'metadata_json': True,
                },
                 'audio_best_source': {
                    'format': 'bestaudio/best',
                    'extract_audio': True,
                    'audio_format': 'best', # Keep original codec if possible, or best conversion
                    'audio_quality': '0', # best quality for variable bitrate codecs like opus/vorbis
                    'thumbnail': True,
                    'embed_thumbnail': True,
                },
                'archive_playlist': {
                    'format': 'best',
                    'subtitles': True,
                    'auto_subtitles': True,
                    'allsubtitles': True, # Download all available subtitle languages
                    'thumbnail': True,
                    'metadata_json': True,
                    'description_file': True,
                    'ignore_errors': True,
                    'output_template': "%(playlist_uploader)s/%(playlist_title)s/%(playlist_index)s - %(title)s [%(id)s].%(ext)s"
                }
            }
        }

def setup_argument_parser() -> argparse.ArgumentParser:
    """Setup command line argument parser"""
    parser = argparse.ArgumentParser(
        description='YtDorn v0.1.2 - Super Powerful YouTube Downloader by 0xb0rn3',
        formatter_class=argparse.RawTextHelpFormatter, # RawDescriptionHelpFormatter was causing issues with epilog
        epilog=f"""
{Colors.PRIMARY}Examples:{Colors.RESET}
  %(prog)s                           # Interactive mode
  %(prog)s -u "VIDEO_URL"            # Quick download with default preset
  %(prog)s -u "VIDEO_URL" -p audio_mp3_good # Download using 'audio_mp3_good' preset
  %(prog)s --url "PLAYLIST_URL" --preset archive_playlist
  %(prog)s --batch urls.txt --preset default_video # Batch download with a preset
  %(prog)s --info "URL"                          # Get video info only (JSON output)
  %(prog)s --list-presets                        # List available presets
  %(prog)s --config K=V K2=V2                    # Set default config values (e.g., default_output_dir=/path/to/dir)

{Colors.MUTED}For custom format strings, refer to yt-dlp documentation.{Colors.RESET}
"""
    )

    # Core arguments
    parser.add_argument('-u', '--url', help='YouTube or compatible URL (video, playlist, channel)')
    parser.add_argument('--batch', help='Path to a text file containing URLs to download (one per line)')
    parser.add_argument('--info', metavar="URL", help='Get media information as JSON and exit (ignores download options)')
    
    # Output and Formatting (can be overridden by presets)
    parser.add_argument('-o', '--output', help='Output directory (default: from config or ~/Downloads/YtDorn)')
    parser.add_argument('-f', '--format', help='yt-dlp format string (e.g., "bestvideo+bestaudio/best")')
    parser.add_argument('--output-template', help='yt-dlp output filename template')

    # Content Selection
    parser.add_argument('--extract-audio', action='store_true', help='Extract audio only (implies -f bestaudio)')
    parser.add_argument('--audio-format', help='Audio format for extraction (e.g., mp3, m4a, wav, opus)')
    parser.add_argument('--audio-quality', help='Audio quality for extraction (e.g., 192 for mp3, 0 for best VBR)')
    parser.add_argument('--subtitles', action='store_true', help='Download subtitles')
    parser.add_argument('--auto-subtitles', action='store_true', help='Include auto-generated subtitles if manual are missing')
    parser.add_argument('--subtitle-langs', default='en', help='Comma-separated subtitle languages (e.g., en,es,ja)')
    parser.add_argument('--embed-subs', action='store_true', help='Embed subtitles into media file (requires ffmpeg)')
    parser.add_argument('--thumbnail', action='store_true', help='Download thumbnail image')
    parser.add_argument('--embed-thumbnail', action='store_true', help='Embed thumbnail into media file (requires ffmpeg)')
    parser.add_argument('--metadata-json', action='store_true', help='Write video metadata to a .json file')
    parser.add_argument('--description-file', action='store_true', help='Write video description to a .description file')

    # Playlist specific (can be overridden by presets)
    parser.add_argument('--playlist-items', help='Specific items to download from a playlist (e.g., "1,3,5-7")')
    parser.add_argument('--no-playlist', action='store_true', help='If URL is a playlist, download only the video specified by URL (not the whole playlist)')

    # Configuration and Utility
    parser.add_argument('--preset', help='Use a configuration preset for download options (see --list-presets)')
    parser.add_argument('--list-presets', action='store_true', help='List available presets from config and exit')
    parser.add_argument('--config', nargs='*', help="Set default config key=value pairs (e.g., default_output_dir=/path/to/my/videos)")
    parser.add_argument('--reset-config', action='store_true', help='Reset configuration to default values')
    
    parser.add_argument('--quiet', '-q', action='store_true', help='Quiet mode (minimal output, overrides interactive spinner/progress)')
    parser.add_argument('--version', action='version', version=f'%(prog)s v0.1.2 by 0xb0rn3')

    return parser

def run_cli_mode(args: argparse.Namespace, ui: ModernUI, downloader: SuperDownloader):
    """Run in command line mode with arguments"""
    config = ConfigManager.load_config()

    if args.reset_config:
        default_cfg = ConfigManager._get_default_config()
        if ConfigManager.save_config(default_cfg):
            print(f"{Colors.SUCCESS}Configuration reset to defaults and saved to {ConfigManager.CONFIG_FILE}{Colors.RESET}")
        else:
            print(f"{Colors.ERROR}Failed to reset configuration.{Colors.RESET}")
        return

    if args.config:
        updated = False
        for item in args.config:
            key, sep, value = item.partition('=')
            if sep:
                # Try to intelligently convert value type for known config keys
                if key in config and isinstance(config[key], bool): value = value.lower() in ['true', '1', 'yes']
                elif key in config and isinstance(config[key], int): value = int(value)
                elif key in config and isinstance(config[key], list) and isinstance(value, str): value = [v.strip() for v in value.split(',')]
                
                # For nested presets, e.g., presets.my_preset.format=newValue
                keys = key.split('.')
                d = config
                for k_part in keys[:-1]:
                    d = d.setdefault(k_part, {})
                d[keys[-1]] = value
                updated = True
                print(f"{Colors.MUTED}Config: set {key} = {value}{Colors.RESET}")
            else:
                print(f"{Colors.WARNING}Invalid config format: {item}. Use key=value.{Colors.RESET}")
        if updated:
            ConfigManager.save_config(config)
            print(f"{Colors.SUCCESS}Configuration updated and saved to {ConfigManager.CONFIG_FILE}{Colors.RESET}")
        return # Exit after config change


    if args.list_presets:
        print(f"{Colors.PRIMARY}{Colors.BOLD}Available Presets (from {ConfigManager.CONFIG_FILE}):{Colors.RESET}")
        if not config.get('presets'):
            print(f"{Colors.MUTED}  No presets found.{Colors.RESET}")
            return
        for name, settings in config['presets'].items():
            print(f"\n  {Colors.SUCCESS}{name}{Colors.RESET}:")
            for key, value in settings.items():
                print(f"    {Colors.MUTED}{key}{Colors.RESET}: {Colors.PRIMARY}{value}{Colors.RESET}")
        return

    if args.info:
        spinner = ModernSpinner() if not args.quiet else None
        if spinner: spinner.start(f"Fetching info for {args.info}...")
        try:
            info = downloader.get_video_info(args.info)
            if spinner: spinner.stop()
            # Output as JSON
            try:
                print(json.dumps(info, indent=2, ensure_ascii=False))
            except TypeError: # Handle non-serializable items if any (e.g. datetime if not stringified)
                # A simple way to handle non-serializable: convert to string
                print(json.dumps(info, indent=2, default=str, ensure_ascii=False))
        except Exception as e:
            if spinner: spinner.stop(f"{Colors.ERROR}Error fetching info: {str(e)}{Colors.RESET}")
            else: print(f"Error: {str(e)}", file=sys.stderr)
            sys.exit(1)
        return

    # --- Prepare download options from CLI args and presets ---
    cli_options: Dict[str, Any] = {}

    # Start with config defaults
    cli_options['output_dir'] = config.get('default_output_dir', str(Path.home() / "Downloads" / "YtDorn"))
    cli_options['format'] = config.get('default_format', 'best')
    # ... other defaults from config can be added here

    # Apply preset if specified
    if args.preset:
        if args.preset in config.get('presets', {}):
            cli_options.update(config['presets'][args.preset])
            if not args.quiet: print(f"{Colors.INFO}Applied preset: {args.preset}{Colors.RESET}")
        else:
            print(f"{Colors.ERROR}Preset '{args.preset}' not found. Use --list-presets to see available ones.{Colors.RESET}", file=sys.stderr)
            sys.exit(1)

    # Override with direct CLI arguments
    if args.output: cli_options['output_dir'] = args.output
    if args.format: cli_options['format'] = args.format
    if args.output_template: cli_options['output_template'] = args.output_template # Full path if provided
    
    if args.extract_audio: cli_options['extract_audio'] = True
    if args.audio_format: cli_options['audio_format'] = args.audio_format
    if args.audio_quality: cli_options['audio_quality'] = args.audio_quality
    
    if args.subtitles: cli_options['subtitles'] = True
    if args.auto_subtitles: cli_options['auto_subtitles'] = True # Works if subtitles is true
    if args.subtitle_langs: cli_options['subtitle_langs'] = [lang.strip() for lang in args.subtitle_langs.split(',')]
    if args.embed_subs: cli_options['embed_subs'] = True
    
    if args.thumbnail: cli_options['thumbnail'] = True
    if args.embed_thumbnail: cli_options['embed_thumbnail'] = True
    
    if args.metadata_json: cli_options['metadata_json'] = True
    if args.description_file: cli_options['description_file'] = True
    
    if args.playlist_items: cli_options['playlist_items'] = args.playlist_items
    if args.no_playlist: cli_options['no_playlist'] = True
    
    if args.quiet:
        # Suppress progress hooks if quiet mode is on for CLI
        downloader.download_hook = lambda d: None # type: ignore

    # Ensure output directory is resolved and output_template is constructed correctly
    cli_options['output_dir'] = str(Path(cli_options['output_dir']).resolve())
    if 'output_template' not in cli_options or not Path(cli_options['output_template']).is_absolute():
        # Default filename pattern if not fully specified by template or preset
        default_filename_pattern = "%(title).150s [%(id)s].%(ext)s"
        # Check if it's a playlist URL for playlist-specific pattern if not overridden by preset
        # This check is simplistic here; ideally, we'd fetch info first even in CLI if not too slow.
        is_likely_playlist = False
        if args.url and ('playlist?list=' in args.url or '/playlist/' in args.url or '/channel/' in args.url or '/c/' in args.url):
            is_likely_playlist = True
            if not cli_options.get('no_playlist'): # only if processing as playlist
                 default_filename_pattern = "%(playlist_index)s - %(title).150s [%(id)s].%(ext)s"
        
        # If output_template was relative or just a pattern, join with output_dir
        current_template_pattern = cli_options.get('output_template', default_filename_pattern)
        cli_options['output_template'] = str(Path(cli_options['output_dir']) / current_template_pattern)


    # --- Execute Download ---
    # Create output directory
    try:
        Path(cli_options['output_dir']).mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"{Colors.ERROR}Error creating output directory {cli_options['output_dir']}: {e}{Colors.RESET}", file=sys.stderr)
        sys.exit(1)

    if args.batch:
        if not Path(args.batch).is_file():
            print(f"{Colors.ERROR}Batch file not found: {args.batch}{Colors.RESET}", file=sys.stderr)
            sys.exit(1)
        if not args.quiet: print(f"{Colors.PRIMARY}Starting batch download from: {args.batch}{Colors.RESET}")
        # For CLI batch, we assume UI is not available for confirmations per item.
        success = BatchDownloader.download_from_file(args.batch, cli_options, ui, downloader)
        sys.exit(0 if success else 1)

    elif args.url:
        if not validate_url(args.url): # Basic check, yt-dlp will do the final validation
             # validate_url prints its own messages
             # sys.exit(1) # Commented out to allow yt-dlp to try anyway
             if not args.quiet: print(f"{Colors.WARNING}URL validation failed, but attempting download with yt-dlp...{Colors.RESET}")


        if not args.quiet:
            print(f"{Colors.PRIMARY}Starting download for: {args.url}{Colors.RESET}")
            print(f"{Colors.MUTED}Options: {cli_options}{Colors.RESET}")
        
        success = downloader.download_with_options(args.url, cli_options)
        
        if not args.quiet:
            if success:
                print(f"\n{Colors.SUCCESS}✨ CLI Download process completed!{Colors.RESET}")
                print(f"{Colors.INFO}📁 Files saved to (or attempted in): {Path(cli_options['output_dir']).resolve()}{Colors.RESET}")
            else:
                print(f"\n{Colors.WARNING}⚠️ CLI Download process finished with some issues.{Colors.RESET}")
        sys.exit(0 if success else 1)

    else: # No URL, batch, info, or list-presets given that would exit
        # This case should ideally not be reached if parser is setup correctly with subparsers or required groups.
        # If it's reached, it means only optional flags like --quiet were given without a primary action.
        # The `if any(meaningful_args):` check before calling `run_cli_mode` handles this.
        # So, this `else` block is a fallback.
        print(f"{Colors.ERROR}No action specified (URL, batch, info, list-presets). Use --help for options.{Colors.RESET}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    # Initialize UI and Downloader instances for both modes
    # This helps if CLI mode still needs to show some UI elements or use downloader methods.
    ui_instance = ModernUI()
    downloader_instance = SuperDownloader()
    
    # Check if running in CLI mode (with arguments)
    arg_parser = setup_argument_parser()
    cli_args = arg_parser.parse_args()

    # Determine if CLI mode should run based on provided arguments
    # Meaningful args are those that specify an action, not just modifiers like --quiet
    # or config-only changes like --reset-config / --config
    action_args_present = cli_args.url or \
                          cli_args.batch or \
                          cli_args.info or \
                          cli_args.list_presets
    
    config_action_args_present = cli_args.config or \
                                 cli_args.reset_config

    should_run_cli = action_args_present or config_action_args_present

    try:
        if should_run_cli:
            # Check dependencies even for CLI mode, unless it's just for --version or --help (handled by argparse)
            # For --list-presets or config changes, dependencies might not be strictly needed, but yt-dlp presence is good.
            if action_args_present and not (cli_args.info and cli_args.list_presets): # Skip dep check for list-presets and info for now
                 if not DependencyManager.install_missing_dependencies(ModernSpinner(style='dots')): # Use a basic spinner for CLI
                    # Errors printed by the method
                    sys.exit(1)
            run_cli_mode(cli_args, ui_instance, downloader_instance)
        else:
            # No meaningful CLI arguments provided, run interactive mode
            main() # main() uses global ui, spinner, downloader

    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}🛑 Application interrupted by user. Goodbye!{Colors.RESET}")
        sys.exit(0)
    except Exception as e:
        # This is a top-level catch-all for unexpected errors not handled elsewhere.
        print(f"{Colors.ERROR}☠️ A critical unhandled error occurred: {str(e)}{Colors.RESET}")
        # For debugging, uncomment the next line:
        # import traceback; print(f"{Colors.MUTED}{traceback.format_exc()}{Colors.RESET}")
        sys.exit(1)
