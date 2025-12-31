from faster_whisper import WhisperModel
from pathlib import Path
import sys
import json

CHECKPOINT_SUFFIX = ".checkpoint.json"
OUTPUT_SUFFIX = ".txt"


def sec_to_hms(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def transcribe_resumable_with_timestamps(mp3_path: str):
    mp3_path = Path(mp3_path)
    checkpoint_path = mp3_path.with_suffix(CHECKPOINT_SUFFIX)
    output_path = mp3_path.with_suffix(OUTPUT_SUFFIX)

    if not mp3_path.exists():
        raise FileNotFoundError(mp3_path)

    # Resume logic
    if checkpoint_path.exists():
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        last_end = checkpoint["last_end"]
        print(f"Resuming from {sec_to_hms(last_end)}")
    else:
        checkpoint = {"last_end": 0.0}
        last_end = 0.0
        output_path.write_text("", encoding="utf-8")
        print("Starting fresh transcription")

    model = WhisperModel(
        "medium",
        device="cpu",
        compute_type="int8"
    )

    segments, info = model.transcribe(
        str(mp3_path),
        language="el",
        vad_filter=True,
        beam_size=5
    )

    with output_path.open("a", encoding="utf-8") as out:
        for segment in segments:
            if segment.end <= last_end:
                continue

            text = segment.text.strip()
            if not text:
                continue

            start_ts = sec_to_hms(segment.start)
            end_ts = sec_to_hms(segment.end)

            out.write(f"[{start_ts} → {end_ts}] {text}\n")
            out.flush()

            checkpoint["last_end"] = segment.end
            checkpoint_path.write_text(
                json.dumps(checkpoint),
                encoding="utf-8"
            )

    print("\nTranscription complete.")
    print(f"Output: {output_path}")
    checkpoint_path.unlink(missing_ok=True)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python gr_transcriber_timestamps.py audio.mp3")
        sys.exit(1)

    transcribe_resumable_with_timestamps(sys.argv[1])
