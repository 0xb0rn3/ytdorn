#!/usr/bin/env python3
import sys
import platform
import subprocess
import os
from typing import Tuple
import pkg_resources
import shutil
from datetime import datetime
class Colors:
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
def print_banner():
    print(f"\n{Colors.BLUE}{Colors.BOLD}YtDorn3 {Colors.RESET}{Colors.BLUE}v1.3 by Q4n0{Colors.RESET}")
    print(f"{Colors.BLUE}https://github.com/Q4n0{Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * 40}{Colors.RESET}\n")
def check_dependencies() -> Tuple[bool, bool]:
    yt_dlp_installed = shutil.which('yt-dlp') is not None
    try:
        pkg_resources.get_distribution('yt-dlp')
        yt_dlp_installed = True
    except pkg_resources.DistributionNotFound:
        pass
    ffmpeg_installed = shutil.which('ffmpeg') is not None
    return yt_dlp_installed, ffmpeg_installed
def install_dependencies():
    os_type = platform.system().lower()
    os_bits = platform.machine().lower()
    yt_dlp_installed, ffmpeg_installed = check_dependencies()
    print("\nChecking dependencies...")
    if not yt_dlp_installed:
        print("\nInstalling yt-dlp...")
        try:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp", "--break-system-packages"], 
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except subprocess.CalledProcessError:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"], 
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"{Colors.GREEN}✓ yt-dlp installed successfully!{Colors.RESET}")
        except subprocess.CalledProcessError:
            print(f"{Colors.RED}✗ Error installing yt-dlp.{Colors.RESET}")
            print("\nTry installing manually with either:")
            print("1. pip install yt-dlp --break-system-packages")
            print("2. pip install yt-dlp --user")
            print("3. Create and use a virtual environment first")
            sys.exit(1)
    if not ffmpeg_installed:
        print("\nInstalling ffmpeg...")
        try:
            if os_type == "windows":
                if shutil.which('choco'):
                    subprocess.check_call(['choco', 'install', 'ffmpeg', '-y'])
                else:
                    print("Please install Chocolatey (https://chocolatey.org/) or ffmpeg manually")
                    print("FFmpeg download page: https://ffmpeg.org/download.html")
                    sys.exit(1)
            elif os_type == "darwin":
                if shutil.which('brew'):
                    subprocess.check_call(['brew', 'install', 'ffmpeg'])
                else:
                    print("Please install Homebrew (https://brew.sh/) or ffmpeg manually")
                    print("You can install Homebrew with:")
                    print('/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"')
                    sys.exit(1)
            elif os_type == "linux":
                if shutil.which('apt-get'):
                    subprocess.check_call(['sudo', 'apt-get', 'update'])
                    subprocess.check_call(['sudo', 'apt-get', 'install', '-y', 'ffmpeg'])
                elif shutil.which('dnf'):
                    subprocess.check_call(['sudo', 'dnf', 'install', '-y', 'ffmpeg'])
                elif shutil.which('pacman'):
                    subprocess.check_call(['sudo', 'pacman', '-S', '--noconfirm', 'ffmpeg'])
                elif shutil.which('zypper'):
                    subprocess.check_call(['sudo', 'zypper', 'install', '-y', 'ffmpeg'])
                else:
                    print("Unable to detect package manager. Please install ffmpeg manually.")
                    print("FFmpeg download page: https://ffmpeg.org/download.html")
                    sys.exit(1)
            print(f"{Colors.GREEN}✓ ffmpeg installed successfully!{Colors.RESET}")
        except subprocess.CalledProcessError as e:
            print(f"{Colors.RED}✗ Error installing ffmpeg: {str(e)}{Colors.RESET}")
            print("Please install ffmpeg manually from: https://ffmpeg.org/download.html")
            sys.exit(1)
