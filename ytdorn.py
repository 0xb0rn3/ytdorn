#!/usr/bin/env python3
"""
YtDorn - Super Powerful YouTube Downloader
Version: 0.1.2
Author: 0xb0rn3
GitHub: https://github.com/0xb0rn3/ytdorn

A modern, fast, and user-friendly YouTube downloader with rich terminal interface.
"""

import sys
import os
import json
import subprocess
import argparse
import asyncio
import concurrent.futures
import time
from pathlib import Path
from typing import Dict, List, Optional, Union
from urllib.parse import urlparse, parse_qs
import threading
import signal

# Rich terminal interface imports
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.prompt import Prompt, Confirm
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
    from rich.style import Style
    from rich.align import Align
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Installing rich for better terminal experience...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "rich"])
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.prompt import Prompt, Confirm
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
    from rich.style import Style
    from rich.align import Align

# YouTube-DL imports
try:
    import yt_dlp
except ImportError:
    print("Installing yt-dlp...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])
    import yt_dlp

# Initialize rich console
console = Console()

class YtDornConfig:
    """Configuration manager for YtDorn settings and presets."""
    
    def __init__(self):
        self.config_path = Path.home() / ".ytdorn_config.json"
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """Load configuration from file or create default."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        # Default configuration
        return {
            "recent_dirs": [],
            "default_quality": "best",
            "default_format": "mp4",
            "presets": {
                "high_quality_mp4": {
                    "format": "1080p",
                    "extract_audio": False,
                    "subtitles": True,
                    "thumbnails": True,
                    "description": "High quality MP4 with subtitles"
                },
                "audio_only": {
                    "format": "best",
                    "extract_audio": True,
                    "audio_format": "mp3",
                    "subtitles": False,
                    "thumbnails": True,
                    "description": "Audio extraction to MP3"
                }
            }
        }
    
    def save_config(self):
        """Save current configuration to file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except IOError as e:
            console.print(f"[yellow]Warning: Could not save config: {e}[/yellow]")
    
    def add_recent_dir(self, directory: str):
        """Add directory to recent directories list."""
        if directory in self.config["recent_dirs"]:
            self.config["recent_dirs"].remove(directory)
        self.config["recent_dirs"].insert(0, directory)
        self.config["recent_dirs"] = self.config["recent_dirs"][:5]  # Keep only 5 recent
        self.save_config()

class YtDornDownloader:
    """Core downloader class with advanced features."""
    
    def __init__(self, config: YtDornConfig):
        self.config = config
        self.interrupted = False
        self.current_task = None
        
        # Setup signal handlers for graceful interruption
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle interruption signals gracefully."""
        self.interrupted = True
        if self.current_task:
            console.print("\n[yellow]⚠️  Download interrupted by user[/yellow]")
            console.print("[dim]Cleaning up...[/dim]")
    
    def check_dependencies(self) -> Dict[str, bool]:
        """Check if required dependencies are available."""
        deps = {"yt-dlp": False, "ffmpeg": False}
        
        # Check yt-dlp
        try:
            import yt_dlp
            deps["yt-dlp"] = True
        except ImportError:
            pass
        
        # Check FFmpeg
        try:
            subprocess.run(["ffmpeg", "-version"], 
                         capture_output=True, check=True)
            deps["ffmpeg"] = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        return deps
    
    def get_video_info(self, url: str) -> Optional[Dict]:
        """Get detailed information about a video/playlist."""
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                return info
        except Exception as e:
            console.print(f"[red]Error getting video info: {e}[/red]")
            return None
    
    def format_video_info(self, info: Dict) -> Panel:
        """Format video information for display."""
        if info.get('_type') == 'playlist':
            title = f"📁 {info.get('title', 'Unknown Playlist')}"
            details = f"🎬 {info.get('playlist_count', 0)} videos\n"
            details += f"👤 {info.get('uploader', 'Unknown')}\n"
            if info.get('description'):
                details += f"📝 {info['description'][:100]}..."
        else:
            title = f"🎥 {info.get('title', 'Unknown Video')}"
            details = f"⏱️  {self._format_duration(info.get('duration', 0))}\n"
            details += f"👤 {info.get('uploader', 'Unknown')}\n"
            details += f"👀 {info.get('view_count', 0):,} views\n"
            if info.get('description'):
                details += f"📝 {info['description'][:100]}..."
        
        return Panel(details, title=title, expand=False)
    
    def _format_duration(self, seconds: int) -> str:
        """Format duration in seconds to human readable format."""
        if not seconds:
            return "Unknown"
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def download_content(self, url: str, options: Dict) -> bool:
        """Download content with specified options."""
        try:
            # Build yt-dlp options
            ydl_opts = self._build_ydl_options(options)
            
            # Create progress hook
            def progress_hook(d):
                if self.interrupted:
                    raise KeyboardInterrupt("Download interrupted by user")
                
                if d['status'] == 'downloading':
                    # Update progress display
                    pass
                elif d['status'] == 'finished':
                    console.print(f"[green]✅ Downloaded: {d['filename']}[/green]")
            
            ydl_opts['progress_hooks'] = [progress_hook]
            
            # Perform download
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self.current_task = ydl
                ydl.download([url])
                
            return True
            
        except KeyboardInterrupt:
            console.print("[yellow]Download cancelled by user[/yellow]")
            return False
        except Exception as e:
            console.print(f"[red]Download failed: {e}[/red]")
            return False
        finally:
            self.current_task = None
    
    def _build_ydl_options(self, options: Dict) -> Dict:
        """Build yt-dlp options dictionary from user options."""
        ydl_opts = {
            'outtmpl': os.path.join(options['output_dir'], '%(title)s.%(ext)s'),
            'format': self._get_format_string(options.get('format', 'best')),
        }
        
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
            if options.get('embed_subtitles'):
                ydl_opts['embedsubs'] = True
        
        # Thumbnails
        if options.get('thumbnails'):
            ydl_opts['writethumbnail'] = True
            if options.get('embed_thumbnails'):
                ydl_opts['embedthumbnail'] = True
        
        # Metadata
        if options.get('metadata'):
            ydl_opts['writeinfojson'] = True
            ydl_opts['writedescription'] = True
        
        return ydl_opts
    
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

class YtDornInterface:
    """Rich terminal interface for YtDorn."""
    
    def __init__(self):
        self.config = YtDornConfig()
        self.downloader = YtDornDownloader(self.config)
    
    def show_banner(self):
        """Display the YtDorn banner."""
        banner = """
╭─────────────────────────────────────────────╮
│  ██╗  ██╗████████╗██████╗  ██████╗ ██████╗ │
│  ╚██╗ ██╔╝╚══██╔══╝██╔══██╗██╔═══██╗██╔══██╗│
│   ╚████╔╝   ██║   ██║  ██║██║   ██║██████╔╝│
│    ╚██╔╝    ██║   ██║  ██║██║   ██║██╔══██╗│
│     ██║     ██║   ██████╔╝╚██████╔╝██║  ██║│
│     ╚═╝     ╚═╝   ╚═════╝  ╚═════╝ ╚═╝  ╚═╝│
╰─────────────────────────────────────────────╯
"""
        console.print(Panel(banner, style="bold blue"))
        console.print(Align.center("[bold]YtDorn v0.1.2 by 0xb0rn3[/bold]"))
        console.print(Align.center("Super Powerful YouTube Downloader"))
        console.print(Align.center("https://github.com/0xb0rn3/ytdorn"))
        console.print("═" * 50)
    
    def check_system_status(self):
        """Check and display system status."""
        deps = self.downloader.check_dependencies()
        
        if deps["yt-dlp"] and deps["ffmpeg"]:
            console.print("[green]✓ yt-dlp and FFmpeg found.[/green]")
            console.print("[green]🚀 System ready![/green]")
        elif deps["yt-dlp"]:
            console.print("[green]✓ yt-dlp found.[/green]")
            console.print("[yellow]⚠️  FFmpeg not found. Audio conversion may be limited.[/yellow]")
        else:
            console.print("[red]❌ yt-dlp not found. Installing...[/red]")
            return False
        
        console.print("═" * 60)
        return True
    
    def show_main_menu(self) -> str:
        """Display main menu and get user choice."""
        menu_table = Table(show_header=False, box=None, padding=(0, 1))
        menu_table.add_column("Option", style="bold cyan")
        menu_table.add_column("Description", style="white")
        
        menu_table.add_row("[s]", "🎥 Single Video/Playlist Item")
        menu_table.add_row("", "[dim]Download specific video or item(s) from a playlist[/dim]")
        menu_table.add_row("[p]", "🎬 Full Playlist/Channel")
        menu_table.add_row("", "[dim]Download entire playlist or select a playlist from a channel[/dim]")
        menu_table.add_row("[i]", "📊 Content Info")
        menu_table.add_row("", "[dim]Get detailed info for a URL (video, playlist, channel)[/dim]")
        menu_table.add_row("[q]", "🚪 Quit")
        menu_table.add_row("", "[dim]Exit YtDorn[/dim]")
        
        menu_panel = Panel(menu_table, title="─ Main Menu ─", expand=False)
        console.print(menu_panel)
        
        return Prompt.ask("❯ Select option", choices=["s", "p", "i", "q"], default="s")
    
    def get_url_input(self) -> str:
        """Get URL input from user."""
        while True:
            url = Prompt.ask("\n🔗 Enter YouTube URL")
            if self._is_valid_youtube_url(url):
                return url
            console.print("[red]❌ Invalid YouTube URL. Please try again.[/red]")
    
    def _is_valid_youtube_url(self, url: str) -> bool:
        """Validate YouTube URL."""
        parsed = urlparse(url)
        youtube_domains = ['youtube.com', 'www.youtube.com', 'youtu.be', 'm.youtube.com']
        return parsed.netloc in youtube_domains
    
    def get_download_options(self) -> Dict:
        """Get download options from user."""
        options = {}
        
        # Quality selection
        console.print("\n📺 Quality Selection:")
        quality_choices = ["best", "1080p", "720p", "480p", "360p"]
        options['format'] = Prompt.ask("Select quality", choices=quality_choices, default="best")
        
        # Audio extraction
        options['extract_audio'] = Confirm.ask("🎵 Extract audio only?", default=False)
        if options['extract_audio']:
            audio_formats = ["mp3", "m4a", "opus"]
            options['audio_format'] = Prompt.ask("Audio format", choices=audio_formats, default="mp3")
        
        # Output directory
        options['output_dir'] = self._get_output_directory()
        
        # Additional options
        console.print("\n⚙️  Additional Options:")
        options['subtitles'] = Confirm.ask("📝 Download subtitles?", default=False)
        options['thumbnails'] = Confirm.ask("🖼️  Download thumbnails?", default=False)
        options['metadata'] = Confirm.ask("📊 Save metadata?", default=False)
        
        return options
    
    def _get_output_directory(self) -> str:
        """Get output directory from user."""
        console.print("\n📁 Output Directory:")
        
        # Show recent directories
        recent_dirs = self.config.config.get("recent_dirs", [])
        if recent_dirs:
            console.print("Recent directories:")
            for i, directory in enumerate(recent_dirs[:3], 1):
                console.print(f"  [{i}] {directory}")
            
            choice = Prompt.ask("Select recent directory or enter new path", default="new")
            if choice.isdigit() and 1 <= int(choice) <= len(recent_dirs):
                return recent_dirs[int(choice) - 1]
        
        # Get new directory
        default_dir = os.path.join(os.path.expanduser("~"), "Downloads", "YtDorn")
        directory = Prompt.ask("Enter output directory", default=default_dir)
        
        # Create directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)
        self.config.add_recent_dir(directory)
        
        return directory
    
    def show_download_summary(self, url: str, info: Dict, options: Dict):
        """Show download summary before starting."""
        summary_table = Table(show_header=False, box=None)
        summary_table.add_column("Setting", style="bold")
        summary_table.add_column("Value", style="cyan")
        
        summary_table.add_row("URL:", url[:50] + "..." if len(url) > 50 else url)
        summary_table.add_row("Title:", info.get('title', 'Unknown')[:50])
        summary_table.add_row("Quality:", options['format'])
        summary_table.add_row("Audio Only:", "Yes" if options['extract_audio'] else "No")
        summary_table.add_row("Output:", options['output_dir'])
        summary_table.add_row("Subtitles:", "Yes" if options['subtitles'] else "No")
        summary_table.add_row("Thumbnails:", "Yes" if options['thumbnails'] else "No")
        
        console.print(Panel(summary_table, title="📋 Download Summary", expand=False))
        
        return Confirm.ask("\n🚀 Start download?", default=True)
    
    def run_interactive_mode(self):
        """Run the interactive mode."""
        self.show_banner()
        
        if not self.check_system_status():
            return
        
        while True:
            try:
                choice = self.show_main_menu()
                
                if choice == 'q':
                    console.print("\n👋 Thanks for using YtDorn!")
                    break
                
                elif choice == 'i':
                    # Info mode
                    url = self.get_url_input()
                    with console.status("🔍 Fetching video information..."):
                        info = self.downloader.get_video_info(url)
                    
                    if info:
                        console.print(self.downloader.format_video_info(info))
                    
                elif choice in ['s', 'p']:
                    # Download mode
                    url = self.get_url_input()
                    
                    # Get video info
                    with console.status("🔍 Analyzing content..."):
                        info = self.downloader.get_video_info(url)
                    
                    if not info:
                        console.print("[red]❌ Could not fetch video information[/red]")
                        continue
                    
                    # Show video info
                    console.print(self.downloader.format_video_info(info))
                    
                    # Get download options
                    options = self.get_download_options()
                    
                    # Show summary and confirm
                    if self.show_download_summary(url, info, options):
                        with Progress(
                            SpinnerColumn(),
                            TextColumn("[progress.description]{task.description}"),
                            BarColumn(),
                            TaskProgressColumn(),
                            TimeRemainingColumn(),
                            console=console
                        ) as progress:
                            task = progress.add_task("Downloading...", total=100)
                            success = self.downloader.download_content(url, options)
                            progress.update(task, completed=100)
                        
                        if success:
                            console.print("[green]✅ Download completed successfully![/green]")
                        else:
                            console.print("[red]❌ Download failed[/red]")
                
                console.print("\n" + "═" * 60)
                
            except KeyboardInterrupt:
                console.print("\n[yellow]Operation cancelled by user[/yellow]")
                break
            except Exception as e:
                console.print(f"[red]Unexpected error: {e}[/red]")

def create_cli_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="YtDorn - Super Powerful YouTube Downloader",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('-u', '--url', help='YouTube URL to download')
    parser.add_argument('-f', '--format', default='best', 
                       choices=['best', '1080p', '720p', '480p', '360p'],
                       help='Video quality/format')
    parser.add_argument('-o', '--output', help='Output directory')
    parser.add_argument('--extract-audio', action='store_true',
                       help='Extract audio only')
    parser.add_argument('--audio-format', default='mp3',
                       choices=['mp3', 'm4a', 'opus'],
                       help='Audio format for extraction')
    parser.add_argument('--subtitles', action='store_true',
                       help='Download subtitles')
    parser.add_argument('--thumbnails', action='store_true',
                       help='Download thumbnails')
    parser.add_argument('--metadata', action='store_true',
                       help='Save metadata')
    parser.add_argument('--batch', help='Batch download from file')
    parser.add_argument('--preset', help='Use saved preset')
    parser.add_argument('--info', action='store_true',
                       help='Show video information only')
    parser.add_argument('--list-presets', action='store_true',
                       help='List available presets')
    
    return parser

def main():
    """Main entry point."""
    parser = create_cli_parser()
    args = parser.parse_args()
    
    interface = YtDornInterface()
    
    # Handle CLI arguments
    if args.list_presets:
        console.print("📋 Available Presets:")
        for name, preset in interface.config.config.get('presets', {}).items():
            console.print(f"  • {name}: {preset.get('description', 'No description')}")
        return
    
    if args.url:
        # CLI mode
        options = {
            'format': args.format,
            'extract_audio': args.extract_audio,
            'audio_format': args.audio_format,
            'subtitles': args.subtitles,
            'thumbnails': args.thumbnails,
            'metadata': args.metadata,
            'output_dir': args.output or os.path.join(os.path.expanduser("~"), "Downloads", "YtDorn")
        }
        
        # Apply preset if specified
        if args.preset:
            preset = interface.config.config.get('presets', {}).get(args.preset)
            if preset:
                options.update(preset)
            else:
                console.print(f"[red]Preset '{args.preset}' not found[/red]")
                return
        
        os.makedirs(options['output_dir'], exist_ok=True)
        
        if args.info:
            # Info mode
            info = interface.downloader.get_video_info(args.url)
            if info:
                console.print(interface.downloader.format_video_info(info))
        else:
            # Download mode
            success = interface.downloader.download_content(args.url, options)
            if success:
                console.print("[green]✅ Download completed![/green]")
            else:
                console.print("[red]❌ Download failed[/red]")
    
    elif args.batch:
        # Batch mode
        try:
            with open(args.batch, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
            
            console.print(f"📥 Processing {len(urls)} URLs from batch file...")
            
            for i, url in enumerate(urls, 1):
                console.print(f"\n[{i}/{len(urls)}] Processing: {url}")
                # Process each URL with same logic as single URL
                
        except FileNotFoundError:
            console.print(f"[red]Batch file '{args.batch}' not found[/red]")
    
    else:
        # Interactive mode
        interface.run_interactive_mode()

if __name__ == "__main__":
    main()
