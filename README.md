# Human detection and recognition in video

This code is part of bachelor thesis for human detection and recognition 
in video [2018-2019]. It is written in Python programming language. 

## Required libraries

Required Python version is 3.6.x. Program was developed on Python 3.6.8 and
Windows 10 operating system. Dlib wheel in project cannot be installed on 
Linux nor macOS machines. When using these OS, please download dlib 19.8.1 
wheel according to your OS.

Program is using following libraries:
* Imutils 0.5.2
* Numpy 1.16.2
* OpenCV 3.4.4.19
* Pillow 5.4.1
* Dlib

These libraries (except Dlib) can be downloaded via pip manager with
following commands:

```bash
pip install imutils==0.5.2
pip install numpy==1.16.2
pip install opencv-contrib-python==3.4.4.19
pip install Pillow==5.4.1
```

or via requirements.txt:
```bash
pip install requirements.txt
```

Dlib must be installed via wheel (whl) file, included in root directory
of the project. Open the terminal in project directory and execute:

```bash
pip install dlib-19.8.1-cp36-cp36m-win_amd64.whl
```

## Running the program

Program can be run via terminal with following command:

```bash
python recognition_system.py
```

### Author

© 2019 Martin Nguyen