import json
import os
import time

import click
import cv2


@click.command()
@click.option("--path", "-p")
@click.option("--sleep_sec", "-s", default=0.15)
def main(path, sleep_sec):
    index_imgs = []
    video = cv2.VideoWriter(
        f"ants_{time.time_ns()}.mp4", cv2.VideoWriter_fourcc(*"mp4v"), max(1, int(1 / sleep_sec)), (1080, 1080)
    )
    try:
        for f in os.listdir(path):
            if os.path.isfile(os.path.join(path, f)) and f.endswith(".png"):
                index_imgs.append(os.path.join(path, f))
                print(f)
            else:
                print(f"{f} is wrong")
        for img in sorted(index_imgs):
            cv2.imshow("lol", cv2.imread(img))
            img = cv2.imread(img)
            video.write(cv2.resize(img, (1080, 1080)))
            cv2.waitKey(int(sleep_sec * 1000))
    except:
        video.release()
        raise
    video.release()


if __name__ == "__main__":
    main()
