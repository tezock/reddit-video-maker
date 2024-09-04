# Main File for Reddit Videos

# handle making audio.
def makeAudio(author, text):
    
    # import elevenlabs api
    from elevenlabs import generate, set_api_key

    # set API key
    set_api_key("API_KEY_HERE")

    # set the desired voice ID
    voiceId = "EXAVITQu4vr4xnSDxMaL"

    # generate the audio
    audio = generate(
        text=text,
        voice=voiceId
    )

    # write the audio to the given file.
    with open(author + ".wav", "wb") as fp:
        fp.write(audio)

    return


# return a list of all of the requests.
def getRequests(subreddit, limit):

    # handle imports
    import requests

    # set the user agent header so that we can uniquely make requests.
    headers = {'User-agent': 'your bot 0.1'}

    # make the request utilizing the input subreddit and limit.
    response = requests.get("https://www.reddit.com/r/" + str(subreddit) + ".json?limit=" + str(limit), headers=headers)

    # track the results
    results = []

    # if the response is okay, populate results!
    if response.ok:

        data = response.json()

        posts = data["data"]["children"]

        for post in posts:
            
            # get the actual post
            item = post["data"]

            # get the author text and title
            author = item["author"]
            text = item["selftext"]
            title = item["title"]

            # got URL, not needed though.
            url = item["url"]

            results.append({"author": author, "text": text, "title": title})

    return results

def makePic(author, title):
    
    # handle imports
    from PIL import Image, ImageDraw, ImageFont

    NL_NUM = 40

    # open the template image
    image = Image.open("template-two.png")

    # instantiate a draw object on the image
    d = ImageDraw.Draw(image)

    # get the font size and type.
    font = ImageFont.truetype("Roboto-Regular.ttf", 15) #350 // len(title))

    # if the text is too long, splice the title and add new line delimeters every 28 characters.
    if len(title) > 28:
        
        chars = list(title)

        i = NL_NUM

        while i < len(chars):

            # go back to a space.
            while i > 0 and chars[i] != ' ' and chars[i] != "\n" and chars[i] != "-\n":

                i -= 1

            # if i is equal to 0 or we found a delimeter, add the -\n delimiter after 28 chars and increment i.
            if i == 0 or chars[i] == "\n" or chars[i] == "-\n":
                
                # shift i forward to where the insertion should be.
                i += NL_NUM

                # only insert if the index is in bounds.
                if i < len(chars) - NL_NUM:
                    chars.insert(i, "-\n")
                
                # now check the next insertion point
                i += NL_NUM
            
            # if not, we found a space. replace index with delimeter.
            else:
                chars[i] = "\n"
                i += NL_NUM

        title = "".join(chars)
        

    text = title
    text_pos = (30, 90)
    text_color = (0, 0, 0)

    # write the text to the image.
    d.text(text_pos, text=text, fill=text_color, font=font)

    # save the image.
    image.save(str(author) + ".png")

    return

# makes subtitles for a given author
def make_subtitles(author):
    
    # import assemblyai
    import assemblyai as aai

    # set the API key
    aai.settings.api_key = "API_KEY"

    # instantiate the transcriber
    transcriber = aai.Transcriber()

    # transcribe the transcript from the necessary audio
    transcript = transcriber.transcribe(str(author) + ".wav")

    # store the subtitles from the transcriber
    subtitles = transcript.export_subtitles_srt(17)

    # create the subtitles into a file.
    with open(str(author) + ".srt", "w") as f:

        f.write(subtitles)

    return

