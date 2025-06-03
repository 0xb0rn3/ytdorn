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
            
    def download_single_video(self):
        """Download a single video with highest quality"""
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
        
        format_choice = input("\nChoose format (v=video+audio, a=audio only): ").lower()
        
        # Build yt-dlp command for highest quality
        cmd = ['yt-dlp']
        
        if format_choice == 'a':
            # Best audio quality
            cmd.extend(['-f', 'bestaudio/best', '--extract-audio'])
        else:
            # Best video+audio quality
            cmd.extend(['-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'])
            
        cmd.extend([
            '-o', str(self.download_dir / '%(title)s.%(ext)s'),
            url
        ])
        
        print("\n🚀 Starting download...")
        try:
            subprocess.run(cmd, check=True)
            print("✅ Download completed!")
        except subprocess.CalledProcessError:
            print("❌ Download failed")
            
        input("Press Enter to continue...")
        
    def download_playlist(self):
        """Download entire playlist"""
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
            
        format_choice = input("Choose format (v=video+audio, a=audio only): ").lower()
        
        # Create playlist subdirectory
        playlist_dir = self.download_dir / "playlist_%(playlist_title)s"
        
        cmd = ['yt-dlp']
        
        if format_choice == 'a':
            cmd.extend(['-f', 'bestaudio/best', '--extract-audio'])
        else:
            cmd.extend(['-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'])
            
        cmd.extend([
            '-o', str(playlist_dir / '%(playlist_index)s - %(title)s.%(ext)s'),
            '--yes-playlist',
            url
        ])
        
        print("\n🚀 Starting playlist download...")
        try:
            subprocess.run(cmd, check=True)
            print("✅ Playlist download completed!")
        except subprocess.CalledProcessError:
            print("❌ Playlist download failed")
            
        input("Press Enter to continue...")
        
    def download_channel(self):
        """Download entire channel"""
        print("\n📺 Channel Download")
        print("-" * 30)
        print("⚠️  Warning: This may download many videos!")
        
        url = input("Enter channel URL: ").strip()
        if not url:
            return
            
        # Options for channel download
        print("\nOptions:")
        print("1. All videos")
        print("2. Latest 10 videos")
        print("3. Latest 50 videos")
        print("4. Videos from last month")
        
        option = input("Choose option (1-4): ").strip()
        
        cmd = ['yt-dlp']
        
        # Add date/count filters based on option
        if option == '2':
            cmd.extend(['--playlist-end', '10'])
        elif option == '3':
            cmd.extend(['--playlist-end', '50'])
        elif option == '4':
            cmd.extend(['--dateafter', 'now-1month'])
            
        format_choice = input("Choose format (v=video+audio, a=audio only): ").lower()
        
        if format_choice == 'a':
            cmd.extend(['-f', 'bestaudio/best', '--extract-audio'])
        else:
            cmd.extend(['-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'])
            
        # Create channel subdirectory
        channel_dir = self.download_dir / "channel_%(uploader)s"
        
        cmd.extend([
            '-o', str(channel_dir / '%(upload_date)s - %(title)s.%(ext)s'),
            url
        ])
        
        confirm = input(f"\nProceed with channel download? (y/N): ").lower()
        if confirm != 'y':
            return
            
        print("\n🚀 Starting channel download...")
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
