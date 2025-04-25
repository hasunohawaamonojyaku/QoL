import pytesseract
from PIL import Image
import os
import argparse
import tkinter as tk
from tkinter import filedialog
import sys

def select_image_file():
    """
    Opens a file dialog to select an image file.
    Returns the path to the selected file or None if canceled.
    """
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    file_path = filedialog.askopenfilename(
        title="Select Image for OCR",
        filetypes=[
            ("Image files", "*.png;*.jpg;*.jpeg;*.tiff;*.bmp;*.gif"),
            ("All files", "*.*")
        ]
    )
    
    return file_path if file_path else None

def get_image_path():
    """
    Determines the image path from command line arguments or file dialog.
    Returns the image path or None if no valid path is provided.
    """
    parser = argparse.ArgumentParser(description='Perform OCR on an image')
    parser.add_argument('--image', help='Path to the image file')
    parser.add_argument('--lang', default='eng', help='Language for OCR (default: English)')
    parser.add_argument('--search', help='Optional word to search for in the results')
    
    # Parse only known args to avoid errors with other arguments
    args, _ = parser.parse_known_args()
    
    image_path = args.image
    
    # If image path not provided in command line, prompt with file dialog
    if not image_path:
        image_path = select_image_file()
        
    return image_path, args.lang, args.search

def perform_ocr(image_path, lang='eng'):
    """
    Performs OCR on an image using Tesseract and returns the text.

    Args:
        image_path: Path to the image file.
        lang: Language for OCR (default: English).

    Returns:
        A tuple containing:
            - The extracted text (string).
            - A dictionary with the bounding box, confidence, and text of each detected word.
    """
    try:
        img = Image.open(image_path)
    except FileNotFoundError:
        print(f"Error: Image not found at {image_path}")
        return None, None
    except Exception as e:
        print(f"Error opening image: {e}")
        return None, None

    try:
        # Perform OCR using Tesseract
        text = pytesseract.image_to_string(img, lang=lang)

        # Get bounding box information for each word
        data = pytesseract.image_to_data(img, lang=lang, output_type=pytesseract.Output.DICT)

        # Prepare a structured result
        word_data = []
        n_boxes = len(data['level'])
        for i in range(n_boxes):
            if int(data['level'][i]) == 5:  # Level 5 represents individual words
                if len(data['text'][i].strip()) > 0:  # Only include non-empty words
                    word_data.append({
                        'text': data['text'][i],
                        'confidence': data['conf'][i],
                        'left': data['left'][i],
                        'top': data['top'][i],
                        'width': data['width'][i],
                        'height': data['height'][i]
                    })
        
        return text, word_data

    except pytesseract.TesseractNotFoundError:
        print("Error: Tesseract is not installed or not in your system's PATH.")
        print("Please install Tesseract and configure its path using pytesseract.pytesseract.tesseract_cmd.")
        return None, None
    except Exception as e:
        print(f"Error during OCR: {e}")
        return None, None

def save_results(text, filepath=None):
    """
    Saves the OCR results to a text file.
    
    Args:
        text: The text to save
        filepath: Optional filepath, if None will use the same name as the image
    """
    if not filepath:
        filepath = os.path.splitext(image_path)[0] + "_ocr.txt"
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"OCR results saved to: {filepath}")
        return True
    except Exception as e:
        print(f"Error saving results: {e}")
        return False

def main():
    # Try to set Tesseract path if it's in a common location
    common_tesseract_paths = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',  # Windows
        r'/usr/local/bin/tesseract',  # macOS (Homebrew)
        r'/usr/bin/tesseract',  # Linux
        r'/opt/homebrew/bin/tesseract'  # macOS Apple Silicon
    ]
    
    for path in common_tesseract_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            break
    
    # Get image path from command line or file dialog
    image_path, lang, search_word = get_image_path()
    
    if not image_path:
        print("No image selected. Exiting.")
        return
    
    print(f"Processing image: {image_path}")
    print(f"Using language: {lang}")
    
    extracted_text, word_data = perform_ocr(image_path, lang)

    if extracted_text:
        print("\n" + "="*50)
        print("EXTRACTED TEXT:")
        print("="*50)
        print(extracted_text)
        
        # Ask if user wants to save the results
        save_choice = input("\nSave results to text file? (y/n): ").lower()
        if save_choice == 'y':
            save_results(extracted_text, filepath=None)

        # Search for word if specified
        if search_word:
            print(f"\nSearching for: '{search_word}'")
            found_instances = []
            for word in word_data:
                if search_word.lower() in word['text'].lower():
                    found_instances.append(word)
            
            if found_instances:
                print(f"Found '{search_word}' {len(found_instances)} times:")
                for i, instance in enumerate(found_instances):
                    print(f"  {i+1}. '{instance['text']}' with confidence: {instance['confidence']}%")
            else:
                print(f"'{search_word}' not found in the OCR results.")

    else:
        print("OCR failed to extract any text.")


if __name__ == "__main__":
    main()