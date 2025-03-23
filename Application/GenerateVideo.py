from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
import json
from pathlib import Path
import sys

class VideoCreator:
    def __init__(self, timing_folder="output/timing", output_folder="output/videos"):
        self.timing_folder = Path(timing_folder)
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(exist_ok=True)
        
        
        self.width = 1920
        self.height = 1080
        self.fps = 24
        
        
        self.fade_duration = 0.5  

    def create_slide_clip(self, image_path, audio_path, duration):
        """Create a video clip from an image and audio"""
        try:
            
            image_clip = (ImageClip(str(image_path))
                         .set_duration(duration)
                         .resize(width=self.width, height=self.height)
                         .fadein(self.fade_duration)
                         .fadeout(self.fade_duration))
            
            
            audio_clip = AudioFileClip(str(audio_path))
            video_clip = image_clip.set_audio(audio_clip)
            
            return video_clip
            
        except Exception as e:
            print(f"Error creating clip for {image_path}: {str(e)}")
            return None

    def create_video_from_timing(self, timing_file):
        """Create a video from timing information"""
        try:
            
            with open(timing_file, 'r', encoding='utf-8') as f:
                timing_data = json.load(f)
            
            print(f"\nCreating video for: {timing_data['title']}")
            clips = []
            
            
            for slide in timing_data['slides']:
                print(f"Processing slide: {slide.get('title', slide['type'])}")
                
                if 'image_path' not in slide or 'audio_path' not in slide:
                    print(f"Missing image or audio path for slide")
                    continue
                
                clip = self.create_slide_clip(
                    slide['image_path'],
                    slide['audio_path'],
                    slide['duration']
                )
                
                if clip:
                    clips.append(clip)
            
            if not clips:
                print("No valid clips created")
                return False
            
            
            print("Concatenating clips...")
            final_video = concatenate_videoclips(clips, method="compose")
            
            
            output_file = self.output_folder / f"{Path(timing_file).stem}.mp4"
            
            
            print(f"Writing video to {output_file}...")
            final_video.write_videofile(
                str(output_file),
                fps=self.fps,
                codec='libx264',
                audio_codec='aac',
                threads=4,
                preset='medium'
            )
            
            
            final_video.close()
            for clip in clips:
                clip.close()
            
            print(f"Video created successfully: {output_file}")
            return True
            
        except Exception as e:
            print(f"Error creating video: {str(e)}")
            return False

    def process_all_timing_files(self):
        """Process all timing files in the timing folder"""
        try:
            timing_files = list(self.timing_folder.glob('*_timing.json'))
            
            if not timing_files:
                print(f"No timing files found in {self.timing_folder}")
                return
            
            print(f"Found {len(timing_files)} timing files to process")
            
            for timing_file in timing_files:
                print(f"\nProcessing {timing_file.name}")
                self.create_video_from_timing(timing_file)
                
        except Exception as e:
            print(f"Error processing timing files: {str(e)}")

def main():
    try:
        creator = VideoCreator()
        creator.process_all_timing_files()
        
    except KeyboardInterrupt:
        print("\nVideo creation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error in main execution: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()