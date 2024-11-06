from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import os
import azure.cognitiveservices.speech as speechsdk
from pydub import AudioSegment


AudioSegment.ffmpeg = os.getenv("FFMPEG_BINARY", "/usr/bin/ffmpeg")
AudioSegment.ffprobe = os.getenv("FFPROBE_BINARY", "/usr/bin/ffprobe")

# Home view that shows a welcome message and a button to synthesize speech
def home_view(request):
    return HttpResponse("""
<html>
    <head>
        <title>Synthesize Speech</title>
    </head>
    <body>
        <h1>Welcome to the Speech Synthesizer</h1>
        <p>Enter the text you would like to synthesize, then click the button below:</p>
        <form method="post" action="/synthesize/">
            <!-- CSRF token for form submission -->
            {% csrf_token %}
            
            <!-- Input box for the text to be synthesized -->
            <label for="text">Text to Synthesize:</label><br>
            <input type="text" id="text" name="text" required placeholder="Enter text here"><br><br>
            
            <!-- Submit button -->
            <button type="submit" name="synthesize">Synthesize Speech</button>
        </form>
    </body>
</html>

        
    """)

@csrf_exempt
def synthesize_speech(request):
    if request.method == "POST":
        # Extract text to synthesize from the POST request
        text = request.POST.get("text", "Hello world!")  # Default text if not provided
        output_file = '/tmp/output.mp3'  # Save output in the temp directory for serverless functions

        # Azure Speech API configuration
        speech_config = speechsdk.SpeechConfig(
            subscription=os.getenv('SPEECH_KEY'), 
            region=os.getenv('SPEECH_REGION')
        )
        speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
        )
        audio_config = speechsdk.audio.AudioOutputConfig(filename=output_file)
        speech_config.speech_synthesis_voice_name = 'en-US-AvaMultilingualNeural'
        speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config, audio_config=audio_config
        )

        # Synthesize text to audio file
        result = speech_synthesizer.speak_text_async(text).get()
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print(f"Speech synthesized for text [{text}] and saved to '{output_file}'")
        elif result.reason == speechsdk.ResultReason.Canceled:
            return JsonResponse({"error": "Speech synthesis canceled."}, status=500)

        # Overlay background music onto the synthesized speech
        final_output_path = '/tmp/final_output_with_bgm.mp3'
        add_bgm(output_file, 'assets/bgm.mp3', final_output_path)

        # Return final output as a file response
        with open(final_output_path, "rb") as f:
            response = HttpResponse(f.read(), content_type="audio/mpeg")
            response["Content-Disposition"] = "attachment; filename=final_output_with_bgm.mp3"
            return response
        
    else :
        return JsonResponse({"error": "POST request required."}, status=405)

def add_bgm(podcast_path, bgm_path, final_path):
    # Load the synthesized speech and BGM directly as MP3
    podcast = AudioSegment.from_mp3(podcast_path)
    bgm = AudioSegment.from_mp3(bgm_path)

    # Extract intro, middle, and outro parts of BGM
    bgm_intro = bgm[:3000]  # First 3 seconds
    bgm_outro = bgm[-13000:-5000]  # Last 8 seconds
    bgm_middle = bgm[3000:-13000]  # Middle section

    # Set volume levels for different parts
    bgm_intro = bgm_intro - 15 
    bgm_outro = bgm_outro - 18
    bgm_middle = bgm_middle - 22

    # Calculate the required length for the middle BGM to loop
    middle_duration = len(podcast) - len(bgm_intro) - 1000

    # Loop the middle part of the BGM to cover the podcast duration
    bgm_middle_loop = bgm_middle * (middle_duration // len(bgm_middle) + 1)
    bgm_middle_loop = bgm_middle_loop[:middle_duration]  # Trim to exact duration

    # Combine intro, looped middle, and outro of BGM
    bgm_full = bgm_intro + bgm_middle_loop + bgm_outro

    # Overlay the background music on top of the synthesized speech
    final_mix = bgm_full.overlay(podcast, position=len(bgm_intro))
    
    # Export the final audio as MP3
    final_mix.export(final_path, format="mp3", bitrate="24k")
