import pyautogui
import math
import cv2
import numpy as np
import time
import mediapipe as mp
import ssl 

ssl._create_default_https_context = ssl._create_unverified_context

mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=True, min_detection_confidence=0.3, model_complexity=2)
mp_drawing = mp.solutions.mediapipe.solutions.drawing_utils

def detectPose(image, pose, blankImage=False):

    output_image = image.copy()

    if blankImage:
        blank_image = np.zeros((720,1920,3), np.uint8)
        output_image = blank_image

    imageRGB = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    
    results = pose.process(imageRGB)
   
    height, width, _ = image.shape
    
    landmarks = []
    
    if results.pose_landmarks:
        mp_drawing.draw_landmarks(image=output_image, landmark_list=results.pose_landmarks, connections=mp_pose.POSE_CONNECTIONS)
        
        for landmark in results.pose_landmarks.landmark:
            
            landmarks.append((int(landmark.x * width), int(landmark.y * height),
                                  (landmark.z * width)))
    return output_image, landmarks, results


def calculateAngle(landmark1, landmark2, landmark3):

    x1, y1, _ = landmark1
    x2, y2, _ = landmark2
    x3, y3, _ = landmark3
    angle = math.degrees(math.atan2(y3 - y2, x3 - x2) - math.atan2(y1 - y2, x1 - x2))
    if angle < 0:
        angle += 360
    return angle


def classifyPose(landmarks, output_image):
    
    label = 'Unknown Pose'

    color = (0, 0, 255)
    
    left_elbow_angle = calculateAngle(landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value],
                                      landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value],
                                      landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value])
    
    right_elbow_angle = calculateAngle(landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value],
                                       landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value],
                                       landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value])   
    
    left_shoulder_angle = calculateAngle(landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value],
                                         landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value],
                                         landmarks[mp_pose.PoseLandmark.LEFT_HIP.value])

    right_shoulder_angle = calculateAngle(landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value],
                                          landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value],
                                          landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value])

    left_knee_angle = calculateAngle(landmarks[mp_pose.PoseLandmark.LEFT_HIP.value],
                                     landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value],
                                     landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value])

    right_knee_angle = calculateAngle(landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value],
                                      landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value],
                                      landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value])
    
    if left_elbow_angle > 165 and left_elbow_angle < 195 and right_elbow_angle > 165 and right_elbow_angle < 195:

        if left_shoulder_angle > 80 and left_shoulder_angle < 110 and right_shoulder_angle > 80 and right_shoulder_angle < 110:


            if left_knee_angle > 165 and left_knee_angle < 195 or right_knee_angle > 165 and right_knee_angle < 195:

                if left_knee_angle > 90 and left_knee_angle < 120 or right_knee_angle > 90 and right_knee_angle < 120:

                    label = 'Warrior II Pose' 
                        
            if left_knee_angle > 160 and left_knee_angle < 195 and right_knee_angle > 160 and right_knee_angle < 195:

                label = 'T Pose'

    if left_knee_angle > 165 and left_knee_angle < 195 or right_knee_angle > 165 and right_knee_angle < 195:

        if left_knee_angle > 315 and left_knee_angle < 335 or right_knee_angle > 25 and right_knee_angle < 45:

            label = 'Tree Pose'
                
    if label != 'Unknown Pose':
        
        color = (0, 255, 0)  
    
    cv2.putText(output_image, label, (10, 30),cv2.FONT_HERSHEY_PLAIN, 2, color, 2)
    
    return output_image, label



def checkHandsJoined(img,results, draw=False):
    height, width, _ = img.shape

    output_img = img.copy()

    left_wrist_landmark = (results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_WRIST].x * width,results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_WRIST].y * height)
    right_wrist_landmark = (results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_WRIST].x * width,results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_WRIST].y * height)

    distance = int(math.hypot(left_wrist_landmark[0] - right_wrist_landmark[0],left_wrist_landmark[1] - right_wrist_landmark[1]))

    if distance < 130:
        hand_status = 'Hands Joined'
        color = (0, 255, 0)
        
    else:
        hand_status = 'Hands Not Joined'
        color = (0, 0, 255)

    if draw:
        cv2.putText(output_img, hand_status, (10, 30), cv2.FONT_HERSHEY_PLAIN, 2, color, 3)
        cv2.putText(output_img, f'Distance: {distance}', (10, 70), cv2.FONT_HERSHEY_PLAIN, 2, color, 3)
        
    return output_img, hand_status

def checkLeftRight(img, results, draw=False):


    horizontal_position = None
    
    height, width, c = img.shape
    
    output_image = img.copy()
    
    left_x = int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].x * width)
    right_x = int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].x * width)
    
    if (right_x <= width//2 and left_x <= width//2):
        horizontal_position = 'Left'

    elif (right_x >= width//2 and left_x >= width//2):
        horizontal_position = 'Right'
    
    elif (right_x >= width//2 and left_x <= width//2):
        horizontal_position = 'Center'
        
    if draw:

        cv2.putText(output_image, horizontal_position, (5, height - 10), cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 255), 3)
        cv2.line(output_image, (width//2, 0), (width//2, height), (255, 255, 255), 2)


    return output_image, horizontal_position


def checkJumpCrouch(img, results, MID_Y=250, draw=False):

        height, width, _ = img.shape
    
        output_image = img.copy()
        
        left_y = int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].y * height)
        right_y = int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].y * height)

        actual_mid_y = abs(right_y + left_y) // 2
        
        lower_bound = MID_Y-15
        upper_bound = MID_Y+100
        
        if (actual_mid_y < lower_bound):
            posture = 'Jumping'
        
        elif (actual_mid_y > upper_bound):
            posture = 'Crouching'
        
        else:
            posture = 'Standing'
            
        if draw:
            cv2.putText(output_image, posture, (5, height - 50), cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 255), 3)
            cv2.line(output_image, (0, MID_Y),(width, MID_Y),(255, 255, 255), 2)
            
        return output_image, posture