def create_progress_bar(current, total, width=30):
    progress = int(width * current / total) if total > 0 else 0
    blocks = '█' * progress + '░' * (width - progress)
    percentage = current / total * 100 if total > 0 else 0
    return f"[{Colors.YELLOW}{blocks}{Colors.RESET}] {percentage:0.1f}%"
def format_size(bytes):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024:
            return f"{bytes:.1f}{unit}"
        bytes /= 1024
    return f"{bytes:.1f}TB"
def download_hook(d):
    if d['status'] == 'downloading':
        sys.stdout.write('\r\033[K')
        filename = os.path.basename(d.get('filename', ''))
        if filename:
            total_bytes = d.get('total_bytes', 0)
            downloaded_bytes = d.get('downloaded_bytes', 0)
            speed = d.get('speed', 0)
            progress_bar = create_progress_bar(downloaded_bytes, total_bytes)
            downloaded = format_size(downloaded_bytes)
            total = format_size(total_bytes) if total_bytes else 'N/A'
            speed_str = f"{format_size(speed)}/s" if speed else 'N/A'
            status = f"\r↓ {filename[:30]}... {progress_bar} ({downloaded}/{total}) @ {speed_str}"
            sys.stdout.write(status)
            sys.stdout.flush()
    elif d['status'] == 'finished':
        sys.stdout.write('\r\033[K')
        sys.stdout.write(f"\r{Colors.GREEN}✓ Download complete{Colors.RESET}\n")
        sys.stdout.flush()
def get_download_type():
    print(f"\n{Colors.CYAN}Download Type:{Colors.RESET}")
    print("1. 📋 Playlist Download")
    print("2. 🎥 Single Video Download")
    while True:
        choice = input(f"\nSelect option (1-2): ").strip()
        if choice in ['1', '2']:
            return choice
def get_download_options():
    print(f"\n{Colors.CYAN}Quality Options:{Colors.RESET}")
    print("1. 🎥 Best Quality Video (1080p or best available)")
    print("2. 🎥 Medium Quality Video (720p)")
    print("3. 🎥 Low Quality Video (480p)")
    print("4. 🎵 Audio Only (Best Quality)")
    print("5. 🎵 Audio Only (Medium Quality)")
    while True:
        choice = input("\nSelect option (1-5): ").strip()
        if choice in ['1', '2', '3', '4', '5']:
            return choice
def get_format_options(choice):
    if choice == '1':
        return {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'format_note': 'Best Quality Video'
        }
    elif choice == '2':
        return {
            'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best',
            'format_note': '720p Video'
        }
    elif choice == '3':
        return {
            'format': 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best',
            'format_note': '480p Video'
        }
    elif choice == '4':
        return {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'format_note': 'Best Quality Audio',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'm4a',
                'preferredquality': '192',
            }]
        }
    else:
        return {
            'format': 'worstaudio/worst',
            'format_note': 'Medium Quality Audio',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'm4a',
                'preferredquality': '128',
            }]
        }
def is_playlist_url(url):
    return 'playlist' in url or 'list=' in url
def download_playlist(playlist_url, output_dir='downloads', format_choice='1'):
    from yt_dlp import YoutubeDL
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    format_options = get_format_options(format_choice)
    ydl_opts = {
        'outtmpl': os.path.join(output_dir, '%(playlist)s', '%(title)s.%(ext)s'),
        'ignoreerrors': True,
        'noplaylist': False,
        'quiet': True,
        'no_warnings': True,
        'progress_hooks': [download_hook],
        'no_color': True,
        'extract_flat': True,
        'logger': type('QuietLogger', (), {
            'debug': lambda *args, **kw: None,
            'warning': lambda *args, **kw: None,
            'error': lambda *args, **kw: None,
        })()
    }
    ydl_opts.update(format_options)
    try:
        print(f"\n{Colors.CYAN}📥 Initializing download...{Colors.RESET}")
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(playlist_url, download=False)
            playlist_title = info.get('title', 'Playlist')
            video_count = len(info['entries'])
            print(f"\n{Colors.CYAN}📑 Playlist: {Colors.RESET}{playlist_title}")
            print(f"{Colors.CYAN}📊 Total items: {Colors.RESET}{video_count}\n")
            ydl_opts['extract_flat'] = False
            with YoutubeDL(ydl_opts) as ydl_download:
                ydl_download.download([playlist_url])
        print(f"\n{Colors.GREEN}✨ All downloads completed successfully!{Colors.RESET}")
        print(f"{Colors.CYAN}📂 Files saved in: {Colors.RESET}{os.path.abspath(output_dir)}\n")
    except Exception as e:
        print(f'\n{Colors.RED}❌ Error occurred: {str(e)}{Colors.RESET}')
