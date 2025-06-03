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
    PRIMARY = '\033[38;2;64;224;255m'    # Bright cyan
    SECONDARY = '\033[38;2;255;100;255m'  # Bright magenta
    SUCCESS = '\033[38;2;0;255;127m'      # Bright green
    WARNING = '\033[38;2;255;191;0m'      # Bright yellow
    ERROR = '\033[38;2;255;69;58m'        # Bright red
    INFO = '\033[38;2;175;175;255m'       # Light blue
    MUTED = '\033[38;2;128;128;128m'      # Gray
    
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
        text_length = len([c for c in text if c.strip()]) # Consider only non-whitespace for length
        char_index = 0
        
        for char in text:
            if char.strip():
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
        sys.stdout.write('\r\033[K') # Clear the line
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
        self.speed_samples = [] # Stores (timestamp, bytes)
        self.last_update_time = time.time() # For speed calculation interval

    def update(self, current_bytes: int, extra_info: str = "") -> str:
        """Update progress with enhanced statistics. current_bytes is the total downloaded so far."""
        self.current = current_bytes
        now = time.time()
        
        # Calculate speed with smoothing
        current_speed_str = ""
        if now - self.last_update_time > 0.5 or not self.speed_samples: # Update speed roughly every 0.5s or on first update
            if self.speed_samples:
                # Calculate speed based on the change since the last sample used for speed calculation
                # This avoids using the very first self.start_time for ongoing speed, making it more reactive.
                # A better approach would be a rolling average of instantaneous speeds.
                # For simplicity, let's use an overall average if samples are few, or more recent if many.
                
                # Add current sample
                if not self.speed_samples or now > self.speed_samples[-1][0]: # ensure time moves forward
                     self.speed_samples.append((now, current_bytes))
                
                # Keep a window of speed samples
                if len(self.speed_samples) > 10:
                    self.speed_samples.pop(0)

                # Calculate speed over the window or available samples
                if len(self.speed_samples) > 1:
                    time_delta = self.speed_samples[-1][0] - self.speed_samples[0][0]
                    byte_delta = self.speed_samples[-1][1] - self.speed_samples[0][1]
                    if time_delta > 0:
                        speed = byte_delta / time_delta
                        current_speed_str = f" @ {self._format_bytes(speed)}/s"
            elif now > self.start_time : # First few updates, use overall average
                speed = current_bytes / (now - self.start_time)
                current_speed_str = f" @ {self._format_bytes(speed)}/s"
                if now > self.start_time: # Add first sample if not already added by previous logic
                    self.speed_samples.append((now, current_bytes))

            self.last_update_time = now


        # Calculate percentage and bar
        percentage = (current_bytes / self.total * 100) if self.total > 0 else 0
        filled_exact = (self.width * current_bytes / self.total) if self.total > 0 else 0
        filled = int(filled_exact)
        
        bar = ''
        for i in range(filled):
            intensity = min(255, 50 + int(i * 205 / self.width)) if self.width > 0 else 50
            bar += Colors.rgb(intensity, 100, 255) + '█'
        
        # Fractional part of the bar (smoother look)
        if filled < self.width:
            bar_chars = ['█', '▉', '▊', '▋', '▌', '▍', '▎', '▏']
            fraction = filled_exact - filled
            if fraction > 0.125: # Add fractional char if it's significant
                 char_index = min(len(bar_chars)-1, int(fraction * len(bar_chars)))
                 intensity = min(255, 50 + int(filled * 205 / self.width)) if self.width > 0 else 50
                 bar += Colors.rgb(intensity, 100, 255) + bar_chars[char_index]
                 bar += Colors.MUTED + '░' * (self.width - filled -1)
            else:
                 bar += Colors.MUTED + '░' * (self.width - filled)

        bar += Colors.RESET

        # Calculate ETA
        elapsed = now - self.start_time
        eta = "--:--"
        if current_bytes > 0 and elapsed > 0 and len(self.speed_samples) > 1 : # Use sampled speed for ETA
            # Use speed calculated over the sample window for ETA
            time_delta_sample = self.speed_samples[-1][0] - self.speed_samples[0][0]
            byte_delta_sample = self.speed_samples[-1][1] - self.speed_samples[0][1]
            if time_delta_sample > 0 and byte_delta_sample > 0 :
                rate = byte_delta_sample / time_delta_sample
                if rate > 0:
                    eta_seconds = (self.total - current_bytes) / rate
                    eta = self._format_duration(eta_seconds)
        elif current_bytes > 0 and elapsed > 0: # Fallback to overall rate if not enough samples
            rate = current_bytes / elapsed
            if rate > 0:
                eta_seconds = (self.total - current_bytes) / rate
                eta = self._format_duration(eta_seconds)


        # Format sizes
        current_size_fmt = self._format_bytes(current_bytes)
        total_size_fmt = self._format_bytes(self.total)
        
        return (f"\r{Colors.PRIMARY}▶{Colors.RESET} {self.description[:30]:<30} "
                f"[{bar}] {percentage:5.1f}% "
                f"({current_size_fmt}/{total_size_fmt}){current_speed_str} "
                f"ETA: {eta} {extra_info}")

    @staticmethod
    def _format_bytes(bytes_val: float) -> str:
        """Format bytes with appropriate units"""
        if bytes_val < 0: bytes_val = 0 # Speed can sometimes be negative on fluctuations
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
│  ██╗  ██╗████████╗██████╗  ██████╗ ██████╗ │
│  ╚██╗ ██╔╝╚══██╔══╝██╔══██╗██╔═══██╗██╔══██╗│
│   ╚████╔╝   ██║   ██║  ██║██║   ██║██████╔╝│
│    ╚██╔╝    ██║   ██║  ██║██║   ██║██╔══██╗│
│     ██║     ██║   ██████╔╝╚██████╔╝██║  ██║│
│     ╚═╝     ╚═╝   ╚═════╝  ╚═════╝ ╚═╝  ╚═╝│
╰─────────────────────────────────────────────╯"""
        
        print(Colors.gradient_text(banner_text, (64, 224, 255), (255, 100, 255)))
        print(f"\n{Colors.PRIMARY}{Colors.BOLD}YtDorn v0.1.2{Colors.RESET} {Colors.MUTED}by 0xb0rn3{Colors.RESET}")
        print(f"{Colors.INFO}Super Powerful YouTube Downloader{Colors.RESET}")
        print(f"{Colors.MUTED}https://github.com/0xb0rn3{Colors.RESET}") # Replace with actual if available
        print(Colors.gradient_text('═' * 50, (64, 224, 255), (255, 100, 255)))

    @staticmethod
    def create_interactive_menu(title: str, options: List[Tuple[str, str, str]], 
                                show_shortcuts: bool = True) -> str:
        """Create modern interactive menu with shortcuts and descriptions"""
        print(f"\n{Colors.PRIMARY}{Colors.BOLD}┌─ {title} ─┐{Colors.RESET}")
        
        for i, (key, title_text, description) in enumerate(options, 1):
            icon = key if len(key) == 1 and show_shortcuts else str(i)
            shortcut = f"[{icon}]" if show_shortcuts else f"[{i}]"
            print(f"{Colors.INFO}{shortcut:<4}{Colors.RESET} {title_text}")
            if description:
                print(f"      {Colors.MUTED}{description}{Colors.RESET}")
        
        print(f"{Colors.PRIMARY}└{'─' * (len(title) + 4)}┘{Colors.RESET}")
        
        while True:
            prompt_text = f"\n{Colors.PRIMARY}❯{Colors.RESET} Select option: "
            choice = input(prompt_text).strip().lower()
            
            for i, (key, _, _) in enumerate(options, 1):
                if choice == key.lower() or choice == str(i):
                    return str(i) # Return the numeric index as a string
            
            print(f"{Colors.ERROR}Invalid selection. Please try again.{Colors.RESET}")

    @staticmethod
    def get_user_input(prompt: str, default: str = None, validator=None) -> str:
        """Enhanced input with validation and defaults"""
        display_default = f" ({default})" if default else ""
        full_prompt = f"{Colors.PRIMARY}❯{Colors.RESET} {prompt}{Colors.MUTED}{display_default}{Colors.RESET}: "
        
        while True:
            value = input(full_prompt).strip()
            if not value and default:
                return default
            if not value:
                print(f"{Colors.ERROR}This field is required.{Colors.RESET}")
                continue
            if validator and not validator(value):
                print(f"{Colors.ERROR}Invalid input. Please try again.{Colors.RESET}")
                continue
            return value

    @staticmethod
    def get_directory_input(prompt: str, default: str, recent_dirs: List[str], validator=None) -> Tuple[str, bool]:
        """
        Prompts the user for a directory, offering default and recent options.
        Returns a tuple: (chosen_path: str, is_newly_specified: bool).
        'is_newly_specified' is True if the path was typed new or chosen via "Enter new path" option.
        """
        print(f"\n{Colors.PRIMARY}{Colors.BOLD}┌─ {prompt} ─┐{Colors.RESET}")
        
        choices_menu = []
        current_id_counter = 1

        # Option 1: Default directory
        choices_menu.append({'id': str(current_id_counter), 
                             'text': f"Use default: {Colors.PRIMARY}{default}{Colors.RESET}", 
                             'value': default, 
                             'is_new': False})
        print(f"{Colors.INFO}[{choices_menu[-1]['id']}] {Colors.RESET}{choices_menu[-1]['text']}")
        current_id_counter += 1
        
        # Options for recent directories
        default_resolved = Path(default).resolve()
        unique_recent_dirs = [p for p in recent_dirs if Path(p).resolve() != default_resolved]
        
        if unique_recent_dirs:
            print(f"{Colors.MUTED}--- Recent Directories ---{Colors.RESET}")
            for path_str in unique_recent_dirs:
                choices_menu.append({'id': str(current_id_counter), 
                                     'text': f"Recent: {Colors.SECONDARY}{path_str}{Colors.RESET}", 
                                     'value': path_str, 
                                     'is_new': False})
                print(f"{Colors.INFO}[{choices_menu[-1]['id']}] {Colors.RESET}{choices_menu[-1]['text']}")
                current_id_counter += 1
        
        # Option for entering a new path
        if unique_recent_dirs : # Add separator if recent dirs were listed
            print(f"{Colors.MUTED}--- Other Options ---{Colors.RESET}")
        elif not unique_recent_dirs and choices_menu: # Add separator if only default was listed
             print(f"{Colors.MUTED}--- Other Options ---{Colors.RESET}")

        
        choices_menu.append({'id': str(current_id_counter), 
                             'text': "Enter new or custom path", 
                             'value': '__NEW__', 
                             'is_new': True}) # This option itself signifies intent for a new path
        print(f"{Colors.INFO}[{choices_menu[-1]['id']}] {Colors.RESET}{choices_menu[-1]['text']}")
        
        print(f"{Colors.PRIMARY}└{'─' * (len(prompt) + 4)}┘{Colors.RESET}")

        while True:
            input_prompt_text = f"\n{Colors.PRIMARY}❯{Colors.RESET} Select option number or type path directly: "
            user_input_str = input(input_prompt_text).strip()

            selected_option = next((c for c in choices_menu if c['id'] == user_input_str), None)

            if selected_option:
                if selected_option['value'] == '__NEW__':
                    path_prompt_text = f"{Colors.PRIMARY}❯{Colors.RESET} Enter new directory path (or press Enter for default '{default}'): "
                    new_path_str = input(path_prompt_text).strip()
                    
                    if not new_path_str: # User pressed Enter, defaulting
                        print(f"{Colors.INFO}Using default directory: {default}{Colors.RESET}")
                        return default, False # Defaulting, so not "newly specified"
                    
                    if validator and not validator(new_path_str):
                        print(f"{Colors.ERROR}Invalid path input. Please try again.{Colors.RESET}")
                        continue
                    print(f"{Colors.INFO}Using custom directory: {new_path_str}{Colors.RESET}")
                    return new_path_str, True # Explicitly new path
                else:
                    # User selected default or a recent path from menu
                    print(f"{Colors.INFO}Selected directory: {selected_option['value']}{Colors.RESET}")
                    return selected_option['value'], selected_option.get('is_new', False)
            
            elif user_input_str: # User typed a path directly
                if validator and not validator(user_input_str):
                    print(f"{Colors.ERROR}Invalid path input. Please try again.{Colors.RESET}")
                    continue
                print(f"{Colors.INFO}Using custom directory: {user_input_str}{Colors.RESET}")
                return user_input_str, True # Typed directly, considered new
            
            elif not user_input_str: # Empty input
                print(f"{Colors.WARNING}No input provided. Please select an option or type a path.{Colors.RESET}")
            
            else: # Invalid number or unhandled case
                 print(f"{Colors.ERROR}Invalid selection. Please choose an option number or type a valid path.{Colors.RESET}")

    @staticmethod
    def show_info_panel(title: str, items: Dict[str, str]):
        """Display information in a modern panel format"""
        max_key_length = max(len(key) for key in items.keys()) if items else 0
        
        print(f"\n{Colors.INFO}┌─ {title} {'─' * max(0, (max_key_length + 20 - len(title) -4))}") #Adjusted for panel width
        for key, value in items.items():
            print(f"{Colors.INFO}│{Colors.RESET} {key:<{max_key_length}} : {Colors.PRIMARY}{value}{Colors.RESET}")
        print(f"{Colors.INFO}└{'─' * (max_key_length + len(title) + 25 - len(title)-4 +2)}{Colors.RESET}") # Adjusted for panel width


class DependencyManager:
    """Advanced dependency management with better error handling"""
    
    @staticmethod
    def check_system_dependencies() -> Dict[str, bool]:
        """Comprehensive dependency check"""
        deps = {}
        
        # Check yt-dlp
        deps['yt-dlp'] = shutil.which('yt-dlp') is not None
        if not deps['yt-dlp']:
            try:
                import yt_dlp 
                deps['yt-dlp'] = True
            except ImportError:
                pass # yt-dlp not found as command or module
        
        # Check ffmpeg (optional but recommended for some features)
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
                    "FFmpeg is recommended for audio extraction and format conversion.\n"
                    "Install it via your system's package manager (e.g., apt, brew, choco) or from https://ffmpeg.org"
                )
        return instructions

    @staticmethod
    def install_missing_dependencies(spinner: ModernSpinner):
        """Install missing dependencies with progress feedback"""
        deps = DependencyManager.check_system_dependencies()
        
        if deps.get('yt-dlp') and deps.get('ffmpeg'): # Assuming ffmpeg is now checked
            return True # All essential (and recommended checked) deps are present
        
        spinner.start("Checking system dependencies...")
        time.sleep(0.5) # Brief pause for user to read
        # spinner.stop() # Stop before printing specific messages

        missing_for_auto_install = []
        if not deps.get('yt-dlp'):
            missing_for_auto_install.append('yt-dlp')
        
        # We won't auto-install ffmpeg by default as it's more complex system-wide
        # But we will report if it's missing.
        
        if not missing_for_auto_install and deps.get('ffmpeg'): # Only yt-dlp was auto-installable and it's present
            spinner.stop(f"{Colors.SUCCESS}✓ yt-dlp found.{Colors.RESET} {Colors.SUCCESS if deps.get('ffmpeg') else Colors.WARNING}FFmpeg "
                         f"{'found.' if deps.get('ffmpeg') else 'not found (some features may be limited).'}{Colors.RESET}")
            return True

        if not deps['yt-dlp']:
            spinner.message = "yt-dlp not found. Attempting to install..."
            # spinner.start("Installing yt-dlp...") # spinner already started
            try:
                pip_command = [sys.executable, "-m", "pip", "install", "yt-dlp"]
                # Attempt to add --break-system-packages if on a system that might need it (e.g. newer Debian/Ubuntu)
                # This is a heuristic. A more robust check for PEP 668 environment might be needed.
                if platform.system() == "Linux":
                     # Simple check, could be more refined
                    try:
                        # Check pip version, if it's new enough to support/require this
                        pip_version_proc = subprocess.run([sys.executable, "-m", "pip", "--version"], capture_output=True, text=True, check=False)
                        if "pip 23" in pip_version_proc.stdout or "pip 24" in pip_version_proc.stdout : # Add more versions as they come
                             pip_command.append("--break-system-packages")
                    except Exception:
                        pass # Ignore if pip version check fails, proceed without flag

                subprocess.check_call(pip_command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                spinner.stop(f"{Colors.SUCCESS}✓ yt-dlp installed successfully.{Colors.RESET}")
                deps['yt-dlp'] = True # Update status
            except subprocess.CalledProcessError as e:
                error_message = e.stderr.decode() if e.stderr else "Unknown pip error."
                spinner.stop(f"{Colors.ERROR}✗ Failed to install yt-dlp. Error: {error_message.splitlines()[-1] if error_message else 'Unknown'}\n"
                             f"  Please manually install using: pipx install yt-dlp OR pip install yt-dlp\n"
                             f"  Or ensure pip is configured correctly.{Colors.RESET}")
                return False # Critical dependency failed
            except FileNotFoundError: # sys.executable -m pip failed (pip not found with python)
                 spinner.stop(f"{Colors.ERROR}✗ Failed to install yt-dlp: 'pip' command not found with the current Python interpreter.\n"
                              f"  Please ensure pip is installed and accessible.{Colors.RESET}")
                 return False


        if not deps.get('ffmpeg'):
            # spinner.start("Setting up ffmpeg...") # Not auto-installing
            # spinner.stop() # Stop before printing message
            if not deps.get('yt-dlp'): # if yt-dlp was just installed, print its success first if not done
                 print(f"{Colors.SUCCESS}✓ yt-dlp is now available.{Colors.RESET}")

            print(f"{Colors.WARNING}⚠ FFmpeg not found. Some features like custom audio extraction or format conversion might be limited.{Colors.RESET}")
            # Optionally, attempt _install_ffmpeg or provide more detailed instructions
            # if DependencyManager._install_ffmpeg():
            #     spinner.stop(f"{Colors.SUCCESS}✓ ffmpeg configured successfully{Colors.RESET}")
            # else:
            #     spinner.stop(f"{Colors.WARNING}⚠ ffmpeg not found - some features may be limited{Colors.RESET}")
        
        # Final check
        return deps.get('yt-dlp', False) # Script can run without ffmpeg, but yt-dlp is essential

    @staticmethod
    def _install_ffmpeg() -> bool:
        """Attempt to install ffmpeg based on the system (Placeholder - complex and risky to automate broadly)"""
        # This method is complex and can be risky. Manual installation is generally preferred for ffmpeg.
        # For this reason, it's commented out from direct use in install_missing_dependencies.
        system = platform.system().lower()
        
        try:
            if system == "windows":
                # Try winget first, then chocolatey
                for cmd_parts in [['winget', 'install', '-e', '--id', 'Gyan.FFmpeg'], ['choco', 'install', 'ffmpeg', '-y']]:
                    if shutil.which(cmd_parts[0]):
                        subprocess.check_call(cmd_parts, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        return True
            elif system == "darwin": # macOS
                if shutil.which('brew'):
                    subprocess.check_call(['brew', 'install', 'ffmpeg'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return True
            elif system == "linux":
                # Try multiple package managers (common ones)
                # This requires sudo privileges usually, which a script shouldn't assume.
                pkg_managers = [
                    # (['sudo', 'apt', 'update', '-y'], ['sudo', 'apt', 'install', '-y', 'ffmpeg']),
                    # (['sudo', 'dnf', 'install', '-y', 'ffmpeg'],),
                    # (['sudo', 'pacman', '-Syu', '--noconfirm', 'ffmpeg'],), # ffmpeg-full might not exist
                    # (['sudo', 'zypper', 'install', '-y', 'ffmpeg'],)
                ]
                # Due to sudo requirement, automatic installation on Linux is generally not advised from a script.
                # User should be prompted or instructed.
                print(f"{Colors.INFO}On Linux, please install ffmpeg using your package manager, e.g., 'sudo apt install ffmpeg'.{Colors.RESET}")

        except subprocess.CalledProcessError:
            pass # Installation attempt failed
        except FileNotFoundError:
            pass # Package manager not found
        
        return False


class SuperDownloader:
    """Advanced downloader with comprehensive YouTube support"""
    
    def __init__(self):
        self.progress_bars: Dict[str, AdvancedProgressBar] = {}
        self.download_stats: Dict[str, Dict[str, Any]] = {}
        self.concurrent_downloads = 3 # Placeholder, not fully implemented for multiple simultaneous progress bars in one TUI line
        self.active_downloads = 0 # For managing multiple progress lines if implemented

    def download_hook(self, d: Dict[str, Any]):
        """Enhanced progress hook with detailed tracking"""
        filename = d.get('info_dict', {}).get('title', d.get('filename', 'Unknown_File')) # Prefer title from info_dict
        base_filename = os.path.basename(filename)
        # Truncate base_filename if too long for display
        max_desc_len = 25
        display_desc = (base_filename[:max_desc_len-3] + '...') if len(base_filename) > max_desc_len else base_filename


        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded_bytes = d.get('downloaded_bytes', 0)

            if total_bytes is None or downloaded_bytes is None: # Skip if essential data is missing
                 return

            if display_desc not in self.progress_bars:
                self.progress_bars[display_desc] = AdvancedProgressBar(
                    int(total_bytes), 
                    display_desc 
                )
                self.download_stats[display_desc] = {'start_time': time.time()}
            
            # Use 'speed' from d if available, otherwise AdvancedProgressBar calculates its own
            speed_from_hook = d.get('speed') 
            extra_info = ""
            # if speed_from_hook: # yt-dlp speed is often more accurate
            #     extra_info = f"({AdvancedProgressBar._format_bytes(speed_from_hook)}/s)"
            # Let AdvancedProgressBar handle its own speed display for now

            progress_line = self.progress_bars[display_desc].update(int(downloaded_bytes), extra_info)
            
            # Crude multi-line handling (can get messy if many downloads)
            # For true multi-line, a library like `blessings` or `curses` would be better.
            # This assumes only one primary download is actively showing progress.
            # If we have multiple, they'd overwrite each other on the same line.
            sys.stdout.write(progress_line)
            sys.stdout.flush()
            
        elif d['status'] == 'finished':
            if display_desc in self.progress_bars:
                # Ensure the progress bar is updated to 100%
                final_bytes = self.progress_bars[display_desc].total
                self.progress_bars[display_desc].update(final_bytes)
                sys.stdout.write('\r\033[K') # Clear the progress line

                duration = time.time() - self.download_stats[display_desc]['start_time']
                print(f"{Colors.SUCCESS}✓ {display_desc} completed in "
                      f"{AdvancedProgressBar._format_duration(duration)}{Colors.RESET}")
                
                del self.progress_bars[display_desc]
                del self.download_stats[display_desc]
        elif d['status'] == 'error':
            sys.stdout.write('\r\033[K') # Clear progress line
            print(f"{Colors.ERROR}✗ Error downloading {display_desc}.{Colors.RESET}")
            if display_desc in self.progress_bars:
                del self.progress_bars[display_desc]
            if display_desc in self.download_stats:
                del self.download_stats[display_desc]


    def get_video_info(self, url: str) -> Dict[str, Any]:
        """Extract comprehensive video information"""
        try:
            from yt_dlp import YoutubeDL # Import here to ensure it's available post-dependency check
        except ImportError:
            raise Exception("yt-dlp module is not installed or accessible.")

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': 'in_playlist', # Faster for playlists, gets per-video info if not a playlist
            'skip_download': True,
        }
        
        with YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                return self._process_video_info(info)
            except Exception as e:
                # More specific error messages from yt-dlp can be helpful
                error_msg = str(e)
                if "Unsupported URL" in error_msg:
                     raise Exception(f"Unsupported URL: {url}")
                elif "Video unavailable" in error_msg:
                     raise Exception(f"Video unavailable: {error_msg}")
                raise Exception(f"Could not extract video info: {error_msg}")

    def _process_video_info(self, info: Dict[str, Any]) -> Dict[str, Any]:
        """Process and clean video information"""
        # Handle cases where info might be for a playlist or a single video
        is_playlist = info.get('_type') == 'playlist' or 'entries' in info

        if is_playlist and info.get('entries') and info['entries'][0]: # Use first video for some details if playlist
            first_video = info['entries'][0]
            title = first_video.get('title', 'Unknown Video in Playlist')
            uploader = first_video.get('uploader', info.get('uploader', 'Unknown Uploader')) # Playlist uploader fallback
            duration = first_video.get('duration', 0)
            view_count = first_video.get('view_count', 0)
            upload_date_str = first_video.get('upload_date', '') # YYYYMMDD
        else: # Single video or playlist info itself
            title = info.get('title', 'Unknown Title')
            uploader = info.get('uploader', 'Unknown Uploader')
            duration = info.get('duration', 0)
            view_count = info.get('view_count', 0)
            upload_date_str = info.get('upload_date', '') # YYYYMMDD
        
        # Format upload_date
        upload_date_formatted = ''
        if upload_date_str and len(upload_date_str) == 8:
            try:
                dt_obj = datetime.strptime(upload_date_str, '%Y%m%d')
                upload_date_formatted = dt_obj.strftime('%Y-%m-%d')
            except ValueError:
                upload_date_formatted = upload_date_str # Keep original if parsing fails

        processed = {
            'title': title,
            'uploader': uploader,
            'duration': duration, # In seconds
            'view_count': view_count,
            'upload_date': upload_date_formatted,
            'description': (info.get('description', '')[:200] + '...' if info.get('description') else 'No description'),
            'formats': len(info.get('formats', [])), # Number of available formats for the first video or single video
            'is_live': info.get('is_live', False),
            'is_playlist': is_playlist,
        }
        
        if processed['is_playlist']:
            processed['playlist_count'] = info.get('playlist_count', len(info.get('entries', [])))
            processed['playlist_title'] = info.get('title', 'Unknown Playlist') # Playlist's own title
            # For playlist, title might be the playlist title, uploader might be channel.
            # The individual video details are now from the first entry for consistency.
            processed['title'] = info.get('title', 'Unknown Playlist Title') # Use playlist title for 'title' if it's a playlist
            if info.get('entries') and info['entries'][0]:
                 processed['first_video_title'] = first_video.get('title', 'N/A')


        return processed

    def download_with_options(self, url: str, options: Dict[str, Any]):
        """Download with comprehensive options"""
        try:
            from yt_dlp import YoutubeDL
        except ImportError:
            print(f"{Colors.ERROR}yt-dlp module is not installed. Cannot download.{Colors.RESET}")
            return False

        # Build yt-dlp options
        ydl_opts = {
            'outtmpl': options.get('output_template', '%(title)s.%(ext)s'),
            'format': options.get('format', 'best'),
            'writesubtitles': options.get('subtitles', False),
            'writeautomaticsub': options.get('auto_subtitles', False), # If user wants auto subs
            'subtitleslangs': options.get('sub_langs', ['en']), # Default to English or allow config
            'writethumbnail': options.get('thumbnail', False),
            'writedescription': options.get('description_file', False), # if 'description' key exists
            'writeinfojson': options.get('metadata_json', False), # if 'metadata' key exists
            'ignoreerrors': options.get('ignore_errors', True), # Default to true for batch/playlist
            'no_warnings': True,
            'progress_hooks': [self.download_hook],
            'quiet': True, # Suppress yt-dlp's direct stdout/stderr, we handle it
            'noplaylist': options.get('no_playlist', False), # If URL is playlist, download only video
            # 'playlist_items': options.get('playlist_items'), # e.g. '1,3-5'
            'ffmpeg_location': shutil.which('ffmpeg') or None, # Help yt-dlp find ffmpeg
        }
        
        # Add post-processors based on options
        postprocessors = []
        
        if options.get('extract_audio'):
            postprocessors.append({
                'key': 'FFmpegExtractAudio',
                'preferredcodec': options.get('audio_format', 'mp3'), # e.g., mp3, m4a, wav, flac
                'preferredquality': options.get('audio_quality', '192'), # For CBR, or 0-9 for VBR (MP3)
            })
        
        if options.get('embed_subs') and options.get('subtitles'): # Only if subtitles are downloaded
            postprocessors.append({
                'key': 'FFmpegEmbedSubtitle',
                # 'subtitleslangs': ydl_opts['subtitleslangs'] # yt-dlp handles this
            })
        
        if postprocessors:
            ydl_opts['postprocessors'] = postprocessors
        
        # Handle playlist options
        if options.get('playlist_items'):
            ydl_opts['playlist_items'] = options['playlist_items']
        
        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            return True
        except Exception as e:
            # self.download_hook({'status': 'error', 'filename': 'Download Operation'}) # Generic error hook
            print(f"{Colors.ERROR}Download failed: {str(e)}{Colors.RESET}")
            return False

    @staticmethod
    def get_format_options() -> List[Tuple[str, str, str]]:
        """Get available format options with descriptions"""
        return [
            ('best', '🎬 Best Quality', 'Highest available video+audio (MP4 preferred)'),
            ('1080p', '📺 1080p HD', 'Max 1080p video+audio (MP4 preferred)'),
            ('720p', '📹 720p HD', 'Max 720p video+audio (MP4 preferred)'),
            ('480p', '📱 480p SD', 'Max 480p video+audio (MP4 preferred)'),
            ('audio', '🎵 Audio Only (Best)', 'Extract best quality audio (e.g., M4A/Opus)'),
            ('mp3', '🎶 MP3 Audio (192k)', 'Convert audio to MP3 format (192kbps)'),
            ('custom', '⚙️ Custom Format', 'Specify custom yt-dlp format string'),
        ]

def create_advanced_options_menu() -> Tuple[Dict[str, Any], bool]:
    """Create comprehensive options selection.
    Returns a tuple: (options_dict, output_dir_is_newly_specified_bool)
    """
    ui = ModernUI()
    options: Dict[str, Any] = {} # Initialize options dict
    config = ConfigManager.load_config() 
    
    default_dir = str(Path(config.get('default_output_dir', 'downloads')).resolve()) # Resolve for display consistency
    recent_dirs = config.get('recent_output_dirs', [])
    if not isinstance(recent_dirs, list):
        recent_dirs = []

    chosen_path, is_newly_specified = ui.get_directory_input(
        "Output Directory Selection", 
        default=default_dir,
        recent_dirs=recent_dirs,
        validator=lambda x: bool(x.strip()) # Basic validation: non-empty path
    )
    options['output_dir'] = chosen_path
    
    # Format selection
    format_options_list = SuperDownloader.get_format_options()
    format_choice_input_idx_str = ui.create_interactive_menu("Format Selection", format_options_list)
    
    chosen_format_key = 'best' # Default
    try:
        selected_list_idx = int(format_choice_input_idx_str) - 1
        if 0 <= selected_list_idx < len(format_options_list):
            chosen_format_key = format_options_list[selected_list_idx][0]
        else:
            print(f"{Colors.WARNING}Invalid format choice index, defaulting to 'best'.{Colors.RESET}")
    except ValueError:
        print(f"{Colors.WARNING}Could not parse format choice, defaulting to 'best'.{Colors.RESET}")

    # Map chosen_format_key to yt-dlp format strings and other options
    if chosen_format_key == 'best':
        options['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
    elif chosen_format_key == '1080p':
        options['format'] = 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best[height<=1080]'
    elif chosen_format_key == '720p':
        options['format'] = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best[height<=720]'
    elif chosen_format_key == '480p':
        options['format'] = 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best[height<=480]'
    elif chosen_format_key == 'audio':
        options['format'] = 'bestaudio/best'
        options['extract_audio'] = True
        # Keep default audio format from yt-dlp (usually m4a or opus)
    elif chosen_format_key == 'mp3':
        options['format'] = 'bestaudio/best' # Download best audio
        options['extract_audio'] = True
        options['audio_format'] = 'mp3' # Convert to mp3
        options['audio_quality'] = '192K' # Default quality for mp3
    elif chosen_format_key == 'custom':
        options['format'] = ui.get_user_input("Enter custom yt-dlp format string", default="bestvideo+bestaudio/best")
    else: # Fallback
        options['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
    
    # Additional options (subtitles)
    extra_options_subs = [
        ('y', '📥 Download subtitles (English if available)', ''),
        ('n', '❌ Skip subtitles', ''),
    ]
    sub_choice_idx = ui.create_interactive_menu("Subtitle Options", extra_options_subs)
    if sub_choice_idx == '1':
        options['subtitles'] = True
        options['auto_subtitles'] = True # Get auto-subs if manual aren't found for the language
        options['sub_langs'] = ['en', 'en-US'] # Prioritize English subtitles
        # options['embed_subs'] = True # Ask if user wants to embed
        embed_subs_options = [('y', '🔗 Embed subtitles into video file', ''), ('n', '📄 Keep subtitles as separate files', '')]
        embed_choice = ui.create_interactive_menu("Embed Subtitles?", embed_subs_options)
        if embed_choice == '1':
            options['embed_subs'] = True

    # Additional options (thumbnail)
    extra_features_thumb = [
        ('y', '🖼️ Download thumbnail', ''),
        ('n', '❌ Skip thumbnail', ''),
    ]
    thumb_choice_idx = ui.create_interactive_menu("Thumbnail Options", extra_features_thumb)
    options['thumbnail'] = thumb_choice_idx == '1'
    
    # Set output template
    safe_title = "%(title).150s" # Limit title length for filename, allow a bit more
    output_dir_path = Path(options['output_dir']) # Already a string, Path() ensures it's a Path object
    options['output_template'] = str(output_dir_path / f"{safe_title}.%(ext)s")
    
    return options, is_newly_specified

def validate_url(url: str) -> bool:
    """Validate YouTube URL (basic check)"""
    # This is a very basic check. yt-dlp has more robust URL validation.
    # Common YouTube URL patterns
    youtube_patterns = [
        re.compile(r"^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$"),
        # Add other patterns if necessary, e.g., for music.youtube.com
    ]
    if not url or not isinstance(url, str):
        return False
    try:
        parsed = urlparse(url)
        if not all([parsed.scheme, parsed.netloc]): # Scheme and netloc must exist
             # Try adding https if missing scheme
             if not parsed.scheme and parsed.netloc:
                 parsed = urlparse("https://" + url)
             elif not parsed.scheme and not parsed.netloc and parsed.path: # Handle cases like youtu.be/xxxx
                 if "youtu.be/" in url:
                     parsed = urlparse("https://" + url)
                 else: # Could be a search term, not a URL
                     return False # Let yt-dlp handle search if that's intended behavior later
             else:
                 return False


        # Check domain (more flexible)
        # Common YouTube domains. Add more if needed (e.g. country specific, music)
        valid_domains = ['youtube.com', 'youtu.be', 'music.youtube.com']
        domain_is_valid = any(d in parsed.netloc for d in valid_domains)
        
        if not domain_is_valid:
             return False

        # Further checks (e.g., for video ID or playlist ID presence) could be added
        # For example, 'v=' for video, 'list=' for playlist in query params or path
        if "youtube.com/watch" in url:
            return "v=" in parsed.query
        if "youtu.be/" in url:
            return bool(parsed.path[1:]) # Path part after / should be video ID
        if "youtube.com/playlist" in url:
            return "list=" in parsed.query
        if "youtube.com/shorts/" in url:
            return bool(parsed.path.split('/')[-1]) # Last part of path for shorts ID
        if "youtube.com/live/" in url:
            return bool(parsed.path.split('/')[-1])

        # If it's a channel URL or other valid yt-dlp target, this simple check might not be enough.
        # Rely on yt-dlp for ultimate validation. This is a pre-check.
        return domain_is_valid # Basic domain check is enough for pre-validation

    except Exception: # Broad exception for any parsing errors
        return False


def main():
    """Enhanced main function with comprehensive features"""
    ui = ModernUI()
    spinner = ModernSpinner()
    downloader = SuperDownloader()
    
    def signal_handler(signum, frame):
        spinner.stop() # Stop spinner if active
        print(f"\n\n{Colors.WARNING}🛑 Operation interrupted by user. Exiting gracefully...{Colors.RESET}\n")
        # Perform any cleanup if necessary
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler) # Handle Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler) # Handle termination signals

    ui.print_banner()
    
    if not DependencyManager.install_missing_dependencies(spinner):
        # Error messages are printed by install_missing_dependencies
        # print(f"{Colors.ERROR}Failed to satisfy required dependencies. Exiting.{Colors.RESET}") # Redundant
        sys.exit(1)
    
    # If install_missing_dependencies printed a warning (e.g. for ffmpeg), it's already shown.
    # We can proceed if yt-dlp is available.
    if not DependencyManager.check_system_dependencies().get('yt-dlp'):
         print(f"{Colors.ERROR}Yt-dlp is not available even after installation attempt. Exiting.{Colors.RESET}")
         sys.exit(1)

    print(f"\n{Colors.SUCCESS}🚀 System ready!{Colors.RESET}")
    
    while True:
        try:
            print(f"\n{Colors.gradient_text('═' * 60, (64, 224, 255), (255, 100, 255))}")
            
            main_options = [
                ('s', '🎥 Single Video/Playlist Item', 'Download a specific video or item(s) from a playlist'),
                ('p', '📋 Full Playlist/Channel', 'Download an entire playlist or channel content'),
                ('i', '📊 Video/Playlist Info', 'Get detailed information without downloading'),
                ('q', '🚪 Quit', 'Exit the application'),
            ]
            
            choice = ui.create_interactive_menu("Main Menu", main_options)
            
            if choice == '4': # Quit
                print(f"\n{Colors.SUCCESS}👋 Thank you for using YtDorn! Goodbye!{Colors.RESET}\n")
                break
            
            url_prompt = "Enter YouTube Video/Playlist URL"
            if choice == '1': url_prompt = "Enter YouTube Video URL (or Playlist URL for specific items)"
            elif choice == '2': url_prompt = "Enter YouTube Playlist/Channel URL"
            
            url = ui.get_user_input(url_prompt, validator=validate_url)
            if not validate_url(url) and not choice == '3': # Stricter validation before download attempt
                # (validate_url might be too strict for all yt-dlp supported URLs, e.g. search terms)
                # Consider allowing yt-dlp to try if our validation fails, or improve validate_url
                print(f"{Colors.WARNING}The provided URL might not be a standard YouTube video/playlist URL. Attempting anyway...{Colors.RESET}")
                # No, for interactive, better to be sure or guide user.
                # print(f"{Colors.ERROR}Invalid YouTube URL format. Please try again.{Colors.RESET}")
                # continue

            if choice == '3': # Video info
                spinner.start("Extracting video information...")
                try:
                    info = downloader.get_video_info(url)
                    spinner.stop()
                    
                    info_items = {
                        'Title': info.get('title', 'N/A'),
                        'Uploader': info.get('uploader', 'N/A'),
                        'Duration': AdvancedProgressBar._format_duration(info.get('duration', 0)) if info.get('duration') else 'N/A (Playlist/Live)',
                        'Views': f"{info.get('view_count', 0):,}" if info.get('view_count') else 'N/A',
                        'Upload Date': info.get('upload_date', 'N/A'),
                        'Formats (est.)': str(info.get('formats', 'N/A')),
                        'Is Live': 'Yes' if info.get('is_live') else 'No',
                    }
                    if info.get('is_playlist'):
                        info_items['Type'] = 'Playlist'
                        info_items['Playlist Title'] = info.get('playlist_title', info.get('title', 'N/A')) # Use playlist_title if available
                        info_items['Video Count'] = str(info.get('playlist_count', 'N/A'))
                        if 'first_video_title' in info:
                             info_items['First Video (sample)'] = info['first_video_title']

                    ui.show_info_panel("Video Information", info_items)
                except Exception as e:
                    spinner.stop(f"{Colors.ERROR}Failed to get video info: {str(e)}{Colors.RESET}")
                continue
            
            spinner.start("Analyzing URL...")
            try:
                # Get basic info for download preview
                info_for_preview = downloader.get_video_info(url) # Reuse get_video_info
                spinner.stop()
                
                preview_title = info_for_preview.get('playlist_title' if info_for_preview.get('is_playlist') else 'title', 'Unknown Content')
                preview_type = 'Playlist' if info_for_preview.get('is_playlist') else 'Single Video'
                if choice == '2' and not info_for_preview.get('is_playlist'): # User chose full playlist but URL is single video
                    preview_type = f"Single Video (Full Playlist/Channel option was selected)"


                basic_info = {
                    'Content Title': (preview_title[:50] + '...' if len(preview_title) > 50 else preview_title),
                    'Detected Type': preview_type,
                    'Duration/Count': (f"{info_for_preview.get('playlist_count', 'N/A')} videos" if info_for_preview.get('is_playlist') 
                                        else AdvancedProgressBar._format_duration(info_for_preview.get('duration', 0)) if info_for_preview.get('duration') else 'N/A'),
                }
                ui.show_info_panel("Download Preview", basic_info)
            except Exception as e:
                spinner.stop(f"{Colors.ERROR}Error analyzing URL: {str(e)}{Colors.RESET}")
                continue
            
            options, output_dir_is_newly_specified = create_advanced_options_menu()

            if choice == '1' and info_for_preview.get('is_playlist'): # Single video from playlist
                items_to_dl = ui.get_user_input(
                    "Enter video number(s) or range (e.g., 1, 3-5, 10) (leave empty for all if intended, though 'Full Playlist' option is better for that)",
                    default="" # No default, user must specify or it might download all
                )
                if items_to_dl:
                    options['playlist_items'] = items_to_dl.strip()
                    options['no_playlist'] = False # We are dealing with playlist items
                else: # If empty, and it's a playlist, but user chose single video
                    options['noplaylist'] = True # Assume they want just the video linked if URL is watch?v=...&list=...
                    if 'list=' in url: # if URL is a video within a playlist context
                         print(f"{Colors.INFO}Downloading only the specified video from the playlist context, not the entire playlist.{Colors.RESET}")
                    else: # If URL itself is a playlist URL but they chose single and gave no items
                         print(f"{Colors.WARNING}No specific items selected from playlist. Consider 'Full Playlist' option or specify items.{Colors.RESET}")
                         # This case might be ambiguous, could default to first, or ask again.
                         # For now, yt-dlp might download the first item or the whole playlist depending on URL structure if playlist_items is not set.
                         # To be safe, if user wants specific items from a playlist, they must provide them.
                         # If they want the whole playlist, they should use option 'p'.

            elif choice == '2': # Full playlist/channel
                options['no_playlist'] = False # Ensure we download the playlist

            confirm_options_list = [
                ('y', '✅ Start Download', 'Begin downloading with selected options'),
                ('n', '❌ Cancel', 'Return to main menu'),
                ('m', '⚙️ Modify Options', 'Change download settings again'),
            ]
            
            confirm_choice = ui.create_interactive_menu("Confirm Download", confirm_options_list)
            
            if confirm_choice == '2': # Cancel
                continue
            elif confirm_choice == '3': # Modify options
                options, output_dir_is_newly_specified = create_advanced_options_menu()
                # confirm_choice = '1' # Proceed with download implicitly, or re-confirm? Let's re-confirm.
                confirm_choice = ui.create_interactive_menu("Confirm Download (after modification)", confirm_options_list)
                if confirm_choice != '1': continue # If not 'y' after modification, loop back


            if confirm_choice == '1': # Start download
                print(f"\n{Colors.PRIMARY}🚀 Starting download...{Colors.RESET}")
                
                output_directory = Path(options['output_dir'])
                try:
                    output_directory.mkdir(parents=True, exist_ok=True)
                except OSError as e:
                    print(f"{Colors.ERROR}Could not create output directory {output_directory}: {e}{Colors.RESET}")
                    continue 
                
                success = downloader.download_with_options(url, options)
                
                if success:
                    print(f"\n{Colors.SUCCESS}✨ Download completed successfully!{Colors.RESET}")
                    abs_output_dir = str(output_directory.resolve())
                    print(f"{Colors.INFO}📁 Files saved to: {abs_output_dir}{Colors.RESET}")
                    ConfigManager.add_recent_output_dir(abs_output_dir, make_default=output_dir_is_newly_specified)
                else:
                    print(f"\n{Colors.ERROR}❌ Download failed. Check messages above.{Colors.RESET}")
        
        except KeyboardInterrupt:
            # Signal handler will take care of this, but also catch here if signal handler failed or was bypassed
            spinner.stop()
            print(f"\n\n{Colors.WARNING}🛑 Operation cancelled by user.{Colors.RESET}")
            continue # Go to "Continue?" menu
        except Exception as e:
            spinner.stop()
            print(f"\n{Colors.ERROR}❌ An unexpected error occurred in the main loop: {str(e)}{Colors.RESET}")
            # logging.exception("Unexpected error in main loop:") # For debugging
            continue # Go to "Continue?" menu
            
        continue_options_list = [
            ('y', '🔄 Download Another', 'Start a new download'),
            ('n', '🚪 Exit', 'Quit the application'),
        ]
        
        continue_choice = ui.create_interactive_menu("Continue?", continue_options_list)
        if continue_choice == '2': # Exit
            print(f"\n{Colors.SUCCESS}👋 Thank you for using YtDorn! Goodbye!{Colors.RESET}\n")
            break

class BatchDownloader:
    """Handle batch downloads from file or multiple URLs"""
    
    @staticmethod
    def download_from_file(file_path: str, base_options: Dict[str, Any]) -> bool:
        """Download multiple URLs from a text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip() and not line.startswith('#')] # Ignore comments
            
            valid_urls = [url for url in urls if validate_url(url)]
            invalid_urls_count = len(urls) - len(valid_urls)

            if not valid_urls:
                print(f"{Colors.ERROR}No valid URLs found in file: {file_path}{Colors.RESET}")
                if invalid_urls_count > 0:
                    print(f"{Colors.WARNING}{invalid_urls_count} line(s) were not recognized as valid URLs.{Colors.RESET}")
                return False
            
            print(f"{Colors.INFO}Found {len(valid_urls)} valid URLs to download from {file_path}.{Colors.RESET}")
            if invalid_urls_count > 0:
                 print(f"{Colors.WARNING}{invalid_urls_count} lines were skipped (comments or invalid format).{Colors.RESET}")

            
            downloader = SuperDownloader()
            successful_downloads = 0
            
            output_dir_path = Path(base_options['output_dir'])
            try:
                output_dir_path.mkdir(parents=True, exist_ok=True)
                abs_output_dir = str(output_dir_path.resolve())
                ConfigManager.add_recent_output_dir(abs_output_dir, make_default=True) # Make batch dir default
                print(f"{Colors.INFO}Downloads will be saved to: {abs_output_dir}{Colors.RESET}")
            except OSError as e:
                print(f"{Colors.ERROR}Could not create base output directory {output_dir_path}: {e}{Colors.RESET}")
                return False


            for i, url in enumerate(valid_urls, 1):
                print(f"\n{Colors.PRIMARY}Batch Download {i}/{len(valid_urls)}: {Colors.SECONDARY}{url}{Colors.RESET}")
                # For batch, we might want to make filenames unique or put them in subfolders
                # Current 'output_template' in base_options will apply to all.
                # Could modify options per URL if needed, e.g., create subfolder based on URL or index.
                # For now, use base_options as is.
                if downloader.download_with_options(url, base_options):
                    successful_downloads += 1
                else:
                    print(f"{Colors.WARNING}⚠️ Skipping failed URL: {url}{Colors.RESET}")
            
            print(f"\n{Colors.SUCCESS}✅ Batch download completed: {successful_downloads}/{len(valid_urls)} successful.{Colors.RESET}")
            return successful_downloads == len(valid_urls) # True if all succeeded
            
        except FileNotFoundError:
            print(f"{Colors.ERROR}Batch file not found: {file_path}{Colors.RESET}")
            return False
        except Exception as e:
            print(f"{Colors.ERROR}Error processing batch file: {str(e)}{Colors.RESET}")
            # logging.exception("Error in batch download:") # For debugging
            return False

