import cv2
from cvzone.HandTrackingModule import HandDetector
from time import sleep, time
import numpy as np
import cvzone
from pynput.keyboard import Controller, Key

# Camera Setup
cap = cv2.VideoCapture(0)
cap.set(3, 1280)
cap.set(4, 720)

# Hand Detector - increased confidence for better detection
detector = HandDetector(detectionCon=0.9, maxHands=1)

# Modern Keyboard Layout with improved aesthetics
keys = [["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "⌫"],
        ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "⏎"],
        ["A", "S", "D", "F", "G", "H", "J", "K", "L", ";"],
        ["Z", "X", "C", "V", "B", "N", "M", ",", ".", "/"],
        ["CTRL", "ALT", "SPACE", "←", "↑", "↓", "→"]]

finalText = ""
keyboard = Controller()

# Modern Color definitions - sleek and futuristic
DARK_BG = (40, 44, 52)      # Dark background
KEY_DARK = (59, 66, 82)     # Dark key color
KEY_LIGHT = (97, 110, 136)  # Light key color (hover)
KEY_PRESS = (66, 99, 235)   # Pressed key - vibrant blue
KEY_BORDER = (75, 85, 99)   # Key border

# Text colors
WHITE = (255, 255, 255)     # White text
BRIGHT_TEXT = (224, 240, 255)  # Bright text
LIGHT_TEXT = (187, 198, 209)   # Light gray text

# Status colors
GREEN = (0, 230, 118)       # Success green
RED = (66, 66, 230)         # Alert red (in BGR)
YELLOW = (20, 195, 235)     # Warning yellow (in BGR)
ACCENT = (232, 150, 77)     # Accent color - orange/teal

# Create a cool gradient function for modern keys
def get_key_gradient(img, x, y, w, h, color1, color2, vertical=True):
    # Create a gradient for keys
    if vertical:
        for i in range(h):
            blend_factor = i/h
            blended = [int(color1[j] * (1-blend_factor) + color2[j] * blend_factor) for j in range(3)]
            cv2.line(img, (x, y+i), (x+w, y+i), blended, 1)
    else:
        for i in range(w):
            blend_factor = i/w
            blended = [int(color1[j] * (1-blend_factor) + color2[j] * blend_factor) for j in range(3)]
            cv2.line(img, (x+i, y), (x+i, y+h), blended, 1)
    return img

# Pinch detection parameters - stricter requirements
VERTICAL_THRESHOLD = 40     # Maximum vertical distance for pinch detection
PINCH_THRESHOLD = 45        # Maximum Euclidean distance for pinch detection
HOLD_FRAMES = 5             # Number of frames a pinch must be stable before registering
current_pinch_frames = 0    # Counter for stable pinch frames
last_pinch_time = 0         # Time of last successful pinch

# Debounce system - stores the last time each key was pressed
key_cooldown = {}           # Dictionary to track key press cooldown
KEY_COOLDOWN_TIME = 0.8     # Seconds to wait before allowing the same key again

# Create particle system for visual feedback
class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.vx = np.random.randint(-5, 6)
        self.vy = np.random.randint(-5, 0)
        self.lifetime = np.random.randint(10, 30)
        
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1
        return self.lifetime > 0
    
    def draw(self, img):
        cv2.circle(img, (int(self.x), int(self.y)), 2, self.color, -1)
        return img

# List to hold active particles
particles = []

