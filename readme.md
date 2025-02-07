# Windows Program Self-Updater

A lightweight auto-update solution for Windows applications, supporting both MSI and EXE installers. This tool provides a user-friendly update experience with progress tracking and multilingual support (English/Korean).

## Features

- Version check against a remote server
- Automatic download with progress bar
- Support for both MSI and EXE installers
- Clean installation process with automatic cleanup
- Multilingual support (English/Korean)
- Automatic application restart after update
- User-friendly error handling

## Update Process Flow

1. Main application launches updater.exe with 4 arguments:
   - Version check URL
   - Current version
   - Download save path
   - Application path

2. Updater checks version:
   - Downloads version.json from server
   - Compares current version with latest version

3. If update available:
   - Shows update confirmation dialog with version information
   - User can accept or decline

4. If user accepts update:
   - Shows download progress window
   - Downloads installer to specified save path
   - Shows progress bar and allows cancellation

5. After successful download:
   - Creates a batch script for installation
   - Launches the batch script
   - Exits updater with code 0 (signals main app to close)

6. Batch script performs:
   - Runs the installer (MSI or EXE)
   - Deletes the downloaded installer
   - Attempts to restart application from specified path
   - If app path changed: Shows message to start manually
   - Deletes itself

7. If no update or user cancels:
   - Exits updater with code 1 (main app continues running)

## Server Configuration

### Version Check JSON

Create a JSON file on your server (e.g., `version.json`) with the following structure:

```json
{
    "latest-version": "4.0.0",
    "download-url": "https://your-server.com/downloads/YourApp_4.0.0.msi"
}
```

- `latest-version`: The newest version number (follows semantic versioning)
- `download-url`: Direct download URL for the installer (supports both .msi and .exe)

### Server Requirements

1. Host the version check JSON file at a publicly accessible URL
2. Host your installer files (MSI/EXE) at a publicly accessible URL
3. Ensure HTTPS support for secure downloads
4. Update the JSON file whenever a new version is released

## Usage

### Basic Command Line Usage

```bash
updater.exe <version_check_url> <current_version> [save_path] [app_path]
```

Parameters:
- `version_check_url`: URL to your version.json file
- `current_version`: Current version of the application
- `save_path` (optional): Path where the installer will be downloaded
- `app_path` (optional): Path to restart the application after update

### Integration Example (C++)

```cpp
std::string versionCheck = "https://your-server.com/version.json";
std::string currentVersion = "3.0.0";
std::string savePath = "C:\\ProgramData\\YourApp\\Updates";
std::string appPath = "C:\\Program Files\\YourApp\\YourApp.exe";

// Construct command
std::string cmd = "updater.exe \"" + versionCheck + "\" \"" + 
                  currentVersion + "\" \"" + savePath + "\" \"" + 
                  appPath + "\"";

// Execute updater
STARTUPINFOA si = {sizeof(si)};
PROCESS_INFORMATION pi;
CreateProcessA(NULL, cmd.data(), NULL, NULL, FALSE, 0, NULL, NULL, &si, &pi);

// Wait for updater to finish and check result
WaitForSingleObject(pi.hProcess, INFINITE);
DWORD exitCode;
GetExitCodeProcess(pi.hProcess, &exitCode);

// Exit application if update was downloaded (exitCode == 0)
if (exitCode == 0) {
    // Clean up and exit your application
    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);
    ExitProcess(0);
}
```

### Exit Codes

- `0`: Update was downloaded and installation started
- `1`: No update available or update was cancelled

## Build from Source

1. Install required Python packages:
```bash
pip install requests packaging tk
```

2. Create executable using PyInstaller:
```bash
pip install pyinstaller
pyinstaller --onefile updater.py
```

## Important Notes

### Permissions and Paths

- The `save_path` must be writable without administrator privileges. If the path requires elevated permissions, the updater may fail silently.
  ```cpp
  // Recommended: Use AppData or similar user-writable locations
  std::string savePath = "%APPDATA%\\YourApp\\Updates";  // Good
  std::string savePath = "C:\\Program Files\\YourApp\\Updates";  // Bad (requires admin rights)
  ```

### Application Restart Behavior

- If your installer allows users to change the installation directory, the automatic restart feature (`app_path`) will not work if the user installs to a different location.
  ```cpp
  // Only use app_path if you:
  // 1. Don't allow installation path changes, or
  // 2. Can predict/detect the new installation path
  std::string appPath = "C:\\Program Files\\YourApp\\YourApp.exe";  // May fail if user changes install location
  ```

### Best Practices for Handling These Limitations

1. Save Path Selection:
   - Always use user-writable locations for `save_path`
   - Consider using environment variables for dynamic path resolution:
     ```cpp
     char appData[MAX_PATH];
     SHGetFolderPathA(NULL, CSIDL_APPDATA, NULL, 0, appData);
     std::string savePath = std::string(appData) + "\\YourApp\\Updates";
     ```

2. Application Restart:
   - If you allow custom installation paths:
     - Consider storing the installation path in registry/config
     - Skip the automatic restart and inform users to start manually
     - Or implement a path detection mechanism
   - If you use fixed installation paths:
     - Document the limitation in your installer
     - Consider disabling path customization

[Rest of the document remains the same...]

## License

MIT License
