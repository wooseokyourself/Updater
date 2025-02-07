import sys
import json
import requests
from packaging import version
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import subprocess
import os
from urllib.parse import urlparse
import locale
import ctypes
import time

# Get system language using Windows API
def get_system_language():
    try:
        windll = ctypes.windll.kernel32
        LOCALE_SYSTEM_DEFAULT = 0x0800
        LOCALE_SISO639LANGNAME = 0x0059
        language_code = ctypes.create_unicode_buffer(9)
        windll.GetLocaleInfoW(LOCALE_SYSTEM_DEFAULT, LOCALE_SISO639LANGNAME, language_code, 9)
        return language_code.value
    except:
        return 'en'

# Get system language
system_lang = get_system_language()
is_korean = system_lang == 'ko'

# Localized messages
MESSAGES = {
    'en': {
        'download_title': "Update Download",
        'download_start': "Starting download...",
        'downloading': "Downloading... ({progress})",
        'download_complete': "Download complete. Launching installer...",
        'update_available': "Update Available",
        'update_prompt': "New version {latest_version} is available. Current version: {current_version}\n\nDo you want to update?",
        'cancel_button': "Cancel",
        'download_cancelled': "Download Cancelled",
        'cancel_message': "Download has been cancelled.",
        'error': "Error",
        'network_error': "Network error occurred:\n{error}",
        'launcher_error': "Error launching update program.",
        'json_error': "Invalid version information file.",
        'unexpected_error': "An unexpected error occurred:\n{error}",
        'version_format_error': "Invalid version information format.",
        'up_to_date': "Up to Date",
        'up_to_date_message': "You are using the latest version.",
        'usage': "Usage: updater.py <version_check_url> <current_version> [save_path] [app_path]",
        'install_complete': "Installation Complete",
        'cleaning_up': "Cleaning up temporary files..."
    },
    'ko': {
        'download_title': "업데이트 다운로드",
        'download_start': "다운로드를 시작합니다...",
        'downloading': "다운로드 중... ({progress})",
        'download_complete': "다운로드 완료. 설치 프로그램을 실행합니다...",
        'update_available': "업데이트 가능",
        'update_prompt': "새로운 버전 {latest_version}이(가) 있습니다. 현재 버전: {current_version}\n\n업데이트하시겠습니까?",
        'cancel_button': "취소",
        'download_cancelled': "다운로드 취소됨",
        'cancel_message': "다운로드가 취소되었습니다.",
        'error': "오류",
        'network_error': "네트워크 오류가 발생했습니다:\n{error}",
        'launcher_error': "업데이트 프로그램 실행 중 오류가 발생했습니다.",
        'json_error': "버전 정보 파일이 올바르지 않습니다.",
        'unexpected_error': "예상치 못한 오류가 발생했습니다:\n{error}",
        'version_format_error': "버전 정보 형식이 잘못되었습니다.",
        'up_to_date': "알림",
        'up_to_date_message': "현재 최신 버전을 사용 중입니다.",
        'usage': "사용법: updater.py <version_check_url> <current_version> [save_path] [app_path]",
        'install_complete': "설치 완료",
        'cleaning_up': "임시 파일을 정리하는 중..."
    }
}

# Get messages based on system language
msgs = MESSAGES['ko'] if is_korean else MESSAGES['en']

class ProgressDialog:
    def __init__(self, title, message):
        self.root = tk.Tk()
        self.root.title(title)
        self.cancelled = False
        self.file_handle = None
        
        # Window size and position
        window_width = 300
        window_height = 150
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        
        # Window properties
        self.root.resizable(False, False)
        self.root.attributes('-topmost', True)
        self.root.protocol("WM_DELETE_WINDOW", self.cancel)
        
        # Message label
        self.label = tk.Label(self.root, text=message, padx=20, pady=10)
        self.label.pack()
        
        # Progress bar
        self.progress = ttk.Progressbar(self.root, length=250, mode='determinate')
        self.progress.pack(padx=20, pady=10)
        
        # Cancel button
        self.cancel_button = tk.Button(self.root, text=msgs['cancel_button'], command=self.cancel)
        self.cancel_button.pack(pady=10)
        
    def update_progress(self, progress):
        if not self.cancelled and self.root:
            self.progress['value'] = progress
            self.root.update()
            
    def update_message(self, message):
        if not self.cancelled and self.root:
            self.label.config(text=message)
            self.root.update()
        
    def cancel(self):
        self.cancelled = True
        if self.file_handle:
            self.file_handle.close()
        self.close()
            
    def close(self):
        if self.root:
            try:
                self.root.quit()
                self.root.destroy()
            except:
                pass

