# ImgeAI

![License](https://img.shields.io/badge/license-MIT-blue.svg) ![Nuxt](https://img.shields.io/badge/Nuxt-3.0-green) ![Python](https://img.shields.io/badge/Python-3.1%2B-yellow)

> **Turns plain Chinese into natural English without the robotic AI flavor.**
>
> 拒绝“AI味”，让中文转英文更像真人。

## 📖 The Story / 初衷

**My English is bad. Used AI translation to post before and got deleted. So I made this project. Turns Chinese into English without the AI flavor. Reads and writes naturally. Communication without borders.**

之前因为英文不好，利用 AI 翻译发帖被删过（因为语气太像机器人）。所以有了这个项目。将中文转为英文，去除 AI 味，实现自然读写，沟通无国界。

## ✨ Features / 功能

- **De-AI Translator**: Strips away the "robotic" tone (e.g., "Furthermore", "In conclusion") common in standard LLM outputs.
  - 去除常见的 AI 僵硬语气词，让表达更地道。
- **Natural Flow**: Focuses on how native speakers actually write in tech communities (Reddit, Hacker News, GitHub).
  - 模拟海外技术社区的真人沟通习惯。
- **Modern Stack**: Built with a separated but cohesive architecture.
  - **Frontend**: Nuxt 4 (Vue 3)
  - **Backend**: Python

## 📂 Project Structure / 项目结构

This project is a monorepo containing both the backend and frontend.
本项目采用单体仓库模式，包含前后端代码。

```text
imgeai/
├── server/      # Python Backend (API, Logic)
├── web/         # Nuxt Frontend (UI, Interaction)
├── docker-compose.yml
└── README.md

cd ./server run  python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt