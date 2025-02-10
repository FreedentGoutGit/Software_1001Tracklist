import os
import requests
from bs4 import BeautifulSoup
import yt_dlp as youtube_dl
import tkinter as tk
from tkinter import messagebox, ttk

# Function to scrape tracklist from 1001 Tracklists
def scrape_tracklist(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com'
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    tracks = []

    # Find all track names in the tracklist
    for item in soup.select('.tlpItem'):
        # Find the track name
        track_value = item.find('span', class_='trackValue')
        if track_value:
            track_name = track_value.get_text(strip=True)
            tracks.append(track_name)
            print(f"Track Name: {track_name}")
        else:
            print("Track name not found.")

    return tracks

# Function to search YouTube and download MP3
def download_youtube_mp3(query, folder, progress_callback=None):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }],
        'outtmpl': f'{folder}/%(title)s.%(ext)s',
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([f"ytsearch:{query}"])
            if progress_callback:
                progress_callback()
        except Exception as e:
            print(f"Error downloading {query}: {e}")

# Main function to handle the download process
def start_download():
    url = url_entry.get()
    folder = folder_entry.get()

    if not url or not folder:
        messagebox.showerror("Error", "Please enter both the URL and folder name.")
        return

    # Create folder if it doesn't exist
    if not os.path.exists(folder):
        os.makedirs(folder)

    # Scrape the tracklist
    try:
        tracks = scrape_tracklist(url)
        total_tracks = len(tracks)
        progress_bar["maximum"] = total_tracks
        status_label.config(text=f"Found {total_tracks} tracks. Starting download...")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to scrape tracklist: {e}")
        return

    # Download each track
    for i, track in enumerate(tracks):
        status_label.config(text=f"Downloading: {track}")
        download_youtube_mp3(track, folder, lambda: progress_bar.step())
        progress_bar.update()

    status_label.config(text="Download complete!")
    messagebox.showinfo("Success", "All tracks have been downloaded.")

# GUI Setup
app = tk.Tk()
app.title("Playlist Downloader")

# URL Entry
tk.Label(app, text="1001 Tracklists URL:").grid(row=0, column=0, padx=10, pady=10)
url_entry = tk.Entry(app, width=50)
url_entry.grid(row=0, column=1, padx=10, pady=10)

# Folder Entry
tk.Label(app, text="Save Folder Name:").grid(row=1, column=0, padx=10, pady=10)
folder_entry = tk.Entry(app, width=50)
folder_entry.grid(row=1, column=1, padx=10, pady=10)

# Start Button
start_button = tk.Button(app, text="Start Download", command=start_download)
start_button.grid(row=2, column=0, columnspan=2, pady=10)

# Progress Bar
progress_bar = ttk.Progressbar(app, orient="horizontal", length=400, mode="determinate")
progress_bar.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

# Status Label
status_label = tk.Label(app, text="Enter URL and folder name to start.")
status_label.grid(row=4, column=0, columnspan=2, pady=10)

# Run the app
app.mainloop()