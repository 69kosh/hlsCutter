import subprocess
from time import sleep, time
import ffmpeg
import numpy as np


def cutter(srcFilename, dstFilename, scenes, every):

    probe = ffmpeg.probe(srcFilename)
    video_stream = next(
        (stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
    width = int(video_stream['width'])  # // 2
    height = int(video_stream['height'])  # // 2
    lengthTime = float(video_stream['duration'])
    lengthFrames = int(video_stream['nb_frames'])

    audio_stream = next(
        (stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
    print(video_stream, audio_stream)
    # maxSize = min(width, height)
    # targetSize = min(480, maxSize)
    # ratio = targetSize/maxSize

    # width = int(width*ratio/2)*2
    # height = int(height*ratio/2)*2

    # print(width, height)
    # return
    rate = video_stream['r_frame_rate']
    secondsPerFrame = lengthTime/lengthFrames

    srcVProcess = (
        ffmpeg  # .output()
        .input(srcFilename)
        .output('pipe:', format='rawvideo', pix_fmt='bgr24', s='{}x{}'.format(width, height), r=rate)
        .run_async(pipe_stdout=True, quiet=True)
    )

    srcAProcess = (
        ffmpeg
        .input(srcFilename)
        .output('-', format='s16le', acodec='pcm_s16le', ac=2, ar='48k')
        .run_async(pipe_stdout=True, quiet=True)
    )

    # dstProcesses = {}
    # for filename in scenes:
    #     dstProcesses[filename] = (
    #         ffmpeg
    #         .input('pipe:', format='rawvideo', pix_fmt='bgr24', s='{}x{}'.format(width, height))
    #         .output(filename, pix_fmt='yuv420p')
    #         .overwrite_output()
    #         .run_async(pipe_stdin=True)
    #     )

    dstVProcess = (
        ffmpeg
        .input('pipe:', format='rawvideo', pix_fmt='bgr24', s='{}x{}'.format(width, height), r=rate)
        .output(dstFilename, pix_fmt='yuv420p', r=rate)
        .overwrite_output()
        .run_async(pipe_stdin=True)
    )
    dstAProcess = (
        ffmpeg
        .input('pipe:', format='s16le', acodec='pcm_s16le', ac=2, ar='48k')
        .output(dstFilename + '.aac')
        .overwrite_output()
        .run_async(pipe_stdin=True)
    )

    # vStream = ffmpeg.input('pipe:', format='rawvideo', pix_fmt='bgr24', s='{}x{}'.format(width, height), r=25).video
    # aStream = ffmpeg.input('pipe:', f='s16le', acodec='pcm_s16le', ac=2, ar='48000').audio

    # dstProcess = (
    # 	ffmpeg
    # 		# .concat(vStream, v=1)
    # 		.concat(vStream, aStream, v=1, a=1)
    # 		.output(dstFilename, pix_fmt='yuv420p', r=25)
    # 		.overwrite_output()
    # 		.run_async(pipe_stdin=True)
    # )

    i = 0
    while True:
        inVBytes = srcVProcess.stdout.read(width * height * 3)
        if not inVBytes:
            break

        inABytes = srcAProcess.stdout.read(
            int(48000*2*2*secondsPerFrame))  # 48000*2*2 bytes per second
        if not inABytes:
            break

        dstVProcess.stdin.write(inVBytes)
        dstVProcess.stdin.flush()
        dstAProcess.stdin.write(inABytes)
        i += 1

        # if i > 600:
        #     break

    # srcVProcess.wait()
    # srcAProcess.wait()
    dstVProcess.stdin.close()
    dstVProcess.wait()
    dstAProcess.stdin.close()
    dstAProcess.wait()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='MP4 to HLS cutter based on scenes list')
    parser.add_argument('mp4Filename', metavar='mp4', type=str,
                        help='mp4 file')
    parser.add_argument('scenesFilename', metavar='scenes', type=str,
                        help='scenes CSV file')
    parser.add_argument('--every', type=int, default=1,
                        help='multiplier for scene frame numbers')
    args = parser.parse_args()
    # print(args.mp4Filename, args.scenesFilename, args.every)
    cutter(args.mp4Filename, args.mp4Filename +
           '.mp4', args.scenesFilename, args.every)
