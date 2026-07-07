# PicoScale // Image Optimizer Core

![Version](https://img.shields.io/badge/version-v2.4_Core-17181c?style=for-the-badge)
![Python](https://img.shields.io/badge/python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/flask-3.0.3-000000?style=for-the-badge&logo=flask&logoColor=white)
![Celery](https://img.shields.io/badge/celery-5.4.0-37814A?style=for-the-badge&logo=celery&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-blue?style=for-the-badge)

**PicoScale** is a lightweight, open-source, high-throughput image processing and structural mutation engine. Designed to execute entirely in-memory without disk I/O latency, it combines an asynchronous Celery/Flask backend with a responsive, glassmorphism frontend featuring visual cropping, multi-unit dimension conversion, and real-time array metadata inspection.

---

## Key Features

*  Zero-Latency In-Memory Pipeline:** Bypasses disk read/write bottlenecks by executing all bitmap decompression, Lanczos resampling, and format transcoding directly inside system RAM using `Pillow` and `OpenCV`.
*  Serverless-Ready Eager Mode:** Hardwired with `CELERY_TASK_ALWAYS_EAGER=True` support, allowing the entire asynchronous task queue to run synchronously inside a single web container—**no external Redis database or background worker dynos required** for free-tier cloud deployments.
*  Interactive Aspect Ratio Snapping:** Integrated with `Cropper.js` to provide instant bounding-box presets for **16:9 (Widescreen)**, **4:3 (Standard)**, **1:1 (Square)**, and **9:16 (Story/Portrait)** layouts.
*  Intelligent Multi-Unit Resizing:** Switch dynamically between **Pixels (px)**, **Centimeters (cm)**, and **Inches (in)** at a standard 96 DPI screen density with client-side mathematical conversion.
*  On-the-Fly Format Transcoding:** Easily convert uploaded image arrays between **JPEG**, **PNG**, and **WEBP** formats, with automatic RGB background layering for alpha-channel conversions.
*  Batch Ingestion & Auto-Download:** Process up to 4 files simultaneously with automated browser blob streaming that instantly downloads mutated files to the user's device.
*  Modern Frosted UI:** Built with Tailwind CSS, Space Grotesk typography, and an ascending CSS-only 3D mechanical printing press animation running continuously in the background.

---

## 🛠️ Tech Stack

### **Backend Engine**
* **Framework:** Python 3.12, Flask 3.0.3
* **Task Broker / Queue:** Celery 5.4.0, Kombu, Redis 5.0.4 (Optional in Eager Mode)
* **Image Manipulation:** Pillow 10.3.0, OpenCV (`opencv-python-headless==4.9.0.80`), NumPy 1.26.4 (Pinned for ABI stability)
* **Server & Hardware Monitoring:** Gunicorn 22.0.0, psutil 5.9.8

### **Frontend Interface**
* **Styling:** Tailwind CSS (via CDN), Custom Glassmorphism UI
* **Interactive Tooling:** Cropper.js v1.6.1
* **Typography:** Google Fonts (`Space Grotesk`, `JetBrains Mono`)
* **Background Art:** Uiverse.io 3D Mechanical Printing Press

---

##  Local Development Setup

### 1. Prerequisites
Ensure you have **Python 3.12+** installed on your local machine.

### 2. Clone & Initialize Environment
# Clone the repository
git clone [https://github.com/YOUR_GITHUB_USERNAME/picoscale.git](https://github.com/YOUR_GITHUB_USERNAME/picoscale.git)
cd picoscale

# Create a virtual environment
py -3.12 -m venv venv

# Activate the virtual environment
# On Windows PowerShell:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

### **2. Image Mutation Execution**
Ingests a multipart form payload and returns the mutated binary file stream directly.

* **URL:** `/api/process`
* **Method:** `POST`
* **Headers:** `Content-Type: multipart/form-data`
* **Form Parameters:**

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `images` | `File(s)` | *Required* | Image array payload (Max 4 files, 25MB limit). |
| `quality` | `Integer` | `85` | Compression percentage (5 to 100). |
| `format` | `String` | `original` | Target format: `original`, `JPEG`, `PNG`, or `WEBP`. |
| `width` | `Integer` | `None` | Target width in standard pixels. |
| `height` | `Integer` | `None` | Target height in standard pixels. |
| `crop` | `String` | `None` | Bounding box coordinates formatted as `"x,y,width,height"`. |

---

## 📄 License

This project is open-source and distributed under the terms of the **MIT License**. See the [LICENSE](LICENSE) file for more details.