# Time to build the videos!
def make_video(author, videos):

    # handle necessary imports
    import moviepy
    from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, ImageClip
    from moviepy.video.tools.subtitles import SubtitlesClip
    import random

    # get a random video.
    choices = videos
    choice = random.choice(choices)

    # Load video clip
    video_clip = VideoFileClip(choice)

    # Load audio clip
    audio_clip = AudioFileClip(str(author) + ".wav")

    # get a random clip from the video that's the same length as the audio.
    start = 0
    end = video_clip.duration - audio_clip.duration
    random_start = random.uniform(start, end)
    video_clip = video_clip.subclip(random_start, random_start + audio_clip.duration)

    # load Image clip
    title_image_clip = ImageClip(str(author) + ".png", duration=5.00)

    # load subtitles
    generator = lambda txt: TextClip(txt, font='KOMIKAX_.ttf', fontsize=32, color='white', stroke_color='black', stroke_width=2)
    text_clips = SubtitlesClip(str(author) + '.srt', generator)

    # Set the video clip's audio to the loaded audio clip
    video_clip = video_clip.set_audio(audio_clip)

    # add the subtitles into the video.
    video_clip = CompositeVideoClip([video_clip, text_clips.set_pos(("center"))])

    # add the title image clip
    video_clip = CompositeVideoClip([video_clip, title_image_clip.set_pos("center")])

    # Set the duration of the video to match the duration of the audio
    video_clip = video_clip.set_duration(audio_clip.duration)

    # Write the output video with the combined audio
    video_clip.write_videofile(str(author) + ".mp4", codec="libx264", audio_codec="aac")

    # Close the video and audio clips
    video_clip.close()
    audio_clip.close()
    text_clips.close()
    title_image_clip.close()

# general function to make and partition videos with any given title, text, and author.
def make_videos(author, text, title, videos):

    # if the length of the text is not greater than 2500 characters, do basic logic.
    if len(text) < 2500:

        # # MAKE a picture from its title
        print("Making Picture...")
        makePic(author, title)
            
        # # MAKE the audio for its text
        print("Making Audio...")
        makeAudio(author, title + text)
            
        # # MAKE the subtitles from the audio
        print("Making Subtitles...")
        make_subtitles(author)
            
        # # MAKE the video from all three.
        print("Making Video...")
        make_video(author, videos)

        # after the video is made, remove the cruft
        import os

        extensions = [".png", ".srt", ".wav"]

        for extension in extensions:

            file_name = author + extension

            os.remove(file_name)

    else:

        # partition segments of 1250 characters to not break api limit.
        
        part_start = 0
        part_end  = 1250
        partitions = []

        # do work while there are still characters left.
        while part_start < len(text):

            # properly get the beginning of words before the start partition, ending of words after the start partition
            temp_start = part_start
            temp_end = part_end

            # shift start backward
            while temp_start > 0 and text[temp_start] != ' ':

                temp_start -= 1

            # shift temp end forward
            while temp_end < len(text) and text[temp_end] != ' ':

                temp_end += 1

            partitions.append(text[temp_start:temp_end])

            part_start += 1250
            part_end += 1250

        # create a video for each partition present.
        print("Making " + str(len(partitions)) + " videos...")

        for i in range(len(partitions)):

            print("\nMaking video " + str(i + 1) + "...\n")

            part_title = title  + " Part " + str(i + 1) + " " 
            part_text = title + partitions[i]
            part_author = author + "_" + str(i + 1)

            # # MAKE a picture from its title
            print("Making Picture...")
            makePic(part_author, part_title)
                
            # # MAKE the audio for its text
            print("Making Audio...")
            makeAudio(part_author, part_text)
                
            # # MAKE the subtitles from the audio
            print("Making Subtitles...")
            make_subtitles(part_author)
                
            # # MAKE the video from all three.
            print("Making Video...")
            make_video(part_author)

            # after the video is made, remove the cruft
            import os

            extensions = [".png", ".srt", ".wav"]

            for extension in extensions:

                file_name = part_author + extension

                os.remove(file_name)
    
    print("Done editing!")

# FLOW WILL BE
    
# GET the post that will have its video created

title = ""

text = """
"""
author = ""

"""
"""

video_pathnames = ["mcvideo1-cropped.mp4", "gtavid1.mp4", "mcvideo2-cropped.mp4"]

make_videos("testing-new-font", "Hello There Traveler! I am currently just testing out a new font that I wanted to use for making videos. I am going to just add a bunch of new random text so that I can have more seconds in the clip to actually see what the subs look like.", "New font testing? Join to see what's coming next!")