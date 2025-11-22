import whisper
import os
import tempfile
from typing import Optional, Dict
from pathlib import Path
from app.core.config import get_settings

settings = get_settings()


class WhisperService:
    def __init__(self):
        self.model_name = settings.WHISPER_MODEL
        self.model = None
        self._initialized = False
    
    def initialize(self):
        """
        Initialize Whisper model
        """
        if not self._initialized:
            print(f"Loading Whisper model: {self.model_name}")
            self.model = whisper.load_model(self.model_name)
            self._initialized = True
            print("Whisper model loaded successfully")
    
    def transcribe_audio(self, audio_path: str, language: str = "es") -> Dict[str, any]:
        """
        Transcribe audio file to text
        
        Args:
            audio_path: Path to audio/video file
            language: Language code (default: "es" for Spanish)
        
        Returns:
            Dict with transcription and metadata
        """
        if not self._initialized:
            self.initialize()
        
        # Check if file exists
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Transcribe
        result = self.model.transcribe(
            audio_path,
            language=language,
            fp16=False,  # Use FP32 for better compatibility
            verbose=False
        )
        
        return {
            'text': result['text'],
            'language': result['language'],
            'segments': result['segments'],
            'duration': result.get('duration', 0)
        }
    
    def transcribe_video(self, video_path: str, language: str = "es") -> Dict[str, any]:
        """
        Transcribe video file (extracts audio and transcribes)
        
        Args:
            video_path: Path to video file
            language: Language code
        
        Returns:
            Dict with transcription and metadata
        """
        # Whisper can handle video files directly
        return self.transcribe_audio(video_path, language)
    
    def transcribe_with_timestamps(self, audio_path: str, language: str = "es") -> Dict[str, any]:
        """
        Transcribe with detailed timestamp information
        """
        if not self._initialized:
            self.initialize()
        
        result = self.model.transcribe(
            audio_path,
            language=language,
            fp16=False,
            verbose=False,
            word_timestamps=True
        )
        
        # Format segments with timestamps
        formatted_segments = []
        for segment in result['segments']:
            formatted_segments.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': segment['text'],
                'words': segment.get('words', [])
            })
        
        return {
            'text': result['text'],
            'language': result['language'],
            'segments': formatted_segments,
            'duration': result.get('duration', 0)
        }
    
    def detect_speakers(self, segments: list) -> Dict[str, any]:
        """
        Basic speaker detection based on audio patterns
        (This is a simplified version - for production, use pyannote.audio)
        """
        # Group segments by potential speakers based on timing gaps
        speakers = []
        current_speaker = []
        last_end = 0
        
        for segment in segments:
            start = segment['start']
            # If gap is more than 2 seconds, assume new speaker
            if start - last_end > 2.0:
                if current_speaker:
                    speakers.append({
                        'segments': current_speaker,
                        'total_time': sum(s['end'] - s['start'] for s in current_speaker)
                    })
                current_speaker = []
            
            current_speaker.append(segment)
            last_end = segment['end']
        
        # Add last speaker
        if current_speaker:
            speakers.append({
                'segments': current_speaker,
                'total_time': sum(s['end'] - s['start'] for s in current_speaker)
            })
        
        return {
            'num_speakers': len(speakers),
            'speakers': speakers
        }
    
    def extract_audio_from_video(self, video_path: str, output_path: Optional[str] = None) -> str:
        """
        Extract audio from video file using ffmpeg
        """
        import ffmpeg
        
        if output_path is None:
            # Create temporary file
            temp_dir = tempfile.gettempdir()
            output_path = os.path.join(temp_dir, f"extracted_audio_{os.getpid()}.wav")
        
        try:
            # Extract audio
            (
                ffmpeg
                .input(video_path)
                .output(output_path, acodec='pcm_s16le', ac=1, ar='16k')
                .overwrite_output()
                .run(quiet=True)
            )
            return output_path
        except ffmpeg.Error as e:
            raise Exception(f"Error extracting audio: {str(e)}")
    
    def analyze_participation_from_video(self, video_path: str) -> Dict[str, any]:
        """
        Analyze student participation from video presentation
        """
        # Transcribe video
        transcription_result = self.transcribe_with_timestamps(video_path)
        
        # Detect potential speakers
        speaker_analysis = self.detect_speakers(transcription_result['segments'])
        
        # Calculate participation metrics
        total_duration = transcription_result['duration']
        participation_data = {
            'total_duration': total_duration,
            'transcription': transcription_result['text'],
            'num_speakers_detected': speaker_analysis['num_speakers'],
            'speaker_times': []
        }
        
        for i, speaker in enumerate(speaker_analysis['speakers']):
            speaker_time = speaker['total_time']
            percentage = (speaker_time / total_duration * 100) if total_duration > 0 else 0
            participation_data['speaker_times'].append({
                'speaker_id': i + 1,
                'time': round(speaker_time, 2),
                'percentage': round(percentage, 2)
            })
        
        return participation_data


# Singleton instance
whisper_service = WhisperService()
