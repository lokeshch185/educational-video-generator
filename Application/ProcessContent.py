import json
import pyttsx3
from pptx import Presentation
from pptx.util import Inches, Pt
from moviepy.editor import AudioFileClip, concatenate_audioclips
import os
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

class VideoGenerator:
    def __init__(self, json_file):
        
        with open(json_file, 'r', encoding='utf-8') as f:
            self.lesson_data = json.load(f)
        
        
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 175)
        
        
        self.base_dir = Path.cwd() / 'output'
        self.slides_dir = self.base_dir / 'slides'
        self.audio_dir = self.base_dir / 'audio'
        self.timing_dir = self.base_dir / 'timing'
        
        
        for dir_path in [self.slides_dir, self.audio_dir, self.timing_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        
        self.slide_width = 1920
        self.slide_height = 1080
        
        
        self.setup_fonts()

    def setup_fonts(self):
        """Setup fonts for Windows"""
        try:
            
            windows_fonts = [
                "arial.ttf",
                "arialbd.ttf",  
                "calibri.ttf",
                "calibrib.ttf"  
            ]
            
            
            font_dir = Path(os.environ['SYSTEMROOT']) / 'Fonts'
            
            
            for font in windows_fonts:
                font_path = font_dir / font
                if font_path.exists():
                    if 'bd' in font.lower() or 'b.' in font.lower():
                        self.title_font = str(font_path)
                    else:
                        self.body_font = str(font_path)
                    
            print("Fonts loaded successfully")
        except Exception as e:
            print(f"Error loading fonts: {str(e)}")
            self.title_font = None
            self.body_font = None

    def create_slide_image(self, title, points, output_path):
        """Create a slide image using Pillow"""
        
        img = Image.new('RGB', (self.slide_width, self.slide_height), 'white')
        
        try:
            draw = ImageDraw.Draw(img)

            
            try:
                title_font = ImageFont.truetype(self.title_font if self.title_font else "arial.ttf", 60)
                body_font = ImageFont.truetype(self.body_font if self.body_font else "arial.ttf", 40)
            except:
                print("Warning: Using default font")
                title_font = ImageFont.load_default()
                body_font = ImageFont.load_default()

            
            title_bbox = draw.textbbox((0, 0), title, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_height = title_bbox[3] - title_bbox[1]
            
            
            title_bg_color = (240, 240, 240)  
            draw.rectangle([0, 0, self.slide_width, title_height + 100], fill=title_bg_color)
            
            
            title_x = (self.slide_width - title_width) // 2
            draw.text((title_x, 50), title, font=title_font, fill='black')

            
            y_position = 200
            for point in points:
                
                max_width = self.slide_width - 200  
                words = point.split()
                line = ''
                for word in words:
                    test_line = line + word + ' '
                    test_bbox = draw.textbbox((0, 0), test_line, font=body_font)
                    test_width = test_bbox[2] - test_bbox[0]
                    
                    if test_width > max_width:
                        
                        draw.text((150, y_position), line, font=body_font, fill='black')
                        y_position += 50
                        line = word + ' '
                    else:
                        line = test_line
                
                
                draw.text((100, y_position), "•", font=body_font, fill='black')
                
                if line:
                    draw.text((150, y_position), line, font=body_font, fill='black')
                y_position += 70

            
            img.save(output_path, quality=95)
            return True

        except Exception as e:
            print(f"Error creating slide image: {str(e)}")
            return False

    def sanitize_filename(self, filename):
        """Convert a string to a valid filename."""
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        filename = filename.replace(' ', '_')
        if len(filename) > 200:
            filename = filename[:200]
        return filename.strip('._')

    def generate_audio(self, text, filename):
        """Generate audio file from text"""
        try:
            safe_filename = self.sanitize_filename(filename)
            audio_path = self.audio_dir / f'{safe_filename}.mp3'
            
            self.engine.save_to_file(text, str(audio_path))
            self.engine.runAndWait()
            
            
            audio = AudioFileClip(str(audio_path))
            duration = audio.duration
            audio.close()
            
            return str(audio_path), duration
            
        except Exception as e:
            print(f"Error generating audio: {str(e)}")
            return None, 0

    def process_subtopic(self, content):
        """Process a subtopic to generate slides and audio with timing"""
        try:
            print(f"\nProcessing: {content['title']}")
            safe_title = self.sanitize_filename(content['title'])
            
            
            image_folder = self.slides_dir / f'{safe_title}_images'
            image_folder.mkdir(exist_ok=True)
            
            timing_info = {
                'title': content['title'],
                'slides': []
            }
            
            
            title_path = image_folder / 'slide_0.png'
            self.create_slide_image(content['title'], [""], title_path)
            
            intro_audio_path, intro_duration = self.generate_audio(
                content['introduction'],
                f"{safe_title}_intro"
            )
            
            if intro_audio_path:
                timing_info['slides'].append({
                    'type': 'title',
                    'image_path': str(title_path),
                    'audio_path': intro_audio_path,
                    'duration': intro_duration
                })
            
            
            for i, slide_content in enumerate(content['slides'], 1):
                slide_path = image_folder / f'slide_{i}.png'
                self.create_slide_image(
                    slide_content['title'],
                    slide_content['key_points'],
                    slide_path
                )
                
                audio_path, duration = self.generate_audio(
                    slide_content['teacher_speech'],
                    f"{safe_title}_slide_{i}"
                )
                
                if audio_path:
                    timing_info['slides'].append({
                        'type': 'content',
                        'title': slide_content['title'],
                        'image_path': str(slide_path),
                        'audio_path': audio_path,
                        'duration': duration
                    })
            
            
            conclusion_path = image_folder / f'slide_{len(content["slides"])+1}.png'
            self.create_slide_image("Conclusion", [""], conclusion_path)
            
            conclusion_audio_path, conclusion_duration = self.generate_audio(
                content['conclusion'],
                f"{safe_title}_conclusion"
            )
            
            if conclusion_audio_path:
                timing_info['slides'].append({
                    'type': 'conclusion',
                    'image_path': str(conclusion_path),
                    'audio_path': conclusion_audio_path,
                    'duration': conclusion_duration
                })
            
            
            timing_path = self.timing_dir / f'{safe_title}_timing.json'
            with open(timing_path, 'w', encoding='utf-8') as f:
                json.dump(timing_info, f, indent=4)
            
            print(f"Generated images in: {image_folder}")
            print(f"Generated timing info: {timing_path}")
            print("Slide durations:")
            for slide in timing_info['slides']:
                print(f"- {slide.get('title', slide['type'])}: {slide['duration']:.2f} seconds")
            
        except Exception as e:
            print(f"Error processing subtopic: {str(e)}")

    def generate_full_lesson(self):
        """Generate all subtopics"""
        for content in self.lesson_data['content']:
            self.process_subtopic(content)

if __name__ == "__main__":
    generator = VideoGenerator('lesson_plan.json')
    generator.generate_full_lesson()