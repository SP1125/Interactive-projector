# Interactive Projected Battleships

A webcam-controlled, projected Battleships game developed as a collaborative university project. The system uses real-time hand tracking to allow players to interact with a projected game board without conventional physical controls.

## My contribution

I was responsible for the **core runtime architecture and integration of the project**. I brought the hand-tracking and game components together into a functioning real-time application, including the communication between the vision pipeline and game loop, gesture/event handling, input state management, game-mode architecture, and Battleships interaction logic.

The project was developed collaboratively. Other team members contributed substantially to the **hand-detection/landmarking pipeline** and the **visual/UI design and rendering**. I also modified and integrated components from these areas where necessary to connect them to the overall runtime architecture.

### System architecture

```text
Webcam
   ↓
Hand detection / landmarks
   ↓
Fingertip & gesture processing
   ↓
Game events
   ↓
Event queue
   ↓
Pygame game loop
   ↓
Game state / Battleships logic
   ↓
Projected display
```

This repository contains the integrated project rather than only my individual contribution, since the runtime depends on the interaction between all of these components.

## Limitations & Future Work

The prototype was developed within the constraints of a university project and presentation timeline. Several areas remain open for further development:

* **Camera–projector calibration:** A homography-based calibration system was prototyped to map camera coordinates to projected-screen coordinates, but was not fully integrated into the final runtime. Further work would be required to make the interaction robust to changes in camera/projector position and perspective.
* **Input latency:** The current vision-to-game pipeline has noticeable latency, particularly during continuous hand movement. Future work would investigate camera capture and processing rates, MediaPipe inference cost, event-queue behaviour, and unnecessary processing between the vision and rendering pipelines.
* **Robustness:** Further testing across different lighting conditions, camera positions and user hand positions would be needed to make the interaction system reliable outside the controlled presentation environment.
