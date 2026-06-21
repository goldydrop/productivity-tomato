import win32gui
import win32api
import win32con
import time
from PIL import ImageGrab, Image
import tkinter as tk
import threading

# --- EDGE AI IMPORTS ---
from transformers import CLIPProcessor, CLIPModel
import torch

# --- GLOBAL VARIABLES ---
USER_ROLE = "Student"
USER_GOAL = "Studying Python coding"
ALLOWED_TOOLS = "VS Code, StackOverflow, Google, Command Prompt"
SHOULD_DROP_TOMATO = False 
IS_AI_THINKING = False 
KNOWN_SAFE_WINDOWS = set()         
KNOWN_DISTRACTING_WINDOWS = set()  

# --- DYNAMIC GRACE PERIOD CONFIG ---
BASE_GRACE_PERIOD = 15.0     
VIDEO_GRACE_PERIOD = 3.0     

print("-> Loading Edge AI model locally... (This takes a moment on startup)")
edge_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
edge_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
print("-> Edge AI Loaded! Ready to monitor offline.")

def get_active_window_title():
    window = win32gui.GetForegroundWindow()
    return win32gui.GetWindowText(window)

def take_screenshot():
    try:
        hwnd = win32gui.GetForegroundWindow()
        rect = win32gui.GetWindowRect(hwnd)
        
        if rect[2] - rect[0] > 0 and rect[3] - rect[1] > 0:
            screenshot = ImageGrab.grab(bbox=rect, all_screens=True)
        else:
            screenshot = ImageGrab.grab(all_screens=True)
            
        screenshot.thumbnail((800, 600)) 
        screenshot.save("fomi_vision.jpg")
        
    except Exception as e:
        screenshot = ImageGrab.grab(all_screens=True)
        screenshot.thumbnail((800, 600))
        screenshot.save("fomi_vision.jpg")

def ask_the_ai(window_title):
    global SHOULD_DROP_TOMATO, IS_AI_THINKING, KNOWN_SAFE_WINDOWS, KNOWN_DISTRACTING_WINDOWS
    
    IS_AI_THINKING = True 
    
    try:
        time.sleep(1.5)
        
        if get_active_window_title() != window_title:
            IS_AI_THINKING = False
            return
            
        goal_keywords = [word.lower() for word in USER_GOAL.split() if len(word) > 2]
        goal_keywords.extend(["tutorial", "programming", "course", "lecture", "learn", "documentation"])
        has_study_keyword = any(keyword in window_title.lower() for keyword in goal_keywords)
        
        print(f"-> Analyzing window content: '{window_title}'")
        take_screenshot()
        img = Image.open("fomi_vision.jpg")
        
        categories = [
            "a software development text editor IDE or programming terminal window filled with code lines",
            "a web browser playing a streaming entertainment video or youtube video player container",
            "a video game screen with active gameplay graphics",
            "a social media timeline feed on a website"
        ]
        
        inputs = edge_processor(text=categories, images=img, return_tensors="pt", padding=True)
        with torch.no_grad():
            outputs = edge_model(**inputs)
        
        logits_per_image = outputs.logits_per_image
        probs = logits_per_image.softmax(dim=1).cpu().numpy()[0]
        
        best_match_index = probs.argmax()
        winning_category = categories[best_match_index]
        winning_percentage = probs[best_match_index] * 100
        
        print(f"-> Local AI Result ({winning_percentage:.1f}% match): {winning_category}")
        
        if "video" in winning_category or "game" in winning_category or "social media" in winning_category:
            if has_study_keyword:
                KNOWN_SAFE_WINDOWS.add(window_title)
                print(f"-> AI Override! Educational match. Memorized as SAFE ✅")
            else:
                KNOWN_DISTRACTING_WINDOWS.add(window_title)
                print(f"-> Memorized as DISTRACTING: {window_title}")
        else:
            if "YouTube" in window_title and not has_study_keyword:
                KNOWN_DISTRACTING_WINDOWS.add(window_title)
                print(f"-> Catch Triggered! Prevented bad window capture. Memorized as DISTRACTING 🍅")
            else:
                KNOWN_SAFE_WINDOWS.add(window_title)
                print(f"-> Memorized as SAFE: {window_title}")
            
    except Exception as e:
        print(f"-> ERROR: Local AI execution failed. Details: {e}")
        
    IS_AI_THINKING = False