class ConfigManager:
    """Manage user configurations and presets"""
    
    CONFIG_FILE = str(Path.home() / ".ytdorn_config.json") # Ensure it's a string for open()

    @staticmethod
    def load_config() -> Dict[str, Any]:
        """Load user configuration"""
        try:
            if Path(ConfigManager.CONFIG_FILE).exists():
                with open(ConfigManager.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Ensure essential keys exist from default if missing in loaded config
                    default_conf = ConfigManager._get_default_config()
                    for key, value in default_conf.items():
                        if key not in config:
                            config[key] = value
                        # Specifically for presets, merge rather than overwrite
                        elif key == 'presets' and isinstance(value, dict) and isinstance(config[key], dict):
                            for p_key, p_value in value.items():
                                if p_key not in config[key]:
                                    config[key][p_key] = p_value
                    return config
        except json.JSONDecodeError:
            print(f"{Colors.WARNING}Configuration file {ConfigManager.CONFIG_FILE} is corrupted. Using defaults.{Colors.RESET}")
            # Optionally, backup corrupted file and save a new default one
            Path(ConfigManager.CONFIG_FILE).rename(ConfigManager.CONFIG_FILE + ".corrupted_" + datetime.now().strftime("%Y%m%d%H%M%S"))
        except Exception as e:
            print(f"{Colors.WARNING}Could not load config: {e}. Using defaults.{Colors.RESET}")
        
        new_config = ConfigManager._get_default_config()
        ConfigManager.save_config(new_config) # Save a fresh default config if load failed or file not found
        return new_config
    
    @staticmethod
    def save_config(config: Dict[str, Any]) -> bool:
        """Save user configuration"""
        try:
            with open(ConfigManager.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"{Colors.ERROR}Could not save config to {ConfigManager.CONFIG_FILE}: {e}{Colors.RESET}")
            return False
    
    @staticmethod
    def _get_default_config() -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'default_output_dir': str(Path.home() / 'Downloads' / 'YtDorn'), # More specific default
            'recent_output_dirs': [],
            'default_format': 'best', # This is a general default, specific format keys are used in menus
            'auto_subtitles': False, # User is prompted for subtitles
            'download_thumbnails': False, # User is prompted
            'concurrent_downloads': 3, # Not fully implemented for UI
            'presets': {
                'high_quality_mp4': {
                    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                    'subtitles': True, 'embed_subs': True, 'sub_langs': ['en', 'en-US'],
                    'thumbnail': True, 'description_file': True, 'metadata_json': True,
                    'output_dir': str(Path.home() / 'Videos' / 'YtDorn_HQ'),
                },
                'audio_mp3_collection': {
                    'format': 'bestaudio/best', 'extract_audio': True,
                    'audio_format': 'mp3', 'audio_quality': '192K',
                    'thumbnail': True, # Album art often embedded from thumbnail
                    'output_dir': str(Path.home() / 'Music' / 'YtDorn_MP3s'),
                },
                'archive_data_saver': {
                    'format': 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best[height<=480]',
                    'subtitles': True, 'sub_langs': ['en'],
                    'output_dir': str(Path.home() / 'Videos' / 'YtDorn_Archive_SD'),
                }
            }
        }

    @staticmethod
    def add_recent_output_dir(output_path: str, make_default: bool = False, max_recent: int = 5):
        config = ConfigManager.load_config()
        recent_dirs = config.get('recent_output_dirs', [])
        if not isinstance(recent_dirs, list): recent_dirs = [] # Ensure it's a list
        
        try:
            abs_path = str(Path(output_path).resolve())
        except Exception: # If path is malformed
            return # Do not add invalid paths

        if abs_path in recent_dirs:
            recent_dirs.remove(abs_path)
        
        recent_dirs.insert(0, abs_path)
        config['recent_output_dirs'] = recent_dirs[:max_recent]
        
        if make_default:
            config['default_output_dir'] = abs_path
            
        ConfigManager.save_config(config)