def safe_remove_file(file_path, max_attempts=5, delay=1):
    """Safely remove a file with multiple attempts"""
    for i in range(max_attempts):
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
        except Exception as e:
            if i < max_attempts - 1:
                time.sleep(delay)
            continue
    return False

def get_download_path(save_path, filename):
    """Get the full path for downloading the file"""
    try:
        from urllib.parse import unquote
        decoded_filename = unquote(filename)
        if save_path and os.path.isdir(save_path):
            return os.path.join(save_path, decoded_filename)
        return decoded_filename
    except Exception as e:
        print(f"Error processing filename: {e}")
        return filename

def download_file(url, destination, progress_dialog):
    """Download a file from URL to the specified destination with progress updates"""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Get file size
        file_size = int(response.headers.get('content-length', 0))
        
        if (file_size == 0): 
            raise Exception('file ' + url + " is empty or missing.")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        
        # Download with progress
        downloaded_size = 0
        progress_dialog.file_handle = open(destination, 'wb')
        
        for chunk in response.iter_content(chunk_size=8192):
            if progress_dialog.cancelled:
                progress_dialog.file_handle.close()
                safe_remove_file(destination)
                return False
                
            if chunk:
                progress_dialog.file_handle.write(chunk)
                downloaded_size += len(chunk)
                
                if file_size:
                    progress = (downloaded_size * 100) / file_size
                    progress_text = f"{progress:.1f}%"
                else:
                    progress = 0
                    progress_text = f"{downloaded_size/1024/1024:.1f} MB"
                    
                progress_dialog.update_progress(progress)
                progress_dialog.update_message(msgs['downloading'].format(progress=progress_text))
        
        progress_dialog.file_handle.close()
        progress_dialog.file_handle = None
        return True
        
    except Exception as e:
        if progress_dialog.file_handle:
            progress_dialog.file_handle.close()
            progress_dialog.file_handle = None
        safe_remove_file(destination)
        raise e

def create_batch_script(installer_path, app_path):
    """Create a batch script that will run the installer, delete it, and restart the app"""
    try:
        batch_path = os.path.join(os.path.dirname(installer_path), "update_and_restart.bat")
        
        installer_path = os.path.abspath(installer_path)
        if app_path:
            app_path = os.path.abspath(app_path)
        
        with open(batch_path, 'w', encoding='utf-8') as f:
            f.write('@echo off\n')
            f.write('echo Starting installation...\n')
            f.write(f'echo Installer path: {installer_path}\n')
            
            f.write(f'cd /d "{os.path.dirname(installer_path)}"\n')
            
            installer_filename = os.path.basename(installer_path)
            
            f.write('echo Checking installer type...\n')
            f.write(f'if /i "%~x1" == ".msi" (\n')
            f.write(f'    echo Installing MSI package...\n')
            f.write(f'    msiexec /i "{installer_filename}" /passive /log "install.log"\n')
            f.write('    if errorlevel 1 goto error\n')
            f.write(') else (\n')
            f.write(f'    echo Running executable installer...\n')
            f.write(f'    start /wait "" "{installer_filename}"\n')
            f.write('    if errorlevel 1 goto error\n')
            f.write(')\n')
            
            f.write('timeout /t 5 /nobreak\n')
            
            f.write(f'del /f /q "{installer_filename}"\n')
            f.write('if exist "install.log" del /f /q "install.log"\n')
            
            if app_path:
                f.write(f'echo Starting application: {app_path}\n')
                f.write(f'start "" "{app_path}"\n')
            
            f.write('(goto) 2>nul & del "%~f0"\n')
            f.write('exit /b 0\n')
            
            f.write(':error\n')
            f.write('echo Installation failed!\n')
            f.write('if exist "install.log" type install.log\n')
            f.write('pause\n')
            f.write('exit /b 1\n')
        
        return batch_path
    except Exception as e:
        print(f"Error creating batch script: {e}")
        return None