def show_setup_menu():
    print("Opening Setup Menu...")
    menu = tk.Tk()
    menu.title("Fomi Tracker Setup")
    menu.geometry("400x350")
    
    tk.Label(menu, text="Configure Your Focus Session", font=("Arial", 14, "bold")).pack(pady=10)
    
    tk.Label(menu, text="Your Role (e.g., Student, Developer):").pack()
    role_entry = tk.Entry(menu, width=50)
    role_entry.insert(0, USER_ROLE)
    role_entry.pack(pady=5)
    
    tk.Label(menu, text="What is your current goal?").pack()
    goal_entry = tk.Entry(menu, width=50)
    goal_entry.insert(0, USER_GOAL)
    goal_entry.pack(pady=5)
    
    tk.Label(menu, text="Allowed Tools (comma separated):").pack()
    tools_entry = tk.Entry(menu, width=50)
    tools_entry.insert(0, ALLOWED_TOOLS)
    tools_entry.pack(pady=5)
    
    def start_tracking():
        global USER_ROLE, USER_GOAL, ALLOWED_TOOLS
        USER_ROLE = role_entry.get()
        USER_GOAL = goal_entry.get()
        ALLOWED_TOOLS = tools_entry.get()
        menu.destroy()

    tk.Button(menu, text="Start Tracker", font=("Arial", 12, "bold"), bg="#4CAF50", fg="white", command=start_tracking).pack(pady=20)
    menu.mainloop()

# --- MAIN FLOW ---
show_setup_menu()

print(f"Tracker Started for: {USER_GOAL}!")
current_app = ""
window_start_time = time.time() 

TOMATO_ROOT = None
TOMATO_TIMEOUT = 0

while True:
    new_app = get_active_window_title()
    current_time = time.time()
    
    # --- 1. DETECT WINDOW CHANGE & LOG SMART CACHE ---
    if new_app != current_app and new_app != "":
        current_app = new_app
        window_start_time = current_time 
        
        if current_app in KNOWN_SAFE_WINDOWS:
            print(f"-> Cache Hit: SAFE ✅ ({current_app})")
            
        elif current_app in KNOWN_DISTRACTING_WINDOWS:
            print(f"-> Cache Hit: DISTRACTING 🍅 ({current_app})")
            SHOULD_DROP_TOMATO = True 

    # --- 1.5. THE SELF-HEALING AI TRIGGER ---
    # Constantly check: Are we on an unknown YouTube/Discord page, and is the AI resting?
    # This prevents the app from ever missing a dynamic title change!
    if ("YouTube" in current_app or "Discord" in current_app) and current_app != "":
        if current_app not in KNOWN_SAFE_WINDOWS and current_app not in KNOWN_DISTRACTING_WINDOWS:
            if not IS_AI_THINKING:
                print(f"\nActive Window: {current_app} (Unknown. Triggering background analysis...)")
                threading.Thread(target=ask_the_ai, args=(current_app,)).start() 
    
    # --- 2. DYNAMIC GRACE PERIOD LOGIC ---
    active_grace_period = BASE_GRACE_PERIOD
    
    if "YouTube" in current_app:
        is_clean_home = current_app.strip() == "YouTube" or current_app.strip().startswith("YouTube -")
        is_search_page = "search" in current_app.lower()
        
        if not is_clean_home and not is_search_page:
            active_grace_period = VIDEO_GRACE_PERIOD
            
    time_on_window = current_time - window_start_time
    
    if current_app in KNOWN_DISTRACTING_WINDOWS:
        if time_on_window > active_grace_period:
            SHOULD_DROP_TOMATO = True 
            window_start_time = current_time 
    
    # --- 3. NON-BLOCKING TOMATO SPAWNER ---
    if SHOULD_DROP_TOMATO:
        if TOMATO_ROOT is None:
            print(f"-> Grace period ({active_grace_period}s) expired! Dropping the tomato!")
            TOMATO_ROOT = tk.Tk()
            TOMATO_ROOT.attributes('-topmost', True)
            TOMATO_ROOT.overrideredirect(True)
            TOMATO_ROOT.configure(bg='red')
            
            hwnd = win32gui.GetForegroundWindow()
            monitor = win32api.MonitorFromWindow(hwnd, win32con.MONITOR_DEFAULTTONEAREST)
            monitor_info = win32api.GetMonitorInfo(monitor)
            left, top, right, bottom = monitor_info['Monitor']
            
            monitor_width = right - left
            monitor_height = bottom - top
            window_width = 600
            window_height = 200
            
            x = left + int((monitor_width / 2) - (window_width / 2))
            y = top + int((monitor_height / 2) - (window_height / 2))
            
            TOMATO_ROOT.geometry(f'{window_width}x{window_height}+{x}+{y}')
            label = tk.Label(TOMATO_ROOT, text="🍅 GET BACK TO WORK! 🍅", font=("Arial", 30, "bold"), bg="red", fg="white")
            label.pack(expand=True)
            
            TOMATO_TIMEOUT = current_time + 3.0
        SHOULD_DROP_TOMATO = False 
    
    # --- 4. LIVE INTERFACE POLISHING ---
    if TOMATO_ROOT is not None:
        if current_time > TOMATO_TIMEOUT or (new_app != current_app and new_app not in KNOWN_DISTRACTING_WINDOWS and new_app != ""):
            try:
                TOMATO_ROOT.destroy()
            except:
                pass
            TOMATO_ROOT = None
            print("-> Tomato dismissed!")
        else:
            try:
                TOMATO_ROOT.update() 
            except:
                TOMATO_ROOT = None

    time.sleep(0.1)