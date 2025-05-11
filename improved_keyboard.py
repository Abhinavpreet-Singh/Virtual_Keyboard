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

# Hand Detector with higher confidence for better detection
detector = HandDetector(detectionCon=0.9, maxHands=1)

# Keyboard Layout - Redesigned for better accessibility
# Top row in a C shape for easier reach
keys = [["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
        ["A", "S", "D", "F", "G", "H", "J", "K", "L", ";"],
        ["Z", "X", "C", "V", "B", "N", "M", ",", ".", "/"],
        ["<", "SPACE", "ENTER"]]  # Added ENTER key and moved backspace to bottom row

finalText = ""
keyboard = Controller()

# Color definitions
CYAN = (255, 255, 0)         # Light cyan - normal keys
LIGHT_CYAN = (255, 255, 128)  # Very light cyan - hover effect
NAVY = (128, 128, 0)         # Dark cyan/navy - clicked keys
BLACK = (0, 0, 0)            # Black for text
WHITE = (255, 255, 255)      # White for text display
GREEN = (0, 255, 0)          # Green for success indicators
RED = (0, 0, 255)            # Red for alerts/warnings
YELLOW = (0, 255, 255)       # Yellow for intermediate states

# Pinch detection parameters - adjusted for better performance
VERTICAL_THRESHOLD = 50       # Maximum vertical distance for pinch detection
PINCH_THRESHOLD = 45          # Maximum distance for pinch detection (smaller value = more precise pinch needed)
HOLD_FRAMES = 5               # Number of consecutive frames a pinch must be detected before registering
current_pinch_frames = 0      # Counter for stable pinch frames
pinch_cooldown = {}           # Dictionary to track last pinch time for each key
PINCH_COOLDOWN_TIME = 0.5     # Time in seconds before allowing the same key to be pinched again

# Button Class for Virtual Keys
class Button():
    def __init__(self, pos, text, size=[85, 85]):
        self.pos = pos
        self.size = size
        self.text = text
        self.pressed = False  # Track if key is currently pressed

# Drawing Function
def drawAll(img, buttonList):
    for button in buttonList:
        x, y = button.pos
        w, h = button.size
        cvzone.cornerRect(img, (button.pos[0], button.pos[1], button.size[0], button.size[1]),
                          20, rt=0)
        cv2.rectangle(img, button.pos, (x + w, y + h), CYAN, cv2.FILLED)  # Cyan keys
        
        # Center text for spacebar, regular positioning for other keys
        if button.text == "SPACE":
            cv2.putText(img, button.text, (x + w//2 - 60, y + 65),
                        cv2.FONT_HERSHEY_PLAIN, 4, BLACK, 4)  # Black text
        elif button.text == "ENTER":
            cv2.putText(img, button.text, (x + 20, y + 65),
                        cv2.FONT_HERSHEY_PLAIN, 3, BLACK, 4)  # Black text
        else:
            cv2.putText(img, button.text, (x + 20, y + 65),
                        cv2.FONT_HERSHEY_PLAIN, 4, BLACK, 4)  # Black text
    return img

# Create Buttons
buttonList = []
for i in range(len(keys)):
    for j, key in enumerate(keys[i]):
        # Create a concave curved keyboard layout with top row brought lower
        if i == 0:  # Top row - create a concave curve
            # Make the center higher than the edges
            curve_offset = 80 - abs(j - 4.5) * 5  # Higher in the middle (more extreme curve)
            y_pos = 100 * i + 80 + curve_offset
            buttonList.append(Button([100 * j + 50, y_pos], key))
        elif key == "SPACE":
            # Make spacebar wider and position it centrally 
            buttonList.append(Button([400, 100 * i + 50], key, size=[400, 85]))
        elif key == "ENTER":
            # Make ENTER key wider
            buttonList.append(Button([850, 100 * i + 50], key, size=[150, 85]))
        elif key == "<":
            # Make backspace key slightly wider
            buttonList.append(Button([100, 100 * i + 50], key, size=[150, 85]))
        else:
            buttonList.append(Button([100 * j + 50, 100 * i + 50], key))

# Last pressed state
last_pinch_state = False
last_pressed_button = None
last_key_time = 0

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
    
    # Reset pinch detection for this frame
    current_pinch = False
    current_button = None
    
    # Check for hand position
    if hands:
        hand = hands[0]  # First hand
        lmList = hand["lmList"]  # List of 21 landmarks
        
        # Get important finger landmarks
        thumb_tip = lmList[4]  # Thumb tip
        index_tip = lmList[8]  # Index finger tip
        middle_tip = lmList[12]  # Middle finger tip
        thumb_base = lmList[2]  # Thumb base (near wrist)
        index_base = lmList[5]  # Index finger base
        
        # Draw circles on fingertips for visual feedback
        cv2.circle(img, (thumb_tip[0], thumb_tip[1]), 12, WHITE, cv2.FILLED)
        cv2.circle(img, (index_tip[0], index_tip[1]), 12, WHITE, cv2.FILLED)
        
        # Calculate distances for pinch detection
        try:
            # Calculate vertical distance between thumb and index finger tips
            vertical_distance = abs(thumb_tip[1] - index_tip[1])
            horizontal_distance = abs(thumb_tip[0] - index_tip[0])
            
            # Calculate euclidean distance for more accuracy
            euclidean_distance = np.sqrt(vertical_distance**2 + horizontal_distance**2)
            
            # Draw line between thumb and index finger
            cv2.line(img, (thumb_tip[0], thumb_tip[1]), (index_tip[0], index_tip[1]), 
                    CYAN, 3)
            
            # Add visual reference for vertical distance
            midpoint_x = (thumb_tip[0] + index_tip[0]) // 2
            cv2.line(img, (midpoint_x, thumb_tip[1]), (midpoint_x, index_tip[1]), 
                     GREEN, 2)
            
            # Show distance measurements for debugging
            cv2.putText(img, f"Distance: {int(euclidean_distance)}px", (45, 130), 
                        cv2.FONT_HERSHEY_PLAIN, 1.5, WHITE, 2)
            
            # Check if thumb is raised relative to its base position
            thumb_raised = (thumb_tip[1] < thumb_base[1] - 20)
            
            # Improved pinch detection logic
            # 1. Vertical distance should be small (vertical pinch)
            # 2. Overall distance should be small
            # 3. Thumb should be raised from its base position
            is_pinching = (euclidean_distance < PINCH_THRESHOLD and vertical_distance < VERTICAL_THRESHOLD and thumb_raised)
            
            # Visual indicator for pinch detection status
            if is_pinching:
                cv2.putText(img, "PINCH DETECTED", (45, 180), 
                        cv2.FONT_HERSHEY_PLAIN, 2, GREEN, 3)
                
                # Only count consecutive pinch frames
                current_pinch_frames += 1
                if current_pinch_frames > HOLD_FRAMES:
                    current_pinch = True
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
                
                # Highlight button with lighter cyan when hovering
                cv2.rectangle(img, (x - 5, y - 5), (x + w + 5, y + h + 5), LIGHT_CYAN, cv2.FILLED)
                cv2.putText(img, button.text, (x + 20, y + 65),
                            cv2.FONT_HERSHEY_PLAIN, 4, BLACK, 4)
                
                # Check if button is in cooldown
                in_cooldown = False
                if button.text in pinch_cooldown:
                    time_elapsed = current_time - pinch_cooldown[button.text]
                    if time_elapsed < PINCH_COOLDOWN_TIME:
                        in_cooldown = True
                        
                        # Show cooldown progress bar
                        remaining = PINCH_COOLDOWN_TIME - time_elapsed
                        progress = int((remaining / PINCH_COOLDOWN_TIME) * w)
                        cv2.rectangle(img, (x, y + h - 5), (x + progress, y + h), RED, cv2.FILLED)
                
                # If pinch is stable and not in cooldown
                if current_pinch and not in_cooldown:
                    # Reset pinch frames to avoid multiple triggers
                    current_pinch_frames = 0
                    
                    # Set cooldown for this key
                    pinch_cooldown[button.text] = current_time
                    button.pressed = True
                    
                    # Visual feedback (turn button navy blue when clicked)
                    cv2.rectangle(img, button.pos, (x + w, y + h), NAVY, cv2.FILLED)
                    cv2.putText(img, button.text, (x + 20, y + 65),
                                cv2.FONT_HERSHEY_PLAIN, 4, WHITE, 4)
                    
                    # Handle different key types
                    if button.text == '<':
                        # Backspace handling
                        try:
                            keyboard.press(Key.backspace)
                            sleep(0.02)
                            keyboard.release(Key.backspace)
                            print("Backspace pressed")
                        except Exception as e:
                            print(f"Backspace error: {e}")
                                
                        if len(finalText) > 0:
                            finalText = finalText[:-1]
                    elif button.text == "SPACE":
                        # Space handling
                        try:
                            # Multiple approaches to ensure space works
                            keyboard.press(Key.space)
                            sleep(0.02)
                            keyboard.release(Key.space)
                            print("Space pressed")
                        except Exception as e:
                            print(f"Space error: {e}")
                            try:
                                # Fallback
                                keyboard.type(" ")
                            except:
                                pass
                                
                        finalText += " "
                    elif button.text == "ENTER":
                        # Enter handling
                        try:
                            keyboard.press(Key.enter)
                            sleep(0.02)
                            keyboard.release(Key.enter)
                            print("Enter pressed")
                        except Exception as e:
                            print(f"Enter error: {e}")
                            
                        finalText += "\n"
                    else:
                        # Normal key press - try multiple methods for reliability
                        key_char = button.text.lower()  # Use lowercase for typing
                        
                        try:
                            # Type directly using pynput's type method
                            keyboard.type(key_char)
                            print(f"Typed key: {key_char}")
                        except Exception as e:
                            print(f"Type error: {e}")
                            try:
                                # Second approach: press and release with slight delay
                                keyboard.press(key_char)
                                sleep(0.02)  # Brief delay
                                keyboard.release(key_char)
                                print(f"Press-Release: {key_char}")
                            except Exception as e2:
                                print(f"Press-Release error: {e2}")
                                
                        finalText += button.text
                        
                    # Add a brief delay after successful key press for stability
                    sleep(0.1)
                    
                # Show "almost pinching" indicator
                elif 'is_pinching' in locals() and is_pinching:
                    # Show progress bar for pinch hold time
                    hold_progress = int((current_pinch_frames / HOLD_FRAMES) * w)
                    cv2.rectangle(img, (x, y + h - 5), (x + hold_progress, y + h), GREEN, cv2.FILLED)
                    
                # Show hover indicator when finger is over button but not pinching
                elif 'is_pinching' in locals() and not is_pinching and not in_cooldown:
                    cv2.rectangle(img, (x, y + h - 5), (x + w, y + h), YELLOW, cv2.FILLED)
    
    # Display the text box - larger, more visible box at the bottom
    cv2.rectangle(img, (50, 550), (1200, 650), BLACK, cv2.FILLED)  # Black background
    cv2.rectangle(img, (50, 550), (1200, 650), CYAN, 3)  # Cyan border
    
    # Limit text display to fit in the box (show last 40 characters if longer)
    displayText = finalText[-40:] if len(finalText) > 40 else finalText
    
    # Draw the text with better visibility
    cv2.putText(img, displayText, (60, 610),  # Position text in the middle of the box
                cv2.FONT_HERSHEY_PLAIN, 4, WHITE, 4)
    
    # Add a label for the text box
    cv2.putText(img, "Your Text:", (60, 540), 
                cv2.FONT_HERSHEY_PLAIN, 2, CYAN, 2)
                
    # Add usage instructions at the top of the screen
    cv2.rectangle(img, (50, 10), (1200, 40), BLACK, cv2.FILLED)
    cv2.putText(img, "Place index finger over key and pinch with thumb to type", (60, 30), 
                cv2.FONT_HERSHEY_PLAIN, 1.5, CYAN, 2)
    cv2.putText(img, "Press 'q' to quit", (950, 30),
                cv2.FONT_HERSHEY_PLAIN, 1.5, CYAN, 2)
                
    # Add visual guide for vertical pinch gesture in the corner of the screen
    guide_size = 200
    guide_position = (img.shape[1] - guide_size - 20, 70)
    
    # Create a small guide area
    cv2.rectangle(img, guide_position, (guide_position[0] + guide_size, guide_position[1] + guide_size), 
                 BLACK, cv2.FILLED)
    cv2.rectangle(img, guide_position, (guide_position[0] + guide_size, guide_position[1] + guide_size), 
                 CYAN, 2)
    
    # Draw thumb and index finger for vertical pinch demonstration
    thumb_pos = (guide_position[0] + 100, guide_position[1] + 140)  # Thumb below
    index_pos = (guide_position[0] + 100, guide_position[1] + 60)   # Index above
    
    # Draw fingers
    cv2.circle(img, thumb_pos, 20, CYAN, cv2.FILLED)  # Thumb
    cv2.circle(img, index_pos, 15, CYAN, cv2.FILLED)  # Index
    
    # Draw arrows showing vertical pinch motion
    arrow_start1 = (thumb_pos[0], thumb_pos[1] - 20)
    arrow_end1 = (thumb_pos[0], thumb_pos[1] - 40)
    arrow_start2 = (index_pos[0], index_pos[1] + 15)
    arrow_end2 = (index_pos[0], index_pos[1] + 40)
    
    cv2.arrowedLine(img, arrow_start1, arrow_end1, WHITE, 3, tipLength=0.3)
    cv2.arrowedLine(img, arrow_start2, arrow_end2, WHITE, 3, tipLength=0.3)
    
    # Draw vertical distance line
    cv2.line(img, (guide_position[0] + 120, thumb_pos[1]), 
             (guide_position[0] + 120, index_pos[1]), GREEN, 2)
    
    # Add labels
    cv2.putText(img, "Thumb", (thumb_pos[0] - 60, thumb_pos[1]), 
               cv2.FONT_HERSHEY_PLAIN, 1, WHITE, 2)
    cv2.putText(img, "Index", (index_pos[0] - 60, index_pos[1]), 
               cv2.FONT_HERSHEY_PLAIN, 1, WHITE, 2)
    
    # Show image
    cv2.imshow("Virtual Keyboard", img)
    
    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
