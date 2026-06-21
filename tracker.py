import win32gui
import win32api
import win32con
import time
from PIL import ImageGrab, Image, ImageTk
import tkinter as tk
import customtkinter as ctk  
import threading
import json  
import os    
import sys
import random 

# --- EDGE AI IMPORTS ---
from transformers import CLIPProcessor, CLIPModel
import torch

# --- CONFIG MEMORY SETUP ---
CONFIG_FILE = "fomi_config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {}

saved_config = load_config()

# --- GLOBAL VARIABLES ---
USER_ROLE = saved_config.get("role", "Student")
USER_GOAL = saved_config.get("goal", "Studying Python coding")
ALLOWED_TOOLS = saved_config.get("allowed", "VS Code, StackOverflow, Command Prompt, Gemini, Windows PowerShell") 
BLOCK_LIST = saved_config.get("blocked", "Reddit, Twitter, TikTok, Instagram, Facebook")  

SHOULD_DROP_TOMATO = False 
IS_AI_THINKING = False 
KNOWN_SAFE_WINDOWS = set()         
KNOWN_DISTRACTING_WINDOWS = set()  

# --- DYNAMIC GRACE PERIOD CONFIG ---
DEFAULT_GRACE_PERIOD = 3.0  

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
            "a software development text editor IDE, programming terminal, or reading educational documents", 
            "a web browser playing a streaming entertainment video or youtube", 
            "a video game screen with active gameplay graphics", 
            "a social media timeline feed, chat app, shopping website, or casual web browsing" 
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

# --- DYNAMIC TEXT INTERVENTION ENGINE ---
def generate_intervention(role, goal, distraction_window):
    """Generates a dynamic, psychological guilt trip based on user inputs."""
    
    clean_distraction = "that window"
    # List of common browsers we want to ignore
    browsers = ["Google Chrome", "Mozilla Firefox", "Microsoft Edge", "Brave", "Opera", "Safari", "Arc"]
    
    if "-" in distraction_window:
        # Split the title by hyphens and clean up spaces
        parts = [p.strip() for p in distraction_window.split("-")]
        
        # Filter out the browser names from the parts list
        parts = [p for p in parts if not any(b.lower() in p.lower() for b in browsers)]
        
        if parts:
            # The last remaining part is usually the website name (e.g., "YouTube" or "Reddit")
            clean_distraction = parts[-1]
        else:
            # Fallback just in case
            clean_distraction = distraction_window.split("-")[0].strip()
            
    elif distraction_window:
        clean_distraction = distraction_window[:20] + ("..." if len(distraction_window) > 20 else "")

    templates = [
        f"Is looking at {clean_distraction} really helping you with '{goal}'?",
        f"You told me you were a {role} on a mission. Prove it. Close {clean_distraction}.",
        f"Every minute spent on {clean_distraction} is a minute stolen from '{goal}'.",
        f"I see you on {clean_distraction}. Let's get back to the plan: {goal}.",
        f"Your future self who actually finished '{goal}' is begging you to close {clean_distraction}.",
        f"Warning: {clean_distraction} is actively sabotaging your mission to {goal.lower()}.",
        f"A true {role} wouldn't let {clean_distraction} distract them right now.",
        f"Take a deep breath, close {clean_distraction}, and let's get back to {goal}."
    ]
    
    return random.choice(templates)