# Button Class for Virtual Keys with enhanced visual design
class Button():
    def __init__(self, pos, text, size=[90, 90]):
        self.pos = pos
        self.size = size
        self.text = text
        self.pressed = False  # Track if key is currently pressed
        self.animation = 0  # For press animation
        
    def draw(self, img):
        x, y = self.pos
        w, h = self.size
        
        # Animation effect when key is pressed (3D press effect)
        offset = min(5, self.animation // 2)
        if self.animation > 0:
            self.animation -= 1
            
        # Modern design for all keys
        # Draw key shadow for 3D effect
        shadow_offset = 4 + offset
        if not self.pressed:
            cv2.rectangle(img, (x+shadow_offset, y+shadow_offset), 
                        (x+w+shadow_offset, y+h+shadow_offset), 
                        (20, 20, 20), cv2.FILLED)
        
        # Get gradient background based on key type
        if self.pressed:
            # Pressed state - different gradient
            img = get_key_gradient(img, x+offset, y+offset, w, h, 
                                  KEY_PRESS, (KEY_PRESS[0]//2, KEY_PRESS[1]//2, KEY_PRESS[2]//2), 
                                  vertical=True)
        elif self.text == "SPACE":
            # Spacebar has horizontal gradient
            img = get_key_gradient(img, x, y, w, h, KEY_DARK, KEY_LIGHT, vertical=False)
        elif self.text == "⌫" or self.text == "⏎":
            # Function keys with slight variation
            accent_dark = (ACCENT[0]//2, ACCENT[1]//2, ACCENT[2]//2)
            img = get_key_gradient(img, x, y, w, h, ACCENT, accent_dark, vertical=True)
        elif self.text == "CTRL" or self.text == "ALT":
            # Special function keys
            img = get_key_gradient(img, x, y, w, h, (70, 75, 95), KEY_DARK, vertical=True)
        elif self.text == "←" or self.text == "↑" or self.text == "→" or self.text == "↓":
            # Arrow keys with distinct style
            img = get_key_gradient(img, x, y, w, h, (90, 120, 90), (60, 80, 60), vertical=True)
        else:
            # Standard key gradient
            img = get_key_gradient(img, x, y, w, h, KEY_DARK, KEY_LIGHT, vertical=True)
        
        # Add glossy effect at the top
        gloss_height = h // 4
        if not self.pressed:
            for i in range(gloss_height):
                alpha = 0.4 * (1.0 - i/gloss_height)  # Fading transparency
                cv2.line(img, (x+2, y+2+i), (x+w-2, y+2+i), 
                        [int(255*alpha + c*(1-alpha)) for c in KEY_LIGHT], 1)
        
        # Add rounded corners with modern look
        corner_radius = 15
        cvzone.cornerRect(img, (x+offset, y+offset, w, h), corner_radius, rt=0, 
                         colorC=KEY_BORDER, colorR=KEY_BORDER)
        
        # Text color changes when pressed
        text_color = WHITE if self.pressed else BRIGHT_TEXT
        
        # Special cases for different key types
        if self.text == "SPACE":
            # Modern spacebar with subtle text and icon
            cv2.line(img, (x+w//2-50, y+h//2), (x+w//2+50, y+h//2), text_color, 3)
            cv2.putText(img, "SPACE", (x + w//2 - 60, y + h//2 + 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (text_color[0]//2, text_color[1]//2, text_color[2]//2), 2)
        elif self.text == "⌫":
            # Backspace button with improved design - clean left arrow
            arrow_start = (x + w - 25 + offset, y + h//2 + offset)
            arrow_end = (x + 25 + offset, y + h//2 + offset)
            # Draw the main arrow
            cv2.arrowedLine(img, arrow_start, arrow_end, text_color, 3, tipLength=0.3)
            # Add a small vertical line at the right to complete the backspace symbol
            cv2.line(img, (x + w - 25 + offset, y + h//2 - 15 + offset), 
                    (x + w - 25 + offset, y + h//2 + 15 + offset), text_color, 3)
        elif self.text == "⏎":
            # Enter key with arrow symbol
            arrow_start = (x + 30 + offset, y + h//2 + offset)
            arrow_end = (x + w - 20 + offset, y + h//2 + offset)
            # Draw horizontal line
            cv2.line(img, (x + 30 + offset, y + h//2 - 15 + offset), 
                    (x + 30 + offset, y + h//2 + offset), text_color, 3)
            # Draw the return arrow
            cv2.arrowedLine(img, arrow_start, arrow_end, text_color, 3, tipLength=0.3)
        elif self.text == "←" or self.text == "↑" or self.text == "→" or self.text == "↓":
            # Arrow keys centered with bright text
            text_size = cv2.getTextSize(self.text, cv2.FONT_HERSHEY_PLAIN, 4, 4)[0]
            text_x = x + offset + (w - text_size[0])//2
            text_y = y + offset + h//2 + 15
            cv2.putText(img, self.text, (text_x, text_y), 
                       cv2.FONT_HERSHEY_PLAIN, 4, text_color, 4)
        elif self.text == "CTRL" or self.text == "ALT":
            # Function keys with smaller font
            text_size = cv2.getTextSize(self.text, cv2.FONT_HERSHEY_PLAIN, 2, 2)[0]
            text_x = x + offset + (w - text_size[0])//2
            text_y = y + offset + h//2 + 8
            cv2.putText(img, self.text, (text_x, text_y), 
                       cv2.FONT_HERSHEY_PLAIN, 2, text_color, 2)
        else:
            # Standard keys with better centering and modern font
            text_size = cv2.getTextSize(self.text, cv2.FONT_HERSHEY_PLAIN, 4, 4)[0]
            text_x = x + offset + (w - text_size[0])//2
            text_y = y + offset + h//2 + 15
            cv2.putText(img, self.text, (text_x, text_y), 
                       cv2.FONT_HERSHEY_PLAIN, 4, text_color, 4)
            
            # Add a subtle highlight under each letter for 3D effect
            if not self.pressed:
                cv2.putText(img, self.text, (text_x+1, text_y+1), 
                          cv2.FONT_HERSHEY_PLAIN, 4, (30, 30, 30), 1)
        
        return img

# Create modern ergonomic keyboard layout
buttonList = []

# Create a curved/ergonomic keyboard layout
# Each row will have a slight arc for a more natural finger position
row_offsets = [15, 30, 45, 35, 0]  # Pixel offsets for each row
row_heights = [50, 150, 250, 350, 450]  # Y positions

for i in range(len(keys)):
    row_offset = row_offsets[i]  # Get offset for this row
    y_pos = row_heights[i]
    
    # Calculate key width based on available space and number of keys in row
    total_keys = len(keys[i])
    key_width = 90  # Default key width
    key_spacing = 10  # Space between keys
    
    # Calculate starting position to center the row
    if i == 4:  # Special row with spacebar
        # Distribute keys on bottom row with spacebar
        x_positions = []
        widths = []
        
        # Calculate widths for each key in bottom row
        for k, key in enumerate(keys[i]):
            if key == "SPACE":
                widths.append(400)  # Spacebar width
            elif key == "CTRL" or key == "ALT":
                widths.append(120)  # Function key width
            else:
                widths.append(90)  # Arrow key width
                
        # Calculate total row width
        total_row_width = sum(widths) + ((len(widths)-1) * key_spacing)
        
        # Start position for first key
        x_start = (1280 - total_row_width) // 2
        
        # Place each key
        x_pos = x_start
        for k, key in enumerate(keys[i]):
            buttonList.append(Button([x_pos, y_pos], key, size=[widths[k], 90]))
            x_pos += widths[k] + key_spacing
    else:
        # Center the row horizontally for normal rows
        total_row_width = (total_keys * key_width) + ((total_keys-1) * key_spacing)
        x_start = (1280 - total_row_width) // 2 + row_offset
        
        # Create keys for this row
        for j, key in enumerate(keys[i]):
            x_pos = x_start + (j * (key_width + key_spacing))
            
            # Apply different visual styles based on key type
            if key == "⌫":
                # Backspace key - larger and distinctive
                buttonList.append(Button([x_pos-10, y_pos], key, size=[130, 95]))
            elif key == "⏎":
                # Enter key - larger and distinctive
                buttonList.append(Button([x_pos-10, y_pos], key, size=[130, 95]))
            else:
                # Standard keys with consistent modern look
                buttonList.append(Button([x_pos, y_pos], key, size=[95, 95]))

# Main Loop
while True:
    # Create dark modern background
    img = np.ones((720, 1280, 3), np.uint8) * DARK_BG  # Dark background
    
    # Get image from camera
    success, camera_img = cap.read()
    if not success:
        print("Failed to grab frame")
        continue
        
    # Flip the image horizontally for a more natural interaction
    camera_img = cv2.flip(camera_img, 1)
    
    # Make camera feed smaller and position in corner
    camera_h, camera_w = 180, 240
    camera_img_resized = cv2.resize(camera_img, (camera_w, camera_h))
    
    # Place camera feed in top right corner with border
    img[20:20+camera_h, 1280-20-camera_w:1280-20] = camera_img_resized
    cv2.rectangle(img, (1280-20-camera_w-2, 18), (1280-18, 20+camera_h+2), 
                 KEY_BORDER, 2)
    
    # Find hands
    hands, camera_img = detector.findHands(camera_img)
    
    # Draw buttons
    for button in buttonList:
        img = button.draw(img)
    
    # Update and draw particles for visual effects
    for i in range(len(particles)-1, -1, -1):
        if particles[i].update():
            particles[i].draw(img)
        else:
            particles.pop(i)
    
    # Check for hand position
    if hands:
        hand = hands[0]  # First hand
        lmList = hand["lmList"]  # List of 21 landmarks
        
        # Get important landmarks
        thumb_tip = lmList[4]  # Thumb tip
        index_tip = lmList[8]  # Index finger tip
        middle_tip = lmList[12]  # Middle finger tip
        thumb_base = lmList[2]  # Thumb base (near wrist)
        
        # Scale to match display size
        thumb_tip = (thumb_tip[0] * camera_w // camera_img.shape[1], 
                     thumb_tip[1] * camera_h // camera_img.shape[0])
        index_tip = (index_tip[0] * camera_w // camera_img.shape[1], 
                     index_tip[1] * camera_h // camera_img.shape[0])
        thumb_base = (thumb_base[0] * camera_w // camera_img.shape[1], 
                      thumb_base[1] * camera_h // camera_img.shape[0])
        
        # Adjust to full screen coordinates
        thumb_tip = (1280-20-camera_w + thumb_tip[0], 20 + thumb_tip[1])
        index_tip = (1280-20-camera_w + index_tip[0], 20 + index_tip[1])
        thumb_base = (1280-20-camera_w + thumb_base[0], 20 + thumb_base[1])
        
        # Draw circles on fingertips for visual feedback
        cv2.circle(img, (thumb_tip[0], thumb_tip[1]), 10, WHITE, cv2.FILLED)
        cv2.circle(img, (index_tip[0], index_tip[1]), 10, WHITE, cv2.FILLED)
        
        # Calculate distances for pinch detection
        try:
            # Calculate vertical distance between thumb and index finger tips
            vertical_distance = abs(thumb_tip[1] - index_tip[1])
            horizontal_distance = abs(thumb_tip[0] - index_tip[0])
            
            # Calculate euclidean distance for more accuracy
            euclidean_distance = np.sqrt(vertical_distance**2 + horizontal_distance**2)
            
            # Draw line between thumb and index finger with nice visual
            cv2.line(img, (thumb_tip[0], thumb_tip[1]), (index_tip[0], index_tip[1]), 
                    (ACCENT[0], ACCENT[1], ACCENT[2], 150), 3)
            
            # Add visual reference for vertical distance
            midpoint_x = (thumb_tip[0] + index_tip[0]) // 2
            cv2.line(img, (midpoint_x, thumb_tip[1]), (midpoint_x, index_tip[1]), 
                     GREEN, 2)
            
            # Show distance measurements for debugging
            cv2.putText(img, f"V: {int(vertical_distance)}px", (45, 100), 
                        cv2.FONT_HERSHEY_PLAIN, 1.5, LIGHT_TEXT, 2)
            cv2.putText(img, f"D: {int(euclidean_distance)}px", (45, 130), 
                        cv2.FONT_HERSHEY_PLAIN, 1.5, LIGHT_TEXT, 2)
            
            # Check if thumb is raised relative to its base position
            thumb_raised = (thumb_tip[1] < thumb_base[1] - 30)
            
            # Strict pinch detection with multiple conditions:
            # 1. Vertical distance must be small 
            # 2. Euclidean distance must be small
            # 3. Thumb must be raised from base position
            is_pinching = (vertical_distance < VERTICAL_THRESHOLD and 
                           euclidean_distance < PINCH_THRESHOLD and 
                           thumb_raised)
            
            # Visual indicator for pinch detection status
            if is_pinching:
                cv2.putText(img, "PINCHING", (45, 180), 
                        cv2.FONT_HERSHEY_PLAIN, 2, GREEN, 3)
                
                # Only count consecutive pinch frames
                current_pinch_frames += 1
            else:
                # Reset consecutive frame counter if pinch broken
                current_pinch_frames = 0
                
                # Show guidance on what's needed to pinch
                if not thumb_raised:
                    cv2.putText(img, "Raise thumb", (45, 180),
                            cv2.FONT_HERSHEY_PLAIN, 2, RED, 2)
                elif vertical_distance >= VERTICAL_THRESHOLD:
                    cv2.putText(img, "Closer", (45, 180),
                            cv2.FONT_HERSHEY_PLAIN, 2, YELLOW, 2)
        except Exception as e:
            print(f"Error calculating pinch: {e}")
            current_pinch_frames = 0  # Reset on error
        
        # Check for button interaction with index finger
        for button in buttonList:
            x, y = button.pos
            w, h = button.size
            
            # Check if index finger tip is over button
            if x < index_tip[0] < x + w and y < index_tip[1] < y + h:
                current_time = time()
                
                # Check if button is in cooldown
                in_cooldown = False
                if button.text in key_cooldown:
                    time_elapsed = current_time - key_cooldown[button.text]
                    if time_elapsed < KEY_COOLDOWN_TIME:
                        in_cooldown = True
                        
                        # Show cooldown progress bar
                        remaining = KEY_COOLDOWN_TIME - time_elapsed
                        progress = int((remaining / KEY_COOLDOWN_TIME) * w)
                        cv2.rectangle(img, (x, y + h - 5), (x + progress, y + h), RED, cv2.FILLED)
                
                # If pinch is stable and not in cooldown
                if current_pinch_frames >= HOLD_FRAMES and not in_cooldown:
                    # Reset pinch frames to avoid multiple triggers
                    current_pinch_frames = 0
                    
                    # Set cooldown for this key
                    key_cooldown[button.text] = current_time
                    button.pressed = True
                    button.animation = 10  # Start animation
                    
                    # Create particle effect
                    for _ in range(20):
                        particles.append(Particle(x + w//2, y + h//2, 
                                                (KEY_PRESS[0], KEY_PRESS[1], KEY_PRESS[2])))
                    
                    # Handle different key types
                    if button.text == "⌫":  # Backspace key
                        try:
                            # First attempt with regular backspace
                            keyboard.press(Key.backspace)
                            sleep(0.03)  # Small delay for reliable operation
                            keyboard.release(Key.backspace)
                            print("Backspace pressed")
                        except Exception as e:
                            print(f"Backspace error: {e}")
                            try:
                                # Try alternate method
                                keyboard.type('\b')
                            except:
                                pass
                                
                        # Always update display text
                        if len(finalText) > 0:
                            finalText = finalText[:-1]
                            
                    elif button.text == "SPACE":
                        # Space handling - more reliable approach
                        try:
                            # Try multiple approaches to ensure space works
                            keyboard.press(Key.space)
                            sleep(0.05)  # Brief delay
                            keyboard.release(Key.space)
                            print("Space pressed")
                        except Exception as e:
                            print(f"Space error: {e}")
                            try:
                                # Fallback method
                                keyboard.type(" ")
                            except:
                                pass
                                
                        finalText += " "
                        
                    elif button.text == "⏎":
                        try:
                            keyboard.press(Key.enter)
                            sleep(0.05)
                            keyboard.release(Key.enter)
                            print("ENTER pressed")
                        except Exception as e:
                            print(f"ENTER error: {e}")
                        finalText += "\n" # Visual representation in text box
                        
                    elif button.text == "↑":
                        try:
                            keyboard.press(Key.up)
                            sleep(0.05)
                            keyboard.release(Key.up)
                            print("UP arrow pressed")
                        except Exception as e:
                            print(f"UP arrow error: {e}")
                            
                    elif button.text == "↓":
                        try:
                            keyboard.press(Key.down)
                            sleep(0.05)
                            keyboard.release(Key.down)
                            print("DOWN arrow pressed")
                        except Exception as e:
                            print(f"DOWN arrow error: {e}")
                            
                    elif button.text == "←":
                        try:
                            keyboard.press(Key.left)
                            sleep(0.05)
                            keyboard.release(Key.left)
                            print("LEFT arrow pressed")
                        except Exception as e:
                            print(f"LEFT arrow error: {e}")
                            
                    elif button.text == "→":
                        try:
                            keyboard.press(Key.right)
                            sleep(0.05)
                            keyboard.release(Key.right)
                            print("RIGHT arrow pressed")
                        except Exception as e:
                            print(f"RIGHT arrow error: {e}")
                            
                    elif button.text == "CTRL":
                        try:
                            keyboard.press(Key.ctrl)
                            sleep(0.05)
                            keyboard.release(Key.ctrl)
                            print("CTRL pressed")
                        except Exception as e:
                            print(f"CTRL error: {e}")
                            
                    elif button.text == "ALT":
                        try:
                            keyboard.press(Key.alt)
                            sleep(0.05)
                            keyboard.release(Key.alt)
                            print("ALT pressed")
                        except Exception as e:
                            print(f"ALT error: {e}")
                    
                    else:
                        # Normal key press - try multiple methods for reliability
                        key_char = button.text.lower()  # Use lowercase for typing
                        
                        try:
                            # First method - type directly
                            keyboard.type(key_char)
                            print(f"Typed key: {key_char}")
                        except Exception as e:
                            print(f"Type error: {e}")
                            
                            # Second method - press and release with delay
                            try:
                                keyboard.press(key_char)
                                sleep(0.05)  # Short delay 
                                keyboard.release(key_char)
                                print(f"Press-release: {key_char}")
                            except Exception as e2:
                                print(f"Press-release error: {e2}")
                                
                        # Update display text regardless of typing success
                        finalText += button.text
                        
                    # Add a brief delay after successful key press
                    sleep(0.1)
                    
                # Show "almost pinching" indicator
                elif 'is_pinching' in locals() and is_pinching:
                    # Show progress bar for pinch hold time
                    hold_progress = int((current_pinch_frames / HOLD_FRAMES) * w)
                    cv2.rectangle(img, (x, y + h - 5), (x + hold_progress, y + h), GREEN, cv2.FILLED)
                    
                # Show hover indicator when finger is over button but not pinching
                elif 'is_pinching' in locals() and not is_pinching and not in_cooldown:
                    cv2.rectangle(img, (x, y + h - 5), (x + w, y + h), YELLOW, cv2.FILLED)
    
    # Create a modern text display area with a futuristic design
    # Drop shadow for text box
    shadow_offset = 8
    cv2.rectangle(img, (50+shadow_offset, 550+shadow_offset), 
                 (1200+shadow_offset, 650+shadow_offset), (20, 20, 20), cv2.FILLED)
                 
    # Main text box with gradient
    img = get_key_gradient(img, 50, 550, 1150, 100, 
                           (KEY_DARK[0]//2, KEY_DARK[1]//2, KEY_DARK[2]//2),
                           KEY_DARK, vertical=False)
    
    # Border with accent color
    cv2.rectangle(img, (50, 550), (1200, 650), ACCENT, 2)
    
    # Add glowing accent corners for futuristic look
    corner_size = 15
    # Top left corner
    cv2.line(img, (50, 550), (50+corner_size, 550), ACCENT, 3)
    cv2.line(img, (50, 550), (50, 550+corner_size), ACCENT, 3)
    # Top right corner
    cv2.line(img, (1200, 550), (1200-corner_size, 550), ACCENT, 3)
    cv2.line(img, (1200, 550), (1200, 550+corner_size), ACCENT, 3)
    # Bottom left corner
    cv2.line(img, (50, 650), (50+corner_size, 650), ACCENT, 3)
    cv2.line(img, (50, 650), (50, 650-corner_size), ACCENT, 3)
    # Bottom right corner
    cv2.line(img, (1200, 650), (1200-corner_size, 650), ACCENT, 3)
    cv2.line(img, (1200, 650), (1200, 650-corner_size), ACCENT, 3)
    
    # Limit text display to fit in the box (show last 40 characters if longer)
    displayText = finalText[-40:] if len(finalText) > 40 else finalText
    
    # Draw the text with better visibility
    cv2.putText(img, displayText, (60, 610),  # Position text in the middle of the box
                cv2.FONT_HERSHEY_SIMPLEX, 1.5, WHITE, 2)
    
    # Add a label for the text box
    cv2.putText(img, "Your Text:", (60, 540), 
                cv2.FONT_HERSHEY_PLAIN, 2, ACCENT, 2)
                
    # Add modern usage instructions with futuristic design
    instruction_y = 20
    cv2.rectangle(img, (20, instruction_y-10), (700, instruction_y+30), (30, 30, 40), cv2.FILLED)
    cv2.rectangle(img, (20, instruction_y-10), (700, instruction_y+30), KEY_BORDER, 1)
    cv2.putText(img, "Place index finger over key & pinch with thumb to type", (30, instruction_y+15), 
                cv2.FONT_HERSHEY_PLAIN, 1.2, LIGHT_TEXT, 2)
    
    # Add quit instruction
    cv2.putText(img, "Press 'q' to quit", (1000, instruction_y+15),
                cv2.FONT_HERSHEY_PLAIN, 1.2, LIGHT_TEXT, 2)
    
    # Show pinch progress indicator as a circular meter
    if current_pinch_frames > 0:
        # Draw circular progress indicator
        center = (60, 220)
        radius = 30
        # Background circle
        cv2.circle(img, center, radius, (40, 40, 50), cv2.FILLED)
        cv2.circle(img, center, radius, KEY_BORDER, 2)
        # Progress arc
        progress = current_pinch_frames / HOLD_FRAMES
        end_angle = int(360 * progress)
        # Draw arc segments to simulate progress
        for angle in range(0, end_angle, 6):
            x1 = int(center[0] + radius * np.cos(np.radians(angle)))
            y1 = int(center[1] + radius * np.sin(np.radians(angle)))
            x2 = int(center[0] + radius * np.cos(np.radians(angle+5)))
            y2 = int(center[1] + radius * np.sin(np.radians(angle+5)))
            cv2.line(img, (x1, y1), (x2, y2), GREEN, 3)
        # Label
        cv2.putText(img, "PINCH", (center[0]-25, center[1]+50), cv2.FONT_HERSHEY_PLAIN, 1.2, LIGHT_TEXT, 2)
    
    # Show image with window name
    cv2.imshow("AI Virtual Keyboard - Modern Edition", img)
    
    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
