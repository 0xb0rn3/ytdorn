# YtDorn 🎥

[![Version](https://img.shields.io/badge/version-0.1.2-blue.svg)](https://github.com/0xb0rn3/ytdorn/releases)
[![Python](https://img.shields.io/badge/python-3.7+-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

> A powerful and user-friendly command-line tool for downloading YouTube content with a modern terminal interface

YtDorn combines the simplicity of an interactive menu system with the flexibility of command-line automation. Whether you're downloading a single video or batch-processing entire playlists, YtDorn provides an elegant solution with rich visual feedback and comprehensive format options.

## ✨ Features

### 🎨 Interactive Experience
- **Beautiful Terminal UI**: Colorful, menu-driven interface with dynamic spinners and detailed progress bars
- **Smart Navigation**: Guided selections with ETA calculations and download speeds
- **Intelligent Defaults**: Remembers your preferences and recent output directories

### 📥 Versatile Downloads
- **Multiple Content Types**: Single videos, specific playlist items, entire playlists, and full channel content
- **Quality Control**: Choose from various video resolutions (1080p, 720p, 480p) with MP4 preference
- **Audio Extraction**: High-quality audio-only downloads (M4A, Opus) with MP3 conversion support
- **Batch Processing**: Download multiple URLs from a text file in one operation

### ⚡ Advanced Features
- **Custom Presets**: Create and save download configurations for common scenarios
- **Metadata Support**: Download subtitles (with embedding), thumbnails, descriptions, and JSON metadata
- **Cross-Platform**: Runs seamlessly on Linux, macOS, and Windows
- **Smart Dependencies**: Automatic yt-dlp installation and FFmpeg detection

## 🚀 Quick Start

### Prerequisites

Before diving in, make sure you have these essentials installed:

- **Python 3.7+**: The foundation that powers YtDorn
- **yt-dlp**: The core download engine (YtDorn will install this automatically if missing)
- **FFmpeg** *(recommended)*: Required for audio conversion and subtitle embedding

### Installation

Getting YtDorn up and running is straightforward:

```bash
# Clone the repository
git clone https://github.com/0xb0rn3/ytdorn.git
cd ytdorn

# Make the script executable (Linux/macOS)
chmod +x ytdorn.py

# Run YtDorn
python ytdorn.py
```

### Optional: System-Wide Installation

For convenient access from anywhere on your system:

```bash
# Linux/macOS example
sudo ln -s /path/to/your/cloned/ytdorn/ytdorn.py /usr/local/bin/ytdorn

# Now you can simply type:
ytdorn
```

## 🎯 Usage Guide

### Interactive Mode (Recommended)

Launch YtDorn without arguments to enter the guided experience:

```bash
python ytdorn.py
```

You'll be walked through an intuitive process:

1. **Content Selection**: Choose what type of content to download
2. **URL Input**: Paste your YouTube link
3. **Preview**: See basic information about your content
4. **Directory Setup**: Select where to save your downloads
5. **Format Choice**: Pick your preferred quality and format
6. **Extra Options**: Configure subtitles, thumbnails, and more
7. **Confirmation**: Review settings and start downloading

### Command-Line Interface

For power users and automation, YtDorn offers comprehensive CLI options:

#### Basic Downloads

```bash
# Download with best quality to default location
python ytdorn.py -u "https://youtube.com/watch?v=VIDEO_ID"

# Specify quality and output directory
python ytdorn.py -u "VIDEO_URL" -f 720p -o "/path/to/videos"
```

#### Audio Extraction

```bash
# Extract high-quality audio
python ytdorn.py -u "VIDEO_URL" --extract-audio

# Convert to MP3 with specific bitrate
python ytdorn.py -u "VIDEO_URL" --extract-audio --audio-format mp3
```

#### Batch Operations

```bash
# Process multiple URLs from a file
python ytdorn.py --batch urls.txt

# Use a preset for consistent settings
python ytdorn.py --batch urls.txt --preset high_quality_mp4
```

#### Information and Management

```bash
# Get detailed video information
python ytdorn.py --info "VIDEO_URL"

# List all available presets
python ytdorn.py --list-presets

# View all available options
python ytdorn.py --help
```

## ⚙️ Configuration

YtDorn uses a JSON configuration file located at `~/.ytdorn_config.json` to store your preferences and presets. This file automatically tracks your recent output directories and custom download configurations.

### Creating Presets

Presets allow you to save common download configurations for quick reuse. You can create them through the interactive interface or by directly editing the configuration file.

Example preset structure:
```json
{
  "presets": {
    "high_quality_mp4": {
      "format": "1080p",
      "output_dir": "/home/user/Videos/YouTube",
      "subtitles": true,
      "thumbnails": true
    }
  }
}
```

## 📋 Download Options

### Content Types
- **Single Videos**: Download individual YouTube videos
- **Playlists**: Complete playlists or specific items within them
- **Channels**: All videos from a YouTube channel
- **Custom Selections**: Flexible content targeting

### Quality Options
- **Video**: Best available, 1080p, 720p, 480p (MP4 preferred)
- **Audio**: Best quality audio formats (M4A, Opus) or MP3 conversion
- **Custom**: Advanced users can specify any valid yt-dlp format string

### Additional Content
- **Subtitles**: Download and optionally embed subtitle files
- **Thumbnails**: Save video thumbnail images
- **Metadata**: Description files and comprehensive JSON metadata

## 🔧 Dependencies

Understanding YtDorn's dependencies helps ensure smooth operation:

### Core Dependencies
- **yt-dlp**: The download engine that handles YouTube's complex formats and restrictions. YtDorn automatically checks for this and attempts installation via pip if missing.

### Optional but Recommended
- **FFmpeg**: Essential for audio conversion (especially MP3), format transcoding, and subtitle embedding. While not strictly required for basic video downloads, many advanced features depend on it.

If FFmpeg is missing, YtDorn will display a helpful warning and guide you to installation resources. You can typically install it through your system's package manager:

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS (with Homebrew)
brew install ffmpeg

# Windows (with Chocolatey)
choco install ffmpeg
```

## 🤝 Contributing

We welcome contributions from the community! Here's how you can help improve YtDorn:

1. **Fork** the repository on GitHub
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** your changes: `git commit -am 'Add amazing feature'`
4. **Push** to your branch: `git push origin feature/amazing-feature`
5. **Open** a Pull Request with a clear description of your changes

### Development Guidelines
- Follow existing code style and conventions
- Add comments for complex logic
- Test your changes across different platforms when possible
- Update documentation for new features

## 📝 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for complete details.

## 👤 Author

**0xb0rn3** - [GitHub Profile](https://github.com/0xb0rn3)

## 🙏 Acknowledgments

YtDorn builds upon the excellent work of:
- **[yt-dlp team](https://github.com/yt-dlp/yt-dlp)** - For their incredible YouTube download library
- **[FFmpeg project](https://ffmpeg.org/)** - For their indispensable multimedia framework

## 📞 Support

Encountering issues or have suggestions? We're here to help:

- **Bug Reports**: Open an issue on our [GitHub Issues page](https://github.com/0xb0rn3/ytdorn/issues)
- **Feature Requests**: Share your ideas through GitHub Issues
- **Questions**: Check existing issues or start a new discussion

## 📈 Changelog

### v0.1.2 - Current Release

This version represents a significant enhancement focusing on user experience and functionality:

**New Features:**
- Modern terminal interface with rich colors and dynamic visual feedback
- Comprehensive interactive menu system for guided downloads
- Robust CLI interface supporting all major use cases
- External JSON configuration system with preset support
- Intelligent directory management with recent path tracking
- Automated dependency checking and installation assistance

**Improvements:**
- Enhanced error handling with graceful interruption support
- Batch processing capabilities for multiple URL downloads
- Extensive format and quality selection options
- Cross-platform compatibility improvements

---

*Ready to start downloading? Simply run `python ytdorn.py` and let YtDorn guide you through your first download!*
