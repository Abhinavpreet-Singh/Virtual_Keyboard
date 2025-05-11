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

# Keyboard Layout - Improved, straight layout with all necessary keys
keys = [["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "⌫"],
        ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "'"],
        ["A", "S", "D", "F", "G", "H", "J", "K", "L", ";",],
        ["Z", "X", "C", "V", "B", "N", "M", ",", ".", "/", ],
        ["SPACE",]]  # Complete keyboard layout with function keys

finalText = ""
keyboard = Controller()

# Color definitions - Modern color palette
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

# Button Class for Virtual Keys
class Button():
    def __init__(self, pos, text, size=[85, 85]):
        self.pos = pos
        self.size = size
        self.text = text
        self.pressed = False  # Track if key is currently pressed

# Drawing Function - Modern Design
def drawAll(img, buttonList):
    for button in buttonList:
        x, y = button.pos
        w, h = button.size
        
        # Modern design for all keys
        # Draw key shadow for 3D effect
        shadow_offset = 4
        cv2.rectangle(img, (x+shadow_offset, y+shadow_offset), 
                     (x+w+shadow_offset, y+h+shadow_offset), 
                     (20, 20, 20), cv2.FILLED)
        
        # Get gradient background based on key type
        if button.text == "SPACE":
            # Spacebar has horizontal gradient
            img = get_key_gradient(img, x, y, w, h, KEY_DARK, KEY_LIGHT, vertical=False)
        elif button.text == "⌫" or button.text == "⏎":
            # Function keys with slight variation
            accent_dark = (KEY_PRESS[0]//2, KEY_PRESS[1]//2, KEY_PRESS[2]//2)
            img = get_key_gradient(img, x, y, w, h, accent_dark, KEY_DARK, vertical=True)
        else:
            # Standard key gradient
            img = get_key_gradient(img, x, y, w, h, KEY_DARK, KEY_LIGHT, vertical=True)
        
        # Add glossy effect at the top
        gloss_height = h // 4
        for i in range(gloss_height):
            alpha = 0.4 * (1.0 - i/gloss_height)  # Fading transparency
            cv2.line(img, (x+2, y+2+i), (x+w-2, y+2+i), 
                    [int(255*alpha + c*(1-alpha)) for c in KEY_LIGHT], 1)
        
        # Add rounded corners with modern look
        corner_radius = 15
        cvzone.cornerRect(img, (x, y, w, h), corner_radius, rt=0, 
                         colorC=KEY_BORDER, colorR=KEY_BORDER)
        
        # Special cases for different key types
        if button.text == "SPACE":
            # Modern spacebar with subtle text
            cv2.putText(img, "SPACE", (x + w//2 - 60, y + h//2 + 12),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.9, BRIGHT_TEXT, 2)  # Bright text
        elif button.text == "⌫":
            # Backspace button with improved design - clean left arrow
            arrow_start = (x + w - 25, y + h//2)
            arrow_end = (x + 25, y + h//2)
            
            # Draw the main arrow
            cv2.arrowedLine(img, arrow_start, arrow_end, BRIGHT_TEXT, 3, tipLength=0.3)
            
            # Add a small vertical line at the right to complete the backspace symbol
            cv2.line(img, (x + w - 25, y + h//2 - 15), (x + w - 25, y + h//2 + 15), BRIGHT_TEXT, 3)
        elif button.text == "⏎":
            # Enter key with arrow symbol
            arrow_start = (x + 30, y + h//2)
            arrow_end = (x + w - 20, y + h//2)
            
            # Draw horizontal line
            cv2.line(img, (x + 30, y + h//2 - 15), (x + 30, y + h//2), BRIGHT_TEXT, 3)
            
            # Draw the return arrow
            cv2.arrowedLine(img, arrow_start, arrow_end, BRIGHT_TEXT, 3, tipLength=0.3)
        elif button.text == "←" or button.text == "↑" or button.text == "→" or button.text == "↓":
            # Arrow keys centered with bright text
            text_size = cv2.getTextSize(button.text, cv2.FONT_HERSHEY_PLAIN, 4, 4)[0]
            text_x = x + (w - text_size[0])//2
            text_y = y + h//2 + 15
            cv2.putText(img, button.text, (text_x, text_y), cv2.FONT_HERSHEY_PLAIN, 4, BRIGHT_TEXT, 4)
        else:
            # Standard keys with better centering and modern font
            text_size = cv2.getTextSize(button.text, cv2.FONT_HERSHEY_PLAIN, 4, 4)[0]
            text_x = x + (w - text_size[0])//2
            text_y = y + h//2 + 15
            cv2.putText(img, button.text, (text_x, text_y), cv2.FONT_HERSHEY_PLAIN, 4, BRIGHT_TEXT, 4)
            
            # Add a subtle highlight under each letter
            cv2.putText(img, button.text, (text_x+1, text_y+1), 
                       cv2.FONT_HERSHEY_PLAIN, 4, (30, 30, 30), 1)
            
    return img

# Create Buttons - improved layout with more consistency and proper spacing
buttonList = []
for i in range(len(keys)):
    for j, key in enumerate(keys[i]):
        # Base position calculations - ensure straight and consistent alignment
        x_pos = 100 * j + 50
        y_pos = 100 * i + 50
        
        # Create a straight keyboard layout with consistent spacing
        if key == "⌫":
            # Make backspace key wider and more visible
            buttonList.append(Button([x_pos, y_pos], key, size=[120, 85]))
        elif key == "⏎":
            # Make enter key wider and more visible
            buttonList.append(Button([x_pos, y_pos], key, size=[120, 85]))
        elif key == "SPACE":
            # Make spacebar wider and position it centrally 
            buttonList.append(Button([250, y_pos], key, size=[450, 85]))
        elif key == "←" or key == "↑" or key == "→" or key == "↓":
            # Arrow keys
            buttonList.append(Button([x_pos, y_pos], key, size=[90, 85]))
        elif key == "CTRL" or key == "ALT":
            # Add function keys with appropriate size
            buttonList.append(Button([x_pos, y_pos], key, size=[150, 85]))
        else:
            # Standard sized keys with consistent spacing
            buttonList.append(Button([x_pos, y_pos], key, size=[90, 85]))

# Main Loop
while True:
    # Get image from camera
    success, img = cap.read()
    if not success:
        print("Failed to grab frame")
        continue
        
    # Flip the image horizontally for a more natural interaction
    img = cv2.flip(img, 1)
    
    # Find hands
    hands, img = detector.findHands(img)
    
    # Draw keyboard
    img = drawAll(img, buttonList)
    
    # Reset button states
    for button in buttonList:
        button.pressed = False
    
    # Check for hand position
    if hands:
        hand = hands[0]  # First hand
        lmList = hand["lmList"]  # List of 21 landmarks
        
        # Get important landmarks
        thumb_tip = lmList[4]  # Thumb tip
        index_tip = lmList[8]  # Index finger tip
        middle_tip = lmList[12]  # Middle finger tip
        thumb_base = lmList[2]  # Thumb base (near wrist)
        
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
            
            # Draw line between thumb and index finger
            cv2.line(img, (thumb_tip[0], thumb_tip[1]), (index_tip[0], index_tip[1]), 
                    ACCENT, 3)
            
            # Add visual reference for vertical distance
            midpoint_x = (thumb_tip[0] + index_tip[0]) // 2
            cv2.line(img, (midpoint_x, thumb_tip[1]), (midpoint_x, index_tip[1]), 
                     GREEN, 2)
            
            # Show distance measurements for debugging
            cv2.putText(img, f"V: {int(vertical_distance)}px", (45, 100), 
                        cv2.FONT_HERSHEY_PLAIN, 1.5, WHITE, 2)
            cv2.putText(img, f"D: {int(euclidean_distance)}px", (45, 130), 
                        cv2.FONT_HERSHEY_PLAIN, 1.5, WHITE, 2)
            
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
                
                # Highlight button with lighter color when hovering
                cv2.rectangle(img, (x - 5, y - 5), (x + w + 5, y + h + 5), KEY_LIGHT, cv2.FILLED)
                cv2.putText(img, button.text, (x + 20, y + 65),
                            cv2.FONT_HERSHEY_PLAIN, 4, DARK_BG, 4)
                
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
                    # Visual feedback (turn button blue when clicked)
                    cv2.rectangle(img, button.pos, (x + w, y + h), KEY_PRESS, cv2.FILLED)
                    
                    # Keep consistent text positioning when clicked
                    if button.text == "SPACE":
                        cv2.putText(img, button.text, (x + w//2 - 60, y + h//2 + 15),
                                    cv2.FONT_HERSHEY_PLAIN, 4, WHITE, 4)
                    elif button.text == "⌫":
                        # Draw improved backspace symbol with white color
                        arrow_start = (x + w - 25, y + h//2)
                        arrow_end = (x + 25, y + h//2)
                        
                        # Draw the main arrow line
                        cv2.arrowedLine(img, arrow_start, arrow_end, WHITE, 3, tipLength=0.3)
                        
                        # Add a small vertical line at the right to complete the backspace symbol
                        cv2.line(img, (x + w - 25, y + h//2 - 15), (x + w - 25, y + h//2 + 15), WHITE, 3)
                    elif button.text == "⏎":
                        # Enter key with white arrow symbol
                        arrow_start = (x + 30, y + h//2)
                        arrow_end = (x + w - 20, y + h//2)
                        
                        # Draw horizontal line
                        cv2.line(img, (x + 30, y + h//2 - 15), (x + 30, y + h//2), WHITE, 3)
                        
                        # Draw the return arrow
                        cv2.arrowedLine(img, arrow_start, arrow_end, WHITE, 3, tipLength=0.3)
                    elif button.text == "←" or button.text == "↑" or button.text == "→" or button.text == "↓":
                        # Arrow keys centered
                        text_size = cv2.getTextSize(button.text, cv2.FONT_HERSHEY_PLAIN, 4, 4)[0]
                        text_x = x + (w - text_size[0])//2
                        text_y = y + h//2 + 15
                        cv2.putText(img, button.text, (text_x, text_y), cv2.FONT_HERSHEY_PLAIN, 4, WHITE, 4)
                    else:
                        # Standard keys with better centering
                        text_size = cv2.getTextSize(button.text, cv2.FONT_HERSHEY_PLAIN, 4, 4)[0]
                        text_x = x + (w - text_size[0])//2
                        text_y = y + h//2 + 15
                        cv2.putText(img, button.text, (text_x, text_y), cv2.FONT_HERSHEY_PLAIN, 4, WHITE, 4)
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
    
    # Display the text box with modern styling
    # Create a gradient text box background
    img = get_key_gradient(img, 50, 550, 1150, 100, 
                         (KEY_DARK[0]//2, KEY_DARK[1]//2, KEY_DARK[2]//2),
                         KEY_DARK, vertical=False)
    
    # Add border with accent color
    cv2.rectangle(img, (50, 550), (1200, 650), ACCENT, 2)
    
    # Limit text display to fit in the box (show last 40 characters if longer)
    displayText = finalText[-40:] if len(finalText) > 40 else finalText
    
    # Draw the text with better visibility
    cv2.putText(img, displayText, (60, 610),  # Position text in the middle of the box
                cv2.FONT_HERSHEY_PLAIN, 4, WHITE, 4)
    
    # Add a label for the text box
    cv2.putText(img, "Your Text:", (60, 540), 
                cv2.FONT_HERSHEY_PLAIN, 2, ACCENT, 2)
    
    # Add usage instructions at the top of the screen
    cv2.rectangle(img, (50, 10), (1200, 40), DARK_BG, cv2.FILLED)
    cv2.putText(img, "Place index finger over key and HOLD pinch with thumb to type", (60, 30), 
                cv2.FONT_HERSHEY_PLAIN, 1.5, LIGHT_TEXT, 2)
    cv2.putText(img, "Press 'q' to quit", (950, 30),
                cv2.FONT_HERSHEY_PLAIN, 1.5, LIGHT_TEXT, 2)
    
    # Show pinch progress indicator at the top right corner (much smaller and out of the way)
    if current_pinch_frames > 0:
        # Small progress indicator that doesn't block the keyboard
        progress_width = int((current_pinch_frames / HOLD_FRAMES) * 100)
        cv2.rectangle(img, (1150, 50), (1150 + progress_width, 70), GREEN, cv2.FILLED)
        cv2.rectangle(img, (1150, 50), (1250, 70), ACCENT, 2)
        cv2.putText(img, "PINCH", (1155, 65), cv2.FONT_HERSHEY_PLAIN, 1, WHITE, 1)
    
    # Show image
    cv2.imshow("AI Virtual Keyboard - Modern Edition", img)
    
    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