def checkHandGestures(img, results, draw=False):
    height, width, _ = img.shape
    output_image = img.copy()
    
    # Get wrist and shoulder landmarks
    left_wrist = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_WRIST]
    right_wrist = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_WRIST]
    left_shoulder = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER]
    right_shoulder = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER]
    
    # Convert to pixel coordinates
    left_wrist_pos = (int(left_wrist.x * width), int(left_wrist.y * height))
    right_wrist_pos = (int(right_wrist.x * width), int(right_wrist.y * height))
    left_shoulder_pos = (int(left_shoulder.y * height))
    right_shoulder_pos = (int(right_shoulder.y * height))
    
    gesture = 'Standing'
    color = (255, 255, 255)
    
    # Check for jump (either hand raised above shoulder)
    if left_wrist.y < left_shoulder.y - 0.1 or right_wrist.y < right_shoulder.y - 0.1:
        gesture = 'Jumping'
        color = (0, 255, 0)
    
    # Check for crouch (hands close together near waist)
    elif math.hypot(left_wrist_pos[0] - right_wrist_pos[0], 
                   left_wrist_pos[1] - right_wrist_pos[1]) < 100:
        gesture = 'Crouching'
        color = (0, 0, 255)
    
    # Check for left/right movement
    if left_wrist.x < 0.3 and right_wrist.x < 0.3:
        gesture = 'Left'
        color = (255, 0, 0)
    elif left_wrist.x > 0.7 and right_wrist.x > 0.7:
        gesture = 'Right'
        color = (0, 0, 255)
    
    if draw:
        cv2.putText(output_image, f'Gesture: {gesture}', (10, 30), 
                   cv2.FONT_HERSHEY_PLAIN, 2, color, 2)
    
    return output_image, gesture

if __name__ == '__main__':
    
    pose_video = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5, model_complexity=1)

    # Try multiple camera indices
    camera_index = 0
    max_tries = 2
    cap = None
    
    for i in range(max_tries):
        print(f"Trying to open camera {i}...")
        cap = cv2.VideoCapture(i)
        
        if cap is None or not cap.isOpened():
            print(f"Failed to open camera {i}")
            if i < max_tries - 1:
                continue
            else:
                print("Error: Could not open any camera")
                print("Please check camera permissions in System Settings > Privacy & Security > Camera")
                exit(1)
        
        # Try reading a test frame
        ret, test_frame = cap.read()
        if ret:
            print(f"Successfully opened camera {i}")
            break
        else:
            print(f"Could not read from camera {i}")
            cap.release()
            if i < max_tries - 1:
                continue
            else:
                print("Error: Could not read from any camera")
                print("Please check camera permissions in System Settings > Privacy & Security > Camera")
                exit(1)

    # Set camera properties
    cap.set(3, 640)
    cap.set(4, 360)
    pTime = 0
    
    game_started = False 
    x_pos_index = 1
    y_pos_index = 1
    MID_Y = None
    counter = 0
    num_of_frames = 10




    
    while True:
        success, img = cap.read()
        if not success:
            print("Error: Failed to grab frame")
            break
            
        img = cv2.flip(img, 1)
        h, w, _ = img.shape
        img, landmarks, results = detectPose(img, pose_video)
        
        if landmarks:
            if game_started:
                img, gesture = checkHandGestures(img, results, draw=True)
                
                # Handle different gestures
                if gesture == 'Left' and x_pos_index != 0:
                    pyautogui.press('left')
                    x_pos_index -= 1
                    
                elif gesture == 'Right' and x_pos_index != 2:
                    pyautogui.press('right')
                    x_pos_index += 1
                    
                elif gesture == 'Jumping' and y_pos_index == 1:
                    pyautogui.press('up')
                    y_pos_index += 1
                    
                elif gesture == 'Crouching' and y_pos_index == 1:
                    pyautogui.press('down')
                    y_pos_index -= 1
                    
                elif gesture == 'Standing' and y_pos_index != 1:
                    y_pos_index = 1
                
            else:
                cv2.putText(img, 'JOIN BOTH HANDS TO START THE GAME.', (5, h - 10),
                           cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 3)
            
            if checkHandsJoined(img, results)[1] == 'Hands Joined':

                counter += 1

                if counter == num_of_frames:

                    if not(game_started):

                        game_started = True
                        left_y = int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].y * h)
                        right_y = int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].y * h)
                        MID_Y = abs(right_y + left_y) // 2
                        pyautogui.click(x=1300, y=800, button='left')
                    else:
                        pyautogui.press('space')
                    
                    
                    counter = 0

            else:

                counter = 0
            
            if MID_Y:
                
                img, posture = checkJumpCrouch(img, results, MID_Y, draw=True)
                
                if posture == 'Jumping' and y_pos_index == 1:

                    pyautogui.press('up')
                    y_pos_index += 1 

                elif posture == 'Crouching' and y_pos_index == 1:


                    pyautogui.press('down')

                    y_pos_index -= 1

                elif posture == 'Standing' and y_pos_index   != 1:

                    y_pos_index = 1
                print(posture)
            
     
        else:

            counter = 0
        
        cTime = time.time()
        fps = 1/(cTime-pTime)
        pTime = cTime

        cv2.putText(img,str(int(fps)),(70,50),cv2.FONT_HERSHEY_PLAIN,3,(255,0,0),3)


        cv2.imshow('Game', img)
        k = cv2.waitKey(1) & 0xFF
        if(k == 27) or (k==113):
            break
    cap.release()
    cv2.destroyAllWindows()