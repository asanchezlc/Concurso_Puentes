# Bridges Contest - ETSICCP UGR

**First authors:**  
- **Enrique García-Macías**
- **Antonio S. López-Cuervo**  

## 1. Description

This repository contains codes to plot real time sensor data from bridge load tests in ETSICCP UGR.


## 2. Prerequisites

Make sure you have the following prerequisites configured:

- Python 3.x (tested on Python 3.11.5):
- Packages included in requirements.txt

In order to facilitate the use in a different pc, creating a virtual environment is recommended

## 3. Installation

**Clone the repository locally:**
``` bash
git clone https://github.com/asanchezlc/Concurso_Puentes.git
```

**Create virtual environment**: go to the project directory to create the virtual environment 
``` bash
python -m venv <name_of_virtual_environment>  # e.g. python -m venv .venv
```

**Activate virtual environment**
``` bash
# Windows
\.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

**Upgrade pip and install requirements**
``` bash
python -m pip install --upgrade pip
pip install requirements.txt
```

## 4. Interface Configuration and GUI Panel

### 🔹 Modifiable Variables
To configure the interface, open the main script **`interface.py`** and search for **"MODIFIABLE VARIABLES"**.

There, you can set the following parameters:

- **`refresh_time`** → Refresh time for updating **graph plots** and **text updates** (in milliseconds).
- **`arduino_port`** → Check the `.ino` file for the correct port (e.g., `"COM3"`).
- **`baud_rate`** → Check the `.ino` file for the correct baud rate (e.g., `9600`).
- **`smooth_plots`** → Set to `True` if you want smoothed graphs.
- **`step_smooth`** → Number of points used for smoothing (before and after). Applies **only if** `smooth_plots = True`.
- **`threshold_mass_peaks`** → Threshold for detecting **outliers in mass** (e.g., peaks greater than `50 kg`).
- **`simulated`** → Defaults to `False`. Set to `True` when the **Arduino Mega** is **not connected** (for debugging purposes).

---

### 🔹 Running the Interface
After setting the desired parameters, **run the `interface.py` file**.

### 🔹 GUI Overview
The GUI consists of the following sections:

### 1️⃣ Left Bottom Side (Name Input)
- Allows you to **set a team name**, which will be used as the **default name** for saved files (e.g., `"Equipo_1"`).
- If you **change the name**, click the **"Save"** button to apply the changes.

#### 2️⃣ Start Measurement Button
- When clicked, a **calibration process** starts:
  - **Both mass and deflection are set to 0.**
  - The calibration lasts **5 seconds**.
- After calibration, the **measurement starts automatically**.
- Clicking the button again (**Stop Measurement**) does the following:
  - **Saves a file** in the `"data"` folder.
  - While the measurement is running, **a backup file is saved every 10 seconds** in `"data/backup"`.
