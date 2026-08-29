![Expense Tracker API Banner](banner.png)

# Expense Tracker API

> A robust, feature-rich RESTful API built with Python, FastAPI, and SQLAlchemy for tracking expenses, managing budgets, and generating automated email alerts.

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Tests Status](https://img.shields.io/badge/tests-passing-brightgreen)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)

---

## 📋 Table of Contents

- [About the Project](#-about-the-project)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Installation & Setup](#-installation--setup)
- [Usage Examples](#-usage-examples)
- [Contributing](#-contributing)
- [License](#-license)
- [Contact](#-contact)

---

## 🎯 About the Project

Managing personal finances effectively can be challenging. The **Expense Tracker API** is designed to solve this problem by providing developers and users with a secure, fast, and reliable backend system to record, monitor, and analyze daily spending habits. It includes built-in automated email notifications to alert users when they exceed their predefined category budgets.

---

## ✨ Features

- **User Authentication & Authorization**: Secure signup and login workflows.
- **Expense Management**: Full CRUD operations (Create, Read, Update, Delete) for managing individual expenses.
- **Budget Tracking & Email Alerts**: Automated SMTP email notifications triggered when spending limits are crossed.
- **Analytics & Graphs**: AI-assisted insights and structured data processing for expense visualization.
- **Automated Background Service**: Configurable via NSSM to run smoothly as a persistent system service.

---

## 💻 Tech Stack

- **Language**: Python 3.10+
- **Framework**: FastAPI
- **Database & ORM**: PostgreSQL / MySQL with SQLAlchemy
- **Environment Management**: Python Dotenv
- **Utilities**: Smtplib (Email Alerts), Pydantic (Data Validation)

---

## 🗂️ Project Structure

```text
expense-tracker-api/
│
├── __pycache__/
├── env/                 # Virtual environment
├── auth.py              # Authentication logic & token handling
├── database.py          # Database connection & session setup
├── email_utils.py       # SMTP email alert functions
├── main.py              # FastAPI app initialization & routing
├── models.py            # SQLAlchemy database models
├── schemas.py           # Pydantic data validation schemas
├── requirements.txt     # Project dependencies
└── README.md            # Project documentation
