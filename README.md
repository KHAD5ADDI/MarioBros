# 🕹️ Super Mario Bros AI Simulator

## 🎯 Project Objective

This project aims to develop an interactive **Super Mario Bros simulator** integrating two machine learning models capable of learning to play the game under different levels of knowledge.

The goal is to simulate and compare the **performance of two intelligent agents** in a controlled game environment:

- An **informed agent** (Agent 1), which knows the game objects (enemies, bonuses, obstacles) **and their functions** (e.g., "this mushroom gives speed").
- A **naive agent** (Agent 2), which sees the objects but **has no knowledge of their roles or the correct timing for actions** (e.g., when to jump, avoid, or enter tunnels).


## 🧠 Technical Approach

### 🕵️‍♂️ Agent 1 – Feature-Informed Learning
- **Inputs**: Object type, object role, Mario’s state, relative positions.
- **Model**: Neural network (supervised learning + reinforcement learning, e.g., Q-learning or PPO).
- **Goal**: Optimize performance (speed + score) using **semantic features** to accelerate learning.

### 🤖 Agent 2 – Pure Exploration Learning
- **Inputs**: Raw visual or vector-based game state (e.g., sprites, map layout, environmental info).
- **Model**: Neural network trained via **reinforcement learning only**, without prior object knowledge.
- **Goal**: Learn to play by exploration, like a human discovering the game for the first time.

## 🏗️ Project Architecture


---

## 🧪 Technologies Used

- 🐍 **Python 3.10+**
- 🎮 **Pygame** (2D game development)
- 🧠 **PyTorch** or **TensorFlow** (neural model development)
- 📊 **Pandas**, **NumPy**, **Matplotlib** (data handling & visualization)
- 🤖 **Stable-Baselines3** (optional RL library)

## 📊 Evaluation Goals

- Compare the **learning efficiency** between an agent with prior knowledge and one learning from scratch.
- Visualize agent decision paths and behavior.
- Analyze how the naive agent discovers mechanics (e.g., learning that pipes are tunnels, mushrooms are boosts).


## 📥 Data & Resources

The game objects and levels used are either:
- **Scraped** from public Mario level datasets (e.g., HuggingFace, GitHub, Spriters Resource), or
- **Programmatically generated** for simulated environments.

> ⚠️ All external resources are documented in `data/README.md` with proper credits and license info.

## 🚀 Run the Project

```bash
git clone https://github.com/yourusername/mario-simulator.git
cd mario-simulator
pip install -r requirements.txt
python src/simulator.py
```

## 📌 Authors

Project developed as part of the ML Proof of Concept 2024-2025 course – Albert Global Data School by:
- Florent NEGAF
- Khadidja ADDI
- Titouan PERRON

👨‍🏫 Supervised by Gianluca QUERCINI
