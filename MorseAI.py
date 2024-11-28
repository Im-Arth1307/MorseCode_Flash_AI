import cv2
import numpy as np
import time
from tensorflow import keras
from keras.models import Sequential # type: ignore
from keras.layers import LSTM, Dense, TimeDistributed, Conv3D, MaxPooling3D, Flatten  # type: ignore
import threading


# Morse code dictionary
MORSE_CODE = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.',
    'F': '..-.', 'G': '--.', 'H': '....', 'I': '..', 'J': '.---',
    'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---',
    'P': '.--.', 'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-',
    'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-', 'Y': '-.--',
    'Z': '--..', ' ': ' '
}

class FlashlightMorseTransmitter:
    def __init__(self) :
        # In a real implementation, you would use platform-specific code
        # to control the flashlight. This is a mock implementation.
        self.flashlight_on = False
        
    def text_to_morse(self, text):
        """Convert text to morse code"""
        morse = []
        for c in text:
            if c.upper() in MORSE_CODE:
                morse.append(MORSE_CODE[c.upper()])
            elif c == ' ':
                morse.append(' ')
            else:
                morse.append('')  # Skip invalid characters
        return ' '.join(morse)
    
    def transmit_morse(self, morse_code):
        #In a real implementation, you would use platform-specific code
        #to control the flashlight. This is a mock implementation.
        DOT_DURATION = 0.2
        DASH_DURATION = 0.6
        
        try:
            for symbol in morse_code:
                if not self.istransmitting:
                    break
                if symbol == '.':
                    self.flash_on()
                    #Turn the flash on
                    time.sleep(DOT_DURATION)
                    #Keep it on for the duration of the dot
                    self.flash_off()
                    #Turn the flash off
                
                elif symbol == '-':
                    self.flash_on()
                    time.sleep(DASH_DURATION)
                    self.flash_off()
                    
                elif symbol == ' ':
                    time.sleep(DOT_DURATION * 3)
                time.sleep(DOT_DURATION)
        except Exception as e:
            self.flash_off()    #Flash off on error
            print(f"Error while transmitting Morse code: {e}")
            

    def flash_on(self):
        #In a real implementation, you would use platform-specific code
        #to control the flashlight. This is a mock implementation.
        self.flashlight_on = True
        
    def flash_off(self):
        #In a real implementation, you would use platform-specific code
        #to control the flashlight. This is a mock implementation.
        self.flashlight_on = False
        
class FlashlightMorseReceiver:
    def __init__(self):
        self.model = self.build_model()
        self.camera = None  # Initialize the camera object(None for now)
        self.isrecording = False
        self.buffer_size = 100
        
    def __del__(self):
        self.stop_recording()
        if self.camera:
            self.camera.release()
            
    def build_model(self):
        model = Sequential([
            Conv3D(32, kernel_size = (3 , 3, 3), activation = 'relu', input_shape = (None, 64, 64, 1)),
            MaxPooling3D(pool_size = (1, 2, 2)),
            Conv3D(64, kernel_size = (3, 3, 3), activation = 'relu'),
            MaxPooling3D(pool_size = (1, 2, 2)),
            TimeDistributed(Flatten()),
            LSTM(128, return_sequences = True),
            LSTM(64),
            Dense(32, activation = 'relu'),
            Dense(len(MORSE_CODE), activation = 'softmax')
        ])
        
    def _record_and_buffer(self):
        frame_buffer = []
        last_frame_time = time.time()
        desired_fps = 30
        frame_interval = 1.0 / desired_fps
        
        
        while self.is_recording:
            current_time = time.time()
            if current_time - last_frame_time < frame_interval:
                continue
            
            try:
                ret, frame = self.camera.read()
                if not ret:
                    print("Failed to capture frame")
                    continue
        
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                resized = cv2.resize(gray, (64, 64))
                normalized = resized / 255.0
                
                frame_buffer.append(normalized)
                
                if len(frame_buffer) > self.buffer_size:
                    frame_buffer = frame_buffer[-self.buffer_size:]
                    
                if len(frame_buffer) == self.buffer_size:
                    prediction = self._process_buffer(frame_buffer)
                    self._decode_prediction(prediction)
                    
                last_frame_time = current_time
                
            except Exception as e:
                print(f"Error while recording and buffering: {str(e)}")
                time.sleep(0.1)
    
    def decode_prediction(self, prediction):
        #Decode model prediction to morse code and then text
        
        THRESHOLD = 0.6
        symbols = []
        
        for prob in prediction:
            if prob[0] > THRESHOLD:
                symbols.append('.')
            elif prob[1] > THRESHOLD:
                symbols.append('-')
            elif prob[2] > THRESHOLD:
                symbols.append(' ')
                
        #Convert to text:
        morse_sequence = ''.join(symbols)
        words = morse_sequence.split('   ')  #3 spaces between words
        
        decoded_text = ''
        reverse_morse = {v:k for k, v in MORSE_CODE.items()}
        
        for word in words:
            chars = word.split(' ')
            for char in chars:
                if char in reverse_morse:
                    decoded_text += reverse_morse[char]
            decoded_text += ' '
            
        print(f"Decoded text: {decoded_text.strip()}")
        
    def generate_training_data(num_samples=1000):
        """Generate synthetic training data for the model"""
        X = []  # Video sequences
        y = []  # Labels
        
        # Generate sequences
        for _ in range(num_samples):
            # Create empty sequence
            sequence = np.zeros((100, 64, 64, 1))
            
            # Randomly choose dot, dash, or space
            symbol_type = np.random.choice(['dot', 'dash', 'space'])
            
            if symbol_type == 'dot':
                # Create short flash pattern
                sequence[10:15, 20:40, 20:40, 0] = 1.0
                y.append([1, 0, 0])
            elif symbol_type == 'dash':
                # Create long flash pattern
                sequence[10:25, 20:40, 20:40, 0] = 1.0
                y.append([0, 1, 0])
            else:
                # Create space (no flash)
                y.append([0, 0, 1])
                
            X.append(sequence)
        
        return np.array(X), np.array(y)
            
            