def download_single_video(video_url, output_dir='downloads', format_choice='1'):
    from yt_dlp import YoutubeDL
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    format_options = get_format_options(format_choice)
    ydl_opts = {
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'ignoreerrors': True,
        'quiet': True,
        'no_warnings': True,
        'progress_hooks': [download_hook],
        'no_color': True,
        'logger': type('QuietLogger', (), {
            'debug': lambda *args, **kw: None,
            'warning': lambda *args, **kw: None,
            'error': lambda *args, **kw: None,
        })()
    }
    ydl_opts.update(format_options)
    try:
        print(f"\n{Colors.CYAN}📥 Initializing download...{Colors.RESET}")
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            video_title = info.get('title', 'Video')
            print(f"\n{Colors.CYAN}🎬 Video: {Colors.RESET}{video_title}")
            ydl.download([video_url])
        print(f"\n{Colors.GREEN}✨ Download completed successfully!{Colors.RESET}")
        print(f"{Colors.CYAN}📂 File saved in: {Colors.RESET}{os.path.abspath(output_dir)}\n")
    except Exception as e:
        print(f'\n{Colors.RED}❌ Error occurred: {str(e)}{Colors.RESET}')
def main():
    print_banner()
    install_dependencies()
    print(f"\n{Colors.GREEN}✓ Ready to download!{Colors.RESET}")
    while True:
        print(f"\n{Colors.CYAN}{'=' * 40}{Colors.RESET}")
        download_type = get_download_type()
        url = input(f"\n{Colors.CYAN}🔗 Enter URL (or 'exit' to quit): {Colors.RESET}").strip()
        if url.lower() == 'exit':
            break
        if download_type == '1' and not is_playlist_url(url):
            print(f"\n{Colors.YELLOW}⚠️  This appears to be a single video URL. Would you like to:{Colors.RESET}")
            print("1. Download as single video")
            print("2. Enter a different URL")
            choice = input("\nSelect option (1-2): ").strip()
            if choice == '2':
                continue
            download_type = '2'
        elif download_type == '2' and is_playlist_url(url):
            print(f"\n{Colors.YELLOW}⚠️  This appears to be a playlist URL. Would you like to:{Colors.RESET}")
            print("1. Download entire playlist")
            print("2. Enter a different URL")
            choice = input("\nSelect option (1-2): ").strip()
            if choice == '2':
                continue
            download_type = '1'
        output_dir = input(f"{Colors.CYAN}📁 Enter output directory (press Enter for default 'downloads'): {Colors.RESET}").strip()
        if not output_dir:
            output_dir = 'downloads'
        format_choice = get_download_options()
        if download_type == '1':
            download_playlist(url, output_dir, format_choice)
        else:
            download_single_video(url, output_dir, format_choice)
        again = input(f"\n{Colors.CYAN}🔄 Download another video/playlist? (y/n): {Colors.RESET}").strip().lower()
        if again != 'y':
            break
   print(f"\n{Colors.GREEN}👋 Thanks for using Ytdorn3!{Colors.RESET}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}👋 Download canceled. Goodbye!{Colors.RESET}\n")
        sys.exit(0)
