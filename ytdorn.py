#!/usr/bin/env python3
"""
Enhanced YtDorn - Fast Multi-threaded YouTube Downloader
Version: 1.0.0
Minimal interface, maximum performance
"""

import sys
import os
import json
import subprocess
import argparse
import asyncio
import concurrent.futures
import threading
import signal
import time
from pathlib import Path
from typing import Dict, List, Optional, Union
from urllib.parse import urlparse, parse_qs
from dataclasses import dataclass

# Auto-install dependencies with fallback
def auto_install_dependencies():
    """Auto-install required dependencies with multiple methods."""
    required_packages = ['rich', 'yt-dlp']
    missing_packages = []
    
    # Check which packages are missing
    for package in required_packages:
        try:
            if package == 'rich':
                import rich
            elif package == 'yt-dlp':
                import yt_dlp
        except ImportError:
            missing_packages.append(package)
    
    if not missing_packages:
        return True
    
    print(f"Installing missing packages: {', '.join(missing_packages)}")
    
    # Try multiple installation methods
    install_methods = [
        # System package manager (Arch Linux)
        lambda pkg: subprocess.run(['sudo', 'pacman', '-S', '--noconfirm', f'python-{pkg}'], 
                                  capture_output=True),
        # pip with break-system-packages
        lambda pkg: subprocess.run([sys.executable, '-m', 'pip', 'install', 
                                  '--break-system-packages', pkg], capture_output=True),
        # regular pip
        lambda pkg: subprocess.run([sys.executable, '-m', 'pip', 'install', pkg], 
                                  capture_output=True),
    ]
    
    for package in missing_packages:
        installed = False
        for method in install_methods:
            try:
                result = method(package)
                if result.returncode == 0:
                    print(f"✓ Installed {package}")
                    installed = True
                    break
            except Exception:
                continue
        
        if not installed:
            print(f"✗ Failed to install {package}. Please install manually.")
            return False
    
    return True

# Auto-install before importing
if not auto_install_dependencies():
    sys.exit(1)

# Now import the dependencies
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.progress import Progress, TaskID
    import yt_dlp
except ImportError as e:
    print(f"Import error after installation: {e}")
    sys.exit(1)

console = Console()

@dataclass
class DownloadTask:
    """Represents a single download task."""
    url: str
    title: str
    output_path: str
    options: Dict
    status: str = "pending"
    progress: float = 0.0
    error: Optional[str] = None

