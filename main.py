import cv2
import mediapipe as mp
import numpy as np
import pyttsx3
import tkinter as tk
from tkinter import ttk, PhotoImage
from PIL import Image, ImageTk
import threading
import time

class SignSpeakConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("SignSpeak Converter")
        self.root.geometry("1000x700")
        self.root.resizable(False, False)
        
        # Initialize variables
        self.cap = None
        self.running = False
        self.text_output = ""
        self.speech_enabled = True
        self.current_gesture = "None"
        
        # Initialize mediapipe
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # Initialize text-to-speech
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)
        
        # Setup GUI
        self.setup_gui()
        
    def setup_gui(self):
        # Configure styles
        style = ttk.Style()
        style.configure('TButton', font=('Arial', 12), padding=10)
        style.configure('TLabel', font=('Arial', 12))
        style.configure('TFrame', background='#f0f0f0')
        
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Video frame
        self.video_frame = ttk.Label(main_frame)
        self.video_frame.grid(row=0, column=0, columnspan=3, padx=5, pady=5)
        
        # Text display
        self.text_display = tk.Text(
            main_frame, 
            height=8, 
            width=60, 
            font=('Arial', 14),
            wrap=tk.WORD
        )
        self.text_display.grid(row=1, column=0, columnspan=3, pady=10)
        
        # Gesture label
        self.gesture_label = ttk.Label(
            main_frame, 
            text="Current Gesture: None", 
            font=('Arial', 14, 'bold')
        )
        self.gesture_label.grid(row=2, column=0, columnspan=3, pady=5)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=10)
        
        # Control buttons
        self.start_btn = ttk.Button(
            button_frame, 
            text="Start", 
            command=self.start_capture
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(
            button_frame, 
            text="Stop", 
            command=self.stop_capture,
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_btn = ttk.Button(
            button_frame, 
            text="Clear Text", 
            command=self.clear_text
        )
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        self.speak_btn = ttk.Button(
            button_frame, 
            text="Speak Text", 
            command=self.speak_text
        )
        self.speak_btn.pack(side=tk.LEFT, padx=5)
        
        self.toggle_speech_btn = ttk.Button(
            button_frame, 
            text="Toggle Speech (ON)", 
            command=self.toggle_speech
        )
        self.toggle_speech_btn.pack(side=tk.LEFT, padx=5)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(
            main_frame, 
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_bar.grid(row=4, column=0, columnspan=3, sticky=tk.EW)
        
    def start_capture(self):
        if not self.running:
            self.cap = cv2.VideoCapture(0)
            self.running = True
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.status_var.set("Capturing...")
            self.update_video()
    
    def stop_capture(self):
        if self.running:
            self.running = False
            if self.cap:
                self.cap.release()
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.status_var.set("Stopped")
    
    def clear_text(self):
        self.text_output = ""
        self.text_display.delete(1.0, tk.END)
        self.status_var.set("Text cleared")
    
    def speak_text(self):
        if self.text_output.strip():
            self.engine.say(self.text_output)
            self.engine.runAndWait()
            self.status_var.set("Speaking text...")
        else:
            self.status_var.set("No text to speak")
    
    def toggle_speech(self):
        self.speech_enabled = not self.speech_enabled
        state = "ON" if self.speech_enabled else "OFF"
        self.toggle_speech_btn.config(text=f"Toggle Speech ({state})")
        self.status_var.set(f"Speech output {state}")
    
    def update_video(self):
        if self.running:
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.flip(frame, 1)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Process hand landmarks
                results = self.hands.process(rgb_frame)
                
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        self.mp_draw.draw_landmarks(
                            frame, 
                            hand_landmarks, 
                            self.mp_hands.HAND_CONNECTIONS
                        )
                        
                        # Get hand landmarks
                        landmarks = []
                        for landmark in hand_landmarks.landmark:
                            landmarks.append([landmark.x, landmark.y, landmark.z])
                        
                        # Simple gesture recognition (you can expand this)
                        self.detect_gesture(landmarks)
                
                # Convert to PhotoImage for Tkinter
                img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(img)
                img = ImageTk.PhotoImage(image=img)
                
                self.video_frame.configure(image=img)
                self.video_frame.image = img
                
                # Update gesture label
                self.gesture_label.config(text=f"Current Gesture: {self.current_gesture}")
                
                # Schedule next update
                self.root.after(10, self.update_video)
            else:
                self.stop_capture()
    
    def detect_gesture(self, landmarks):
        # Simple gesture detection based on finger positions
        # Thumb (landmark 4) and index finger (landmark 8)
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        
        # Calculate distance between thumb and index finger
        distance = np.sqrt(
            (thumb_tip[0] - index_tip[0])**2 + 
            (thumb_tip[1] - index_tip[1])**2
        )
        
        # Detect gestures (you can customize these thresholds)
        if distance < 0.05:
            self.current_gesture = "A"
            self.add_to_output("A")
        elif distance < 0.1:
            self.current_gesture = "B"
            self.add_to_output("B")
        elif distance < 0.15:
            self.current_gesture = "C"
            self.add_to_output("C")
        else:
            self.current_gesture = "None"
    
    def add_to_output(self, char):
        if self.text_output.endswith(char) and len(self.text_output) > 0:
            return  # Avoid duplicate characters
        
        self.text_output += char
        self.text_display.insert(tk.END, char)
        self.text_display.see(tk.END)
        
        if self.speech_enabled:
            self.engine.say(char)
            self.engine.runAndWait()
        
        self.status_var.set(f"Added '{char}' to output")
    
    def on_closing(self):
        self.stop_capture()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = SignSpeakConverter(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()