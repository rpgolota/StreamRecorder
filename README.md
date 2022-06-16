# Stream Recorder (Modified) 

This modified stream recorder can be used in the same way as originally intended: (https://github.com/microsoft/HoloLens2ForCV/tree/main/Samples/StreamRecorder).
The modifications to it and the processing scripts allow for easy eye data collection.

## Contents

| File/folder | Description |
|-------------|-------------|
| `StreamRecorderApp` | C++ application files and assets. |
| `StreamRecorderConverter` | Python conversion script resources. |
| `README.md` | This README file. |

## Prerequisites

* Windows Device Portal set up for the hololens.
* Python3 installed with numpy, opencv-python, open3d for compatibility with all StreamRecorder features.

## Setup

1. After cloning and opening the **StreamRecorderApp/StreamRecorder.snl** solution in Visual Studio, build (ARM64), and deploy.
2. [Enable Device Portal and Research Mode](https://docs.microsoft.com/windows/mixed-reality/research-mode)

## Running the app

1. Find StreamRecorder on the hololens under all apps.
2. Open StreamRecorder.
3. Press Start to begin recording.
4. Press Stop to stop the recording.

## Downloading the data

1. Run `recorder_console.py` after having changed the three lines in side containing the ip address of the device portal, and login information.
2. Run `list` to see the available recordings to download.
3. Run `download <X>` to download the x'th recording.

## Key differences

**StreamRecorderApp**

The stream recording modes allow for different streams to be captures.
As this modified version focuses on Eye data collection, if only the eye stream is enabled, then the output will only contain a csv file with eye data in it.
The following lines in AppMain.cpp are set to ensure this.
```
std::vector<ResearchModeSensorType> AppMain::kEnabledRMStreamTypes = { };
std::vector<StreamTypes> AppMain::kEnabledStreamTypes = { StreamTypes::EYE };
```

**Recorded data**

The file saved will be a csv file containing the following data:
| Timestamp | EyePresent | Origin X | Origin Y | Origin Z | Origin W | Direction X | Direction Y | Direction Z | Direction W | Distance |
|-|-|-|-|-|-|-|-|-|-|-|

The timestamp is recorded in windows Integer8 format (100-nanoseconds elapsed since January 1, 1601 UTC). 

**StreamRecorderConverter**

The post processing script `recorder_console.py` was changed to use a custom HololensInterface, using the python requests module instead of urllib.
This cleans up the code significantly and make it much more usable.

This new code is seen in `connection.py`.