def setup_argument_parser() -> argparse.ArgumentParser:
    """Setup command line argument parser"""
    parser = argparse.ArgumentParser(
        description='YtDorn v0.1.2 - Super Powerful YouTube Downloader by 0xb0rn3.',
        formatter_class=argparse.RawTextHelpFormatter, # Using RawTextHelpFormatter for better control over epilog
        epilog=f"""
{Colors.PRIMARY}Examples:{Colors.RESET}
  %(prog)s                                  # Interactive mode (default)
  %(prog)s -u "VIDEO_URL"                    # Quick download with best quality to default folder
  %(prog)s -u "VIDEO_URL" -f 720p -o "MyVideos" # Download 720p to MyVideos
  %(prog)s -u "VIDEO_URL" --preset audio_mp3_collection # Download using a preset
  %(prog)s --batch urls.txt --preset high_quality_mp4 # Batch download with preset
  %(prog)s --info "VIDEO_URL"                # Get video info (JSON output)
  %(prog)s --list-presets                    # List available presets and exit
  %(prog)s --config                          # Open configuration file location (planned)

{Colors.PRIMARY}Available format keys for -f/--format (CLI):{Colors.RESET}
  best, 1080p, 720p, 480p, audio, mp3, or any valid yt-dlp format string.

{Colors.MUTED}Full documentation and more examples at the project's repository.{Colors.RESET}
"""
    )
    
    # General options
    parser.add_argument('--version', action='version', version='%(prog)s v0.1.2')
    parser.add_argument('--quiet', '-q', action='store_true', help='Minimal output (non-interactive). Errors still shown.')

    # URL and Batch processing
    parser.add_argument('-u', '--url', metavar='URL', help='YouTube video/playlist URL.')
    parser.add_argument('--batch', metavar='FILE', help='File containing list of URLs to download (one URL per line).')

    # Output options
    parser.add_argument('-o', '--output', metavar='DIRECTORY',
                        help='Output directory. If not set, uses default from config or "YtDorn_Downloads".')
    parser.add_argument('--output-template', metavar='TEMPLATE',
                        help='Custom output filename template (yt-dlp format). Overrides default.')


    # Format and Quality
    parser.add_argument('-f', '--format', metavar='FORMAT_KEY',
                        help='Video/audio format. Keys: best, 1080p, 720p, 480p, audio, mp3, or yt-dlp format string.')
    parser.add_argument('--extract-audio', action='store_true', help='Extract audio only. Sets format to bestaudio.')
    parser.add_argument('--audio-format', metavar='CODEC', default='mp3',
                        help='Audio codec for extraction (e.g., mp3, m4a, wav, flac). Default: mp3.')
    parser.add_argument('--audio-quality', metavar='QUALITY', default='192K',
                        help='Audio quality (e.g., 192K for mp3 CBR, 0-9 for VBR). Default: 192K.')

    # Metadata and Extras
    parser.add_argument('--subtitles', action='store_true', help='Download subtitles (default: English).')
    parser.add_argument('--sub-langs', metavar='LANGS', default='en,en-US',
                        help='Subtitle languages (comma-separated, e.g., en,es,fr). Default: en,en-US.')
    parser.add_argument('--embed-subs', action='store_true', help='Embed subtitles into video file (if downloading video).')
    parser.add_argument('--thumbnail', action='store_true', help='Download video thumbnail.')
    parser.add_argument('--description-file', action='store_true', help='Write video description to a .description file.')
    parser.add_argument('--metadata-json', action='store_true', help='Write video metadata to a .info.json file.')

    # Playlist specific
    parser.add_argument('--playlist-items', metavar='ITEMS',
                        help='Specific items to download from a playlist (e.g., "1,3-5,10").')
    parser.add_argument('--no-playlist', action='store_true',
                        help='If URL is a video in a playlist, download only the video, not the playlist.')


    # Configuration and Info
    parser.add_argument('--preset', metavar='PRESET_NAME', help='Use a saved configuration preset.')
    parser.add_argument('--list-presets', action='store_true', help='List available presets and exit.')
    parser.add_argument('--info', metavar="URL_FOR_INFO", help='Get video/playlist information as JSON and exit.')
    # parser.add_argument('--config', action='store_true', help='Show path to config file and exit (planned).')
    
    return parser

