import whisper
import os
import tempfile
from typing import Optional, Dict
from pathlib import Path
from app.core.config import get_settings
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


class WhisperService:
    def __init__(self):
        self.model_name = settings.WHISPER_MODEL
        self.model = None
        self._initialized = False
        logger.info(f"🔧 WhisperService created with model: {self.model_name}")
    
    def initialize(self):
        """
        Initialize Whisper model
        """
        if not self._initialized:
            logger.info(f"📥 Loading Whisper model: {self.model_name}")
            print(f"📥 Loading Whisper model: {self.model_name}")
            try:
                self.model = whisper.load_model(self.model_name)
                self._initialized = True
                logger.info("✅ Whisper model loaded successfully")
                print("✅ Whisper model loaded successfully")
            except Exception as e:
                logger.error(f"❌ Error loading Whisper model: {str(e)}")
                print(f"❌ Error loading Whisper model: {str(e)}")
                raise
    
    def transcribe_audio(self, audio_path: str, language: str = "es") -> Dict[str, any]:
        """
        Transcribe audio file to text
        
        Args:
            audio_path: Path to audio/video file
            language: Language code (default: "es" for Spanish)
        
        Returns:
            Dict with transcription and metadata
        """
        logger.info(f"🎤 Starting audio transcription: {audio_path}")
        print(f"🎤 Starting audio transcription: {audio_path}")
        
        if not self._initialized:
            logger.info("Model not initialized, initializing now...")
            print("Model not initialized, initializing now...")
            self.initialize()
        
        # Check if file exists
        if not os.path.exists(audio_path):
            error_msg = f"Audio file not found: {audio_path}"
            logger.error(f"❌ {error_msg}")
            print(f"❌ {error_msg}")
            raise FileNotFoundError(error_msg)
        
        file_size = os.path.getsize(audio_path)
        logger.info(f"📊 File size: {file_size / 1024 / 1024:.2f} MB")
        print(f"📊 File size: {file_size / 1024 / 1024:.2f} MB")
        
        try:
            # Transcribe
            logger.info(f"🔄 Transcribing with language: {language}")
            print(f"🔄 Transcribing with language: {language}")
            
            result = self.model.transcribe(
                audio_path,
                language=language,
                fp16=False,  # Use FP32 for better compatibility
                verbose=False
            )
            
            logger.info(f"✅ Transcription completed: {len(result['text'])} characters")
            print(f"✅ Transcription completed: {len(result['text'])} characters")
            print(f"📝 Preview: {result['text'][:200]}...")
            
            return {
                'text': result['text'],
                'language': result['language'],
                'segments': result['segments'],
                'duration': result.get('duration', 0)
            }
            
        except Exception as e:
            logger.error(f"❌ Error during transcription: {str(e)}")
            print(f"❌ Error during transcription: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    def transcribe_video(self, video_path: str, language: str = "es") -> Dict[str, any]:
        """
        Transcribe video file (extracts audio and transcribes)
        
        Args:
            video_path: Path to video file
            language: Language code
        
        Returns:
            Dict with transcription and metadata
        """
        logger.info(f"🎥 Starting video transcription: {video_path}")
        print(f"🎥 Starting video transcription: {video_path}")
        
        # Whisper can handle video files directly
        return self.transcribe_audio(video_path, language)
    
    def transcribe_with_timestamps(self, audio_path: str, language: str = "es") -> Dict[str, any]:
        """
        Transcribe with detailed timestamp information
        """
        logger.info(f"⏱️ Starting transcription with timestamps: {audio_path}")
        print(f"⏱️ Starting transcription with timestamps: {audio_path}")
        
        if not self._initialized:
            self.initialize()
        
        try:
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
            
            logger.info(f"✅ Transcription with timestamps completed: {len(formatted_segments)} segments")
            print(f"✅ Transcription with timestamps completed: {len(formatted_segments)} segments")
            
            return {
                'text': result['text'],
                'language': result['language'],
                'segments': formatted_segments,
                'duration': result.get('duration', 0)
            }
            
        except Exception as e:
            logger.error(f"❌ Error in timestamp transcription: {str(e)}")
            print(f"❌ Error in timestamp transcription: {str(e)}")
            raise
    
    def detect_speakers(self, segments: list) -> Dict[str, any]:
        """
        Basic speaker detection based on audio patterns
        (This is a simplified version - for production, use pyannote.audio)
        """
        logger.info(f"👥 Detecting speakers from {len(segments)} segments")
        print(f"👥 Detecting speakers from {len(segments)} segments")
        
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
        
        logger.info(f"✅ Detected {len(speakers)} potential speakers")
        print(f"✅ Detected {len(speakers)} potential speakers")
        
        return {
            'num_speakers': len(speakers),
            'speakers': speakers
        }
    
    def extract_audio_from_video(self, video_path: str, output_path: Optional[str] = None) -> str:
        """
        Extract audio from video file using ffmpeg
        """
        import ffmpeg
        
        logger.info(f"🎬 Extracting audio from video: {video_path}")
        print(f"🎬 Extracting audio from video: {video_path}")
        
        if output_path is None:
            # Create temporary file
            temp_dir = tempfile.gettempdir()
            output_path = os.path.join(temp_dir, f"extracted_audio_{os.getpid()}.wav")
        
        logger.info(f"📁 Output path: {output_path}")
        print(f"📁 Output path: {output_path}")
        
        try:
            # Extract audio
            (
                ffmpeg
                .input(video_path)
                .output(output_path, acodec='pcm_s16le', ac=1, ar='16k')
                .overwrite_output()
                .run(quiet=True)
            )
            
            logger.info(f"✅ Audio extracted successfully")
            print(f"✅ Audio extracted successfully")
            return output_path
            
        except ffmpeg.Error as e:
            error_msg = f"Error extracting audio: {str(e)}"
            logger.error(f"❌ {error_msg}")
            print(f"❌ {error_msg}")
            raise Exception(error_msg)
    
    def analyze_participation_from_video(self, video_path: str) -> Dict[str, any]:
        """
        Analyze student participation from video presentation
        """
        logger.info(f"📊 Starting participation analysis: {video_path}")
        print(f"📊 Starting participation analysis: {video_path}")
        
        try:
            # Transcribe video
            logger.info("Step 1: Transcribing video with timestamps...")
            print("Step 1: Transcribing video with timestamps...")
            transcription_result = self.transcribe_with_timestamps(video_path)
            
            # Detect potential speakers
            logger.info("Step 2: Detecting speakers...")
            print("Step 2: Detecting speakers...")
            speaker_analysis = self.detect_speakers(transcription_result['segments'])
            
            # Calculate participation metrics
            logger.info("Step 3: Calculating participation metrics...")
            print("Step 3: Calculating participation metrics...")
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
                
                logger.info(f"   Speaker {i+1}: {speaker_time:.2f}s ({percentage:.1f}%)")
                print(f"   Speaker {i+1}: {speaker_time:.2f}s ({percentage:.1f}%)")
            
            logger.info(f"✅ Participation analysis completed")
            print(f"✅ Participation analysis completed")
            
            return participation_data
            
        except Exception as e:
            logger.error(f"❌ Error in participation analysis: {str(e)}")
            print(f"❌ Error in participation analysis: {str(e)}")
            import traceback
            traceback.print_exc()
            raise


# Singleton instance
whisper_service = WhisperService()

# Log initialization
logger.info("🎤 Whisper service module loaded")
print("🎤 Whisper service module loaded")