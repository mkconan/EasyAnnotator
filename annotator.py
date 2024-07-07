import cv2
import json
from pathlib import Path

# 動画ファイルのパスを指定
video_path_list = ["./lovot.MP4", "./sea.MP4"]
video_path_list = list(map(lambda x: Path(x), video_path_list))

# クロップ情報を保存するリスト
crop_info = []

step_frame_number: int = 10
display_scale: float = 1 / 2


# 矩形選択のコールバック関数
def select_roi(event: int, x: int, y: int, flags: int, param):
    global roi_start, roi_end, selecting_roi, org_frame, draw_frame, cropped_image, roi_selected
    if event == cv2.EVENT_LBUTTONDOWN:
        draw_frame = org_frame.copy()
        roi_start = (x, y)
        selecting_roi = True
    elif event == cv2.EVENT_MOUSEMOVE:
        if selecting_roi:
            frame_copy = draw_frame.copy()
            cv2.rectangle(frame_copy, roi_start, (x, y), (0, 255, 0), 2)
            cv2.imshow("Video", frame_copy)
    elif event == cv2.EVENT_LBUTTONUP:
        roi_end = (x, y)
        selecting_roi = False
        roi_selected = True
        cv2.rectangle(draw_frame, roi_start, roi_end, (0, 255, 0), 2)
        cv2.imshow("Video", draw_frame)


cv2.namedWindow("Video")
cv2.setMouseCallback("Video", select_roi)

selecting_roi = False
roi_selected = False
roi_start = (0, 0)
roi_end = (0, 0)


for i, video_path in enumerate(video_path_list):
    # 動画のキャプチャを開始
    cap = cv2.VideoCapture(video_path)
    save_png_base_path = Path(f"./img/{i:03d}/")
    save_png_base_path.mkdir(exist_ok=True)
    # フレーム番号
    frame_number = 0
    while True:
        ret, org_frame = cap.read()
        if not ret:
            break

        # 表示する画像は縮小させる
        org_frame = cv2.resize(org_frame, dsize=None, fx=display_scale, fy=display_scale, interpolation=cv2.INTER_CUBIC)
        draw_frame = org_frame.copy()
        draw_frame = cv2.putText(
            draw_frame,
            f"frm:{frame_number:3d}",
            org=(0, 50),
            fontFace=cv2.FONT_HERSHEY_COMPLEX,
            fontScale=1.0,
            color=(255, 255, 255),
            thickness=1,
        )

        # 動画の1フレーム目、または 'N' が押されたら次のスキップされたフレーム目を表示
        if frame_number % step_frame_number == 0 or frame_number == 0:
            cv2.imshow("Video", draw_frame)

        key = cv2.waitKey(0)

        # N を押したら、フレームをスキップ
        if key == ord("n"):
            frame_number += step_frame_number
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            roi_selected = False
        # B を押したら、フレームを戻す
        elif key == ord("b"):
            frame_number = max(0, frame_number - step_frame_number)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            roi_selected = False
        # 図形が選択された状態で、Sが押されたらクロップ画像と座標が保存される
        elif key == ord("s") and roi_selected:
            scaled_x1, scaled_y1 = roi_start
            scaled_x2, scaled_y2 = roi_end
            cropped_image = org_frame[scaled_y1:scaled_y2, scaled_x1:scaled_x2]

            # 元画像の縮尺でのクロップした座標系を計算する
            x1, y1, x2, y2 = map(lambda p: int(p * (1 / display_scale)), [scaled_x1, scaled_y1, scaled_x2, scaled_y2])
            print(
                f"save {frame_number:3d}th frame cropped image at top_lft: ({scaled_x1:4d}, {scaled_y1:4d}) btm_rgt: ({scaled_x2:4d}, {scaled_y2:4d})"
            )
            crop_filename = save_png_base_path / f"cropped_{frame_number:03d}.png"
            cv2.imwrite(str(crop_filename), cropped_image)
            crop_info.append(
                {
                    "video_file": str(video_path.absolute()),
                    "frame_number": frame_number,
                    "roi": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                }
            )
            roi_selected = False

            frame_number += step_frame_number
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            roi_selected = False
        elif key == ord("q"):
            break
    cap.release()

cv2.destroyAllWindows()

# JSONファイルにクロップ情報を保存
json_filename = Path("crop_info.json")
with open(json_filename, "w") as json_file:
    json.dump(crop_info, json_file, indent=4)