# --- SMOOTH SCROLLING WIZARD UI ---
def show_setup_menu():
    print("Opening Setup Wizard...")
    
    ctk.set_appearance_mode("Dark")  
    ctk.set_default_color_theme("blue")  
    
    menu = ctk.CTk()
    menu.title("Fomi - Focus Assistant")
    menu.geometry("600x350")
    menu.resizable(False, False)
    
    def on_closing():
        print("-> Setup cancelled. Exiting Fomi entirely.")
        menu.destroy()
        sys.exit(0) 
        
    menu.protocol("WM_DELETE_WINDOW", on_closing)
    
    user_data = {
        "role": USER_ROLE,
        "goal": USER_GOAL,
        "allowed": ALLOWED_TOOLS,
        "blocked": BLOCK_LIST
    }
    
    steps = [
        {"title": "Step 1: Your Identity", "prompt": "What is your role today? (e.g., Student, Developer)", "key": "role", "color": "white"},
        {"title": "Step 2: Your Mission", "prompt": "What is your specific goal for this session?", "key": "goal", "color": "white"},
        {"title": "Step 3: Allowed Tools", "prompt": "What apps/sites are ALLOWED? (comma separated)", "key": "allowed", "color": "white"},
        {"title": "Step 4: Distractions", "prompt": "What triggers an INSTANT tomato? (comma separated)", "key": "blocked", "color": "#FF6B6B"}
    ]
    
    current_step = 0
    is_animating = False
    
    carousel_container = ctk.CTkFrame(master=menu, fg_color="transparent")
    carousel_container.pack(fill="both", expand=True, padx=20, pady=(20, 0))
    
    btn_frame = ctk.CTkFrame(master=menu, fg_color="transparent")
    btn_frame.pack(fill="x", padx=40, pady=20)
    
    step_frames = []
    entries = []
    
    for step in steps:
        frame = ctk.CTkFrame(master=carousel_container)
        
        step_label = ctk.CTkLabel(master=frame, text=step["title"], font=("Roboto", 16, "bold"), text_color="#A0A0A0")
        step_label.pack(pady=(20, 5))
        
        prompt_label = ctk.CTkLabel(master=frame, text=step["prompt"], font=("Roboto", 20), text_color=step["color"])
        prompt_label.pack(pady=(10, 20))
        
        entry_box = ctk.CTkEntry(master=frame, width=500, height=45, font=("Roboto", 16))
        entry_box.insert(0, user_data[step["key"]])
        entry_box.pack(pady=10, padx=20)
        
        step_frames.append(frame)
        entries.append(entry_box)

    step_frames[0].place(relx=0.5, rely=0.5, relwidth=1.0, relheight=1.0, anchor="center")
    
    def slide_frames(out_frame, in_frame, direction):
        nonlocal is_animating
        is_animating = True
        
        steps_count = 25  
        delay = 10        
        
        in_start_x = 1.5 if direction == 1 else -0.5
        out_end_x = -0.5 if direction == 1 else 1.5
        
        in_frame.place(relx=in_start_x, rely=0.5, relwidth=1.0, relheight=1.0, anchor="center")
        
        def animate(i):
            nonlocal is_animating
            if i <= steps_count:
                progress = i / steps_count
                ease = 1 - pow(1 - progress, 3) 
                
                cur_out_x = 0.5 + (out_end_x - 0.5) * ease
                cur_in_x = in_start_x + (0.5 - in_start_x) * ease
                
                out_frame.place(relx=cur_out_x, rely=0.5, relwidth=1.0, relheight=1.0, anchor="center")
                in_frame.place(relx=cur_in_x, rely=0.5, relwidth=1.0, relheight=1.0, anchor="center")
                
                menu.after(delay, animate, i + 1)
            else:
                out_frame.place_forget()
                in_frame.place(relx=0.5, rely=0.5, relwidth=1.0, relheight=1.0, anchor="center")
                entries[current_step].focus()
                is_animating = False
                
        animate(1)

    def update_buttons():
        if current_step == 0:
            back_btn.configure(state="disabled")
        else:
            back_btn.configure(state="normal")
            
        if current_step == len(steps) - 1:
            next_btn.configure(text="Start Tracking", fg_color="#28a745", hover_color="#218838")
        else:
            next_btn.configure(text="Next ➔", fg_color=["#3a7ebf", "#1f538d"], hover_color=["#325882", "#14375e"])

    def go_next(event=None):
        global USER_ROLE, USER_GOAL, ALLOWED_TOOLS, BLOCK_LIST
        nonlocal current_step
        if is_animating: return
        
        current_key = steps[current_step]["key"]
        user_data[current_key] = entries[current_step].get()
        
        if current_step < len(steps) - 1:
            out_frame = step_frames[current_step]
            current_step += 1
            in_frame = step_frames[current_step]
            
            update_buttons()
            slide_frames(out_frame, in_frame, direction=1)
        else:
            USER_ROLE = user_data["role"]
            USER_GOAL = user_data["goal"]
            ALLOWED_TOOLS = user_data["allowed"]
            BLOCK_LIST = user_data["blocked"]
            
            try:
                with open(CONFIG_FILE, 'w') as f:
                    json.dump(user_data, f)
            except Exception as e:
                print(f"-> Failed to save config: {e}")
            
            menu.protocol("WM_DELETE_WINDOW", menu.destroy)
            menu.destroy()

    def go_back(event=None):
        nonlocal current_step
        if is_animating or current_step == 0: return
        
        current_key = steps[current_step]["key"]
        user_data[current_key] = entries[current_step].get()
        
        out_frame = step_frames[current_step]
        current_step -= 1
        in_frame = step_frames[current_step]
        
        update_buttons()
        slide_frames(out_frame, in_frame, direction=-1)
            
    menu.bind('<Return>', lambda event: go_next())

    back_btn = ctk.CTkButton(master=btn_frame, text="⬅ Back", width=100, height=40, font=("Roboto", 14), fg_color="gray", hover_color="#555555", command=go_back)
    back_btn.pack(side="left")
    
    next_btn = ctk.CTkButton(master=btn_frame, text="Next ➔", width=140, height=40, font=("Roboto", 16, "bold"), command=go_next)
    next_btn.pack(side="right")

    update_buttons()
    entries[0].focus()
    menu.mainloop()

