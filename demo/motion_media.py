"""v2 hard-cut picture, caption burn-in, and absolute-time audio mixing."""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image

import media
from pipeline import BuildError, Subtitle


def encode_frames(frames: Path, destination: Path, length: float, fps: int = 30) -> None:
    count = math.ceil(length*fps-1e-8)
    for index in range(count):
        if not (frames / f'frame-{index:06}.png').is_file():
            raise BuildError(f'Missing motion frame {index}; rerun the host frame renderer.')
    media.ffmpeg(['-framerate', str(fps), '-start_number', '0', '-i', frames/'frame-%06d.png',
                  '-frames:v', str(count), '-an', *media.video_encoder(), '-movflags', '+faststart', destination],
                 destination.parent/'encode.log')


def window_subtitles(cues: list[Subtitle], start: float, length: float) -> list[Subtitle]:
    return [Subtitle(max(0,c.start-start), min(length,c.end-start), c.text)
            for c in cues if c.end > start and c.start < start+length]


def caption_canvas(text: str, panel_path: Path, *, font_size: int = 50) -> Image.Image:
    """The same caption placement is used by the film and review stills."""
    panel_path.parent.mkdir(parents=True, exist_ok=True)
    media.text_panel(text, panel_path, font_size=font_size)
    with Image.open(panel_path) as panel:
        if panel.height > 136:
            raise BuildError('Caption does not fit the reserved bottom 200 px with a 64 px safe margin.')
        frame = Image.new('RGBA', media.SIZE)
        caption_y = media.SIZE[1]-64-panel.height
        frame.alpha_composite(panel, ((media.SIZE[0]-panel.width)//2, caption_y))
    return frame


def caption_at(cues: list[Subtitle], time: float) -> str | None:
    """Use the encoder's 30 fps ceil boundaries, including end-exclusive cues."""
    frame = math.floor(time*media.FPS+1e-8)
    return next((c.text for c in cues if math.ceil(c.start*media.FPS-1e-8) <= frame
                 < math.ceil(c.end*media.FPS-1e-8)), None)


def caption_review_frame(source: Path, destination: Path, cues: list[Subtitle], time: float, *, font_size: int = 50) -> str | None:
    text = caption_at(cues, time)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as image:
        if image.size != media.SIZE:
            raise BuildError('Review frame must be 1920×1080.')
        frame = image.convert('RGBA')
    if text:
        frame.alpha_composite(caption_canvas(text, destination.parent/'panels'/destination.name, font_size=font_size))
    frame.convert('RGB').save(destination)
    return text


def burn_captions(picture: Path, cues: list[Subtitle], destination: Path, length: float, *, font_size: int = 50) -> None:
    """One transparent PNG stream avoids opening every cue as a looping video input."""
    folder = destination.parent/'captions'; folder.mkdir(parents=True,exist_ok=True)
    blank = folder/'blank.png'; Image.new('RGBA',media.SIZE).save(blank)
    total_frames = math.ceil(length*media.FPS-1e-8)
    cursor, lines = 0, ['ffconcat version 1.0']
    def hold(name: str, frames: int) -> None:
        if frames > 0:
            lines.extend([f"file '{name}'", 'option framerate 30', f'duration {frames/media.FPS:.9f}'])
    for i,cue in enumerate(cues):
        first, last = max(cursor,math.ceil(cue.start*media.FPS-1e-8)), min(total_frames,math.ceil(cue.end*media.FPS-1e-8))
        if last <= first:
            continue
        hold('blank.png',first-cursor)
        caption_canvas(cue.text, folder/f'panel-{i:03}.png', font_size=font_size).save(folder/f'cue-{i:03}.png')
        hold(f'cue-{i:03}.png',last-first)
        cursor=last
    hold('blank.png',total_frames-cursor)
    # concat needs the following packet to retain the preceding still's duration.
    lines.extend(["file 'blank.png'", 'option framerate 30'])
    playlist=folder/'captions.ffconcat'; playlist.write_text('\n'.join(lines)+'\n')
    media.ffmpeg(['-i',picture,'-safe','0','-f','concat','-i',playlist,
                  '-filter_complex','[1:v]fps=30,format=rgba[c];[0:v][c]overlay=x=0:y=0:eof_action=repeat:format=auto[v]',
                  '-map','[v]','-an','-t',f'{length:.9f}','-r','30',*media.video_encoder(),
                  '-movflags','+faststart',destination],destination.parent/'captions.log')


def mix_audio(voices: list[Path], shots: list[dict], music: Path, gain: float, destination: Path,
              *, offset: float, timeline_duration: float, start: float = 0, length: float | None = None) -> None:
    length=timeline_duration-start if length is None else length
    args, filters, labels = [], [], []
    for voice,shot in zip(voices,shots):
        a,b=max(start,shot['start']),min(start+length,shot['voice_end'])
        if b <= a:
            continue
        index=len(labels); label=f'voice{index}'
        args += ['-ss',f"{a-shot['start']:.9f}",'-t',f'{b-a:.9f}','-i',voice]
        delay=round((a-start)*48000)
        filters.append(f'[{index}:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,'
                       f'adelay={delay}S:all=1,apad,atrim=duration={length:.9f}[{label}]')
        labels.append(label)
    if not labels:
        raise BuildError('Selected motion window contains no narration; choose a window over the first flips.')
    filters.append(''.join(f'[{label}]' for label in labels)+f'amix=inputs={len(labels)}:duration=longest:normalize=0[voice]')
    music_index=len(labels)
    args += ['-ss',f'{offset+start:.9f}','-t',f'{length:.9f}','-i',music]
    fade_start=max(0,timeline_duration-2-start)
    fade=(f',afade=t=out:st={fade_start:.9f}:d=2' if start+length>timeline_duration-2 else '')
    filters += ['[voice]asplit=2[narration][sidechain]',
                f'[{music_index}:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,'
                f'volume={gain}dB,atrim=duration={length:.9f},asetpts=PTS-STARTPTS{fade}[bed]',
                '[bed][sidechain]sidechaincompress=threshold=0.025:ratio=6:attack=30:release=400[ducked]',
                '[narration][ducked]amix=inputs=2:duration=first:normalize=0[mixed]']
    media.ffmpeg([*args,'-filter_complex',';'.join(filters),'-map','[mixed]','-t',f'{length:.9f}',
                  '-c:a','pcm_s24le','-ar','48000','-ac','2',destination],destination.parent/'mix.log')
