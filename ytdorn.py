#!/usr/bin/env python3
"""
YtDorn - Universal Multi-Downloader Tool
Version: 0.1.3
Supports: YouTube (Videos, Playlists, Channels), Torrents (via libtorrent), Generic URLs
Features: Auto-dependency installation, aria2c for speed, basic config management.
"""

import os
import sys
import subprocess
import json
import time
import shutil
import importlib
from pathlib import Path
from typing import Optional, Dict, List, Any
import shlex # For safely formatting command strings for display

# Global flags, will be set after checking/installing dependencies
PSUTIL_AVAILABLE = False
LIBTORRENT_AVAILABLE = False
LT_MODULE = None # To store the imported libtorrent module

class YtDorn:
    def __init__(self):
        self.version = "0.1.3"
        self._check_and_install_dependencies() # Critical first step

        self.current_dir = Path.cwd()
        self.download_dir = self.current_dir / "YtDorn_Downloads_v013" # Default, version specific
        self.config_dir = Path.home() / ".ytdorn"
        self.config_file = self.config_dir / "config.json"
        
        self.ensure_config_dir()
        self.config = self.load_config()
        
        self.download_dir = Path(self.config.get('download_dir', str(self.download_dir)))
        self.ensure_download_dir()

        self.torrent_session: Optional[Any] = None
        self.active_torrent_handles: Dict[str, Any] = {}

        self.aria2c_path = shutil.which("aria2c")
        
        if LIBTORRENT_AVAILABLE:
            self.setup_torrent_session_on_init()

    def _install_package(self, package_name: str, import_name: Optional[str] = None) -> bool:
        if import_name is None:
            import_name = package_name
        
        print(f"↪️ Attempting to install '{package_name}'...")
        pip_command = [sys.executable, "-m", "pip", "install", package_name]
        
        # Add --break-system-packages for Linux environments that require it
        # This is a common requirement on newer Debian/Ubuntu systems for global pip installs
        if sys.platform.startswith("linux"):
            # A more robust check would be to see if pip is externally managed.
            # For now, broadly applying for Linux as requested.
            pip_command.append("--break-system-packages")
            
        try:
            subprocess.check_call(pip_command)
            print(f"✅ Successfully installed '{package_name}'.")
            importlib.import_module(import_name) # Verify import
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install '{package_name}' using pip. Return code: {e.returncode}")
            print(f"   Command: {' '.join(pip_command)}")
            # Attempt to decode stderr if it's bytes
            stderr_output = e.stderr
            if isinstance(stderr_output, bytes):
                stderr_output = stderr_output.decode(errors='replace')
            print(f"   Error output: {stderr_output}")
            print(f"   You may need to install it manually or ensure pip has necessary permissions.")
        except ImportError:
            print(f"❌ Installed '{package_name}', but failed to import '{import_name}'.")
        except Exception as e:
            print(f"❌ An unexpected error occurred during installation of '{package_name}': {e}")
        return False

    def _check_and_install_dependencies(self):
        global PSUTIL_AVAILABLE, LIBTORRENT_AVAILABLE, LT_MODULE
        
        dependencies = {
            "yt-dlp": ("yt_dlp", True, "YouTube and generic URL downloads"),
            "psutil": ("psutil", False, "Detailed system/storage information"),
            "python-libtorrent": ("libtorrent", False, "Torrent downloading features"),
        }
        
        missing_deps_to_install = []
        print("--- Initial Dependency Check (YtDorn v0.1.3) ---")

        for pip_name, (import_name, is_critical, purpose) in dependencies.items():
            try:
                module = importlib.import_module(import_name)
                print(f"✔️ {import_name}: Found")
                if import_name == "psutil": PSUTIL_AVAILABLE = True
                if import_name == "libtorrent":
                    LIBTORRENT_AVAILABLE = True
                    LT_MODULE = module
            except ImportError:
                print(f"⚠️ {import_name}: Not found ({purpose})")
                missing_deps_to_install.append({'pip_name': pip_name, 'import_name': import_name, 'is_critical': is_critical})

        if missing_deps_to_install:
            print("\n-------------------------------------------------------------")
            print("The following dependencies are missing or not found:")
            for dep in missing_deps_to_install:
                critical_status = "(Critical!)" if dep['is_critical'] else "(Optional)"
                print(f"  - {dep['pip_name']} (module: {dep['import_name']}) {critical_status}")
            print("-------------------------------------------------------------")
            
            try:
                choice = input("Attempt automatic installation using pip? (y/N): ").strip().lower()
            except EOFError: choice = 'n'; print("Non-interactive environment: Skipping auto-install.")

            if choice == 'y':
                successfully_installed_all_critical = True
                for dep in missing_deps_to_install:
                    if self._install_package(dep['pip_name'], dep['import_name']):
                        if dep['import_name'] == "psutil": PSUTIL_AVAILABLE = True
                        if dep['import_name'] == "libtorrent":
                            try:
                                LT_MODULE = importlib.import_module(dep['import_name'])
                                LIBTORRENT_AVAILABLE = True
                            except ImportError:
                                LIBTORRENT_AVAILABLE = False
                                if dep['is_critical']: successfully_installed_all_critical = False
                    elif dep['is_critical']:
                        successfully_installed_all_critical = False
                
                if not successfully_installed_all_critical:
                    print("\n❌ Not all critical dependencies could be installed. Key features might not work.")
                    # Specific check for yt-dlp as it's most critical
                    try: importlib.import_module("yt_dlp")
                    except ImportError:
                        print("CRITICAL FAILURE: yt-dlp is still missing after install attempt.")
                        if input("Exit application due to missing yt-dlp? (Y/n): ").strip().lower() != 'n':
                             sys.exit("Exiting: yt-dlp is essential and could not be installed.")
            else:
                print("Skipping automatic installation.")
                try: importlib.import_module("yt_dlp")
                except ImportError:
                    print("CRITICAL: yt-dlp not found and installation skipped. Most features will fail. Exiting.")
                    sys.exit(1)
        
        print("--- Dependency Check Complete ---\n")
        time.sleep(0.5)

    def ensure_config_dir(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def load_config(self) -> Dict:
        default_config = {
            'download_dir': str(self.download_dir),
            'favorite_dirs': [],
            'default_yt_quality': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'yt_output_template_video': "%(uploader)s/%(title)s [%(id)s].%(ext)s",
            'yt_output_template_playlist': "%(uploader)s/%(playlist_title)s/%(playlist_index)s - %(title)s [%(id)s].%(ext)s",
            'yt_output_template_channel': "%(uploader)s/%(channel)s/%(playlist_title,NA)s/%(title)s [%(id)s].%(ext)s",
            'torrent_save_path': str(self.download_dir / "Torrents"),
            'torrent_port_min': 6881,
            'torrent_port_max': 6891,
            'use_aria2c_if_available': True,
        }
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                merged_config = default_config.copy()
                merged_config.update(saved_config)
                return merged_config
            except (json.JSONDecodeError, KeyError) as e:
                print(f"⚠️ Config file '{self.config_file}' corrupted ({e}). Backing up and using defaults.")
                try: shutil.move(str(self.config_file), str(self.config_file) + ".corrupted")
                except Exception as move_err: print(f"Could not backup corrupted config: {move_err}")
                # Fall through to create new default config
            except Exception as e: # Catch other potential errors like permission issues
                 print(f"⚠️ Error loading config '{self.config_file}': {e}. Using defaults.")


        # Create new default config if file doesn't exist or was corrupted
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2)
            print(f"✅ Default configuration file created/recreated at '{self.config_file}'.")
        except Exception as save_e:
            print(f"❌ CRITICAL: Could not write default config to '{self.config_file}': {save_e}")
        return default_config

    def save_config(self):
        self.config['download_dir'] = str(self.download_dir)
        self.config['torrent_save_path'] = str(Path(self.config.get('torrent_save_path', self.download_dir / "Torrents")))
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e: print(f"⚠️ Could not save config: {e}")

    def ensure_download_dir(self):
        try:
            self.download_dir.mkdir(parents=True, exist_ok=True)
            Path(self.config.get('torrent_save_path', self.download_dir / "Torrents")).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"❌ CRITICAL: Could not create download directories: {e}. Please check permissions.")
            sys.exit("Directory creation failed.")


    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def show_header(self, title=""):
        self.clear_screen()
        print("=" * 70)
        print(f"🎬 YtDorn Universal Downloader v{self.version} 🎬")
        if title: print(f"--- {title} ---")
        print("=" * 70)
        print(f"💾 Default Download Location: {self.download_dir}")
        if self.aria2c_path and self.config.get('use_aria2c_if_available'):
            print(f"🚀 aria2c detected. Using for faster YouTube/HTTP downloads (if enabled).")
        elif not self.aria2c_path and self.config.get('use_aria2c_if_available'):
            print(f"💨 aria2c not found. Install for potentially faster YouTube/HTTP downloads.")
        print("-" * 70)
        
    def main_loop(self):
        while True:
            self.show_header("Main Menu")
            print("\nChoose Download Type or Action:")
            print("  [YouTube Downloader]")
            print("    1. Download Single YouTube Video")
            print("    2. Download YouTube Playlist")
            print("    3. Download Entire YouTube Channel")
            print("\n  [Other Downloaders]")
            print("    4. Download from Generic URL (HTTP/S, FTP, etc.)")
            print("    5. Download Torrent")
            print("\n  [Management & Utilities]")
            print("    N. Navigate Directories & Set Download Location (TODO)")
            print("    S. Storage Overview (TODO)")
            print("    F. Manage Favorite Locations (TODO)")
            print("    C. Configuration Settings (TODO)")
            print("    D. Check Dependencies (Interactive)")
            print("    X. Exit YtDorn")

            choice = input("\nEnter your choice: ").strip().lower()

            actions = {
                '1': self.download_youtube_single_interactive,
                '2': self.download_youtube_playlist_interactive,
                '3': self.download_youtube_channel_interactive,
                '4': self.download_generic_url_interactive,
                '5': self.download_torrent_interactive,
                'n': self.navigate_directory_placeholder,
                's': self.show_storage_overview_placeholder,
                'f': self.manage_favorites_placeholder,
                'c': self.show_configuration_menu_placeholder,
                'd': self.check_dependencies_interactive,
            }

            if choice == 'x':
                print("\n👋 Exiting YtDorn. Goodbye!")
                if self.torrent_session and LIBTORRENT_AVAILABLE:
                    print("Shutting down torrent session...")
                    # self.torrent_session.pause() # Consider graceful shutdown
                break
            elif choice in actions:
                actions[choice]()
            else:
                print("❌ Invalid choice. Please try again.")
            
            if choice != 'x': 
                input("\nPress Enter to return to menu...")

    def check_dependencies_interactive(self):
        global PSUTIL_AVAILABLE, LIBTORRENT_AVAILABLE, LT_MODULE
        self.show_header("Dependency Check (Interactive)")
        print("Status of required and optional dependencies:\n")
        
        try: # yt-dlp
            importlib.import_module("yt_dlp")
            result = subprocess.run(['yt-dlp', '--version'], capture_output=True, check=True, text=True, encoding='utf-8', errors='replace')
            print(f"✅ yt-dlp: Installed ({result.stdout.strip()})")
        except: print("❌ yt-dlp: NOT INSTALLED or not in PATH. (Critical)")

        # psutil
        if PSUTIL_AVAILABLE:
            try:
                import psutil as psutil_check
                print(f"✅ psutil: Installed (Version: {psutil_check.__version__})")
            except: print(f"⚠️ psutil: Auto-detected but failed to import now.")
        else: print("⚠️ psutil: Not installed. (Optional, for detailed storage overview)")
        
        # libtorrent
        if LIBTORRENT_AVAILABLE and LT_MODULE:
            print(f"✅ libtorrent: Installed (Version: {LT_MODULE.version})")
        else: print("❌ libtorrent: NOT INSTALLED. (Required for Torrent downloads)")

        # aria2c
        self.aria2c_path = shutil.which("aria2c") 
        if self.aria2c_path:
            try:
                result = subprocess.run([self.aria2c_path, '--version'], capture_output=True, text=True, check=True, encoding='utf-8', errors='replace')
                print(f"✅ aria2c: Installed ({result.stdout.splitlines()[0].strip()})")
            except: print(f"⚠️ aria2c: Detected but version check failed.")
        else: print("⚠️ aria2c: Not found. (Optional, for faster segmented downloads)")
        
        # ffmpeg
        if shutil.which("ffmpeg"): print(f"✅ ffmpeg: Detected. (Recommended for yt-dlp)")
        else: print("⚠️ ffmpeg: Not found. (Optional, yt-dlp may have limited format options)")

    def _run_yt_dlp_command(self, command_args: List[str], title: str = "yt-dlp process") -> bool:
        print(f"\n🔄 Starting: {title}")
        safe_display_args = ' '.join(shlex.quote(str(arg)) for arg in command_args) # Ensure all args are strings
        print(f"   Command: yt-dlp {safe_display_args}")
        
        final_command = ['yt-dlp'] + [str(arg) for arg in command_args] # Ensure all args are strings
        
        if self.aria2c_path and self.config.get('use_aria2c_if_available', True):
            is_downloader_set = any(arg.startswith('--downloader') for arg in command_args)
            if not is_downloader_set:
                 final_command.extend(['--downloader', 'aria2c'])
                 # Example aria2c args for better performance on good connections
                 final_command.extend(['--downloader-args', 'aria2c:-j16 -x16 -s16 -k1M'])


        try:
            process = subprocess.Popen(final_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace')
            spinner = ['-', '\\', '|', '/']; idx = 0
            while process.poll() is None:
                print(f"\r   Progress: {spinner[idx % len(spinner)]} Running...", end=""); idx+=1; time.sleep(0.2)
            stdout, stderr = process.communicate(timeout=3600) # Add a long timeout
            print("\r", " " * 40, "\r", end="") 

            if process.returncode == 0:
                print(f"✅ Success: {title} completed."); return True
            else:
                print(f"❌ Error: {title} failed (Code: {process.returncode}).")
                if stderr: print("   yt-dlp STDERR:\n", '\n'.join([f"     {line}" for line in stderr.splitlines()]))
                if stdout: print("   yt-dlp STDOUT:\n", '\n'.join([f"     {line}" for line in stdout.splitlines()]))
                return False
        except subprocess.TimeoutExpired:
            print(f"❌ Timeout: {title} took too long and was terminated.")
            process.kill()
            return False
        except FileNotFoundError: print("❌ CRITICAL: yt-dlp command not found."); return False
        except Exception as e: print(f"❌ Unexpected error running yt-dlp: {e}"); return False

    def _get_yt_dlp_json_info(self, url: str, extra_args: Optional[List[str]] = None) -> Optional[Dict]:
        command = ['yt-dlp', '--quiet', '--no-warnings', '--dump-single-json', '--skip-download']
        if extra_args: command.extend(extra_args)
        command.append(url)
        
        print(f"ℹ️  Fetching info for: {url}...")
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8', errors='replace', timeout=60)
            return json.loads(result.stdout)
        except subprocess.TimeoutExpired:
            print(f"❌ Timeout fetching info for {url}.")
            return None
        except subprocess.CalledProcessError as e:
            stderr_output = e.stderr.strip() if e.stderr else "No stderr output."
            print(f"❌ Error fetching info with yt-dlp for {url}. Code: {e.returncode}\n   Stderr: {stderr_output}")
            return None
        except json.JSONDecodeError: print(f"❌ Error decoding JSON from yt-dlp for {url}."); return None
        except Exception as e: print(f"❌ Unexpected error fetching info: {e}"); return None

    def download_youtube_single_interactive(self):
        self.show_header("Download Single YouTube Video")
        url = input("Enter YouTube video URL: ").strip()
        if not url: print("❌ No URL entered."); return
        info = self._get_yt_dlp_json_info(url)
        if not info: return
        print(f"\n🎥 Video Found:\n   Title: {info.get('title', 'N/A')}\n   Uploader: {info.get('uploader', 'N/A')}\n   Duration: {time.strftime('%H:%M:%S', time.gmtime(info.get('duration', 0)))}")
        if input("\nProceed with download? (y/N): ").lower() != 'y': print("Download cancelled."); return
        
        output_path_base = self.download_dir / "YouTube" / "Single Videos"
        output_path_base.mkdir(parents=True, exist_ok=True)
        output_template = str(output_path_base / self.config.get('yt_output_template_video'))
        
        args = ['--format', self.config.get('default_yt_quality'), '--output', output_template, url]
        self._run_yt_dlp_command(args, title=f"Downloading '{info.get('title', 'video')}'")

    def download_youtube_playlist_interactive(self):
        self.show_header("Download YouTube Playlist")
        url = input("Enter YouTube playlist URL: ").strip()
        if not url: print("❌ No URL entered."); return
        info = self._get_yt_dlp_json_info(url, ['--flat-playlist']) # Fast way to get count and title
        if not info: return
        
        video_count = info.get('playlist_count', len(info.get('entries', [])))
        print(f"\n🎶 Playlist Found:\n   Title: {info.get('title', 'N/A')}\n   Uploader: {info.get('uploader', 'N/A')}\n   Videos: {video_count}")
        if video_count == 0: print("   Playlist appears empty."); return
        if input("\nProceed with download? (y/N): ").lower() != 'y': print("Download cancelled."); return

        output_path_base = self.download_dir / "YouTube" / "Playlists"
        # Output template itself should create subfolder for playlist name
        output_template = str(output_path_base / self.config.get('yt_output_template_playlist'))
        
        args = ['--format', self.config.get('default_yt_quality'), '--output', output_template, '--yes-playlist', '--ignore-errors', url]
        self._run_yt_dlp_command(args, title=f"Downloading playlist '{info.get('title', 'playlist')}'")

    def download_youtube_channel_interactive(self):
        self.show_header("Download YouTube Channel")
        url = input("Enter YouTube channel URL: ").strip()
        if not url: print("❌ No URL entered."); return
        info = self._get_yt_dlp_json_info(url, ['--flat-playlist']) # Fast way to get count and title
        if not info: return
        
        video_count = info.get('playlist_count', len(info.get('entries', []))) # yt-dlp treats channel as a type of playlist
        print(f"\n📺 Channel Found:\n   Name: {info.get('uploader', info.get('channel', 'N/A'))}\n   Title: {info.get('title', 'N/A')}\n   Videos: {video_count}")
        if video_count == 0: print("   Channel appears empty or has no public videos."); return
        print("\n   Note: This will download all public videos. Use output templates for organization.")
        if input("\nProceed with download? (y/N): ").lower() != 'y': print("Download cancelled."); return

        output_path_base = self.download_dir / "YouTube" / "Channels"
        output_template = str(output_path_base / self.config.get('yt_output_template_channel'))
        
        args = ['--format', self.config.get('default_yt_quality'), '--output', output_template, '--ignore-errors', url]
        self._run_yt_dlp_command(args, title=f"Downloading channel '{info.get('title', 'channel')}'")

    def download_generic_url_interactive(self):
        self.show_header("Download from Generic URL")
        url = input("Enter URL to download: ").strip()
        if not url: print("❌ No URL entered."); return
        
        default_filename = url.split('/')[-1].split('?')[0] if url.split('/')[-1] else "downloaded_file"
        filename = input(f"Enter filename (default: '{default_filename}'): ").strip() or default_filename
        
        output_path_base = self.download_dir / "Generic Downloads"
        output_path_base.mkdir(parents=True, exist_ok=True)
        output_target = str(output_path_base / filename)
        
        print(f"\nAttempting to download from: {url}\nSaving as: {output_target}")
        if input("\nProceed? (y/N): ").lower() != 'y': print("Download cancelled."); return
        args = ['--output', output_target, url]
        self._run_yt_dlp_command(args, title=f"Downloading '{filename}'")

    def setup_torrent_session_on_init(self):
        global LT_MODULE
        if not LIBTORRENT_AVAILABLE or not LT_MODULE: return False
        if self.torrent_session: return True
        try:
            settings = {
                'listen_interfaces': f'0.0.0.0:{self.config.get("torrent_port_min")},[::]:{self.config.get("torrent_port_min")}',
                'user_agent': f'YtDorn/{self.version} libtorrent/{LT_MODULE.version}',
                'alert_mask': LT_MODULE.alert_category.status | LT_MODULE.alert_category.storage | LT_MODULE.alert_category.error,
                'dht_bootstrap_nodes': 'dht.libtorrent.org:25401,router.utorrent.com:6881,router.bittorrent.com:6881,dht.transmissionbt.com:6881'
            }
            self.torrent_session = LT_MODULE.session(settings)
            print(f"✅ Torrent session initialized (libtorrent {LT_MODULE.version}).")
            return True
        except Exception as e: print(f"❌ Failed to initialize torrent session: {e}"); self.torrent_session = None; return False

    def download_torrent_interactive(self):
        global LT_MODULE
        self.show_header("Download Torrent")
        if not LIBTORRENT_AVAILABLE or not LT_MODULE:
            print("❌ Torrent functionality is disabled: libtorrent not available."); return
        if not self.torrent_session and not self.setup_torrent_session_on_init():
             print("❌ Could not start torrent session."); return

        source_type = input("Enter 'm' for magnet link or 'f' for .torrent file path: ").strip().lower()
        save_path = Path(self.config.get('torrent_save_path'))
        save_path.mkdir(parents=True, exist_ok=True)
        handle = None; name_hint = "torrent_download"

        if source_type == 'm':
            uri = input("Enter magnet link: ").strip()
            if not uri.startswith("magnet:?"): print("❌ Invalid magnet link."); return
            try:
                params = LT_MODULE.parse_magnet_uri(uri)
                params.save_path = str(save_path)
                name_hint = params.name or uri[:50]+"..."
                handle = self.torrent_session.add_torrent(params)
                print(f"➕ Added torrent (magnet): {name_hint}")
            except Exception as e: print(f"❌ Error adding magnet: {e}"); return
        elif source_type == 'f':
            f_path_str = input("Enter path to .torrent file: ").strip()
            f_path = Path(f_path_str)
            if not f_path.is_file(): print(f"❌ File not found: {f_path}"); return
            try:
                ti = LT_MODULE.torrent_info(str(f_path))
                params = {'ti': ti, 'save_path': str(save_path)}
                name_hint = ti.name()
                handle = self.torrent_session.add_torrent(params)
                print(f"➕ Added torrent (file): {name_hint}")
            except Exception as e: print(f"❌ Error adding .torrent file: {e}"); return
        else: print("❌ Invalid source type."); return
        
        if not handle or not handle.is_valid(): print("❌ Failed to add torrent."); return
        self.active_torrent_handles[name_hint] = handle

        print(f"\n⏳ Monitoring '{name_hint}' (Ctrl+C to stop monitoring)...")
        try:
            while handle.is_valid() and not \
                  (handle.status().state == LT_MODULE.torrent_status.states.seeding or \
                   handle.status().state == LT_MODULE.torrent_status.states.finished):
                s = handle.status()
                states = ['queued', 'checking', 'dl metadata', 'dl', 'finished', 'seeding', 'allocating', 'chk fastresume']
                bar = self.create_usage_bar(s.progress * 100, 30)
                print(f"\r{name_hint[:25]:<25} {bar} {s.progress*100:.2f}% "
                      f"DL:{s.download_rate/1024:.1f}KiB/s UL:{s.upload_rate/1024:.1f}KiB/s "
                      f"S:{s.num_seeds}({s.list_seeds}) P:{s.num_peers}({s.list_peers}) St:{states[s.state]}", end=" ")
                sys.stdout.flush()
                
                # Basic alert processing for completion/error
                alerts = self.torrent_session.pop_alerts()
                for alert in alerts:
                    if alert.handle != handle: continue # Ensure alert is for current torrent
                    if isinstance(alert, LT_MODULE.torrent_finished_alert): print(f"\n✅ Torrent '{name_hint}' finished."); break
                    if isinstance(alert, LT_MODULE.torrent_error_alert): print(f"\n❌ Torrent error '{name_hint}': {alert.error.message()}"); break
                else: # No break from inner loop means no finish/error alert yet
                    time.sleep(1)
                    continue # Continue outer while loop
                break # Break outer while loop if finish/error alert processed
        except KeyboardInterrupt: print(f"\nℹ️  Stopped monitoring '{name_hint}'. Continues in background.")
        except Exception as e: print(f"\n❌ Torrent monitoring error: {e}")

        if handle.is_valid():
            s = handle.status()
            if s.state == LT_MODULE.torrent_status.states.seeding: print(f"\n✅ '{name_hint}' completed, now seeding.")
            elif s.state == LT_MODULE.torrent_status.states.finished: print(f"\n✅ '{name_hint}' finished (not seeding).")
            else: print(f"\nℹ️  '{name_hint}' monitoring ended. State: {s.state}")

    def create_usage_bar(self, percentage: float, width: int = 20) -> str:
        if not (0 <= percentage <= 100): percentage = 0
        filled = int(round(percentage / 100 * width))
        return f"[{'█' * filled}{'░' * (width - filled)}]"

    # --- Placeholder Methods for User to Implement ---
    def navigate_directory_placeholder(self):
        self.show_header("Navigate Directories (TODO)")
        print("This feature (Navigate Directories & Set Download Location) needs to be implemented.")
        print("Please integrate your previous directory navigation logic here.")

    def show_storage_overview_placeholder(self):
        self.show_header("Storage Overview (TODO)")
        if PSUTIL_AVAILABLE:
            print("psutil is available. Implement storage overview logic here.")
        else:
            print("psutil is NOT available. This feature would be limited.")
            print("Please install 'psutil' for detailed storage information.")
        print("Integrate your previous storage overview logic here.")

    def manage_favorites_placeholder(self):
        self.show_header("Manage Favorite Locations (TODO)")
        print("This feature needs to be implemented.")
        print("Please integrate your previous favorites management logic here.")

    def show_configuration_menu_placeholder(self):
        self.show_header("Configuration Settings (TODO)")
        print("This feature needs to be implemented.")
        print("Please integrate your previous configuration menu logic here,")
        print("allowing users to change settings like default paths, quality, etc.")


if __name__ == '__main__':
    if os.name == 'nt': # For better Unicode support on Windows cmd
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32; kernel32.SetConsoleOutputCP(65001)
        except: pass # Ignore if it fails

    app = YtDorn()
    try:
        app.main_loop()
    except KeyboardInterrupt:
        print("\nℹ️ User interrupted. Exiting YtDorn...")
    finally:
        if app.torrent_session and LIBTORRENT_AVAILABLE and LT_MODULE:
            print("Pausing torrent session on exit...")
            app.torrent_session.pause()
            # Consider saving resume data here for all active torrents
            # for name, handle in app.active_torrent_handles.items():
            # if handle.is_valid() and handle.has_metadata():
            # handle.save_resume_data(LT_MODULE. υψηλή_ακρίβεια_resume_data)
            print("Torrent session paused. Some operations might continue briefly to save state.")
            time.sleep(1) # Brief pause for libtorrent to process
        print("YtDorn shutdown complete.")
