# **HydroEdventure**

HydroEdventure is a Python-based tool designed to streamline the generation of voice lines for video game characters. By parsing large CSV files containing character dialogue, the software leverages the Eleven Labs API to produce high-quality text-to-speech outputs efficiently.

---

## **Table of Contents**

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Requirements](#requirements)
- [Contributing](#contributing)
- [License](#license)
- [Credits](#credits)
- [GitHub Repository](#github-repository)

---

## **Features**

- **Dialogue Parsing**: Processes large CSV files containing character dialogue.
- **API Integration**: Seamless text-to-speech functionality with the Eleven Labs API.
- **Scalability**: Designed for handling extensive datasets efficiently.
- **Customization**: Adjustable settings for voice styles and character-specific configurations.

---

## **Installation**

### **Prerequisites**

- Python 3.8+
- Eleven Labs API key

### **Steps**

1. Clone the repository:
    ```bash
    git clone https://github.com/jljenkins1/HydroEdventure.git
    cd HydroEdventure
    ```

2. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Configure the API key:
    - Add your Eleven Labs API key to a `.env` file or directly in the configuration.

---

## **Usage**

### **CSV File Format**

Prepare a CSV file with the following structure:

**File Name**: `DialogueEntries.csv`

```csv
entrytag,DialogueText
Text,text
0_Toppo_0,"Test line!"
0_Anderson_1,"Test two!"
```
## **Requirements**

The following dependencies are required for HydroEdventure to run:

- `Flask==3.0.0`: A web framework for Python.
- `Flask-Session==0.4.0`: Flask extension for server-side session management.
- `requests==2.31.0`: A simple HTTP library for making API calls.
- `python-dotenv==1.0.0`: A library to manage environment variables.
- `PyJWT==2.8.0`: A Python library for handling JSON Web Tokens (JWT).
- `Werkzeug==3.0.0`: A comprehensive WSGI web application library.

### **Installation**

To install the required dependencies, simply run:

```bash
pip install -r requirements.txt
```
## **Contributing**

Contributions are welcome! To contribute:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Submit a pull request with a detailed description of your changes.

## **License**

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## **Credits**

- **Developers**:
  - Cole Anyan
  - Chase Deskin
  - Josh Jenkins
  - Jimmy Scowden
  - Cameron Snow

- **API**: Eleven Labs API for text-to-speech functionality.

---

## **GitHub Repository**

You can find the HydroEdventure project on GitHub: [HydroEdventure Repository](https://github.com/jljenkins1/HydroEdventure)

