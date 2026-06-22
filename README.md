# 🍅 Productivity Tomato (Fomi)

A privacy-first, locally-run productivity tool that lives silently in your Windows system tray, monitors your workspace, and utilizes **Edge AI** to detect non-productive distractions. When you wander off-task, it overlays an aggressive tomato splash on your screen paired with dynamic psychological interventions to get you back to work!

---

## ✨ Features

* **🧠 100% Local Edge AI Processing:** Uses PyTorch (`torch`) and Hugging Face `transformers` to run OpenAI's `CLIP` vision model completely offline on your own hardware. Your screen data never leaves your machine!
* **📭 Silent Tray Operation:** Boots silently into the Windows system tray (`pystray`), taking up no taskbar space and avoiding interruptions until necessary.
* **💤 Lazy Browser Activation:** The tracking engine stays dormant until you explicitly focus on a web browser window. It then smoothly initializes its onboarding wizard.
* **📋 Smart Single-Instance Protection:** Built-in system-wide Windows Mutex tracking detects if the app is already running in the background. If you attempt to open it again, it cleanly prompts you with an interface option to terminate the active background instance.
* **🎨 Dynamic Text Intervention Engine:** Analyzes window titles and generates customized, psychological guilt-trips tailored specifically to your active role, distraction target, and current work session mission. (in-progress)

---

## 🛠️ Prerequisites

* **OS:** Windows 10 or 11 (uses native `win32` window handles)
* **Python Version:** Python 3.8 to 3.11 (Recommended)

---

## 🚀 Getting Started (Installation & Setup)

### 1. Clone or Download the Project
Open your command prompt or terminal and move to your working directory:

    git clone https://github.com/YourUsername/productivity-tomato.git
    cd productivity-tomato

### 2. Set Up a Virtual Environment (Highly Recommended)
Create an isolated environment to prevent library dependency conflicts on your system:

    python -m venv venv

Activate the environment:
* **Command Prompt:** venv\Scripts\activate.bat
* **PowerShell:** .\venv\Scripts\Activate.ps1

### 3. Install the Required Libraries
Install the core application dependencies, including the local AI math frameworks, Windows automation handlers, and system tray tools:

    pip install torch transformers Pillow customtkinter pywin32 pystray

### 4. Run the Application
Launch the main script:

    python tracker.py

> ⚠️ **Important Note on First Run:** Because this application uses Edge AI to prioritize data privacy, it must download the vision model weights (`openai/clip-vit-base-patch32`, approx. 600MB) from Hugging Face directly to your machine's system cache. **The very first launch will take a few minutes to complete.** Future executions will happen instantly and run 100% offline.

---

## 💻 Building a Standalone Executable (.exe)

If you want to compile this program into a portable Windows executable folder (`.exe`) to distribute or attach to a GitHub Release, use **PyInstaller**.

### 1. Install PyInstaller
Ensure PyInstaller is available inside your active virtual environment:

    pip install pyinstaller

### 2. Clean Compilation via Terminal
Run the following compilation script. 

*Note: We purposefully use the default directory mode (`--onedir`) instead of a single file (`--onefile`). Because local machine learning models are massive, an unpacked directory ensures the application loads instantly, whereas a single compressed file would add an annoying 30-second decompression delay on every single boot.*

    pyinstaller --noconsole --name="Fomi-Productivity-Tomato" --add-data "splat.png;." tracker.py

#### Flag breakdown:
* `--noconsole`: Hides any underlying black terminal windows, allowing the program to stay hidden in the background.
* `--name`: Titles your compiled output executable.
* `--add-data "splat.png;."`: Embeds your structural tomato splash image asset right into the program directory.

### 3. Distribution & Sharing
1. Once compilation finishes, navigate into the newly generated `dist/` directory.
2. Inside, open the `Fomi-Productivity-Tomato` folder.
3. Ensure your `splat.png` asset is located inside this folder right next to your newly created `Fomi-Productivity-Tomato.exe`.
4. Right-click the entire `Fomi-Productivity-Tomato` folder and click **Compress to ZIP file**. You can now upload this clean archive directly onto your GitHub Releases dashboard!

---

## 🔒 Local Architecture & File Management

The application creates and manages a few small system utility files inside your project directory to sustain state management:
* `fomi_config.json`: Stores user configurations (roles, goals, blocklists, and allowlists) safely across computer restarts so you don't have to fill out the wizard every single time.
* `fomi.pid`: Automatically tracks the active operating system Process ID to manage automated closures and clean window instance replacement.
* `fomi_vision.jpg`: A temporary, rotating snapshot container utilized exclusively by the local CLIP model for window evaluations. It is continuously overwritten locally and never saved or transmitted online.