# --- MAIN FLOW ---
show_setup_menu()

print(f"Tracker Started for: {USER_GOAL}!")
current_app = ""
window_start_time = time.time() 

TOMATO_ROOT = None
TOMATO_TIMEOUT = 0

blocked_keywords = [b.strip().lower() for b in BLOCK_LIST.split(",") if b.strip()]
allowed_keywords = [a.strip().lower() for a in ALLOWED_TOOLS.split(",") if a.strip()]

while True:
    new_app = get_active_window_title()
    current_time = time.time()
    
    if new_app != current_app and new_app != "":
        current_app = new_app
        window_start_time = current_time 
        
        is_safe_harbor = current_app.lower().startswith("new tab") or current_app.lower() == "google - google chrome" or current_app.strip().lower() == "google"
        is_explicitly_allowed = any(good_word in current_app.lower() for good_word in allowed_keywords)
        is_hard_blocked = any(bad_word in current_app.lower() for bad_word in blocked_keywords)
        
        if is_explicitly_allowed or is_safe_harbor:
            if current_app not in KNOWN_SAFE_WINDOWS:
                KNOWN_SAFE_WINDOWS.add(current_app)
                print(f"-> 🛡️ ALLOWLIST/SAFE HARBOR HIT: {current_app}. Bypassing AI!")
                
        elif is_hard_blocked:
            if current_app not in KNOWN_DISTRACTING_WINDOWS:
                KNOWN_DISTRACTING_WINDOWS.add(current_app)
                print(f"-> 🛑 BLOCKLIST HIT: {current_app}. Bypassing AI!")
            SHOULD_DROP_TOMATO = True
            
        elif current_app in KNOWN_SAFE_WINDOWS:
            print(f"-> Cache Hit: SAFE ✅ ({current_app})")
            
        elif current_app in KNOWN_DISTRACTING_WINDOWS:
            print(f"-> Cache Hit: DISTRACTING 🍅 ({current_app})")
            SHOULD_DROP_TOMATO = True 

    if current_app != "":
        is_safe_harbor = current_app.lower().startswith("new tab") or current_app.lower() == "google - google chrome" or current_app.strip().lower() == "google"
        is_explicitly_allowed = any(good_word in current_app.lower() for good_word in allowed_keywords)
        is_hard_blocked = any(bad_word in current_app.lower() for bad_word in blocked_keywords)
        
        if not is_explicitly_allowed and not is_safe_harbor and not is_hard_blocked and current_app not in KNOWN_SAFE_WINDOWS and current_app not in KNOWN_DISTRACTING_WINDOWS:
            if not IS_AI_THINKING:
                print(f"\nActive Window: {current_app} (Unknown. Triggering background analysis...)")
                threading.Thread(target=ask_the_ai, args=(current_app,)).start() 
    
    # --- DYNAMIC GRACE PERIOD LOGIC ---
    active_grace_period = DEFAULT_GRACE_PERIOD
    
    is_currently_blocked = any(bad_word in current_app.lower() for bad_word in blocked_keywords)
    is_currently_allowed = any(good_word in current_app.lower() for good_word in allowed_keywords)
    
    if is_currently_blocked and not is_currently_allowed:
        active_grace_period = 0.0
            
    time_on_window = current_time - window_start_time
    
    if current_app in KNOWN_DISTRACTING_WINDOWS or (is_currently_blocked and not is_currently_allowed):
        if time_on_window >= active_grace_period:
            SHOULD_DROP_TOMATO = True 
            window_start_time = current_time 
    
   # --- MODERN NON-BLOCKING TOMATO SPAWNER WITH AI INTERVENTION ---
    if SHOULD_DROP_TOMATO:
        if TOMATO_ROOT is None:
            print(f"-> Timer expired ({active_grace_period}s)! Dropping the tomato!")
            
            # Use standard TK for transparent background shapes
            TOMATO_ROOT = tk.Tk()
            TOMATO_ROOT.attributes('-topmost', True)
            TOMATO_ROOT.overrideredirect(True) 
            
            # The Magic Trick: Make black completely invisible!
            transparent_color = '#000000'
            TOMATO_ROOT.attributes('-transparentcolor', transparent_color)
            TOMATO_ROOT.configure(bg=transparent_color)
            
            hwnd = win32gui.GetForegroundWindow()
            monitor = win32api.MonitorFromWindow(hwnd, win32con.MONITOR_DEFAULTTONEAREST)
            monitor_info = win32api.GetMonitorInfo(monitor)
            left, top, right, bottom = monitor_info['Monitor']
            
            # --- SCALED UP DIMENSIONS ---
            monitor_width = right - left
            monitor_height = bottom - top
            window_width = 1200   # Scaled up from 800
            window_height = 900   # Scaled up from 600
            
            x = left + int((monitor_width / 2) - (window_width / 2))
            y = top + int((monitor_height / 2) - (window_height / 2))
            
            TOMATO_ROOT.geometry(f'{window_width}x{window_height}+{x}+{y}')
            
            # Use a Canvas to layer the image and text without solid backgrounds
            canvas = tk.Canvas(TOMATO_ROOT, width=window_width, height=window_height, bg=transparent_color, highlightthickness=0)
            canvas.pack()
            
            # Try to load the splat image, fallback to a red circle if missing
            try:
                # We use LANCZOS for high-quality resizing
                splat_img = Image.open("splat.png").convert("RGBA").resize((window_width, window_height), Image.Resampling.LANCZOS)
                TOMATO_ROOT.splat_photo = ImageTk.PhotoImage(splat_img) 
                canvas.create_image(window_width/2, window_height/2, image=TOMATO_ROOT.splat_photo)
            except Exception as e:
                print("-> Could not load splat.png, drawing a giant tomato circle instead.")
                canvas.create_oval(50, 50, window_width-50, window_height-50, fill="#B22222", outline="#FF6347", width=5)
            
            # Generate the dynamic AI guilttrip
            dynamic_intervention = generate_intervention(USER_ROLE, USER_GOAL, current_app)
            
            # Subtracting a larger number (-45) to actually push the whole block further to the LEFT
            center_x = (window_width / 2) - 57
            
            # --- REAL ALIGNMENT FIX ---
            
            # Header Text (Unchanged)
            canvas.create_text(center_x, window_height/2 - 80, text="🍅   GET BACK TO WORK!   🍅", font=("Roboto", 24, "bold"), fill="white", justify="center")
            
            # Body Text: Widened the wrap (from 270 to 340) so the text breathes and wraps more naturally!
            canvas.create_text(center_x, window_height/2 + 80, text=dynamic_intervention, font=("Roboto", 20, "italic"), fill="#FFCCCB", width=340, justify="center")
            
            TOMATO_TIMEOUT = current_time + 3.0
        SHOULD_DROP_TOMATO = False
    
    # --- LIVE INTERFACE POLISHING ---
    if TOMATO_ROOT is not None:
        if current_time > TOMATO_TIMEOUT or (new_app != current_app and new_app not in KNOWN_DISTRACTING_WINDOWS and new_app != "" and not any(b in new_app.lower() for b in blocked_keywords)):
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