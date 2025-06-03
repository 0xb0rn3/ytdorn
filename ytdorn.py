#!/usr/bin/env python3
"""
ytdorn - YouTube Multi-Downloader Tool
Version: 0.1.2
A minimal, powerful CLI YouTube downloader with advanced features
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path
from typing import Optional, Dict, List

class YtDorn:
    def __init__(self):
        self.version = "0.1.2"
        self.current_dir = Path.cwd()
        self.download_dir = self.current_dir / "downloads"
        self.ensure_download_dir()
        
    def ensure_download_dir(self):
        """Create downloads directory if it doesn't exist"""
        self.download_dir.mkdir(exist_ok=True)
        
    def check_dependencies(self):
        """Check and install required dependencies"""
        print("🔧 Checking dependencies...")
        
        # Check if yt-dlp is installed
        try:
            subprocess.run(['yt-dlp', '--version'], 
                         capture_output=True, check=True)
            print("✅ yt-dlp is installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("📦 Installing yt-dlp...")
            self.install_package('yt-dlp')
            
        # Check if ffmpeg is available
        try:
            subprocess.run(['ffmpeg', '-version'], 
                         capture_output=True, check=True)
            print("✅ ffmpeg is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️  ffmpeg not found. Install it for better audio/video processing:")
            print("   Ubuntu/Debian: sudo apt install ffmpeg")
            print("   Fedora: sudo dnf install ffmpeg")
            print("   Arch: sudo pacman -S ffmpeg")
            
    def install_package(self, package_name: str):
        """Install Python package using pip with --break-system-packages if needed"""
        try:
            # First try normal pip install
            subprocess.run([sys.executable, '-m', 'pip', 'install', package_name], 
                         check=True, capture_output=True)
            print(f"✅ {package_name} installed successfully")
        except subprocess.CalledProcessError:
            try:
                # If that fails, try with --break-system-packages
                print(f"🔄 Retrying {package_name} with --break-system-packages...")
                subprocess.run([sys.executable, '-m', 'pip', 'install', 
                              '--break-system-packages', package_name], 
                             check=True, capture_output=True)
                print(f"✅ {package_name} installed with --break-system-packages")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to install {package_name}: {e}")
                sys.exit(1)
                
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
        
    def show_header(self):
        """Display application header"""
        print("=" * 60)
        print(f"🎬 ytdorn v{self.version} - YouTube Multi-Downloader")
        print("=" * 60)
        print(f"📁 Current directory: {self.current_dir}")
        print(f"📥 Download directory: {self.download_dir}")
        print("=" * 60)
        
    def navigate_directory(self):
        """Directory navigation interface"""
        while True:
            self.clear_screen()
            self.show_header()
            print("\n📂 Directory Navigation")
            print("-" * 30)
            
            # Show current directory contents
            try:
                items = list(self.current_dir.iterdir())
                dirs = [item for item in items if item.is_dir()]
                files = [item for item in items if item.is_file()]
                
                print(f"Current: {self.current_dir}")
                print(f"Parent: {self.current_dir.parent}")
                print()
                
                # Show directories first
                if dirs:
                    print("📁 Directories:")
                    for i, d in enumerate(dirs[:10], 1):  # Show max 10 items
                        print(f"  {i}. {d.name}/")
                        
                if files:
                    print("📄 Files:")
                    for i, f in enumerate(files[:5], len(dirs) + 1):  # Show max 5 files
                        print(f"  {i}. {f.name}")
                        
            except PermissionError:
                print("❌ Permission denied accessing this directory")
                
            print("\nOptions:")
            print("p) Go to parent directory")
            print("h) Go to home directory") 
            print("s) Set as download directory")
            print("b) Back to main menu")
            print("1-9) Enter numbered directory")
            
            choice = input("\nChoice: ").strip().lower()
            
            if choice == 'b':
                break
            elif choice == 'p':
                self.current_dir = self.current_dir.parent
            elif choice == 'h':
                self.current_dir = Path.home()
            elif choice == 's':
                self.download_dir = self.current_dir / "downloads"
                self.ensure_download_dir()
                print(f"✅ Download directory set to: {self.download_dir}")
                input("Press Enter to continue...")
            elif choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(dirs):
                    new_dir = dirs[idx]
                    if new_dir.is_dir():
                        self.current_dir = new_dir
                        
    def get_video_info(self, url: str) -> Optional[Dict]:
        """Get video information using yt-dlp"""
        try:
            result = subprocess.run([
                'yt-dlp', '--dump-json', '--no-download', url
            ], capture_output=True, text=True, check=True)
            
            # Handle multiple videos (playlists)
            lines = result.stdout.strip().split('\n')
            if len(lines) == 1:
                return json.loads(lines[0])
            else:
                # Return info about first video for preview
                return json.loads(lines[0])
                
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            return None
    
    def get_available_formats(self, url: str) -> Optional[List[Dict]]:
        """Get all available formats for a video"""
        try:
            result = subprocess.run([
                'yt-dlp', '--list-formats', '--dump-json', '--no-download', url
            ], capture_output=True, text=True, check=True)
            
            # Parse the JSON output to get format information
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if line.strip().startswith('{'):
                    data = json.loads(line)
                    if 'formats' in data:
                        return data['formats']
            return None
            
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            return None
    
    def format_filesize(self, size_bytes: Optional[int]) -> str:
        """Convert bytes to human readable format"""
        if not size_bytes:
            return "Unknown"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def display_quality_options(self, formats: List[Dict]) -> Dict[str, Dict]:
        """Display available quality options and return selection mapping"""
        print("\n📊 Available Quality Options")
        print("=" * 80)
        
        # Separate video and audio formats
        video_formats = []
        audio_formats = []
        combined_formats = []
        
        for fmt in formats:
            if fmt.get('vcodec') != 'none' and fmt.get('acodec') != 'none':
                # Combined video+audio format
                combined_formats.append(fmt)
            elif fmt.get('vcodec') != 'none' and fmt.get('acodec') == 'none':
                # Video-only format
                video_formats.append(fmt)
            elif fmt.get('acodec') != 'none' and fmt.get('vcodec') == 'none':
                # Audio-only format
                audio_formats.append(fmt)
        
        quality_options = {}
        option_num = 1
        
        # Display combined formats first (these are usually lower quality but convenient)
        if combined_formats:
            print("🎬 Combined Video+Audio Formats:")
            print("-" * 50)
            for fmt in sorted(combined_formats, key=lambda x: x.get('height', 0), reverse=True):
                resolution = f"{fmt.get('width', '?')}x{fmt.get('height', '?')}" if fmt.get('height') else "Audio"
                fps = f" @{fmt.get('fps')}fps" if fmt.get('fps') else ""
                ext = fmt.get('ext', 'unknown')
                filesize = self.format_filesize(fmt.get('filesize'))
                vcodec = fmt.get('vcodec', 'unknown')[:15]
                acodec = fmt.get('acodec', 'unknown')[:15]
                
                print(f"  {option_num:2d}. [{resolution}{fps}] {ext.upper()} - {filesize}")
                print(f"      Video: {vcodec} | Audio: {acodec}")
                
                quality_options[str(option_num)] = {
                    'format': fmt['format_id'],
                    'description': f"{resolution} {ext.upper()} (Combined)",
                    'type': 'combined'
                }
                option_num += 1
                
                if option_num > 8:  # Limit display to prevent overwhelming
                    break
            print()
        
        # Display best video+audio combinations
        if video_formats and audio_formats:
            print("🎥 High Quality Video+Audio Combinations:")
            print("-" * 50)
            
            # Get best video formats (top 5)
            best_videos = sorted(video_formats, 
                               key=lambda x: (x.get('height', 0), x.get('tbr', 0)), 
                               reverse=True)[:5]
            
            # Get best audio format
            best_audio = max(audio_formats, 
                           key=lambda x: x.get('abr', 0), 
                           default=audio_formats[0])
            
            for vid_fmt in best_videos:
                resolution = f"{vid_fmt.get('width', '?')}x{vid_fmt.get('height', '?')}"
                fps = f" @{vid_fmt.get('fps')}fps" if vid_fmt.get('fps') else ""
                vid_ext = vid_fmt.get('ext', 'unknown')
                vid_codec = vid_fmt.get('vcodec', 'unknown')[:15]
                aud_codec = best_audio.get('acodec', 'unknown')[:15]
                
                # Estimate combined filesize (rough approximation)
                vid_size = vid_fmt.get('filesize', 0) or 0
                aud_size = best_audio.get('filesize', 0) or 0
                total_size = self.format_filesize(vid_size + aud_size) if (vid_size and aud_size) else "Unknown"
                
                print(f"  {option_num:2d}. [{resolution}{fps}] {vid_ext.upper()} + Audio - {total_size}")
                print(f"      Video: {vid_codec} | Audio: {aud_codec}")
                
                quality_options[str(option_num)] = {
                    'format': f"{vid_fmt['format_id']}+{best_audio['format_id']}",
                    'description': f"{resolution} {vid_ext.upper()} + Best Audio",
                    'type': 'combined_manual'
                }
                option_num += 1
            print()
        
        # Audio-only options
        if audio_formats:
            print("🎵 Audio-Only Formats:")
            print("-" * 50)
            
            # Sort by audio bitrate
            best_audio_formats = sorted(audio_formats, 
                                      key=lambda x: x.get('abr', 0), 
                                      reverse=True)[:3]
            
            for aud_fmt in best_audio_formats:
                bitrate = f"{aud_fmt.get('abr', '?')}kbps"
                ext = aud_fmt.get('ext', 'unknown')
                codec = aud_fmt.get('acodec', 'unknown')[:15]
                filesize = self.format_filesize(aud_fmt.get('filesize'))
                
                print(f"  {option_num:2d}. Audio [{bitrate}] {ext.upper()} - {filesize}")
                print(f"      Codec: {codec}")
                
                quality_options[str(option_num)] = {
                    'format': aud_fmt['format_id'],
                    'description': f"Audio {bitrate} {ext.upper()}",
                    'type': 'audio'
                }
                option_num += 1
        
        # Add quick selection options
        print("⚡ Quick Selection:")
        print("-" * 50)
        print(f"  {option_num:2d}. 🏆 Best Quality (Automatic)")
        quality_options[str(option_num)] = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'description': 'Best available quality',
            'type': 'auto_best'
        }
        option_num += 1
        
        print(f"  {option_num:2d}. 🎵 Best Audio Only")
        quality_options[str(option_num)] = {
            'format': 'bestaudio/best',
            'description': 'Best audio quality',
            'type': 'auto_audio'
        }
        option_num += 1
        
        print(f"  {option_num:2d}. 📱 Mobile Friendly (720p)")
        quality_options[str(option_num)] = {
            'format': 'best[height<=720][ext=mp4]/best[ext=mp4]',
            'description': '720p mobile-friendly',
            'type': 'mobile'
        }
        
        return quality_options
    
    def select_quality(self, url: str) -> Optional[str]:
        """Interactive quality selection interface"""
        print("🔍 Analyzing available formats...")
        
        # Get available formats
        formats = self.get_available_formats(url)
        if not formats:
            print("❌ Could not retrieve format information")
            return None
        
        # Display options and get user selection
        quality_options = self.display_quality_options(formats)
        
        print("\n" + "=" * 80)
        while True:
            choice = input("Select quality option (number): ").strip()
            
            if choice in quality_options:
                selected = quality_options[choice]
                print(f"✅ Selected: {selected['description']}")
                return selected['format']
            else:
                print("❌ Invalid selection. Please choose a number from the list.")
                continue
            
    def download_single_video(self):
        """Download a single video with quality selection"""
        print("\n🎥 Single Video Download")
        print("-" * 30)
        
        url = input("Enter YouTube URL: ").strip()
        if not url:
            return
            
        print("🔍 Getting video information...")
        info = self.get_video_info(url)
        
        if not info:
            print("❌ Could not get video information")
            input("Press Enter to continue...")
            return
            
        print(f"📹 Title: {info.get('title', 'Unknown')}")
        print(f"⏱️  Duration: {info.get('duration_string', 'Unknown')}")
        print(f"👤 Uploader: {info.get('uploader', 'Unknown')}")
        
        # Quality selection
        print("\nQuality Selection Options:")
        print("1. Quick select (automatic best)")
        print("2. Choose specific quality")
        
        quality_choice = input("Choose option (1-2): ").strip()
        
        format_string = None
        
        if quality_choice == '1':
            # Quick selection
            format_type = input("Quick select - (v)ideo+audio or (a)udio only: ").lower()
            if format_type == 'a':
                format_string = 'bestaudio/best'
            else:
                format_string = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        elif quality_choice == '2':
            # Detailed quality selection
            format_string = self.select_quality(url)
            if not format_string:
                print("❌ Quality selection failed")
                input("Press Enter to continue...")
                return
        else:
            print("❌ Invalid choice, using automatic best quality")
            format_string = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        
        # Build yt-dlp command
        cmd = ['yt-dlp', '-f', format_string]
        cmd.extend([
            '-o', str(self.download_dir / '%(title)s.%(ext)s'),
            url
        ])
        
        print(f"\n🚀 Starting download with format: {format_string}")
        try:
            subprocess.run(cmd, check=True)
            print("✅ Download completed!")
        except subprocess.CalledProcessError:
            print("❌ Download failed")
            
        input("Press Enter to continue...")
        
    def download_playlist(self):
        """Download entire playlist with quality selection"""
        print("\n📋 Playlist Download")
        print("-" * 30)
        
        url = input("Enter playlist URL: ").strip()
        if not url:
            return
            
        print("🔍 Getting playlist information...")
        
        # Get playlist info
        try:
            result = subprocess.run([
                'yt-dlp', '--flat-playlist', '--dump-json', url
            ], capture_output=True, text=True, check=True)
            
            entries = result.stdout.strip().split('\n')
            print(f"📊 Found {len(entries)} videos in playlist")
            
        except subprocess.CalledProcessError:
            print("❌ Could not get playlist information")
            input("Press Enter to continue...")
            return
        
        # Quality selection for playlist
        print("\nQuality Selection for Playlist:")
        print("1. Quick select (same quality for all videos)")
        print("2. Choose specific quality (same for all videos)")
        
        quality_choice = input("Choose option (1-2): ").strip()
        
        format_string = None
        
        if quality_choice == '1':
            format_type = input("Quick select - (v)ideo+audio or (a)udio only: ").lower()
            if format_type == 'a':
                format_string = 'bestaudio/best'
            else:
                format_string = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        elif quality_choice == '2':
            print("🔍 Getting format information from first video...")
            # Get first video URL for format analysis
            first_entry = json.loads(entries[0])
            first_url = f"https://www.youtube.com/watch?v={first_entry['id']}"
            format_string = self.select_quality(first_url)
            if not format_string:
                print("❌ Quality selection failed, using automatic best")
                format_string = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        else:
            print("❌ Invalid choice, using automatic best quality")
            format_string = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        
        # Create playlist subdirectory
        playlist_dir = self.download_dir / "playlist_%(playlist_title)s"
        
        cmd = ['yt-dlp', '-f', format_string]
        cmd.extend([
            '-o', str(playlist_dir / '%(playlist_index)s - %(title)s.%(ext)s'),
            '--yes-playlist',
            url
        ])
        
        print(f"\n🚀 Starting playlist download with format: {format_string}")
        print(f"📁 Files will be saved to: playlist_[playlist_name]/")
        try:
            subprocess.run(cmd, check=True)
            print("✅ Playlist download completed!")
        except subprocess.CalledProcessError:
            print("❌ Playlist download failed")
            
        input("Press Enter to continue...")
        
    def download_channel(self):
        """Download entire channel with quality selection"""
        print("\n📺 Channel Download")
        print("-" * 30)
        print("⚠️  Warning: This may download many videos!")
        
        url = input("Enter channel URL: ").strip()
        if not url:
            return
            
        # Options for channel download
        print("\nDownload Range Options:")
        print("1. All videos")
        print("2. Latest 10 videos")
        print("3. Latest 50 videos")
        print("4. Videos from last month")
        
        option = input("Choose option (1-4): ").strip()
        
        # Quality selection for channel
        print("\nQuality Selection for Channel:")
        print("1. Quick select (same quality for all videos)")
        print("2. Choose specific quality (same for all videos)")
        
        quality_choice = input("Choose option (1-2): ").strip()
        
        format_string = None
        
        if quality_choice == '1':
            format_type = input("Quick select - (v)ideo+audio or (a)udio only: ").lower()
            if format_type == 'a':
                format_string = 'bestaudio/best'
            else:
                format_string = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        elif quality_choice == '2':
            print("🔍 Getting format information from channel...")
            # For channels, we'll use the channel URL directly for analysis
            format_string = self.select_quality(url)
            if not format_string:
                print("❌ Quality selection failed, using automatic best")
                format_string = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        else:
            print("❌ Invalid choice, using automatic best quality")
            format_string = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        
        cmd = ['yt-dlp', '-f', format_string]
        
        # Add date/count filters based on option
        if option == '2':
            cmd.extend(['--playlist-end', '10'])
        elif option == '3':
            cmd.extend(['--playlist-end', '50'])
        elif option == '4':
            cmd.extend(['--dateafter', 'now-1month'])
        
        # Create channel subdirectory
        channel_dir = self.download_dir / "channel_%(uploader)s"
        
        cmd.extend([
            '-o', str(channel_dir / '%(upload_date)s - %(title)s.%(ext)s'),
            url
        ])
        
        # Show summary before confirmation
        range_desc = {
            '1': 'ALL videos',
            '2': 'latest 10 videos', 
            '3': 'latest 50 videos',
            '4': 'videos from last month'
        }.get(option, 'selected videos')
        
        print(f"\n📋 Summary:")
        print(f"   Range: {range_desc}")
        print(f"   Quality: {format_string}")
        print(f"   Destination: channel_[channel_name]/")
        
        confirm = input(f"\nProceed with channel download? (y/N): ").lower()
        if confirm != 'y':
            return
            
        print(f"\n🚀 Starting channel download...")
        try:
            subprocess.run(cmd, check=True)
            print("✅ Channel download completed!")
        except subprocess.CalledProcessError:
            print("❌ Channel download failed")
            
        input("Press Enter to continue...")
        
    def show_main_menu(self):
        """Display main menu"""
        print("\n🎯 Main Menu")
        print("-" * 30)
        print("1. Download single video")
        print("2. Download playlist")
        print("3. Download channel")
        print("4. Navigate directories")
        print("5. Check dependencies")
        print("6. Exit")
        
    def run(self):
        """Main application loop"""
        self.clear_screen()
        print("🚀 Initializing ytdorn...")
        self.check_dependencies()
        
        while True:
            self.clear_screen()
            self.show_header()
            self.show_main_menu()
            
            choice = input("\nEnter choice (1-6): ").strip()
            
            if choice == '1':
                self.download_single_video()
            elif choice == '2':
                self.download_playlist()
            elif choice == '3':
                self.download_channel()
            elif choice == '4':
                self.navigate_directory()
            elif choice == '5':
                self.check_dependencies()
                input("Press Enter to continue...")
            elif choice == '6':
                print("👋 Thanks for using ytdorn!")
                break
            else:
                print("❌ Invalid choice")
                time.sleep(1)

def main():
    """Entry point"""
    try:
        app = YtDorn()
        app.run()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