class DirectoryNavigator:
    """Enhanced directory navigation and selection."""
    
    def __init__(self):
        self.home_dir = Path.home()
        self.current_dir = self.home_dir
        self.bookmarks = self._load_bookmarks()
    
    def _load_bookmarks(self) -> Dict[str, str]:
        """Load directory bookmarks."""
        bookmark_file = self.home_dir / ".ytdorn_bookmarks.json"
        if bookmark_file.exists():
            try:
                with open(bookmark_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        # Default bookmarks
        return {
            "Downloads": str(self.home_dir / "Downloads"),
            "Desktop": str(self.home_dir / "Desktop"),
            "Documents": str(self.home_dir / "Documents"),
            "Videos": str(self.home_dir / "Videos"),
            "Music": str(self.home_dir / "Music"),
        }
    
    def _save_bookmarks(self):
        """Save directory bookmarks."""
        bookmark_file = self.home_dir / ".ytdorn_bookmarks.json"
        try:
            with open(bookmark_file, 'w') as f:
                json.dump(self.bookmarks, f, indent=2)
        except IOError:
            pass
    
    def select_directory(self) -> str:
        """Interactive directory selection with navigation."""
        console.print("\n📁 Directory Selection")
        
        while True:
            # Show current directory and options
            table = Table(show_header=False, box=None)
            table.add_column("Option", style="cyan")
            table.add_column("Path", style="white")
            
            # Current directory info
            table.add_row("[.]", f"Current: {self.current_dir}")
            table.add_row("", "")
            
            # Bookmarks
            for i, (name, path) in enumerate(self.bookmarks.items(), 1):
                if Path(path).exists():
                    table.add_row(f"[{i}]", f"{name}: {path}")
            
            # Navigation options
            table.add_row("", "")
            table.add_row("[b]", "Browse/Navigate directories")
            table.add_row("[c]", f"Create new folder in {self.current_dir}")
            table.add_row("[a]", "Add current directory to bookmarks")
            table.add_row("[p]", "Enter custom path")
            table.add_row("[u]", "Use current directory")
            
            console.print(table)
            
            choice = Prompt.ask("Select option").strip()
            
            if choice == 'u':
                selected_dir = str(self.current_dir)
                break
            elif choice == 'p':
                custom_path = Prompt.ask("Enter path")
                if Path(custom_path).exists() or Confirm.ask(f"Create {custom_path}?"):
                    Path(custom_path).mkdir(parents=True, exist_ok=True)
                    selected_dir = custom_path
                    break
            elif choice == 'b':
                self._browse_directories()
            elif choice == 'c':
                folder_name = Prompt.ask("New folder name")
                new_path = self.current_dir / folder_name
                new_path.mkdir(exist_ok=True)
                console.print(f"✓ Created {new_path}")
                self.current_dir = new_path
            elif choice == 'a':
                name = Prompt.ask("Bookmark name")
                self.bookmarks[name] = str(self.current_dir)
                self._save_bookmarks()
                console.print(f"✓ Added bookmark: {name}")
            elif choice.isdigit():
                idx = int(choice) - 1
                bookmark_items = list(self.bookmarks.items())
                if 0 <= idx < len(bookmark_items):
                    selected_dir = bookmark_items[idx][1]
                    break
        
        # Ensure directory exists
        Path(selected_dir).mkdir(parents=True, exist_ok=True)
        return selected_dir
    
    def _browse_directories(self):
        """Browse directory structure interactively."""
        try:
            # List directories in current path
            dirs = [d for d in self.current_dir.iterdir() if d.is_dir()]
            dirs.sort()
            
            if not dirs:
                console.print("No subdirectories found.")
                return
            
            table = Table(show_header=False, box=None)
            table.add_column("Option", style="cyan")
            table.add_column("Directory", style="white")
            
            table.add_row("[..]", "Parent directory")
            for i, directory in enumerate(dirs, 1):
                table.add_row(f"[{i}]", directory.name)
            
            console.print(table)
            
            choice = Prompt.ask("Select directory or '..' for parent").strip()
            
            if choice == '..':
                if self.current_dir.parent != self.current_dir:
                    self.current_dir = self.current_dir.parent
            elif choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(dirs):
                    self.current_dir = dirs[idx]
            
        except Exception as e:
            console.print(f"Error browsing directories: {e}")

class MultiThreadDownloader:
    """High-performance multi-threaded downloader."""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.download_queue: List[DownloadTask] = []
        self.completed_tasks: List[DownloadTask] = []
        self.failed_tasks: List[DownloadTask] = []
        self.interrupted = False
        self.active_downloads = 0
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle interruption signals."""
        self.interrupted = True
        console.print("\n⚠️ Download interrupted. Finishing current downloads...")
    
    def add_task(self, task: DownloadTask):
        """Add a download task to the queue."""
        self.download_queue.append(task)
    
    def _download_single(self, task: DownloadTask, progress_callback=None) -> bool:
        """Download a single video with progress tracking."""
        try:
            def progress_hook(d):
                if self.interrupted:
                    raise KeyboardInterrupt("Download interrupted")
                
                if d['status'] == 'downloading':
                    if 'total_bytes' in d and d['total_bytes']:
                        task.progress = (d['downloaded_bytes'] / d['total_bytes']) * 100
                    elif 'total_bytes_estimate' in d and d['total_bytes_estimate']:
                        task.progress = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
                    
                    if progress_callback:
                        progress_callback(task)
                
                elif d['status'] == 'finished':
                    task.progress = 100.0
                    task.status = "completed"
            
            # Build yt-dlp options
            ydl_opts = {
                'outtmpl': os.path.join(task.output_path, '%(title)s.%(ext)s'),
                'format': self._get_format_string(task.options.get('format', 'best')),
                'progress_hooks': [progress_hook],
                'quiet': True,
                'no_warnings': True,
            }
            
            # Apply additional options
            self._apply_download_options(ydl_opts, task.options)
            
            # Perform download
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                task.status = "downloading"
                ydl.download([task.url])
            
            task.status = "completed"
            return True
            
        except KeyboardInterrupt:
            task.status = "cancelled"
            task.error = "Cancelled by user"
            return False
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            return False
    
    def _apply_download_options(self, ydl_opts: Dict, options: Dict):
        """Apply download options to yt-dlp configuration."""
        # Audio extraction
        if options.get('extract_audio'):
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': options.get('audio_format', 'mp3'),
                'preferredquality': '192',
            }]
        
        # Subtitles
        if options.get('subtitles'):
            ydl_opts['writesubtitles'] = True
            ydl_opts['writeautomaticsub'] = True
        
        # Thumbnails
        if options.get('thumbnails'):
            ydl_opts['writethumbnail'] = True
        
        # Metadata
        if options.get('metadata'):
            ydl_opts['writeinfojson'] = True
            ydl_opts['writedescription'] = True
    
    def _get_format_string(self, quality: str) -> str:
        """Convert quality selection to yt-dlp format string."""
        quality_map = {
            'best': 'best[ext=mp4]/best',
            '1080p': 'best[height<=1080][ext=mp4]/best[height<=1080]',
            '720p': 'best[height<=720][ext=mp4]/best[height<=720]',
            '480p': 'best[height<=480][ext=mp4]/best[height<=480]',
            '360p': 'best[height<=360][ext=mp4]/best[height<=360]',
        }
        return quality_map.get(quality, quality)
    
    def download_all(self):
        """Download all queued tasks with multi-threading."""
        if not self.download_queue:
            console.print("No downloads queued.")
            return
        
        console.print(f"Starting {len(self.download_queue)} downloads with {self.max_workers} threads...")
        
        with Progress(console=console) as progress:
            # Create progress tasks
            progress_tasks = {}
            for task in self.download_queue:
                progress_id = progress.add_task(f"[cyan]{task.title[:50]}...", total=100)
                progress_tasks[task] = progress_id
            
            def update_progress(task: DownloadTask):
                if task in progress_tasks:
                    progress.update(progress_tasks[task], completed=task.progress)
            
            # Execute downloads with thread pool
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_task = {
                    executor.submit(self._download_single, task, update_progress): task 
                    for task in self.download_queue
                }
                
                for future in concurrent.futures.as_completed(future_to_task):
                    task = future_to_task[future]
                    success = future.result()
                    
                    if success:
                        self.completed_tasks.append(task)
                        progress.update(progress_tasks[task], completed=100)
                    else:
                        self.failed_tasks.append(task)
                        progress.update(progress_tasks[task], completed=100, 
                                      description=f"[red]Failed: {task.title[:40]}...")
                    
                    if self.interrupted:
                        break
        
        # Print summary
        console.print(f"\n✅ Completed: {len(self.completed_tasks)}")
        console.print(f"❌ Failed: {len(self.failed_tasks)}")
        
        if self.failed_tasks:
            console.print("\nFailed downloads:")
            for task in self.failed_tasks:
                console.print(f"  • {task.title}: {task.error}")

class EnhancedYtDorn:
    """Main application class with enhanced features."""
    
    def __init__(self):
        self.navigator = DirectoryNavigator()
        self.downloader = MultiThreadDownloader()
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load application configuration."""
        config_path = Path.home() / ".ytdorn_config.json"
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        return {
            "default_quality": "1080p",
            "default_threads": 4,
            "recent_downloads": []
        }
    
    def _save_config(self):
        """Save application configuration."""
        config_path = Path.home() / ".ytdorn_config.json"
        try:
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except IOError:
            pass
    
    def get_video_info(self, url: str) -> Optional[Dict]:
        """Get detailed video/playlist/channel information."""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,  # Get full info
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info
        except Exception as e:
            console.print(f"Error getting info: {e}")
            return None
    
    def extract_channel_videos(self, channel_url: str) -> List[Dict]:
        """Extract all videos from a YouTube channel."""
        try:
            # Handle different channel URL formats
            if '/channel/' not in channel_url and '/c/' not in channel_url and '/@' not in channel_url:
                if 'youtube.com/user/' not in channel_url:
                    channel_url = f"https://www.youtube.com/c/{channel_url}"
            
            ydl_opts = {
                'quiet': True,
                'extract_flat': True,  # Only get video URLs, not full info
                'playlistend': None,   # Get all videos
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(channel_url, download=False)
                
                if info and 'entries' in info:
                    return list(info['entries'])
                else:
                    return []
                    
        except Exception as e:
            console.print(f"Error extracting channel videos: {e}")
            return []
    
    def process_url(self, url: str, options: Dict) -> List[DownloadTask]:
        """Process URL and create download tasks."""
        tasks = []
        
        console.print("🔍 Analyzing URL...")
        info = self.get_video_info(url)
        
        if not info:
            console.print("❌ Could not extract information from URL")
            return tasks
        
        output_dir = options['output_dir']
        
        if info.get('_type') == 'playlist':
            # Playlist processing
            console.print(f"📁 Found playlist: {info.get('title', 'Unknown')}")
            console.print(f"🎬 {len(info.get('entries', []))} videos")
            
            if not Confirm.ask("Download entire playlist?"):
                return tasks
            
            for entry in info.get('entries', []):
                if entry:
                    task = DownloadTask(
                        url=entry.get('url', entry.get('webpage_url', '')),
                        title=entry.get('title', 'Unknown'),
                        output_path=output_dir,
                        options=options.copy()
                    )
                    tasks.append(task)
        
        elif 'channel' in url.lower() or '/c/' in url or '/@' in url:
            # Channel processing
            console.print("📺 Extracting channel videos...")
            videos = self.extract_channel_videos(url)
            
            if videos:
                console.print(f"🎬 Found {len(videos)} videos in channel")
                
                if Confirm.ask("Download all channel videos?"):
                    for video in videos:
                        if video:
                            task = DownloadTask(
                                url=f"https://www.youtube.com/watch?v={video.get('id', '')}",
                                title=video.get('title', 'Unknown'),
                                output_path=output_dir,
                                options=options.copy()
                            )
                            tasks.append(task)
        
        else:
            # Single video
            task = DownloadTask(
                url=url,
                title=info.get('title', 'Unknown'),
                output_path=output_dir,
                options=options.copy()
            )
            tasks.append(task)
        
        return tasks
    
    def get_download_options(self) -> Dict:
        """Get download options from user with minimal interface."""
        options = {}
        
        # Quick options
        console.print("\n⚙️ Download Options")
        
        # Quality
        quality_choices = ["best", "1080p", "720p", "480p", "360p"]
        options['format'] = Prompt.ask("Quality", 
                                     choices=quality_choices, 
                                     default=self.config.get('default_quality', 'best'))
        
        # Audio extraction
        options['extract_audio'] = Confirm.ask("Audio only?", default=False)
        if options['extract_audio']:
            options['audio_format'] = Prompt.ask("Audio format", 
                                               choices=["mp3", "m4a", "opus"], 
                                               default="mp3")
        
        # Directory selection
        options['output_dir'] = self.navigator.select_directory()
        
        # Additional options (quick)
        console.print("\nAdditional options (y/n):")
        options['subtitles'] = Confirm.ask("Subtitles?", default=False)
        options['thumbnails'] = Confirm.ask("Thumbnails?", default=False)
        options['metadata'] = Confirm.ask("Metadata?", default=False)
        
        return options
    
    def run_interactive(self):
        """Run interactive mode with minimal interface."""
        console.print("🚀 Enhanced YtDorn - Fast YouTube Downloader")
        console.print("=" * 50)
        
        while True:
            try:
                # Simple menu
                console.print("\nOptions: [d]ownload [i]nfo [q]uit")
                choice = Prompt.ask("Select", choices=["d", "i", "q"], default="d")
                
                if choice == 'q':
                    break
                
                # Get URL
                url = Prompt.ask("\n🔗 YouTube URL")
                
                if choice == 'i':
                    # Info mode
                    info = self.get_video_info(url)
                    if info:
                        console.print(f"\n📺 Title: {info.get('title', 'Unknown')}")
                        console.print(f"👤 Channel: {info.get('uploader', 'Unknown')}")
                        if info.get('duration'):
                            console.print(f"⏱️ Duration: {info['duration']}s")
                        if info.get('view_count'):
                            console.print(f"👀 Views: {info['view_count']:,}")
                
                elif choice == 'd':
                    # Download mode
                    options = self.get_download_options()
                    
                    # Process URL and create tasks
                    tasks = self.process_url(url, options)
                    
                    if tasks:
                        # Add tasks to downloader
                        for task in tasks:
                            self.downloader.add_task(task)
                        
                        # Confirm and start download
                        console.print(f"\n📦 {len(tasks)} items queued for download")
                        if Confirm.ask("Start download?", default=True):
                            self.downloader.download_all()
                        
                        # Clear completed tasks
                        self.downloader.download_queue.clear()
                        self.downloader.completed_tasks.clear()
                        self.downloader.failed_tasks.clear()
                
            except KeyboardInterrupt:
                console.print("\n👋 Goodbye!")
                break
            except Exception as e:
                console.print(f"❌ Error: {e}")

def create_cli_parser():
    """Create CLI argument parser."""
    parser = argparse.ArgumentParser(description="Enhanced YtDorn - Fast YouTube Downloader")
    
    parser.add_argument('url', nargs='?', help='YouTube URL')
    parser.add_argument('-f', '--format', default='best', help='Video quality')
    parser.add_argument('-o', '--output', help='Output directory')
    parser.add_argument('-t', '--threads', type=int, default=4, help='Number of download threads')
    parser.add_argument('--audio', action='store_true', help='Extract audio only')
    parser.add_argument('--audio-format', default='mp3', help='Audio format')
    parser.add_argument('--subs', action='store_true', help='Download subtitles')
    parser.add_argument('--thumbs', action='store_true', help='Download thumbnails')
    parser.add_argument('--meta', action='store_true', help='Save metadata')
    parser.add_argument('--info', action='store_true', help='Show info only')
    
    return parser

def main():
    """Main entry point."""
    parser = create_cli_parser()
    args = parser.parse_args()
    
    app = EnhancedYtDorn()
    
    if args.url:
        # CLI mode
        options = {
            'format': args.format,
            'extract_audio': args.audio,
            'audio_format': args.audio_format,
            'subtitles': args.subs,
            'thumbnails': args.thumbs,
            'metadata': args.meta,
            'output_dir': args.output or os.path.join(os.path.expanduser("~"), "Downloads", "YtDorn")
        }
        
        os.makedirs(options['output_dir'], exist_ok=True)
        
        if args.info:
            info = app.get_video_info(args.url)
            if info:
                console.print(f"Title: {info.get('title', 'Unknown')}")
                console.print(f"Channel: {info.get('uploader', 'Unknown')}")
                if info.get('duration'):
                    console.print(f"Duration: {info['duration']}s")
        else:
            # Set thread count
            app.downloader.max_workers = args.threads
            
            # Process and download
            tasks = app.process_url(args.url, options)
            if tasks:
                for task in tasks:
                    app.downloader.add_task(task)
                app.downloader.download_all()
    else:
        # Interactive mode
        app.run_interactive()

if __name__ == "__main__":
    main()
