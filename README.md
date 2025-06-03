YtDorn v0.1.2

YtDorn is a powerful and user-friendly command-line tool for downloading YouTube content. It features a modern terminal interface, offering a rich interactive experience alongside robust command-line capabilities for scripting and quick downloads.
Key Features

    Interactive Mode: A colorful, menu-driven interface with spinners, progress bars (including ETA & speed), and guided selections.

    Versatile Downloading: Supports single videos, specific playlist items, entire playlists, and channel content.

    Quality & Format Control: Choose from various video resolutions, audio-only extraction (e.g., M4A, Opus), and MP3 conversion.

    CLI Power: Execute downloads directly from the command line with arguments for URL, format, output, and more.

    Batch Downloads: Process a list of URLs from a text file.

    Configuration & Presets: Customize default settings and create presets for common download scenarios via ~/.ytdorn_config.json.

    Smart Directory Handling: Remembers recent output directories and allows setting new defaults interactively.

    Dependency Management: Automatically checks for yt-dlp and attempts installation if missing. Warns about missing FFmpeg.

    Cross-Platform: Designed to run on Linux, macOS, and Windows.

    Metadata & Extras: Option to download subtitles (and embed them), thumbnails, description files, and metadata JSON.

Prerequisites

    Python: Version 3.7 or higher.

    yt-dlp: The core download engine. YtDorn will attempt to install it via pip if not found.

    FFmpeg: Highly recommended for audio extraction, format conversion, and embedding subtitles. YtDorn will warn if it's missing.

Installation

    Clone the Repository:

    git clone [https://github.com/0xb0rn3/ytdorn.git](https://github.com/0xb0rn3/ytdorn.git)
    cd ytdorn

    Run the Script:
    The script is typically named ytdorn.py (or similar).

    python ytdorn.py

    You can make it executable (chmod +x ytdorn.py) for easier calling (./ytdorn.py).

    Optional: Add to PATH:
    For system-wide access (e.g., by just typing ytdorn):

    # Example for Linux/macOS (ensure script is executable)
    # sudo ln -s /path/to/your/cloned/ytdorn/ytdorn.py /usr/local/bin/ytdorn

Getting Started
Interactive Mode (Recommended for most users)

Launch YtDorn without any arguments:

python ytdorn.py

You'll be guided through a series of menus:

    Main Menu: Select download type (single video, full playlist, info, etc.).

    URL Input: Provide the YouTube link.

    Download Preview: Basic information about the content will be shown.

    Output Directory: Choose from default, recent paths, or specify a new one.

    Format Selection: Pick your desired video/audio quality and format.

    Additional Options: Configure subtitles, thumbnails, etc.

    Confirmation: Review and start the download.

Command-Line Interface (CLI)

For quick tasks or scripting, use CLI arguments. Here are some common examples:

    Download a video (best quality, default output):

    python ytdorn.py -u "YOUR_YOUTUBE_VIDEO_URL"

    Download 720p video to a specific folder:

    python ytdorn.py -u "VIDEO_URL" -f 720p -o "/path/to/videos"

    Extract audio as MP3:

    python ytdorn.py -u "VIDEO_URL" --extract-audio --audio-format mp3

    Batch download from urls.txt using a preset:

    python ytdorn.py --batch urls.txt --preset high_quality_mp4

    Get video info (JSON output):

    python ytdorn.py --info "VIDEO_URL"

    List available presets:

    python ytdorn.py --list-presets

    View all CLI options:

    python ytdorn.py --help

Download Options Summary

    Content Types: Single videos, full playlists, channel content, specific playlist items.

    Video Quality: Best available, 1080p, 720p, 480p (MP4 preferred).

    Audio Extraction: Best quality audio (e.g., M4A, Opus) or convert to MP3 (e.g., 192kbps).

    Custom Formats: Advanced users can specify any valid yt-dlp format string.

    Extras: Subtitles (download & embed), thumbnails, description files, metadata JSON.

Output & Configuration

    Output Directory: Chosen interactively or via CLI (-o). Defaults are managed in the config file (typically ~/Downloads/YtDorn or a preset-defined path).

    Configuration File: Located at ~/.ytdorn_config.json. Stores default output directory, recent paths, and user-defined presets.

    Presets: Define collections of settings (format, output directory, extras) for quick use in both interactive and CLI modes.

Dependencies Management

    yt-dlp: Automatically checked on startup. If missing, YtDorn attempts to install it using pip.

    FFmpeg: Checked for availability. If not found, a warning is displayed, as some features (like MP3 conversion or embedding subtitles) require it. Users are typically guided to install it manually via their system's package manager (e.g., apt, brew, choco) or from ffmpeg.org.

Contributing

Contributions are welcome! Please follow these steps:

    Fork the repository (https://github.com/0xb0rn3/ytdorn.git).

    Create a new branch for your feature (git checkout -b feature/your-feature-name).

    Commit your changes (git commit -am 'Add some amazing feature').

    Push to the branch (git push origin feature/your-feature-name).

    Open a Pull Request.

License

This project is licensed under the MIT License. See the LICENSE file for full details.
Author

0xb0rn3 - GitHub Profile
Acknowledgments

    The yt-dlp team for their incredible download library.

    The FFmpeg project for their indispensable multimedia framework.

Support

If you encounter any issues or have suggestions, please open an issue on the GitHub repository issues page.
Changelog (YtDorn v0.1.2)

This version (v0.1.2) represents a significant enhancement with a focus on a rich interactive experience and a capable command-line interface.

    UI/UX: Modern terminal interface with colors, dynamic spinners, and detailed progress bars. Interactive menus for all download operations.

    Core Functionality: Robust downloading of videos, playlists, and channels. Extensive format and quality selection. Audio extraction and MP3 conversion.

    Configuration: External JSON configuration for defaults and presets. Smart tracking of recent output directories.

    CLI: Comprehensive command-line arguments for non-interactive use and scripting, including batch processing and preset utilization.

    Dependencies: Automated yt-dlp installation check and FFmpeg availability warning.

    Error Handling: Improved error reporting and graceful interruption.
