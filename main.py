import cv2
from cvzone.HandTrackingModule import HandDetector
from time import sleep
import numpy as np
import cvzone
from pynput.keyboard import Controller

# Camera Setup
cap = cv2.VideoCapture(0)
cap.set(3, 1280)
cap.set(4, 720)

# Hand Detector
detector = HandDetector(detectionCon=0.8, maxHands=1)

# Keyboard Layout
keys = [["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
        ["A", "S", "D", "F", "G", "H", "J", "K", "L", ";"],
        ["Z", "X", "C", "V", "B", "N", "M", ",", ".", "/", "<"]]

finalText = ""
keyboard = Controller()

# Button Class for Virtual Keys
class Button():
    def __init__(self, pos, text, size=[85, 85]):
        self.pos = pos
        self.size = size
        self.text = text

# Drawing Function
def drawAll(img, buttonList):
    for button in buttonList:
        x, y = button.pos
        w, h = button.size
        cvzone.cornerRect(img, (button.pos[0], button.pos[1], button.size[0], button.size[1]),
                          20, rt=0)
        cv2.rectangle(img, button.pos, (x + w, y + h), (255, 0, 255), cv2.FILLED)
        cv2.putText(img, button.text, (x + 20, y + 65),
                    cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 4)
    return img

# Create Buttons
buttonList = []
for i in range(len(keys)):
    for j, key in enumerate(keys[i]):
        buttonList.append(Button([100 * j + 50, 100 * i + 50], key))

# Main Loop
while True:
    # Get image from camera
    success, img = cap.read()
    
    # Find hands
    hands, img = detector.findHands(img)
    
    # Draw keyboard
    img = drawAll(img, buttonList)
    
    # Check for hand position
    if hands:
        hand = hands[0]  # First hand
        lmList = hand["lmList"]  # List of 21 landmarks
        
        for button in buttonList:
            x, y = button.pos
            w, h = button.size
            
            # Check if index finger tip is over button
            if x < lmList[8][0] < x + w and y < lmList[8][1] < y + h:
                # Highlight button
                cv2.rectangle(img, (x - 5, y - 5), (x + w + 5, y + h + 5), (175, 0, 175), cv2.FILLED)
                cv2.putText(img, button.text, (x + 20, y + 65),
                            cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 4)
                
                # Check if clicking (distance between index and middle finger)
                try:
                    # Using index finger (8) and middle finger (12) landmarks
                    distance, _, _ = detector.findDistance(lmList[8][:2], lmList[12][:2], img, draw=False)
                    
                    # When clicked
                    if distance < 30:
                        # Press the key
                        keyboard.press(button.text)
                        
                        # Visual feedback
                        cv2.rectangle(img, button.pos, (x + w, y + h), (0, 255, 0), cv2.FILLED)
                        cv2.putText(img, button.text, (x + 20, y + 65),
                                    cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 4)
                        
                        # Handle backspace and adding text
                        if button.text == '<':
                            if len(finalText) > 0:
                                finalText = finalText[:-1]
                        else:
                            finalText += button.text
                        
                        # Delay to avoid multiple clicks
                        sleep(0.5)
                except:
                    pass
    
    # Display the text box
    cv2.rectangle(img, (50, 350), (700, 450), (175, 0, 175), cv2.FILLED)
    cv2.putText(img, finalText, (60, 430),
                cv2.FONT_HERSHEY_PLAIN, 5, (255, 255, 255), 5)
    
    # Show image
    cv2.imshow("Virtual Keyboard", img)
    
    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