def run_cli_mode(args: argparse.Namespace, config: Dict[str, Any]):
    """Run in command line mode with arguments"""
    if args.list_presets:
        print(f"{Colors.PRIMARY}{Colors.BOLD}Available Presets:{Colors.RESET}")
        if config['presets']:
            for name, settings in config['presets'].items():
                print(f"  {Colors.SUCCESS}{name}{Colors.RESET}:")
                for key, value in settings.items():
                    print(f"    {key}: {Colors.SECONDARY}{value}{Colors.RESET}")
        else:
            print(f"  {Colors.MUTED}No presets defined in configuration.{Colors.RESET}")
        sys.exit(0)
    
    downloader = SuperDownloader()

    if args.info:
        if not args.quiet: print(f"{Colors.INFO}Fetching information for: {args.info}{Colors.RESET}")
        try:
            info_data = downloader.get_video_info(args.info) # Already processed by _process_video_info
            print(json.dumps(info_data, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"{Colors.ERROR}Error fetching info: {str(e)}{Colors.RESET}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)
    
    # Build options from command line arguments and config defaults
    cli_options: Dict[str, Any] = {}

    # Output directory
    cli_options['output_dir'] = args.output if args.output else config.get('default_output_dir', 'YtDorn_Downloads_CLI')
    
    # Format mapping from CLI key to yt-dlp format string / options
    # This mirrors interactive logic but for CLI args.
    chosen_format_key_cli = args.format if args.format else config.get('default_format_cli', 'best') # Default to 'best'

    if args.extract_audio: # Override format if --extract-audio is specified
        chosen_format_key_cli = 'audio' # Signal audio extraction
        cli_options['extract_audio'] = True
        cli_options['audio_format'] = args.audio_format
        cli_options['audio_quality'] = args.audio_quality
    
    if chosen_format_key_cli == 'best':
        cli_options['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
    elif chosen_format_key_cli == '1080p':
        cli_options['format'] = 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best[height<=1080]'
    elif chosen_format_key_cli == '720p':
        cli_options['format'] = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best[height<=720]'
    elif chosen_format_key_cli == '480p':
        cli_options['format'] = 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best[height<=480]'
    elif chosen_format_key_cli == 'audio': # Handles --extract-audio case too
        cli_options['format'] = 'bestaudio/best'
        cli_options['extract_audio'] = True
        cli_options['audio_format'] = args.audio_format
        cli_options['audio_quality'] = args.audio_quality
    elif chosen_format_key_cli == 'mp3':
        cli_options['format'] = 'bestaudio/best'
        cli_options['extract_audio'] = True
        cli_options['audio_format'] = 'mp3'
        cli_options['audio_quality'] = args.audio_quality
    else: # Assumed to be a direct yt-dlp format string
        cli_options['format'] = chosen_format_key_cli
        if args.extract_audio: # if user provides custom format AND --extract-audio
            cli_options['extract_audio'] = True # ensure audio extraction settings are honored
            cli_options['audio_format'] = args.audio_format
            cli_options['audio_quality'] = args.audio_quality


    # Metadata and extras
    cli_options['subtitles'] = args.subtitles
    if args.subtitles:
        cli_options['sub_langs'] = args.sub_langs.split(',') if args.sub_langs else ['en']
        cli_options['embed_subs'] = args.embed_subs
        cli_options['auto_subtitles'] = True # Usually desired if asking for subs

    cli_options['thumbnail'] = args.thumbnail
    cli_options['description_file'] = args.description_file
    cli_options['metadata_json'] = args.metadata_json

    # Playlist handling
    cli_options['playlist_items'] = args.playlist_items
    cli_options['no_playlist'] = args.no_playlist
    
    # Apply preset if specified (overrides individual CLI options set before preset)
    if args.preset:
        if args.preset in config['presets']:
            if not args.quiet: print(f"{Colors.INFO}Applying preset: {args.preset}{Colors.RESET}")
            # Preset values override CLI args if they conflict, unless CLI arg was explicitly set for that specific option type
            # A more sophisticated merge could be done (e.g. CLI always wins if provided)
            # For simplicity, preset.update(cli_options_explicitly_set) or cli_options.update(preset)
            # Current: preset values are primary, then fill in with CLI if not in preset.
            # Better: CLI args specified by user should override preset.
            
            preset_settings = config['presets'][args.preset].copy()
            # Merge: start with preset, then update with any CLI args that were actually provided by user
            # We need to distinguish args that had default values vs user-set
            
            temp_options_from_cli = {k: v for k, v in vars(args).items() if getattr(parser.get_default(k), 'value', getattr(parser.get_default(k), 'default', None)) != v}

            # Sensible merge: preset forms base, args overwrite specific fields from preset
            merged_opts = preset_settings.copy() # Start with preset
            
            # Map arg names to option keys if different, or directly update
            # output_dir from preset can be overridden by args.output
            if args.output: merged_opts['output_dir'] = args.output
            # format from preset can be overridden by args.format (after key mapping)
            if args.format or args.extract_audio: # If user specified format or audio extraction
                 merged_opts.update({k:v for k,v in cli_options.items() if k in ['format', 'extract_audio', 'audio_format', 'audio_quality']})
            
            if args.subtitles: merged_opts['subtitles'] = True; merged_opts['sub_langs'] = cli_options['sub_langs']; merged_opts['embed_subs'] = cli_options['embed_subs']
            if args.thumbnail: merged_opts['thumbnail'] = True
            # ... and so on for other overridable options
            
            cli_options = merged_opts # Use the merged options
            
        else:
            print(f"{Colors.ERROR}Preset '{args.preset}' not found in configuration.{Colors.RESET}", file=sys.stderr)
            sys.exit(1)
    
    # Output template
    if args.output_template:
        cli_options['output_template'] = args.output_template
    else:
        # Use a consistent safe title format if not overridden by preset or CLI
        safe_title_cli = cli_options.get('output_template_title_format', "%(title).150s")
        output_dir_for_template = Path(cli_options['output_dir'])
        cli_options['output_template'] = str(output_dir_for_template / f"{safe_title_cli}.%(ext)s")

    # Ensure output directory exists
    final_output_dir = Path(cli_options['output_dir'])
    try:
        final_output_dir.mkdir(parents=True, exist_ok=True)
        if not args.quiet:
            print(f"{Colors.INFO}Output directory: {final_output_dir.resolve()}{Colors.RESET}")
    except OSError as e:
        print(f"{Colors.ERROR}Cannot create output directory {final_output_dir}: {e}{Colors.RESET}", file=sys.stderr)
        sys.exit(1)

    # Add to recent dirs (even for CLI)
    ConfigManager.add_recent_output_dir(str(final_output_dir.resolve()), make_default=True)


    if args.batch:
        if not args.quiet: print(f"{Colors.PRIMARY}Starting batch download from: {args.batch}{Colors.RESET}")
        success = BatchDownloader.download_from_file(args.batch, cli_options)
        sys.exit(0 if success else 1)
    
    elif args.url:
        if not validate_url(args.url):
            # For CLI, be more permissive or rely on yt-dlp's more extensive validation
            if not args.quiet: print(f"{Colors.WARNING}URL validation failed for '{args.url}', but attempting download anyway...{Colors.RESET}")
            # No, if user provides bad URL, it should fail early.
            # print(f"{Colors.ERROR}Invalid YouTube URL provided: {args.url}{Colors.RESET}", file=sys.stderr)
            # sys.exit(1)


        if not args.quiet: print(f"{Colors.PRIMARY}Starting download for: {args.url}{Colors.RESET}")
        success = downloader.download_with_options(args.url, cli_options)
        if not args.quiet and success:
             print(f"{Colors.SUCCESS}Download completed successfully.{Colors.RESET}")
        elif not args.quiet and not success:
             print(f"{Colors.ERROR}Download failed.{Colors.RESET}")
        sys.exit(0 if success else 1)
    
    else:
        # This case should ideally not be reached if parser is setup with URL as required for non-interactive
        # or if interactive mode is default. But as a fallback:
        parser.print_help() # Show help if no action is specified for CLI
        print(f"\n{Colors.ERROR}No URL, batch file, or info request specified for command-line mode.{Colors.RESET}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    # Basic logging setup (optional, for deeper debugging)
    # logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Load configuration first
    config = ConfigManager.load_config() # Load config once

    parser = setup_argument_parser()
    args = parser.parse_args()

    # Determine if running in CLI mode based on presence of specific args
    # These args imply user wants CLI, not interactive mode.
    # Default values for these are None or False.
    cli_mode_indicators = [
        args.url,
        args.batch,
        args.info,
        args.list_presets,
        # args.quiet # Quiet implies CLI but isn't an action itself
    ]

    try:
        if any(cli_mode_indicators):
            if args.quiet:
                # Suppress most print statements if quiet mode (handled within run_cli_mode where appropriate)
                # Or, redirect stdout for non-essential prints. For now, rely on checks.
                pass
            run_cli_mode(args, config)
        else:
            # Default to interactive mode if no CLI-specific action args are given
            main() 
            
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}🛑 Application interrupted by user. Goodbye!{Colors.RESET}")
        sys.exit(0)
    except Exception as e:
        # This is a final catch-all for unexpected top-level errors
        print(f"{Colors.ERROR}A critical error occurred: {str(e)}{Colors.RESET}")
        # logging.exception("Critical error at top level:") # For debugging
        sys.exit(1)
