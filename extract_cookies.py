import sys
import subprocess
import argparse
import os

def main():
    parser = argparse.ArgumentParser(description="Extract browser cookies for yt-dlp authentication and save to cookies.txt.")
    parser.add_argument('--browser', type=str, default='chrome', help='Browser to extract cookies from (e.g., chrome, firefox, edge, brave)')
    parser.add_argument('--output', type=str, default='cookies.txt', help='Output file to save the Netscape format cookies')
    
    args = parser.parse_args()

    print(f"Attempting to extract cookies from '{args.browser}'...")
    print(f"Destination: {os.path.abspath(args.output)}\n")

    # yt-dlp allows exporting cookies by passing just these arguments with a dummy URL or simply calling it.
    # However, to be safe and avoid the "URL needed" error, we will try to fetch info of a random public YouTube video.
    # We use skip-download so it's very fast, and we just extract cookies.
    dummy_url = "https://www.youtube.com/watch?v=BaW_jenozKc"  # YouTube dummy video
    
    command = [
        sys.executable, '-m', 'yt_dlp',
        '--cookies-from-browser', args.browser,
        '--cookies', args.output,
        '--skip-download',
        '--print', 'Using yt-dlp to extract cookies...',
        dummy_url
    ]

    try:
        subprocess.run(command, check=True)
        print(f"\n✅ Success! Browser cookies saved to '{args.output}'")
        print("Your flask application will now automatically use this file for authentication.")
        print("Note: The generated file gives full access to your browser session. Do not share it.")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error during extraction. Ensure your browser '{args.browser}' is closed if on Windows and try again.")
        print(f"Details: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