def run_installer(file_path, app_path):
    """Run the installer with appropriate command based on file type"""
    try:
        if not os.path.exists(file_path):
            print(f"Could Not Find {file_path}")
            return False
            
        if file_path.lower().endswith('.msi'):
            print(f"Creating batch script for MSI installation: {file_path}")
            batch_path = create_batch_script(file_path, app_path)
            
            if batch_path and os.path.exists(batch_path):
                print(f"Running batch script: {batch_path}")
                subprocess.Popen(['cmd', '/c', batch_path], 
                               shell=True,
                               creationflags=subprocess.CREATE_NEW_CONSOLE)
                return True
            return False
        else:
            subprocess.Popen([file_path])
            return True
            
    except Exception as e:
        print(f"Error executing update: {e}")
        return False
    
def check_version_and_update(version_check_url, current_version, save_path=None, app_path=None):
    root = tk.Tk()
    root.withdraw()
    
    try:
        # Download and parse version check JSON
        response = requests.get(version_check_url)
        response.raise_for_status()
        version_info = response.json()
        
        # Extract version information
        latest_version = version_info.get('latest-version')
        download_url = version_info.get('download-url')
        
        if not latest_version or not download_url:
            messagebox.showerror(msgs['error'], msgs['version_format_error'])
            return
        
        # Compare versions
        if version.parse(latest_version) > version.parse(current_version):
            # Show update confirmation dialog
            result = messagebox.askyesno(
                msgs['update_available'],
                msgs['update_prompt'].format(latest_version=latest_version, current_version=current_version)
            )
            
            if result:
                # Create progress dialog
                progress_dialog = ProgressDialog(msgs['download_title'], msgs['download_start'])
                
                try:
                    # Download the update
                    filename = os.path.basename(urlparse(download_url).path)
                    if not filename:
                        filename = "update.exe"
                    
                    # Get full download path
                    download_path = get_download_path(save_path, filename)
                    
                    # Download file with progress updates
                    if download_file(download_url, download_path, progress_dialog):
                        progress_dialog.update_message(msgs['download_complete'])
                        progress_dialog.root.update()
                        progress_dialog.close()
                        
                        # Execute the downloaded file
                        if run_installer(download_path, app_path):
                            sys.exit(0)
                        else:
                            messagebox.showerror(msgs['error'], msgs['launcher_error'])
                    elif progress_dialog.cancelled:
                        messagebox.showinfo(msgs['download_cancelled'], msgs['cancel_message'])
                
                except requests.exceptions.RequestException as e:
                    print("Updater error: ", msgs['network_error'].format(error=str(e)), file=sys.stderr)
                    progress_dialog.close()
                except Exception as e:
                    progress_dialog.close()
                    messagebox.showerror(msgs['error'], msgs['unexpected_error'].format(error=str(e)))
            
    except requests.exceptions.RequestException as e:
        print("Updater error: ", msgs['network_error'].format(error=str(e)), file=sys.stderr)
    except json.JSONDecodeError as e:
        print("Updater error: ", msgs['json_error'].format(error=str(e)), file=sys.stderr)
    except Exception as e:
        print("Updater error: ", msgs['unexpected_error'].format(error=str(e)), file=sys.stderr)
    
    sys.exit(1)

def main():
    if len(sys.argv) < 3:
        print(msgs['usage'])
        return
    
    version_check_url = sys.argv[1]
    current_version = sys.argv[2]
    save_path = sys.argv[3] if len(sys.argv) > 3 else None
    app_path = sys.argv[4] if len(sys.argv) > 4 else None
    
    check_version_and_update(version_check_url, current_version, save_path, app_path)

if __name__ == "__main__":
    main()