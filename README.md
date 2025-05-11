# Virtual Keyboard with Hand Gesture Control

A computer vision-based virtual keyboard that allows you to type without a physical keyboard using hand gestures and motion tracking.

## Description

This project implements a virtual keyboard that you can control using hand gestures captured through your webcam. The system uses computer vision techniques to track hand movements and detect gestures, allowing you to "press" keys by pinching your fingers together.

## Features

- Virtual QWERTY keyboard displayed on screen
- Hand tracking without additional hardware
- Gesture-based key selection and pressing
- Text display showing your typed content
- Backspace functionality

## Setup Instructions

1. Create a virtual environment:
   ```
   python -m venv venv
   ```

2. Activate the virtual environment:
   - Windows:
     ```
     .\venv\Scripts\Activate
     ```
   - Linux/Mac:
     ```
     source venv/bin/activate
     ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Run the application:
   ```
   python main.py
   ```

## How to Use

1. Make sure your webcam is enabled and functioning.
2. Run the application to open a window showing your webcam feed.
3. Position your hand within the camera view.
4. Move your index finger to the desired key.
5. Pinch your index finger and middle finger together to "click" on the key.
6. Use the "<" key to backspace.
7. Press 'q' on your physical keyboard to quit the application.

## Dependencies

- OpenCV
- cvzone
- numpy
- pynput
- mediapipe

## Requirements

- Python 3.7 or higher
- Webcam

## Project Structure

```
Virtual-Keyboard/
│
├── main.py              # Main application file
├── requirements.txt     # Project dependencies
├── .gitignore           # Git ignore file
├── README.md            # Project documentation
└── LICENSE              # MIT License
```

## How It Works

The application utilizes several computer vision techniques:

1. **Keyboard Layout Model**: An array of the keyboard layout in QWERTY format is displayed using OpenCV.
2. **Hand Detection**: MediaPipe's hand tracking model identifies hand positions in the video feed.
3. **Landmark Tracking**: The system tracks 21 key points (landmarks) on each detected hand.
4. **Click Detection**: The distance between index finger and middle finger landmarks is measured to detect a "click" gesture.

## Troubleshooting

- **Webcam not detected**: Ensure your webcam is properly connected and not being used by another application
- **Hand detection issues**: Ensure good lighting and a clear background
- **Performance problems**: Try reducing the resolution in the code (cap.set values)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- MediaPipe for the hand tracking technology
- OpenCV for computer vision capabilities
- The computer vision community for inspiration and resources

When the distance between index and middle finger points is less than a threshold, the system registers it as a key press and records it.
