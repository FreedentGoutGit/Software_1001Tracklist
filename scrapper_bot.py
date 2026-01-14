import os
import requests
from bs4 import BeautifulSoup
import yt_dlp as youtube_dl
import customtkinter as ctk
from tkinter import messagebox, filedialog
import threading
from pathlib import Path

# Function to scrape tracklist from 1001 Tracklists
def scrape_tracklist(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        tracks = []
        for item in soup.select('.tlpItem'):
            track_value = item.find('span', class_='trackValue')
            if track_value:
                track_name = track_value.get_text(strip=True)
                tracks.append(track_name)
                print(f"Track Name: {track_name}")
        return tracks
    except requests.RequestException as e:
        print(f"Error scraping {url}: {e}")
        return []

# Function to get tracks from YouTube playlist
def get_youtube_playlist_tracks(url):
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'skip_download': True
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            tracks = [entry['title'] for entry in info.get('entries', [])]
            return tracks
        except Exception as e:
            print(f"Error extracting playlist: {e}")
            return []

# Function to search YouTube and download MP3
def download_youtube_mp3(query, folder, progress_callback=None, quality="320"):
    if quality == "Best":
        format_str = 'bestaudio/best'
        pref_quality = '320'
    else:
        format_str = f'bestaudio[abr<={quality}]/bestaudio'
        pref_quality = quality
    
    ydl_opts = {
        'format': format_str,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': pref_quality,
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

def start_download():
    url = url_entry.get().strip()
    folder = folder_entry.get().strip()
    
    if not url or not folder:
        messagebox.showerror("Validation Error", "Please enter both the URL and folder name.")
        return
    
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    start_button.configure(state="disabled")
    progress_bar.set(0)
    
    def download_thread():
        try:
            source = source_var.get()
            if source == "1001 Tracklists":
                tracks = scrape_tracklist(url)
            elif source == "YouTube Playlist":
                tracks = get_youtube_playlist_tracks(url)
            else:
                tracks = []
            
            total_tracks = len(tracks)
            
            if total_tracks == 0:
                status_label.configure(text="No tracks found.", text_color="red")
                start_button.configure(state="normal")
                return
            
            status_label.configure(text=f"Found {total_tracks} tracks. Downloading...", text_color="white")
            app.update()
            
            for i, track in enumerate(tracks):
                status_label.configure(text=f"({i+1}/{total_tracks}) {track[:50]}...")
                app.update()
                download_youtube_mp3(track, folder, lambda: None, quality_var.get())
                progress_bar.set((i + 1) / total_tracks)
                app.update()
            
            status_label.configure(text="✓ Complete! All tracks downloaded.", text_color="green")
            messagebox.showinfo("Success", f"Downloaded {total_tracks} tracks to:\n{folder}")
        
        except Exception as e:
            status_label.configure(text=f"Error: {str(e)[:50]}", text_color="red")
            messagebox.showerror("Error", f"Failed:\n{e}")
        
        finally:
            start_button.configure(state="normal")
    
    thread = threading.Thread(target=download_thread, daemon=True)
    thread.start()

def browse_folder():
    folder = filedialog.askdirectory(title="Select Folder")
    if folder:
        folder_entry.delete(0, "end")
        folder_entry.insert(0, folder)

if __name__ == "__main__":
    # Set appearance
    ctk.set_appearance_mode("dark")

    # Main window
    app = ctk.CTk()
    app.title("Playlist Downloader")
    app.geometry("700x650")
    app.resizable(False, False)

    # Main frame
    main_frame = ctk.CTkFrame(app, fg_color="#1a1a1a")
    main_frame.pack(fill="both", expand=True, padx=0, pady=0)

    # Header
    header_frame = ctk.CTkFrame(main_frame, fg_color="#000000", corner_radius=0)
    header_frame.pack(fill="x", padx=0, pady=0)

    title_label = ctk.CTkLabel(
        header_frame,
        text="Playlist Downloader",
        font=("Helvetica", 28, "bold"),
        text_color="white"
    )
    title_label.pack(pady=20, padx=20)

    subtitle_label = ctk.CTkLabel(
        header_frame,
        text="Download high-quality MP3s from 1001 Tracklists or YouTube",
        font=("Helvetica", 11),
        text_color="#b0b0b0"
    )
    subtitle_label.pack(pady=(0, 15), padx=20)

    # Content frame
    content_frame = ctk.CTkFrame(main_frame, fg_color="#1a1a1a")
    content_frame.pack(fill="both", expand=True, padx=30, pady=30)

    # Top options frame for dropdowns
    options_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    options_frame.pack(fill="x", pady=(0, 25))

    # Source selection
    source_label = ctk.CTkLabel(
        options_frame,
        text="Source",
        font=("Helvetica", 10, "bold"),
        text_color="#e0e0e0"
    )
    source_label.grid(row=0, column=0, sticky="w", padx=(0, 10))

    source_var = ctk.StringVar(value="1001 Tracklists")
    source_menu = ctk.CTkOptionMenu(
        options_frame,
        values=["1001 Tracklists", "YouTube Playlist"],
        variable=source_var,
        fg_color="#2a2a2a",
        button_color="#ffffff",
        button_hover_color="#e0e0e0",
        text_color="#000000",
        font=("Helvetica", 9, "bold"),
        dropdown_font=("Helvetica", 9),
        dropdown_fg_color="#2a2a2a",
        dropdown_hover_color="#3a3a3a",
        dropdown_text_color="white",
        width=140
    )
    source_menu.grid(row=0, column=1, sticky="w", padx=(0, 20))

    # Quality selection
    quality_label = ctk.CTkLabel(
        options_frame,
        text="Quality",
        font=("Helvetica", 10, "bold"),
        text_color="#e0e0e0"
    )
    quality_label.grid(row=0, column=2, sticky="w", padx=(0, 10))

    quality_var = ctk.StringVar(value="320")
    quality_menu = ctk.CTkOptionMenu(
        options_frame,
        values=["128", "256", "320", "Best"],
        variable=quality_var,
        fg_color="#2a2a2a",
        button_color="#ffffff",
        button_hover_color="#e0e0e0",
        text_color="#000000",
        font=("Helvetica", 9, "bold"),
        dropdown_font=("Helvetica", 9),
        dropdown_fg_color="#2a2a2a",
        dropdown_hover_color="#3a3a3a",
        dropdown_text_color="white",
        width=100
    )
    quality_menu.grid(row=0, column=3, sticky="w", padx=(0, 30))

    # Download button on the right
    start_button = ctk.CTkButton(
        options_frame,
        text="Download",
        command=start_download,
        fg_color="#000000",
        hover_color="#1a1a1a",
        text_color="white",
        font=("Helvetica", 10, "bold"),
        corner_radius=4,
        height=32,
        width=120,
        border_width=1,
        border_color="#555555"
    )
    start_button.grid(row=0, column=4, sticky="e", padx=(20, 0))

    # Divider
    divider = ctk.CTkFrame(content_frame, fg_color="#2a2a2a", height=1)
    divider.pack(fill="x", pady=(0, 25))

    # URL input
    url_label = ctk.CTkLabel(
        content_frame,
        text="Playlist URL",
        font=("Helvetica", 12, "bold"),
        text_color="white"
    )
    url_label.pack(anchor="w", pady=(0, 8))

    url_entry = ctk.CTkEntry(
        content_frame,
        placeholder_text="https://...",
        fg_color="#2a2a2a",
        border_color="#444444",
        text_color="white",
        placeholder_text_color="#666666",
        font=("Helvetica", 10),
        border_width=2
    )
    url_entry.pack(fill="x", pady=(0, 20), ipady=8)

    # Folder selection
    folder_label = ctk.CTkLabel(
        content_frame,
        text="Save Folder",
        font=("Helvetica", 12, "bold"),
        text_color="white"
    )
    folder_label.pack(anchor="w", pady=(0, 8))

    folder_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    folder_frame.pack(fill="x", pady=(0, 25))

    folder_entry = ctk.CTkEntry(
        folder_frame,
        placeholder_text=str(Path.home() / "Downloads" / "Playlist"),
        fg_color="#2a2a2a",
        border_color="#444444",
        text_color="white",
        placeholder_text_color="#666666",
        font=("Helvetica", 10),
        border_width=2
    )
    folder_entry.pack(side="left", fill="both", expand=True, ipady=8)

    browse_button = ctk.CTkButton(
        folder_frame,
        text="Browse",
        command=browse_folder,
        fg_color="#ffffff",
        hover_color="#e0e0e0",
        text_color="#000000",
        font=("Helvetica", 10, "bold"),
        width=80,
        border_width=1,
        border_color="#cccccc"
    )
    browse_button.pack(side="right", padx=(10, 0), pady=0)

    # Progress bar
    progress_bar = ctk.CTkProgressBar(
        content_frame,
        fg_color="#2a2a2a",
        progress_color="#ffffff",
        corner_radius=4,
        height=6
    )
    progress_bar.pack(fill="x", pady=(0, 15))
    progress_bar.set(0)

    # Status label
    status_label = ctk.CTkLabel(
        content_frame,
        text="Ready to download",
        font=("Helvetica", 10),
        text_color="#888888"
    )
    status_label.pack(anchor="w")

    app.mainloop()