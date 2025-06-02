# YtDorn

YtDorn3 is a feature-rich command-line YouTube downloader with an elegant terminal user interface. It supports downloading both single videos and playlists with various quality options and real-time progress tracking.

![YtDorn Banner](https://raw.githubusercontent.com/0xb0rn3/ytdorn/main/.github/banner.png)

## Features

- Beautiful terminal user interface with color gradients and animations
- Download single videos or entire playlists
- Multiple quality options for both video and audio
- Real-time download progress with ETA and speed indicators
- Automatic dependency management
- Cross-platform support (Linux, macOS, Windows)
- Playlist organization with automatic folder creation
- Graceful error handling and recovery
- Support for various audio and video formats

## Requirements

- Python 3.6 or higher
- FFmpeg (automatically installed if missing)
- yt-dlp (automatically installed if missing)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/0xb0rn3/ytdorn.git
cd ytdorn
```

2. Make the script executable:
```bash
chmod +x ytdorn
```

3. Optional: Add to PATH for system-wide access:
```bash
sudo ln -s $(pwd)/ytdorn /usr/local/bin/ytdorn
```

## Usage

### Basic Usage

Simply run the script:
```bash
./ytdorn
```

Follow the interactive menu to:
1. Choose between playlist or single video download
2. Enter the YouTube URL
3. Specify output directory (defaults to 'downloads')
4. Select quality options

### Quality Options

1. Best Quality Video (1080p or best available)
2. Medium Quality Video (720p)
3. Low Quality Video (480p)
4. Audio Only (Best Quality)
5. Audio Only (Medium Quality)

### Examples

Download a single video:
```bash
./ytdorn
# Select: Single Video Download
# Enter URL: https://youtube.com/watch?v=example
# Choose quality and output directory through the interactive menu
```

Download a playlist:
```bash
./ytdorn
# Select: Playlist Download
# Enter URL: https://youtube.com/playlist?list=example
# Choose quality and output directory through the interactive menu
```

## Output Structure

Downloads are organized as follows:

```
downloads/
├── single_videos/
│   ├── video1.mp4
│   └── video2.mp4
└── playlists/
    └── Playlist_Name/
        ├── video1.mp4
        └── video2.mp4
```
# Interactive mode
python ytdorn.py

# Quick download
python ytdorn.py -u "https://youtube.com/watch?v=..." -f best

# Audio extraction
python ytdorn.py -u "URL" --extract-audio --audio-format mp3

# Batch download
python ytdorn.py --batch urls.txt --preset high_quality
## Dependencies

YtDorn automatically manages its dependencies:

- **yt-dlp**: Used for video extraction and downloading
- **FFmpeg**: Required for video/audio processing
- **Python packages**: All required packages are automatically installed

## Error Handling

- Graceful handling of network interruptions
- Clear error messages with recovery suggestions
- Automatic retry on temporary failures
- Safe cancellation with Ctrl+C

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Known Issues

- Some region-restricted videos may not download
- Download speed depends on YouTube's server load
- Certain live streams may not be supported

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**0xb0rn3** - [GitHub Profile](https://github.com/0xb0rn3)

## Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for the core downloading functionality
- [FFmpeg](https://ffmpeg.org/) for media processing capabilities

## Support

For support, please open an issue on the [GitHub repository](https://github.com/0xb0rn3/ytdorn/issues).

## Changelog

### v1.3
- Added gradient progress bar
- Improved error handling
- Enhanced playlist organization
- Added ETA calculation
- Improved cross-platform support

### v1.2
- Added audio-only download options
- Enhanced terminal UI
- Improved dependency management

### v1.1
- Added playlist support
- Enhanced progress tracking
- Added quality options

### v1.0
- Initial release
- Basic video downloading
- Terminal UI
